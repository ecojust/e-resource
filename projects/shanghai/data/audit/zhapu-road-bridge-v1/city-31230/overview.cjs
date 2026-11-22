const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {chromium} = require('playwright');
const [phase, output] = process.argv.slice(2);
const before = phase === 'before', phone = ['phone','touch'].includes(phase);
assert(['before','phone','desktop','mouse','touch'].includes(phase));
const proof = JSON.parse(fs.readFileSync(path.join(__dirname, 'presentation-inputs.json')));
const original = JSON.parse(fs.readFileSync('/workspace/e-resource/projects/shanghai/data/audit/zhapu-road-bridge-v1/final-placement-contract.json'));
const stage = proof.rows[before ? '229' : '230'];
const base = 'http://127.0.0.1:' + stage.port + '/';
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const url = base + 'landmarks.html';
const report = {passed:false, phase, base, production:stage.production_sha256, files:{}, errors:[], screenshots:[]};
const finish = () => fs.writeFileSync(path.join(output,'report.json'), JSON.stringify(report,null,2)+'\n');
(async()=>{
 fs.mkdirSync(output,{recursive:true}); const browser = await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--single-process','--in-process-gpu','--no-zygote','--disable-background-networking','--disable-extensions','--disable-gpu-shader-disk-cache','--disable-back-forward-cache','--disable-features=MediaRouter,OptimizationHints,Translate,Prerender2','--disable-breakpad','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--max-old-space-size=160 --max-semi-space-size=2 --optimize-for-size --no-concurrent-recompilation','--force-gpu-mem-available-mb=48','--msaa-sample-count=0','--disable-zero-copy','--disable-accelerated-2d-canvas','--disk-cache-size=2097152']});
 try {
  const page=await browser.newPage({viewport:before?{width:390,height:304}:phone?{width:390,height:844}:{width:850,height:620},deviceScaleFactor:before?.60:phase==='touch'?.64:phone?.78:.7,hasTouch:phone,ignoreHTTPSErrors:true});page.setDefaultTimeout(180000);
  page.on('pageerror',e=>report.errors.push(String(e)));page.on('response',r=>{if(r.status()>=400)report.errors.push({url:r.url(),status:r.status()});});page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')report.errors.push({url:r.url(),failure:r.failure()});});
  const defaultDevice = await page.evaluate(()=>({logicalCores:navigator.hardwareConcurrency,memoryGiB:navigator.deviceMemory}));
  await page.addInitScript(()=>Object.defineProperty(Navigator.prototype,'deviceMemory',{get:()=>2,configurable:true}));
  report.deviceProfile = {original:defaultDevice, logicalCores:1, memoryGiB:2, viewport:page.viewportSize()};
  const cdp=await page.context().newCDPSession(page);
  await cdp.send('Emulation.setHardwareConcurrencyOverride',{hardwareConcurrency:1});
  report.logicalCores=1;finish();
  let gcBusy=false;
  async function reclaim() {
    if(gcBusy||page.isClosed())return;
    gcBusy=true;
    try {await cdp.send('HeapProfiler.collectGarbage');}catch(e){/* The page may close between the two calls. */}
    finally{gcBusy=false;}
  }
  const gcTimer=setInterval(()=>{void reclaim()},9000);gcTimer.unref();

  report.bootstrap={initialViewport:page.viewportSize(),productionResourceRequests:0,productionResourceResponses:0,
    serializedBinaryTransfers:true,mode:before?'One live binary transfer at a time with the original URLs and bytes.':'Two live binary transfers at a time with the original URLs and bytes.'};
  // Stagger starts. If the map cancels an in-flight request, subsequent live requests
  // remain independent. Chromium still fetches every requested URL from its real origin.
  const inFlight = new Map();
  const finished = new WeakSet();
  function release(request){
    finished.add(request);
    inFlight.delete(request);
  }
  page.on('requestfinished',release);
  page.on('requestfailed',release);
  report.bootstrap.mode='At most one pending binary transfer; canceled requests and timed-out permits allow subsequent requests to proceed.';
  report.bootstrap.permitTimeoutMs=2400;
  await page.route(/\.(glb|glb\.gz|pbf)(?:\?|$)/,async route=>{
    const request=route.request();
    while(inFlight.size && !finished.has(request) && !page.isClosed()){
      await new Promise(resolve=>setTimeout(resolve,100));
      for(const [entry,started] of inFlight){
        if(Date.now()-started>report.bootstrap.permitTimeoutMs)inFlight.delete(entry);
      }
    }
    if(finished.has(request)||page.isClosed())return;
    inFlight.set(request,Date.now());
    report.bootstrap.productionResourceRequests++;if(report.bootstrap.productionResourceRequests%15===0)finish();
    try{await route.continue();}
    catch(error){release(request);}
  });
  page.on('response',r=>{if(/\.(glb|glb\.gz|pbf)(?:\?|$)/.test(r.url()))report.bootstrap.productionResourceResponses++;});
  async function clickBeacon(id,prev,center,report) {
    const oldRoute=new URL('index.html',base);
    oldRoute.hash=new URLSearchParams({lng:center[0].toFixed(6),lat:center[1].toFixed(6),mode:'overview'});
    await page.goto(oldRoute.href,{waitUntil:'domcontentloaded'});
    report.phaseStep='river-coordinate-before-beacon';finish();
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()),null,{timeout:180000});
    const navigation=page.locator('#panel-toggle');
    if(await navigation.getAttribute('aria-expanded')==='true')await navigation.click();
    await jump({center,zoom:phase==='touch'?17.74:16.4,pitch:0,bearing:0,elevation:0,padding:{left:0,right:0,top:0,bottom:0}});
    await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene;const p=s.getBuildingBeaconState().labelPositions.find(x=>x.id===id||x.memberIds?.includes(id));if(!p||s.pickBuildingBeacon(p)!==p.id)return false;const b=s.map.getCanvas().getBoundingClientRect(),el=document.elementFromPoint(b.x+p.x,b.y+p.y);return el===s.map.getCanvas()||el?.closest('.maplibregl-canvas-container');},id,{polling:300,timeout:180000});
    const action=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,p=s.getBuildingBeaconState().labelPositions.find(x=>x.id===id||x.memberIds?.includes(id)),b=s.map.getCanvas().getBoundingClientRect();return {x:b.x+p.x,y:b.y+p.y,id:p.id,group:p.memberIds?.length>0,previous:location.hash,viewport:[innerWidth,innerHeight]};},id);
    const priorParams=new URLSearchParams(action.previous.slice(1));
    assert.equal(priorParams.get('lng'),center[0].toFixed(6));assert.equal(priorParams.get('lat'),center[1].toFixed(6));assert(!priorParams.has('landmark'));
    const touch=phase==='touch';report.beaconBeforeInput=action;finish();
    if(touch)await page.touchscreen.tap(action.x,action.y);else await page.mouse.click(action.x,action.y);
    if(action.group){const choice=page.locator('dialog.beacon-group-picker[open] [data-landmark="'+id+'"]');if(touch)await choice.tap();else await choice.click();}
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id,{timeout:180000});
    report.realBeacon={...action,landed:id,action:touch?'physical canvas touch':'physical canvas mouse click'};finish();
  }
  async function jump(camera){
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
  }

  let card;
  if(before||phase==='mouse'||phase==='touch') {
    const response = await page.request.get(url);
    const bytes = await response.body();
    assert.equal(response.status(),200);
    assert.equal(hash(bytes),stage.files['landmarks.html'].sha256);
    const markers = Array.from(bytes.toString('utf8').matchAll(/<article\b[^>]*\bdata-landmark="([^"]+)"/g), m=>m[1]);
    assert.equal(markers.length,stage.count);
    assert.equal(markers.includes(original.id),!before);
    report.directory={url,sha256:hash(bytes),count:markers.length,containsNewBridge:markers.includes(original.id)};
    await response.dispose();
    finish();
  } else {
    const response=await page.goto(url,{waitUntil:'domcontentloaded'});
    assert.equal(hash(await response.body()),stage.files['landmarks.html'].sha256);
    card=page.locator('article[data-landmark="'+original.id+'"]');
    assert.equal(await page.locator('article[data-landmark]').count(),stage.count);
    assert.equal(await card.count(),1);
    finish();
  }
  if(before){
    report.phaseStep='open-original-coordinate';finish();
    await page.goto(base+'index.html#lng='+original.lng.toFixed(6)+'&lat='+original.lat.toFixed(6)+'&mode=overview',{waitUntil:'domcontentloaded'});
    report.phaseStep='original-coordinate-loaded';finish();
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.map));
    const box=page.locator('#panel-toggle');if(await box.getAttribute('aria-expanded')==='true')await box.click();
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.jumpTo({center:[c.lng,c.lat],bearing:c.overviewBearing,pitch:c.overviewPitch,zoom:c.overviewZoom+.14});s.loadLandmarks();},original);
  }else if(['mouse','touch'].includes(phase)){
    await clickBeacon(original.id,'huangpu-bund-signal-tower',[original.lng,original.lat],report);
  }else{
    const overview=card.locator('.card-foot a[href$="mode=overview"]'),walk=card.locator('a[href$="mode=walk"]');assert.equal(await walk.count(),1);
    report.walkHref=await walk.getAttribute('href');report.directoryAction=phone?'touch':'mouse';
    if(phone)await overview.tap();else await overview.click();
  }
  report.phaseStep='wait-visible-bridge-and-old-ground';finish();
  if(phase==='touch'){
    const frames=await page.context().newCDPSession(page);
    let armed=false,last=null;
    frames.on('Page.screencastFrame',ev=>{
      if(armed && !last){
        const data=Buffer.from(ev.data,'base64');
        if(data.length>3000 && data.subarray(1,4).toString()==='PNG'){
          last={bytes:data,metadata:ev.metadata};fs.writeFileSync(path.join(output,'map-touch.png'),data);
        }
      }
      frames.send('Page.screencastFrameAck',{sessionId:ev.sessionId}).catch(()=>{});
    });
    await frames.send('Page.enable');
    await frames.send('Page.startScreencast',{format:'png',maxWidth:390,maxHeight:844,everyNthFrame:1});
    const deadline=Date.now()+90000;
    while(Date.now()<deadline&&!report.observed){
      const state=await page.evaluate(({id,sources,near,far})=>{
        const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,asset=s.getLandmarkAssetState(id),sel=s.getCandidateIntegrationState().active.find(x=>x.id===id),gl=m.painter.context.gl;
        const variant=asset?.verifiedAsset?.variant;if(!sel||!asset?.visible||!['web','lod'].includes(variant))return null;
        const expected=variant==='lod'?far:near;
        if(asset.verifiedAsset.sha256!==expected||sel.assetSha256!==expected||m.isMoving()||getComputedStyle(document.querySelector('#loading')).visibility!=='hidden')return null;
        const road=[...new Set(m.querySourceFeatures(s.sourceId,{sourceLayer:'transportation'}).filter(f=>sources.includes(f.id)).map(f=>f.id))];
        const water=m.querySourceFeatures(s.sourceId,{sourceLayer:'water'}).length;
        if(road.length!==sources.length||!water)return null;
        return {url:location.href,count:s.getBuildingBeaconState().count,mode:a.mode,asset:{id,status:asset.status,variant:asset.variant,visible:asset.visible,verifiedAsset:asset.verifiedAsset},active:[sel],bridgeSources:road,water,camera:{center:m.getCenter(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom()},webgl:gl.getError(),contextLost:gl.isContextLost()};
      },{id:original.id,sources:original.bridge_walk.transportation_feature_ids,near:original.model_geometry_sha256.web,far:original.model_geometry_sha256.lod});
      if(state){report.observed=state;report.phaseStep='verified-live-touch-frame';report.actualSelectedVariant=state.asset.verifiedAsset.variant;finish();armed=true;await page.evaluate(()=>window.__SHANGHAI_APP__.scene.map.triggerRepaint());}
      else await new Promise(r=>setTimeout(r,100));
    }
    assert(report.observed && report.observed.count===stage.count && !report.observed.contextLost && report.observed.webgl===0);
    assert.equal(new URL(report.observed.url).hash,'#landmark='+original.id+'&mode=overview');
    while(!last && Date.now()<deadline){await page.evaluate(()=>window.__SHANGHAI_APP__.scene.map.triggerRepaint());await new Promise(r=>setTimeout(r,100));}
    assert(last && last.bytes.length>3000);
    report.screenshots=[{file:'map-touch.png',sha256:hash(last.bytes),bytes:last.bytes.length,source:'Chromium compositor PNG after verified touch selection',metadata:last.metadata}];
    assert.deepEqual(report.errors,[]);report.passed=true;finish();
    await frames.send('Page.stopScreencast');await frames.detach();return;
  }

  let checking=false;
  const probe=async()=>{
    if(checking||page.isClosed())return;checking=true;
    try{
      const actual=await page.evaluate(ident=>{
        const s=window.__SHANGHAI_APP__?.scene,m=s?.map;if(!s||!m)return null;
        const asset=s.getLandmarkAssetState(ident);const active=s.getCandidateIntegrationState().active?.find(v=>v.id===ident);const ld=document.querySelector('#loading');return {selectedVariant:asset?.variant,verifiedVariant:asset?.verifiedAsset?.variant,verifiedSha256:asset?.verifiedAsset?.sha256,assetVisible:asset?.visible,activeVariant:active?.variant,activeSha:active?.assetSha256,moving:m.isMoving(),visible:ld&&getComputedStyle(ld).visibility,loaderClass:ld?.className,loaderOpacity:ld&&getComputedStyle(ld).opacity,loaderMessage:document.querySelector('#loading-message')?.innerText,hud:document.querySelector('#live-status')?.innerText,tiles:m.querySourceFeatures(s.sourceId,{sourceLayer:'transportation'}).length,water:m.querySourceFeatures(s.sourceId,{sourceLayer:'water'}).length,
          count:s.getBuildingBeaconState()?.count,zoom:m.getZoom(),center:m.getCenter(),asset:s.getLandmarkAssetState(ident)?.status,active:s.getCandidateIntegrationState().active?.some(v=>v.id===ident)};
      },original.id);
      if(actual){(report.originalFrameHistory??=[]).push(actual);finish();}
    }catch(e){report.lastProbeError=String(e);finish();}
    finally{checking=false;}
  };
  await probe();
  if(before){
    const diagnostic=await page.context().newCDPSession(page);
    const capture=await diagnostic.send('Page.captureScreenshot',{format:'jpeg',quality:66,fromSurface:true});
    fs.writeFileSync(path.join(output,'first-original-frame.jpg'),Buffer.from(capture.data,'base64'));
    await diagnostic.detach();
    report.firstOriginalFrame={file:'first-original-frame.jpg',sha256:hash(fs.readFileSync(path.join(output,'first-original-frame.jpg')))};finish();
  }
  const monitor=setInterval(probe,3000);monitor.unref();
  await page.waitForFunction(({id,before,count,web,lod,tap})=>{
    const app=window.__SHANGHAI_APP__,s=app?.scene,m=s?.map,loader=document.querySelector('#loading');if(!s||!m||m.isMoving()||!loader||getComputedStyle(loader).visibility!=='hidden')return false;
    const tiles=m.querySourceFeatures(s.sourceId,{sourceLayer:'transportation'});
    const a=s.getLandmarkAssetState(id),states=s.getCandidateIntegrationState().active;const expected=tap && a?.verifiedAsset?.variant==='lod' && ['distant','lod'].includes(a?.variant) ? lod : web;
    return tiles.length>0&&s.getBuildingBeaconState().count===count&&(before?!states.some(row=>row.id===id):a?.visible&&a.verifiedAsset?.sha256===expected&&states.some(row=>row.id===id&&row.assetSha256===expected));
  },{id:original.id,before,count:stage.count,web:original.model_geometry_sha256.web,lod:original.model_geometry_sha256.lod,tap:phase==='touch'}, {polling:300,timeout:240000});
  clearInterval(monitor);
  report.observed=await page.evaluate(({id,expected})=>{const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,gl=m.painter.context.gl;return {url:location.href,count:s.getBuildingBeaconState().count,mode:app.mode,asset:s.getLandmarkAssetState(id),active:s.getCandidateIntegrationState().active.filter(x=>x.id===id),tiles:s.getStreamingState().active.map(x=>x.id),bridgeSources:[...new Set(m.querySourceFeatures(s.sourceId,{sourceLayer:'transportation'}).filter(f=>expected.includes(f.id)).map(f=>f.id))],water:m.querySourceFeatures(s.sourceId,{sourceLayer:'water'}).length,camera:{center:m.getCenter(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom()},webgl:gl.getError(),contextLost:gl.isContextLost()};},{id:original.id,expected:original.bridge_walk.transportation_feature_ids});
  assert.equal(report.observed.webgl,0);assert.equal(report.observed.contextLost,false);assert(report.observed.water>0);
  assert.deepEqual(report.observed.bridgeSources.sort(),[...original.bridge_walk.transportation_feature_ids].sort());
  if(!before){assert.equal(new URL(report.observed.url).hash,'#landmark='+original.id+'&mode=overview');const role=phase==='touch'&&report.observed.asset.verifiedAsset.variant==='lod'&&['distant','lod'].includes(report.observed.asset.variant)?'lod':'web';assert.equal(report.observed.asset.verifiedAsset.sha256,original.model_geometry_sha256[role]);report.actualSelectedVariant=role;}
  const c=await page.context().newCDPSession(page);const bytes=Buffer.from((await c.send('Page.captureScreenshot',{format:'png',fromSurface:true})).data,'base64');await c.detach();const file='map-'+phase+'.png';fs.writeFileSync(path.join(output,file),bytes);report.screenshots.push({file,sha256:hash(bytes),bytes:bytes.length});
  assert.deepEqual(report.errors,[]);report.passed=true;
 }finally{await browser.close();report.closed=true;finish();}
})().catch(e=>{report.failure=String(e.stack||e);finish();process.exitCode=1;});
