#!/usr/bin/env python3
"""Focused actual V15 model acceptance, no mocks or production mutation.

Run only after root READY. Camera navigation uses normal scene methods and ranges.
Read-only probes capture runtime objects through synchronous restored getter
wrappers; no feature state, model visibility, deadline or quality is overridden.
"""
from __future__ import annotations
import argparse, json, math, os, time, traceback
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs
from helpers import need, utc, descriptor, metres, offset, proxy_options, source_check

HERE=Path(__file__).resolve().parent
os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--url',required=True)
 p.add_argument('--output',required=True,type=Path)
 p.add_argument('--id',default='baoshan-confucian-dacheng-hall')
 p.add_argument('--expected-landmarks',required=True,type=Path)
 p.add_argument('--expected-registry',required=True,type=Path)
 p.add_argument('--runtime-baseline',required=True,type=Path)
 p.add_argument('--views',required=True,type=Path,help='Reviewed front/rear relative camera requests; see README')
 p.add_argument('--expected-count',type=int,default=32)
 p.add_argument('--runtime-count',type=int,default=35)
 p.add_argument('--neighbor-count',type=int,default=8)
 p.add_argument('--chromium',default='/usr/bin/chromium')
 p.add_argument('--use-env-proxy',action='store_true')
 p.add_argument('--timeout-ms',type=int,default=180000,help='Observation limit; never a product deadline')
 p.add_argument('--hold-ms',type=int,default=1000)
 args=p.parse_args();ID=args.id
 need(not args.output.exists() or not any(args.output.iterdir()),'Use a fresh output directory; retain previous runs')
 args.output.mkdir(parents=True,exist_ok=True)
 report={'schema':'single-building-actual-browser-v15','building_id':ID,'started_at':utc(),
  'passed':False,'technical_passed':False,'checks':{},'captures':[],'asset_audits':[],
  'page_errors':[],'console_errors':[],'console_warnings':[],'shader_errors':[],
  'http_errors':[],'network_failures':[],'expected_aborts':[],'model_responses':[],'model_requests':[],
  'visual_review':{'status':'pending','actually_viewed':False},
  'limits':['One target and current actual online building source mode only; no all-city model validation.',
            'Static-model ownership lifecycle is tested; dynamic-only catalog loading is not claimed.',
            'Software rendering is not a hardware FPS measurement.',
            'Mapped source-footprint match is not surveyed architectural accuracy.',
            'Screenshots need root visual review; this report records technical checks.']}
 def save():
  tmp=args.output/'browser.json.tmp';tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(args.output/'browser.json')
 def stage(label):report['stage']=label;save();print(label,flush=True)
 def event(key,row):report[key].append(row);save()
 def wait_ready(variant,near=False):
  page.wait_for_function("""({id,variant,near})=>{
   const a=__SHANGHAI_APP__,p=__BUILDING_PROBE__,r=a.scene.getLandmarkState().find(x=>x.id===id),s=a.scene.getLandmarkAssetState(id);
   if(!p.sourceReadiness().ready||r?.status!=='loaded'||r.loadingModel||s.variant!==variant||!s.visible||p.local.suppression.pending.size)return false;
   const v=p.targetAudit();return v.passed&&v.active&&(!near||v.hiddenNear);
  }""",arg={'id':ID,'variant':variant,'near':near},timeout=args.timeout_ms,polling=300)
 def frame():
  page.evaluate("""timeout=>new Promise((resolve,reject)=>{
   const m=__SHANGHAI_APP__.scene.map;const done=()=>{clearTimeout(timer);m.off('render',done);resolve()};
   const timer=setTimeout(()=>{m.off('render',done);reject(Error('Actual render timed out'))},timeout);m.on('render',done);m.triggerRepaint();
  })""",min(args.timeout_ms,90000))
 def snapshot():return page.evaluate('()=>__BUILDING_PROBE__.snapshot()')
 def audit():return page.evaluate('()=>__BUILDING_PROBE__.targetAudit()')
 def capture(name,variant,near=False):
  stage('CAPTURE '+name);wait_ready(variant,near);frame()
  state=snapshot();actual=audit();need(actual['passed'] and (not near or actual['hiddenNear']),name+': owner/near audit failed')
  need(state['assets'][ID]['triangles']==record['triangles' if variant=='full' else 'lod_triangles'],name+': decoded triangles differ')
  path=args.output/(name+'.png');row={'name':name,'variant':variant,'state':state,'target_audit':actual,'screenshot_complete':False}
  report['captures'].append(row);save()
  page.screenshot(path=str(path),timeout=min(args.timeout_ms,90000));row['screenshot']={**descriptor(path),'file':path.name};row['screenshot_complete']=True
  row['after']=audit();need(row['after']['passed'] and (not near or row['after']['hiddenNear']),name+': ownership changed across screenshot');save();return row
 def near_view():
  page.evaluate("""async id=>{const a=__SHANGHAI_APP__,r=a.landmarks.find(r=>r.id===id);a.syncMode('walk',false);a.controller.resetCamera();await a.selectPlace(r);a.scene.map.stop();a.scene.loadLandmarks();}""",ID)
 def camera(view):
  request={'from':offset(record,view['east'],view['north'],view['alt']),
           'to':offset(record,view.get('to_east',0),view.get('to_north',0),view['to_alt']),'fov':view.get('fov',48)}
  page.evaluate("""v=>{const a=__SHANGHAI_APP__;a.syncMode('overview',false);a.scene.map.stop();a.scene.map.setVerticalFieldOfView(v.fov);a.scene.setCameraFromTo({from:v.from,to:v.to});a.scene.loadLandmarks();}""",request)
  return request
 def asset_check(variant):
  actual=page.evaluate((HERE/'audit-asset.js').read_text(),{'record':record,'variant':variant});role='web' if variant=='full' else 'lod'
  need(actual['bytes']==record[role+'_bytes'] and actual['sha256']==record[role+'_sha256'],'Served '+role+' asset bytes differ')
  need(actual['triangles']==record['triangles' if variant=='full' else 'lod_triangles'],'Decoded '+role+' triangles differ')
  need(actual['bytes']<100_000_000 and not actual['externalResources'],'Model file too large or external dependency');report['asset_audits'].append(actual);save()
 page=None;browser=None
 try:
  baseline=json.loads(args.runtime_baseline.read_text());nav=json.loads(args.expected_landmarks.read_text());registry=json.loads(args.expected_registry.read_text());views=json.loads(args.views.read_text())
  need(baseline['file_count']==len(baseline['files'])==args.runtime_count,'Unexpected runtime baseline count')
  need(len(nav)==len({r['id'] for r in nav})==args.expected_count,'Unexpected unique navigation count')
  record=next(r for r in nav if r['id']==ID);need(record['kind']=='building','Expected individual building')
  need(len(record['owner']['preserve_neighbor_local_ids'])==args.neighbor_count,'Unexpected preserved neighbor count')
  need(set(views)=={'front','rear'},'Exactly reviewed front/rear camera requests required')
  expected_pose=record.get('navigation',{}).get('walkStart',record['walkStart']);pose={'lng':expected_pose[0],'lat':expected_pose[1]}
  report.update(web_sha256=record['web_sha256'],lod_sha256=record['lod_sha256'],runtime_baseline_sha256=descriptor(args.runtime_baseline)['sha256'],
   expected_landmarks=descriptor(args.expected_landmarks),expected_registry=descriptor(args.expected_registry),reviewed_views=descriptor(args.views),
   tools=[descriptor(f) for f in sorted(HERE.glob('*.js'))]+[descriptor(HERE/'helpers.py'),descriptor(Path(__file__))])
  base=args.url.split('#',1)[0].split('?',1)[0];base=base.rsplit('/',1)[0]+'/' if base.endswith('.html') else base.rstrip('/')+'/'
  target_urls={urljoin(base,record['assets'][role]['file']) for role in ('web','lod')}
  proxy,report['network']=proxy_options() if args.use_env_proxy else (None,{'enabled':False})
  def console(message):
   if message.type not in ('error','warning'):return
   row={'type':message.type,'text':message.text,'location':message.location};key='shader_errors' if any(s in message.text.lower() for s in ('shader error','shader failed','webglprogram','context lost')) else 'console_errors' if message.type=='error' else 'console_warnings';event(key,row)
  def failed(request):event('expected_aborts' if 'ERR_ABORTED' in str(request.failure) else 'network_failures',{'url':request.url,'error':request.failure})
  def response(value):
   if value.status>=400:event('http_errors',{'url':value.url,'status':value.status})
   if value.url in target_urls:event('model_responses',{'url':value.url,'status':value.status})
  def request(value):
   if '.glb' in value.url:event('model_requests',value.url)
  from playwright.sync_api import sync_playwright
  with sync_playwright() as playwright:
   try:
    stage('BROWSER_START');browser=playwright.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'])
    options={'viewport':{'width':1040,'height':760},'device_scale_factor':1}
    if proxy:options['proxy']=proxy
    context=browser.new_context(**options);page=context.new_page();page.set_default_timeout(args.timeout_ms)
    page.on('pageerror',lambda e:event('page_errors',str(e)));page.on('console',console);page.on('requestfailed',failed);page.on('response',response);page.on('request',request)
    page.add_init_script("window.__CONTEXT_LOSSES__=0;window.__KEYBOARD_SMOKE_EVENTS__=[];document.addEventListener('webglcontextlost',()=>window.__CONTEXT_LOSSES__++,true);for(const type of ['keydown','keyup'])window.addEventListener(type,event=>{if(event.code==='KeyW')window.__KEYBOARD_SMOKE_EVENTS__.push({type,code:event.code,isTrusted:event.isTrusted,at:performance.now()})},{capture:true,passive:true});")
    stage('DIRECTORY_AND_GENUINE_CLICK');page.goto(urljoin(base,'landmarks.html'),wait_until='domcontentloaded',timeout=args.timeout_ms)
    links=page.locator('a[data-landmark]');hrefs=links.evaluate_all('(xs)=>xs.map(x=>x.getAttribute("href"))');ids=[parse_qs(urlsplit(h).fragment)['landmark'][0] for h in hrefs]
    need(len(ids)==len(set(ids))==args.expected_count and set(ids)=={r['id'] for r in nav},'Directory IDs/count differ')
    need(all(parse_qs(urlsplit(h).fragment).get('mode')==['walk'] for h in hrefs),'Directory mode must be walk')
    report['directory']={'count':len(ids),'ids':ids,'all_walk':True};save()
    page.locator('a[data-landmark="'+ID+'"]').click()
    page.wait_for_function('()=>Boolean(window.__SHANGHAI_APP__?.controller)&&__SHANGHAI_APP__.mode==="walk"&&document.getElementById("loading").classList.contains("loaded")',timeout=args.timeout_ms)
    report['initial_direct_link']=page.evaluate('()=>({hash:location.hash,name:document.getElementById("location-name").textContent,position:{...__SHANGHAI_APP__.controller.position}})')
    direct=report['initial_direct_link'];direct['distance_m']=metres(direct['position'],pose);direct['first_model_requests']=report['model_requests'][:8]
    need(parse_qs(urlsplit(page.url).fragment).get('landmark')==[ID] and direct['distance_m']<1,'Actual directory click did not reach reviewed start');report['checks']['directory_direct_link']=True;save()
    stage('METADATA_AND_RUNTIME')
    fetched=page.evaluate((HERE/'fetch-json.js').read_text(),{'registry':'data/precise-buildings-v6.json','landmarks':'data/landmarks.json'});report['actual_metadata']={k:{x:y for x,y in v.items() if x!='data'} for k,v in fetched.items()}
    need(fetched['registry']['sha256']==report['expected_registry']['sha256'] and fetched['landmarks']['sha256']==report['expected_landmarks']['sha256'],'Served metadata differs from pinned candidate')
    runtime=page.evaluate("""async files=>Promise.all(files.map(async f=>{const r=await fetch(new URL(f.file,document.baseURI));if(!r.ok)throw Error(f.file+': '+r.status);const b=await r.arrayBuffer();return {file:f.file,bytes:b.byteLength,sha256:Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('')}}))""",baseline['files'])
    report['actual_runtime']=runtime;need(runtime==baseline['files'],'Actual runtime differs from pinned completed V14');report['checks']['runtime_unchanged']=True;save()
    report['streaming_probe']=page.evaluate((HERE/'streaming-probe.js').read_text(),fetched['registry']['data']);report['target_probe']=page.evaluate((HERE/'target-probe.js').read_text(),record)
    stage('FULL_NEAR_SOURCE_OWNER');wait_ready('full',True)
    report['initial_full']=snapshot();report['initial_target']=audit();need(report['initial_full']['assets'][ID]['triangles']==record['triangles'],'Full actual triangles differ');report['checks']['full_loaded']=True
    page.wait_for_function('()=>{const r=__BUILDING_PROBE__.sourceReadiness();return r.ready&&r.sourcePresent&&r.sourceLoaded}',timeout=args.timeout_ms)
    source=page.evaluate('()=>__BUILDING_PROBE__.sourceObservation()');report['actual_source_observation']=source;save();report['source_check']=source_check(source,record);report['checks']['source_owner']=True
    catalog=page.evaluate('()=>__BUILDING_PROBE__.catalogState()');report['catalog_observation']=catalog
    need(catalog['staticOwner'] and catalog['runtimeTargetCount']==catalog['navigationTargetCount']==1,'Target is not a unique static owner')
    asset_check('full')
    keyboard=(HERE/'keyboard-snapshot.js').read_text();safe=page.evaluate(keyboard,ID);report['reviewed_start']=safe
    from shapely.geometry import shape,Point
    need(not shape(record['confirmed_boundary']).covers(Point(safe['position']['lng'],safe['position']['lat'])),'Reviewed start intersects source target boundary')
    need(safe['ground']['loadedSourceCollision'] is None and safe['ground']['localCollision'] is None,'Reviewed start collides with loaded building/water/local obstacle')
    need(metres(safe['position'],pose)<1,'Reviewed start drifted during loading');report['checks']['reviewed_start_safe']=True;save()
    for name in ('front','rear'):
     request=camera(views[name]);row=capture(name,'full');row['requested_camera']=request;save()
    stage('DISTANT_LOD');far=max(600,record.get('lod_switch_out_m',400)+180)
    request=camera({'east':far,'north':0,'alt':record['height_m']+110,'to_alt':record['height_m']*.3,'fov':36.87})
    row=capture('distant-lod','distant');row['requested_camera']=request
    need(metres(row['state']['camera']['eye'],record)>record.get('lod_switch_out_m',400),'Camera did not cross outer LOD threshold');asset_check('distant');report['checks']['lod_loaded']=True;save()
    stage('OWNER_RELEASE');release={'center':offset(record,18000,0,0),'zoom':15,'pitch':50,'bearing':20}
    report['release_navigation']={'requested':release,'required_distance_above_m':12300}
    page.evaluate("""v=>{const a=__SHANGHAI_APP__;a.syncMode('overview',false);a.scene.map.stop();a.scene.map.jumpTo({center:[v.center.lng,v.center.lat],zoom:v.zoom,pitch:v.pitch,bearing:v.bearing});a.scene.loadLandmarks()}""",release)
    actual=page.evaluate("()=>{const a=__SHANGHAI_APP__,m=a.scene.map,c=m.getCenter();return {mode:a.mode,center:{lng:c.lng,lat:c.lat},zoom:m.getZoom()}}")
    report['release_navigation']['actual']=actual;report['release_navigation']['actual_distance_m']=metres(actual['center'],record);save()
    need(actual['mode']=='overview' and actual['zoom']==15 and metres(actual['center'],record)>12300,'Actual release camera did not cross overview range+hysteresis')
    page.wait_for_function("""id=>{const p=__BUILDING_PROBE__,v=p.targetAudit();return !v.active&&v.passed&&!p.local.suppression.pending.size&&!v.online.keys.length&&(!v.parent||!v.parent.preciseOwners.some(([key])=>key===id))}""",arg=ID,timeout=args.timeout_ms)
    report['release_state']=snapshot();report['release_target']=audit();save()
    stage('RETURN_FULL');near_view();wait_ready('full',True)
    report['return_state']=snapshot();report['return_target']=audit();need(report['return_target']['neighborsExact'],'Returned near group lost preserved neighbors')
    report['checks'].update(returned_full=True,owner_lifecycle=True,neighbors_preserved=True);save()
    stage('TRUSTED_KEYBOARD');page.locator('canvas.maplibregl-canvas').focus()
    idle=page.evaluate(keyboard,ID);page.wait_for_timeout(750);before=page.evaluate(keyboard,ID);report['keyboard']={'idle':idle,'before':before};save()
    need(metres(idle['position'],before['position'])<=.05,'Idle start adjusted before keyboard measurement')
    need(before['mode']=='walk' and before['controller']['enabled'] and before['avatar']['effectiveVisible'],'Walk/avatar not ready')
    need(not before['controller']['keys'] and before['controller']['moveVector']=={'x':0,'y':0} and not before['controller']['manualRun'],'Another movement input is active')
    try:
     page.keyboard.down('KeyW');started=time.monotonic();report['keyboard']['during']=page.evaluate("()=>({keys:[...__SHANGHAI_APP__.controller.keys],events:__KEYBOARD_SMOKE_EVENTS__.slice()})");page.wait_for_timeout(max(0,args.hold_ms-(time.monotonic()-started)*1000))
    finally:page.keyboard.up('KeyW')
    after=page.evaluate(keyboard,ID);report['keyboard']['immediate_after']=after;samples=[]
    for _ in range(3):
     page.wait_for_timeout(500);samples.append(page.evaluate(keyboard,ID));report['keyboard']['post_keyup_samples']=samples;save()
    need(all(s['position']==after['position'] and s['controller']['distance']==after['controller']['distance'] for s in samples),'Player moved after key release')
    moved=metres(before['position'],after['position']);distance=after['controller']['distance']-before['controller']['distance'];events=after['keyboardEvents'][len(before['keyboardEvents']):];camera_distance=metres(after['camera']['actualMapEye'],after['position'])
    report['keyboard']['measurement']={'displacement_m':moved,'controller_distance_m':distance,'camera_player_distance_m':camera_distance,'events':events}
    need(any(e['type']=='keydown' and e['isTrusted'] for e in events) and any(e['type']=='keyup' and e['isTrusted'] for e in events),'No trusted W keydown/up')
    need('KeyW' in report['keyboard']['during']['keys'] and 'KeyW' not in after['controller']['keys'],'Controller did not accept/release W')
    need(moved>.10 and distance>.10 and moved<=distance+.10,'No accounted trusted keyboard displacement')
    need(camera_distance>.5 and after['avatar']['effectiveVisible'],'Third-person camera/avatar not separate')
    need(before['controller']['spawnGeneration']==after['controller']['spawnGeneration'],'Navigation changed during input')
    need(after['ground']['loadedSourceCollision'] is None and after['ground']['localCollision'] is None,'Trusted movement ended inside collision')
    report['checks'].update(keyboard_movement=True,post_keyup_stopped=True);capture('return-full-after-W','full',True)
    report['webgl_context_losses']=page.evaluate('window.__CONTEXT_LOSSES__');need(report['webgl_context_losses']==0,'WebGL context was lost')
    need(not(report['page_errors'] or report['shader_errors'] or report['console_errors']),'Browser/runtime errors occurred')
    need(not [r for r in report['http_errors'] if r['url'].startswith(base) or r['url'] in target_urls],'Actual local/model HTTP failure')
    need(not [r for r in report['network_failures'] if r['url'].startswith(base) or r['url'] in target_urls],'Actual local/model network failure')
    need(len(report['captures'])==4 and all(r['screenshot_complete'] for r in report['captures']),'Required screenshots incomplete')
    report['screenshot_bytes']=sum(r['screenshot']['bytes'] for r in report['captures']);need(report['screenshot_bytes']<2_000_000,'Capture budget exceeded')
    report['technical_passed']=report['passed']=True;save()
   except Exception as error:
    report['error']={'message':str(error),'traceback':traceback.format_exc()};save()
    if page:
     try:page.keyboard.up('KeyW')
     except Exception:pass
     try:report['failure_snapshot']=page.evaluate('()=>window.__BUILDING_PROBE__?.snapshot()||null');save()
     except Exception as exc:report['failure_snapshot_error']=str(exc)
     try:
      path=args.output/'failure.png';page.screenshot(path=str(path),timeout=30000);report['failure_screenshot']={**descriptor(path),'file':path.name}
     except Exception as exc:report['failure_screenshot_error']=str(exc)
   finally:
    if browser:browser.close()
 except Exception as error:report['error']={'message':str(error),'traceback':traceback.format_exc()}
 report['finished_at']=utc();report['stage']='FINISHED';save();print(json.dumps({'report':str(args.output/'browser.json'),'technical_passed':report['technical_passed'],'visual_review':'pending'}),flush=True)
 return 0 if report['technical_passed'] else 1

if __name__=='__main__':raise SystemExit(main())
