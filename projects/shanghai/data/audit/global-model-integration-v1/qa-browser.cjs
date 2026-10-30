/* Shared city integration: real routes, WebGL assets, LOD and geographic transforms. MIT. */
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{createHash}=require('crypto');
const base=process.env.MODEL_BASE_URL||'http://127.0.0.1:8782/';
const output=process.env.QA_OUTPUT_DIR||__dirname;
const project=path.resolve(__dirname,'../../..');
const sha=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const dist=(a,b)=>Math.hypot((a.lng-b.lng)*111319.49079327358*Math.cos(b.lat*Math.PI/180),(a.lat-b.lat)*111319.49079327358);

(async()=>{
 const catalogPath=path.join(project,'data/candidate-city-integrations.json');
 const catalog=JSON.parse(fs.readFileSync(catalogPath));
 const inventory=JSON.parse(fs.readFileSync(path.join(__dirname,'inventory.json')));
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const scope=process.env.QA_SCOPE||'complete';
 const report={generatedAt:new Date().toISOString(),browserVersion:browser.version(),base,scope,completed:false,catalog_sha256:sha(catalogPath),script_sha256:sha(__filename),runtime:{},routes:[],models:[],screenshots:[],pageErrors:[],consoleErrors:[],httpErrors:[]};
 for(const name of ['app.js','map-scene.js','candidate-city-integrations.js','candidate-city-clipping.js','building-beacons.js']){const f=path.join(project,'src',name);if(fs.existsSync(f))report.runtime[name]=sha(f);}
 fs.mkdirSync(output,{recursive:true});
 const save=()=>fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify(report,null,2)+'\n');
 try{
  const page=await browser.newPage({viewport:{width:1280,height:900}});
  page.on('pageerror',e=>{report.pageErrors.push(e.message);console.error('PAGEERROR',e.message);});
  page.on('console',m=>{if(m.type()==='error'){report.consoleErrors.push(m.text());console.error('CONSOLE',m.text());}});
  page.on('response',r=>{if(r.status()>=400)report.httpErrors.push({url:r.url(),status:r.status()});});
  await page.goto(base+'index.html#landmark='+catalog.models[0].id+'&mode=overview',{waitUntil:'domcontentloaded',timeout:90000});
  await page.waitForFunction(()=>window.__SHANGHAI_APP__,null,{timeout:240000});
  console.log('PASS bootstrap',catalog.models.length,'candidate models');
  if(scope!=='visual'){await page.evaluate(()=>window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:false,surfaceNormals:true}));report.assetProbeVisualQuality='Realtime shadows disabled during repeated route/variant checks; screenshot phase restores defaults.';}
  const routes=await page.evaluate(async({oldIds,ids})=>{
   const app=window.__SHANGHAI_APP__;
   const {resolveNavigationRoute}=await import('./src/landmark-navigation.js');
   const options={districts:app.districts,landmarks:app.landmarks,bund:{id:'bund',name:'外滩历史建筑群'}};
   return {count:app.landmarks.length,allIds:app.landmarks.map(r=>r.id),routes:[...oldIds,...ids].map(id=>{const r=resolveNavigationRoute('#landmark='+id+'&mode=overview',options);return {id,matched:r.place?.id,error:r.error||null,mode:r.mode};}),districts:app.districts.map(d=>{const r=resolveNavigationRoute('#district='+d.id+'&mode=overview',options);return {id:d.id,matched:r.place?.id,error:r.error||null};})};
  },{oldIds:inventory.existing_city_ids,ids:catalog.models.map(r=>r.id)});
  assert.equal(routes.count,70);assert.equal(new Set(routes.allIds).size,70);
  for(const row of [...routes.routes,...routes.districts]){assert.equal(row.matched,row.id);assert.equal(row.error,null);}
  report.routeRegistry=routes;
  const ready=async(id,variant)=>page.waitForFunction(({id,variant})=>{const s=window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id);return s.visible&&s.status==='loaded'&&s.variant===variant;},{id,variant},{timeout:180000});
  const state=id=>page.evaluate(id=>{const a=window.__SHANGHAI_APP__;return {id,hash:location.hash,title:document.querySelector('#location-title')?.textContent||document.querySelector('#location-name')?.textContent,mode:a.mode,asset:a.scene.getLandmarkAssetState(id),map:{lng:a.scene.map.getCenter().lng,lat:a.scene.map.getCenter().lat,zoom:a.scene.map.getZoom(),pitch:a.scene.map.getPitch(),bearing:a.scene.map.getBearing()},candidate:a.scene.getCandidateIntegrationState()};},id);
  const shot=async(id,label)=>{const file='browser-'+label+'.png';await page.screenshot({path:path.join(output,file)});report.screenshots.push({id,file,sha256:sha(path.join(output,file)),bytes:fs.statSync(path.join(output,file)).size,viewport:[1280,900]});};
  for(const row of scope==='visual'?[]:catalog.models){
   await page.evaluate(id=>{location.hash='#landmark='+id+'&mode=overview';},row.id);
   await page.waitForFunction(row=>new URLSearchParams(location.hash.slice(1)).get('landmark')===row.id&&window.__SHANGHAI_APP__.mode==='overview'&&document.querySelector('#location-name').textContent===row.name,row);
   await page.evaluate(row=>{const a=window.__SHANGHAI_APP__;a.scene.map.stop();a.scene.map.jumpTo({center:[row.lng,row.lat],zoom:22.5,pitch:0,bearing:row.heading});a.scene.loadLandmarks();},row);
   await ready(row.id,'full');
   const full=await state(row.id);assert.equal(full.asset.triangles,row.assets.web.triangles);assert.ok(dist(full.map,row)<.1);
   assert.ok(full.asset.cityIntegration&&full.asset.worldBounds&&full.asset.position,'Actual model transform audit state is required');
   assert.deepEqual(full.asset.anchor,[row.lng,row.lat]);assert.equal(full.asset.heading,row.heading);assert.equal(full.asset.scale,row.scale);
   assert.ok(Math.abs(full.asset.rotation[1]+row.heading*Math.PI/180)<1e-10);
   assert.equal(full.asset.verifiedAsset.sha256,row.assets.web.sha256);assert.equal(full.asset.verifiedAsset.bytes,row.assets.web.bytes);
   const transform=await page.evaluate(row=>{
    const origin=maplibregl.MercatorCoordinate.fromLngLat([121.4737,31.2304],0),point=maplibregl.MercatorCoordinate.fromLngLat([row.lng,row.lat],row.altitude||0);
    const unit=origin.meterInMercatorCoordinateUnits(),factor=point.meterInMercatorCoordinateUnits()/unit*row.scale;
    return {position:[(point.x-origin.x)/unit,point.z/unit,(point.y-origin.y)/unit],minY:point.z/unit+row.bounds_glb.min[1]*factor,maxY:point.z/unit+row.bounds_glb.max[1]*factor};
   },row);
   for(let axis=0;axis<3;axis++)assert.ok(Math.abs(full.asset.position[axis]-transform.position[axis])<1e-6);
   assert.ok(Math.abs(full.asset.worldBounds.min[1]-transform.minY)<.05);assert.ok(Math.abs(full.asset.worldBounds.max[1]-transform.maxY)<.05);
   assert.ok(full.candidate.active.some(r=>r.id===row.id&&r.assetSha256===row.assets.web.sha256));
   await page.evaluate(row=>{const a=window.__SHANGHAI_APP__;a.scene.map.jumpTo({center:[row.lng,row.lat],zoom:18.5,pitch:45,bearing:row.heading});a.scene.loadLandmarks();},row);
   await ready(row.id,'distant');
   const lod=await state(row.id);assert.equal(lod.asset.triangles,row.assets.lod.triangles);assert.equal(lod.asset.verifiedAsset.sha256,row.assets.lod.sha256);
   assert.ok(lod.candidate.active.some(r=>r.id===row.id&&r.assetSha256===row.assets.lod.sha256));
   report.models.push({id:row.id,full,lod,expectedTransform:transform});report.routes.push({id:row.id,hash:full.hash,centerDistanceMetres:dist(full.map,row),mode:full.mode});save();console.log('PASS global full/LOD and route',row.id);
  }
  const pictures=[['chongming-pan-pool-bridge','pan-pool',21.3],['chongming-stele-corridors','stele-courtyard',20.3],['chongming-dacheng-hall','chongming-site',19.8],['huangpu-grand-theatre','grand-partial',20.6],['hongkou-luxun-residence-facade','luxun-facade',21.3],['huangpu-old-wing-on-company','old-wing-on',19.4],['xuhui-soong-ching-ling-residence','soong-residence',20.3]];
  await page.evaluate(()=>window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:true,surfaceNormals:true}));
  for(const [id,label,zoom] of scope==='assets'?[]:pictures){
   const row=catalog.models.find(r=>r.id===id);
   await page.evaluate(async({row,zoom})=>{const a=window.__SHANGHAI_APP__;await a.selectPlace(a.landmarks.find(r=>r.id===row.id),{mode:'overview'});a.scene.map.stop();a.scene.map.jumpTo({center:[row.lng,row.lat],zoom,pitch:55,bearing:row.heading+25});a.scene.loadLandmarks();},{row,zoom});
   await page.waitForFunction(id=>window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id).visible,id,{timeout:120000});
   await sleep(1500);await shot(id,label);
  }
  assert.deepEqual(report.pageErrors,[]);assert.deepEqual(report.consoleErrors,[]);if(scope!=='visual')assert.equal(report.models.length,30);report.completed=true;save();
 }catch(error){report.failure=error.stack;save();throw error;}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
