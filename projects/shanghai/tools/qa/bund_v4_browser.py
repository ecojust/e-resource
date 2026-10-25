import asyncio,json,os,sys,math,time,shutil
from pathlib import Path
from playwright.async_api import async_playwright
os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'
async def main():
 url=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000/'
 out=Path(sys.argv[2] if len(sys.argv)>2 else str(Path.cwd()/'tests/browser-artifacts/bund-v4'));out.parent.mkdir(parents=True,exist_ok=True)
 result={'url':url,'page_errors':[],'shader_errors':[],'failed_requests':[]}
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--remote-debugging-port=9223'])
  page=await browser.new_page(viewport={'width':1280,'height':850},device_scale_factor=1)
  page.on('pageerror',lambda e:result['page_errors'].append(str(e)))
  page.on('console',lambda m:result['shader_errors'].append(m.text) if 'Shader Error' in m.text or 'VALIDATE_STATUS' in m.text else None)
  page.on('requestfailed',lambda r:result['failed_requests'].append({'url':r.url,'error':r.failure}))
  await page.goto(url,wait_until='domcontentloaded',timeout=60000)
  if await page.get_by_text('Open the page',exact=False).count():await page.get_by_text('Open the page',exact=False).first.click()
  await page.wait_for_function('window.__SHANGHAI_APP__',timeout=240000);print('APP_READY',flush=True)
  await page.wait_for_function('()=>{const a=__SHANGHAI_APP__;return a.scene.getLandmarkState().every(r=>r.status==="loaded"&&!r.loadingModel)&&a.scene.getStreamingState().loading===0}',timeout=240000)
  await page.wait_for_timeout(2500)
  result['initial']=await page.evaluate('()=>({mode:__SHANGHAI_APP__.mode,districts:__SHANGHAI_APP__.districts.length,models:__SHANGHAI_APP__.scene.getLandmarkState(),stream:__SHANGHAI_APP__.scene.getStreamingState(),realism:__SHANGHAI_APP__.scene.getRealismState(),centerElevation:__SHANGHAI_APP__.scene.map.getCenterElevation(),clamped:__SHANGHAI_APP__.scene.map.getCenterClampedToGround(),overflow:document.documentElement.scrollWidth>innerWidth})')
  await page.screenshot(path=str(out)+'-street.png',timeout=60000);print('STREET',flush=True)
  shadow_start=await page.evaluate('__SHANGHAI_APP__.scene.getRealismState().lighting.shadowRefreshRequests')
  await page.wait_for_timeout(2500)
  result['stationary_shadow_refreshes']=(await page.evaluate('__SHANGHAI_APP__.scene.getRealismState().lighting.shadowRefreshRequests'))-shadow_start
  before=await page.evaluate('({...__SHANGHAI_APP__.controller.position})')
  await page.keyboard.down('s');await page.wait_for_timeout(1500);await page.keyboard.up('s')
  after=await page.evaluate('({...__SHANGHAI_APP__.controller.position})')
  result['movement_metres']=math.hypot((after['lng']-before['lng'])*111320*math.cos(math.radians(before['lat'])),(after['lat']-before['lat'])*111320)
  await page.evaluate('()=>{const a=__SHANGHAI_APP__;a.syncMode("overview",false);a.scene.map.jumpTo({center:[121.48552,31.23845],zoom:16,pitch:58,bearing:285});}')
  await page.wait_for_function('()=>__SHANGHAI_APP__.scene.getLandmarkState().filter(r=>r.id!=="bund-streets"&&(r.id.startsWith("bund")||r.id==="customs-house")).every(r=>r.activeVariant==="distant"&&!r.loadingModel)',timeout=240000)
  result['overview']=await page.evaluate('()=>({models:__SHANGHAI_APP__.scene.getLandmarkState(),centerElevation:__SHANGHAI_APP__.scene.map.getCenterElevation(),clamped:__SHANGHAI_APP__.scene.map.getCenterClampedToGround(),realism:__SHANGHAI_APP__.scene.getRealismState()})')
  await page.screenshot(path=str(out)+'-overview.png',timeout=60000);print('OVERVIEW_LODS',flush=True)
  await page.evaluate('()=>{__SHANGHAI_APP__.syncMode("walk",false);}')
  await page.wait_for_function('()=>__SHANGHAI_APP__.scene.getLandmarkState().filter(r=>["bund17","bund18","bund19"].includes(r.id)).every(r=>r.activeVariant==="full"&&!r.loadingModel)',timeout=240000)
  result['return_walk']=await page.evaluate('()=>({models:__SHANGHAI_APP__.scene.getLandmarkState(),realism:__SHANGHAI_APP__.scene.getRealismState(),exclusions:__SHANGHAI_APP__.scene.getLandmarkExclusionState()})')
  await page.set_viewport_size({'width':390,'height':844});await page.wait_for_timeout(2000)
  await page.screenshot(path=str(out)+'-mobile.png',timeout=60000)
  result['mobile']=await page.evaluate('()=>({overflow:document.documentElement.scrollWidth>innerWidth,joystick:!document.getElementById("mobile-controls").hidden,mode:__SHANGHAI_APP__.mode,controls_do_not_overlap_card:document.getElementById("mobile-controls").getBoundingClientRect().bottom < document.getElementById("location-card").getBoundingClientRect().top})')
  print('MOBILE',flush=True)
  # A failed distant swap must retain its complete near model and exclusion owner.
  if '127.0.0.1' in url:
   await page.route('**/assets/models/bund/lod-v4/bund18.glb',lambda route:route.abort('failed'))
   await page.evaluate('()=>{const a=__SHANGHAI_APP__;a.syncMode("overview",false);a.scene.map.jumpTo({center:[121.48552,31.23845],zoom:16,pitch:58,bearing:285});}')
   await page.wait_for_function('()=>{const r=__SHANGHAI_APP__.scene.getLandmarkState();return r.find(r=>r.id==="bund17").activeVariant==="distant"&&r.every(r=>!r.loadingModel)}',timeout=240000)
   result['failed_lod_swap']=await page.evaluate('()=>({model:__SHANGHAI_APP__.scene.getLandmarkState().find(r=>r.id==="bund18"),exclusions:__SHANGHAI_APP__.scene.getLandmarkExclusionState(),realism:__SHANGHAI_APP__.scene.getRealismState()})')
   assert result['failed_lod_swap']['model']['status']=='loaded' and result['failed_lod_swap']['model']['activeVariant']=='full'
  initial=result['initial'];realism=initial['realism'];mobile=result['mobile']
  result['passed']=initial['districts']==16 and initial['stream']['total']==1708 and initial['mode']=='walk' and not initial['clamped'] and initial['centerElevation']>2 and realism['surfaces']['textures']==9 and realism['lighting']['reflectionReady'] and not realism['lighting']['reflectionError'] and result['stationary_shadow_refreshes']==0 and result['overview']['clamped'] and result['overview']['centerElevation']==0 and result['movement_metres']>.1 and mobile['joystick'] and mobile['controls_do_not_overlap_card'] and not initial['overflow'] and not mobile['overflow'] and not result['page_errors'] and not result['shader_errors']
  out.with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('RESULT',result['passed'],flush=True)
  await browser.close()
asyncio.run(main())
