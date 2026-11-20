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
 const old=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../../../source/precise/hongkou-hongde-church/revisions/entrance-guardians/baseline.json')));
 const manifest=before?{assets:{full:{...old.assets.web,triangles:old.prior_triangles.web},lod:{...old.assets.lod,triangles:old.prior_triangles.lod}}}:JSON.parse(await get(slug));
 const macroFile='data/precise-buildings/macros/'+macro+'/index.json';
 const rootFile='data/precise-buildings-v6.json',catalogFile='data/precise-buildings/catalog.json';
 const registry=JSON.parse(await get(rootFile));const catalogBytes=await get(catalogFile);assert.equal(hash(catalogBytes),registry.ordinary_catalog.sha256);
 const indexPointer=JSON.parse(catalogBytes).macros.find(r=>r.id===macro);const indexBytes=await get(macroFile);assert.equal(hash(indexBytes),indexPointer.sha256);
 const row=JSON.parse(indexBytes).models.find(x=>x.id===id);assert.equal(row.web_sha256,manifest.assets.full.sha256);assert.equal(row.lod_sha256,manifest.assets.lod.sha256);
 assert.equal(row.owner.feature_local_id,2557);assert.equal(row.bearing,185.5747301862071);
 const fallback={[macroFile]:hash(indexBytes),[manifest.assets.full.file]:manifest.assets.full.sha256,[manifest.assets.lod.file]:manifest.assets.lod.sha256};
 const b=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--disk-cache-size=8388608','--num-raster-threads=1','--renderer-process-limit=2']});
 const log={id,base,started:new Date().toISOString(),browser:b.version(),driver_sha256:hash(fs.readFileSync(__filename)),snapshot_sha256:hash(fs.readFileSync(process.env.QA_SNAPSHOT)),assets:[],views:[],unexpected:[],localHttpErrors:[],completed:false};
 const file=path.join(out,'ordinary-map.json');const save=()=>fs.writeFileSync(file,JSON.stringify(log,null,2)+'\n');
 try{
  const page=await b.newPage({viewport:before?{width:1100,height:744}:{width:390,height:844},hasTouch:true,deviceScaleFactor:1,ignoreHTTPSErrors:true});page.setDefaultTimeout(90000);
  page.on('pageerror',e=>{log.unexpected.push(e.message);save();});
  page.on('crash',()=>{log.crashed=true;save();});
  page.on('requestfailed',r=>{(log.requestFailures??=[]).push({url:r.url(),reason:r.failure()?.errorText});});
  const diagnostic=async name=>{
    try{log.lastState=await page.evaluate(id=>{const a=window.__SHANGHAI_APP__,s=a?.scene,m=s?.map,r=s?.getLandmarkAssetState(id);return {route:location.href,mode:a?.mode,id,
     ready:!!s,asset:r?{visible:r.visible,variant:r.variant,sha256:r.verifiedAsset?.sha256,triangles:r.triangles}:null,
     containsTargetGroup:s?.getOrdinaryCatalogState()?.activeMacros?.includes('14-13720-6692'),camera:m?{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch()}:null,
     curtain:document.querySelector('#loading')?getComputedStyle(document.querySelector('#loading')).opacity:null};},id);
     log.phase=name;save();}catch(e){log.diagnosticError=String(e);save();}
  };
  let phase='opening real directory';const observation=setInterval(()=>{void diagnostic(phase);},18000);observation.unref();
  const received=new Map();
  page.on('response',r=>{const u=new URL(r.url());if(u.origin!==new URL(base).origin)return;if(r.status()>=400){log.localHttpErrors.push({url:r.url(),status:r.status()});save();}else if(r.status()===200)received.set(u.pathname.slice(1)+u.search,r);});
  await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
  const entry=page.locator('article[data-landmark="'+id+'"] .card-foot a');
  assert.equal(await page.locator('.landmark-card[data-landmark]').count(),176);
  assert.equal(await entry.getAttribute('href'),'index.html#landmark='+id+'&mode=walk');
  if(before)await entry.click();else await entry.tap();
  await page.waitForFunction(()=>{const e=document.querySelector('#loading');if(!e)return true;const st=getComputedStyle(e);return st.display==='none'||st.visibility==='hidden'||Number(st.opacity)<.015;},null,{timeout:300000});
  log.directoryEntry={count:176,input:before?'click':'tap',mode:'walk',id};
  async function nextFrame(){
   await page.evaluate(()=>new Promise(resolve=>{
    const a=window.__SHANGHAI_APP__.scene.map;let n=0;
    function rendered(){if(++n===3){requestAnimationFrame(resolve);return;}a.once('render',rendered);a.triggerRepaint();}
    a.once('render',rendered);a.triggerRepaint();
   }));
  }
  async function hidePanel(){
   const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
  }
  async function record(name,variant,role){
   phase=name;await diagnostic(name);await page.waitForFunction(({id,macro,variant,sha})=>{const a=window.__SHANGHAI_APP__;const s=a?.scene;if(!s)return false;
    const r=s.getLandmarkAssetState(id);const cat=s.getOrdinaryCatalogState();return cat?.activeMacros.includes(macro)&&r?.visible&&r.variant===variant&&r.verifiedAsset?.sha256===sha;},{id,macro,variant,sha:manifest.assets[role].sha256},{polling:650,timeout:360000});
   await nextFrame();const state=await page.evaluate(id=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,r=s.getLandmarkAssetState(id);return{
     route:location.hash,mode:a.mode,asset:r.verifiedAsset,triangles:r.triangles,anchor:r.anchor,candidate:r.cityIntegration,beacons:s.getBuildingBeaconState().count,ordinary:s.getOrdinaryCatalogState(),renderer:s.getStreamingState().renderer,viewport:{width:innerWidth,height:innerHeight},camera:{center:m.getCenter().toArray(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),elevation:m.getCenterElevation(),padding:m.getPadding()},selected:new URLSearchParams(location.hash.slice(1)).get('landmark'),gl:m.painter.context.gl.getError(),lost:m.painter.context.gl.isContextLost(),navigation:document.querySelector('#location-name').textContent
   };},id);
   if(state.mode==='walk'){assert.equal(state.selected,id);assert.equal(state.navigation,'鸿德堂 · 多伦路59号');}
   assert.equal(state.candidate,false);assert.equal(state.beacons,snapshot.resulting_count);assert.equal(state.triangles,manifest.assets[role].triangles);assert.equal(state.gl,0);assert.equal(state.lost,false);
   const f=name+'.png';const img=await page.screenshot({path:path.join(out,f),timeout:90000});
   log.views.push({name,file:f,bytes:img.length,sha256:hash(img),state});save();console.log('[ordinary]',name);
  }
  if(!before){
   await record('north-entrance-phone','full','full');
   await page.setViewportSize({width:1100,height:744});
   await page.evaluate(()=>window.__SHANGHAI_APP__.scene.map.resize());
  }
  await record('north-entrance-walk','full','full');
  const overview=page.locator('#overview-mode');await overview.click({force:true});
  await page.waitForFunction(()=>window.__SHANGHAI_APP__?.mode==='overview',null,{timeout:120000});
  await hidePanel();await page.evaluate(()=>{const m=window.__SHANGHAI_APP__.scene.map;m.stop();m.setPadding({left:0,right:0,top:0,bottom:0});});
  // The pair at one entrance is sampled in the actual city with the ordinary object and its neighbours active.
  const northFront=[121.47799511,31.26396103];
  const cameras=[
   {name:'both-guardians-street',center:northFront,bearing:185.57,pitch:73,zoom:22.37,elevation:1.23},
   {name:'east-guardian-street',center:[121.47801556,31.26395922],bearing:192,pitch:72,zoom:23.62,elevation:1.28},
   {name:'west-guardian-street',center:[121.47797477,31.26396266],bearing:178,pitch:72,zoom:23.62,elevation:1.28}];
  for(const c of cameras){
   if(before&&c.name==='west-guardian-street')continue;
   await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;const m=s.map;m.stop();m.setCenterClampedToGround(false);m.jumpTo({...c,padding:{left:0,right:0,top:0,bottom:0}});s.loadLandmarks();s.refreshBuildingBeacons();},c);
   await record(c.name,'full','full');
  }
  await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene;s.map.jumpTo({center:[121.47798,31.26396],zoom:15.95,pitch:35,bearing:185,elevation:0});s.loadLandmarks();});
  // Zoom can unload the ordinary catalog while the curated entry remains installed.
  await page.waitForFunction(id=>{const r=window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id);return r?.visible&&r.variant==='distant';},id,{timeout:260000,polling:550});
  // In this overview the macro is optional, so bind the actual earlier registration and current remote mesh.
  const distant=await page.evaluate(id=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,r=s.getLandmarkAssetState(id);return{route:location.hash,mode:a.mode,asset:r.verifiedAsset,triangles:r.triangles,visible:r.visible,variant:r.variant,ordinary:s.getOrdinaryCatalogState(),beacons:s.getBuildingBeaconState().count,camera:{center:m.getCenter().toArray(),zoom:m.getZoom()},gl:m.painter.context.gl.getError()};},id);
  assert.equal(distant.asset.sha256,manifest.assets.lod.sha256);assert.equal(distant.triangles,manifest.assets.lod.triangles);assert.equal(distant.gl,0);
  await nextFrame();const im=await page.screenshot({path:path.join(out,'city-lod.png'),timeout:90000});log.views.push({name:'city-lod',file:'city-lod.png',bytes:im.length,sha256:hash(im),state:distant});save();
  for(const [f,r]of received){
   const uri=f.split('?')[0];const tok=f.slice(uri.length);
   if(uri===manifest.assets.full.file||uri===manifest.assets.lod.file||uri==='data/landmarks.json'||uri==='data/precise-buildings-v6.json'||uri==='data/precise-buildings/catalog.json'||uri==='data/precise-buildings/macros/14-13720-6692/index.json'){
    const raw=await r.body();const signed=snapshot.files[uri]||fallback[uri];assert.ok(signed,uri);assert.equal(hash(raw),signed,uri);
    if(uri.endsWith('/catalog.json')||uri.endsWith('/index.json'))assert.equal(new URLSearchParams(tok).get('sha256'),hash(raw));
    if(uri==='data/landmarks.json'||uri==='data/precise-buildings-v6.json')assert.ok(new URLSearchParams(tok).get('v'));
    log.assets.push({resource:f,bytes:raw.length,sha256:hash(raw)});
   }
  }
  assert.equal(new Set(log.assets.map(x=>x.resource.split('?')[0])).size,6);assert.deepEqual(log.unexpected,[]);assert.deepEqual(log.localHttpErrors,[]);log.completed=true;clearInterval(observation);
 }catch(e){log.failure=String(e);throw e;}finally{await b.close();log.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
