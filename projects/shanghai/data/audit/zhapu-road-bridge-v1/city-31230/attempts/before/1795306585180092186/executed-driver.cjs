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
  const page=await browser.newPage({viewport:before?{width:390,height:304}:phone?{width:390,height:844}:{width:850,height:620},deviceScaleFactor:before?.60:phone?.78:.7,hasTouch:phone,ignoreHTTPSErrors:true});page.setDefaultTimeout(180000);
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
    report.bootstrap.productionResourceRequests++;
    try{await route.continue();}
    catch(error){release(request);}
  });
  page.on('response',r=>{if(/\.(glb|glb\.gz|pbf)(?:\?|$)/.test(r.url()))report.bootstrap.productionResourceResponses++;});
  async function clickBeacon(id,prev,center,report) {
    await page.goto(new URL('index.html#landmark='+prev+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()),null,{timeout:180000});
    await jump({center,zoom:16.4,pitch:0,bearing:0,elevation:0,padding:{left:0,right:0,top:0,bottom:0}});
    await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene;const p=s.getBuildingBeaconState().labelPositions.find(x=>x.id===id||x.memberIds?.includes(id));if(!p||s.pickBuildingBeacon(p)!==p.id)return false;const b=s.map.getCanvas().getBoundingClientRect(),el=document.elementFromPoint(b.x+p.x,b.y+p.y);return el===s.map.getCanvas()||el?.closest('.maplibregl-canvas-container');},id,{polling:300,timeout:180000});
    const action=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,p=s.getBuildingBeaconState().labelPositions.find(x=>x.id===id||x.memberIds?.includes(id)),b=s.map.getCanvas().getBoundingClientRect();return {x:b.x+p.x,y:b.y+p.y,id:p.id,group:p.memberIds?.length>0,previous:location.hash,viewport:[innerWidth,innerHeight]};},id);
    assert.equal(new URLSearchParams(action.previous.slice(1)).get('landmark'),prev);
    const touch=phase==='touch';
    if(touch)await page.touchscreen.tap(action.x,action.y);else await page.mouse.click(action.x,action.y);
    if(action.group){const choice=page.locator('dialog.beacon-group-picker[open] [data-landmark="'+id+'"]');if(touch)await choice.tap();else await choice.click();}
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id,{timeout:180000});
    report.realBeacon={...action,landed:id,action:touch?'physical canvas touch':'physical canvas mouse click'};finish();
  }
  async function jump(camera){
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
  }

  const response=await page.goto(url,{waitUntil:'domcontentloaded'});assert.equal(hash(await response.body()),stage.files['landmarks.html'].sha256);
  const card=page.locator('article[data-landmark="'+original.id+'"]');
  assert.equal(await page.locator('article[data-landmark]').count(),stage.count);assert.equal(await card.count(),before?0:1);
  if(before){
    await page.goto(base+'index.html#lng='+original.lng+'&lat='+original.lat+'&mode=overview',{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.map));
    const box=page.locator('#panel-toggle');if(await box.getAttribute('aria-expanded')==='true')await box.click();
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.jumpTo({center:[c.lng,c.lat],bearing:c.overviewBearing,pitch:c.overviewPitch,zoom:c.overviewZoom});s.loadLandmarks();},original);
  }else if(['mouse','touch'].includes(phase)){
    await clickBeacon(original.id,'huangpu-bund-signal-tower',[original.lng,original.lat],report);
  }else{
    const overview=card.locator('.card-foot a[href$="mode=overview"]'),walk=card.locator('a[href$="mode=walk"]');assert.equal(await walk.count(),1);
    report.walkHref=await walk.getAttribute('href');report.directoryAction=phone?'touch':'mouse';
    if(phone)await overview.tap();else await overview.click();
  }
  await page.waitForFunction(({id,before,count,web})=>{
    const app=window.__SHANGHAI_APP__,s=app?.scene,m=s?.map,loader=document.querySelector('#loading');if(!s||!m||m.isMoving()||!loader||getComputedStyle(loader).visibility!=='hidden')return false;
    const tiles=m.querySourceFeatures(s.sourceId,{sourceLayer:'transportation'});
    const a=s.getLandmarkAssetState(id),states=s.getCandidateIntegrationState().active;
    return tiles.length>0&&s.getBuildingBeaconState().count===count&&(before?!states.some(row=>row.id===id):a?.visible&&a.verifiedAsset?.sha256===web&&states.some(row=>row.id===id&&row.assetSha256===web));
  },{id:original.id,before,count:stage.count,web:original.model_geometry_sha256.web}, {polling:400,timeout:240000});
  report.observed=await page.evaluate(({id,expected})=>{const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,gl=m.painter.context.gl;return {url:location.href,count:s.getBuildingBeaconState().count,mode:app.mode,asset:s.getLandmarkAssetState(id),active:s.getCandidateIntegrationState().active.filter(x=>x.id===id),tiles:s.getStreamingState().active.map(x=>x.id),bridgeSources:[...new Set(m.querySourceFeatures(s.sourceId,{sourceLayer:'transportation'}).filter(f=>expected.includes(f.id)).map(f=>f.id))],water:m.querySourceFeatures(s.sourceId,{sourceLayer:'water'}).length,camera:{center:m.getCenter(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom()},webgl:gl.getError(),contextLost:gl.isContextLost()};},{id:original.id,expected:original.bridge_walk.transportation_feature_ids});
  assert.equal(report.observed.webgl,0);assert.equal(report.observed.contextLost,false);assert(report.observed.water>0);
  assert.deepEqual(report.observed.bridgeSources.sort(),[...original.bridge_walk.transportation_feature_ids].sort());
  if(!before){assert.equal(new URL(report.observed.url).hash,'#landmark='+original.id+'&mode=overview');assert.equal(report.observed.asset.verifiedAsset.sha256,original.model_geometry_sha256.web);}
  const c=await page.context().newCDPSession(page);const bytes=Buffer.from((await c.send('Page.captureScreenshot',{format:'png',fromSurface:true})).data,'base64');await c.detach();const file='map-'+phase+'.png';fs.writeFileSync(path.join(output,file),bytes);report.screenshots.push({file,sha256:hash(bytes),bytes:bytes.length});
  assert.deepEqual(report.errors,[]);report.passed=true;
 }finally{await browser.close();report.closed=true;finish();}
})().catch(e=>{report.failure=String(e.stack||e);finish();process.exitCode=1;});
