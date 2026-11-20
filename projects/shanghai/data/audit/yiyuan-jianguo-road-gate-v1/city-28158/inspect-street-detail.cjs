const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const hash=b=>createHash('sha256').update(b).digest('hex');
const w=__dirname,out=path.join(w,'street-detail');
const read=f=>JSON.parse(fs.readFileSync(f));
const prior=read(path.join(w,'after/after.json'));
assert.ok(prior.completed&&prior.browserClosed);
const scene=read('/dev/shm/yiyuan158-latest-inputs/158-production.json');
const target=prior.id,base=prior.site;
const previous=prior.views.find(v=>v.file==='map-desktop.png');
const hidden=prior.views.find(v=>v.file==='map-name-tablet-and-side-passage.png');
const signed=prior.modelInputs.full.sha256;
const stamp={site:base,target,sourceSceneSHA:prior.snapshotSha256,previousObstruction:hidden.sha256,scriptSHA:hash(fs.readFileSync(__filename)),views:[],errors:[],passed:false};
fs.mkdirSync(out,{recursive:true});
const record=()=>fs.writeFileSync(path.join(out,'review.json'),JSON.stringify(stamp,null,2)+'\n');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:960,height:700}});
  page.on('pageerror',e=>stamp.errors.push(e.message));
  const got=await page.request.get(base+'data/candidate-city-integrations.json');
  assert.equal(hash(await got.body()),scene.files['data/candidate-city-integrations.json']);
  await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
  await page.locator('.landmark-card[data-landmark="'+target+'"] .card-foot a[href="index.html#landmark='+target+'&mode=overview"]').click();
  const steady=()=>page.waitForFunction(id=>{const a=window.__SHANGHAI_APP__,s=a?.scene,m=s?.map,asset=s?.getLandmarkAssetState(id),loader=document.querySelector('#loading');return m&&!m.isMoving()&&asset?.visible&&asset.variant==='full'&&asset.status==='loaded'&&loader&&getComputedStyle(loader).visibility==='hidden';},target,{timeout:180000,polling:250});
  await steady();
  const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
  for(const cfg of [{label:'street-gate-detail',zoom:21.72,pitch:27},{label:'street-name-and-side-arch',zoom:22.12,pitch:32}]){
   const camera={center:previous.camera.center,zoom:cfg.zoom,pitch:cfg.pitch,bearing:previous.camera.bearing,elevation:previous.camera.elevation,padding:{left:0,right:0,top:0,bottom:0}};
   await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
   await steady();
   await page.evaluate(async()=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(14000);await new Promise(ok=>{s.map.once('render',ok);s.map.triggerRepaint();});});
   const obs=await page.evaluate(({id,points})=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,asset=s.getLandmarkAssetState(id),canvas=m.getCanvas(),gl=m.painter.context.gl;return {title:document.querySelector('#location-name').textContent,asset:asset.verifiedAsset,viewport:[innerWidth,innerHeight],renderer:[gl.getError(),gl.isContextLost()],camera:{zoom:m.getZoom(),center:m.getCenter().toArray(),elevation:m.getCenterElevation(),bearing:m.getBearing(),pitch:m.getPitch()},features:points.map(p=>{const z=()=>p.z;const xy=m.transform.locationToScreenPoint({lng:p.lngLat[0],lat:p.lngLat[1]},{getElevationForLngLat:z,getElevationForLngLatZoom:z});return {name:p.feature,x:xy.x,y:xy.y,canvas:document.elementFromPoint(xy.x,xy.y)===canvas};})};},{id:target,points:previous.projections});
   assert.equal(obs.asset.sha256,signed);assert.deepEqual(obs.renderer,[0,false]);assert.ok(obs.features.every(p=>p.canvas));
   const file=cfg.label+'.png',bytes=await page.screenshot({path:path.join(out,file),timeout:180000});stamp.views.push({file,sha256:hash(bytes),bytes:bytes.length,...obs});record();
  }
  assert.deepEqual(stamp.errors,[]);stamp.passed=true;
 }finally{await browser.close();stamp.closed=new Date().toISOString();record();}
})().catch(e=>{stamp.failure=e.stack;record();console.error(e);process.exitCode=1});
