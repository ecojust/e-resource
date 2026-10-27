#!/usr/bin/env python3
"""Continue actual navigation after retained v1 checkpoints; trusted mouse only."""
import json,time,traceback,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_navigation import now,metres,proxy
BASE='http://127.0.0.1:8894/'
ROOT=Path('/workspace/shanghai_expansion/navigation-v14/qa');out=ROOT/'actual-v2';out.mkdir(exist_ok=True)
prior=json.loads((ROOT/'actual-v1/browser.json').read_text());done={x['id'] for x in prior['model_checks'] if x['passed']}
rows=json.loads(Path('/workspace/shanghai_project/data/landmarks.json').read_text());remaining=[x for x in rows if x['id'] not in done]
r={'schema':'actual-landmark-navigation-remaining-v14','started_at':now(),'passed':False,'prior_verified_ids':sorted(done),'checks':[],'actions':[],'page_errors':[],'http_errors':[],'network_failures':[],'console_errors':[],'captures':[],'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
def save():(out/'browser.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
def stage(s):r['stage']=s;save();print(s,flush=True)
def screenshot(page,name):
 p=out/(name+'.png');page.screenshot(path=str(p),timeout=60000);r['captures'].append({'file':str(p),'bytes':p.stat().st_size});save()
def click(page,selector):
 started=time.monotonic()
 hit=page.locator(selector).evaluate('''e=>{e.scrollIntoView({block:'nearest'});const b=e.getBoundingClientRect(),x=b.x+b.width/2,y=b.y+b.height/2;return {x,y,width:b.width,height:b.height,hit:e.contains(document.elementFromPoint(x,y)),viewport:[innerWidth,innerHeight]}}''',timeout=20000)
 assert hit['width']>0 and hit['height']>0 and hit['hit'],(selector,hit)
 assert 0<=hit['x']<=hit['viewport'][0] and 0<=hit['y']<=hit['viewport'][1],hit
 page.mouse.click(hit['x'],hit['y']);r['actions'].append({'selector':selector,'hit':hit,'seconds':round(time.monotonic()-started,3)});save()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'])
 try:
  ctx=browser.new_context(viewport={'width':1040,'height':760},device_scale_factor=1,proxy=proxy());page=ctx.new_page();page.set_default_timeout(150000)
  page.on('pageerror',lambda e:r['page_errors'].append(str(e)))
  page.on('console',lambda m:r['console_errors'].append(m.text) if m.type=='error' else None)
  page.on('response',lambda x:r['http_errors'].append({'url':x.url,'status':x.status}) if x.status>=400 else None)
  page.on('requestfailed',lambda x:r['network_failures'].append({'url':x.url,'error':x.failure}) if 'ERR_ABORTED' not in str(x.failure) else None)
  stage('START '+remaining[0]['id']);page.goto(BASE+'index.html#landmark='+remaining[0]['id']+'&mode=walk',wait_until='domcontentloaded')
  page.wait_for_function('()=>window.__SHANGHAI_APP__ && document.getElementById("loading").classList.contains("loaded")')
  for row in remaining:
   ident=row['id'];started=time.monotonic();stage('OPEN_PANEL '+ident)
   if page.locator('#panel-toggle').get_attribute('aria-expanded')!='true':click(page,'#panel-toggle')
   stage('SEARCH '+ident);click(page,'#landmark-tab');page.locator('#place-search').fill(row['name'],timeout=20000)
   stage('CLICK '+ident);click(page,'#place-list button[data-place="'+ident+'"]')
   page.wait_for_function('(id)=>__SHANGHAI_APP__.mode==="walk"&&new URLSearchParams(location.hash.slice(1)).get("landmark")===id',arg=ident,timeout=20000)
   pos=page.evaluate('()=>({...__SHANGHAI_APP__.controller.position})');pose=row.get('navigation',{}).get('walkStart',row['walkStart']);distance=metres(pos,pose)
   check={'id':ident,'name':row['name'],'position':pos,'reviewed_pose':pose,'distance_m':distance,'mode':'walk','passed':False};r['checks'].append(check);save();assert distance<25,check
   stage('LOAD_FULL '+ident)
   try:
    page.wait_for_function('(id)=>{const s=__SHANGHAI_APP__.scene.getLandmarkAssetState(id);return s.status==="loaded"&&s.visible&&s.variant==="full"}',arg=ident,timeout=150000)
    check['asset']=page.evaluate('(id)=>__SHANGHAI_APP__.scene.getLandmarkAssetState(id)',ident);assert check['asset']['triangles']>0
    check['passed']=True
    if ident in ['oriental-pearl','shanghai-tower']:screenshot(page,ident+'-walk')
   except Exception as e:
    check['error']=str(e);check['asset']=page.evaluate('(id)=>__SHANGHAI_APP__.scene.getLandmarkAssetState(id)',ident)
   check['elapsed_seconds']=round(time.monotonic()-started,2);save()
  stage('MOBILE_APP_ENTRY');r['mobile_app_entry']=[]
  for width in [375,320]:
   page.set_viewport_size({'width':width,'height':812});page.wait_for_timeout(250)
   entry=page.locator('a.landmark-directory-link');bounds=entry.bounding_box();assert bounds and bounds['x']>=0 and bounds['x']+bounds['width']<=width and bounds['y']>=0,bounds
   hit=entry.evaluate('(e)=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}');assert hit
   r['mobile_app_entry'].append({'viewport_width':width,'bounds':bounds,'not_occluded':hit})
  screenshot(page,'app-mobile320')
  stage('INVALID_HASH_NOTICE');page.evaluate('()=>location.hash="landmark=does-not-exist&mode=walk"');page.wait_for_timeout(300)
  r['invalid_hash_notice']=page.locator('#toast').inner_text();assert '地标' in r['invalid_hash_notice']
  stage('MOBILE_ENTRY_CLICK');click(page,'a.landmark-directory-link');page.wait_for_url('**/landmarks.html');assert page.locator('a[data-landmark]').count()==31;r['mobile_directory_click']=True
  r['passed']=all(x['passed'] for x in r['checks']) and len(r['checks'])+len(done)==31 and not r['page_errors'];r['finished_at']=now();save();print(json.dumps({'passed':r['passed'],'checks':len(r['checks']),'prior':len(done),'report':str(out/'browser.json')},ensure_ascii=False),flush=True)
 except Exception as e:
  r['error']=str(e);r['traceback']=traceback.format_exc();r['finished_at']=now();save()
  try:
   r['failure_state']=page.evaluate('()=>({hash:location.hash,mode:window.__SHANGHAI_APP__?.mode,panel:document.getElementById("panel-toggle")?.getAttribute("aria-expanded"),name:document.getElementById("location-name")?.textContent,toast:document.getElementById("toast")?.textContent})');screenshot(page,'failure')
  except Exception:pass
  save();print(r['traceback'],flush=True);raise
 finally:browser.close()
