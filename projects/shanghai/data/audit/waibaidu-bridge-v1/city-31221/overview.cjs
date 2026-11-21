const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {chromium} = require('playwright');
const [phase, output] = process.argv.slice(2);
const before = phase === 'before', phone = ['phone','touch'].includes(phase);
assert(['before','phone','desktop','mouse','touch'].includes(phase));
const proof = JSON.parse(fs.readFileSync(path.join(__dirname, 'presentation-inputs.json')));
const original = JSON.parse(fs.readFileSync('/workspace/e-resource/projects/shanghai/data/audit/waibaidu-bridge-v1/final-placement-contract.json'));
const stage = proof.rows[before ? '220' : '221'];
const base = 'http://127.0.0.1:' + stage.port + '/';
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const url = base + 'landmarks.html';
const report = {passed:false, phase, base, production:stage.production_sha256, files:{}, errors:[], screenshots:[]};
const finish = () => fs.writeFileSync(path.join(output,'report.json'), JSON.stringify(report,null,2)+'\n');
(async()=>{
 fs.mkdirSync(output,{recursive:true}); const browser = await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--single-process','--no-zygote','--in-process-gpu','--disable-gpu-rasterization','--enable-low-end-device-mode','--disable-gpu-shader-disk-cache','--renderer-process-limit=1','--js-flags=--max-old-space-size=320 --max-semi-space-size=4','--disk-cache-size=2097152']});
 try {
  const page=await browser.newPage({viewport:phone?{width:390,height:844}:before?{width:440,height:380}:{width:700,height:510},deviceScaleFactor:before?0.64:0.85,hasTouch:phone,ignoreHTTPSErrors:true});page.setDefaultTimeout(180000);
  page.on('pageerror',e=>report.errors.push(String(e)));page.on('response',r=>{if(r.status()>=400)report.errors.push({url:r.url(),status:r.status()});});page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')report.errors.push({url:r.url(),failure:r.failure()});});
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
  report.stage='directory-open';finish();
  const card=page.locator('article[data-landmark="'+original.id+'"]');
  assert.equal(await page.locator('article[data-landmark]').count(),stage.count);assert.equal(await card.count(),before?0:1);
  if(before){
    const earlierCard=page.locator('article[data-landmark="huangpu-astor-house-hotel"] .card-foot a[href$="mode=overview"]');
    const near=await earlierCard.count() ? earlierCard.first() : page.locator('article[data-landmark="yangpu-yangshupu-power-turbine-hall"] .card-foot a[href$="mode=overview"]').first();
    report.previousCityEntry=await near.getAttribute('href');finish();
    await near.click();
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.map));
    const box=page.locator('#panel-toggle');if(await box.getAttribute('aria-expanded')==='true')await box.click();
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.jumpTo({center:[c.lng,c.lat],bearing:c.overviewBearing,pitch:c.overviewPitch,zoom:c.overviewZoom});s.loadLandmarks();s.map.triggerRepaint();},original);
  }else if(['mouse','touch'].includes(phase)){
    await clickBeacon(original.id,'yangpu-yangshupu-power-turbine-hall',[original.lng,original.lat],report);
  }else{
    const overview=card.locator('.card-foot a[href$="mode=overview"]'),walk=card.locator('a[href$="mode=walk"]');assert.equal(await walk.count(),1);
    report.walkHref=await walk.getAttribute('href');report.directoryAction=phone?'touch':'mouse';
    if(phone)await overview.tap();else await overview.click();
  }
  report.stage='city-view-positioned';finish();
  await page.exposeBinding('recordCityReadiness',(_,snapshot)=>{report.readiness=snapshot;finish();});
  await page.waitForFunction(({id,before,count,web,lod,roadIds})=>{
    const app=window.__SHANGHAI_APP__,s=app?.scene,m=s?.map,loader=document.querySelector('#loading');if(!s||!m)return false;
    const tiles=m.querySourceFeatures(s.sourceId,{sourceLayer:'transportation'}),state=s.getLandmarkAssetState(id),row=s.getCandidateIntegrationState().active.find(v=>v.id===id);
    const expected=state?.variant==='distant'?lod:web;
    const observed={url:location.href,moving:m.isMoving(),loading:loader&&getComputedStyle(loader).visibility,mode:app.mode,beacons:s.getBuildingBeaconState().count,expectedCount:count,tiles:tiles.length,asset:state?.verifiedAsset?.sha256,expected,active:row?.assetSha256,variant:state?.variant,visible:state?.visible,status:state?.status,zoom:m.getZoom(),center:m.getCenter()};
    if(!window.lastCityReadiness||Date.now()-window.lastCityReadiness>5000){window.lastCityReadiness=Date.now();window.recordCityReadiness(observed);}
    return !m.isMoving()&&loader&&observed.loading==='hidden'&&roadIds.every(i=>tiles.some(f=>f.id===i))&&m.querySourceFeatures(s.sourceId,{sourceLayer:'water'}).length>0&&observed.beacons===count&&(before?!row:state.visible&&observed.asset===expected&&observed.active===expected);
  },{id:original.id,before,count:stage.count,web:original.model_geometry_sha256.web,lod:original.model_geometry_sha256.lod,roadIds:original.bridge_walk.transportation_feature_ids}, {polling:500,timeout:180000});
  report.observed=await page.evaluate(({id,expected})=>{const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,gl=m.painter.context.gl;return {url:location.href,count:s.getBuildingBeaconState().count,mode:app.mode,asset:s.getLandmarkAssetState(id),active:s.getCandidateIntegrationState().active.filter(x=>x.id===id),tiles:s.getStreamingState().active.map(x=>x.id),bridgeSources:[...new Set(m.querySourceFeatures(s.sourceId,{sourceLayer:'transportation'}).filter(f=>expected.includes(f.id)).map(f=>f.id))],water:m.querySourceFeatures(s.sourceId,{sourceLayer:'water'}).length,camera:{center:m.getCenter(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom()},webgl:gl.getError(),contextLost:gl.isContextLost()};},{id:original.id,expected:original.bridge_walk.transportation_feature_ids});
  assert.equal(report.observed.webgl,0);assert.equal(report.observed.contextLost,false);assert(report.observed.water>0);
  assert.deepEqual(report.observed.bridgeSources.sort(),[...original.bridge_walk.transportation_feature_ids].sort());
  if(!before){assert.equal(new URL(report.observed.url).hash,'#landmark='+original.id+'&mode=overview');assert.equal(report.observed.asset.verifiedAsset.sha256,original.model_geometry_sha256[report.observed.asset.variant==='distant'?'lod':'web']);}
  report.stage='render-state-checked';finish();
  const c=await page.context().newCDPSession(page);const bytes=Buffer.from((await c.send('Page.captureScreenshot',{format:'png',fromSurface:true})).data,'base64');await c.detach();const file='map-'+phase+'.png';fs.writeFileSync(path.join(output,file),bytes);report.screenshots.push({file,sha256:hash(bytes),bytes:bytes.length});
  assert.deepEqual(report.errors,[]);report.passed=true;
 }finally{await browser.close();report.closed=true;finish();}
})().catch(e=>{report.failure=String(e.stack||e);finish();process.exitCode=1;});
