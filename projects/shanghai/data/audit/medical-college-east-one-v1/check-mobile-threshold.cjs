// Capture the 390px overview before its first zoom button press. The shared near-tile streamer starts at 17.3.
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{createHash}=require('node:crypto');
const folder=process.env.QA_OUTPUT_DIR,id='xuhui-medical-college-east-building-one',owner=2076;
(async()=>{
 const b=await chromium.connectOverCDP('http://127.0.0.1:'+process.env.QA_CDP_PORT,{timeout:15000});
 const p=b.contexts()[0].pages().find(p=>p.url().includes('index.html#landmark='+id));assert.ok(p);
 const observed=await p.evaluate(id=>{
  const scene=window.__SHANGHAI_APP__.scene,map=scene.map,integrations=scene.getCandidateIntegrationState(),beacons=scene.getBuildingBeaconState();
  const asset=scene.getLandmarkAssetState(id),target=beacons.labelPositions.find(v=>v.id===id);
  return {url:location.href,viewport:[innerWidth,innerHeight],cityCount:beacons.count,asset,farMacroFetched:performance.getEntriesByType('resource').some(v=>new URL(v.name).pathname.endsWith('/macros/14-13719-6696/far.glb')),
    active:integrations.active.find(v=>v.id===id),nearSources:integrations.shader.ownerScopedSources.filter(v=>v.macro_id==='14-13719-6696'&&v.feature_local_ids.includes(2076)),
    nearTiles:scene.getStreamingState().detail.active.map(v=>v.id),sourceState:map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:'d2dc605e-5be1-4b23-89d9-bcd2c0aebdc1'}),
    camera:{center:map.getCenter(),zoom:map.getZoom(),pitch:map.getPitch(),bearing:map.getBearing(),elevation:map.getCenterElevation()},selectedLabel:target&&{x:target.x,y:target.y,pick:scene.pickBuildingBeacon({x:target.x,y:target.y})}};
 },id);
 assert.deepEqual(observed.viewport,[390,844]);assert.equal(observed.cityCount,166);assert.equal(observed.selectedLabel.pick,id);
 assert.ok(observed.camera.zoom<17.3 && observed.farMacroFetched && !observed.nearTiles.length && !observed.nearSources.length && observed.active);assert.equal(observed.asset.variant,'full');
 const cfg=JSON.parse(fs.readFileSync(path.join(__dirname,'../../../assets/models/candidates/'+id+'/manifest.json')));assert.equal(observed.asset.verifiedAsset.sha256,cfg.assets.full.sha256);
 const first=path.join(folder,'mobile-default-before-zoom.png');const screenshot=fs.existsSync(first)?fs.readFileSync(first):await p.screenshot({path:first,timeout:100000});observed.photo={file:'mobile-default-before-zoom.png',bytes:screenshot.length,sha256:createHash('sha256').update(screenshot).digest('hex')};
 observed.checkedAt=new Date().toISOString();observed.scriptSha256=createHash('sha256').update(fs.readFileSync(__filename)).digest('hex');const save=()=>fs.writeFileSync(path.join(folder,'mobile-threshold.json'),JSON.stringify(observed,null,2)+'\n');save();
 const button=p.locator('#zoom-in');const box=await button.boundingBox();assert.ok(box);const x=box.x+box.width/2,y=box.y+box.height/2;
 assert.equal(await p.evaluate(([x,y])=>document.elementFromPoint(x,y)?.closest('button')?.id,[x,y]),'zoom-in');
 const cdp=await p.context().newCDPSession(p);
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y,radiusX:2,radiusY:2,force:1,id:1}]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await cdp.detach();
 await p.waitForFunction(previous=>window.__SHANGHAI_APP__.scene.map.getZoom()>previous+.5,observed.camera.zoom,{timeout:35000});
 observed.action={control:'#zoom-in',input:'touch',button:box,zoomAfter:await p.evaluate(()=>window.__SHANGHAI_APP__.scene.map.getZoom())};save();
 console.log('Captured the real phone default, then tapped +.',observed.camera.zoom,observed.action.zoomAfter);process.exit(0);
})().catch(e=>{console.error(e);process.exit(1)});
