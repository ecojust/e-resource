"""Compare original and roof-enriched city manifests with identical cameras.

The views JSON contains [{name, center: [lng,lat], zoom, pitch, bearing, tile}].
This checks rendered source tiles, not architectural survey accuracy or GPU FPS.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
from playwright.async_api import async_playwright

os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY'] = '1'


async def main(args):
    views = json.loads(args.views.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'url': args.url, 'views': views, 'page_errors': [], 'shader_errors': [],
              'asset_errors': [], 'captures': [], 'hardware_performance_test': False}
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),
            headless=True, args=['--no-sandbox', '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'])
        try:
            page = await browser.new_page(viewport={'width': 1280, 'height': 850}, device_scale_factor=1)
            page.on('pageerror', lambda e: report['page_errors'].append(str(e)))
            page.on('console', lambda m: report['shader_errors'].append(m.text)
                    if 'Shader Error' in m.text or 'VALIDATE_STATUS' in m.text else None)
            page.on('response', lambda r: report['asset_errors'].append({'url': r.url, 'status': r.status})
                    if r.status >= 400 and ('.glb' in r.url or '/assets/city/' in r.url) else None)
            await page.goto(args.url, wait_until='domcontentloaded', timeout=60000)
            if await page.get_by_text('Open the page', exact=False).count():
                await page.get_by_text('Open the page', exact=False).first.click()
            await page.wait_for_function('window.__SHANGHAI_APP__', timeout=180000)
            print('APP_READY', flush=True)
            await page.evaluate('()=>{__SHANGHAI_APP__.syncMode("overview",false);}')
            if await page.locator('#panel-toggle').get_attribute('aria-expanded') == 'true':
                await page.locator('#panel-toggle').click()
            for name, manifest in [('before', args.before), ('after', args.after)]:
                if not manifest:
                    continue
                result = await page.evaluate('async url=>await __SHANGHAI_APP__.scene.setCityManifest(url)', manifest)
                assert not result.get('fallback'), result
                print('MANIFEST_READY', name, flush=True)
                for view in views:
                    await page.evaluate('async v=>{const a=__SHANGHAI_APP__;await a.selectPlace({id:v.name,name:v.label||"屋顶样例街区",districtId:v.district,walkStart:v.center,bearing:v.bearing,overviewZoom:v.zoom,custom:true});a.scene.map.stop();if(v.from){a.scene.setCameraFromTo({from:v.from,to:{lng:v.center[0],lat:v.center[1],alt:v.targetAltitude}});}else{a.scene.map.jumpTo({center:v.center,zoom:v.zoom,pitch:v.pitch,bearing:v.bearing});}}', view)
                    print('VIEW_READY', name, view['name'], flush=True)
                    await page.wait_for_function('tile=>{const s=__SHANGHAI_APP__.scene.getStreamingState();return s.loading===0&&s.queued===0&&s.active.some(r=>r.id===tile&&r.visible);}', arg=view['tile'], timeout=180000)
                    await page.wait_for_timeout(1200)
                    path = args.output / f'{view["name"]}-{name}.png'
                    await page.screenshot(path=str(path), timeout=90000)
                    state = await page.evaluate('()=>({stream:__SHANGHAI_APP__.scene.getStreamingState(),districts:__SHANGHAI_APP__.districts.length,mode:__SHANGHAI_APP__.mode,camera:{center:__SHANGHAI_APP__.scene.map.getCenter().toArray(),zoom:__SHANGHAI_APP__.scene.map.getZoom(),pitch:__SHANGHAI_APP__.scene.map.getPitch(),bearing:__SHANGHAI_APP__.scene.map.getBearing()}})')
                    report['captures'].append({'variant': name, 'view': view['name'], 'image': path.name, **state})
                    print('CAPTURE', name, view['name'], flush=True)
            report['passed'] = bool(report['captures']) and all(c['districts'] == 16 for c in report['captures']) and not any(report[k] for k in ('page_errors', 'shader_errors', 'asset_errors'))
            (args.output / 'browser.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            assert report['passed'], report
            print('PASSED', flush=True)
        finally:
            await browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--before')
    parser.add_argument('--after', required=True)
    parser.add_argument('--views', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    asyncio.run(main(parser.parse_args()))
