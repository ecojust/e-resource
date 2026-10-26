#!/usr/bin/env python3
"""One-browser accepted-catalog lifecycle QA. Preparing/importing never launches.

Static production metadata is tested first. A second page then intercepts ONLY
navigation/top-registry responses to remove the selected static ordinary target,
leaving the hash-bound accepted catalog/index/replacement bytes unchanged. This
is explicit test injection, not a claim about production defaults. No disk model
or metadata changes. A third page corrupts one macro-index byte to test fallback.
"""
from __future__ import annotations
import argparse,asyncio,copy,hashlib,json,os,time
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
HERE=Path(__file__).resolve().parent
TARGET='qingpu-beidajie-222'
CHECKS=('source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','browser_proof','uncertainty')
def sha(data):return hashlib.sha256(data).hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode()
def require(value,message):
 if not value:raise RuntimeError(message)
def remove_static_metadata(body,kind,target,macro):
 """Only top-level responses; preserve the ordinary_catalog descriptor exactly."""
 doc=json.loads(body)
 if kind=='navigation':
  require(sum(r['id']==target for r in doc)==1,'Static target must appear exactly once');doc=[r for r in doc if r['id']!=target]
 else:
  descriptor=copy.deepcopy(doc['ordinary_catalog']);matches=[m for m in doc['macros'] if m['id']==macro]
  require(len(matches)==1 and {g['landmark_id'] for n in matches[0]['near'] for g in n['groups']}=={target},'Dynamic-only fixture may remove only a target-exclusive macro')
  doc['macros']=[m for m in doc['macros'] if m['id']!=macro];doc['landmarks']=[r for r in doc['landmarks'] if r['id']!=target]
  require(doc['ordinary_catalog']==descriptor,'Catalog descriptor was changed by the fixture')
 return encoded(doc)
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
 p.add_argument('--target',default=TARGET);p.add_argument('--chromium',default='/usr/bin/chromium');p.add_argument('--timeout-ms',type=int,default=240000)
 p.add_argument('--width',type=int,default=1040);p.add_argument('--height',type=int,default=760);p.add_argument('--dpr',type=float,default=1)
 return p.parse_args()

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
 from playwright.async_api import async_playwright
 require(args.output.resolve()!=HERE,'Output must not overwrite the tool directory');args.output.mkdir(parents=True,exist_ok=True)
 report_path=args.output/'browser.json';require(not report_path.exists(),'Refuse to overwrite an existing browser report')
 base=args.url if args.url.endswith('/') else args.url.rsplit('/',1)[0]+'/' if args.url.endswith('index.html') else args.url+'/'
 require(urlsplit(base).scheme in ('http','https'),'HTTP(S) project URL required')
 proxy_options,network_config=environment_proxy()
 report={'schema':'ordinary-catalog-browser-v1','started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'passed':False,'technical_passed':False,
  'target':args.target,'url':base,'network':network_config,'single_browser':True,'sequential_pages':True,'disk_models_modified':False,'test_injections':[],
  'phases':[],'captures':[],'events':[],'page_errors':[],'shader_errors':[],'console_warnings':[],'http_errors':[],
  'asset_requests':[],'visual_review':'not performed by script','script_sha256':sha(Path(__file__).read_bytes()),
  'probe_sha256':sha((HERE/'catalog-base-probe.js').read_bytes()),'extension_sha256':sha((HERE/'catalog-extension-probe.js').read_bytes())}
 def save():
  tmp=report_path.with_suffix('.tmp');tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');tmp.replace(report_path)
 def progress(label,**detail):
  row={'at':time.time(),'label':label,**detail};report['events'].append(row);print(json.dumps(row,ensure_ascii=False),flush=True);save()
 browser=None;page=None;phase='initial';context=None;original={};record=None;macro=None;catalog=None;project_base=None;index_url=None
 async def fetch_json(url,expected=None):
  response=await context.request.get(url,timeout=args.timeout_ms);require(response.ok,f'Metadata HTTP {response.status}: {url}');body=await response.body();require(len(body)<8*1024*1024,'Metadata exceeds runtime limit')
  if expected:require(len(body)==expected['bytes'] and sha(body)==expected['sha256'],'Original metadata SHA/bytes differ: '+url)
  return {'url':url,'bytes':len(body),'sha256':sha(body),'data':json.loads(body)}
 async def snapshot():return await page.evaluate('()=>__V6_CAPTURE__.catalogSnapshot()')
 async def wait_state(label,condition):
  progress('WAIT BEGIN',stage=label)
  handle=await page.wait_for_function('condition=>{const s=__V6_CAPTURE__.catalogSnapshot();window.__CATALOG_QA_LAST_WAIT__=s;return ('+condition+')(s)?s:false}',arg=None,timeout=args.timeout_ms,polling=500)
  try:state=await handle.json_value()
  finally:await handle.dispose()
  progress('WAIT READY',stage=label);return state
 def assert_owner_state(state):
  require(state['districts']==16,'16-district navigation changed');require(state['audit']['passed'],'Owner audit failed: '+str(state['audit']['errors']))
  require(state['streaming']['detail']['metadataMismatches']==0,'Actual near owner/baseline mismatch')
  require(state['audit']['onlinePending']==0 and state['streaming']['pendingStates']==0,'Owner updates are not settled')
  if state['source']['buildingSource']=='overture':
   for entry in state['audit']['online']:
    for source in entry['sources']:require(bool((source['state'] or {}).get('localModel'))==(source['expectedReferences']>0),'Online UUID state differs from shared references')
 async def capture(name,condition,screenshot=True):
  # A real render and a fresh coherent state are required. Never pass a timeout.
  progress('RENDER BEGIN',stage=name)
  await page.evaluate('timeout=>new Promise((resolve,reject)=>{const m=__SHANGHAI_APP__.scene.map;const done=()=>{clearTimeout(timer);m.off("render",done);resolve()};const timer=setTimeout(()=>{m.off("render",done);reject(Error("Actual render timed out"))},timeout);m.on("render",done);m.triggerRepaint()})',min(args.timeout_ms,90000))
  state=await wait_state(name,condition);assert_owner_state(state)
  asset=state['assets'].get(args.target,{})
  if asset.get('status')=='loaded' and asset.get('visible'):
   expected=record['photo_texture']['expected_images']['web'];require(len(asset['images'])==expected,'Actual ordinary photo image count differs')
   if expected:require([[i['width'],i['height']] for i in asset['images']]==[record['photo_texture']['orientation']['rawSize']]*expected,'Actual ordinary decoded image dimensions differ')
  if screenshot:
   progress('SCREENSHOT BEGIN',stage=name);await page.screenshot(path=str(args.output/(name+'.png')),timeout=min(args.timeout_ms,90000));progress('SCREENSHOT READY',stage=name)
  report['captures'].append({'phase':phase,'name':name,'image':name+'.png' if screenshot else None,**state});save();return state
 async def navigate(near=True):
  progress('NAVIGATE BEGIN',near=near)
  if near:
   # A normal map-style reviewed start, not a private load/owner mutation. It
   # works both with and without the static target navigation entry.
   await page.evaluate('async r=>{const a=__SHANGHAI_APP__;a.syncMode("walk",false);a.controller.resetCamera();await a.selectPlace({id:"catalog-qa-reviewed-start",name:r.name+" · 已审核临街起点",custom:true,districtId:r.districtId,walkStart:r.navigation.walkStart,bearing:r.navigation.bearing});a.scene.map.stop();a.scene.loadLandmarks()}',record)
  else:
   await page.evaluate('async()=>{const a=__SHANGHAI_APP__;const d=a.districts.find(r=>r.id==="310104");if(!d)throw Error("Missing Xuhui district");a.syncMode("overview",false);await a.selectPlace(d);a.scene.map.stop();a.scene.loadLandmarks()}')
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
    after=remove_static_metadata(before,kind,args.target,macro) if dynamic and kind else corrupt_one_byte(before)
    report['test_injections'].append({'phase':phase,'url':url,'kind':'remove-static-'+kind if dynamic and kind else 'equal-length-one-byte-hash-failure',
     'before_bytes':len(before),'after_bytes':len(after),'before_sha256':sha(before),'after_sha256':sha(after),
     'ordinary_catalog_chain_changed':False if kind else url==corrupt,'disk_modified':False})
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
  probe=await page.evaluate((HERE/'catalog-extension-probe.js').read_text(),{'target':args.target,'macroId':macro,'owner':record['owner']});require(probe['read_only_prototypes_restored'],'Probe prototype not restored')
  progress('PAGE READY',dynamic_only=dynamic)

 async with async_playwright() as playwright:
  try:
   progress('BROWSER BEGIN');browser=await playwright.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'])
   context=await browser.new_context(viewport={'width':args.width,'height':args.height},device_scale_factor=args.dpr,proxy=proxy_options)
   original['registry']=await fetch_json(urljoin(base,'data/precise-buildings-v6.json'));original['navigation']=await fetch_json(urljoin(base,'data/landmarks.json'))
   rows=[r for r in original['navigation']['data'] if r['id']==args.target];require(len(rows)==1,'Accepted static target must exist once');record=rows[0]
   require(record.get('accepted') is True and not record.get('candidate_only') and record.get('pending_stages')==[] and all(record.get('acceptance',{}).get(k,{}).get('status')=='passed' for k in CHECKS),'Actual ordinary target is not accepted')
   require(record.get('navigation',{}).get('listed') is True,'The static adoption fixture needs an explicit reviewed start')
   macro=record['owner']['macro_id'];descriptor=original['registry']['data'].get('ordinary_catalog');require(descriptor,'No ordinary catalog descriptor')
   catalog_url=urljoin(base,descriptor['file']);project_base=descriptor.get('project_base_url') or base
   original['catalog']=await fetch_json(catalog_url,descriptor);catalog=original['catalog']['data'];entries=[r for r in catalog['macros'] if r['id']==macro];require(len(entries)==1,'Target macro missing/duplicate')
   index_url=urljoin(project_base,entries[0]['file']);original['index']=await fetch_json(index_url,entries[0]);index=original['index']['data']
   matches=[r for r in index['models'] if r['id']==args.target];require([local_project_links(r,project_base) for r in matches]==[local_project_links(record,project_base)],'Static/index ordinary records differ')
   original['replacement']=await fetch_json(urljoin(project_base,index['replacement_registry']['file']),index['replacement_registry'])
   expected_neighbors={macro+':'+str(i) for i in record['owner']['preserve_neighbor_local_ids']};require(len(expected_neighbors)==27,'This acceptance fixture expects the reviewed 27 Qingpu neighbors')
   model_urls={urljoin(project_base,record['assets'][role]['file']) for role in ('web','lod')}
   report['metadata']={k:{x:v for x,v in value.items() if x!='data'} for k,value in original.items()};report['record']=record;report['expected_neighbors']=sorted(expected_neighbors)
   report['static_navigation_count']=len(original['navigation']['data']);save()
   target=json.dumps(args.target);macro_js=json.dumps(macro)
   coherent='s.audit.passed&&s.audit.onlinePending===0&&s.streaming.pendingStates===0&&s.streaming.detail.metadataMismatches===0'
   live=f's=>{coherent}&&s.assets[{target}]?.status==="loaded"&&s.assets[{target}].visible&&s.assets[{target}].variant==="full"&&s.ordinary.entry?.hasSession&&s.ordinary.entry.status==="ready"&&s.ordinary.targetRecords.length===1&&s.audit.parents.some(p=>p.near.some(r=>r.visible&&r.groups.some(g=>g.landmark==={target}&&!g.visible)))'
   away=f's=>{coherent}&&s.ordinary.state.loading===0&&s.ordinary.state.activeMacros.length===0&&s.ordinary.ordinaryRegistries===0&&!s.assets[{target}]?.visible&&!s.audit.activePrecise.includes({target})'
   phase='static_adoption';await new_page();await navigate();first=await capture('static-catalog-loaded',live)
   require(first['ordinary']['staticTargetCount']==1 and first['ordinary']['entry']['adoptedIds']==[args.target],'Catalog did not adopt the static target exactly once')
   require(expected_neighbors.issubset(first['audit']['visibleNeighborIDs']),'Preserved static neighbor groups are not visible');before_uuid=first['ordinary']['actualGroupUUID'];before_requests=request_count()
   await page.evaluate('v=>__SHANGHAI_APP__.scene.setOrdinaryCatalog(v.catalog,{districts:__SHANGHAI_APP__.districts,baseURL:v.baseURL})',{'catalog':catalog,'baseURL':project_base})
   adopted=await capture('static-catalog-reused',live)
   require(adopted['ordinary']['actualGroupUUID']==before_uuid and request_count()==before_requests,'Catalog reset duplicated/reloaded the already visible static model')
   await navigate(False);released=await capture('static-catalog-unloaded',away,False);require(len(released['ordinary']['targetRecords'])==1,'Catalog unload deleted a curated static record')
   await navigate();returned=await capture('static-catalog-returned',live);require(returned['ordinary']['entry']['adoptedIds']==[args.target],'Static return was not adopted')
   report['phases'].append({'name':phase,'passed':True,'static_navigation_count':first['ordinary']['staticNavigationCount'],'single_record_reused':True,'warm_reset_same_object_no_new_model_request':True,'unload_static_record_retained':True,'owner_restored':True,'neighbors':len(expected_neighbors)});save()
   phase='dynamic_only';await new_page(dynamic=True)
   before=await snapshot();require(before['ordinary']['staticTargetCount']==0 and not before['ordinary']['targetRecords'] and args.target not in before['ordinary']['staticReplacementIds'],'Top-level test removal did not take effect')
   await navigate();loaded=await capture('dynamic-catalog-loaded',live)
   require(loaded['ordinary']['entry']['adoptedIds']==[] and loaded['ordinary']['staticTargetCount']==0,'Dynamic catalog path unexpectedly reused a static record');require(expected_neighbors.issubset(loaded['audit']['visibleNeighborIDs']),'Dynamic neighbor groups missing')
   held=await page.evaluate('()=>__V6_CAPTURE__.holdTarget()');await navigate(False)
   gone=await capture('dynamic-catalog-unloaded',away,False)
   require(not gone['ordinary']['targetRecords'],'Dynamic record survived macro unload');resource=gone['ordinary']['held'];require(resource['detached'] and resource['geometryCount']>0 and resource['geometriesDisposed']==resource['geometryCount'],'Dynamic GPU geometries not disposed')
   await navigate();again=await capture('dynamic-catalog-returned',live);require(again['ordinary']['actualGroupUUID']!=held['uuid'],'Dynamic return did not reload a released model');require(expected_neighbors.issubset(again['audit']['visibleNeighborIDs']),'Returned dynamic neighbors missing')
   report['phases'].append({'name':phase,'passed':True,'static_navigation_count':loaded['ordinary']['staticNavigationCount'],'runtime_record_added':True,'record_removed_on_unload':True,'geometry_disposal':resource,'returned_new_object':True,'owner_restored':True,'neighbors':len(expected_neighbors)});save()
   phase='dynamic_hash_failure';await new_page(dynamic=True,corrupt=index_url);await navigate()
   failed=f's=>{coherent}&&s.ordinary.entry?.status==="error"&&s.ordinary.state.failed>0&&s.ordinary.state.loading===0&&s.ordinary.state.residentRecords===0&&s.ordinary.ordinaryRegistries===0&&s.ordinary.targetRecords.length===0&&!s.audit.activePrecise.includes({target})&&s.ordinary.targetMacroNear.some(r=>r.visible&&!r.replacement&&r.ids.includes({record["owner"]["feature_local_id"]}))'
   rejected=await capture('dynamic-index-hash-rejected-baseline-visible',failed)
   require(request_count()==0,'Rejected index initiated a precise model request');require(not rejected['ordinary']['entry']['hasSession'],'Bad index installed a macro session')
   expected_ids=set(record['owner']['baseline_near_feature_local_ids']);require(any(r['visible'] and not r['replacement'] and set(r['ids'])==expected_ids for r in rejected['ordinary']['targetMacroNear']),'Failed catalog did not retain the complete baseline near owner set')
   require(any(row['kind']=='equal-length-one-byte-hash-failure' and row['phase']==phase for row in report['test_injections']),'Failure injection did not run')
   require(any('SHA256 differs' in row['text'] and row['phase']==phase for row in report['console_warnings']),'No explicit SHA rejection diagnostic')
   report['phases'].append({'name':phase,'passed':True,'static_navigation_count':rejected['ordinary']['staticNavigationCount'],'precise_model_requests':0,'no_new_records_or_registry':True,'baseline_complete_owner_ids':sorted(expected_ids),'neighbor_count':len(expected_neighbors)});save()
   require(not report['page_errors'] and not report['shader_errors'],'Browser/page/shader errors occurred')
   require(await page.evaluate('window.__CATALOG_CONTEXT_LOSSES__')==0,'WebGL context lost')
   report.update(passed=True,technical_passed=True,pass_scope='Accepted static adoption, explicit dynamic-only response fixture, macro load/unload/return with source/near/far ownership, geometry disposal and SHA-failure baseline preservation. No claim of new visual/source acceptance or hardware performance.')
  except Exception as error:
   report['error']={'type':type(error).__name__,'message':str(error)};progress('FAILED',**report['error'])
   if page:
    try:report['failure_state']=await snapshot()
    except Exception as e:report['failure_state_error']=str(e)
    try:await page.screenshot(path=str(args.output/'failure.png'),timeout=30000)
    except Exception as e:report['failure_screenshot_error']=str(e)
   raise
  finally:
   report['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());save()
   if browser:await browser.close()
 return report
if __name__=='__main__':
 os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'
 asyncio.run(run(parse_args()))
