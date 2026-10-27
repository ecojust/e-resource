#!/usr/bin/env python3
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_navigation import proxy,now
out=Path('/workspace/shanghai_expansion/navigation-v14/qa/mobile-entry-v1');out.mkdir(exist_ok=True)
r={'passed':False,'started_at':now(),'checks':[],'page_errors':[]}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'])
 try:
  context=browser.new_context(viewport={'width':375,'height':812},device_scale_factor=1,proxy=proxy());page=context.new_page();page.set_default_timeout(150000);page.on('pageerror',lambda e:r['page_errors'].append(str(e)))
  page.goto('http://127.0.0.1:8894/index.html#landmark=yangpu-library&mode=walk',wait_until='domcontentloaded')
  page.wait_for_function('()=>window.__SHANGHAI_APP__ && document.getElementById("loading").classList.contains("loaded")')
  for width in [375,320]:
   page.set_viewport_size({'width':width,'height':812});page.wait_for_timeout(250)
   element=page.locator('a.landmark-directory-link');bounds=element.bounding_box();assert bounds and bounds['x']>=0 and bounds['x']+bounds['width']<=width and bounds['y']>=0 and bounds['y']+bounds['height']<812,bounds
   top=element.evaluate('(e)=>{const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest("a")===e}')
   assert top,'Persistent entry occluded'
   r['checks'].append({'viewport_width':width,'bounds':bounds,'not_occluded':top,'href':element.get_attribute('href')})
  page.screenshot(path=str(out/'app-mobile320.png'),timeout=60000)
  page.locator('a.landmark-directory-link').click();page.wait_for_url('**/landmarks.html');assert page.locator('a[data-landmark]').count()==31
  r['click_reached_directory']=True;r['passed']=not r['page_errors']
 finally:
  browser.close();r['finished_at']=now();(out/'browser.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
