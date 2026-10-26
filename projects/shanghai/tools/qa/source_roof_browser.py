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
from shapely.geometry import shape, Point
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY'] = '1'


async def main(args):
    views = [] if args.bund_only else json.loads(args.views.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'url': args.url, 'views': views, 'forced_osm_fallback': args.force_osm, 'page_errors': [], 'shader_errors': [], 'map_warnings': [],
              'asset_errors': [], 'captures': [], 'hardware_performance_test': False}
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),
            headless=True, args=['--no-sandbox', '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'])
        try:
            page = await browser.new_page(viewport={'width': 1280, 'height': 850}, device_scale_factor=args.dpr)
            report['device_pixel_ratio'] = args.dpr
            if args.force_osm:
                await page.route('https://tiles.overturemaps.org/**', lambda route: route.abort())
                await page.route('https://stac.overturemaps.org/**', lambda route: route.abort())
            page.on('pageerror', lambda e: report['page_errors'].append(str(e)))
            page.on('console', lambda m: report['shader_errors'].append(m.text)
                    if 'Shader Error' in m.text or 'VALIDATE_STATUS' in m.text else None)
            page.on('console', lambda m: report['map_warnings'].append(m.text) if '[Shanghai map]' in m.text else None)
            page.on('response', lambda r: report['asset_errors'].append({'url': r.url, 'status': r.status})
                    if r.status >= 400 and ('.glb' in r.url or '/assets/city/' in r.url) else None)
            await page.goto(args.url, wait_until='domcontentloaded', timeout=60000)
            if await page.get_by_text('Open the page', exact=False).count():
                await page.get_by_text('Open the page', exact=False).first.click()
            await page.wait_for_function('window.__SHANGHAI_APP__', timeout=180000)
            print('APP_READY', flush=True)
            if args.check_bund:
                for attempt in range(8):
                    try:
                        await page.wait_for_function('()=>{const a=__SHANGHAI_APP__,s=a.scene.getStreamingState(),f=a.scene.getRealismState().osmFallback;return a.mode==="walk"&&s.loading===0&&s.pendingStates===0&&a.scene.getLandmarkState().every(r=>r.status==="loaded"&&!r.loadingModel)&&(!f?.active||(!f.pending&&f.coveredIDs>0&&f.residualReady));}', timeout=30000)
                        break
                    except PlaywrightTimeoutError:
                        progress=await page.evaluate('()=>{const a=__SHANGHAI_APP__,s=a.scene.getStreamingState();return {loadedLandmarks:a.scene.getLandmarkState().filter(r=>r.status==="loaded"&&!r.loadingModel).length,loadingCity:s.loading,fps:s.renderer?.fps,fallback:a.scene.getRealismState().osmFallback};}')
                        print('BUND_WAIT', json.dumps(progress), flush=True)
                        if attempt == 7:
                            raise
                if args.check_photos:
                    await page.wait_for_function('()=>__SHANGHAI_APP__.scene.getRealismState().lighting.reflectionSource==="photographic"', timeout=120000)
                    report['photo_model']=await page.evaluate('()=>__SHANGHAI_APP__.scene.getLandmarkAssetState("bund18")')
                    assert report['photo_model']['variant']=='full' and report['photo_model']['photoMeshes']>0
                    assert report['photo_model']['images'] and all(i['width']==1920 and i['height']==1369 for i in report['photo_model']['images'])
                    report['photo_asset']=await page.evaluate('''async()=>{
                      const record=(await(await fetch("data/landmarks.json")).json()).find(x=>x.id==="bund18");
                      const buffer=await(await fetch(record.model)).arrayBuffer(),view=new DataView(buffer),jsonLength=view.getUint32(12,true);
                      const doc=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,20,jsonLength))),binStart=28+jsonLength;
                      const hash=async b=>Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",b))).map(x=>x.toString(16).padStart(2,"0")).join("");
                      const images=await Promise.all(doc.images.map(async image=>{const v=doc.bufferViews[image.bufferView];return {bytes:v.byteLength,sha256:await hash(buffer.slice(binStart+(v.byteOffset||0),binStart+(v.byteOffset||0)+v.byteLength))};}));
                      return {bytes:buffer.byteLength,sha256:await hash(buffer),expectedBytes:record.web_bytes,expectedSha256:record.web_sha256,images,expectedPhotoSha256:record.reference.sha256,copyright:doc.asset.copyright};
                    }''')
                    photo=report['photo_asset']
                    assert photo['bytes']==photo['expectedBytes'] and photo['sha256']==photo['expectedSha256']
                    assert len(photo['images'])==1 and photo['images'][0]['sha256']==photo['expectedPhotoSha256']
                    assert 'ScareCriterion12' in photo['copyright'] and 'CC BY-SA 4.0' in photo['copyright']
                await page.screenshot(path=str(args.output/'bund-fallback.png'), timeout=90000)
                report['bund_walk']=await page.evaluate('()=>({mode:__SHANGHAI_APP__.mode,source:__SHANGHAI_APP__.scene.getCollisionState(),realism:__SHANGHAI_APP__.scene.getRealismState(),stream:__SHANGHAI_APP__.scene.getStreamingState()})')
                if args.force_osm:
                    residual = await page.evaluate('()=>{const m=__SHANGHAI_APP__.scene.map;return {original:m.getFeatureState({source:"openmaptiles",sourceLayer:"building",id:23809960}),data:m.getStyle().sources["shanghai-osm-building-residuals"]?.data};}')
                    assert isinstance(residual.get('data'),dict), 'Missing committed residual source'
                    target=Point(121.4850321254,31.2403431656)
                    parts=[f for f in residual['data'].get('features',[]) if str(f.get('originalSourceId',f.get('properties',{}).get('originalSourceId')))=='23809960']
                    result={'original_hidden':residual['original'].get('localModel') is True,'residual_components_for_source':len(parts),'bund18_in_residual':any(shape(f['geometry']).covers(target) for f in parts)}
                    report['bund_compound_replacement']=result
                    assert result['original_hidden'] and parts and not result['bund18_in_residual'], result
                if args.bund_only:
                    report['street_asset']=await page.evaluate('async()=>{const p=(await(await fetch("data/scene-props.json")).json()).find(x=>x.id==="bund-streets"),b=await(await fetch(p.model)).arrayBuffer(),hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",b))).map(x=>x.toString(16).padStart(2,"0")).join("");return {version:p.version,model:p.model,bytes:b.byteLength,sha256:hash,metadataBytes:p.bytes,metadataSha256:p.sha256};}')
                    asset=report['street_asset']
                    assert asset['bytes']==asset['metadataBytes'] and asset['sha256']==asset['metadataSha256'], asset
                print('BUND_WALK', flush=True)
            if not args.bund_only:
                await page.evaluate('()=>{__SHANGHAI_APP__.syncMode("overview",false);}')
            if not args.bund_only and await page.locator('#panel-toggle').get_attribute('aria-expanded') == 'true':
                await page.locator('#panel-toggle').click()
            for name, manifest in ([] if args.bund_only else [('before', args.before), ('after', args.after)]):
                if not manifest:
                    continue
                result = await page.evaluate('async url=>url==="initial"?__SHANGHAI_APP__.scene.getStreamingState():await __SHANGHAI_APP__.scene.setCityManifest(url)', manifest)
                assert not result.get('fallback'), result
                print('MANIFEST_READY', name, flush=True)
                for view in views:
                    await page.evaluate('async v=>{const a=__SHANGHAI_APP__;a.scene.setAvatarVisible(false);await a.selectPlace({id:v.name,name:v.label||"屋顶样例街区",districtId:v.district,walkStart:v.center,bearing:v.bearing,overviewZoom:v.zoom,custom:true});a.scene.map.stop();if(v.from){a.scene.setCameraFromTo({from:v.from,to:{lng:v.center[0],lat:v.center[1],alt:v.targetAltitude}});}else{a.scene.map.jumpTo({center:v.center,zoom:v.zoom,pitch:v.pitch,bearing:v.bearing});}}', view)
                    print('VIEW_READY', name, view['name'], flush=True)
                    await page.wait_for_function('tile=>{const s=__SHANGHAI_APP__.scene.getStreamingState();return s.loading===0&&s.queued===0&&s.active.some(r=>r.id===tile&&r.visible);}', arg=view['tile'], timeout=180000)
                    if args.force_osm:
                        await page.wait_for_function('()=>{const a=__SHANGHAI_APP__,f=a.scene.getRealismState().osmFallback;return a.scene.getCollisionState().buildingSource==="osm"&&f?.active&&!f.pending&&f.pendingRemovals===0&&f.coveredIDs>0;}',timeout=120000)
                    await page.wait_for_timeout(1200)
                    path = args.output / f'{view["name"]}-{name}.png'
                    await page.screenshot(path=str(path), timeout=90000)
                    state = await page.evaluate('()=>{const a=__SHANGHAI_APP__,map=a.scene.map;return {stream:a.scene.getStreamingState(),districts:a.districts.length,mode:a.mode,buildingSource:a.scene.getCollisionState(),osmFallback:a.scene.getRealismState().osmFallback,buildingLayers:map.getStyle().layers.filter(l=>l.type==="fill-extrusion").map(l=>({id:l.id,source:l.source,sourceLayer:l["source-layer"],visibility:l.layout?.visibility||"visible",filter:l.filter})),renderedBuildings:map.queryRenderedFeatures([[innerWidth*.3,innerHeight*.3],[innerWidth*.7,innerHeight*.7]]).filter(f=>f.layer.type==="fill-extrusion").slice(0,20).map(f=>({id:f.id,source:f.source,sourceLayer:f.sourceLayer,state:map.getFeatureState({source:f.source,sourceLayer:f.sourceLayer,id:f.id}),properties:f.properties,geometryType:f.geometry.type})),camera:{center:map.getCenter().toArray(),zoom:map.getZoom(),pitch:map.getPitch(),bearing:map.getBearing()}};}')
                    report['captures'].append({'variant': name, 'view': view['name'], 'image': path.name, **state})
                    print('CAPTURE', name, view['name'], flush=True)
            report['passed'] = bool(report['captures'] or report.get('bund_walk')) and all(c['districts'] == 16 for c in report['captures']) and not any(report[k] for k in ('page_errors', 'shader_errors', 'asset_errors'))
            if args.force_osm:
                report['passed'] = report['passed'] and all(c['buildingSource']['buildingSource'] == 'osm' and c['osmFallback']['active'] and c['osmFallback']['coveredIDs']>0 and c['osmFallback']['pendingRemovals']==0 and c['osmFallback']['failedWrites']==0 for c in report['captures'])
            (args.output / 'browser.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            assert report['passed'], {k:report[k] for k in ('page_errors','shader_errors','asset_errors')}
            print('PASSED', flush=True)
        except Exception as error:
            report['passed'] = False
            report['error'] = str(error)
            try:
                report['failure_state'] = await page.evaluate('()=>window.__SHANGHAI_APP__?{mode:__SHANGHAI_APP__.mode,stream:__SHANGHAI_APP__.scene.getStreamingState(),realism:__SHANGHAI_APP__.scene.getRealismState(),landmarks:__SHANGHAI_APP__.scene.getLandmarkState()}:null')
            except Exception:
                pass
            (args.output / 'browser.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            raise
        finally:
            await browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--before')
    parser.add_argument('--after', required=True, help='Manifest URL, or initial to retain the app default manifest')
    parser.add_argument('--views', type=Path)
    parser.add_argument('--bund-only', action='store_true', help='Check only the initial third-person Bund scene')
    parser.add_argument('--dpr', type=float, default=1, help='Rendering pixel ratio; CSS viewport remains 1280 by 850')
    parser.add_argument('--check-bund', action='store_true', help='Capture initial third-person Bund under the same service condition')
    parser.add_argument('--force-osm', action='store_true', help='Block Overture services to test emergency OSM fallback')
    parser.add_argument('--check-photos', action='store_true', help='Verify the loaded Bund18 photo, exact embedded bytes and photographic reflection')
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    if not args.bund_only and not args.views:
        parser.error('--views is required unless --bund-only is used')
    if not 0.5 <= args.dpr <= 2:
        parser.error('--dpr must be between 0.5 and 2')
    args.check_bund=args.check_bund or args.bund_only
    asyncio.run(main(args))
