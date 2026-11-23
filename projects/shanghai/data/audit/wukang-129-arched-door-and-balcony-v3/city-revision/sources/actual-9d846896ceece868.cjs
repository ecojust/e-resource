/* Observe both city asset variants, the original owner group, and real UI inputs. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright-core');
const [base, out] = process.argv.slice(2);
const id='xuhui-wukang-129';
const macro='14-13718-6695';
const sha=b=>createHash('sha256').update(b).digest('hex');
fs.mkdirSync(out,{recursive:true});
assert(!fs.existsSync(path.join(out,'result.json')));
fs.copyFileSync(__filename,path.join(out,'actual-driver.cjs'));
const result={id,base,driver_sha256:sha(fs.readFileSync(__filename)),node:process.pid,started:new Date().toISOString(),images:{},inputs:[],responses:{},errors:[],warnings:[]};
function save() {fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');}
async function run() {
 const r=await fetch(new URL('data/landmarks.json',base));assert(r.ok);
 const bytes=Buffer.from(await r.arrayBuffer());const entries=JSON.parse(bytes);const row=entries.find(b=>b.id===id);
 result.static={count:entries.length,sha256:sha(bytes),row};assert.equal(entries.filter(b=>b.id===id).length,1);
 const browser=await chromium.launch({headless:false,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--disable-translate','--disable-features=Translate,TranslateUI','--ozone-platform=x11','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-program-cache','--disable-background-networking','--enable-low-end-device-mode','--renderer-process-limit=1','--force-gpu-mem-available-mb=64','--disable-gpu-rasterization','--disk-cache-size=1048576','--no-sandbox','--no-zygote','--single-process','--in-process-gpu','--disable-dev-shm-usage','--num-raster-threads=1','--disable-gpu-shader-disk-cache','--js-flags=--optimize-for-size --max-old-space-size=210 --max-semi-space-size=1']});
 let page;
 try{
  page=await browser.newPage({viewport:{width:430,height:350},deviceScaleFactor:1});
  page.setDefaultTimeout(48000);
  const cdp=await page.context().newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:16,downloadThroughput:1400000,uploadThroughput:1400000});
  await page.addInitScript(anchor=>{
   Object.defineProperty(navigator,'hardwareConcurrency',{value:1,configurable:true});
   let library;
   Object.defineProperty(window,'maplibregl',{configurable:true,get(){return library;},set(obj){
    library=obj;if(typeof obj?.setWorkerCount==='function')obj.setWorkerCount(1);
    if(typeof obj?.Map==='function'){
     const MapOriginal=obj.Map;
     obj.Map=class extends MapOriginal{constructor(options){super({...options,center:anchor,zoom:18.8,pitch:0,pixelRatio:.30,maxTileCacheSize:2,antialias:false,canvasContextAttributes:{...options.canvasContextAttributes,antialias:false}});}};
    }
   }});
  },row.anchor);
  const schedule={started:Date.now(),otherNext:0,requests:[]};
  await page.route(/\.(?:glb|gltf)(?:\.gz)?(?:\?|$)|\/READY\.json(?:\?|$)/i,async route=>{
   const u=new URL(route.request().url()),frame=Date.now(),own=u.pathname.includes('/'+id+'/'),local=u.pathname.includes('/'+macro+'/');
   let when=frame;
   if(!own&&!local){when=Math.max(schedule.started+14000,frame+1100,schedule.otherNext);schedule.otherNext=when+1900;}
   if(when>frame)await new Promise(done=>setTimeout(done,when-frame));
   schedule.requests.push({file:u.pathname.slice(1),queued_ms:when-frame,at:Date.now()});
   await route.continue().catch(()=>{});
  });
  result.networkProfile={latency:16,download_bytes_per_second:1400000,map_pixel_ratio:.30,antialias:false,workers:1,neighbor_queue_ms:1900};
  let collecting=false;const timer=setInterval(async()=>{if(collecting)return;collecting=true;try{await cdp.send('Memory.simulatePressureNotification',{level:'moderate'});await cdp.send('HeapProfiler.collectGarbage');}catch{}finally{collecting=false;}},2500);timer.unref();

  let materialNext=Date.now()+35000;
  await page.route('**/assets/materials/realism-v4/**',async route=>{
   const when=Math.max(Date.now(),materialNext);materialNext=when+4500;
   await new Promise(ok=>setTimeout(ok,when-Date.now()));await route.continue().catch(()=>{});
  });
  const promises=[];
  page.on('pageerror',e=>result.errors.push(e.message));
  page.on('console',m=>{if(m.type()==='warning'&&m.text().includes('[Shanghai map]'))result.warnings.push(m.text());});
  page.on('response',res=>{
   const rel=new URL(res.url()).pathname.slice(1);
   if(rel===row.assets.web.file||rel===row.assets.lod.file||rel.includes('1_1-s1-s0.glb.gz')||rel.endsWith('/'+macro+'/index.json')){
    promises.push(res.body().then(body=>{result.responses[rel]={sha256:sha(body),bytes:body.length,status:res.status()};}).catch(err=>{(result.responseReadErrors??=[]).push([rel,String(err)]);}));
   }
  });
  await page.addInitScript(()=>{window.addEventListener('error',()=>{});Object.defineProperty(window,'devicePixelRatio',{get:()=>.55,configurable:true});});
  await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
  const entry=page.locator('article[data-landmark="'+id+'"]');assert.equal(await entry.count(),1);
  result.realDirectoryCount=await page.locator('article[data-landmark]').count();
  const link=entry.locator('.card-foot a[href*="mode=walk"]');
  await page.evaluate(()=>document.addEventListener('pointerup',ev=>sessionStorage.setItem('city-review-directory',JSON.stringify({id:ev.target.closest('[data-landmark]')?.dataset.landmark,trusted:ev.isTrusted,type:ev.pointerType})),{capture:true,once:true}));
  save();await link.click();result.reachedFromDirectory=page.url();save();
  await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene?.map,null,{timeout:160000});
  result.inputs.push(await page.evaluate(()=>JSON.parse(sessionStorage.getItem('city-review-directory'))));assert.equal(result.inputs[0].id,id);assert(result.inputs[0].trusted);
  await page.evaluate(async({id,macro})=>{
   const sc=window.__SHANGHAI_APP__.scene;
   sc.setVisualQuality({shadows:false,surfaceNormals:true});
   sc.map.setPixelRatio(.30);
   const T=await import('/vendor/three.module.js');
   const original=T.Object3D.prototype.updateMatrixWorld;
   const watched=new WeakSet();window.renderWitness={};
   T.Object3D.prototype.updateMatrixWorld=function(force){
    const value=original.call(this,force);
    const tag=this.userData||{};
    if((tag.cityPreservedLocalIds?.length===17||tag.cityReplacement?.landmark_id===id)&&!watched.has(this)){
     const key=tag.cityReplacement?'previousOwner':'neighbors';
     const obj=this, witness={name:obj.name,ids:tag.cityPreservedLocalIds||tag.cityReplacement.local_ids,draws:0,meshes:0};window.renderWitness[key]=witness;watched.add(obj);
     Object.defineProperty(witness,'visible',{enumerable:true,get:()=>obj.visible});
     obj.traverse(mesh=>{if(!mesh.isMesh)return;witness.meshes++;const prev=mesh.onBeforeRender;mesh.onBeforeRender=function(...args){witness.draws++;return prev.apply(this,args);};});
    }
    return value;
   };
  },{id,macro});
  async function jump(zoom,bearing=0,pitch=26){
   await page.evaluate(({anchor,zoom,pitch,bearing})=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo({center:anchor,zoom,pitch,bearing,elevation:0,padding:{top:0,bottom:0,left:90,right:0}});s.loadLandmarks();s.refreshBuildingBeacons();},{anchor:row.anchor,zoom,pitch,bearing});
  }
  async function state(phase,role){
   await page.waitForFunction(({id,role})=>{let s=window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id);return s.status==='loaded'&&s.visible&&s.variant===role&&s.verifiedAsset;},{id,role},{timeout:140000,polling:400});
   const state=await page.evaluate(id=>{let scene=window.__SHANGHAI_APP__.scene,m=scene.map,asset=scene.getLandmarkAssetState(id);return {asset,camera:{zoom:m.getZoom(),center:m.getCenter(),pitch:m.getPitch(),cameraAltitude:m.transform.getCameraAltitude?.(),cameraLocation:m.transform.getCameraLngLat?.()},registered:scene.getLandmarkState().filter(r=>r.id===id),detail:scene.getStreamingState().detail,ordinaryCatalog:scene.getOrdinaryCatalogState(),neighbors:window.renderWitness,route:location.hash};},id);
   const declared=row.assets[role==='full'?'web':'lod'];
   assert.deepEqual(state.asset.anchor,row.anchor);assert.equal(state.registered.length,1);assert.equal(state.asset.verifiedAsset.sha256,declared.sha256);assert.equal(state.asset.triangles,role==='full'?row.triangles:row.lod_triangles);
   result[phase]=state;save();const name=phase+'.jpg',img=await page.screenshot({type:'jpeg',quality:83,path:path.join(out,name),timeout:30000});result.images[phase]={name,bytes:img.length,sha256:sha(img)};save();
  }
  await page.waitForFunction(()=>{const cover=document.getElementById('loading');return cover?.classList.contains('loaded') && getComputedStyle(cover).visibility==='hidden';},null,{timeout:180000});
  await page.locator('#overview-mode').click();
  const toggle=page.locator('#panel-toggle');
  if(await toggle.getAttribute('aria-expanded')==='true')await toggle.click();
  await jump(20.1,24,52);await state('near','full');
  if(await toggle.getAttribute('aria-expanded')!=='true')await toggle.click();
  const place=page.locator('button[data-place="'+id+'"]');if(!await place.count())await page.locator('#landmark-tab').click();
  await place.scrollIntoViewIfNeeded();await page.evaluate(()=>window.addEventListener('pointerup',e=>{window.placeClick={id:e.target.closest('button[data-place]')?.dataset.place,trusted:e.isTrusted,type:e.pointerType};},{once:true,capture:true}));await place.click();
  const placeInfo=await page.evaluate(()=>window.placeClick);assert(placeInfo.trusted&&placeInfo.id===id);result.inputs.push(placeInfo);save();
  if(await toggle.getAttribute('aria-expanded')==='true')await toggle.click();
  if(await page.locator('#overview-mode').getAttribute('aria-pressed')!=='true')await page.locator('#overview-mode').click();
  await jump(18.6,0,0);
  const b=await page.waitForFunction(id=>{
   const s=window.__SHANGHAI_APP__.scene,c=s.map.getCanvas(),r=c.getBoundingClientRect();
   const label=s.getBuildingBeaconState()?.labelPositions.find(b=>b.id===id||b.memberIds?.includes(id));if(!label)return false;
   for(const dx of [0,-.2,.2])for(const dy of [0,-.18,.18]){const x=label.x+dx*(label.width||0),y=label.y+dy*(label.height||0);if(s.pickBuildingBeacon({x,y})===label.id&&document.elementFromPoint(r.x+x,r.y+y)===c)return {x:x+r.x,y:y+r.y,id:label.id,members:label.memberIds||[]};}return false;
  },id,{timeout:36000,polling:300});
  const point=await b.jsonValue();
  await page.evaluate(()=>window.addEventListener('pointerup',e=>{const s=window.__SHANGHAI_APP__.scene,c=s.map.getCanvas(),r=c.getBoundingClientRect();window.beaconClick={trusted:e.isTrusted,type:e.pointerType,canvas:e.target===c,id:s.pickBuildingBeacon({x:e.clientX-r.x,y:e.clientY-r.y})};},{once:true,capture:true}));
  await page.mouse.click(point.x,point.y);const click=await page.evaluate(()=>window.beaconClick);assert(click.trusted&&click.canvas&&click.id===point.id);result.inputs.push({beacon:click,point});
  if(point.id!==id){assert(point.members.includes(id));await page.locator('dialog.beacon-group-picker[open] [data-landmark="'+id+'"]').click();}
  await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id);save();
  await jump(15.8,0,20);await state('far','distant');
  await jump(19.9,24,52);await state('returnedNear','full');
  await page.waitForFunction(()=>window.renderWitness.neighbors?.draws>0&&window.renderWitness.previousOwner?.visible===false,null,{timeout:90000,polling:350});
  result.neighborEvidence=await page.evaluate(()=>({groups:window.renderWitness,detail:window.__SHANGHAI_APP__.scene.getStreamingState().detail}));
  assert.deepEqual([...result.neighborEvidence.groups.neighbors.ids].sort((a,b)=>a-b),[...row.owner.preserve_neighbor_local_ids].sort((a,b)=>a-b));
  await Promise.allSettled(promises);
  for(const role of ['web','lod']){const reference=row.assets[role],actual=result.responses[reference.file];assert(actual&&actual.sha256===reference.sha256&&actual.bytes===reference.bytes&&actual.status===200);}
  clearInterval(timer);result.networkSchedule=schedule.requests;result.passed=true;
 }catch(e){result.failure=String(e.stack);if(page)result.lastState=await page.evaluate(id=>{const scene=window.__SHANGHAI_APP__?.scene;return {route:location.href,state:scene?.getLandmarkAssetState(id),neighbors:window.renderWitness,detail:scene?.getStreamingState().detail};},id).catch(()=>null);throw e;}
 finally{await browser.close();result.browserClosed=!browser.isConnected();result.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
