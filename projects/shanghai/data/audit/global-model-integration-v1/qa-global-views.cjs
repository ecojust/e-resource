/* Actual default-rendering global views; a single WebGL page. MIT. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{createHash}=require('crypto');
const base=process.env.MODEL_BASE_URL||'http://127.0.0.1:8782/',out=process.env.QA_OUTPUT_DIR||__dirname;
const project=path.resolve(__dirname,'../../..'),sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function run(page,loadedRuntime={}){
 const cat=JSON.parse(fs.readFileSync(path.join(project,'data/candidate-city-integrations.json')));
 const views=[['huangpu-grand-theatre','grand',20.3,40],['hongkou-luxun-residence-facade','luxun',21.0,25],['chongming-pan-pool-bridge','pan-pool',20.8,25],['chongming-stele-corridors','stele-courtyard',20.1,25],['xuhui-soong-ching-ling-residence','soong',20,25]];
 const cameraMode=process.env.QA_CAMERA_MODE||'default';
 const report={generatedAt:new Date().toISOString(),completed:false,scope:'Single 960x720 Chromium page, default realtime shadows retained, no quality downgrade; default-entry camera and actual beacon overlays.',visualAcceptance:'Screenshot capture completion is not visual acceptance; see browser-visual-review.json for actual image review.',cameraMode,catalog_sha256:sha(path.join(project,'data/candidate-city-integrations.json')),runtime:{},views:[],errors:[],warnings:[]};
 for(const name of ['app.js','map-scene.js','candidate-city-clipping.js','candidate-city-integrations.js','building-beacons.js','candidate-overview-camera.js'])report.runtime[name]=sha(path.join(project,'src',name));
 Object.assign(report.runtime,loadedRuntime);
 const bindingPath=path.join(out,'browser-runtime-bindings.json');if(fs.existsSync(bindingPath)){const binding=JSON.parse(fs.readFileSync(bindingPath));Object.assign(report.runtime,binding.runtime);report.browserRuntimeBinding='browser-runtime-bindings.json';report.laterFaultPathDelta='Any subsequent city-detail-streamer near-index error-branch repair is covered by independent fault injection, not exercised or claimed by this normal browser session.';}
 const save=()=>fs.writeFileSync(path.join(out,'browser-global-views.json'),JSON.stringify(report,null,2)+'\n');
 const ownsPage=!page;const browser=ownsPage?await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9223']}):null;
 try{
  if(!ownsPage&&await page.evaluate(()=>innerWidth<700)){
   const before=await page.evaluate(()=>{const a=window.__SHANGHAI_APP__,m=a.scene.map;return {hash:location.hash,title:document.querySelector('#location-name').textContent,center:m.getCenter(),viewport:[innerWidth,innerHeight],positions:a.scene.getBuildingBeaconState().labelPositions};});
   const active=new URLSearchParams(before.hash.slice(1)).get('landmark'),target=before.positions.find(p=>p.id==='huangpu-grand-theatre'&&p.id!==active)||before.positions.find(p=>p.id!==active);assert.ok(target);assert.notEqual(target.id,active);
   const touch=await page.context().newCDPSession(page);await touch.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1});await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:target.x,y:target.y,id:1}]});await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await touch.detach();
   await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id&&document.querySelector('#location-name').textContent===window.__SHANGHAI_APP__.landmarks.find(r=>r.id===id).name,target.id,{timeout:30000});
   const after=await page.evaluate(()=>({hash:location.hash,title:document.querySelector('#location-name').textContent,center:window.__SHANGHAI_APP__.scene.map.getCenter(),mode:window.__SHANGHAI_APP__.mode}));assert.notEqual(before.hash,after.hash);assert.notEqual(before.title,after.title);assert.notDeepEqual(before.center,after.center);
   const file=path.join(out,'browser-beacons.json'),b=JSON.parse(fs.readFileSync(file));b.clicks.filter(c=>c.method==='actual-CDP-touchscreen-tap').forEach(c=>c.reselectedCurrentDestination=true);b.clicks.push({method:'actual-CDP-touchscreen-tap-to-different-destination',id:target.id,point:[target.x,target.y],viewport:before.viewport,before:{hash:before.hash,title:before.title,center:before.center},after});fs.writeFileSync(file,JSON.stringify(b,null,2)+'\n');console.log('PASS true changed-destination mobile tap',target.id,before.hash,after.hash);
  }
  if(!ownsPage)await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.map.setMaxBounds([[120.65,30.55],[122.3,32.0]]);});
  if(ownsPage)page=await browser.newPage({viewport:{width:960,height:720}});else await page.setViewportSize({width:960,height:720});page.on('pageerror',e=>{report.errors.push(e.message);console.error(e.message)});
  page.on('console',m=>{if(m.type()==='error'){report.errors.push(m.text());console.error(m.text())}});
  page.on('console',m=>{if(m.type()==='warning')report.warnings.push(m.text());});
  if(ownsPage)await page.goto(base+'index.html#landmark='+views[0][0]+'&mode=overview',{waitUntil:'domcontentloaded',timeout:90000});
  await page.waitForFunction(()=>window.__SHANGHAI_APP__,null,{timeout:240000});if(await page.locator('#panel-toggle').getAttribute('aria-expanded')!=='true')await page.locator('#panel-toggle').click();await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:true,surfaceNormals:true});});console.log('READY');
  for(const [id,label,zoom,offset] of views){
   const row=cat.models.find(r=>r.id===id);
   await page.evaluate(async({row,zoom,offset,cameraMode})=>{const a=window.__SHANGHAI_APP__;await a.selectPlace(a.landmarks.find(r=>r.id===row.id),{mode:'overview'});if(cameraMode!=='default'){a.scene.map.stop();a.scene.map.jumpTo({center:[row.lng,row.lat],zoom,pitch:20,bearing:row.heading});}a.scene.loadLandmarks();a.scene.refreshBuildingBeacons?.();},{row,zoom,offset,cameraMode});
   await page.waitForFunction(()=>!window.__SHANGHAI_APP__.scene.map.isMoving(),null,{timeout:60000});
   await page.waitForFunction(id=>window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id).visible,id,{timeout:180000});
   await page.waitForFunction(id=>{const a=window.__SHANGHAI_APP__,s=a.scene.getBuildingBeaconState();const p=s?.labelPositions.find(p=>p.id===id);return p&&a.scene.pickBuildingBeacon({x:p.x,y:p.y})===id;},id,{timeout:120000,polling:500});
   await page.waitForFunction(()=>window.__SHANGHAI_APP__.scene.getCandidateIntegrationState().vector.every(v=>!v.active||(!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer?.ready))),null,{timeout:180000,polling:500});
   await page.evaluate(async()=>{const map=window.__SHANGHAI_APP__.scene.map;for(let i=0;i<2;i++)await new Promise(resolve=>{map.once('render',resolve);map.triggerRepaint();});});
   const state=await page.evaluate(id=>{const a=window.__SHANGHAI_APP__;return {viewport:[innerWidth,innerHeight],canvas:[a.scene.map.getCanvas().getBoundingClientRect().width,a.scene.map.getCanvas().getBoundingClientRect().height],hash:location.hash,asset:a.scene.getLandmarkAssetState(id),candidate:a.scene.getCandidateIntegrationState(),beacons:a.scene.getBuildingBeaconState?.(),renderer:a.scene.getStreamingState().renderer,center:a.scene.map.getCenter(),zoom:a.scene.map.getZoom(),pitch:a.scene.map.getPitch(),bearing:a.scene.map.getBearing(),elevation:a.scene.map.transform.elevation,centerClampedToGround:a.scene.map.getCenterClampedToGround?.()}},id);
   assert.deepEqual(state.viewport,[960,720]);assert.deepEqual(state.canvas,[960,720]);
   const file='browser-final-global-'+label+'-'+report.runtime['app.js'].slice(0,8)+'.png';console.log('SCREENSHOT',id,state.asset.variant);report.pendingView={id,state};save();
   await page.screenshot({path:path.join(out,file),timeout:120000});
   const png=fs.readFileSync(path.join(out,file));assert.deepEqual([png.readUInt32BE(16),png.readUInt32BE(20)],state.viewport);
   report.views.push({id,selectedBeaconScreenPick:true,file,sha256:sha(path.join(out,file)),bytes:fs.statSync(path.join(out,file)).size,state});delete report.pendingView;save();console.log('SAVED',file);
  }
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:false,surfaceNormals:true});});
  const oldId='huangpu-sun-yatsen-residence';
  await page.evaluate(async id=>{const a=window.__SHANGHAI_APP__;await a.selectPlace(a.landmarks.find(r=>r.id===id),{mode:'walk'});},oldId);
  await page.waitForFunction(id=>window.__SHANGHAI_APP__.mode==='walk'&&window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id).visible,oldId,{timeout:180000});
  report.existingEntry=await page.evaluate(id=>{const a=window.__SHANGHAI_APP__;return {id,hash:location.hash,mode:a.mode,asset:a.scene.getLandmarkAssetState(id),padding:a.scene.map.getPadding(),position:{...a.controller.position},walkDisabled:document.querySelector('#walk-mode').disabled};},oldId);
  assert.equal(report.existingEntry.mode,'walk');assert.equal(report.existingEntry.walkDisabled,false);assert.ok(Object.values(report.existingEntry.padding).every(v=>v===0));
  await page.evaluate(async id=>{const a=window.__SHANGHAI_APP__;await a.selectPlace(a.landmarks.find(r=>r.id===id),{mode:'walk'});a.syncMode('walk');},views[0][0]);
  report.candidateGuard=await page.evaluate(()=>({hash:location.hash,mode:window.__SHANGHAI_APP__.mode,walkDisabled:document.querySelector('#walk-mode').disabled,startDisabled:document.querySelector('#start-walk').disabled}));
  assert.equal(report.candidateGuard.mode,'overview');assert.ok(report.candidateGuard.walkDisabled&&report.candidateGuard.startDisabled);
  assert.deepEqual(report.errors,[]);report.completed=true;save();
  if(process.env.QA_CONTINUE_MODELS==='1'){console.log('CONTINUE remaining models in the same page');await require('./qa-models-continuation.cjs')(page);}
 }catch(e){report.failure=e.stack;save();if(process.env.QA_KEEP_OPEN_ON_FAILURE==='1'){console.error('FAILED: preserve CDP 9223',e);await new Promise(()=>{});}throw e;}finally{if(ownsPage)await browser.close()}
}
module.exports=run;
if(require.main===module)run().catch(e=>{console.error(e);process.exit(1)});
