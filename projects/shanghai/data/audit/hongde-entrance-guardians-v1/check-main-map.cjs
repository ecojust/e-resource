/* Real ordinary landmark entry and two verified GLBs in the released city's renderer. */
const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');
const assert=require('node:assert/strict');const {createHash}=require('node:crypto');
const base=process.env.MODEL_BASE_URL;const out=process.env.QA_OUTPUT_DIR;
assert.ok(base&&out);const hash=b=>createHash('sha256').update(b).digest('hex');
const id='hongkou-hongde-church',macro='14-13720-6692';
const before=process.env.QA_BEFORE==='1';
async function run(){
 fs.mkdirSync(out,{recursive:true});
 const get=async route=>{let r=await fetch(new URL(route,base));assert.equal(r.status,200);return Buffer.from(await r.arrayBuffer());};
 const snapshot=JSON.parse(fs.readFileSync(process.env.QA_SNAPSHOT));const slug='source/precise/hongkou-hongde-church/revisions/entrance-guardians/manifest.json';
 const old=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../../source/precise/hongkou-hongde-church/revisions/entrance-guardians/baseline.json')));
 const manifest=before?{assets:{full:{...old.assets.web,triangles:old.prior_triangles.web},lod:{...old.assets.lod,triangles:old.prior_triangles.lod}}}:JSON.parse(await get(slug));
 const macroFile='data/precise-buildings/macros/'+macro+'/index.json';
 const rootFile='data/precise-buildings-v6.json',catalogFile='data/precise-buildings/catalog.json';
 const registry=JSON.parse(await get(rootFile));const catalogBytes=await get(catalogFile);assert.equal(hash(catalogBytes),registry.ordinary_catalog.sha256);
 const indexPointer=JSON.parse(catalogBytes).macros.find(r=>r.id===macro);const indexBytes=await get(macroFile);assert.equal(hash(indexBytes),indexPointer.sha256);
 const row=JSON.parse(indexBytes).models.find(x=>x.id===id);assert.equal(row.web_sha256,manifest.assets.full.sha256);assert.equal(row.lod_sha256,manifest.assets.lod.sha256);
 assert.equal(row.owner.feature_local_id,2557);assert.equal(row.bearing,185.5747301862071);
 const fallback={[macroFile]:hash(indexBytes),[manifest.assets.full.file]:manifest.assets.full.sha256,[manifest.assets.lod.file]:manifest.assets.lod.sha256};
 const b=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const log={id,base,started:new Date().toISOString(),browser:b.version(),driver_sha256:hash(fs.readFileSync(__filename)),snapshot_sha256:hash(fs.readFileSync(process.env.QA_SNAPSHOT)),assets:[],views:[],unexpected:[],completed:false};
 const file=path.join(out,'ordinary-map.json');const save=()=>fs.writeFileSync(file,JSON.stringify(log,null,2)+'\n');
 try{
  const page=await b.newPage({viewport:{width:810,height:610},ignoreHTTPSErrors:true});
  page.on('pageerror',e=>log.unexpected.push(e.message));const received=new Map();
  page.on('response',r=>{const u=new URL(r.url());if(u.origin===new URL(base).origin&&r.status()===200)received.set(u.pathname.slice(1)+u.search,r);});
  await page.goto(new URL('index.html#landmark='+id+'&mode=walk',base).href,{waitUntil:'domcontentloaded'});
  async function record(name,variant,role){
   await page.waitForFunction(({id,macro,variant,sha})=>{const a=window.__SHANGHAI_APP__;const s=a?.scene;if(!s)return false;
    const r=s.getLandmarkAssetState(id);const cat=s.getOrdinaryCatalogState();return cat?.activeMacros.includes(macro)&&r?.visible&&r.variant===variant&&r.verifiedAsset?.sha256===sha;},{id,macro,variant,sha:manifest.assets[role].sha256},{polling:650,timeout:360000});
   const state=await page.evaluate(id=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,r=s.getLandmarkAssetState(id);return{
     route:location.hash,mode:a.mode,asset:r.verifiedAsset,triangles:r.triangles,anchor:r.anchor,candidate:r.cityIntegration,beacons:s.getBuildingBeaconState().count,ordinary:s.getOrdinaryCatalogState(),camera:{center:m.getCenter().toArray(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom()},gl:m.painter.context.gl.getError(),lost:m.painter.context.gl.isContextLost(),navigation:document.querySelector('#location-name').textContent
   };},id);
   assert.equal(state.candidate,false);assert.equal(state.beacons,snapshot.resulting_count);assert.equal(state.triangles,manifest.assets[role].triangles);assert.equal(state.gl,0);assert.equal(state.lost,false);
   const f=name+'.png';const img=await page.screenshot({path:path.join(out,f),timeout:90000});
   log.views.push({name,file:f,bytes:img.length,sha256:hash(img),state});save();console.log('[ordinary]',name);
  }
  await record('north-entrance-walk','full','full');
  const overview=page.locator('#overview-mode');await overview.click({force:true});
  await page.waitForFunction(()=>window.__SHANGHAI_APP__?.mode==='overview',null,{timeout:120000});
  // Both entrances are sampled in the actual city with the ordinary object and its neighbours active.
  const northFront=[121.47799462,31.26395658];
  for(const c of [{name:'both-guardians-street',center:northFront,bearing:183,pitch:68,zoom:21.95,elevation:1.19},
                  {name:'east-guardian-street',center:[121.4780154,31.2639600],bearing:195,pitch:67,zoom:22.45,elevation:1.24},
                  {name:'west-guardian-street',center:[121.4779749,31.2639661],bearing:177,pitch:67,zoom:22.45,elevation:1.24}]){
   await page.evaluate(c=>{const m=window.__SHANGHAI_APP__.scene;m.map.stop();m.map.setCenterClampedToGround(false);m.map.jumpTo(c);m.loadLandmarks();m.refreshBuildingBeacons();},c);
   await record(c.name,'full','full');
  }
  await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene;s.map.jumpTo({center:[121.47798,31.26396],zoom:15.95,pitch:35,bearing:185,elevation:0});s.loadLandmarks();});
  // Zoom can unload the ordinary catalog while the curated entry remains installed.
  await page.waitForFunction(id=>{const r=window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id);return r?.visible&&r.variant==='distant';},id,{timeout:260000,polling:550});
  // In this overview the macro is optional, so bind the actual earlier registration and current remote mesh.
  const distant=await page.evaluate(id=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,r=s.getLandmarkAssetState(id);return{route:location.hash,mode:a.mode,asset:r.verifiedAsset,triangles:r.triangles,visible:r.visible,variant:r.variant,ordinary:s.getOrdinaryCatalogState(),beacons:s.getBuildingBeaconState().count,camera:{center:m.getCenter().toArray(),zoom:m.getZoom()},gl:m.painter.context.gl.getError()};},id);
  assert.equal(distant.asset.sha256,manifest.assets.lod.sha256);assert.equal(distant.triangles,manifest.assets.lod.triangles);assert.equal(distant.gl,0);
  const im=await page.screenshot({path:path.join(out,'city-lod.png'),timeout:90000});log.views.push({name:'city-lod',file:'city-lod.png',bytes:im.length,sha256:hash(im),state:distant});save();
  for(const [f,r]of received){
   const uri=f.split('?')[0];const tok=f.slice(uri.length);
   if(uri===manifest.assets.full.file||uri===manifest.assets.lod.file||uri==='data/landmarks.json'||uri==='data/precise-buildings-v6.json'||uri==='data/precise-buildings/catalog.json'||uri==='data/precise-buildings/macros/14-13720-6692/index.json'){
    const raw=await r.body();const signed=snapshot.files[uri]||fallback[uri];assert.ok(signed,uri);assert.equal(hash(raw),signed,uri);
    if(uri.endsWith('/catalog.json')||uri.endsWith('/index.json'))assert.equal(new URLSearchParams(tok).get('sha256'),hash(raw));
    if(uri==='data/landmarks.json'||uri==='data/precise-buildings-v6.json')assert.ok(new URLSearchParams(tok).get('v'));
    log.assets.push({resource:f,bytes:raw.length,sha256:hash(raw)});
   }
  }
  assert.equal(new Set(log.assets.map(x=>x.resource.split('?')[0])).size,6);assert.deepEqual(log.unexpected,[]);log.completed=true;
 }catch(e){log.failure=String(e);throw e;}finally{await b.close();log.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
