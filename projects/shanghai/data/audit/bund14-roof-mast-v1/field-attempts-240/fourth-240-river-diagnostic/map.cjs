/* Exercise the official Bund 14 destination and the specific roof change via the real city application. */
const fs=require('node:fs'), path=require('node:path'), crypto=require('node:crypto');
const assert=require('node:assert/strict'),{chromium}=require('playwright');
const home=__dirname, phase=process.argv[2], read=f=>JSON.parse(fs.readFileSync(f)), hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const spec=read(path.join(home,'bound.json')), old=['before','old-river','old-roof'].includes(phase), stage=old?'239':'240';
const exact=spec.stages[stage],row=exact.row,id='bund14',out=path.join(home,'evidence',phase),mobile=['phone','touch'].includes(phase);
const file=path.join(out,'browser.json'),R={id,phase,port:exact.port,base:exact.origin,case_sha256:hash(fs.readFileSync(path.join(home,'bound.json'))),driver_sha256:hash(fs.readFileSync(__filename)),completed:false,started:new Date().toISOString(),screenshots:[],states:[],localResponses:{},failed:[],errors:[]};
const save=()=>fs.writeFileSync(file,JSON.stringify(R,null,2)+'\n');
const route=(who,mode)=>exact.origin+'index.html#landmark='+who+'&mode='+mode;
async function main(){
 fs.mkdirSync(out,{recursive:true});assert(!fs.existsSync(file),'Keep any preceding browser observations.');save();
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--enable-low-end-device-mode','--num-raster-threads=1','--renderer-process-limit=1','--disable-gpu-rasterization','--js-flags=--max-old-space-size=384','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:mobile?{width:390,height:844}:phase==='distant'?{width:512,height:450}:['old-roof','roof','old-river','river'].includes(phase)?{width:790,height:535}:{width:850,height:650},hasTouch:mobile,deviceScaleFactor:1,acceptDownloads:true});
 page.setDefaultTimeout(180000);const jobs=[],observed=new Set();
 page.on('pageerror',e=>R.errors.push(e.message));
 page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')R.failed.push({url:r.url(),reason:r.failure()?.errorText});});
 const urls=new Map(Object.values(exact.assets).map(a=>[a.path,a]));
 if(phase==='neighbors')for(const n of Object.values(spec.neighbors)) {urls.set(n.model,{sha256:n.web_sha256});urls.set(n.lod_model,{sha256:n.lod_sha256});}
 for(const [k,v] of Object.entries(exact.files))if(['src/app.js','src/map-scene.js','data/landmarks.json'].includes(k))urls.set(k,v);
 page.on('response',r=>{const u=new URL(r.url());if(u.origin!==new URL(exact.origin).origin)return;const key=decodeURIComponent(u.pathname.slice(1));if(r.status()>=400)R.failed.push({url:u.href,status:r.status()});if(r.status()!==200)return;observed.add(key);if(!urls.has(key)||R.localResponses[key])return;
  jobs.push(r.body().then(b=>{const h=hash(b);assert.equal(h,urls.get(key).sha256,key);R.localResponses[key]={sha256:h,bytes:b.length,query:u.search};}).catch(e=>{if(!/No resource with given identifier found|Request content was evicted|No data found for resource|Target page.*closed/.test(String(e)))R.errors.push(String(e));}));
 });
 async function waitAsset(who=id,variant=null){await page.waitForFunction(({who,variant})=>{const s=window.__SHANGHAI_APP__?.scene,m=s?.map,a=s?.getLandmarkAssetState(who);return !!(m&&a?.visible&&a.status==='loaded'&&(!variant||a.variant===variant)&&!m.isMoving());},{who,variant},{polling:300,timeout:220000});}
 async function frame(){await page.evaluate(()=>new Promise(done=>{const map=window.__SHANGHAI_APP__.scene.map;map.once('render',()=>done());map.triggerRepaint();}));}
 async function panel(){const t=page.locator('#panel-toggle');if(await t.getAttribute('aria-expanded')==='true')await t.click();}
 async function state(who=id){return page.evaluate(who=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,g=s.getLandmarkAssetState(who),c=a.controller,gl=m.painter.context.gl;return {id:who,route:location.hash,mode:a.mode,asset:g,pose:{lng:c.position.lng,lat:c.position.lat,bearing:c.bearing,speed:c.speed},camera:{center:m.getCenter().toArray(),bearing:m.getBearing(),zoom:m.getZoom(),pitch:m.getPitch(),elevation:m.getCenterElevation(),padding:m.getPadding()},ground:s.collisionAt(c.position.lng,c.position.lat),renderer:gl.getParameter(gl.RENDERER),glError:gl.getError(),lost:gl.isContextLost(),place:document.querySelector('#location-name')?.textContent};},who);}
 async function image(name,who=id){await frame();await frame();const st=await state(who),rr=who===id?row:spec.neighbors[who];assert(st.asset.visible&&!st.lost);assert.equal(st.glError,0);assert.equal(st.asset.triangles,st.asset.variant==='full'?rr.triangles:rr.lod_triangles);assert.equal(new URLSearchParams(st.route.slice(1)).get('landmark'),who);const b=await page.screenshot({path:path.join(out,name+'.png'),timeout:180000});R.states.push(st);R.screenshots.push({file:name+'.png',sha256:hash(b),bytes:b.length});save();return st;}
 async function jump(c){await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},c);}
 async function uiPoints(){return page.evaluate(points=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,cv=m.getCanvas(),br=cv.getBoundingClientRect();return points.map(o=>{const elevation=()=>o.z,p=m.transform.locationToScreenPoint({lng:o.position[0],lat:o.position[1]},{getElevationForLngLat:elevation,getElevationForLngLatZoom:elevation}),x=p.x+br.left,y=p.y+br.top,hit=document.elementFromPoint(x,y),beacon=s.pickBuildingBeacon(p);return {...o,x,y,clear:hit===cv&&!beacon,beacon,foreground:hit?{tag:hit.tagName,id:hit.id,classes:hit.className}:null};});},spec.photo_points);}
 async function onMap(who=id,mode='overview'){await page.goto(route(who,mode),{waitUntil:'domcontentloaded'});await waitAsset(who);}
 async function targetMode(mode){assert.equal(await page.locator('#'+mode+'-mode').count(),1);if(mobile)await page.locator('#'+mode+'-mode').tap();else await page.locator('#'+mode+'-mode').click();await page.waitForFunction(m=>window.__SHANGHAI_APP__?.mode===m,mode);await waitAsset();}
 try{
  if(['before','phone','desktop'].includes(phase)){
   await page.goto(exact.origin+'landmarks.html',{waitUntil:'domcontentloaded'});assert.equal(await page.locator('.landmark-card[data-landmark]').count(),276);
   const destination=page.locator('article[data-landmark="bund14"] .card-foot a[href="index.html#landmark=bund14&mode=walk"]');if(mobile)await destination.tap();else await destination.click();await waitAsset(id,'full');const s=await image(phase+'-walk');assert.equal(s.mode,'walk');
   const groundPoints=[{name:'signed street start',p:row.walkStart},{name:'Bund 14 footprint',p:[row.lng,row.lat]},...Object.values(spec.neighbors).map(n=>({name:n.id,p:[n.lng,n.lat]}))];
   R.ground=await page.evaluate(async points=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(18000);return points.map(q=>({...q,collision:s.collisionAt(...q.p)}));},groundPoints);assert.equal(R.ground[0].collision,null);for(const q of R.ground.slice(1))assert.equal(q.collision,'building',q.name);
   const delta=Math.hypot((s.pose.lng-row.walkStart[0])*95000,(s.pose.lat-row.walkStart[1])*111320);assert(delta<2,'Walk origin differs from historical row');await targetMode('overview');await image(phase+'-overview');if(mobile){await page.locator('#zoom-in').tap();await waitAsset();await image('phone-zoom');}
  } else if(['old-roof','roof','old-river','river'].includes(phase)){
   const which=phase.endsWith('roof')?'roof':'river',c={...spec.cameras[which]};
   if(which==='roof')c.zoom=21.78;
   await page.goto(route(id,'overview'),{waitUntil:'domcontentloaded'});
   await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene?.map?.isStyleLoaded());
   let pads=[];
   // The dense north-bank beacon labels cover the upper half of the old
   // roof view. Reframe the same surveyed camera lower in the viewport.
   for(const shift of [77,111,139,45,18,-28,155]){
     for(const horizontal of [185,132,82,216,25,-46,-140]){
       pads.push({left:Math.max(0,horizontal*2),right:Math.max(0,-horizontal*2),top:Math.max(0,shift*2),bottom:Math.max(0,-shift*2)});
     }
   }
   if(!old){const parent=read(path.join(home,'evidence','old-'+which,'browser.json'));assert(parent.completed);pads=[parent.cameraUsed.padding];}
   await jump({...c,padding:pads[0]});await panel();let found=false;R.pointAttempts=[];
   for(const pad of pads){const camera={...c,padding:pad};await jump(camera);await waitAsset(id,'full');await frame();const pts=await uiPoints();R.pointAttempts.push({camera,points:pts});save();if(pts.every(p=>p.clear)){found=true;R.cameraUsed=camera;R.points=pts;break;}}
   assert(found,'The map interface covers a projected roof feature');await image(phase+'-comparison');
  } else if(phase==='walk-return'){
   await onMap(id,'walk');await panel();const previous=await state();await page.locator('canvas.maplibregl-canvas').focus();await page.keyboard.down('s');
   try{await page.waitForFunction(({lng,lat})=>{const p=window.__SHANGHAI_APP__.controller.position;return Math.hypot((p.lng-lng)*95000,(p.lat-lat)*111320)>.8;},previous.pose,{polling:100,timeout:35000});}finally{await page.keyboard.up('s');}
   const current=await image('walk-away');assert.equal(current.mode,'walk');await targetMode('overview');await targetMode('walk');await image('walk-return');R.move={previous,current};
  } else if(['mouse','touch'].includes(phase)){
   const near='bund15';await onMap(near);await panel();await jump({center:[row.lng,row.lat],zoom:17.1,bearing:0,pitch:0,elevation:0});
   const hit=await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__?.scene,el=document.querySelector('#loading');if(!s||s.map.isMoving()||!el?.classList.contains('loaded')||getComputedStyle(el).visibility!=='hidden')return false;const p=s.getBuildingBeaconState().labelPositions.find(v=>v.id===id||v.memberIds?.includes(id));if(!p||s.pickBuildingBeacon(p)!==p.id)return false;const b=s.map.getCanvas().getBoundingClientRect(),x=b.x+p.x,y=b.y+p.y;if(document.elementFromPoint(x,y)!==s.map.getCanvas())return false;return {x,y,label:p.id,group:Boolean(p.memberIds),members:p.memberIds||[],route:location.hash};},id,{polling:250,timeout:200000});const pt=await hit.jsonValue();if(mobile)await page.touchscreen.tap(pt.x,pt.y);else await page.mouse.click(pt.x,pt.y);
   if(pt.group){const option=page.locator('dialog.beacon-group-picker[open] [data-landmark="bund14"]');if(mobile)await option.tap();else await option.click();}
   await page.waitForFunction(()=>new URLSearchParams(location.hash.slice(1)).get('landmark')==='bund14');await waitAsset();R.physical={...pt,device:phase};await image(phase+'-selected');
  } else if(phase==='neighbors'){
   for(const who of ['customs-house','bund15']){await onMap(who);await waitAsset(who,'full');await image(who,who);const n=spec.neighbors[who];assert(observed.has(n.model),who+' was never requested by the map');}await onMap();await waitAsset(id,'full');await image('return-bund14');
  } else if(phase==='distant'){
   await onMap();await waitAsset(id,'full');await panel();await jump({center:[row.lng,row.lat],zoom:15.7,pitch:12,bearing:row.bearing,elevation:0});await waitAsset(id,'distant');await image('distant');await jump(spec.cameras.river);await waitAsset(id,'full');await image('returned-full');
  } else throw Error(phase);
  await Promise.all(jobs);for(const key of ['src/app.js','src/map-scene.js','data/landmarks.json'])assert(observed.has(key),key);for(const st of R.states.filter(s=>s.id===id)){const a=exact.assets[st.asset.variant==='full'?'full':'lod'];assert(observed.has(a.path),'City did not request '+a.path);if(!R.localResponses[a.path]){const response=await page.request.get(exact.origin+a.path),b=await response.body();assert.equal(hash(b),a.sha256);R.localResponses[a.path]={sha256:hash(b),observed_original_request:true,checkedBySeparateGET:true};await response.dispose();}}
  assert.deepEqual(R.errors,[]);assert.deepEqual(R.failed,[]);R.completed=true;
 }catch(e){R.failure=e.stack;throw e;}finally{R.finished=new Date().toISOString();save();await browser.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
