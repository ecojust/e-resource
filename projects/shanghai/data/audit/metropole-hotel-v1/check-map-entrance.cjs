/* Take an additional map view from the open intersection, in the delivered city. */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');
const hash=b=>createHash('sha256').update(b).digest('hex');
const id='huangpu-metropole-hotel';
const base=process.env.MODEL_BASE_URL;
const out=process.env.QA_OUTPUT_DIR;
assert.ok(base&&out);
const contract=JSON.parse(fs.readFileSync(path.join(__dirname,'final-placement-contract.json')));
const heading=contract.heading*Math.PI/180,earth=6371008.8*Math.cos(contract.lat*Math.PI/180);
function local(x,y){
 const east=x*Math.cos(heading)+y*Math.sin(heading);
 const north=-x*Math.sin(heading)+y*Math.cos(heading);
 return [contract.lng+east/earth*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(contract.lat*Math.PI/180))+north/earth))*180/Math.PI];
}
async function run(){
 fs.mkdirSync(out,{recursive:true});
 const catalog=await fetch(new URL('data/candidate-city-integrations.json',base));
 assert.equal(catalog.status,200);const body=Buffer.from(await catalog.arrayBuffer());const city=JSON.parse(body);
 assert.equal(city.resulting_city_count,112);const model=city.models.find(m=>m.id===id);
 const html=await fetch(new URL('index.html',base));assert.equal(html.status,200);
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const report={id,base,started:new Date().toISOString(),catalog_sha256:hash(body),index_sha256:hash(Buffer.from(await html.arrayBuffer())),driver_sha256:hash(fs.readFileSync(__filename)),browser:browser.version(),views:[],errors:[],completed:false};
 try{
  const page=await browser.newPage({viewport:{width:940,height:670},deviceScaleFactor:1});
  page.on('pageerror',error=>report.errors.push(error.message));
  await page.goto(new URL('index.html#landmark='+id+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(id=>Boolean(window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id)?.visible),id,{timeout:150000,polling:650});
  await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene,a=s.getLandmarkAssetState(id),c=s.getCandidateIntegrationState();return !s.map.isMoving()&&a?.visible&&a.variant==='full'&&c.sourceSections.some(q=>q.id===id&&q.segments===2);},id,{timeout:240000,polling:550});
  const baseline=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState(id);return{route:location.hash,center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),asset:a.verifiedAsset,visible:a.visible,triangles:a.triangles,sourceSections:s.getCandidateIntegrationState().sourceSections.filter(r=>r.id===id),labels:s.getBuildingBeaconState().count};},id);
  assert.equal(baseline.asset.sha256,model.assets.web.sha256);assert.equal(baseline.labels,112);
  const defaultFile='final-default.png';const defaultImage=await page.screenshot({path:path.join(out,defaultFile),timeout:300000});
  report.views.push({file:defaultFile,bytes:defaultImage.length,sha256:hash(defaultImage),state:baseline});
  const nav=page.locator('#panel-toggle');if(await nav.getAttribute('aria-expanded')==='true')await nav.click();
  for(const [name,zoom,elevation,pitch,bearing] of [['junction-entrance',21.27,5.8,66,contract.heading+2],['junction-portico',21.70,3.85,62,contract.heading-11]]){
   const camera={center:local(0,.40),zoom,elevation,pitch,bearing,padding:{top:55,left:0,right:0,bottom:80}};
   await page.evaluate(cam=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(cam);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
   await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene;const a=s.getLandmarkAssetState(id),c=s.getCandidateIntegrationState(),t=s.getStreamingState();return !s.map.isMoving()&&a?.visible&&a.variant==='full'&&c.sourceSections.some(q=>q.id===id&&q.segments===2)&&t.detail.active.some(q=>q.id==='14-13720-6694/14-13720-6694-2_-3-s1-s0-s1');},id,{timeout:240000,polling:550});
   const state=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;const a=s.getLandmarkAssetState(id);return{route:location.hash,center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),visible:a.visible,variant:a.variant,triangles:a.triangles,asset:a.verifiedAsset,sourceSections:s.getCandidateIntegrationState().sourceSections.filter(q=>q.id===id),beacons:s.getBuildingBeaconState().count,fullRenderer:s.getStreamingState().renderer};},id);
   assert.equal(state.asset.sha256,model.assets.web.sha256);assert.equal(state.triangles,model.assets.web.triangles);
   const file=name+'.png';const image=await page.screenshot({path:path.join(out,file),timeout:300000});
   report.views.push({file,bytes:image.length,sha256:hash(image),requested:camera,state});
  }
  assert.deepEqual(report.errors,[]);report.completed=true;
 }finally{
   await browser.close();report.finished=new Date().toISOString();
   fs.writeFileSync(path.join(out,'junction-entrance.json'),JSON.stringify(report,null,2)+'\n');
 }
}
run().catch(e=>{console.error(e);process.exitCode=1});
