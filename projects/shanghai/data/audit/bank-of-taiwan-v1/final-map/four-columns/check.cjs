const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const {createHash}=require('node:crypto'),{chromium}=require('playwright');
const [base,output,...flags]=process.argv.slice(2);
const prefix=new URL(base).origin, id='huangpu-bank-of-taiwan-building';
const read=f=>JSON.parse(fs.readFileSync(f)),sha=b=>createHash('sha256').update(b).digest('hex');
const columns=read(path.join(__dirname,'columns.json')).columns;
const report={id,base,started:new Date().toISOString(),script_sha256:sha(fs.readFileSync(__filename)),columns_input_sha256:sha(fs.readFileSync(path.join(__dirname,'columns.json'))),views:{},actions:[],files:{},pageErrors:[],completed:false};
fs.mkdirSync(output,{recursive:true});
const save=()=>fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify(report,null,2)+'\n');
const catalogFile='data/candidate-city-integrations.json';
async function run(){
 const catalogBytes=Buffer.from(await (await fetch(new URL(catalogFile,base))).arrayBuffer());
 const catalog=JSON.parse(catalogBytes);const row=catalog.models.find(m=>m.id===id);
 assert.equal(catalog.resulting_city_count,153);report.catalog_sha256=sha(catalogBytes);report.framing={bounds:row.bounds_glb,label:row.label_focus_bounds_glb,overview:row.overview_focus_bounds_glb};
 const bindings=Object.fromEntries(await Promise.all([catalogFile,'src/map-scene.js','src/building-beacons.js',row.candidate_manifest,row.assets.web.file].map(async f=>[f,sha(Buffer.from(await(await fetch(new URL(f,base))).arrayBuffer()))])));
 assert.equal(bindings[row.assets.web.file],row.assets.web.sha256);report.expected=bindings;save();
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try {
  for(const mode of flags.includes('--mobile-only')?['mobile']:flags.includes('--desktop-only')?['desktop']:['mobile','desktop']){
   const mobile=mode==='mobile',dims=mobile?{width:390,height:844}:{width:870,height:660};
   const context=await browser.newContext({viewport:dims,isMobile:mobile,hasTouch:mobile});const page=await context.newPage();
   page.setDefaultTimeout(270000);const tasks=[],files={};report.files[mode]=files;
   page.on('pageerror',e=>report.pageErrors.push(e.message));
   page.on('response',r=>{const u=new URL(r.url()),f=u.pathname.slice(1);if(u.origin!==prefix||r.status()!==200||!bindings[f])return;
    tasks.push(r.body().then(b=>{files[f]={sha256:sha(b),bytes:b.length,url:r.url(),via:'original browser response'};}).catch(e=>{files[f]={bodyError:e.message,url:r.url()};}));});
   async function settle(){
    await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__?.scene,m=s?.map,boot=document.querySelector('#loading');
     if(!m||m.isMoving()||!boot||getComputedStyle(boot).visibility!=='hidden'||Number(getComputedStyle(boot).opacity)!==0)return false;
     const a=s.getLandmarkAssetState(id),c=s.getCandidateIntegrationState(),g=c.shader.ownerScopedSources.find(t=>t.clip_feature_local_ids?.includes(228)), streaming=s.getStreamingState();
     if(!a?.visible||a.variant!=='full'||a.status!=='loaded'||!g||!streaming.detail.active.some(t=>t.id===g.id))return false;
     const ls=m.getStyle().layers.filter(l=>l.id.endsWith('labels-symbol')||l.id.endsWith('labels-numbers')).map(l=>l.id);
     return ls.length===2&&m.queryRenderedFeatures({layers:ls}).some(v=>v.properties.id===id);
    },id,{timeout:295000,polling:500});
    await page.evaluate(()=>new Promise(resolve=>{let n=0;const m=window.__SHANGHAI_APP__.scene.map;const next=()=>{m.once('render',()=>++n===4?resolve():next());m.triggerRepaint()};next()}));
   }
   async function capture(name){
    await settle();const snap=await page.evaluate(({id,row,columns})=>{
     const s=window.__SHANGHAI_APP__.scene,m=s.map,b=s.getBuildingBeaconState(),t=m.transform,ls=m.getStyle().layers.filter(l=>l.id.endsWith('labels-symbol')||l.id.endsWith('labels-numbers')).map(l=>l.id);
     const drawn=new Set(m.queryRenderedFeatures({layers:ls}).map(f=>f.properties.id));const labels=b.labelPositions.filter(l=>drawn.has(l.id)).map(l=>{
      const hits=[];for(const ox of [-.40,0,.40])for(const oy of [-.40,0,.40]){const p={x:l.x+l.width*ox,y:l.y+l.height*oy};hits.push({picked:s.pickBuildingBeacon(p),top:document.elementFromPoint(p.x,p.y)?.className||''});}return {...l,hits};});
     const rad=Math.PI/180,an=rad*row.heading,co=Math.cos(an),si=Math.sin(an),k=6371008.8*Math.cos(row.lat*rad),lat0=Math.asinh(Math.tan(row.lat*rad));
     const projection=Object.fromEntries(Object.entries(columns).map(([key,c])=>[key,c.vertices.map(([x,y,z])=>{const e=x*co+y*si,n=-x*si+y*co,hi=()=>z;const o=t.locationToScreenPoint({lng:row.lng+e/k/rad,lat:Math.atan(Math.sinh(lat0+n/k))/rad},{getElevationForLngLat:hi,getElevationForLngLatZoom:hi});return [Math.round(o.x*1000)/1000,Math.round(o.y*1000)/1000];})]));
     return {projection,labels,viewport:[innerWidth,innerHeight],camera:{center:m.getCenter(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),elevation:m.getCenterElevation(),padding:m.getPadding()},mode:b.labelMode,count:b.count,asset:s.getLandmarkAssetState(id),route:location.hash,name:document.querySelector('#location-name').textContent,panel:document.querySelector('#panel-toggle').getAttribute('aria-expanded'),hud:Object.fromEntries(['#explore-panel','#location-card','#building-beacon-legend','.topbar','.map-tools'].map(k=>[k,document.querySelector(k)?.getBoundingClientRect().toJSON()])),activeSource:s.getCandidateIntegrationState().shader.ownerScopedSources.find(t=>t.clip_feature_local_ids?.includes(228)),contextLost:m.painter.context.gl.isContextLost()};
    },{id,row,columns});
    assert.equal(snap.asset.triangles,54008);assert.equal(snap.asset.verifiedAsset.sha256,bindings[row.assets.web.file]);assert.equal(snap.count,153);assert(!snap.contextLost);assert.equal(snap.panel,mobile?'false':'true');
    const xy=JSON.stringify(snap.projection);delete snap.projection;fs.writeFileSync(path.join(output,name+'-projection.json'),xy);
    const png=await page.screenshot({path:path.join(output,name+'.png'),timeout:270000});
    report.views[name]={...snap,sha256:sha(png),bytes:png.length,projection_sha256:sha(xy)};save();console.log('captured',name,snap.camera.zoom,snap.labels.length);
    return snap;
   }
   await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
   assert.equal(await page.locator('.landmark-card[data-landmark]').count(),153);
   const link=page.locator('#district-310101 [data-landmark="'+id+'"] .card-foot a[href^="index.html"]');
   if(mobile)await link.tap();else await link.click();
   const first=await capture(mode+'-default');
   if(mobile&&!flags.includes('--defaults-only')){
    const focus=first.labels.find(v=>v.id===id);assert(focus);
    await page.touchscreen.tap(focus.x,focus.y);await settle();
    report.actions.push({action:'touch own sign',selected:await page.evaluate(()=>location.hash),x:focus.x,y:focus.y});
    await page.locator('#zoom-in').tap();await page.waitForFunction(z=>window.__SHANGHAI_APP__.scene.map.getZoom()>z+.65,first.camera.zoom);
    await capture('mobile-plus');}
   if(!mobile&&!flags.includes('--defaults-only')){
    const n=first.labels.find(v=>v.id!==id&&!v.memberIds?.length&&v.hits.every(h=>h.picked===v.id&&String(h.top).includes('maplibregl-canvas')));assert(n,'a navigable neighbouring sign');
    await page.mouse.click(n.x,n.y);await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,n.id);
    report.actions.push({action:'click neighbouring sign',x:n.x,y:n.y,id:n.id,selected:await page.evaluate(()=>location.hash),name:await page.locator('#location-name').innerText()});
   }
   await Promise.all(tasks);
   for(const [file,expected] of Object.entries(bindings)){
    if(!files[file]?.sha256){const r=await page.request.get(new URL(file,base).href);assert.equal(r.status(),200);const body=await r.body();files[file]={...files[file],via:'explicit browser request following page inspection',sha256:sha(body),bytes:body.length};}
    assert.equal(files[file].sha256,expected,file);}
   save();await context.close();}
  assert.deepEqual(report.pageErrors,[]);report.completed=true;
 }catch(err){report.failure=err.stack;throw err;}finally{await browser.close();report.closed=true;report.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
