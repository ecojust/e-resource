const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{createHash}=require('node:crypto');
const{chromium}=require('playwright');
const dir=__dirname,base='http://127.0.0.1:20093/',id='huangpu-hamilton-house',read=n=>JSON.parse(fs.readFileSync(n)),hash=b=>createHash('sha256').update(b).digest('hex');
const proposal=read(path.join(dir,'proposal.json')),source=read(path.join(dir,'bindings.json')),points=read(path.join(dir,'points.json'));
const oldRoot='/workspace/e-resource/projects/shanghai/data/audit/hamilton-house-v1';
const oldDesk=read(path.join(oldRoot,'public-zoom-steps.json')).views[0],oldSite=read(path.join(oldRoot,'main-map-browser.json'));
const report={started:new Date().toISOString(),base,id,script:hash(fs.readFileSync(__filename)),proposal:proposal.new_snapshot_sha256,completed:false,views:{},responses:{},errors:[],actions:[]};
const save=()=>fs.writeFileSync(path.join(dir,'result.json'),JSON.stringify(report,null,2)+'\n');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9593']});
 const catalogResponse=await (await fetch(base+'data/candidate-city-integrations.json')).arrayBuffer(),bytes=Buffer.from(catalogResponse);assert.equal(hash(bytes),proposal.http['data/candidate-city-integrations.json'].sha256);
 const cat=JSON.parse(bytes);assert.equal(cat.resulting_city_count,135);const row=cat.models.find(r=>r.id===id);
 const bindings={'src/map-scene.js':proposal.http['src/map-scene.js'].sha256,'src/building-beacons.js':proposal.http['src/building-beacons.js'].sha256,'src/building-beacon-groups.js':proposal.http['src/building-beacon-groups.js'].sha256,[row.assets.web.file]:row.assets.web.sha256};
 let page;const pending=[];
 async function settle(){
  await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__?.scene,m=s?.map;if(!m||m.isMoving())return false;
   const asset=s.getLandmarkAssetState(id),g=s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.clip_feature_local_ids.includes(1844)&&g.feature_local_ids.includes(1415));
   const layers=m.getStyle().layers.filter(l=>l.id.endsWith('labels-symbol')||l.id.endsWith('labels-numbers')).map(l=>l.id);
   return asset?.status==='loaded'&&asset.visible&&asset.variant==='full'&&g&&s.getStreamingState().detail.active.some(x=>x.id===g.id)&&layers.length===2&&m.queryRenderedFeatures({layers}).some(f=>f.properties.id===id)&&new URLSearchParams(location.hash.slice(1)).get('landmark')===id;
  },id,{timeout:310000,polling:700});
  await page.evaluate(()=>new Promise(r=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>r());m.triggerRepaint();}));
 }
 async function open(mobile){
  page=await browser.newPage({viewport:mobile?{width:390,height:844}:{width:900,height:650},hasTouch:mobile,isMobile:mobile,ignoreHTTPSErrors:true});
  page.setDefaultTimeout(220000);page.on('pageerror',e=>report.errors.push(e.message));const resp={};report.responses[mobile?'mobile':'desktop']=resp;
  page.on('response',r=>{const key=new URL(r.url()).pathname.slice(1);if(bindings[key]&&r.status()===200)pending.push(r.body().then(data=>{resp[key]=hash(data);assert.equal(resp[key],bindings[key]);}));});
  await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
  assert.equal(await page.locator('.landmark-card[data-landmark]').count(),135);
  const link=page.locator('#district-310101 [data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]');
  if(mobile)await link.tap();else await link.click();await settle();
 }
 async function state(){
  return page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,b=s.getBuildingBeaconState(),a=s.getLandmarkAssetState(id),layers=m.getStyle().layers.filter(l=>l.id.endsWith('labels-symbol')||l.id.endsWith('labels-numbers')).map(l=>l.id),drawn=new Set(m.queryRenderedFeatures({layers}).map(f=>f.properties.id));
   const labels=b.labelPositions.filter(p=>drawn.has(p.id)).map(p=>{const hits=[];for(const x of [-.40,0,.40])for(const y of [-.40,0,.40]){const point={x:p.x+p.width*x,y:p.y+p.height*y};const dom=document.elementFromPoint(point.x,point.y);hits.push({x:point.x,y:point.y,picked:s.pickBuildingBeacon(point),top:dom?.className||dom?.tagName});}return {...p,hits};});
   const hud=Object.fromEntries(['#explore-panel','#location-card','#building-beacon-legend','.topbar','.map-tools'].map(sel=>[sel,document.querySelector(sel)?.getBoundingClientRect().toJSON()]));
   return {camera:{center:m.getCenter(),zoom:m.getZoom(),bearing:m.getBearing(),pitch:m.getPitch(),elevation:m.getCenterElevation()},viewport:[innerWidth,innerHeight],
    route:location.hash,name:document.querySelector('#location-name').textContent,nav:document.querySelector('#panel-toggle').getAttribute('aria-expanded'),count:b.count,labels,hud,asset:a.verifiedAsset,triangles:a.triangles,variant:a.variant,webgl:m.painter.context.gl.isContextLost()};
  },id);
 }
 async function record(key){
  if(key==='desktop')await page.waitForFunction(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,ls=m.getStyle().layers.filter(l=>l.id.endsWith('labels-symbol')||l.id.endsWith('labels-numbers')).map(l=>l.id),draw=new Set(m.queryRenderedFeatures({layers:ls}).map(f=>f.properties.id));return s.getBuildingBeaconState().labelPositions.filter(l=>draw.has(l.id)).length===7;},null,{polling:650,timeout:130000});
  const st=await state();assert.equal(st.count,135);assert.equal(st.triangles,39472);assert.equal(st.webgl,false);assert.equal(st.asset.sha256,source.mesh.input_sha256);assert.equal(st.variant,'full');
  for(const a of st.labels)assert(a.hits.every(h=>h.picked===a.id&&String(h.top).includes('maplibregl-canvas')),'hit targets '+a.id);
  const coords=await page.evaluate(({row,points})=>{const t=window.__SHANGHAI_APP__.scene.map.transform,rad=Math.PI/180,ang=rad*row.heading,co=Math.cos(ang),si=Math.sin(ang),k=6371008.8*Math.cos(row.lat*rad),lat0=Math.asinh(Math.tan(row.lat*rad));
    return points.map(([x,y,z])=>{const e=x*co+y*si,n=-x*si+y*co,high=()=>z;const s=t.locationToScreenPoint({lng:row.lng+e/k/rad,lat:Math.atan(Math.sinh(lat0+n/k))/rad},{getElevationForLngLat:high,getElevationForLngLatZoom:high});return [Math.round(s.x*1000)/1000,Math.round(s.y*1000)/1000];});},{row,points});
  fs.writeFileSync(path.join(dir,key+'-projection.json'),JSON.stringify(coords));st.projectionSha256=hash(fs.readFileSync(path.join(dir,key+'-projection.json')));
  const name=key+'.png',png=await page.screenshot({path:path.join(dir,name),timeout:260000});report.views[key]={...st,file:name,sha256:hash(png),bytes:png.length};save();console.log('Recorded',key,st.labels.length);
 }
 try{
  await open(false);await record('desktop');const desk=report.views.desktop;assert.equal(desk.nav,'true');assert.equal(desk.labels.length,7);
  assert(Math.abs(desk.camera.zoom-oldDesk.camera.zoom)<.0001);const moved=desk.labels.filter(p=>p.id!==id).map(p=>{const old=oldDesk.labels.find(x=>x.id===p.id);assert(old);return {p,d:Math.hypot(old.x-p.x,old.y-p.y)};}).sort((a,b)=>b.d-a.d);
  assert(moved[0].d>10);const target=moved[0].p;
  await page.mouse.click(target.x,target.y);await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,target.id);
  const targetRow=cat.models.find(r=>r.id===target.id);const reached=await page.locator('#location-name').innerText();if(targetRow)assert.equal(reached,targetRow.name);
  report.actions.push({kind:'real mouse click on relocated neighbouring sign',at:[target.x,target.y],movedBy:moved[0].d,selected:target.id,name:reached});save();
  await page.locator('#place-search').fill('汉弥登');await page.locator('#place-list button[data-place="'+id+'"]').click();await page.locator('#place-search').fill('');await settle();
  report.actions.push({kind:'returned through visible navigation search result',name:await page.locator('#location-name').innerText(),hash:await page.evaluate(()=>location.hash)});
  await page.locator('#zoom-in').click();await page.waitForFunction(z=>{const m=window.__SHANGHAI_APP__.scene.map;return m.getZoom()>z+.85&&!m.isMoving();},desk.camera.zoom);
  report.actions.push({kind:'pressed public zoom-in',zoom:await page.evaluate(()=>window.__SHANGHAI_APP__.scene.map.getZoom())});
  await page.locator('#reset-place').click();await settle();const restored=await state();assert(Math.abs(restored.camera.zoom-desk.camera.zoom)<.001);assert.equal(restored.name,desk.name);
  report.actions.push({kind:'pressed public reset',camera:restored.camera,selected:restored.route});save();await Promise.all(pending);await page.close();
  await open(true);await record('mobile');const mob=report.views.mobile,old=oldSite.views.find(v=>v.view==='main-mobile');assert.equal(mob.nav,'false');assert.equal(mob.viewport.join(','),old.viewport.join(','));assert(Math.abs(mob.camera.zoom-old.camera.zoom)<.0001);
  const focus=mob.labels.find(x=>x.id===id);for(const k of ['x','y','width','height'])assert(Math.abs(focus[k]-old.selected_label[k])<.51);
  await page.touchscreen.tap(focus.x,focus.y);await page.waitForFunction(id=>document.querySelector('#location-name').textContent.includes('汉弥登')&&new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id);
  report.actions.push({kind:'real mobile tap on existing Hamilton sign',at:[focus.x,focus.y],selected:await page.evaluate(()=>location.hash)});await Promise.all(pending);
  for(const d of Object.values(report.responses))for(const [f,expected] of Object.entries(bindings))assert.equal(d[f],expected,f);
  assert.deepEqual(report.errors,[]);report.completed=true;
 }catch(e){report.failure=e.stack;throw e;}finally{await browser.close();report.closed=true;report.finished=new Date().toISOString();save();}
})().catch(e=>{console.error(e);process.exitCode=1});
