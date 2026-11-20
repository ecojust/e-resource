/* Persist the registered distant model before requesting its single real-map image. */
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const assert=require('node:assert/strict');
const {chromium}=require('playwright');

const out=process.env.QA_OUTPUT_DIR,base=process.env.MODEL_BASE_URL;
const production=process.env.QA_PRODUCTION;
const id='huangpu-glen-line-building';
const digest=b=>createHash('sha256').update(b).digest('hex');
const frozen=JSON.parse(fs.readFileSync(production));
const r={id,base,started:new Date().toISOString(),completed:false,stateCaptured:false,screenCaptured:false,
 checkerSha256:digest(fs.readFileSync(__filename)),productionSha256:digest(fs.readFileSync(production)),downloads:[],screenshots:[],errors:[]};
fs.mkdirSync(out,{recursive:true});
const report=path.join(out,'distant-browser.json');
assert.ok(!fs.existsSync(report),'Use an empty destination');
function save(){
 const temp=report+'.tmp';
 fs.writeFileSync(temp,JSON.stringify(r,null,2)+'\n');
 fs.renameSync(temp,report);
}
save();
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--num-raster-threads=1','--renderer-process-limit=2']});
 try{
  r.chromium=browser.version();
  const page=await browser.newPage({viewport:{width:600,height:460},deviceScaleFactor:1,ignoreHTTPSErrors:true});
  page.setDefaultTimeout(150000);
  const received=new Set(),origin=new URL(base).origin;
  page.on('response',resp=>{const u=new URL(resp.url());if(u.origin===origin&&resp.status()===200)received.add(decodeURIComponent(u.pathname.slice(1)));});
  page.on('pageerror',e=>{r.errors.push(e.message);save();});
  page.on('crash',()=>{r.pageCrashed=true;save();});
  const fetch=async file=>{const response=await page.request.get(base+file);assert.equal(response.status(),200);return response.body();};
  const catFile='data/candidate-city-integrations.json',cat=await fetch(catFile);
  r.catalogSha256=digest(cat);assert.equal(r.catalogSha256,frozen.files[catFile]);const catalog=JSON.parse(cat);
  r.catalogRows=catalog.resulting_city_count;assert.equal(r.catalogRows,129);const row=catalog.models.find(v=>v.id===id);
  const mf=await fetch(row.candidate_manifest);r.manifestSha256=digest(mf);assert.equal(r.manifestSha256,frozen.files[row.candidate_manifest]);
  const manifest=JSON.parse(mf),prefix=path.posix.dirname(row.candidate_manifest)+'/';
  const route='index.html#landmark='+id+'&mode=overview';
  await page.goto(base+route,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(({id,name})=>document.querySelector('#location-name')?.textContent===name
    &&window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id)?.status==='loaded',{id,name:row.name},
    {polling:450,timeout:185000});
  const camera={center:[121.48560983269681,31.242834860484248],elevation:0,pitch:32,bearing:-101,zoom:15.5,padding:{top:0,right:0,bottom:0,left:0}};
  r.requestedCamera=camera;r.beforeJump=true;save();
  await page.evaluate(c=>{
   const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();
  },camera);
  const captured=await page.waitForFunction(id=>{
   const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState(id);
   if(m.isMoving()||!a?.visible||a.status!=='loaded'||a.variant!=='distant'||!a.verifiedAsset?.sha256)return false;
   const gl=m.painter.context.gl;
   return {route:location.hash,visible:a.visible,status:a.status,variant:a.variant,verifiedAsset:a.verifiedAsset,
    triangles:a.triangles,anchor:a.anchor,heading:a.heading,contextLost:gl.isContextLost(),viewport:[innerWidth,innerHeight],
    camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),bearing:m.getBearing(),pitch:m.getPitch(),elevation:m.getCenterElevation()}};
  },id,{polling:350,timeout:190000});
  r.state=await captured.jsonValue();r.stateTime=new Date().toISOString();
  assert.equal(r.state.contextLost,false);assert.equal(r.state.verifiedAsset.sha256,manifest.assets.lod.sha256);
  assert.equal(r.state.triangles,manifest.assets.lod.triangles);assert.deepEqual(r.state.anchor,[row.lng,row.lat]);
  assert.ok(received.has(prefix+manifest.assets.lod.file),'The running map itself requested this LOD');
  r.stateCaptured=true;save();console.log('distant visible and saved',r.state.triangles,r.state.verifiedAsset.sha256);
  await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>resolve());m.triggerRepaint();}));
  const img=await page.screenshot({path:path.join(out,'map-distant.png'),timeout:150000});r.screenshots.push({file:'map-distant.png',sha256:digest(img),bytes:img.length});
  r.screenCaptured=true;save();
  for(const [role,v]of Object.entries(manifest.assets)){
   const f=prefix+v.file,data=await fetch(f);assert.equal(data.length,v.bytes);assert.equal(digest(data),v.sha256);
   r.downloads.push({role,file:f,bytes:data.length,sha256:v.sha256,receivedByMapBeforeFileCheck:received.has(f)});save();
  }
  assert.deepEqual(r.errors,[]);r.completed=true;
 }catch(e){r.failure=e.stack;save();throw e;}
 finally{await browser.close();r.finished=new Date().toISOString();save();}
})().catch(e=>{console.error(e);process.exitCode=1;});
