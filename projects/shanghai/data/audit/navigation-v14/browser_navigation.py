#!/usr/bin/env python3
"""Actual browser navigation check; no mocked requests or production changes."""
import argparse, json, math, os, time, traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qs
from playwright.sync_api import sync_playwright


def now():return datetime.now(timezone.utc).isoformat()
def metres(a,b):
 return math.hypot((a['lng']-b[0])*111319.49*math.cos(b[1]*math.pi/180),(a['lat']-b[1])*111319.49)
def proxy():
 raw=os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
 if not raw:return None
 u=urlsplit(raw);o={'server':u.scheme+'://'+u.hostname+(':'+str(u.port) if u.port else ''),'bypass':'localhost,127.0.0.1'}
 if u.username:o['username']=unquote(u.username)
 if u.password:o['password']=unquote(u.password)
 return o

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--url',default='http://127.0.0.1:8894/');ap.add_argument('--output',required=True);ap.add_argument('--timeout-ms',type=int,default=150000);a=ap.parse_args()
 out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 rows=json.loads(Path('/workspace/shanghai_project/data/landmarks.json').read_text());expected={x['id'] for x in rows}
 report={'schema':'actual-landmark-direct-navigation-v14','started_at':now(),'passed':False,'model_checks':[],'page_errors':[],'console_errors':[],'network_failures':[],'http_errors':[],'captures':[],'requests':[]}
 def save():
  (out/'browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 def stage(x):print(x,flush=True);report['stage']=x;save()
 def capture(page,name):
  path=out/(name+'.png');page.screenshot(path=str(path),timeout=60000);report['captures'].append({'file':str(path),'bytes':path.stat().st_size});save()
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'])
  ctx=browser.new_context(viewport={'width':1280,'height':860},device_scale_factor=1,proxy=proxy());page=ctx.new_page();page.set_default_timeout(a.timeout_ms)
  page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
  page.on('console',lambda m:report['console_errors'].append(m.text) if m.type=='error' else None)
  page.on('requestfailed',lambda r:report['network_failures'].append({'url':r.url,'error':r.failure}) if 'ERR_ABORTED' not in str(r.failure) else None)
  page.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  page.on('request',lambda r:report['requests'].append(r.url) if '.glb' in r.url else None)
  try:
   stage('DIRECTORY_DESKTOP')
   page.goto(a.url+'landmarks.html',wait_until='networkidle')
   links=page.locator('a[href*="index.html#landmark="]');hrefs=links.evaluate_all('(xs)=>xs.map(x=>x.getAttribute("href"))')
   ids=[parse_qs(urlsplit(x).fragment)['landmark'][0] for x in hrefs]
   assert set(ids)==expected,(set(ids)^expected)
   assert len(ids)==len(expected),'Duplicate landmark entries'
   report['directory']={'count':len(ids),'ids':ids,'all_walk':all(parse_qs(urlsplit(x).fragment).get('mode')==['walk'] for x in hrefs)}
   assert report['directory']['all_walk']
   search=page.locator('input[type="search"]');assert search.count()==1
   search.fill('杨浦');page.wait_for_timeout(150)
   visible=links.evaluate_all('(xs)=>xs.filter(x=>x.getClientRects().length).map(x=>x.getAttribute("href"))')
   assert len(visible)==1 and 'yangpu-library' in visible[0],visible
   search.fill('');capture(page,'directory-desktop')
   page.set_viewport_size({'width':375,'height':812});page.wait_for_timeout(150)
   overflow=page.evaluate('()=>({width:innerWidth,scroll:document.documentElement.scrollWidth})');assert overflow['scroll']<=overflow['width'],overflow
   report['directory']['mobile']=overflow;capture(page,'directory-mobile')
   page.set_viewport_size({'width':320,'height':812});page.wait_for_timeout(150)
   narrow=page.evaluate('()=>({width:innerWidth,scroll:document.documentElement.scrollWidth})');assert narrow['scroll']<=narrow['width'],narrow;report['directory']['mobile320']=narrow
   nojs=browser.new_context(java_script_enabled=False,viewport={'width':375,'height':812},proxy=proxy());np=nojs.new_page();np.goto(a.url+'landmarks.html');assert np.locator('a[data-landmark]').count()==31;report['directory']['without_javascript']=31;nojs.close()
   page.set_viewport_size({'width':1280,'height':860})
   stage('YANGPU_GENUINE_DIRECTORY_CLICK')
   page.locator('a[href="index.html#landmark=yangpu-library&mode=walk"]').click()
   page.wait_for_function('()=>window.__SHANGHAI_APP__ && __SHANGHAI_APP__.mode==="walk" && document.getElementById("loading").classList.contains("loaded")')
   yangpu=next(x for x in rows if x['id']=='yangpu-library');ypose=yangpu.get('navigation',{}).get('walkStart',yangpu['walkStart'])
   state=page.evaluate('()=>({position:{...__SHANGHAI_APP__.controller.position},name:document.getElementById("location-name").textContent,hash:location.hash})')
   assert 'yangpu-library' in state['hash'];assert metres(state['position'],ypose)<25,state
   page.wait_for_function('()=>{const s=__SHANGHAI_APP__.scene.getLandmarkAssetState("yangpu-library");return s.status==="loaded"&&s.visible&&s.variant==="full"}',timeout=a.timeout_ms)
   state['asset']=page.evaluate('()=>__SHANGHAI_APP__.scene.getLandmarkAssetState("yangpu-library")');state['distance_m']=metres(state['position'],ypose);state['first_model_requests']=report['requests'][:8]
   report['initial_direct_link']=state;capture(page,'yangpu-direct-walk')
   stage('SAME_PAGE_HASH_TRANSITION')
   page.evaluate('()=>location.hash="landmark=jingan-sihang-warehouse&mode=walk"')
   page.wait_for_function('()=>document.getElementById("location-name").textContent.includes("四行仓库")&&__SHANGHAI_APP__.mode==="walk"')
   report['hash_transition']=page.evaluate('()=>({hash:location.hash,position:{...__SHANGHAI_APP__.controller.position},name:document.getElementById("location-name").textContent})')
   target=next(x for x in rows if x['id']=='jingan-sihang-warehouse');pose=target['navigation']['walkStart'];assert metres(report['hash_transition']['position'],pose)<25
   stage('ALL_LANDMARK_UI_SELECTIONS')
   # Geography-grouped ordering keeps streaming pressure bounded without mutating caches.
   for row in rows:
    started=time.monotonic();rid=row['id'];stage('SELECT '+rid)
    page.locator('#overview-mode').click()
    if page.locator('#panel-toggle').get_attribute('aria-expanded')!='true':page.locator('#panel-toggle').click()
    page.locator('#landmark-tab').click();page.locator('#place-search').fill(row['name'])
    page.locator('#place-list button[data-place="'+rid+'"]').click()
    page.wait_for_function('(id)=>__SHANGHAI_APP__.mode==="walk"&&new URLSearchParams(location.hash.slice(1)).get("landmark")===id',arg=rid)
    pos=page.evaluate('()=>({...__SHANGHAI_APP__.controller.position})');pose=row.get('navigation',{}).get('walkStart',row['walkStart']);distance=metres(pos,pose)
    check={'id':rid,'name':row['name'],'position':pos,'reviewed_pose':pose,'distance_m':distance,'mode':'walk','passed':False}
    report['model_checks'].append(check);save();assert distance<25,check
    try:
     page.wait_for_function('(id)=>{const s=__SHANGHAI_APP__.scene.getLandmarkAssetState(id);return s.status==="loaded"&&s.visible&&s.variant==="full"}',arg=rid,timeout=a.timeout_ms)
     check['asset']=page.evaluate('(id)=>__SHANGHAI_APP__.scene.getLandmarkAssetState(id)',rid);assert check['asset']['triangles']>0
     check['passed']=True
     if rid in ['oriental-pearl','shanghai-tower']:capture(page,rid+'-walk')
    except Exception as e:
     check['error']=str(e);check['asset']=page.evaluate('(id)=>__SHANGHAI_APP__.scene.getLandmarkAssetState(id)',rid)
    check['elapsed_seconds']=round(time.monotonic()-started,2);save()
   stage('INVALID_HASH_NOTICE')
   page.evaluate('()=>location.hash="landmark=does-not-exist&mode=walk"');page.wait_for_timeout(1000)
   report['invalid_hash_notice']=page.locator('#toast').inner_text();assert report['invalid_hash_notice']
   report['passed']=all(x['passed'] for x in report['model_checks']) and len(report['model_checks'])==len(rows) and not report['page_errors']
   report['finished_at']=now();save();print(json.dumps({'passed':report['passed'],'count':len(report['model_checks']),'path':str(out/'browser.json')},ensure_ascii=False),flush=True)
  except Exception as e:
   report['error']=str(e);report['traceback']=traceback.format_exc();report['finished_at']=now();save();print(report['traceback'],flush=True);raise
  finally:browser.close()
if __name__=='__main__':main()
