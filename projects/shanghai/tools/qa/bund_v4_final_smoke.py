import asyncio,json,os,sys,shutil
from pathlib import Path
from playwright.async_api import async_playwright
os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY']='1'
async def main():
 url=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000/'
 out=Path(sys.argv[2] if len(sys.argv)>2 else str(Path.cwd()/'tests/browser-artifacts/bund-v4-final'));out.parent.mkdir(parents=True,exist_ok=True)
 result={'url':url,'page_errors':[],'shader_errors':[],'http_errors':[]}
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--remote-debugging-port=9223'])
  page=await browser.new_page(viewport={'width':1280,'height':850},device_scale_factor=1)
  page.on('pageerror',lambda e:result['page_errors'].append(str(e)))
  page.on('console',lambda m:result['shader_errors'].append(m.text) if 'Shader Error' in m.text or 'VALIDATE_STATUS' in m.text else None)
  page.on('response',lambda r:result['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 and ('/projects/shanghai/' in r.url or '/shanghai_project/' in r.url) else None)
  await page.goto(url,wait_until='domcontentloaded',timeout=60000)
  if await page.get_by_text('Open the page',exact=False).count():await page.get_by_text('Open the page',exact=False).first.click()
  await page.wait_for_function('window.__SHANGHAI_APP__',timeout=180000);print('APP_READY',flush=True)
  await page.wait_for_function('()=>{const a=__SHANGHAI_APP__;return a.scene.getLandmarkState().every(r=>r.status==="loaded"&&!r.loadingModel)&&a.scene.getStreamingState().loading===0}',timeout=240000)
  await page.wait_for_timeout(1500)
  result['walk']=await page.evaluate('()=>({models:__SHANGHAI_APP__.scene.getLandmarkState(),stream:__SHANGHAI_APP__.scene.getStreamingState(),realism:__SHANGHAI_APP__.scene.getRealismState(),districts:__SHANGHAI_APP__.districts.length,clamped:__SHANGHAI_APP__.scene.map.getCenterClampedToGround(),elevation:__SHANGHAI_APP__.scene.map.getCenterElevation(),mode:__SHANGHAI_APP__.mode,tunnelsHidden:__SHANGHAI_APP__.scene.map.getStyle().layers.filter(l=>l.id.startsWith("tunnel_")&&l.type==="line").every(l=>l.layout.visibility==="none")})')
  await page.screenshot(path=str(out)+'-street.png',timeout=90000);print('STREET',flush=True)
  result['corrected_model_hashes']=await page.evaluate('''async()=>{
   const out=[];
   for(const id of ['bund02','bund03','bund17']){
    const r=__SHANGHAI_APP__.landmarks.find(r=>r.id===id);
    const response=await fetch(new URL(r.model,document.baseURI));const buffer=await response.arrayBuffer();
    const sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))).map(v=>v.toString(16).padStart(2,'0')).join('');
    out.push({id,status:response.status,sha256:sha,expected:r.web_sha256,passed:sha===r.web_sha256});
   }return out;
  }''')
  print('HASHES',flush=True)
  await page.set_viewport_size({'width':390,'height':844});await page.wait_for_timeout(1000)
  await page.screenshot(path=str(out)+'-mobile.png',timeout=90000)
  result['mobile']=await page.evaluate('()=>({overflow:document.documentElement.scrollWidth>innerWidth,joystick:!document.getElementById("mobile-controls").hidden,controlsDoNotOverlap:document.getElementById("mobile-controls").getBoundingClientRect().bottom<document.getElementById("location-card").getBoundingClientRect().top})')
  await page.evaluate('()=>{__SHANGHAI_APP__.syncMode("overview",false);}')
  result['overview']=await page.evaluate('()=>({streetBasemap:__SHANGHAI_APP__.scene.getRealismState().streetBasemap,clamped:__SHANGHAI_APP__.scene.map.getCenterClampedToGround(),elevation:__SHANGHAI_APP__.scene.map.getCenterElevation(),tunnelVisibility:__SHANGHAI_APP__.scene.map.getStyle().layers.filter(l=>l.id.startsWith("tunnel_")&&l.type==="line").map(l=>l.layout?.visibility||"visible")})')
  w=result['walk'];v=w['realism'];m=result['mobile'];o=result['overview']
  result['passed']=w['districts']==16 and w['mode']=='walk' and not w['clamped'] and abs(w['elevation']-3)<.01 and w['tunnelsHidden'] and v['surfaces']['textures']==9 and v['lighting']['reflectionReady'] and v['lighting']['reflectionError'] is None and v['traffic']['vehicles']==10 and v['streetBasemap']['active'] and v['streetBasemap']['ready'] and not o['streetBasemap']['active'] and o['clamped'] and o['elevation']==0 and all(t=='visible' for t in o['tunnelVisibility']) and not m['overflow'] and m['joystick'] and m['controlsDoNotOverlap'] and all(r['passed'] for r in result['corrected_model_hashes']) and not result['page_errors'] and not result['shader_errors'] and not result['http_errors']
  result['renderer_environment']='Headless Chromium / SwiftShader software WebGL; not a hardware performance benchmark.'
  out.with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('RESULT',result['passed'],flush=True)
  await browser.close()
asyncio.run(main())
