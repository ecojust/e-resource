#!/usr/bin/env python3
"""One-browser accepted whole-macro catalog lifecycle QA, derived from frozen v6.
Every accepted index model is audited. Dynamic-only response injection removes
all curated ordinary models in that macro and its top-level replacement entries;
accepted inner JSON bytes remain unchanged. No browser runs on import.
"""
from __future__ import annotations
import argparse,asyncio,copy,hashlib,json,os,time
from pathlib import Path
import sys
QA_PARENT=Path(__file__).resolve().parent.parent
if str(QA_PARENT) not in sys.path:sys.path.insert(0,str(QA_PARENT))
from modern_inputs import IDS,CONFIG,load_model_inputs,validate_registry as modern_registry
from urllib.parse import urljoin,urlsplit,unquote
import catalog_expectations as contracts
HERE=Path(__file__).resolve().parent
OSM_PROBE=(HERE/'osm-readiness-probe.js').read_text()
OSM_EVIDENCE=None
from capture_journal import begin_capture,observation,completed_screenshot,finish_capture
from modern_inputs import actual,check_runtime_binding
from osm_evidence_set import read_fixture as checked_fixture

CHECKS=('source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','browser_proof','uncertainty')
def sha(data):return hashlib.sha256(data).hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode()
def require(value,message):
 if not value:raise RuntimeError(message)

def corrupt_one_byte(body):
 require(body,'Empty JSON response');data=bytearray(body)
 # Keep valid JSON and the exact byte count; SHA failure must precede parsing.
 i=next((i for i,c in enumerate(data) if c in (9,10,13,32)),None)
 require(i is not None,'Fixture JSON has no whitespace byte');data[i]=9 if data[i]!=9 else 32
 require(len(data)==len(body) and bytes(data)!=body,'Corruption fixture did not change one byte')
 return bytes(data)
def local_project_links(value,project_base):
 if isinstance(value,dict):return {k:local_project_links(v,project_base) for k,v in value.items()}
 if isinstance(value,list):return [local_project_links(v,project_base) for v in value]
 return value[len(project_base):] if isinstance(value,str) and value.startswith(project_base) else value

def parse_args():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--target',required=True);p.add_argument('--inputs',type=Path,required=True,help='Frozen actually accepted whole-macro input file');p.add_argument('--use-env-proxy',action='store_true');p.add_argument('--chromium',default='/usr/bin/chromium');p.add_argument('--timeout-ms',type=int,default=240000)
 p.add_argument('--osm-evidence',type=Path,help='Optional frozen actual-MVT evidence for this target. Active fallback near captures fail closed when absent.')
 p.add_argument('--width',type=int,default=1040);p.add_argument('--height',type=int,default=760);p.add_argument('--dpr',type=float,default=1)
 return p.parse_args()

def read_osm_fixture(path,target):
    if path is None:return {'schema':'actual-osm-component-qa-pending-v1','landmark_id':target,'source_id':None,'geometry':None}
    evidence=json.loads(path.read_bytes())
    require(evidence.get('schema')=='actual-osm-component-qa-v1' and evidence.get('landmark_id')==target,'OSM fixture belongs to another target or is pending')
    ident=evidence.get('source_id')
    require((type(ident) is int and abs(ident)<=9007199254740991) or (isinstance(ident,str) and bool(ident)),'OSM source ID must be an actual safe integer or string')
    geometry=evidence.get('geometry') or {}
    require(evidence.get('source_layer')=='building' and geometry.get('type')=='Polygon' and geometry.get('coordinates'),'Actual source polygon/building layer required')
    require(isinstance(evidence.get('origin'),str) and evidence['origin'].strip(),'Actual observation provenance required')
    return evidence


