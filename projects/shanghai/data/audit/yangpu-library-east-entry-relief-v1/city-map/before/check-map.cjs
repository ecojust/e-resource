/* Real ordinary landmark entry and two verified GLBs in the released city's renderer. */
const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');
const assert=require('node:assert/strict');const {createHash}=require('node:crypto');
const base=process.env.MODEL_BASE_URL;const out=process.env.QA_OUTPUT_DIR;
assert.ok(base&&out);const hash=b=>createHash('sha256').update(b).digest('hex');
const id='yangpu-library',macro='14-13722-6690';
async function run(){
 fs.mkdirSync(out,{recursive:true});
 const get=async route=>{let r=await fetch(new URL(route,base));assert.equal(r.status,200);return Buffer.from(await r.arrayBuffer());};
 const snapshot=JSON.parse(fs.readFileSync(process.env.QA_SNAPSHOT));const slug='source/precise/yangpu-library/revisions/east-entry-relief/manifest.json';
 const control=process.argv.includes('--control');
 const manifest=control?{assets:snapshot.model_assets}:JSON.parse((await get(slug)).toString());
 const b=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const log={id,base,started:new Date().toISOString(),browser:b.version(),driver_sha256:hash(fs.readFileSync(__filename)),snapshot_sha256:hash(fs.readFileSync(process.env.QA_SNAPSHOT)),assets:[],views:[],unexpected:[],completed:false};
 log.control=control;
 const file=path.join(out,'ordinary-map.json');const save=()=>fs.writeFileSync(file,JSON.stringify(log,null,2)+'\n');
 try{
  const page=await b.newPage({viewport:{width:810,height:610},ignoreHTTPSErrors:true});
  page.on('pageerror',e=>log.unexpected.push(e.message));const received=new Map();
  page.on('response',r=>{const u=new URL(r.url());if(u.origin!==new URL(base).origin||r.status()!==200)return;const f=u.pathname.slice(1);
   if([manifest.assets.full.file,manifest.assets.lod.file,'data/landmarks.json','data/precise-buildings-v6.json','data/precise-buildings/catalog.json','data/precise-buildings/macros/14-13722-6690/index.json'].includes(f))received.set(f+u.search,r.body().catch(e=>({error:String(e)}))); });
  await page.goto(new URL('index.html#landmark='+id+'&mode=walk',base).href,{waitUntil:'domcontentloaded'});
  async function record(name,variant,role){
   await page.waitForFunction(({id,macro,variant,sha})=>{const a=window.__SHANGHAI_APP__;const s=a?.scene;if(!s)return false;
    const r=s.getLandmarkAssetState(id);const cat=s.getOrdinaryCatalogState();return cat?.activeMacros.includes(macro)&&r?.visible&&r.variant===variant&&r.verifiedAsset?.sha256===sha;},{id,macro,variant,sha:manifest.assets[role].sha256},{polling:650,timeout:360000});
   const state=await page.evaluate(id=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,r=s.getLandmarkAssetState(id);return{
     route:location.hash,mode:a.mode,asset:r.verifiedAsset,triangles:r.triangles,anchor:r.anchor,candidate:r.cityIntegration,beacons:s.getBuildingBeaconState().count,ordinary:s.getOrdinaryCatalogState(),camera:{center:m.getCenter().toArray(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom()},gl:m.painter.context.gl.getError(),lost:m.painter.context.gl.isContextLost(),navigation:document.querySelector('#location-name').textContent
   };},id);
   assert.equal(state.candidate,false);assert.equal(state.beacons,122);assert.equal(state.triangles,manifest.assets[role].triangles);assert.equal(state.gl,0);assert.equal(state.lost,false);
   const f=name+'.png';const img=await page.screenshot({path:path.join(out,f),timeout:300000});
   log.views.push({name,file:f,bytes:img.length,sha256:hash(img),state});save();console.log('[ordinary]',name);
  }
  await record('east-entry-walk','full','full');
  const overview=page.locator('#overview-mode');await overview.click({force:true});
  await page.waitForFunction(()=>window.__SHANGHAI_APP__?.mode==='overview',null,{timeout:120000});
  await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene;s.map.jumpTo({center:[121.5187877,31.310841],zoom:15.95,pitch:35,bearing:270});s.loadLandmarks();});
  // Zoom can unload the ordinary catalog while the curated entry remains installed.
  await page.waitForFunction(id=>{const r=window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id);return r?.visible&&r.variant==='distant';},id,{timeout:260000,polling:550});
  // In this overview the macro is optional, so bind the actual earlier registration and current remote mesh.
  const distant=await page.evaluate(id=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,r=s.getLandmarkAssetState(id);return{route:location.hash,mode:a.mode,asset:r.verifiedAsset,triangles:r.triangles,visible:r.visible,variant:r.variant,ordinary:s.getOrdinaryCatalogState(),beacons:s.getBuildingBeaconState().count,camera:{center:m.getCenter().toArray(),zoom:m.getZoom()},gl:m.painter.context.gl.getError()};},id);
  assert.equal(distant.asset.sha256,manifest.assets.lod.sha256);assert.equal(distant.triangles,manifest.assets.lod.triangles);assert.equal(distant.gl,0);
  const im=await page.screenshot({path:path.join(out,'city-lod.png'),timeout:300000});log.views.push({name:'city-lod',file:'city-lod.png',bytes:im.length,sha256:hash(im),state:distant});save();
  for(const [f,r]of received){
   const uri=f.split('?')[0];const tok=f.slice(uri.length);
   if(uri===manifest.assets.full.file||uri===manifest.assets.lod.file||uri==='data/landmarks.json'||uri==='data/precise-buildings-v6.json'||uri==='data/precise-buildings/catalog.json'||uri==='data/precise-buildings/macros/14-13722-6690/index.json'){
    const raw=await r;assert.ok(Buffer.isBuffer(raw),uri+" "+raw?.error);assert.ok(snapshot.files[uri]);assert.equal(hash(raw),snapshot.files[uri],uri);
    if(!control&&(uri.endsWith('/catalog.json')||uri.endsWith('/index.json')))assert.equal(new URLSearchParams(tok).get('sha256'),hash(raw));
    if(!control&&(uri==='data/landmarks.json'||uri==='data/precise-buildings-v6.json'))assert.ok(new URLSearchParams(tok).get('v'));
    log.assets.push({resource:f,bytes:raw.length,sha256:hash(raw)});
   }
  }
  assert.equal(new Set(log.assets.map(x=>x.resource.split('?')[0])).size,6);assert.deepEqual(log.unexpected,[]);log.completed=true;
 }catch(e){log.failure=String(e);throw e;}finally{await b.close();log.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
