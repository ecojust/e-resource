"""Real browser checks for Bund12/Bund17 photographs, LOD and hidden caching.

Examples:
  python tools/qa/photographic_facades_browser.py --url http://127.0.0.1:8000/ --output /tmp/facades
  python tools/qa/photographic_facades_browser.py --url URL --output /tmp/bund12 --targets bund12

Starts exactly one Chromium and one page. No browser is started by --help.
Six-window geometry is checked by the model export audit, not inferred from the
number of glTF primitives (the six windows can contain thirty separate panes).
A readiness timeout always fails and writes browser.json with passed:false.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

from playwright.async_api import async_playwright

os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY'] = '1'

SNAPSHOT = """()=>{
 const a=window.__SHANGHAI_APP__;if(!a)return null;
 const m=a.scene.map,t=m.transform,eye=t?.getCameraLngLat?.();
 return {mode:a.mode,districts:a.districts.length,controller:a.controller.getState?.()||
   {position:a.controller.position,bearing:a.controller.bearing,pitch:a.controller.pitch},
   camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),
     fov:m.getVerticalFieldOfView?.(),elevation:m.getCenterElevation?.(),
     eye:eye?{lng:eye.lng,lat:eye.lat,alt:t.getCameraAltitude?.()}:null},
   landmarks:a.scene.getLandmarkState(),cache:a.scene.getLandmarkCacheState(),
   assets:Object.fromEntries(['bund12','bund17','bund18'].map(id=>[id,a.scene.getLandmarkAssetState(id)])),
   stream:a.scene.getStreamingState(),source:a.scene.getCollisionState(),
   realism:a.scene.getRealismState(),exclusions:a.scene.getLandmarkExclusionState()};
}"""

AUDIT_ASSET = """async ({record,variant})=>{
 const hash=async b=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('');
 const file=variant==='full'?(record.url||record.model):record.lod_model;
 const url=new URL(file,document.baseURI).href;
 const response=await fetch(url);if(!response.ok)throw Error(`GLB ${response.status}: ${url}`);
 const buffer=await response.arrayBuffer(),view=new DataView(buffer);
 if(buffer.byteLength<28||view.getUint32(0,true)!==0x46546c67||view.getUint32(4,true)!==2||view.getUint32(8,true)!==buffer.byteLength)throw Error('Invalid GLB header');
 const n=view.getUint32(12,true),doc=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,20,n))),bin=28+n;
 const images=await Promise.all((doc.images||[]).map(async image=>{
   if(image.uri||!Number.isInteger(image.bufferView))throw Error('Photo must be embedded in GLB');
   const b=doc.bufferViews[image.bufferView],start=bin+(b.byteOffset||0);
   return {bytes:b.byteLength,mimeType:image.mimeType,sha256:await hash(buffer.slice(start,start+b.byteLength))};
 }));
 const photographicMaterials=(doc.materials||[]).filter(m=>/^PhotoFacade_/i.test(m.name||''));
 const triangles=(doc.meshes||[]).reduce((n,m)=>n+m.primitives.reduce((n,p)=>n+(doc.accessors[p.indices]?.count||0)/3,0),0);
 return {url,file,bytes:buffer.byteLength,sha256:await hash(buffer),images,triangles,
   copyright:doc.asset.copyright||'',photoMaterialNames:photographicMaterials.map(m=>m.name),
   mappedPhotoMaterialNames:photographicMaterials.filter(m=>m.pbrMetallicRoughness?.baseColorTexture).map(m=>m.name),
   externalResources:(doc.buffers||[]).some(b=>b.uri&&!b.uri.startsWith('data:'))};
}"""


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def normalized_license(value):
    return re.sub(r'[^a-z0-9]', '', str(value).lower())


def check_photo_state(record, state, variant):
    require(state.get('status') == 'loaded' and state.get('variant') == variant,
            f"{record['id']}: expected loaded {variant}: {state}")
    expected_triangles = record['triangles'] if variant == 'full' else record['lod_triangles']
    require(state.get('triangles') == expected_triangles, f"{record['id']}: rendered triangle count differs from manifest")
    if variant == 'distant' and record['photo_texture']['expected_images']['lod'] == 0:
        require(state.get('images') == [], f"{record['id']}: distant LOD must omit the high-resolution photograph")
        return {'id':record['id'],'variant':variant,'decoded_images':[],
                'manifest_triangles':expected_triangles,'photograph_omitted_by_lod':True,'passed':True}
    require(state.get('photoMeshes', 0) > 0 and len(state.get('images', [])) == 1,
            f"{record['id']}: full model must have exactly one decoded photographic texture")
    source = record['photo_texture']['orientation']
    raw = source['rawSize']
    require(source.get('uvConvention') == 'stored-pixels' and len(raw) == 2 and all(isinstance(v, int) and v > 0 for v in raw), 'Invalid photo orientation metadata')
    if record['id'] == 'bund17':
        require(source.get('exifOrientation') == 6 and raw[0] != raw[1], 'Bund17 must declare the verified non-square EXIF-6 source')
    for image in state['images']:
        decoded = [image.get('width'), image.get('height')]
        orientation = image.get('orientation')
        require(orientation and orientation.get('rawSize') == raw, f"{record['id']}: no runtime orientation evidence")
        require(orientation.get('decodedSize') == decoded, f"{record['id']}: reported decoder dimensions disagree")
        require(orientation.get('exifOrientation') == source.get('exifOrientation'), 'Runtime EXIF value differs from metadata')
        if source['exifOrientation'] == 6:
            if decoded == raw[::-1]:
                require(orientation.get('corrected') is True and orientation.get('status') == 'decoder-rotation-compensated', 'Rotated decoder pixels were not compensated')
            else:
                require(decoded == raw and orientation.get('corrected') is False and orientation.get('status') == 'decoder-kept-stored-pixels', 'Unexpected EXIF-6 decoded dimensions/status')
        else:
            require(source['exifOrientation'] == 1 and decoded == raw and orientation.get('corrected') is False and orientation.get('status') == 'identity', 'Unexpected ordinary-photo dimensions/orientation')
    return {'id':record['id'], 'variant':variant, 'decoded_images':state['images'],
            'photo_meshes':state['photoMeshes'], 'manifest_triangles':expected_triangles,
            'passed':True, 'six_window_geometry_verified_here':False}


async def wait_model(page, identity, variant, timeout):
    await page.wait_for_function("""({id,variant})=>{
      const a=__SHANGHAI_APP__,r=a.scene.getLandmarkState().find(r=>r.id===id),
        p=a.scene.getLandmarkAssetState(id),s=a.scene.getLandmarkExclusionState(),
        count=variant==='full'?1:a.landmarks.find(x=>x.id===id).photo_texture.expected_images.lod;
      return r?.status==='loaded'&&!r.loadingModel&&r.activeVariant===variant&&
        (count===1?(p.photoMeshes>0&&p.images.length===1&&p.images.every(i=>i.width>0&&i.height>0)):p.images.length===0)&&s.pendingStates===0;
    }""", arg={'id':identity,'variant':variant}, timeout=timeout)


async def rendered_frame(page, timeout):
    await page.evaluate("""timeout=>new Promise((resolve,reject)=>{
      const m=__SHANGHAI_APP__.scene.map;
      const done=()=>{clearTimeout(timer);m.off('render',done);resolve();};
      const timer=setTimeout(()=>{m.off('render',done);reject(Error('Required rendered frame timed out'));},timeout);
      m.on('render',done);m.triggerRepaint();
    })""", min(timeout, 60000))


async def capture(page, args, report, name, identity=None, variant=None, requested_camera=None):
    await rendered_frame(page, args.timeout_ms)
    state = await page.evaluate(SNAPSHOT)
    require(state and state['districts'] == 16, 'All 16 districts must remain registered')
    if identity:
        record = report['records'][identity]
        check = check_photo_state(record, state['assets'][identity], variant)
        report['checks'].append(check)
    path = args.output / f'{name}.png'
    await page.screenshot(path=str(path), timeout=min(args.timeout_ms, 90000))
    report['captures'].append({'name':name,'image':path.name,'requested_camera':requested_camera,**state})
    print('CAPTURE', name, flush=True)
    write_report(args, report)


def write_report(args, report):
    temporary = args.output / '.browser.json.tmp'
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(args.output / 'browser.json')


async def near_view(page, identity):
    await page.evaluate("""async id=>{
      const a=__SHANGHAI_APP__,r=a.landmarks.find(r=>r.id===id);
      if(!r)throw Error(`Unknown model ${id}`);
      a.syncMode('walk',false);a.controller.resetCamera();await a.selectPlace(r);
      a.scene.map.stop();a.scene.loadLandmarks();
    }""", identity)


async def photographic_view(page, record, distant=False, roof=False):
    bearing = math.radians(record['bearing'])
    outward_east, outward_north = -math.sin(bearing), -math.cos(bearing)
    along_east, along_north = math.cos(bearing), -math.sin(bearing)
    radius = max(600, record.get('lod_switch_out_m', 400) + 180) if distant else 8
    anchor = [record['lng'], record['lat']] if distant else record['walkStart']
    lateral = 0 if distant else 18
    east, north = outward_east*radius+along_east*lateral, outward_north*radius+along_north*lateral
    longitude = anchor[0] + math.degrees(east/(6378137*math.cos(math.radians(anchor[1]))))
    latitude = anchor[1] + math.degrees(north/6378137)
    target_height = record['height_m']*.82 if roof else min(16, record['height_m']*.28)
    # The six selected HSBC windows sit in the north wing, away from the
    # building-centre aim point used for ordinary street/overview navigation.
    target_along = 26 if record['id']=='bund12' and not distant else 0
    target_lng = record['lng'] + math.degrees(along_east*target_along/(6378137*math.cos(math.radians(record['lat']))))
    target_lat = record['lat'] + math.degrees(along_north*target_along/6378137)
    request = {'from':{'lng':longitude,'lat':latitude,'alt':target_height+(110 if distant else 8)},
               'to':{'lng':target_lng,'lat':target_lat,'alt':target_height},
               'fov':36.87 if distant else 48}
    await page.evaluate("""v=>{
      const a=__SHANGHAI_APP__;a.syncMode('overview',false);a.scene.map.stop();
      a.scene.map.setVerticalFieldOfView?.(v.fov);
      a.scene.setCameraFromTo({from:v.from,to:v.to});a.scene.loadLandmarks();
    }""", request)
    return request


async def audit_asset(page, record, variant, report):
    audit = await page.evaluate(AUDIT_ASSET, {'record':record,'variant':variant})
    size = record['web_bytes'] if variant == 'full' else record['lod_bytes']
    digest = record['web_sha256'] if variant == 'full' else record['lod_sha256']
    require(audit['bytes'] == size and audit['sha256'] == digest, f"{record['id']} {variant}: asset bytes/hash mismatch")
    require(audit['bytes'] < 100000000 and not audit['externalResources'], 'Invalid/non-self-contained runtime asset')
    if record['photo_texture']['expected_images']['web' if variant=='full' else 'lod'] == 1:
        require(audit['mappedPhotoMaterialNames'], 'Missing photographic material map')
        require(len(audit['images']) == 1 and audit['images'][0]['sha256'] == record['photo_texture']['sha256'], 'Embedded photograph differs from the single declared source')
        require(record['photo_texture']['author'] in audit['copyright'], 'Photographer attribution missing from GLB')
        require(normalized_license(record['photo_texture']['license']) in normalized_license(audit['copyright']), 'Photo license missing from GLB')
    else:
        require(not audit['images'] and not audit['mappedPhotoMaterialNames'], 'Distant LOD must omit the large photographic texture')
    require(audit['triangles'] == (record['triangles'] if variant == 'full' else record['lod_triangles']), 'GLB triangle count differs from manifest')
    report['asset_audits'].append({'id':record['id'],'variant':variant,**audit,'passed':True})


async def main(args):
    args.output.mkdir(parents=True, exist_ok=True)
    check_cache = not args.smoke and (args.check_cache or (set(args.targets) == {'bund12','bund17'} and not args.skip_cache))
    report = {'version':'photographic-facades-browser-v4.4','started_at':datetime.now(timezone.utc).isoformat(),
              'url':args.url,'targets':args.targets,'cache_check_enabled':check_cache,'smoke_only':args.smoke,'passed':False,
              'viewport':[1280,850],'dpr':args.dpr,'timeout_ms':args.timeout_ms,
              'records':{},'checks':[],'asset_audits':[],'captures':[],
              'page_errors':[],'shader_errors':[],'console_messages':[],'asset_errors':[],
              'requests':{},'hardware_performance_test':False,
              'scope':'One actual browser/page. Source bytes, rendered material decoding, EXIF metadata, LOD and cache lifecycle; not architectural survey accuracy.'}
    write_report(args, report)
    browser = None
    page = None
    required_urls = set()
    async with async_playwright() as playwright:
        try:
            executable = args.chromium or os.environ.get('CHROMIUM') or shutil.which('chromium')
            launch = {'headless':True,'args':['--no-sandbox','--enable-unsafe-swiftshader','--disable-dev-shm-usage']}
            if executable:
                launch['executable_path'] = executable
            browser = await playwright.chromium.launch(**launch)
            page = await browser.new_page(viewport={'width':1280,'height':850}, device_scale_factor=args.dpr)
            page.on('pageerror', lambda error:report['page_errors'].append(str(error)))
            def console(message):
                if len(report['console_messages']) < 500 and message.type in ('warning','error'):
                    report['console_messages'].append({'type':message.type,'text':message.text})
                if any(word in message.text for word in ('Shader Error','VALIDATE_STATUS','GL_INVALID_OPERATION')):
                    report['shader_errors'].append(message.text)
            page.on('console', console)
            page.on('response', lambda response:report['asset_errors'].append({'url':response.url,'status':response.status}) if response.status >= 400 else None)
            def requested(request):
                if urlsplit(request.url).path.endswith(('.glb','.hdr','.jpg','.png')):
                    report['requests'][request.url] = report['requests'].get(request.url, 0) + 1
            page.on('request', requested)
            await page.goto(args.url, wait_until='domcontentloaded', timeout=min(args.timeout_ms,60000))
            gate = page.get_by_text('Open the page', exact=False)
            if await gate.count():
                await gate.first.click(timeout=30000)
            await page.wait_for_function("()=>window.__SHANGHAI_APP__?.scene?.getLandmarkCacheState&&window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState", timeout=args.timeout_ms)
            print('APP_READY', flush=True)
            metadata = await page.evaluate("""async()=>{
              const read=async name=>{const r=await fetch(new URL(name,document.baseURI));if(!r.ok)throw Error(`${name}: ${r.status}`);return r.json();};
              return {runtime:__SHANGHAI_APP__.landmarks,landmarks:await read('data/landmarks.json'),bund:await read('data/bund/manifest.json'),base:document.baseURI};
            }""")
            async def check_record(identity):
                rows = [r for r in metadata['landmarks'] if r['id'] == identity]
                require(len(rows) == 1, f'Missing/duplicate manifest ID: {identity}')
                record = rows[0]
                require(record == next(r for r in metadata['runtime'] if r['id'] == identity), 'Runtime and fetched metadata differ')
                require(record == next(r for r in metadata['bund']['buildings'] if r['id'] == identity), 'Bund and navigation metadata differ')
                photo = record.get('photo_texture')
                require(photo and all(k in photo for k in ('image','sha256','author','license','orientation')), f'{identity}: photographic source metadata incomplete')
                require(record.get('lod_model'), f'{identity}: distant variant missing')
                if identity == 'bund12':
                    scope = photo.get('scope','')
                    six = photo.get('selected_window_count') == 6 or bool(re.search(r'\b(?:six|6)\b|六',scope,re.I) and re.search(r'window|窗',scope,re.I))
                    require(six, 'Bund12 manifest must explicitly identify the six selected windows')
                    report['bund12_window_scope'] = {'selected_window_count':6,'scope':scope,
                        'browser_claim':'Source declaration plus decoded PhotoFacade materials. Thirty panes may implement the six windows; geometric validation belongs to export/model-validation.'}
                report['records'][identity] = record
                urls = await page.evaluate("""r=>[r.url||r.model,r.lod_model,r.photo_texture.image].map(s=>new URL(s,document.baseURI).href)""",record)
                required_urls.update(urls)
                photo_asset = await page.evaluate("""async p=>{
                  const r=await fetch(new URL(p.image,document.baseURI));if(!r.ok)throw Error(`Photo ${r.status}`);
                  const b=await r.arrayBuffer(),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('');
                  return {bytes:b.byteLength,sha256:hash};
                }""", photo)
                require(photo_asset['sha256'] == photo['sha256'], 'Published source JPEG differs from manifest')
                report['checks'].append({'id':identity,'source_photo':photo_asset,'passed':True})
                for variant in ('full','distant'):
                    await audit_asset(page,record,variant,report)
            # Source/GLB checks do not mutate the scene; overlap their fetch/hash
            # round trips on the same page while the software renderer is busy.
            await asyncio.gather(*(check_record(identity) for identity in args.targets))
            if args.hero:
                await wait_model(page,'bund17','full',args.timeout_ms)
                await wait_model(page,'bund18','full',args.timeout_ms)
                await page.wait_for_function("()=>__SHANGHAI_APP__.scene.getLandmarkState().find(r=>r.id==='bund19')?.status==='loaded'&&__SHANGHAI_APP__.scene.getRealismState().lighting.reflectionSource==='photographic'",timeout=args.timeout_ms)
                await capture(page,args,report,'bund-group-initial')
            for identity in args.targets:
                record = report['records'][identity]
                await near_view(page, identity)
                await wait_model(page,identity,'full',args.timeout_ms)
                await page.wait_for_function("()=>__SHANGHAI_APP__.scene.getRealismState().lighting.reflectionSource==='photographic'",timeout=args.timeout_ms)
                await capture(page,args,report,f'{identity}-street',identity,'full')
                if args.smoke:
                    if args.window_closeups and identity in ('bund12','bund17'):
                        camera = await photographic_view(page,record)
                        await wait_model(page,identity,'full',args.timeout_ms)
                        await capture(page,args,report,f'{identity}-windows-oblique',identity,'full',camera)
                    continue
                camera = await photographic_view(page,record)
                await wait_model(page,identity,'full',args.timeout_ms)
                await capture(page,args,report,f'{identity}-windows-oblique',identity,'full',camera)
                if identity == 'bund17':
                    camera = await photographic_view(page,record,roof=True)
                    await wait_model(page,identity,'full',args.timeout_ms)
                    await capture(page,args,report,f'{identity}-roof-oblique',identity,'full',camera)
                camera = await photographic_view(page,record,distant=True)
                await wait_model(page,identity,'distant',args.timeout_ms)
                await capture(page,args,report,f'{identity}-distant-lod',identity,'distant',camera)
            if check_cache:
                # Exercise eviction of the high-resolution photos, not only the
                # intentionally texture-free distant variants just inspected.
                await near_view(page,args.targets[0])
                for identity in args.targets:
                    await wait_model(page,identity,'full',args.timeout_ms)
                    check_photo_state(report['records'][identity],await page.evaluate(
                        'id=>__SHANGHAI_APP__.scene.getLandmarkAssetState(id)',identity),'full')
                before = await page.evaluate(SNAPSHOT)
                await page.evaluate("""async()=>{
                  const a=__SHANGHAI_APP__,d=a.districts.find(r=>String(r.id)==='310120');
                  if(!d)throw Error('Fengxian district missing');a.syncMode('walk',false);a.controller.resetCamera();await a.selectPlace(d);
                }""")
                await page.wait_for_function("""ids=>{
                  const a=__SHANGHAI_APP__,s=a.scene.getLandmarkCacheState(),records=a.scene.getLandmarkState();
                  return s.hidden<=s.maxHiddenCount&&s.hiddenEstimatedBytes<=s.maxHiddenEstimatedBytes&&
                    a.scene.getLandmarkExclusionState().pendingStates===0&&
                    ids.every(id=>{const r=records.find(r=>r.id===id),p=a.scene.getLandmarkAssetState(id);return r?.status==='idle'&&!r.loadingModel&&p.photoMeshes===0&&p.images.length===0;});
                }""",arg=args.targets,timeout=args.timeout_ms)
                after = await page.evaluate(SNAPSHOT)
                require(after['cache']['evicted'] > before['cache']['evicted'],'Far navigation did not exercise eviction')
                report['cache_transition'] = {'before':before['cache'],'after':after['cache'],'targets_evicted':args.targets,'passed':True}
                await capture(page,args,report,'fengxian-after-eviction')
                for identity in args.targets:
                    await near_view(page,identity)
                    await wait_model(page,identity,'full',args.timeout_ms)
                    await capture(page,args,report,f'{identity}-returned-after-eviction',identity,'full')
            report['required_asset_errors'] = [e for e in report['asset_errors'] if e['url'] in required_urls]
            require(not report['page_errors'], f"Page errors: {report['page_errors']}")
            require(not report['shader_errors'], f"Shader errors: {report['shader_errors']}")
            require(not report['required_asset_errors'], f"Required asset errors: {report['required_asset_errors']}")
            report['finished_at'] = datetime.now(timezone.utc).isoformat()
            report['passed'] = True
            write_report(args,report)
            print('PASSED', flush=True)
        except Exception as error:
            report['passed'] = False
            report['error'] = f'{type(error).__name__}: {error}'
            if page:
                try:
                    report['failure_state'] = await asyncio.wait_for(page.evaluate(SNAPSHOT), timeout=12)
                except Exception as secondary:
                    report['failure_state_error'] = str(secondary)
                try:
                    await page.screenshot(path=str(args.output/'failure.png'),timeout=12000)
                except Exception:
                    pass
            write_report(args,report)
            raise
        finally:
            if browser:
                await browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--targets', nargs='+', choices=['bund12','bund17','bund18'], default=['bund17','bund12'])
    parser.add_argument('--hero', action='store_true', help='Capture the initial Bund walking view after its near facades and reflection are ready')
    parser.add_argument('--window-closeups', action='store_true', help='Also inspect the selected photographic windows when using --smoke')
    parser.add_argument('--smoke', action='store_true', help='Verify published bytes and near photo rendering only; skip camera sequence, rendered far LOD and cache transitions')
    parser.add_argument('--dpr', type=float, default=.75)
    parser.add_argument('--timeout-ms', type=int, default=240000)
    parser.add_argument('--chromium', help='Optional executable; otherwise CHROMIUM/PATH/Playwright default')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check-cache', action='store_true', help='Run the far-district eviction/return even with one target')
    group.add_argument('--skip-cache', action='store_true', help='Skip far-district eviction/return')
    args = parser.parse_args()
    if not .5 <= args.dpr <= 2:
        parser.error('--dpr must be between 0.5 and 2')
    if args.timeout_ms < 1000:
        parser.error('--timeout-ms must be at least 1000')
    args.targets = list(dict.fromkeys(args.targets))
    asyncio.run(main(args))