def environment_proxy(environ=None):
 # Test-environment transport only. BrowserContext.request and route.fetch use
 # this same explicit context proxy; the launcher bytes/URLs stay unchanged.
 env=os.environ if environ is None else environ
 name=next((name for name in ('HTTPS_PROXY','HTTP_PROXY') if env.get(name)),None)
 require(name is not None,'Proxy QA requires HTTPS_PROXY or HTTP_PROXY')
 value=urlsplit(env[name])
 require(value.scheme in ('http','https') and value.hostname and value.path in ('','/')
   and not value.query and not value.fragment,'Unsupported environment proxy URL')
 try:port=value.port
 except ValueError:raise RuntimeError('Invalid environment proxy port') from None
 host=value.hostname
 require(not any(c.isspace() or ord(c)<32 for c in host),'Invalid environment proxy host')
 server=value.scheme+'://'+('['+host+']' if ':' in host else host)+((':'+str(port)) if port else '')
 bypass='localhost,127.0.0.1'
 proxy={'server':server,'bypass':bypass}
 if value.username is not None:proxy['username']=unquote(value.username)
 if value.password is not None:proxy['password']=unquote(value.password)
 safe={'enabled':True,'source_environment':name,'scheme':value.scheme,'host':host,'port':port,
  'bypass':bypass,'credentials_supplied':value.username is not None or value.password is not None,
  'scope':'Explicit Playwright BrowserContext proxy shared by browser requests, context.request and route.fetch; localhost remains direct.',
  'remote_urls_or_bytes_rewritten':False}
 return proxy,safe


