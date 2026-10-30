/* Resume actual global model/transform checks without repeating accepted assets. MIT. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{createHash}=require('crypto');
const base=process.env.MODEL_BASE_URL||'http://127.0.0.1:8782/',out=process.env.QA_OUTPUT_DIR||__dirname,project=path.resolve(__dirname,'../../..');
const sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function run(page){
 const catPath=path.join(project,'data/candidate-city-integrations.json'),cat=JSON.parse(fs.readFileSync(catPath)),priorPath=path.join(__dirname,'browser-initial-model-checks.json'),prior=JSON.parse(fs.readFileSync(priorPath));
 assert.equal(prior.catalog_sha256,sha(catPath));
 for(const name of ['candidate-city-integrations.js'])assert.equal(prior.runtime[name],sha(path.join(project,'src',name)));
 const priorIds=new Set(prior.models.map(r=>r.id)),rows=cat.models.filter(r=>!priorIds.has(r.id));assert.equal(rows.length,19);
 const report={generatedAt:new Date().toISOString(),completed:false,scope:'19 remaining models: actual final global full and LOD variants, receipts, transform and clipping lifecycle. Earlier 11 full/LOD checks retain their own runtime hashes; no all-30 final-version pixel acceptance is implied.',viewport:[640,480],visualQuality:'Realtime shadows disabled for state/transform matrix; all buildings retained. Default-shadow visual checks are separate.',catalog_sha256:sha(catPath),runtime:{},models:[],errors:[]};
 for(const name of ['app.js','map-scene.js','candidate-city-integrations.js','candidate-city-clipping.js','building-beacons.js','candidate-overview-camera.js'])report.runtime[name]=sha(path.join(project,'src',name));
 const bindingPath=path.join(out,'browser-runtime-bindings.json');if(fs.existsSync(bindingPath)){const binding=JSON.parse(fs.readFileSync(bindingPath));Object.assign(report.runtime,binding.runtime);report.browserRuntimeBinding='browser-runtime-bindings.json';report.laterFaultPathDelta='Any subsequent city-detail-streamer near-index error-branch repair is covered by independent fault injection, not exercised or claimed by this normal browser session.';}
 if(process.env.QA_CONTINUATION_RESUME){const p=process.env.QA_CONTINUATION_RESUME,last=JSON.parse(fs.readFileSync(p));assert.equal(last.catalog_sha256,report.catalog_sha256);report.models=last.models;report.previousAttempt={file:path.basename(p),sha256:sha(p),completedModels:last.models.length,note:'At 640x480, zoom18.5 did not force the tall Broadway model into LOD; remaining urban LOD probes use zoom17.5. Prior nine records retain their actual verified full/LOD evidence.'};}
 const save=()=>fs.writeFileSync(path.join(out,'browser-models-continuation.json'),JSON.stringify(report,null,2)+'\n');
 const ownsPage=!page;const browser=ownsPage?await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']}):null;
 try{
  if(ownsPage)page=await browser.newPage({viewport:{width:640,height:480}});else await page.setViewportSize({width:640,height:480});page.on('pageerror',e=>report.errors.push(e.message));
  if(ownsPage)await page.goto(base+'index.html#landmark='+rows[0].id+'&mode=overview',{waitUntil:'domcontentloaded',timeout:90000});
  await page.waitForFunction(()=>window.__SHANGHAI_APP__,null,{timeout:240000});
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:false,surfaceNormals:true});});
  for(const row of rows.filter(r=>!report.models.some(m=>m.id===r.id))){
   await page.evaluate(id=>{location.hash='#landmark='+id+'&mode=overview';},row.id);
   await page.waitForFunction(row=>document.querySelector('#location-name').textContent===row.name&&window.__SHANGHAI_APP__.scene.getLandmarkAssetState(row.id).visible,row,{timeout:180000,polling:500});
   const variants=[];
   for(const [variant,zoom,pitch] of [['full',22.5,0],['distant',17.5,45]]){
   await page.evaluate(({row,zoom,pitch})=>{const a=window.__SHANGHAI_APP__;a.scene.map.stop();a.scene.map.jumpTo({center:[row.lng,row.lat],zoom,pitch,bearing:row.heading,padding:{top:0,bottom:0,left:0,right:0},elevation:0});a.scene.loadLandmarks();},{row,zoom,pitch});
   await page.waitForFunction(({id,variant})=>{const s=window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id);return s.visible&&s.status==='loaded'&&s.variant===variant;},{id:row.id,variant},{timeout:180000,polling:500});
   const result=await page.evaluate(row=>{
    const a=window.__SHANGHAI_APP__,s=a.scene.getLandmarkAssetState(row.id),candidate=a.scene.getCandidateIntegrationState();
    const origin=maplibregl.MercatorCoordinate.fromLngLat([121.4737,31.2304],0),p=maplibregl.MercatorCoordinate.fromLngLat([row.lng,row.lat],row.altitude||0),unit=origin.meterInMercatorCoordinateUnits(),factor=p.meterInMercatorCoordinateUnits()/unit*row.scale;
    return {id:row.id,map:{center:a.scene.map.getCenter(),zoom:a.scene.map.getZoom(),pitch:a.scene.map.getPitch(),elevation:a.scene.map.transform.elevation,padding:a.scene.map.getPadding(),viewport:[innerWidth,innerHeight]},hash:location.hash,mode:a.mode,asset:s,active:candidate.active.find(r=>r.id===row.id),sourceClipIds:candidate.clips.map(c=>c.id),selectedClip:candidate.clips.find(c=>c.id===(row.site_replacement?.id||row.id))||null,shader:candidate.shader,expected:{position:[(p.x-origin.x)/unit,p.z/unit,(p.y-origin.y)/unit],minY:p.z/unit+row.bounds_glb.min[1]*factor,maxY:p.z/unit+row.bounds_glb.max[1]*factor},renderer:a.scene.getStreamingState().renderer};
   },row);
   const asset=row.assets[result.asset.variant==='full'?'web':'lod'];
   assert.equal(result.mode,'overview');assert.equal(new URLSearchParams(result.hash.slice(1)).get('landmark'),row.id);
   assert.equal(result.asset.status,'loaded');assert.ok(result.asset.visible&&result.asset.cityIntegration);assert.equal(result.asset.triangles,asset.triangles);
   assert.equal(result.asset.verifiedAsset.sha256,asset.sha256);assert.equal(result.asset.verifiedAsset.bytes,asset.bytes);assert.equal(result.active.assetSha256,asset.sha256);
   assert.deepEqual(result.asset.anchor,[row.lng,row.lat]);assert.equal(result.asset.heading,row.heading);assert.equal(result.asset.scale,row.scale);
   assert.ok(Math.abs(result.asset.rotation[1]+row.heading*Math.PI/180)<1e-10);
   for(let i=0;i<3;i++)assert.ok(Math.abs(result.asset.position[i]-result.expected.position[i])<1e-6);
   if(variant==='full'){assert.ok(Math.abs(result.asset.worldBounds.min[1]-result.expected.minY)<.1);assert.ok(Math.abs(result.asset.worldBounds.max[1]-result.expected.maxY)<.1);}
   const expectedClip=row.site_replacement||((row.replacement_geometry)?{geometry:row.replacement_geometry,source_feature_ids:row.source_feature_ids}:null);if(expectedClip){assert.ok(result.selectedClip);assert.deepEqual(result.selectedClip.geometry,expectedClip.geometry);assert.deepEqual(result.selectedClip.source_feature_ids,expectedClip.source_feature_ids);}
   variants.push(result);
   }
   report.models.push({id:row.id,full:variants[0],lod:variants[1]});save();console.log('PASS remaining global full/LOD',row.id);
  }
  report.routeRegistry=await page.evaluate(async()=>{const a=window.__SHANGHAI_APP__,{resolveNavigationRoute}=await import('./src/landmark-navigation.js'),options={districts:a.districts,landmarks:a.landmarks,bund:{id:'bund',name:'外滩历史建筑群'}};return {count:a.landmarks.length,allIds:a.landmarks.map(r=>r.id),routes:a.landmarks.map(r=>{const t=resolveNavigationRoute('#landmark='+r.id+'&mode=overview',options);return {id:r.id,matched:t.place?.id,error:t.error||null,mode:t.mode};}),districts:a.districts.map(r=>{const t=resolveNavigationRoute('#district='+r.id+'&mode=overview',options);return {id:r.id,matched:t.place?.id,error:t.error||null};})};});
  assert.equal(report.routeRegistry.count,70);for(const r of [...report.routeRegistry.routes,...report.routeRegistry.districts]){assert.equal(r.matched,r.id);assert.equal(r.error,null);}
  assert.equal(report.models.length,19);assert.deepEqual(report.errors,[]);report.completed=true;save();
  report.priorRuntimeDifference={candidateClippingChanged:prior.runtime['candidate-city-clipping.js']!==report.runtime['candidate-city-clipping.js'],note:'Prior full/LOD loading and geographic transforms remain bound to the earlier runtime. Final shared-site clipping pixel acceptance is documented in browser-global-views.json, not inferred from the prior active state.'};save();
  const models=[...prior.models.map(r=>({...r,phase:'initial-11-full-and-lod'})),...report.models.map(r=>({...r,phase:'final-19-full-and-lod'}))];assert.equal(models.length,30);assert.equal(new Set(models.map(r=>r.id)).size,30);
  fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify({completed:true,completed_model_count:30,scope:'All 30 new records have actual global scene loading, verified asset receipts and geographic transforms. Final-runtime clipping state is checked for the remaining 19; the shared Chongming site requires the separate final pixel review. Eleven had full/LOD checks in the first bound runtime; nineteen had final-runtime full/LOD checks. The separate 60-asset browser decode covers every full/LOD asset. Final default-camera pixels, beacons and existing-entry regression are separate reports.',catalog_sha256:sha(catPath),sessions:[{file:path.basename(priorPath),sha256:sha(priorPath),models:11,runtime:prior.runtime},{file:'browser-models-continuation.json',sha256:sha(path.join(out,'browser-models-continuation.json')),models:19,runtime:report.runtime}],models},null,2)+'\n');
 }catch(e){report.failure=e.stack;save();throw e;}finally{if(ownsPage)await browser.close()}
}
module.exports=run;
if(require.main===module)run().catch(e=>{console.error(e);process.exit(1)});
