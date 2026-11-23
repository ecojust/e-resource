"""Exercise the unmodified city route in system Chromium with a single CDP connection."""
import asyncio,hashlib,json,os,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
from websockets.asyncio.client import connect

base,out,task=sys.argv[1:]; out=Path(out);out.mkdir(exist_ok=False)
subject='xuhui-wukang-129'; macro='14-13718-6695'
VIEW_H=650 if task in ('beacon','place')else 355
def sha(data):return hashlib.sha256(data).hexdigest()
own=Path(__file__);(out/own.name).write_bytes(own.read_bytes())
row,=[v for v in json.load(urllib.request.urlopen(base+'data/landmarks.json'))if v['id']==subject]
result={'base':base,'task':task,'subject':subject,'source_sha256':sha(own.read_bytes()),'source':own.name,'row':row,'start':time.time(),'events':[],'requests':[],'inputs':[],'images':{}}
def save():
 tmp=out/'result.tmp';tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');tmp.replace(out/'result.json')
def dispatch(binary,*args,**kwargs):return subprocess.run([binary,*args],check=True,**kwargs)
async def run():
 with tempfile.TemporaryDirectory(prefix='wukang-',dir=os.environ['TMPDIR']) as profile:
  command=['/usr/bin/chromium','--remote-debugging-port=0','--user-data-dir='+profile,'--no-sandbox','--no-zygote','--single-process','--in-process-gpu','--disable-gpu-rasterization','--disable-dev-shm-usage','--num-raster-threads=1','--disable-background-networking','--disable-component-update','--disable-sync','--disable-translate','--disable-features=Translate,TranslateUI','--disk-cache-size=262144','--disable-gpu-shader-disk-cache','--enable-low-end-device-mode','--window-size=540,'+str(VIEW_H+160),'--window-position=0,0','--force-gpu-mem-available-mb=48','--js-flags=--expose-gc --optimize-for-size --max-old-space-size=145 --max-semi-space-size=1','--ozone-platform=x11','--use-angle=swiftshader','--enable-unsafe-swiftshader','about:blank']
  p=subprocess.Popen(command,stdout=(out/'browser.log').open('wb'),stderr=subprocess.STDOUT);result['chromium']=p.pid;save()
  try:
   f=Path(profile,'DevToolsActivePort')
   while not f.exists() and p.poll() is None:await asyncio.sleep(.10)
   port=int(f.read_text().splitlines()[0])
   with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:%d/json/new?about:blank'%port,method='PUT'))as opened: actual_tab=json.load(opened)
   result['tab_id']=actual_tab.get('id');save()
   for turn in range(80):
    tabs=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%port))
    tar=next((t for t in tabs if t['type']=='page' and t.get('id')==actual_tab.get('id')),None)
    if tar:break
    await asyncio.sleep(.1)
   if not tar:raise RuntimeError('No page target available')
   async with connect(tar['webSocketDebuggerUrl'],max_size=6*1024*1024,compression=None)as ws:
    tasks={};seq=0;sched=set();done=False;first=time.time()
    async def req(m,pa={}):
     nonlocal seq
     seq+=1;n=seq;fut=asyncio.get_running_loop().create_future();tasks[n]=fut
     await ws.send(json.dumps({'id':n,'method':m,'params':pa}));r=await asyncio.wait_for(fut,12)
     if 'error'in r:raise RuntimeError(r['error'])
     return r.get('result',{})
    async def evaluate(code):
     e=await req('Runtime.evaluate',{'expression':code,'returnByValue':True});return e.get('result',{}).get('value')
    def schedule(coro):
     t=asyncio.create_task(coro);sched.add(t);t.add_done_callback(sched.discard)
    async def proceed(k,u):
     from urllib.parse import urlsplit
     path=urlsplit(u).path
     if '/'+subject+'/' in path:result['requests'].append({'path':path,'at':time.time()});save()
     elif '/'+macro+'/'in path and (path.endswith('/far.glb')or '1_1-s1-s0.glb' in path or path.endswith('/READY.json')): await asyncio.sleep(1)
     elif task in ('levels','reverse') and any(v in path for v in ('/xuhui-midget-apartments/','/xuhui-huaihai-road-1768-residence/','/xuhui-bajin-residence/')):
      phase='far' if '/xuhui-midget-apartments/' in path else ('returnedNear' if '/xuhui-huaihai-road-1768-residence/' in path else 'finished')
      for poll in range(420):
       if result.get('phase')==phase:break
       await asyncio.sleep(.25)
      result.setdefault('neighborRequestSchedule',[]).append({'path':path,'releaseTime':time.time(),'phase':result.get('phase')});save()
     else: await asyncio.sleep(max(0,first+90-time.time()))
     try:await req('Fetch.continueRequest',{'requestId':k})
     except:pass
    async def receive():
     try:
      async for msg in ws:
       e=json.loads(msg)
       if 'id'in e:
        fut=tasks.pop(e['id'],None)
        if fut and not fut.done():fut.set_result(e)
       elif e.get('method')=='Fetch.requestPaused':schedule(proceed(e['params']['requestId'],e['params']['request']['url']))
       elif e.get('method')=='Runtime.consoleAPICalled':
        m=e['params']['args'][0].get('value','')
        if isinstance(m,str)and m.startswith('WKG '):result['events'].append(json.loads(m[4:]));save()
     finally:
      for f in tasks.values():
       if not f.done():f.set_exception(ConnectionError('Browser disconnected'))
    receiver=asyncio.create_task(receive())
    try:
     await req('Page.enable');await req('Runtime.enable')
     await req('Emulation.setDeviceMetricsOverride',{'width':440,'height':VIEW_H,'deviceScaleFactor':1,'mobile':False})
     await evaluate("document.body.innerHTML='<i style=\"position:fixed;left:0;top:0;background:#cf2bab;width:9px;height:9px\"></i><b style=\"position:fixed;bottom:0;right:0;background:#1fd35d;width:9px;height:9px\"></b>'")
     await req('Page.bringToFront')
     from PIL import Image
     origin=None
     calibration=out/'viewport-calibration.png'
     for attempt in range(6):
      await asyncio.sleep(.15);dispatch('import','-window','root',str(calibration),env={**os.environ,'MAGICK_THREAD_LIMIT':'1'},timeout=9)
      with Image.open(calibration) as frame:
       px=frame.convert('RGB').load()
       origin=next(((x,y)for y in range(frame.height-VIEW_H+1)for x in range(frame.width-440+1)if px[x,y]==(207,43,171)and px[x+8,y+8]==(207,43,171)and px[x+439,y+VIEW_H-1]==(31,211,93)),None)
      if origin:break
     assert origin,'Both viewport corners must appear in the current X11 display'
     result['viewport']={'x':origin[0],'y':origin[1],'width':440,'height':VIEW_H,'evidence':sha(calibration.read_bytes())};save()
     await req('Fetch.enable',{'patterns':[{'urlPattern':q,'requestStage':'Request'} for q in ['*.glb*','*/READY.json*','*/assets/materials/realism-v4/*']]})
     # The probe records ordinary verified assets from the actual main Three scene.
     src=(own.parent/'early-city-events.js').read_text().replace('TASK_LITERAL',json.dumps(task)).replace('ANCHOR_LITERAL',json.dumps(row['anchor'])).replace('ID_LITERAL',json.dumps(subject))
     (out/'actual-early.js').write_text(src);result['init_sha256']=sha(src.encode());save()
     await req('Page.addScriptToEvaluateOnNewDocument',{'source':src})
     async def click_point(pt):
      xx,yy=pt['x'],pt['y']
      await req('Input.dispatchMouseEvent',{'type':'mouseMoved','x':xx,'y':yy})
      await req('Input.dispatchMouseEvent',{'type':'mousePressed','x':xx,'y':yy,'button':'left','clickCount':1})
      await req('Input.dispatchMouseEvent',{'type':'mouseReleased','x':xx,'y':yy,'button':'left','clickCount':1})
     if task=='directory':
      await req('Page.navigate',{'url':base+'landmarks.html'})
      for i in range(100):
       point=await evaluate('''(()=>{const card=document.querySelector('article[data-landmark="xuhui-wukang-129"]');const link=card?.querySelector('.card-foot a[href*="mode=walk"]');if(!link)return;link.scrollIntoView({block:"center"});let r=link.getBoundingClientRect();let x=r.left+r.width/2,y=r.top+r.height/2;if(!link.contains(document.elementFromPoint(x,y)))return;document.addEventListener("pointerup",e=>sessionStorage.setItem("WKG-actual-directory",JSON.stringify({id:e.target.closest("[data-landmark]")?.dataset.landmark,trusted:e.isTrusted})),{once:true,capture:true});return{x,y,count:document.querySelectorAll("article[data-landmark]").length,href:link.href};})()''')
       if point:break
       await asyncio.sleep(.2)
      assert point;await click_point(point)
      for i in range(50):
       r=await evaluate('''({route:location.hash,source:JSON.parse(sessionStorage.getItem("WKG-actual-directory")||"null")})''')
       if r and r['route'].startswith('#landmark='+subject)and r['source']:break
       await asyncio.sleep(.2)
      assert r['source']['id']==subject and r['source']['trusted'];result['inputs'].append({'directory':point,**r});result['passed']=True;save();await req('Browser.close');return
     await req('Page.navigate',{'url':base+'index.html#landmark='+subject+'&mode=overview'})
     for i in range(155):
      await asyncio.sleep(.8)
      if p.poll()is not None:raise RuntimeError('Chromium exited during map load')
      status=await evaluate('''(()=>{const app=window.__SHANGHAI_APP__;const map=window.realCityMap;const sc=app?.scene;return{ready:!!app,zoom:map?.getZoom(),alt:map?.transform?.getCameraAltitude(),actual:sc?.getLandmarkState().find(r=>r.id==="xuhui-wukang-129"),status:document.getElementById("loading-message")?.textContent,route:location.hash};})()''')
      if i%3==0:result['latest']=status;save()
      if status and status.get('ready'):break
     else:raise RuntimeError('City scene never reached the application ready state')
     await evaluate("window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:false,surfaceNormals:true});")
     async def snap(phase,role,zoom):
      result['phase']=phase;save()
      await evaluate(f"""(()=>{{const s=window.__SHANGHAI_APP__.scene;s.map.stop();s.map.setCenterClampedToGround(false);s.setCamera({{lng:{row['anchor'][0]},lat:{row['anchor'][1]},bearing:12,pitch:{0 if role=='distant' else 46},zoom:{zoom}}});s.map.setPadding({{top:0,bottom:0,left:75,right:0}});s.loadLandmarks();s.refreshBuildingBeacons();return s.map.getZoom()}})()""")
      for n in range(160):
       cur=await evaluate('window.__SHANGHAI_APP__.scene.getLandmarkState().find(r=>r.id==="xuhui-wukang-129")')
       if n%8==0:result['last_model']=cur;save()
       if cur and cur['status']=='loaded'and cur['activeVariant']==role:break
       await asyncio.sleep(.6)
      else:raise RuntimeError('No model receipt for '+role)
      state=await evaluate('''(()=>{const s=window.__SHANGHAI_APP__.scene,a=s.getLandmarkAssetState("xuhui-wukang-129");return {asset:a,camera:{zoom:s.map.getZoom(),height:s.map.transform.getCameraAltitude(),center:s.map.getCenter()},owner:window.actualOwnerWitness,route:location.hash};})()''')
      rolekey='lod'if role=='distant'else'web';assert state['asset']['verifiedAsset']['sha256']==row['assets'][rolekey]['sha256'] and state['asset']['triangles']==row['lod_triangles'if role=='distant'else'triangles']
      result[phase]=state;save()
      for _ in range(140):
       covered=await evaluate("(()=>{let e=document.getElementById('loading');return e&&getComputedStyle(e).visibility!=='hidden'&&Number(getComputedStyle(e).opacity)>.01})()")
       if covered is False:break
       await asyncio.sleep(.1)
      assert covered is False
      await asyncio.sleep(.4)
      target=out/(phase+'-x11.jpg');dispatch('import','-window','root','-quality','83',str(target),env={**os.environ,'MAGICK_THREAD_LIMIT':'1'},timeout=9);cropped=out/(phase+'.jpg')
      with Image.open(target)as frame:frame.crop((origin[0],origin[1],origin[0]+440,origin[1]+VIEW_H)).save(cropped,quality=88)
      result['images'][phase]={'file':cropped.name,'sha256':sha(cropped.read_bytes()),'bytes':cropped.stat().st_size,'displayFrame':target.name,'displaySHA256':sha(target.read_bytes())};save()
     if task in ('beacon','place'):
      if task=='place':
       await evaluate('''(()=>{const t=document.getElementById("panel-toggle");if(t.getAttribute("aria-expanded")!=="true")t.click();if(!document.querySelector('button[data-place="xuhui-wukang-129"]'))document.getElementById("landmark-tab").click();return true})()''')
       for r in range(80):
        point=await evaluate('''(()=>{const el=document.querySelector('button[data-place="xuhui-wukang-129"]');if(!el)return;el.scrollIntoView({block:'center'});let b=el.getBoundingClientRect(),x=b.x+b.width/2,y=b.y+b.height/2;if(!el.contains(document.elementFromPoint(x,y)))return;window.addEventListener('pointerup',e=>{window.lastRealCityPoint={id:e.target.closest('button[data-place]')?.dataset.place,trusted:e.isTrusted};},{once:true,capture:true});return{x,y};})()''')
        if point:break
        await asyncio.sleep(.15)
      else:
       await evaluate('''(()=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map;const t=document.getElementById('panel-toggle');if(t.getAttribute('aria-expanded')==='true')t.click();s.setCamera({lng:%f,lat:%f,bearing:0,pitch:0,zoom:18.4,altitude:0});m.setPadding({left:100,right:0,top:0,bottom:25});s.refreshBuildingBeacons();return true;})()'''%tuple(row['anchor']))
       for r in range(130):
        point=await evaluate('''(()=>{const s=window.__SHANGHAI_APP__.scene,c=s.map.getCanvas(),rect=c.getBoundingClientRect();const b=s.getBuildingBeaconState()?.labelPositions.find(z=>z.id==="xuhui-wukang-129"||z.memberIds?.includes("xuhui-wukang-129"));if(!b)return;for(const dx of [0,.2,-.2])for(const dy of [0,.25,-.25]){const x=b.x+dx*(b.width||0),y=b.y+dy*(b.height||0);if(s.pickBuildingBeacon({x,y})!==b.id||document.elementFromPoint(x+rect.left,y+rect.top)!==c)continue;window.addEventListener('pointerup',e=>{window.lastRealCityPoint={id:s.pickBuildingBeacon({x:e.clientX-rect.left,y:e.clientY-rect.top}),trusted:e.isTrusted,onCanvas:e.target===c};},{once:true,capture:true});return{x:x+rect.left,y:y+rect.top,id:b.id,members:b.memberIds||[]};}})()''')
        if point:break
        if r%15==0:
         location=await evaluate('''(()=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState(),a=b.labelPositions.find(t=>t.id==="xuhui-wukang-129"||t.memberIds?.includes("xuhui-wukang-129"));return{kind:b.labelMode,count:b.count,visible:b.labelPositions.length,layout:a,coveredBy:a?document.elementFromPoint(a.x,a.y)?.outerHTML.slice(0,140):null,canvas:s.map.getCanvas().getBoundingClientRect().toJSON(),url:location.href};})()''')
         result.setdefault('beaconDiagnostics',[]).append(location);save()
        if r in (25,50,75,100):await evaluate('''(()=>{const m=window.__SHANGHAI_APP__.scene.map;const p=m.getPadding();m.setPadding({left:(p.left+95)%350,right:0,top:0,bottom:(p.bottom+55)%200});window.__SHANGHAI_APP__.scene.refreshBuildingBeacons();return true})()''')
        await asyncio.sleep(.15)
      assert point,task+' control never reached an uncovered viewport position'
      await click_point(point);hit=await evaluate('window.lastRealCityPoint');assert hit and hit['trusted']
      if task=='beacon' and point['id']!=subject:
       assert subject in point['members'];group=await evaluate('''(()=>{const el=document.querySelector('dialog.beacon-group-picker[open] [data-landmark="xuhui-wukang-129"]');if(!el)return;el.scrollIntoView();let b=el.getBoundingClientRect();return{x:b.left+b.width/2,y:b.top+b.height/2};})()''');assert group;await click_point(group)
      assert hit['id']==(subject if task=='place'else point['id']);assert task!='beacon' or hit['onCanvas'];route=await evaluate('location.hash');assert 'landmark='+subject in route
      result['inputs'].append({'target':point,'input':hit,'landed':route});save()
     elif task=='levels':
      await snap('near','full',19.60);await snap('far','distant',15.80);await req('HeapProfiler.collectGarbage');await snap('returnedNear','full',19.60)
     elif task=='reverse':
      await snap('far','distant',15.9);await evaluate('window.acceptSceneZoom=true');await req('HeapProfiler.collectGarbage');await snap('returnedNear','full',19.60)
     elif task=='far':await snap('far','distant',15.9)
     else:await snap('near','full',19.60)
     result['passed']=True;save();await req('Browser.close')
    finally:
     for t in list(sched):t.cancel()
     receiver.cancel()
  except Exception as ex:
   if not result.get('passed'):result['failure']=repr(ex)
  finally:
   if p.poll()is None:
    try:p.wait(timeout=2)
    except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=8)
   result['exit']=p.returncode;result['finished']=time.time();save()
asyncio.run(run());sys.exit(0 if result.get('passed') else 1)