async def run(args):
 global OSM_EVIDENCE
 require(args.target in IDS and args.osm_evidence is not None,'Actual selected modern target fixture required')
 OSM_EVIDENCE=checked_fixture(args.osm_evidence,args.target)
 inputs=json.loads(args.inputs.read_text());require(inputs.get('schema')=='ordinary-macro-browser-inputs-v1' and inputs.get('primary_target')==args.target,'Frozen primary/whole-macro inputs differ')
 binding=inputs.get('modern_input_binding') or {};source=actual(binding.get('model_inputs'))
 declared=json.loads(source.read_text());selected_fixture=binding.get('osm_evidence_by_target',{}).get(args.target)
 require(selected_fixture is not None and actual(selected_fixture).resolve()==args.osm_evidence.resolve(),'Catalogue fixture differs from bound actual model input')
 require(inputs.get('runtime_baseline_sha256')==binding['runtime_baseline']['sha256'],'Catalogue runtime binding differs')
 require(load_model_inputs(source,inputs.get('modern_candidate_records'))==binding,'Actual modern catalogue prerequisites changed or remain pending')
 from playwright.async_api import async_playwright
 require(not args.output.exists() and not args.output.is_symlink(),'Use a completely NEW catalogue output directory');args.output.mkdir(parents=True,exist_ok=False)
 report_path=args.output/'browser.json';require(not report_path.exists(),'Refuse to overwrite an existing browser report')
 proxy_options,network=environment_proxy() if args.use_env_proxy else (None,{'enabled':False,'source':'Playwright default transport'})
 base=args.url if args.url.endswith('/') else args.url.rsplit('/',1)[0]+'/' if args.url.endswith('index.html') else args.url+'/'
 require(urlsplit(base).scheme in ('http','https'),'HTTP(S) project URL required')
 report={'schema':'ordinary-macro-catalog-browser-v7','started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'passed':False,'technical_passed':False,
  'target':args.target,'url':base,'inputs_sha256':sha(args.inputs.read_bytes()),'network':network,'single_browser':True,'sequential_pages':True,'disk_models_modified':False,'test_injections':[],
  'phases':[],'captures':[],'events':[],'page_errors':[],'shader_errors':[],'console_warnings':[],'http_errors':[],
  'asset_requests':[],'visual_review':'not performed by script','script_sha256':sha(Path(__file__).read_bytes()),
  'probe_sha256':sha((HERE/'catalog-base-probe.js').read_bytes()),'extension_sha256':sha((HERE/'catalog-extension-probe.js').read_bytes())}
 report['modern_input_binding']=binding;report['runtime_baseline_sha256']=binding['runtime_baseline']['sha256']
 report['osm_qa']={'probe_sha256':sha((HERE/'osm-readiness-probe.js').read_bytes()),'evidence_sha256':sha(args.osm_evidence.read_bytes()) if args.osm_evidence else None,'scope':'Lightweight OSM transaction readiness and actual MVT component evidence; root visual review remains mandatory.'}
 def save():
  tmp=report_path.with_suffix('.tmp');tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');tmp.replace(report_path)
 def progress(label,**detail):
  row={'at':time.time(),'label':label,**detail};report['events'].append(row);print(json.dumps(row,ensure_ascii=False),flush=True);save()
 browser=None;page=None;phase='initial';context=None;original={};records={};record=None;macro=None;catalog=None;project_base=None;index_url=None;contract=None;model_urls=set()
 async def fetch_json(url,expected=None):
  response=await context.request.get(url,timeout=args.timeout_ms);require(response.ok,f'Metadata HTTP {response.status}: {url}');body=await response.body();require(len(body)<8*1024*1024,'Metadata exceeds runtime limit')
  if expected:require(len(body)==expected['bytes'] and sha(body)==expected['sha256'],'Original metadata SHA/bytes differ: '+url)
  return {'url':url,'bytes':len(body),'sha256':sha(body),'data':json.loads(body)}
 async def snapshot():return await page.evaluate('()=>__V6_CAPTURE__.catalogSnapshot()')
 async def wait_state(label,condition):
  progress('WAIT BEGIN',stage=label)
  handle=await page.wait_for_function('condition=>{if(!window.__OSM_CAPTURE__?.readiness().ready)return false;const s=__V6_CAPTURE__.catalogSnapshot();window.__CATALOG_QA_LAST_WAIT__=s;return ('+condition+')(s)?s:false}',arg=None,timeout=args.timeout_ms,polling=500)
  try:state=await handle.json_value()
  finally:await handle.dispose()
  progress('WAIT READY',stage=label);return state
 def assert_owner_state(state):
  require(state['ordinary']['staticNavigationCount']==contract['static_navigation_count' if phase=='static_adoption' else 'dynamic_navigation_count'],'Actual navigation count differs from whole-macro removal contract')
  require(state['districts']==16,'16-district navigation changed');require(state['audit']['passed'],'Owner audit failed: '+str(state['audit']['errors']))
  require(state['streaming']['detail']['metadataMismatches']==0,'Actual near owner/baseline mismatch')
  require(state['audit']['onlinePending']==0 and state['streaming']['pendingStates']==0,'Owner updates are not settled')
  if state['source']['buildingSource']=='overture':
   for entry in state['audit']['online']:
    for source in entry['sources']:require(bool((source['state'] or {}).get('localModel'))==(source['expectedReferences']>0),'Online UUID state differs from shared references')
 async def capture(name,condition,screenshot=True,selected=None):
  # A real render and a fresh coherent state are required. Never pass a timeout.
  progress('RENDER BEGIN',stage=name)
  await page.evaluate('timeout=>new Promise((resolve,reject)=>{const m=__SHANGHAI_APP__.scene.map;const done=()=>{clearTimeout(timer);m.off("render",done);resolve()};const timer=setTimeout(()=>{m.off("render",done);reject(Error("Actual render timed out"))},timeout);m.on("render",done);m.triggerRepaint()})',min(args.timeout_ms,90000))
  state=await wait_state(name,condition);assert_owner_state(state)
  asset=state['assets'].get(selected,{}) if selected else {}
  current=records.get(selected)
  if asset.get('status')=='loaded' and asset.get('visible'):
   require(asset.get('variant')=='full' and asset.get('triangles')==current['triangles'],'Actual full model/triangle count differs')
   expected=(current.get('photo_texture') or {}).get('expected_images',{}).get('web',0);require(expected in (0,1),'New multi-photo QA schema requires explicit review');require(len(asset['images'])==expected,'Actual ordinary photo image count differs')
   if expected:require([[i['width'],i['height']] for i in asset['images']]==[current['photo_texture']['orientation']['rawSize']]*expected,'Actual ordinary decoded image dimensions differ')
  saved=begin_capture(report,{'phase':phase,'name':name,'image':None,**state},save)
  inspection_started=time.monotonic();inspection_attempts=[]
  saved['osm_pre_capture_wait']=inspection_attempts
  while True:
      inspection=await page.evaluate('v=>__OSM_CAPTURE__.inspect(v)',{'target':selected})
      inspection_attempts.append({'elapsed_ms':(time.monotonic()-inspection_started)*1000,'inspection':inspection})
      save()
      if inspection.get('ready') is not False:break
      if (time.monotonic()-inspection_started)*1000>=args.timeout_ms:break
      await page.wait_for_timeout(250)
  before=observation(saved,'osm_capture_before',inspection,save)
  state['osm_capture_before']=before
  require(before['passed'],'Actual OSM readiness/component check failed: '+str(before))
  if screenshot:
   progress('SCREENSHOT BEGIN',stage=name);path=args.output/(name+'.png');await page.screenshot(path=str(path),timeout=min(args.timeout_ms,90000))
   completed_screenshot(saved,path,save);progress('SCREENSHOT READY',stage=name)
  after=observation(saved,'osm_capture_after',await page.evaluate('v=>__OSM_CAPTURE__.inspect(v)',{'target':selected}),save)
  state['osm_capture_after']=after
  require(after['passed'],'Actual OSM readiness/component changed during capture: '+str(after))
  finish_capture(saved,save);return state
 async def navigate(identity=None,near=True):
  progress('NAVIGATE BEGIN',near=near,id=identity)
  if near:
   # A normal map-style reviewed start, not a private load/owner mutation. It
   # works both with and without the static target navigation entry.
   await page.evaluate('async r=>{const a=__SHANGHAI_APP__;a.syncMode("walk",false);a.controller.resetCamera();await a.selectPlace({id:"catalog-qa-reviewed-start",name:r.name+" · 模型观景起点",custom:true,districtId:r.districtId,walkStart:r.navigation.walkStart,bearing:r.navigation.bearing});a.scene.map.stop();a.scene.loadLandmarks()}',records[identity])
  else:
   await page.evaluate('async id=>{const a=__SHANGHAI_APP__;const d=a.districts.find(r=>String(r.id)===id);if(!d)throw Error("Missing reviewed away district");a.syncMode("overview",false);await a.selectPlace(d);a.scene.map.stop();a.scene.loadLandmarks()}',contract['away_navigation']['district_id'])
  progress('NAVIGATE READY',near=near)
 def request_count():return sum(r['phase']==phase and r['url'].split('?')[0] in model_urls for r in report['asset_requests'])
 def console(message):
  if message.type not in ('warning','error'):return
  row={'phase':phase,'type':message.type,'text':message.text,'at':time.time()};report['console_warnings'].append(row)
  if any(x in message.text.lower() for x in ('webglprogram','gl_invalid','context lost','shader error','invalid_operation')):report['shader_errors'].append(row)
  print('CONSOLE '+json.dumps(row,ensure_ascii=False),flush=True);save()
 async def new_page(dynamic=False,corrupt=None):
  nonlocal page
  if page is not None:
   losses=await page.evaluate('window.__CATALOG_CONTEXT_LOSSES__||0');require(losses==0,'Previous QA page lost its WebGL context')
   await page.close();page=None
  page=await context.new_page();page.set_default_timeout(args.timeout_ms)
  page.on('console',console)
  def page_error(error):report['page_errors'].append({'phase':phase,'error':str(error)});progress('PAGE ERROR',error=str(error))
  page.on('pageerror',page_error)
  page.on('request',lambda r:report['asset_requests'].append({'phase':phase,'url':r.url,'at':time.time()}) if r.url.endswith(('.glb','.glb.gz')) else None)
  def response_seen(response):
   if response.status>=400:report['http_errors'].append({'phase':phase,'url':response.url,'status':response.status});progress('HTTP ERROR',url=response.url,status=response.status)
  page.on('response',response_seen)
  await page.add_init_script('window.__CATALOG_CONTEXT_LOSSES__=0;document.addEventListener("webglcontextlost",()=>window.__CATALOG_CONTEXT_LOSSES__++,true)')
  if dynamic or corrupt:
   async def route_handler(route):
    url=route.request.url;kind='navigation' if url==urljoin(base,'data/landmarks.json') else 'registry' if url==urljoin(base,'data/precise-buildings-v6.json') else None
    if not ((dynamic and kind) or url==corrupt):await route.continue_();return
    response=await route.fetch(timeout=args.timeout_ms);require(response.ok,'Injected source request failed');before=await response.body()
    expected=original[kind if kind else 'index'];require(sha(before)==expected['sha256'] and len(before)==expected['bytes'],'QA response changed after metadata freeze')
    after=contracts.remove_static_metadata(before,kind,contract) if dynamic and kind else corrupt_one_byte(before)
    report['test_injections'].append({'phase':phase,'url':url,'kind':'remove-static-'+kind if dynamic and kind else 'equal-length-one-byte-hash-failure',
     'before_bytes':len(before),'after_bytes':len(after),'before_sha256':sha(before),'after_sha256':sha(after),
     'ordinary_catalog_chain_changed':False if kind else url==corrupt,'disk_modified':False,'removed_static_ids':contract['removed_static_ids'] if dynamic and kind else [],'removed_macro':macro if dynamic and kind else None})
    headers={k:v for k,v in response.headers.items() if k.lower() not in ('content-length','content-encoding','etag')};headers['cache-control']='no-store'
    await route.fulfill(status=response.status,headers=headers,body=after);save()
   if dynamic:
    await page.route(urljoin(base,'data/landmarks.json'),route_handler);await page.route(urljoin(base,'data/precise-buildings-v6.json'),route_handler)
   if corrupt:await page.route(corrupt,route_handler)
  progress('PAGE BEGIN',dynamic_only=dynamic,corrupt_url=corrupt)
  await page.goto(urljoin(base,'index.html')+'#mode=overview',wait_until='domcontentloaded',timeout=args.timeout_ms)
  await page.wait_for_function('()=>Boolean(window.__SHANGHAI_APP__?.controller)',timeout=args.timeout_ms,polling=500)
  require(await page.evaluate('()=>Boolean(__SHANGHAI_APP__.scene.getOrdinaryCatalogState())'),'Catalog failed to initialize')
  await page.evaluate((HERE/'catalog-base-probe.js').read_text(),original['registry']['data'])
  await page.evaluate(OSM_PROBE,OSM_EVIDENCE)
  probe=await page.evaluate((HERE/'catalog-extension-probe.js').read_text(),{'targets':contract['target_ids'],'macroId':macro,'owners':{ident:r['owner'] for ident,r in records.items()}});require(probe['read_only_prototypes_restored'],'Probe prototype not restored')
  progress('PAGE READY',dynamic_only=dynamic)

 async with async_playwright() as playwright:
  try:
   progress('BROWSER BEGIN');browser=await playwright.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'])
   context_options={'viewport':{'width':args.width,'height':args.height},'device_scale_factor':args.dpr}
   if proxy_options:context_options['proxy']=proxy_options
   context=await browser.new_context(**context_options)
   runtime_rows=check_runtime_binding(binding['runtime_baseline'])['files'];runtime_values=[]
   report['actual_runtime_file_audit']={'passed':False,'files':runtime_values};save()
   for runtime in runtime_rows:
    response=await context.request.get(urljoin(base,runtime['file']),timeout=args.timeout_ms)
    require(response.ok,'Runtime HTTP failure: '+runtime['file']);body=await response.body()
    runtime_values.append({'file':runtime['file'],'bytes':len(body),'sha256':sha(body)});save()
   require(runtime_values==runtime_rows,'Served31 runtime files differ from exact current baseline')
   report['actual_runtime_file_audit']['passed']=True;save()
   original['registry']=await fetch_json(urljoin(base,'data/precise-buildings-v6.json'));original['navigation']=await fetch_json(urljoin(base,'data/landmarks.json'));original['districts']=await fetch_json(urljoin(base,'data/districts.json'))
   actual_binding=load_model_inputs(source,{r['id']:r for r in original['navigation']['data']})
   require(actual_binding==binding,'Catalogue actual model/native/decoder evidence changed')
   rows=[r for r in original['navigation']['data'] if r['id']==args.target];require(len(rows)==1,'Actual primary static target must exist once');record=rows[0]
   macro=record['owner']['macro_id'];descriptor=original['registry']['data'].get('ordinary_catalog');require(descriptor,'No accepted ordinary catalog descriptor')
   catalog_url=urljoin(base,descriptor['file']);project_base=descriptor.get('project_base_url') or base
   original['catalog']=await fetch_json(catalog_url,descriptor);catalog=original['catalog']['data'];entries=[r for r in catalog['macros'] if r['id']==macro];require(len(entries)==1,'Target macro missing/duplicate')
   index_url=urljoin(project_base,entries[0]['file']);original['index']=await fetch_json(index_url,entries[0]);index=original['index']['data']
   original['replacement']=await fetch_json(urljoin(project_base,index['replacement_registry']['file']),index['replacement_registry'])
   contract=contracts.macro_contract(original['navigation']['data'],original['registry']['data'],index,original['replacement']['data'],args.target,project_base)
   contract['away_navigation']=contracts.choose_away_district(original['districts']['data'],entries[0])
   require(contract==inputs['contract'],'Actual whole-macro contract differs from frozen accepted inputs')
   for name,value in original.items():
    expected=inputs['metadata'].get(name);require(expected and value['bytes']==expected['bytes'] and value['sha256']==expected['sha256'],'Actual metadata changed after input freeze: '+name)
   targets=contract['target_ids'];records={ident:contract['models'][ident]['record'] for ident in targets}
   model_urls={urljoin(project_base,r['assets'][role]['file']) for r in records.values() for role in ('web','lod')}
   report['metadata']={k:{x:v for x,v in value.items() if x!='data'} for k,value in original.items()};report['records']=records;report['contract']=contract;report['targets']=targets
   report['static_navigation_count']=contract['static_navigation_count'];save()
   coherent='s.audit.passed&&s.audit.onlinePending===0&&s.streaming.pendingStates===0&&s.streaming.detail.metadataMismatches===0'
   target_json=json.dumps(targets)
   def live(ident):
    target=json.dumps(ident)
    return f's=>{coherent}&&s.assets[{target}]?.status==="loaded"&&s.assets[{target}].visible&&s.assets[{target}].variant==="full"&&s.ordinary.entry?.hasSession&&s.ordinary.entry.status==="ready"&&s.ordinary.targetRecords.length==={len(targets)}&&s.audit.parents.some(p=>p.near.some(r=>r.visible&&r.groups.some(g=>g.landmark==={target}&&!g.visible)))'
   away=f's=>{coherent}&&s.ordinary.entry?.hasSession!==true&&!s.ordinary.selectedMacroRegistryRegistered&&{target_json}.every(id=>!s.assets[id]?.visible&&!s.audit.activePrecise.includes(id))'
   def check_neighbors(state,ident):
    expected=set(contract['models'][ident]['preserved_neighbor_ids']);require(expected.issubset(state['audit']['visibleNeighborIDs']),'Actual preserved neighbors missing for '+ident)
   def adopted_ids(state,expected):require(set(state['ordinary']['entry']['adoptedIds'])==set(expected),'Whole-macro static adoption differs')
   phase='static_adoption';await new_page();static_before={}
   for ident in targets:
    await navigate(ident);state=await capture('static-'+ident+'-loaded',live(ident),selected=ident)
    require(set(state['ordinary']['staticTargetIds'])==set(targets),'Static whole-macro navigation differs');adopted_ids(state,targets);check_neighbors(state,ident)
    static_before[ident]=state['ordinary']['actualGroupUUIDs'][ident]
   last=targets[-1];before_requests=request_count();before_uuid=static_before[last]
   await page.evaluate('v=>__SHANGHAI_APP__.scene.setOrdinaryCatalog(v.catalog,{districts:__SHANGHAI_APP__.districts,baseURL:v.baseURL})',{'catalog':catalog,'baseURL':project_base})
   state=await capture('static-'+last+'-reused',live(last),False,selected=last)
   require(state['ordinary']['actualGroupUUIDs'][last]==before_uuid and request_count()==before_requests,'Catalog reset duplicated/reloaded a visible static model');adopted_ids(state,targets)
   await navigate(near=False);released=await capture('static-whole-macro-unloaded',away,False)
   require({r['id'] for r in released['ordinary']['targetRecords']}==set(targets),'Catalog unload deleted a static curated record')
   for ident in targets:
    await navigate(ident);state=await capture('static-'+ident+'-returned',live(ident),selected=ident);adopted_ids(state,targets);check_neighbors(state,ident)
   report['phases'].append({'name':phase,'passed':True,'static_navigation_count':contract['static_navigation_count'],'target_ids':targets,'single_records_reused':True,'warm_reset_same_object_no_new_model_request':True,'unload_static_records_retained':True,'owner_restored':True,'preserved_neighbor_ids':contract['preserved_neighbor_ids']});save()
   phase='dynamic_only';await new_page(dynamic=True)
   before=await snapshot();require(not before['ordinary']['staticTargetIds'] and before['ordinary']['staticNavigationCount']==contract['dynamic_navigation_count'] and not set(targets).intersection(before['ordinary']['staticReplacementIds']),'Whole-macro dynamic-only removal did not take effect')
   held={}
   for ident in targets:
    await navigate(ident);state=await capture('dynamic-'+ident+'-loaded',live(ident),selected=ident)
    require(not state['ordinary']['staticTargetIds'],'Dynamic catalog unexpectedly has static target records');adopted_ids(state,[]);check_neighbors(state,ident)
    held[ident]=await page.evaluate('id=>__V6_CAPTURE__.holdTarget(id)',ident)
   await navigate(near=False);gone=await capture('dynamic-whole-macro-unloaded',away,False)
   require(not gone['ordinary']['targetRecords'],'Dynamic ordinary records survived macro unload')
   resources=gone['ordinary']['heldTargets'];require(set(resources)==set(targets),'Missing actual held model observations')
   for ident,resource in resources.items():require(resource['detached'] and resource['geometryCount']>0 and resource['geometriesDisposed']==resource['geometryCount'],'Dynamic GPU geometries not disposed: '+ident)
   for ident in targets:
    await navigate(ident);again=await capture('dynamic-'+ident+'-returned',live(ident),selected=ident)
    require(again['ordinary']['actualGroupUUIDs'][ident]!=held[ident]['uuid'],'Returned dynamic object was not reloaded: '+ident);adopted_ids(again,[]);check_neighbors(again,ident)
   report['phases'].append({'name':phase,'passed':True,'static_navigation_count':contract['dynamic_navigation_count'],'target_ids':targets,'runtime_records_added':True,'records_removed_on_unload':True,'geometry_disposal_by_target':resources,'returned_new_objects':True,'owner_restored':True,'preserved_neighbor_ids':contract['preserved_neighbor_ids']});save()
   phase='dynamic_hash_failure';await new_page(dynamic=True,corrupt=index_url);baseline_checks={}
   for ident in targets:
    await navigate(ident);owner=records[ident]['owner'];near=contract['near_contracts'][owner['near_owner_id']];runtime_id=json.dumps(near['runtime_id'])
    failed=f's=>{coherent}&&s.ordinary.entry?.status==="error"&&s.ordinary.state.failed>0&&!s.ordinary.entry.hasSession&&!s.ordinary.selectedMacroRegistryRegistered&&s.ordinary.targetRecords.length===0&&{target_json}.every(id=>!s.audit.activePrecise.includes(id))&&s.ordinary.targetMacroNear.some(r=>r.id==={runtime_id}&&r.visible&&!r.replacement)'
    rejected=await capture('dynamic-'+ident+'-index-hash-rejected-baseline-visible',failed)
    require(request_count()==0,'Rejected macro index initiated a precise model request')
    require(any(r['visible'] and not r['replacement'] and r['id']==near['runtime_id'] and set(r['ids'])==set(near['baseline_ids']) for r in rejected['ordinary']['targetMacroNear']),'Hash failure did not preserve complete baseline near source IDs: '+ident)
    baseline_checks[near['near_id']]=near['baseline_ids']
   require(any(row['kind']=='equal-length-one-byte-hash-failure' and row['phase']==phase for row in report['test_injections']),'Actual index corruption route did not run')
   require(any('SHA256 differs' in row['text'] and row['phase']==phase for row in report['console_warnings']),'No explicit SHA rejection diagnostic')
   report['phases'].append({'name':phase,'passed':True,'static_navigation_count':contract['dynamic_navigation_count'],'target_ids':targets,'precise_model_requests':0,'no_new_records_or_registry':True,'baseline_complete_owner_ids_by_near':baseline_checks,'preserved_neighbor_ids':contract['preserved_neighbor_ids']});save()
   require(not report['page_errors'] and not report['shader_errors'],'Browser/page/shader errors occurred')
   require(await page.evaluate('window.__CATALOG_CONTEXT_LOSSES__')==0,'WebGL context lost')
   require(all(c.get('capture_completed') is True and (not c.get('image') or c.get('screenshot_complete')) for c in report['captures']),'Durable completed catalogue capture records required')
   report.update(passed=True,technical_passed=True,pass_scope='Actual accepted whole-macro static adoption, explicit complete-macro dynamic-only response fixture, every index model load/unload/return with source/near/far ownership and neighbor checks, actual geometry disposal, and corrupt-index full baseline preservation. Root visual review remains required; no new source/visual acceptance or hardware performance claim.')
  except Exception as error:
   report['error']={'type':type(error).__name__,'message':str(error)};progress('FAILED',**report['error'])
   if page:
    try:report['failure_state']=await snapshot()
    except Exception as e:report['failure_state_error']=str(e)
    try:
     failure_path=args.output/'failure.png';await page.screenshot(path=str(failure_path),timeout=30000)
     failure_record={};completed_screenshot(failure_record,failure_path,lambda:None);report['failure_screenshot']=failure_record;save()
    except Exception as e:report['failure_screenshot_error']=str(e)
   raise
  finally:
   report['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());save()
   if browser:await browser.close()
 return report
if __name__=='__main__':
 os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'
 asyncio.run(run(parse_args()))
