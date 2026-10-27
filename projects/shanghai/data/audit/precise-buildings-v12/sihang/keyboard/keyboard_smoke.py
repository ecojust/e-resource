#!/usr/bin/env python3
"""Supplemental Sihang one-start real W-key smoke; no app/QA acceptance protocol changes."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,math,sys,time,traceback
from urllib.parse import urljoin,urlsplit
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
QA=HERE.parent/'qa'
IDS=['jingan-sihang-warehouse']

def need(value,message):
 if not value:raise AssertionError(message)
def descriptor(path):
 path=Path(path)
 with path.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
 return {'source':str(path),'bytes':path.stat().st_size,'sha256':digest}
def verify_sources():
 from prepare_source_binding import verify_binding
 return verify_binding(HERE/'source-binding.json',arguments=sys.argv[1:])
def load_qa():
 sys.path.insert(0,str(QA));spec=importlib.util.spec_from_file_location('frozen_sihang_qa_smoke_dependency',QA/'browser-next-v3.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def settle_post_keyup(initial,read_snapshot,wait_ms,record_snapshot,timeout_ms,clock=time.monotonic):
 started=clock();current=initial
 while True:
  elapsed_ms=(clock()-started)*1000
  record_snapshot({'elapsed_ms':elapsed_ms,'snapshot':current})
  if (current.get('osm')or{}).get('ready')is not False:return current
  if elapsed_ms>=timeout_ms:return current
  wait_ms(min(250,timeout_ms-elapsed_ms))
  current=read_snapshot()

def stationary_after_keyup(initial,snapshots):
 return bool(snapshots)and all(current['position']==initial['position']and current['controller']['distance']==initial['controller']['distance']for current in snapshots)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ['url','output','expectations','osm-evidence-set']:parser.add_argument('--'+name,required=True,type=str if name=='url'else Path)
 parser.add_argument('--force-osm',action='store_true');parser.add_argument('--use-env-proxy',action='store_true')
 parser.add_argument('--chromium',default='/usr/bin/chromium');parser.add_argument('--timeout-ms',type=int,default=240000)
 parser.add_argument('--hold-ms',type=int,default=1000);parser.add_argument('--width',type=int,default=1040);parser.add_argument('--height',type=int,default=760)
 args=parser.parse_args();need(800<=args.hold_ms<=1500,'Only an approximately one-second short input is in scope')
 need(urlsplit(args.url).scheme in ['http','https'],'HTTP(S) candidate URL required');need(args.timeout_ms>0 and 320<=args.width<=1920 and 240<=args.height<=1440,'Invalid bounded browser options')
 need(not args.output.exists()and not args.output.is_symlink(),'Use a new immutable smoke output directory');args.output.mkdir(parents=True)
 report={'schema':'sihang-one-start-keyboard-smoke-v12','technical_passed':False,'visual_review':{'status':'pending','reviewer':'root','actually_viewed':False},
  'url':args.url,'targets':IDS,'hold_ms_requested':args.hold_ms,'attempts':[],'page_errors':[],'console_errors':[],'console_warnings':[],
  'shader_errors':[],'asset_errors':[],'external_http_errors':[],'request_failures':[],'expected_aborts':[],'forced_outage_requests':[],
  'source_bindings':None,'actual_profiles_generated':False,'whole_route_or_interior_tested':False,'ground_survey_verified':False,
  'scope':'Actual short W input at the single selected Sihang exterior start only. Initial near_view uses normal place navigation; no QA position setter is used during measured movement. Ground data are observed, not survey-certified. Separate full browser/model evidence is neither replaced nor marked accepted.'}
 def save():
  tmp=args.output/'keyboard-smoke.json.tmp';tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(args.output/'keyboard-smoke.json')
 def keep(row,key,value):row[key]=value;save();return value
 def screenshot(row,name):
  path=args.output/(name+'.png');page.screenshot(path=str(path),timeout=min(args.timeout_ms,90000))
  keep(row,'screenshot',{'file':path.name,**{k:v for k,v in descriptor(path).items()if k!='source'}})
  need(path.stat().st_size<100000000,'Screenshot exceeds100MB')
 save();browser=page=None
 try:
  report['source_bindings']=verify_sources();qa=load_qa();snapshot=(HERE/'snapshot.js').read_text();save()
  pinned=qa.expectations.load_profile(args.expectations,IDS);binding=qa.validate_profile_binding(pinned)
  fixtures,fixture_binding=qa.read_fixture_set(args.osm_evidence_set,IDS)
  need(fixture_binding['set']==binding['osm_evidence_set'],'Actual fixture input differs from selected profile')
  report.update(expectations=descriptor(args.expectations),sihang_input_binding=binding,runtime_baseline_sha256=binding['runtime_baseline']['sha256']);save()
  proxy,network=qa.environment_proxy()if args.use_env_proxy else(None,{'enabled':False});report['network']=network
  base=args.url.split('#',1)[0].split('?',1)[0];base=base.rsplit('/',1)[0]+'/'if base.endswith('.html')else base.rstrip('/')+'/'
  def event(key,value):report[key].append(value);save()
  def console(message):
   if message.type not in ['error','warning']:return
   row={'type':message.type,'text':message.text,'location':message.location}
   if qa.is_expected_outage_console(message,args.force_osm):event('console_warnings',{**row,'expected_injected_outage':True})
   elif any(s in message.text.lower()for s in ['shader error','shader failed','webglprogram','context lost']):event('shader_errors',row)
   else:event('console_errors'if message.type=='error'else'console_warnings',row)
  def failed(request):
   row={'url':request.url,'error':request.failure}
   key='expected_aborts'if 'ERR_ABORTED'in str(request.failure)or qa.is_expected_outage_request(request.url,request.failure,args.force_osm)else'request_failures'
   event(key,row)
  def response(value):
   if value.status>=400:event('asset_errors'if value.url.split('?')[0].endswith(('.glb','.glb.gz'))else'external_http_errors',{'url':value.url,'status':value.status})
  from playwright.sync_api import sync_playwright
  with sync_playwright()as playwright:
   try:
    browser=playwright.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'])
    options={'viewport':{'width':args.width,'height':args.height},'device_scale_factor':1}
    if proxy:options['proxy']=proxy
    context=browser.new_context(**options);page=context.new_page();page.set_default_timeout(args.timeout_ms)
    page.on('pageerror',lambda error:event('page_errors',str(error)));page.on('console',console);page.on('requestfailed',failed);page.on('response',response)
    urls=[urljoin(base,pinned['targets'][ident]['record']['assets'][role]['file'])for ident in IDS for role in ['web','lod']]
    qa.install_network_observer(context,page,report,save,urls,args.force_osm)
    page.goto(urljoin(base,'index.html')+'#mode=walk',wait_until='domcontentloaded',timeout=args.timeout_ms)
    link=page.get_by_role('link',name='Open the page')
    if link.count():link.click()
    page.wait_for_function('()=>Boolean(window.__SHANGHAI_APP__?.controller)',timeout=args.timeout_ms)
    fetched=page.evaluate(qa.FETCH_JSON,{'registry':'data/precise-buildings-v6.json','landmarks':'data/landmarks.json'})
    keep(report,'actual_metadata',{k:{x:y for x,y in value.items()if x!='data'}for k,value in fetched.items()})
    records={r['id']:r for r in fetched['landmarks']['data']};need(len(records)==len(fetched['landmarks']['data'])==30,'Actual candidate30 required')
    need(fetched['landmarks']['sha256']==pinned['metadata_source']['landmarks_sha256'],'Served navigation differs from pinned final profile')
    qa.expectations.validate_registry(fetched['registry']['data'],fetched['registry']['sha256'],pinned,IDS)
    for ident in IDS:qa.expectations.validate_record(records[ident],pinned['targets'][ident])
    keep(report,'read_only_model_probe',page.evaluate(qa.INSTALL_PROBE,fetched['registry']['data']))
    page.evaluate("()=>{window.__KEYBOARD_SMOKE_EVENTS__=[];for(const type of ['keydown','keyup'])window.addEventListener(type,event=>{if(event.code==='KeyW')window.__KEYBOARD_SMOKE_EVENTS__.push({type,code:event.code,key:event.key,isTrusted:event.isTrusted,at:performance.now()});},{capture:true,passive:true});}")
    runtime=qa.check_runtime_binding(binding['runtime_baseline'])['files']
    values=[]
    keep(report,'actual_runtime_files',values)
    for runtime_row in runtime:
     runtime_response=context.request.get(urljoin(base,runtime_row['file']),timeout=args.timeout_ms)
     need(runtime_response.ok,'Runtime HTTP failure: '+runtime_row['file']);runtime_body=runtime_response.body()
     values.append({'file':runtime_row['file'],'bytes':len(runtime_body),'sha256':hashlib.sha256(runtime_body).hexdigest()});save()
    keep(report,'actual_runtime_files',values);need(values==runtime,'Actual31 runtime files differ')
    for ident in IDS:
     row={'id':ident,'movement_passed':False,'keyboard_attempted':False};report['attempts'].append(row);save();print('TARGET_START '+ident,flush=True)
     try:
      keep(row,'osm_probe',page.evaluate(qa.OSM_PROBE,fixtures[ident]));qa.near_view(page,ident)
      qa.wait_ready(page,ident,'full',args.timeout_ms,True);qa.frame(page,args.timeout_ms)
      value=keep(row,'actual_full_model_bytes',page.evaluate(qa.AUDIT_ASSET,{'record':records[ident],'variant':'full'}));record=records[ident]
      need(value['bytes']==record['web_bytes']and value['sha256']==record['web_sha256']and value['triangles']==record['triangles'],'Actual full model identity differs')
      need(value['bytes']<100000000 and not value['externalResources'],'Unexpected runtime asset size/dependency')
      page.locator('canvas.maplibregl-canvas').focus()
      keep(row,'idle_before',page.evaluate(snapshot,ident));page.wait_for_timeout(1000)
      before=keep(row,'before',page.evaluate(snapshot,ident));idle_drift=qa.metres(before['position'],row['idle_before']['position']);keep(row,'idle_drift_m',idle_drift)
      need(idle_drift<=.05,'Start adjusted while idle; no keyboard movement claim')
      need(before['mode']=='walk'and before['controller']['mode']=='walk'and before['controller']['enabled']and not before['controller']['keys'],'Controller not idle/enabled in walk mode')
      need(before['avatar'].get('effectiveVisible')and before['asset']['visible']and before['asset']['variant']=='full','Avatar/full model not actually visible')
      need(before['controller']['moveVector']=={'x':0,'y':0}and before['controller']['manualRun']is False,'Other movement input active')
      row['keyboard_attempted']=True;save();started=time.monotonic()
      try:
       page.keyboard.down('KeyW');started=time.monotonic()
       keep(row,'during_keydown',page.evaluate("()=>({keys:[...__SHANGHAI_APP__.controller.keys],mode:__SHANGHAI_APP__.mode,events:__KEYBOARD_SMOKE_EVENTS__.slice(),at:performance.now()})"))
       page.wait_for_timeout(max(0,args.hold_ms-(time.monotonic()-started)*1000))
      finally:
       page.keyboard.up('KeyW');row['key_released']=True;row['hold_wall_ms']=(time.monotonic()-started)*1000;save()
      immediate_after=keep(row,'immediate_after',page.evaluate(snapshot,ident))
      source_wait=[];keep(row,'post_keyup_source_wait',source_wait)
      def record_source_wait(value):source_wait.append(value);save()
      after=keep(row,'after',settle_post_keyup(immediate_after,lambda:page.evaluate(snapshot,ident),page.wait_for_timeout,record_source_wait,args.timeout_ms))
      stable=keep(row,'post_keyup_stationary',{'exact_position_and_distance':stationary_after_keyup(immediate_after,[value['snapshot']for value in source_wait]),'snapshot_count':len(source_wait),'comparison':'Exact numeric position and controller.distance equality for every post-keyup snapshot'})
      need(stable['exact_position_and_distance'],'Position or controller distance changed while awaiting post-keyup source readiness')
      qa.frame(page,args.timeout_ms);screenshot(row,ident+'-after-W')
      keep(row,'after_screenshot',page.evaluate(snapshot,ident))
      moved=qa.metres(before['position'],after['position']);travelled=after['controller']['distance']-before['controller']['distance']
      events=after['keyboardEvents'][len(before['keyboardEvents']):]
      down=next((e for e in events if e['type']=='keydown'and e['isTrusted']),None);up=next((e for e in events if e['type']=='keyup'and e['isTrusted']),None)
      keep(row,'trusted_key_hold_ms',up['at']-down['at']if down and up else None)
      eye=after['camera']['actualMapEye'];camera_distance=qa.metres(eye,after['position'])if eye else None
      keep(row,'movement_observation',{'displacement_m':moved,'controller_distance_delta_m':travelled,'actual_keyboard_events':events,'actual_camera_player_horizontal_distance_m':camera_distance,'minimum_visible_motion_m':.10,'no_qa_position_mutation_during_input':True})
      need(any(e['type']=='keydown'and e['isTrusted']for e in events)and any(e['type']=='keyup'and e['isTrusted']for e in events),'Trusted actual keydown/keyup not observed')
      need('KeyW'in row['during_keydown']['keys']and'KeyW'not in after['controller']['keys'],'Real key press/release was not accepted')
      need(math.isfinite(moved)and math.isfinite(travelled)and moved>.10 and travelled>.10 and moved<=travelled+.10,'No visible controller-driven movement, or unaccounted position adjustment')
      need(camera_distance is not None and math.isfinite(camera_distance)and camera_distance>.5,'Actual third-person camera eye was not observed separately from the player')
      need(after['mode']=='walk'and after['avatar'].get('effectiveVisible')and after['asset']['visible']and after['asset']['variant']=='full','Walk/avatar/full model changed during movement')
      need(after['controller']['spawnGeneration']==before['controller']['spawnGeneration'],'Navigation generation changed during measured input')
      need(after['osm']and after['osm'].get('passed')is True,'Actual source observation after movement unresolved')
      row['movement_passed']=True;save();print('SHORT_MOVEMENT_OBSERVED '+ident,flush=True)
     except Exception as error:
      keep(row,'error',{'message':str(error),'traceback':traceback.format_exc()})
      try:page.keyboard.up('KeyW');row['key_released_after_error']=True;save()
      except Exception as release_error:keep(row,'release_error',str(release_error))
      try:keep(row,'failure_snapshot',page.evaluate(snapshot,ident))
      except Exception as snapshot_error:keep(row,'failure_snapshot_error',str(snapshot_error))
      if 'screenshot'not in row:
       try:screenshot(row,ident+'-failure')
       except Exception as image_error:keep(row,'screenshot_error',str(image_error))
    report['technical_passed']=len(report['attempts'])==1 and all(r['movement_passed']for r in report['attempts'])and not(report['page_errors']or report['shader_errors']or report['asset_errors']or report['console_errors']);save()
   except Exception as error:
    report['technical_passed']=False;report['fatal_error']={'message':str(error),'traceback':traceback.format_exc()};save()
    if page:
     try:keep(report,'fatal_actual_state',page.evaluate("()=>{const a=window.__SHANGHAI_APP__,c=a?.controller;return {mode:a?.mode??null,position:c?{...c.position}:null,keys:c?[...c.keys]:null,url:location.href};}"))
     except Exception as state_error:keep(report,'fatal_state_error',str(state_error))
     try:screenshot(report,'global-failure')
     except Exception as image_error:keep(report,'fatal_screenshot_error',str(image_error))
   finally:
    if browser:browser.close();browser=None
 except Exception as error:report['technical_passed']=False;report['fatal_error']={'message':str(error),'traceback':traceback.format_exc()};save()
 report['technical_passed']=report['technical_passed']and not(report.get('fatal_error')or report['page_errors']or report['shader_errors']or report['asset_errors']or report['console_errors'])
 report['finished']=True;save();print(json.dumps({'report':descriptor(args.output/'keyboard-smoke.json'),'technical_passed':report['technical_passed'],'root_visual_review_pending':True}))
 raise SystemExit(0 if report['technical_passed']else 1)
if __name__=='__main__':main()
