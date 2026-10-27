#!/usr/bin/env python3
"""Actual V13 Yangpu Library acceptance. Run one browser; never changes production.

The observation timeout is a harness limit, not a product network deadline.
No routes, fake assets, source outage, model-visibility or mask mutation is used.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import time
import traceback
from urllib.parse import urljoin, urlsplit, unquote

HERE=Path(__file__).resolve().parent
IDENTITY='yangpu-library'
os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'

def need(value,message):
    if not value: raise AssertionError(message)

def utc(): return datetime.now(timezone.utc).isoformat()

def descriptor(path):
    b=Path(path).read_bytes()
    return {'file':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def metres(a,b):
    return math.hypot(math.radians(a['lng']-b['lng'])*6378137*math.cos(math.radians(b['lat'])),
                      math.radians(a['lat']-b['lat'])*6378137)

def offset(record,east,north,alt):
    return {'lng':record['lng']+math.degrees(east/(6378137*math.cos(math.radians(record['lat'])))),
            'lat':record['lat']+math.degrees(north/6378137),'alt':alt}

def proxy_options():
    name=next((n for n in ('HTTPS_PROXY','HTTP_PROXY') if os.environ.get(n)),None)
    need(name,'--use-env-proxy requires HTTPS_PROXY or HTTP_PROXY')
    value=urlsplit(os.environ[name]);need(value.scheme in ('http','https') and value.hostname,'Unsupported proxy URL')
    host=('['+value.hostname+']') if ':' in value.hostname else value.hostname
    config={'server':value.scheme+'://'+host+((':'+str(value.port)) if value.port else ''),'bypass':'localhost,127.0.0.1'}
    if value.username is not None:config['username']=unquote(value.username)
    if value.password is not None:config['password']=unquote(value.password)
    return config,{'enabled':True,'source_environment':name,'bypass':config['bypass'],
                   'credentials_supplied':value.username is not None or value.password is not None,
                   'scope':'Transport only; no URLs or response bytes rewritten.'}

def source_check(value,record):
    """Independent metric geometry comparison; MVT quantization is not surveying."""
    from shapely.geometry import shape
    from shapely.ops import transform
    lat0=record['lat'];lon0=record['lng'];scale=6378137*math.cos(math.radians(lat0))
    def project(x,y,z=None):
        # shapely 2 first offers sequences; both forms are supported.
        try:return [(v-lon0)*math.pi/180*scale for v in x],[(v-lat0)*math.pi/180*6378137 for v in y]
        except TypeError:return (x-lon0)*math.pi/180*scale,(y-lat0)*math.pi/180*6378137
    target=transform(project,shape(value['targetBoundary']))
    need(value['readiness']['ready'],'Actual source replacement still pending')
    need(value['sourcePresent'] and value['sourceLoaded'],'Actual building source is not loaded')
    rows=[];seen=set()
    for row in value['components']:
        poly=transform(project,shape(row['geometry']))
        need(poly.is_valid,'Actual source component is invalid')
        key=(str(row['id']),poly.normalize().wkb_hex)
        if key in seen:continue
        seen.add(key)
        intersection=poly.intersection(target).area
        union=poly.union(target).area
        rows.append((intersection/union if union else 0,row,poly))
    rows.sort(key=lambda r:r[0],reverse=True)
    need(rows,'No actual MVT component overlaps the target footprint')
    score,chosen,poly=rows[0]
    result={'passed':False,'mode':value['readiness']['buildingSource'],'source':value['source'],
            'source_layer':value['sourceLayer'],'unique_candidate_components':len(rows),
            'selected_id':chosen['id'],'selected_component_index':chosen['componentIndex'],
            'selected_iou':score,'target_area_m2':target.area,'component_area_m2':poly.area,
            'feature_state':chosen['featureState'],'minimum_iou':.80,
            'scope':'Actual current MVT component compared with frozen owner footprint in local metric coordinates; not a survey, no injected outage, no cross-session source fixture assumption.'}
    need(score>=.80,'Actual source component does not sufficiently match the frozen whole-library owner')
    need(chosen['featureState'].get('localModel') is True,'Actual source component is not hidden by local-model ownership')
    if value['readiness']['osm']['active']:
        need(value['residualCurrent'] and value['residualValid'],'Current OSM residual source is unavailable')
        intersections=[transform(project,shape(row['geometry'])).intersection(poly).area for row in value['residualComponents']]
        area=sum(intersections)
        result.update(residual_overlap_m2=area,residual_overlap_limit_m2=.01)
        need(area<=.01,'Target source geometry remains in the current OSM residual')
    else:
        expected=record['owner']['feature_key'].split(':',1)[1]
        result['expected_gers_id']=expected
        need(str(chosen['id'])==expected,'Actual Overture source ID differs from the frozen GERS owner')
    result['passed']=True
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--expected-landmarks',required=True,type=Path)
    parser.add_argument('--expected-registry',required=True,type=Path)
    parser.add_argument('--runtime-baseline',required=True,type=Path)
    parser.add_argument('--chromium',default='/usr/bin/chromium')
    parser.add_argument('--use-env-proxy',action='store_true')
    parser.add_argument('--timeout-ms',type=int,default=180000)
    parser.add_argument('--hold-ms',type=int,default=1000)
    parser.add_argument('--catalog-stage',choices=['pending','active'],default='pending',
                        help='Pending candidate is static-only; active requires actual catalog adoption')
    parser.add_argument('--catalog-only',action='store_true',
                        help='Active final metadata: one near screenshot, source/owner/asset/adoption checks only; no repeated W/LOD claims')
    args=parser.parse_args()
    need(not args.catalog_only or args.catalog_stage=='active','--catalog-only requires --catalog-stage active')
    need(not args.output.exists() or not any(args.output.iterdir()),'Use a fresh output directory; preserve previous failures')
    args.output.mkdir(parents=True,exist_ok=True)
    report={'schema':'yangpu-library-actual-browser-v13','building_id':IDENTITY,'started_at':utc(),
            'run_scope':'catalog-only' if args.catalog_only else 'static-and-walk','catalog_stage':args.catalog_stage,
            'passed':False,'technical_passed':False,'checks':{},'captures':[],'asset_audits':[],
            'page_errors':[],'console_errors':[],'console_warnings':[],'shader_errors':[],
            'http_errors':[],'network_failures':[],'expected_aborts':[],'model_responses':[],
            'visual_review':{'status':'pending','actually_viewed':False},
            'limits':['One selected building and current source mode only; no all-city validation.',
                      'Software renderer observations are not a hardware FPS measurement.',
                      'No forced OSM outage, corrupt-index recovery or dynamically-only catalog load is claimed.',
                      'Geometry/source-footprint match is not measured architectural accuracy.']}
    def save():
        temp=args.output/'browser.json.tmp';temp.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temp.replace(args.output/'browser.json')
    def stage(label):report['stage']=label;save();print(label,flush=True)
    def event(key,row):report[key].append(row);save()
    def capture(name,variant,near=False):
        stage('CAPTURE '+name)
        wait_ready(variant,near)
        frame()
        state=page.evaluate('()=>__YANGPU_PROBE__.snapshot()')
        audit=page.evaluate('()=>__YANGPU_PROBE__.targetAudit()')
        need(audit['passed'] and (not near or audit['hiddenNear']),name+': owner/near audit failed')
        actual=state['assets'][IDENTITY]
        need(actual['triangles']==record['triangles' if variant=='full' else 'lod_triangles'],name+': decoded triangle count differs')
        path=args.output/(name+'.png')
        row={'name':name,'variant':variant,'state':state,'target_audit':audit,'screenshot_complete':False}
        report['captures'].append(row);save()
        page.screenshot(path=str(path),timeout=min(args.timeout_ms,90000))
        row['screenshot']={**descriptor(path),'file':path.name};row['screenshot_complete']=True
        row['after']=page.evaluate('()=>__YANGPU_PROBE__.targetAudit()')
        need(row['after']['passed'] and (not near or row['after']['hiddenNear']),name+': ownership changed across screenshot')
        save()
        return row
    def wait_ready(variant,near=False):
        page.wait_for_function("""({id,variant,near})=>{
          const a=__SHANGHAI_APP__,p=__YANGPU_PROBE__,r=a.scene.getLandmarkState().find(x=>x.id===id),s=a.scene.getLandmarkAssetState(id);
          if(!p.sourceReadiness().ready||r?.status!=='loaded'||r.loadingModel||s.variant!==variant||!s.visible||p.local.suppression.pending.size)return false;
          const v=p.targetAudit();return v.passed&&v.active&&(!near||v.hiddenNear);
        }""",arg={'id':IDENTITY,'variant':variant,'near':near},timeout=args.timeout_ms,polling=250)
    def frame():
        page.evaluate("""timeout=>new Promise((resolve,reject)=>{
          const m=__SHANGHAI_APP__.scene.map;const done=()=>{clearTimeout(timer);m.off('render',done);resolve()};
          const timer=setTimeout(()=>{m.off('render',done);reject(Error('Actual render timed out'))},timeout);m.on('render',done);m.triggerRepaint();
        })""",min(args.timeout_ms,90000))
    def near_view():
        page.evaluate("""async id=>{const a=__SHANGHAI_APP__,r=a.landmarks.find(r=>r.id===id);a.syncMode('walk',false);a.controller.resetCamera();await a.selectPlace(r);a.scene.map.stop();a.scene.loadLandmarks();}""",IDENTITY)
    def camera(east,north,alt,to_alt,fov=48,to_east=0,to_north=0):
        request={'from':offset(record,east,north,alt),'to':offset(record,to_east,to_north,to_alt),'fov':fov}
        page.evaluate("""v=>{const a=__SHANGHAI_APP__;a.syncMode('overview',false);a.scene.map.stop();a.scene.map.setVerticalFieldOfView(v.fov);a.scene.setCameraFromTo({from:v.from,to:v.to});a.scene.loadLandmarks();}""",request)
        return request
    page=None;browser=None
    try:
        baseline=json.loads(args.runtime_baseline.read_text())
        need(baseline['file_count']==len(baseline['files'])==31,'Require exact fresh 31-file runtime baseline')
        pinned_nav=json.loads(args.expected_landmarks.read_text());pinned_registry=json.loads(args.expected_registry.read_text())
        record=next(r for r in pinned_nav if r['id']==IDENTITY)
        need(len(pinned_nav)==len({r['id'] for r in pinned_nav})==31,'Require 31 unique navigation records')
        need(record['kind']=='building' and len(record['owner']['preserve_neighbor_local_ids'])==9,'Require whole-library owner and nine preserved neighbors')
        report.update(web_sha256=record['web_sha256'],lod_sha256=record['lod_sha256'],
                      runtime_baseline_sha256=descriptor(args.runtime_baseline)['sha256'],
                      expected_landmarks=descriptor(args.expected_landmarks),expected_registry=descriptor(args.expected_registry),
                      tools=[descriptor(p) for p in sorted(HERE.glob('*.js'))]+[descriptor(Path(__file__))])
        base=args.url.split('#',1)[0].split('?',1)[0]
        base=base.rsplit('/',1)[0]+'/' if base.endswith('.html') else base.rstrip('/')+'/'
        target_urls={urljoin(base,record['assets'][role]['file']) for role in ['web','lod']}
        proxy,report['network']=proxy_options() if args.use_env_proxy else (None,{'enabled':False})
        def console(message):
            if message.type not in ('error','warning'):return
            row={'type':message.type,'text':message.text,'location':message.location}
            key='shader_errors' if any(s in message.text.lower() for s in ('shader error','shader failed','webglprogram','context lost')) else 'console_errors' if message.type=='error' else 'console_warnings'
            event(key,row)
        def failed(request):
            event('expected_aborts' if 'ERR_ABORTED' in str(request.failure) else 'network_failures',{'url':request.url,'error':request.failure})
        def response(value):
            if value.status>=400:event('http_errors',{'url':value.url,'status':value.status})
            if value.url in target_urls:event('model_responses',{'url':value.url,'status':value.status})
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            try:
                stage('BROWSER_START')
                browser=playwright.chromium.launch(executable_path=args.chromium,headless=True,
                    args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'])
                options={'viewport':{'width':1040,'height':760},'device_scale_factor':1}
                if proxy:options['proxy']=proxy
                context=browser.new_context(**options);page=context.new_page();page.set_default_timeout(args.timeout_ms)
                page.on('pageerror',lambda e:event('page_errors',str(e)));page.on('console',console)
                page.on('requestfailed',failed);page.on('response',response)
                page.add_init_script("window.__CONTEXT_LOSSES__=0;window.__KEYBOARD_SMOKE_EVENTS__=[];document.addEventListener('webglcontextlost',()=>window.__CONTEXT_LOSSES__++,true);for(const type of ['keydown','keyup'])window.addEventListener(type,event=>{if(event.code==='KeyW')window.__KEYBOARD_SMOKE_EVENTS__.push({type,code:event.code,isTrusted:event.isTrusted,at:performance.now()})},{capture:true,passive:true});")
                page.goto(urljoin(base,'index.html')+'#landmark='+IDENTITY+'&mode=walk',wait_until='domcontentloaded',timeout=args.timeout_ms)
                link=page.get_by_role('link',name='Open the page')
                if link.count():link.click()
                page.wait_for_function('()=>Boolean(window.__SHANGHAI_APP__?.controller)',timeout=args.timeout_ms)
                stage('METADATA_AND_RUNTIME')
                fetched=page.evaluate((HERE/'fetch-json.js').read_text(),{'registry':'data/precise-buildings-v6.json','landmarks':'data/landmarks.json'})
                report['actual_metadata']={k:{x:y for x,y in v.items() if x!='data'} for k,v in fetched.items()}
                need(fetched['registry']['sha256']==report['expected_registry']['sha256'],'Served registry is not pinned candidate')
                need(fetched['landmarks']['sha256']==report['expected_landmarks']['sha256'],'Served navigation is not pinned candidate')
                runtime=page.evaluate("""async files=>Promise.all(files.map(async f=>{const r=await fetch(new URL(f.file,document.baseURI));if(!r.ok)throw Error(f.file+': '+r.status);const b=await r.arrayBuffer();return {file:f.file,bytes:b.byteLength,sha256:Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('')}}))""",baseline['files'])
                report['actual_runtime']=runtime;need(runtime==baseline['files'],'Actual 31 runtime files differ from completed V12')
                report['checks']['runtime_unchanged']=True;save()
                report['streaming_probe']=page.evaluate((HERE/'streaming-probe.js').read_text(),fetched['registry']['data'])
                report['target_probe']=page.evaluate((HERE/'target-probe.js').read_text(),record)
                stage('FULL_NEAR')
                near_view();capture('east-entry-walk','full',True)
                report['checks']['full_loaded']=True
                if args.catalog_stage=='active':
                    page.wait_for_function("""()=>{const v=__YANGPU_PROBE__.catalogState();return v.entries.some(e=>e.adoptedIds.includes('yangpu-library'))}""",timeout=args.timeout_ms)
                catalog=page.evaluate('()=>__YANGPU_PROBE__.catalogState()');report['catalog_observation']=catalog
                need(catalog['staticOwner'] and catalog['runtimeTargetCount']==catalog['navigationTargetCount']==1,'Catalog duplicated static target')
                if args.catalog_stage=='active':
                    entry=next(e for e in catalog['entries'] if IDENTITY in e['adoptedIds'])
                    need(entry['id']==record['owner']['macro_id'] and len(entry['targetModels'])==1,'Catalog target macro/record differs')
                    need(entry['targetModels'][0]['web_sha256']==record['web_sha256'] and entry['targetModels'][0]['lod_sha256']==record['lod_sha256'],'Catalog adopted different asset bytes')
                    report['checks']['catalog_static_adoption']=True
                else:
                    need(not record.get('accepted') and record.get('candidate_only') is True,'Pending catalog phase requires unaccepted static candidate')
                    need(record['owner']['macro_id'] not in catalog['catalogMacroIds'],'Unaccepted candidate unexpectedly added to active catalog')
                    need(not any(IDENTITY in e['modelIds'] or IDENTITY in e['adoptedIds'] for e in catalog['entries']),'Unaccepted candidate has an active catalog session')
                    report['catalog_adoption_status']='pending; this static-only run makes no adoption claim'
                    report['checks']['candidate_static_only']=True
                page.wait_for_function('()=>{const r=__YANGPU_PROBE__.sourceReadiness();return r.ready&&r.sourcePresent&&r.sourceLoaded}',timeout=args.timeout_ms)
                source=page.evaluate('()=>__YANGPU_PROBE__.sourceObservation()');report['actual_source_observation']=source;save()
                report['source_check']=source_check(source,record);report['checks']['source_owner']=True;save()
                audit=page.evaluate((HERE/'audit-asset.js').read_text(),{'record':record,'variant':'full'})
                need(audit['bytes']==record['web_bytes'] and audit['sha256']==record['web_sha256'] and audit['triangles']==record['triangles'],'Actual full GLB differs')
                report['asset_audits'].append(audit);save()
                if not args.catalog_only:
                    # View dimensions come from the frozen source-owner bounds, never from old-building constants.
                    west,south,east,north=record['bbox']
                    width=metres({'lng':east,'lat':record['lat']},{'lng':west,'lat':record['lat']})
                    length=metres({'lng':record['lng'],'lat':north},{'lng':record['lng'],'lat':south})
                    span=max(width,length);height=record['height_m']
                    request=camera(width*1.2,length*.9,max(height*2.7,span*.75),height*.28,50)
                    row=capture('east-north-courtyards','full');row['requested_camera']=request;save()
                    request=camera(0,-85,12,5,52,to_east=.8,to_north=-40.91)
                    row=capture('south-entry','full');row['requested_camera']=request;save()
                    stage('LOD')
                    far=max(600,record.get('lod_switch_out_m',400)+180)
                    request=camera(far,0,height+110,height*.3,36.87)
                    row=capture('distant-lod','distant');row['requested_camera']=request
                    need(metres(row['state']['camera']['eye'],record)>record.get('lod_switch_out_m',400),'Actual camera failed to cross outer LOD threshold')
                    audit=page.evaluate((HERE/'audit-asset.js').read_text(),{'record':record,'variant':'distant'})
                    need(audit['bytes']==record['lod_bytes'] and audit['sha256']==record['lod_sha256'] and audit['triangles']==record['lod_triangles'],'Actual LOD GLB differs')
                    report['asset_audits'].append(audit);report['checks']['lod_loaded']=True;save()
                    stage('OWNER_RELEASE')
                    release_request={'center':offset(record,18000,0,0),'zoom':15,'pitch':50,'bearing':20}
                    release_distance=metres(release_request['center'],record)
                    report['release_navigation']={'requested':release_request,'requested_distance_m':release_distance,'required_distance_above_m':12300}
                    need(release_distance>12300,'Release request does not exceed the 12000m overview range plus 300m hysteresis')
                    page.evaluate("""v=>{const a=__SHANGHAI_APP__;a.syncMode('overview',false);a.scene.map.stop();a.scene.map.jumpTo({center:[v.center.lng,v.center.lat],zoom:v.zoom,pitch:v.pitch,bearing:v.bearing});a.scene.loadLandmarks()}""",release_request)
                    actual_release=page.evaluate("()=>{const a=__SHANGHAI_APP__,m=a.scene.map,c=m.getCenter();return {mode:a.mode,center:{lng:c.lng,lat:c.lat},zoom:m.getZoom()}}")
                    report['release_navigation']['actual']=actual_release
                    report['release_navigation']['actual_distance_m']=metres(actual_release['center'],record);save()
                    need(actual_release['mode']=='overview' and actual_release['zoom']==15 and report['release_navigation']['actual_distance_m']>12300,'Actual release view did not exceed the overview hysteresis range')
                    page.wait_for_function("""()=>{const p=__YANGPU_PROBE__,v=p.targetAudit();return !v.active&&v.passed&&!p.local.suppression.pending.size&&!v.online.keys.length&&(!v.parent||!v.parent.preciseOwners.some(([id])=>id==='yangpu-library'))}""",timeout=args.timeout_ms)
                    report['release_state']=page.evaluate('()=>__YANGPU_PROBE__.snapshot()');report['release_target']=page.evaluate('()=>__YANGPU_PROBE__.targetAudit()');save()
                    near_view();capture('return-full','full',True)
                    report['checks'].update(returned_full=True,owner_lifecycle=True,neighbors_preserved=True);save()
                    stage('TRUSTED_KEYBOARD')
                    snapshot=(HERE/'keyboard-snapshot.js').read_text()
                    page.locator('canvas.maplibregl-canvas').focus()
                    idle=page.evaluate(snapshot,IDENTITY);page.wait_for_timeout(1000);before=page.evaluate(snapshot,IDENTITY)
                    report['keyboard']={'idle':idle,'before':before};save()
                    need(metres(idle['position'],before['position'])<=.05,'Idle start adjusted before keyboard measurement')
                    need(before['mode']=='walk' and before['controller']['enabled'] and before['avatar']['effectiveVisible'],'Walk/avatar not ready')
                    need(not before['controller']['keys'] and before['controller']['moveVector']=={'x':0,'y':0} and not before['controller']['manualRun'],'Another movement input is active')
                    try:
                        page.keyboard.down('KeyW');start=time.monotonic()
                        report['keyboard']['during']=page.evaluate("()=>({keys:[...__SHANGHAI_APP__.controller.keys],events:__KEYBOARD_SMOKE_EVENTS__.slice()})")
                        page.wait_for_timeout(max(0,args.hold_ms-(time.monotonic()-start)*1000))
                    finally:page.keyboard.up('KeyW')
                    after=page.evaluate(snapshot,IDENTITY);report['keyboard']['immediate_after']=after
                    samples=[]
                    for _ in range(3):
                        page.wait_for_timeout(500);samples.append(page.evaluate(snapshot,IDENTITY))
                        report['keyboard']['post_keyup_samples']=samples;save()
                    need(all(s['position']==after['position'] and s['controller']['distance']==after['controller']['distance'] for s in samples),'Player moved after key release')
                    moved=metres(before['position'],after['position']);distance=after['controller']['distance']-before['controller']['distance']
                    events=after['keyboardEvents'][len(before['keyboardEvents']):]
                    camera_distance=metres(after['camera']['actualMapEye'],after['position'])
                    report['keyboard']['measurement']={'displacement_m':moved,'controller_distance_m':distance,'camera_player_distance_m':camera_distance,'events':events}
                    need(any(e['type']=='keydown' and e['isTrusted'] for e in events) and any(e['type']=='keyup' and e['isTrusted'] for e in events),'No trusted W keydown/up')
                    need('KeyW' in report['keyboard']['during']['keys'] and 'KeyW' not in after['controller']['keys'],'Real controller did not accept/release W')
                    need(moved>.10 and distance>.10 and moved<=distance+.10,'No accounted visible keyboard displacement')
                    need(camera_distance>.5 and after['avatar']['effectiveVisible'],'Actual third-person avatar/camera not separate')
                    need(before['controller']['spawnGeneration']==after['controller']['spawnGeneration'],'Navigation changed during input')
                    capture('after-W','full',True)
                    report['checks'].update(keyboard_movement=True,post_keyup_stopped=True)
                report['webgl_context_losses']=page.evaluate('window.__CONTEXT_LOSSES__')
                need(report['webgl_context_losses']==0,'WebGL context was lost')
                need(not(report['page_errors'] or report['shader_errors'] or report['console_errors']),'Browser/runtime errors occurred')
                need(not [r for r in report['http_errors'] if r['url'].startswith(base) or r['url'] in target_urls],'Actual local/model HTTP failure')
                need(not [r for r in report['network_failures'] if r['url'].startswith(base) or r['url'] in target_urls],'Actual local/model request failure')
                need(all(r['screenshot_complete'] for r in report['captures']) and len(report['captures'])==(1 if args.catalog_only else 6),'Required screenshots incomplete')
                report['technical_passed']=report['passed']=True;save()
            except Exception as error:
                report['technical_passed']=report['passed']=False
                report['error']={'message':str(error),'traceback':traceback.format_exc()};save()
                if page:
                    try:page.keyboard.up('KeyW')
                    except Exception:pass
                    try:report['failure_snapshot']=page.evaluate('()=>window.__YANGPU_PROBE__?.snapshot()||null');save()
                    except Exception as exc:report['failure_snapshot_error']=str(exc)
                    try:
                        path=args.output/'failure.png';page.screenshot(path=str(path),timeout=30000)
                        report['failure_screenshot']={**descriptor(path),'file':path.name}
                    except Exception as exc:report['failure_screenshot_error']=str(exc)
            finally:
                if browser:browser.close()
    except Exception as error:
        report['technical_passed']=report['passed']=False
        report['error']={'message':str(error),'traceback':traceback.format_exc()}
    report['finished_at']=utc();report['stage']='FINISHED';save()
    print(json.dumps({'report':str(args.output/'browser.json'),'technical_passed':report['technical_passed'],'visual_review':'pending'}),flush=True)
    return 0 if report['technical_passed'] else 1

if __name__=='__main__':raise SystemExit(main())
