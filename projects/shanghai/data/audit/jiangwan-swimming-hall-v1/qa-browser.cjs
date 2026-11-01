/* Jiangwan Swimming Hall incremental QA. One browser/page; no old-model matrix. MIT. */
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const {createHash}=require('crypto');
const {waitForContinuation}=require('./continuation-host.cjs');
const PROJECT=path.resolve(process.env.SHANGHAI_PROJECT_ROOT||path.resolve(__dirname,'../../..')),REPO=path.resolve(PROJECT,'../..');
const OUT=process.env.QA_OUTPUT_DIR||__dirname,BASE=process.env.MODEL_BASE_URL||'http://127.0.0.1:8782/';
const ID='yangpu-jiangwan-swimming-hall',TOUCH_FROM='yangpu-jiangwan-gymnasium';
const COUNT=80;
const CONFIG_PATH=process.env.QA_CONTRACT_PATH||path.join(__dirname,'qa-contract.json');
const CONFIG=JSON.parse(fs.readFileSync(CONFIG_PATH,'utf8'));
const PRIVATE_CONFIGURATION_READY=CONFIG.frozen===true;
const EXPECTED_CLIP_TRIANGLES=CONFIG.expected_clip_triangles;
const EXPECTED_SOURCE=CONFIG.main_source_id;
const CLIP_CAPACITY=CONFIG.clip_capacity;
const ZERO_PADDING={top:0,right:0,bottom:0,left:0};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=rel=>JSON.parse(fs.readFileSync(path.join(PROJECT,rel),'utf8'));
const sameIds=(a,b)=>assert.deepEqual([...a].sort(),[...b].sort());
const assertClipCapacity=shader=>{
 assert.equal(shader.triangleLimit,CLIP_CAPACITY);assert.ok(Number.isInteger(shader.triangles)&&shader.triangles>=0&&shader.triangles<=CLIP_CAPACITY);
 for(const [key,value] of Object.entries({width:4,height:CLIP_CAPACITY,bytes:CLIP_CAPACITY*64,type:'FloatType',format:'RGBAFormat',minFilter:'NearestFilter',magFilter:'NearestFilter',generateMipmaps:false}))assert.equal(shader.clippingTexture[key],value,`clippingTexture.${key}`);
};


function readDirectory(file){
 const text=fs.readFileSync(file,'utf8'),section=text.split(/^## 按区查看主要建筑\s*$/m)[1]?.split(/^## /m)[0];
 assert.ok(section,`missing district directory: ${file}`);
 const groups=[...section.matchAll(/^### ([^\n]+?)（(\d+)处）\s*$/gm)];
 const rows=[...section.matchAll(/^\|[^\n]*\[查看网页\]\((https:\/\/[^\s)]+#landmark=([^&\s)]+)&mode=(walk|overview))\)[^\n]*$/gm)].map(m=>({id:m[2],url:m[1],mode:m[3]}));
 assert.equal(groups.length,16);assert.equal(rows.length,COUNT);assert.equal(new Set(rows.map(r=>r.id)).size,COUNT);
 assert.equal(groups.reduce((n,g)=>n+Number(g[2]),0),COUNT);
 assert.equal(rows.find(r=>r.id===ID)?.mode,'overview');
 assert.equal(groups.find(g=>g[1]==='杨浦区')?.[2],'5');
 assert.equal(rows.filter(r=>r.mode==='walk').length,40);
 for(const row of rows)assert.equal(new URL(row.url).pathname,'/ecojust/e-resource/master/projects/shanghai/index.html');
 for(let i=0;i<groups.length;i++){
  const part=section.slice(groups[i].index,groups[i+1]?.index??section.length);
  assert.equal((part.match(/\[查看网页\]\(https:[^\n]*?#landmark=/g)||[]).length,Number(groups[i][2]),groups[i][1]);
 }
 return {file:path.relative(REPO,file),sha256:sha(text),districts:groups.map(g=>({name:g[1],count:Number(g[2])})),rows};
}

async function run(){
 assert.ok(PRIVATE_CONFIGURATION_READY||process.argv.includes('--preflight'),'Private preparation only; wait for public freeze and completed QA adaptation.');
 // Explicit opt-in prevents preparation or syntax checks from starting WebGL.
 assert.ok(process.argv.includes('--run')||process.argv.includes('--preflight'),'Preparation only. Use --preflight for frozen metadata checks; --run starts the one browser after full freeze.');
 fs.mkdirSync(OUT,{recursive:true});
 const catalogPath='data/candidate-city-integrations.json',catalog=read(catalogPath),row=catalog.models.find(r=>r.id===ID),touchFrom=catalog.models.find(r=>r.id===TOUCH_FROM);
 assert.equal(catalog.models.length,40);assert.ok(row&&touchFrom);assert.equal(row.navigation.listed,false);
 const footprint=read('data/audit/jiangwan-swimming-hall-v1/footprint-review.json');
 const manifest=read(`assets/models/candidates/${ID}/manifest.json`);
 const viewer=read('data/model-viewers.json').find(r=>r.id===ID);assert.ok(viewer,'New model must be in auxiliary viewer directory');assert.equal(viewer.page,'jiangwan-swimming-hall.html');assert.equal(viewer.manifest,`assets/models/candidates/${ID}/manifest.json`);
 assert.equal(CONFIG.model_id,ID);assert.equal(CONFIG.baseline_commit,'225af1b75c235177ca23c775b9a9d3483eb032ba');
 assert.equal(CONFIG.footprint_sha256,sha(fs.readFileSync(path.join(PROJECT,'data/audit/jiangwan-swimming-hall-v1/footprint-review.json'))));
 assert.equal(manifest.id,ID);sameIds(row.source_feature_ids.building,CONFIG.source_feature_ids.building);
 assert.ok(Number.isSafeInteger(row.owner.feature_local_id));assert.deepEqual(row.owner,CONFIG.owner);
 assert.ok(CONFIG.all_source_ids.every(id=>!touchFrom.source_feature_ids.building.includes(id)));assert.equal(Boolean(row.site_replacement),CONFIG.has_site_replacement);if(CONFIG.has_site_replacement){assert.deepEqual(row.site_replacement.source_feature_ids,CONFIG.site_source_feature_ids);assert.deepEqual(row.site_replacement.owner,CONFIG.site_owner);assert.equal(row.site_replacement.id,CONFIG.site_clip_id);}
 const contract=footprint.proposed_placement_contract;
 assert.ok(contract.replacement_geometry?.type,'Final replacement geometry must be frozen before QA');
 for(const key of ['replacement_geometry','site_replacement','source_feature_ids','collision_geometry','bounds_glb'])assert.deepEqual(row[key],contract[key],key);
 const placementPath='data/global-models/additional-placement.json',placementRecord=read(placementPath).records.find(r=>r.id===ID);assert.deepEqual(placementRecord,contract);
 assert.equal(contract.expected_replacement_triangle_count,EXPECTED_CLIP_TRIANGLES);for(const [role,key] of [['raw','raw'],['web','full'],['lod','lod']])assert.equal(contract.model_geometry_sha256[role],manifest.assets[key].sha256);assert.equal(contract.expected_global_clip_capacity,CLIP_CAPACITY);
 for(const key of ['lng','lat','heading','scale','overviewBearing','overviewPitch'])assert.equal(row[key],contract[key],key);
 assert.equal(row.partial_model,CONFIG.partial_model);assert.ok(Number.isInteger(EXPECTED_CLIP_TRIANGLES)&&EXPECTED_CLIP_TRIANGLES>0);
 const neighbors=CONFIG.context_sources,contextIds=neighbors.map(n=>n.source_id);
 assert.ok(neighbors.length>0);assert.equal(new Set(contextIds).size,neighbors.length);
 for(const n of neighbors){assert.ok(n.source_id&&!CONFIG.all_source_ids.includes(n.source_id));assert.ok(n.roof_probe.wgs84.every(Number.isFinite)&&Number.isFinite(n.roof_probe.height_m));}
 assert.ok(CONFIG.ground_probes.some(p=>p.expected===null),'Require open-ground negatives');assert.ok(CONFIG.ground_probes.some(p=>p.expected==='building'),'Require actual solid positive controls');
 assert.ok(CONFIG.near_groups.length>0);assert.equal(contract.expected_global_clip_triangle_count,CONFIG.expected_global_clip_triangles);assert.equal(new Set(CONFIG.visual_views.map(v=>v.key)).size,CONFIG.visual_views.length);
 assert.ok(CONFIG.visual_views.some(v=>v.key==='side'));assert.ok(CONFIG.visual_views.some(v=>v.key==='entry'));
 for(const view of CONFIG.visual_views){assert.ok(['full','distant'].includes(view.expected_variant));assert.ok(view.camera.center.every(Number.isFinite));assert.ok(view.camera.zoom>=17.3);assert.ok(view.probe.wgs84.every(Number.isFinite)&&Number.isFinite(view.probe.height_m));}
 for(const g of CONFIG.near_groups){assert.ok(g.group_id&&g.macro_id&&g.feature_local_ids.length&&g.clip_feature_local_ids.length);assert.ok(g.near_path&&/^[0-9a-f]{64}$/.test(g.sha256));}
 const report={generatedAt:new Date().toISOString(),completed:false,browserClosed:false,modelId:ID,
  scope:'Only Jiangwan Swimming Hall, the independent source/near-group ownership and retained neighboring buildings, existing wide shallow roof with raised central clerestory, historic brick perimeter and bounded entrance recesses, full/LOD, the 80-entry directory and 320px beacon capacity increment. One browser and one page, with sequential auxiliary/directory/main-map documents. No replay of the existing 39-model asset matrix.',
  captureStabilityPolicy:'After viewport changes, wait for DOM/canvas/MapLibre dimensions and UI geometry to agree across two rendered frames before fitting the camera. Wait for map and beacon readiness, finished city far/near loading and queues, all pending feature-state writes, actual owner macro visibility, completed vector corrections, then the same stable source/mesh fingerprint across two rendered frames. Any failed attempt must retain its failure record and cannot count as an accepted screenshot.',
  catalog:{file:catalogPath,sha256:sha(fs.readFileSync(path.join(PROJECT,catalogPath))),models:catalog.models.length},
  manifest:{file:`assets/models/candidates/${ID}/manifest.json`,sha256:sha(fs.readFileSync(path.join(PROJECT,`assets/models/candidates/${ID}/manifest.json`)))},
  footprint:{file:'data/audit/jiangwan-swimming-hall-v1/footprint-review.json',sha256:sha(fs.readFileSync(path.join(PROJECT,'data/audit/jiangwan-swimming-hall-v1/footprint-review.json')))},
  qaScript:{file:path.relative(PROJECT,__filename),sha256:sha(fs.readFileSync(__filename))},
  sourceBindings:{},citySourceHTTP:[],http:[],auxiliary:{},directory:{},global:{},beacons:{},captures:[],errors:[],warnings:[]};
 report.expectedSourceBindings=[...new Set(['src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/jiangwan-swimming-hall.js',...['index.html','landmarks.html','jiangwan-swimming-hall.html'].flatMap(file=>[...fs.readFileSync(path.join(PROJECT,file),'utf8').matchAll(/(?:src|href)=["'](src\/[^"']+\.(?:js|css))["']/g)].map(m=>m[1]))])].map(file=>({file,sha256:sha(fs.readFileSync(path.join(PROJECT,file)))}));
 report.referenceDocuments=CONFIG.reference_documents.map(file=>({file,sha256:sha(fs.readFileSync(path.join(PROJECT,file)))}));
 report.qaContract={file:path.relative(PROJECT,CONFIG_PATH),sha256:sha(fs.readFileSync(CONFIG_PATH))};
 report.continuationHelper={file:path.relative(PROJECT,path.join(__dirname,'continuation-host.cjs')),sha256:sha(fs.readFileSync(path.join(__dirname,'continuation-host.cjs')))};
 report.placementBinding={file:placementPath,sha256:sha(fs.readFileSync(path.join(PROJECT,placementPath))),method:'Full additional-placement record equals independent contract; compact runtime catalog geometry/bounds fields compare separately. Source limit and retained geometry belong to the authored placement contract; runtime vector clipping computes original-source minus reviewed replacement geometry.'};
 report.documentBindings=['index.html','landmarks.html','jiangwan-swimming-hall.html'].map(file=>({file,sha256:sha(fs.readFileSync(path.join(PROJECT,file)))}));
 report.viewerRegistry={file:'data/model-viewers.json',sha256:sha(fs.readFileSync(path.join(PROJECT,'data/model-viewers.json'))),entry:viewer};
 const staticDirectories=[readDirectory(path.join(REPO,'README.md')),readDirectory(path.join(PROJECT,'README.md'))];
 sameIds(staticDirectories[0].rows.map(r=>r.id),staticDirectories[1].rows.map(r=>r.id));
 report.preflight={passed:true,directories:staticDirectories.map(d=>({file:d.file,sha256:d.sha256,count:d.rows.length}))};
 if(process.argv.includes('--preflight')){console.log(JSON.stringify({preflight:true,modelId:ID,count:COUNT,catalog:report.catalog.sha256,manifest:report.manifest.sha256,footprint:report.footprint.sha256,script:report.qaScript.sha256}));return;}
 const save=()=>fs.writeFileSync(path.join(OUT,'browser.json'),JSON.stringify(report,null,2)+'\n');
 const verifyFrozenInputs=async()=>{
  for(const b of [report.catalog,report.manifest,report.footprint,report.qaScript,report.viewerRegistry,report.placementBinding,report.continuationHelper,report.qaContract,...report.referenceDocuments,...report.expectedSourceBindings,...report.documentBindings])assert.equal(sha(fs.readFileSync(path.join(PROJECT,b.file))),b.sha256,'Frozen input changed: '+b.file);
  for(const asset of Object.values(manifest.assets))assert.equal(sha(fs.readFileSync(path.join(PROJECT,`assets/models/candidates/${ID}/`,asset.file))),asset.sha256,'Frozen asset changed: '+asset.file);
  for(const b of staticDirectories)assert.equal(sha(fs.readFileSync(path.join(REPO,b.file))),b.sha256,b.file);
  for(const c of report.captures)assert.equal(sha(fs.readFileSync(path.join(OUT,c.file))),c.sha256,c.file);
  for(const r of report.visualPixelReviews||[])assert.equal(sha(fs.readFileSync(path.join(OUT,r.control.file))),r.control.sha256,r.control.file);
  for(const r of report.continuations||[])if(r.type==='continuation-started'&&r.module&&r.moduleSha256)assert.equal(sha(fs.readFileSync(r.module)),r.moduleSha256,r.module);
 };
 const finalizeChecks=async()=>{
  await drainResponses();await verifyFrozenInputs();assert.deepEqual(report.errors,[]);assert.deepEqual(report.warnings,[]);assert.deepEqual(report.http,[]);assert.equal(report.catalog.http?.sha256,report.catalog.sha256);assert.equal(report.originalSourceVerification?.length,CONFIG.source_bindings.length);
  assert.equal(report.auxiliary.downloads?.length,4);sameIds(report.auxiliary.downloads.map(r=>r.role),['raw','full','lod','native']);for(const download of report.auxiliary.downloads){assert.equal(download.status,200);assert.equal(download.sha256,manifest.assets[download.role].sha256);assert.equal(download.bytes,manifest.assets[download.role].bytes);}
  assert.equal(report.directory.cards?.length,COUNT);sameIds(report.global.registry?.ids,cardsFromReport());
  assert.equal(report.global.registry.routes.length,COUNT);for(const r of report.global.registry.routes){assert.equal(r.id,r.matched);assert.equal(r.error,null);}
  assert.ok(report.global.full&&report.global.lod&&report.global.neighborSeparation&&report.global.webglAfterModelChecks,'The new model full/LOD, neighbor and GPU checks must complete');continuationContext.helpers.assertAsset(report.global.full,'full');continuationContext.helpers.assertAsset(report.global.lod,'distant');assert.equal(report.global.webglAfterModelChecks.glError,0);assert.equal(report.global.webglAfterModelChecks.contextLost,false);assertClipCapacity(report.global.webglAfterModelChecks.clipping);
  for(const n of report.global.neighborSeparation.excludedContextSources)if(!n.legitimateExistingReplacement)assert.notEqual(n.state.candidateModel,true,n.id);

  for(const label of ['auxiliary-desktop-full','auxiliary-desktop-lod','auxiliary-mobile-full','global-default-desktop','global-default-mobile','beacons-320-city-80'])assert.ok(report.captures.some(c=>c.label===label),'Required capture missing: '+label);
  for(const view of CONFIG.visual_views){
   const acceptance=report.global.visualAcceptance?.[view.key];assert.ok(acceptance?.accepted,'Required actual pixel review: '+view.key);assert.equal(acceptance.key,view.key);
   const capture=report.captures.find(c=>c.file===acceptance.capture&&c.sha256===acceptance.captureSha256);assert.ok(capture);assert.ok(capture.label===view.label||capture.label.startsWith(view.label+'-adjusted-'));
   const decision=acceptance.decision;assert.equal(decision.accepted,true);assert.equal(decision.viewKey,view.key);assert.equal(decision.captureFile,capture.file);assert.equal(decision.captureSha256,capture.sha256);assert.equal(decision.scriptSha256,capture.captureScript.sha256);assert.equal(decision.captureControlSha256,capture.captureScript.controlSha256||null);assert.equal(decision.runGeneratedAt,report.generatedAt);
   assert.ok(report.visualPixelReviews.some(r=>r.key===view.key&&r.control.sha256===acceptance.control.sha256));assert.deepEqual(JSON.parse(fs.readFileSync(path.join(OUT,acceptance.control.file),'utf8')),decision);
   assert.deepEqual(report.global.visualViews[view.key],capture.state);continuationContext.helpers.validateVisualState(view,capture.state);
  }
  assert.equal(report.global.ownerGroupIsolation?.groups.length,CONFIG.near_groups.length);
  for(const group of report.global.ownerGroupIsolation.groups){assert.equal(group.nearHTTP.status,200);assert.equal(group.nearHTTP.sha256,group.required.sha256);assert.ok(group.observed.length>0);}
  assert.equal(report.global.groundCollision?.length,CONFIG.ground_probes.length);for(let i=0;i<CONFIG.ground_probes.length;i++){const p=report.global.groundCollision[i],required=CONFIG.ground_probes[i];assert.deepEqual({...p,actual:undefined},{...required,actual:undefined});assert.equal(p.actual,required.expected,p.name);}
  assert.equal(report.beacons.state?.count,COUNT);assert.equal(report.beacons.state?.overlapFallbackCount,0);assert.ok(report.beacons.touch?.changedDestination&&report.beacons.touch?.targetAssetVisibleAfterTouch);assert.equal(report.beacons.touch.id,ID);assert.ok(report.beacons.postTouchLayout);assert.ok(report.cardTitleCapacity.count===COUNT&&report.cardTitleCapacity.overlapFallbackCount===0);
  if(report.beacons.worstTitleViewport)assert.ok(report.captures.some(c=>c.label.startsWith('beacons-320x')&&c.state.viewport[1]===report.beacons.worstTitleViewport.scene.viewport[1]));
  if(report.beacons.postTouchCardComparison?.requiresAdditionalCityCapture){assert.ok(report.beacons.postTouchCity);continuationContext.helpers.assertDenseBeacons(report.beacons.postTouchCity);assert.ok(report.captures.some(c=>c.label==='beacons-320-swimming-hall-city-80'));}
  sameIds(report.cardTitleCapacity.rows.map(r=>r.id),cardsFromReport());sameIds(report.cardTitleCapacity.positions.map(r=>r.id),cardsFromReport());for(const hit of report.cardTitleCapacity.hits)assert.equal(hit.id,hit.hit);
  for(const b of report.expectedSourceBindings)assert.equal(report.sourceBindings[b.file.slice(4)]?.sha256,b.sha256,b.file);
  report.completed=true;report.visualAcceptance='Automated checks and required side/entry pixel decisions are complete; all PNGs still require separate QA/root review.';save();
 };
 const cardsFromReport=()=>report.directory.cards.map(c=>c.id);

 const existingBrowser=await fetch('http://127.0.0.1:9223/json/version',{signal:AbortSignal.timeout(1000)}).then(r=>r.ok).catch(()=>false);
 assert.equal(existingBrowser,false,'A QA browser is already active. Keep one controller; do not launch a second instance.');
 report.serverPreflight=[];
 for(const binding of [report.catalog,report.manifest,report.documentBindings.find(b=>b.file==='jiangwan-swimming-hall.html')]){const response=await fetch(new URL(binding.file,BASE),{signal:AbortSignal.timeout(10000)});assert.equal(response.status,200);const bytes=Buffer.from(await response.arrayBuffer());assert.equal(sha(bytes),binding.sha256);report.serverPreflight.push({file:binding.file,status:response.status,bytes:bytes.length,sha256:sha(bytes)});}
 report.originalSourceVerification=[];
 for(const binding of CONFIG.source_bindings){const file=binding.path||binding.repository_path.replace(/^projects\/shanghai\//,'');const response=await fetch(new URL(file,BASE),{signal:AbortSignal.timeout(30000)});assert.equal(response.status,200);const bytes=Buffer.from(await response.arrayBuffer());assert.equal(bytes.length,binding.bytes);assert.equal(sha(bytes),binding.sha256);report.originalSourceVerification.push({file,status:response.status,bytes:bytes.length,sha256:sha(bytes),origin:response.headers.get('x-audit-origin'),verification:'Explicit HTTP request before browser launch; actual in-page near-source HTTP receipts are checked separately.'});}
 console.log('HTTP_HEALTHY',JSON.stringify({documents:report.serverPreflight,originalSources:report.originalSourceVerification}));
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9223']});
 const page=await browser.newPage({viewport:{width:1200,height:900},hasTouch:true});
 report.browserVersion=browser.version();report.playwrightVersion=require('playwright/package.json').version;report.nodeVersion=process.version;let phase='auxiliary';
 let activeCaptureProvenance=report.qaScript;
 const continuationContext={page,browser,report,save,PROJECT,REPO,OUT,BASE,ID,TOUCH_FROM,COUNT,EXPECTED_CLIP_TRIANGLES,EXPECTED_SOURCE,CONFIG,CLIP_CAPACITY,ZERO_PADDING,sha,sameIds,assertClipCapacity,fs,path,assert,catalog,row,footprint,manifest,neighbors,contextIds,staticDirectories,verifyFrozenInputs,finalizeChecks,helpers:{},setPhase:value=>{phase=value;},setCaptureProvenance:binding=>{activeCaptureProvenance={file:path.relative(PROJECT,binding.module),sha256:binding.moduleSha256,controlSha256:binding.controlSha256};},validateContinuationResult:()=>finalizeChecks()};
 // Response listeners retain URL/status/header observations only. Actual response
 // bodies are fetched synchronously on the stable current page before navigation.
 const observed=new Map(),verified=new Set();let verifying=false;
 report.httpObservations=[];report.synchronousHTTP=[];
 const trackedPath=u=>u.origin===new URL(BASE).origin&&(u.pathname.startsWith('/src/')||u.pathname.startsWith('/assets/city-detail/macros/')||u.pathname==='/'+catalogPath||report.documentBindings.some(b=>u.pathname==='/'+b.file));
 page.on('pageerror',e=>{report.errors.push({phase,url:page.url(),message:e.message});save();});
 page.on('console',m=>{if(m.type()==='error')report.errors.push({phase,url:page.url(),message:m.text()});if(m.type()==='warning')report.warnings.push({phase,url:page.url(),message:m.text()});});
 page.on('response',r=>{
  const u=new URL(r.url()),observation={phase,url:r.url(),path:u.pathname.slice(1),status:r.status(),headers:r.headers(),at:new Date().toISOString(),purpose:verifying?'explicit-stable-page-byte-verification':'document-or-scene-request'};
  if(r.status()>=400)report.http.push(observation);
  if(trackedPath(u)){report.httpObservations.push(observation);if(!verifying&&!observed.has(observation.path))observed.set(observation.path,observation);}
 });
 const drainResponses=async()=>{
  // At most one finite snapshot per drain: verification fetches do not enqueue
  // themselves, and all page navigation waits for this function to finish.
  for(const [file,original] of [...observed]){
   if(verified.has(file))continue;
   verifying=true;
   let result;
   try{
    result=await page.evaluate(async({url})=>{
     const response=await fetch(url,{cache:'no-store'}),body=new Uint8Array(await response.arrayBuffer());
     const hex=a=>Array.from(new Uint8Array(a),b=>b.toString(16).padStart(2,'0')).join('');
     const header=new TextEncoder().encode('blob '+body.length+'\0'),gitBytes=new Uint8Array(header.length+body.length);gitBytes.set(header);gitBytes.set(body,header.length);
     return {url:response.url,status:response.status,bytes:body.length,sha256:hex(await crypto.subtle.digest('SHA-256',body)),gitBlob:hex(await crypto.subtle.digest('SHA-1',gitBytes)),origin:response.headers.get('x-audit-origin'),serverSHA256:response.headers.get('x-audit-sha256')};
    },{url:new URL(file,BASE).href});
    assert.equal(result.status,200,'Stable-page fetch failed: '+file);if(result.serverSHA256)assert.equal(result.sha256,result.serverSHA256,file);
    const receipt={...result,path:file,phase,originalRequest:original,verification:'Explicit synchronous in-page fetch at a stable page; body length, SHA256 and Git blob are calculated before any subsequent navigation. Original scene request is separately URL/status observed; no claim to recover its asynchronous Playwright response body.'};
    const documentBinding=report.documentBindings.find(b=>b.file===file);if(documentBinding){assert.equal(receipt.sha256,documentBinding.sha256,file);documentBinding.http=receipt;}
    if(file===catalogPath){assert.equal(receipt.sha256,report.catalog.sha256);report.catalog.http=receipt;}
    if(file.startsWith('src/')){const bytes=fs.readFileSync(path.join(PROJECT,file));assert.equal(receipt.sha256,sha(bytes),file);report.sourceBindings[file.slice(4)]=receipt;}
    if(file.startsWith('assets/city-detail/macros/')){
     const {execFileSync}=require('node:child_process');
     const tree=execFileSync('git',['--no-lazy-fetch','ls-tree',CONFIG.baseline_commit,'--','projects/shanghai/'+file],{cwd:REPO,encoding:'utf8'}).trim();assert.ok(tree,'City source must exist in frozen baseline: '+file);const blob=tree.split(/\s+/)[2];assert.equal(receipt.gitBlob,blob,'Frozen city Git blob: '+file);receipt.baselineCommit=CONFIG.baseline_commit;receipt.expectedGitBlob=blob;
     const required=CONFIG.source_bindings.find(b=>(b.path||b.repository_path.replace(/^projects\/shanghai\//,''))===file);if(required){assert.equal(receipt.bytes,required.bytes);assert.equal(receipt.sha256,required.sha256);}
     report.citySourceHTTP.push(receipt);
    }
    report.synchronousHTTP.push(receipt);verified.add(file);
   }catch(error){report.responseCheckFailures??=[];report.responseCheckFailures.push({at:new Date().toISOString(),phase,path:file,url:new URL(file,BASE).href,message:error.stack||String(error)});save();throw error;}
   finally{verifying=false;}
  }
  assert.deepEqual(report.responseCheckFailures||[],[],'Stable-page HTTP verification failed');save();
 };continuationContext.drainResponses=drainResponses;
 const layoutReady=async(width,height,main)=>{
  await page.evaluate(({width,height,main})=>{
   window.__qaLayoutCancel?.();const m=main?window.__SHANGHAI_APP__.scene.map:null;
   const state=()=>{const canvas=m?m.getCanvas():document.querySelector('canvas'),r=canvas.getBoundingClientRect(),rect=q=>document.querySelector(q)?.getBoundingClientRect().toJSON();return {inner:[innerWidth,innerHeight],canvas:[canvas.clientWidth,canvas.clientHeight],buffer:[canvas.width,canvas.height],rect:[r.width,r.height],transform:m?[m.transform.width,m.transform.height]:null,ui:['#explore-panel','#location-card','.map-tools','#building-beacon-legend'].map(rect)};};
   const dimensions=s=>s.inner[0]===width&&s.inner[1]===height&&(main?s.canvas[0]===width&&s.canvas[1]===height&&s.transform[0]===width&&s.transform[1]===height:s.canvas[0]===s.rect[0]&&s.canvas[1]===s.rect[1]&&s.buffer[0]===Math.round(s.rect[0]*devicePixelRatio)&&s.buffer[1]===Math.round(s.rect[1]*devicePixelRatio));
   const fingerprint=s=>JSON.stringify([s.inner,s.canvas,s.buffer,s.transform,...s.ui.map(r=>r&&[r.left,r.top,r.right,r.bottom].map(v=>Math.round(v*100)/100))]);let previous=null,raf=null;
   window.__qaLayoutProgress={ready:false,frames:0,consecutiveStableComparisons:0,frameKind:main?'actual MapLibre render':'document animation frame after auxiliary render',started:performance.now(),current:state(),renderTimes:[]};
   const listener=()=>{const p=window.__qaLayoutProgress,nextState=state(),next=fingerprint(nextState);p.frames++;p.consecutiveStableComparisons=dimensions(nextState)&&next===previous?p.consecutiveStableComparisons+1:0;previous=next;p.current=nextState;p.renderTimes.push(performance.now());p.ready=p.consecutiveStableComparisons>=2;if(p.ready){if(m)m.off('render',listener);}else if(!m)raf=requestAnimationFrame(listener);};
   window.__qaLayoutCancel=()=>{if(m)m.off('render',listener);if(raf)cancelAnimationFrame(raf);};if(m){m.on('render',listener);m.triggerRepaint();}else raf=requestAnimationFrame(listener);
  },{width,height,main});
  const deadline=Date.now()+900000;let loggedAt=Date.now(),last;
  while(Date.now()<deadline){last=await page.evaluate(main=>{const p=window.__qaLayoutProgress;if(!p.ready&&main)window.__SHANGHAI_APP__.scene.map.triggerRepaint();return p;},main);if(last.ready){assert.ok(last.frames>=3&&last.consecutiveStableComparisons>=2);return {...last.current,actualFrames:last.frames,frameKind:last.frameKind,stableComparisons:last.consecutiveStableComparisons,renderTimes:last.renderTimes};}if(Date.now()-loggedAt>=30000){loggedAt=Date.now();console.log('WAIT_LAYOUT',JSON.stringify({width,height,frames:last.frames,stable:last.consecutiveStableComparisons,current:last.current}));}await new Promise(resolve=>setTimeout(resolve,500));}
  await page.evaluate(()=>window.__qaLayoutCancel?.());throw Error('Layout did not stabilize across real frames within900s: '+JSON.stringify(last));
 };
 const capture=async(label,state,expected)=>{
  const size=await page.evaluate(()=>[innerWidth,innerHeight]);assert.deepEqual(size,expected);
  await drainResponses();const sourceVersion=(report.sourceBindings['building-beacons.js']||report.sourceBindings['jiangwan-swimming-hall.js']).sha256.slice(0,8);
  const version=sourceVersion+'-'+sha(activeCaptureProvenance.sha256+(activeCaptureProvenance.controlSha256||'')+report.catalog.sha256+report.manifest.sha256).slice(0,8);
  const file=`browser-${label}-${version}.png`;assert.ok(!fs.existsSync(path.join(OUT,file)),'Refusing to overwrite screenshot: '+file);await page.screenshot({path:path.join(OUT,file),timeout:120000});
  const bytes=fs.readFileSync(path.join(OUT,file));assert.deepEqual([bytes.readUInt32BE(16),bytes.readUInt32BE(20)],expected);
  const result={label,file,bytes:bytes.length,sha256:sha(bytes),viewport:expected,state:structuredClone(state),sourceBindings:structuredClone(report.sourceBindings),captureScript:structuredClone(activeCaptureProvenance),visualAcceptance:'pending actual image review'};
  report.captures.push(result);save();console.log('SAVED',file);return result;
 };
 Object.assign(continuationContext.helpers,{layoutReady,capture});
 try{
  await page.goto(new URL('jiangwan-swimming-hall.html',BASE).href,{waitUntil:'domcontentloaded',timeout:90000});
  const auxiliaryState=async variant=>{
   await page.waitForFunction(v=>{const s=window.jiangwanSwimmingHallViewer?.getState();return s?.status==='error'||s?.status==='ready'&&s.variant===v;},variant,{timeout:90000});
   const s=await page.evaluate(()=>window.jiangwanSwimmingHallViewer.getState());assert.equal(s.status,'ready');assert.equal(s.variant,variant);assert.equal(s.modelId,ID);
   assert.equal(s.triangles,manifest.assets[variant].triangles);assert.ok(s.renderedTriangles>0);
   const b=s.framing?.screenBounds;assert.ok(b&&Object.values(b).every(Number.isFinite));
   assert.ok(b.minX>=-.96&&b.maxX<=.96&&b.minY>=-.96&&b.maxY<=.96&&b.minZ>=0&&b.maxZ<=1,JSON.stringify(b));
   return s;
  };
  continuationContext.helpers.auxiliaryState=auxiliaryState;report.auxiliary.full=await auxiliaryState('full');
  assert.equal(await page.locator('#enter-model-walk').count(),0);
  assert.ok((await page.locator('header a').getAttribute('href')).includes(`index.html#landmark=${ID}&mode=overview`));
  await capture('auxiliary-desktop-full',report.auxiliary.full,[1200,900]);
  await page.selectOption('#detail','lod');report.auxiliary.lod=await auxiliaryState('lod');assert.ok(report.auxiliary.lod.triangles<report.auxiliary.full.triangles);
  await capture('auxiliary-desktop-lod',report.auxiliary.lod,[1200,900]);
  await page.selectOption('#detail','full');await auxiliaryState('full');
  await page.setViewportSize({width:390,height:844});report.auxiliary.mobileResize=await layoutReady(390,844,false);report.auxiliary.mobile=await auxiliaryState('full');
  report.auxiliary.mobileLayout=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,canvas:document.querySelector('canvas').getBoundingClientRect().toJSON()}));
  assert.ok(report.auxiliary.mobileLayout.scrollWidth<=390);await capture('auxiliary-mobile-full',report.auxiliary.mobile,[390,844]);
  const links=await page.locator('#downloads a').evaluateAll(ns=>ns.map(n=>({role:n.dataset.role,url:n.href,download:n.hasAttribute('download')})));
  assert.equal(links.length,4);report.auxiliary.downloads=[];
  for(const role of ['raw','full','lod','native']){
   const link=links.find(l=>l.role===role),asset=manifest.assets[role];assert.ok(link?.download);assert.equal(new URL(link.url).pathname.split('/').pop(),asset.file);
   const response=await page.request.get(link.url,{timeout:120000});assert.equal(response.status(),200);const bytes=await response.body();assert.equal(bytes.length,asset.bytes);assert.equal(sha(bytes),asset.sha256);assert.ok(bytes.length<100000000);
   report.auxiliary.downloads.push({role,url:link.url,status:response.status(),bytes:bytes.length,sha256:sha(bytes),origin:response.headers()['x-audit-origin']});save();
  }

  // A non-WebGL document destroys the auxiliary renderer before main-map load.
  phase='directory';await page.goto(new URL('landmarks.html',BASE).href,{waitUntil:'domcontentloaded',timeout:90000});
  const cards=await page.locator('.landmark-card[data-landmark]').evaluateAll(ns=>ns.map(n=>({id:n.dataset.landmark,district:n.closest('.landmark-group').id,search:n.dataset.search,links:[...n.querySelectorAll('a')].map(a=>a.getAttribute('href'))})));
  continuationContext.cards=cards;assert.equal(cards.length,COUNT);assert.equal(new Set(cards.map(c=>c.id)).size,COUNT);assert.equal(new Set(cards.map(c=>c.district)).size,16);
  const newCard=cards.find(c=>c.id===ID);assert.equal(newCard.district,'district-310110');assert.ok(newCard.links.includes(`index.html#landmark=${ID}&mode=overview`));
  assert.ok(!newCard.links.some(l=>l.includes('mode=walk')));assert.ok(newCard.links.includes('jiangwan-swimming-hall.html'));
  const readmes=[readDirectory(path.join(REPO,'README.md')),readDirectory(path.join(PROJECT,'README.md'))];
  for(const d of readmes)sameIds(d.rows.map(r=>r.id),cards.map(c=>c.id));
  const mainResponse=await page.request.get(new URL('index.html',BASE).href);assert.equal(mainResponse.status(),200);
  const projectReadme=await page.request.get(new URL('README.md',BASE).href);assert.equal(projectReadme.status(),200);assert.equal(sha(await projectReadme.body()),readmes[1].sha256);
  const searchTerm='江湾';await page.fill('#landmark-search',searchTerm);
  const searched=await page.locator('.landmark-card[data-landmark]:visible').evaluateAll(ns=>ns.map(n=>n.dataset.landmark));
  sameIds(searched,cards.filter(c=>c.search.includes(searchTerm)).map(c=>c.id));assert.ok(searched.includes(ID));
  await page.fill('#landmark-search',row.name);const exactSearch=await page.locator('.landmark-card[data-landmark]:visible').evaluateAll(ns=>ns.map(n=>n.dataset.landmark));sameIds(exactSearch,[ID]);
  report.directory={cards,readmes,swimmingHallSearch:{term:searchTerm,matches:searched,exactTitle:row.name,exactMatches:exactSearch},mainDocumentHTTP:{status:mainResponse.status(),sha256:sha(await mainResponse.body())},projectReadmeHTTP:{status:projectReadme.status(),sha256:sha(await projectReadme.body())},note:'README link fragments are resolved against the local served final main document and actual runtime registry; root README is read from the worktree, not an unpublished remote cache.'};save();

  phase='global';await page.setViewportSize({width:960,height:720});
  await page.goto(new URL(`index.html#landmark=${ID}&mode=overview`,BASE).href,{waitUntil:'domcontentloaded',timeout:90000});
  await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__),null,{timeout:240000});
  report.global.webglCapabilities=await page.evaluate(()=>{
   const m=window.__SHANGHAI_APP__.scene.map,gl=m.painter?.context?.gl;if(!gl)throw Error('Existing map WebGL context is unavailable');
   const webgl2=typeof WebGL2RenderingContext!=='undefined'&&gl instanceof WebGL2RenderingContext;
   return {webgl2,version:gl.getParameter(gl.VERSION),shadingLanguageVersion:gl.getParameter(gl.SHADING_LANGUAGE_VERSION),renderer:gl.getParameter(gl.RENDERER),maxTextureSize:gl.getParameter(gl.MAX_TEXTURE_SIZE),maxFragmentUniformVectors:gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS),maxTextureImageUnits:gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS),maxVertexTextureImageUnits:gl.getParameter(gl.MAX_VERTEX_TEXTURE_IMAGE_UNITS),floatTextureNearestSupported:webgl2||Boolean(gl.getExtension('OES_texture_float')),glError:gl.getError(),clipping:window.__SHANGHAI_APP__.scene.getCandidateIntegrationState().shader,note:'Capabilities read from the existing map context; no second WebGL context is created.'};
  });assert.ok(report.global.webglCapabilities.floatTextureNearestSupported);assert.equal(report.global.webglCapabilities.glError,0);
  const gpu=report.global.webglCapabilities;assert.ok(gpu.maxTextureSize>=CLIP_CAPACITY);assert.ok(gpu.maxTextureImageUnits>=1);assertClipCapacity(gpu.clipping);save();

  const panel=async open=>{
   if((await page.locator('#panel-toggle').getAttribute('aria-expanded')==='true')!==open)await page.locator('#panel-toggle').click();
   // Finish the CSS transition before fitting the production default camera.
   await page.waitForFunction(open=>{const e=document.querySelector('#explore-panel'),r=e.getBoundingClientRect();return open?Math.abs(r.left-20)<.1:e.classList.contains('closed')&&r.right<=1;},open,{timeout:180000});
  };
  const select=async id=>{
   await page.evaluate(async id=>{const a=window.__SHANGHAI_APP__;await a.selectPlace(a.landmarks.find(r=>r.id===id),{mode:'overview'});},id);
   await page.waitForFunction(id=>{const a=window.__SHANGHAI_APP__,s=a.scene.getLandmarkAssetState(id);return s.visible&&s.status==='loaded'&&new URLSearchParams(location.hash.slice(1)).get('landmark')===id;},id,{timeout:180000,polling:500});
  };
  const settle=async requireReplacement=>{
   await page.evaluate(({requireReplacement,ownerId,ownerMacro})=>{window.__qaSwimmingHallSteady=()=>{
    const a=window.__SHANGHAI_APP__,m=a.scene.map,b=a.scene.getBuildingBeaconState(),c=a.scene.getCandidateIntegrationState(),v=c.vector.filter(x=>x.active);
    const owner=m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:ownerId}),stream=a.scene.getStreamingState();
    const city={loading:stream.loading,queued:stream.queued,pendingStates:stream.pendingStates,detailLoading:stream.detail.loading,ownerMacroVisible:stream.active.some(r=>r.id===ownerMacro&&r.visible),active:stream.active.map(r=>[r.id,r.visible]),detailActive:stream.detail.active.map(r=>[r.id,r.triangles])};
    const streamReady=city.loading===0&&city.queued===0&&city.pendingStates===0&&city.detailLoading===0;
    const ready=!m.isMoving()&&m.areTilesLoaded()&&streamReady&&b.sourceIds.every(id=>m.isSourceLoaded(id))&&(!requireReplacement||(city.ownerMacroVisible&&v.every(x=>!x.pending&&!x.residualLayer?.busy&&(!x.partialIDs||x.residualLayer?.ready))&&(owner.localModel===true||owner.candidateModel===true)));
    return {ready,owner,city,fingerprint:JSON.stringify({city,beacons:b.revision,shader:requireReplacement?c.shader:null,vector:requireReplacement?v.map(x=>[x.source,x.coveredIDs,x.partialIDs,x.pending,x.residualLayer?.generation]):null})};
   };},{requireReplacement,ownerId:EXPECTED_SOURCE,ownerMacro:row.owner.macro_id});
   for(let i=0;i<8;i++){
    const deadline=Date.now()+900000;let loggedAt=Date.now(),before;
    while(!(before=await page.evaluate(()=>window.__qaSwimmingHallSteady())).ready){
     if(Date.now()>deadline)throw Error('Scene did not reach ready/queue-zero within 900 seconds');
     if(Date.now()-loggedAt>=30000){loggedAt=Date.now();console.log('WAIT_STEADY',JSON.stringify({requireReplacement,ready:before.ready,city:before.city}));}
     await new Promise(resolve=>setTimeout(resolve,500));
    }
    const size=await page.evaluate(()=>[innerWidth,innerHeight]),renderGate=await layoutReady(size[0],size[1],true);await page.evaluate(gate=>{window.__qaLastSteadyRenderGate=gate;},renderGate);
    const after=await page.evaluate(()=>window.__qaSwimmingHallSteady());if(after.ready&&before.fingerprint===after.fingerprint)return after;
   }throw Error('Source/beacon state did not stabilize across two rendered frames');
  };
  const globalState=()=>page.evaluate(({row,nearbyModels,neighbors,visualViews})=>{
   const a=window.__SHANGHAI_APP__,m=a.scene.map,asset=a.scene.getLandmarkAssetState(row.id),c=a.scene.getCandidateIntegrationState(),b=a.scene.getBuildingBeaconState();
   const origin=maplibregl.MercatorCoordinate.fromLngLat([121.4737,31.2304],0),anchor=maplibregl.MercatorCoordinate.fromLngLat([row.lng,row.lat],row.altitude||0),unit=origin.meterInMercatorCoordinateUnits(),factor=anchor.meterInMercatorCoordinateUnits()/unit*row.scale;
   const worldCorners=[],angle=row.heading*Math.PI/180,cos=Math.cos(angle),sin=Math.sin(angle),u=anchor.meterInMercatorCoordinateUnits();
   for(const x of [row.bounds_glb.min[0],row.bounds_glb.max[0]])for(const y of [row.bounds_glb.min[1],row.bounds_glb.max[1]])for(const z of [row.bounds_glb.min[2],row.bounds_glb.max[2]]){const q=new maplibregl.MercatorCoordinate(anchor.x+(cos*x-sin*z)*row.scale*u,anchor.y+(sin*x+cos*z)*row.scale*u,anchor.z+y*row.scale*u),p=m.transform.coordinatePoint(q,q.toAltitude(),m.transform._pixelMatrix3D);worldCorners.push({x:p.x,y:p.y});}
   const projectWgs=(lngLat,height)=>{const q=maplibregl.MercatorCoordinate.fromLngLat(lngLat,height),p=m.transform.coordinatePoint(q,height,m.transform._pixelMatrix3D);return {lngLat,heightM:height,screen:[p.x,p.y]};};
   const uiRects=Object.fromEntries(['#explore-panel','#location-card','.map-tools','#building-beacon-legend'].map(selector=>[selector,document.querySelector(selector)?.getBoundingClientRect().toJSON()]).filter(([,rect])=>rect));
   const annotateProbe=p=>({...p,insideViewport:p.screen[0]>=0&&p.screen[0]<=innerWidth&&p.screen[1]>=0&&p.screen[1]<=innerHeight,uiAtPoint:Object.entries(uiRects).filter(([,r])=>p.screen[0]>=r.left&&p.screen[0]<=r.right&&p.screen[1]>=r.top&&p.screen[1]<=r.bottom).map(([name])=>name),beaconsAtPoint:b.labelPositions.filter(r=>Math.abs(p.screen[0]-r.x)<=r.width/2&&Math.abs(p.screen[1]-r.y)<=r.height/2).map(r=>r.id)});
   const projectedGeometry=(g,height)=>(g.type==='Polygon'?[g.coordinates]:g.coordinates).map(polygon=>polygon.map(ring=>ring.map(p=>projectWgs(p,height))));
   const preservedNeighborProbes=neighbors.map(n=>({id:n.source_id,localId:n.local_id,name:n.name,heightIsMapEstimate:n.roof_probe.height_is_map_estimate,actualNativeTriangleVerified:n.roof_probe.actual_native_triangle_verified,roof:annotateProbe(projectWgs(n.roof_probe.wgs84,n.roof_probe.height_m)),roofBoundary:projectedGeometry(n.source_geometry_wgs84,n.roof_probe.height_m),note:'Independent mapped source roof probe; visible pixels require image inspection.'}));
   const visualProbes=visualViews.map(v=>({key:v.key,probe:v.probe,projection:annotateProbe(projectWgs(v.probe.wgs84,v.probe.height_m)),note:'Camera target only. Actual image review establishes the swimming hall roof, side window recesses and bounded entrance geometry separately; projection alone does not certify visible depth or interior access.'}));
   return {visualProbes,uiRects,hash:location.hash,title:document.querySelector('#location-name').textContent,preservedNeighborProbes,mode:a.mode,viewport:[innerWidth,innerHeight],canvas:[m.getCanvas().clientWidth,m.getCanvas().clientHeight],map:{center:m.getCenter(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),padding:m.getPadding(),elevation:m.transform.elevation,centerClampedToGround:m.getCenterClampedToGround()},asset,nearbyModelStates:nearbyModels.map(r=>({id:r.id,state:a.scene.getLandmarkAssetState(r.id)})),candidate:c,beacons:b,worldCorners,
    expected:{position:[(anchor.x-origin.x)/unit,anchor.z/unit,(anchor.y-origin.y)/unit],minY:anchor.z/unit+row.bounds_glb.min[1]*factor,maxY:anchor.z/unit+row.bounds_glb.max[1]*factor},sourceStates:neighbors.map(n=>({id:n.source_id,name:n.name,sourceLayer:n.source_layer||'building',state:m.getFeatureState({source:'overture-buildings',sourceLayer:n.source_layer||'building',id:n.source_id})})),walkDisabled:document.querySelector('#walk-mode').disabled&&document.querySelector('#start-walk').disabled,renderer:a.scene.getStreamingState().renderer,streaming:a.scene.getStreamingState(),steady:window.__qaSwimmingHallSteady?.(),lighting:a.scene.getRealismState().lighting,steadyRenderGate:window.__qaLastSteadyRenderGate};
  },{row,nearbyModels:catalog.models.filter(r=>r.id!==ID&&Math.hypot((r.lng-row.lng)*95000,(r.lat-row.lat)*111000)<400),neighbors,visualViews:CONFIG.visual_views});
  const catalogueRows=await page.evaluate(async({models})=>{
   const THREE=await import('./vendor/three.module.js');const origin=maplibregl.MercatorCoordinate.fromLngLat([121.4737,31.2304]),unit=origin.meterInMercatorCoordinateUnits(),records=new Map();
   for(const model of models){if(model.replacement_geometry)records.set(model.id,{id:model.id,geometry:model.replacement_geometry,owner:model.owner,owners:model.owners});if(model.site_replacement){const q=model.site_replacement;if(records.has(q.id)&&JSON.stringify(records.get(q.id).geometry)!==JSON.stringify(q.geometry))throw Error('Shared site id with different geometry');records.set(q.id,q);}}
   const rows=[];for(const [id,clip]of records){let count=0;for(const rings of clip.geometry.type==='Polygon'?[clip.geometry.coordinates]:clip.geometry.coordinates){const contour=rings.map(r=>r.slice(0,-1).map(p=>{const q=maplibregl.MercatorCoordinate.fromLngLat(p);return new THREE.Vector2((q.x-origin.x)/unit,(q.y-origin.y)/unit);}));count+=THREE.ShapeUtils.triangulateShape(contour[0],contour.slice(1)).length*(clip.owners?.length||1);}rows.push({id,triangles:count});}return {rows,total:rows.reduce((n,r)=>n+r.triangles,0),method:'CPU triangulation of final catalogue with shipped THREE triangulator; no old GLB matrix or extra WebGL context.'};
  },{models:catalog.models});assert.equal(catalogueRows.total,CONFIG.expected_global_clip_triangles);const clipRows=Object.fromEntries(catalogueRows.rows.map(r=>[r.id,r.triangles]));report.clipCatalogueAudit={...catalogueRows,capacity:CLIP_CAPACITY,note:'Total catalogue rows differ from dynamically active clips. Each actual model view verifies only its current clip IDs.'};
  const assertAsset=(s,variant)=>{
   assertClipCapacity(s.candidate.shader);
   const a=s.asset,record=row.assets[variant==='full'?'web':'lod'];assert.equal(s.mode,'overview');assert.equal(a.status,'loaded');assert.ok(a.visible&&a.cityIntegration);assert.equal(a.variant,variant);assert.equal(a.triangles,record.triangles);
   assert.equal(a.verifiedAsset.sha256,record.sha256);assert.equal(a.verifiedAsset.bytes,record.bytes);assert.equal(s.candidate.active.find(r=>r.id===ID)?.assetSha256,record.sha256);
   assert.deepEqual(a.anchor,[row.lng,row.lat]);assert.equal(a.heading,row.heading);assert.equal(a.scale,row.scale);assert.ok(Math.abs(a.rotation[1]+row.heading*Math.PI/180)<1e-10);
   for(let i=0;i<3;i++)assert.ok(Math.abs(a.position[i]-s.expected.position[i])<1e-6);
   if(variant==='full'){assert.ok(Math.abs(a.worldBounds.min[1]-s.expected.minY)<.1);assert.ok(Math.abs(a.worldBounds.max[1]-s.expected.maxY)<.1);}
   const clip=s.candidate.clips.find(c=>c.id===ID);assert.ok(clip);assert.deepEqual(clip.geometry,row.replacement_geometry);assert.deepEqual(clip.source_feature_ids,row.source_feature_ids);assert.deepEqual(clip.owner,row.owner);
   sameIds(clip.source_feature_ids.building,CONFIG.source_feature_ids.building);if(row.site_replacement){const site=s.candidate.clips.find(c=>c.id===row.site_replacement.id);assert.ok(site,'Expected site clip missing');for(const key of ['geometry','owner','source_feature_ids'])assert.deepEqual(site[key],row.site_replacement[key],key);}const expectedActive=s.candidate.clips.reduce((n,c)=>{assert.ok(clipRows[c.id]!==undefined,'Unknown active clip '+c.id);return n+clipRows[c.id];},0);assert.equal(s.candidate.shader.triangles,expectedActive,'Active rows must equal the current clip IDs');assert.ok(expectedActive>=EXPECTED_CLIP_TRIANGLES&&expectedActive<=CONFIG.expected_global_clip_triangles);
  };
  const assertFraming=s=>{
   assertClipCapacity(s.candidate.shader);
   assert.deepEqual(s.canvas,s.viewport);const p=s.map.padding;
   for(const c of s.worldCorners){assert.ok(Number.isFinite(c.x)&&Number.isFinite(c.y));assert.ok(c.x>=p.left-.5&&c.x<=s.viewport[0]-p.right+.5&&c.y>=p.top-.5&&c.y<=s.viewport[1]-p.bottom+.5,JSON.stringify({c,p,viewport:s.viewport}));}
   assert.equal(s.map.centerClampedToGround,false);assert.ok(s.walkDisabled);
  };

  const assertNearGroups=(state,requiredIndices)=>{
   assertClipCapacity(state.candidate.shader);assert.ok(state.map.zoom>=17.3);
   return requiredIndices.map(index=>{const required=CONFIG.near_groups[index];assert.ok(required,'Unknown independent near group index');const group=state.candidate.shader.ownerScopedSources.find(g=>g.id===required.group_id&&g.macro_id===required.macro_id);assert.ok(group,'Expected near group not loaded');sameIds(group.feature_local_ids,required.feature_local_ids);sameIds(group.clip_feature_local_ids,required.clip_feature_local_ids);assert.equal(group.triangles,required.triangles);assert.ok(state.streaming.detail.active.some(r=>r.id===group.id));return {index,group};});
  };
  Object.assign(continuationContext.helpers,{panel,select,settle,globalState,assertAsset,assertFraming,assertNearGroups});
  await page.setViewportSize({width:320,height:568});await panel(false);await layoutReady(320,568,true);
  report.cardTitleCapacity=await page.evaluate(async()=>{
   const a=window.__SHANGHAI_APP__,m=a.scene.map,{walkingPose}=await import('./src/precise-registration-ui.js'),{layoutBeaconLabels,hitTestBeaconLabels}=await import('./src/building-beacons.js');
   const originalCard=document.querySelector('#location-card'),before=originalCard.outerHTML,currentRect=originalCard.getBoundingClientRect().toJSON(),clone=originalCard.cloneNode(true);
   clone.id='qa-card-measurement';clone.removeAttribute('aria-live');clone.inert=true;clone.style.transform='translateX(-10000px)';clone.style.visibility='hidden';clone.style.pointerEvents='none';
   for(const node of clone.querySelectorAll('[id]')){node.dataset.qaRole=node.id;node.removeAttribute('id');}
   const part=id=>clone.querySelector('[data-qa-role="'+id+'"]');document.body.append(clone);const rows=[];
   try{for(const place of a.landmarks){const district=a.districts.find(d=>d.id===(place.districtId||place.id)),overviewOnly=place.kind==='building'&&!walkingPose(place);
    part('location-name').textContent=place.name;part('location-district').textContent=(district?.name||'上海市')+(place.city_integration?' · 近似定位 · 外观模型':place.kind==='building'?' · 逐栋复原':place.height_m?' · 城市地标':' · 城市探索');
    part('start-walk').disabled=overviewOnly;part('start-walk').innerHTML=overviewOnly?'当前建筑仅支持俯瞰':'进入漫游 <span>↗</span>';
    part('reference-button').hidden=!place.reference&&!place.city_integration;part('reference-button').textContent=place.city_integration?'查看模型范围说明 ↗':'查看实景参考 ↗';
    const r=clone.getBoundingClientRect();rows.push({id:place.id,name:place.name,top:r.top,height:r.height,width:r.width,overviewOnly});
   }}finally{clone.remove();}
   if(originalCard.outerHTML!==before)throw Error('Main location card changed during offscreen measurement');
   const currentId=new URLSearchParams(location.hash.slice(1)).get('landmark'),currentCopy=rows.find(r=>r.id===currentId);if(!currentCopy||Math.abs(currentCopy.height-currentRect.height)>.5||Math.abs(currentCopy.width-currentRect.width)>.5)throw Error('Offscreen copy does not reproduce current card dimensions');
   const minTop=Math.min(...rows.map(r=>r.top)),maximumCards=rows.filter(r=>Math.abs(r.top-minTop)<.1),tools=document.querySelector('.map-tools').getBoundingClientRect(),legend=document.querySelector('#building-beacon-legend').getBoundingClientRect();
   const insets={left:12,right:Math.max(64,innerWidth-tools.left+8),top:Math.max(182,legend.bottom+8),bottom:Math.max(174,innerHeight-minTop+8)};
   const items=a.landmarks.map(r=>{const p=m.project([r.lng,r.lat]);return {id:r.id,x:p.x,y:p.y,width:176,height:62};}),positions=layoutBeaconLabels(items,{width:320,height:568,insets});
   return {viewport:[innerWidth,innerHeight],count:rows.length,currentId,currentCard:currentRect,currentCopy,rows,minimumCardTop:minTop,maximumCards,insets,positions,hits:positions.map(p=>({id:p.id,hit:hitTestBeaconLabels(positions,{x:p.labelX,y:p.labelY})})),overlapFallbackCount:positions.filter(p=>p.overlapFallback).length,distinctSlots:new Set(positions.map(p=>p.labelX+','+p.labelY)).size,mainCardUnchanged:true,method:'Offscreen cloned card uses current production CSS, real title, district, walkingPose/button and reference visibility for all current records. No other model is selected or loaded. Capacity calls the shipped layout function with all real IDs/locations and maximal name-cell dimensions to enter the same compact branch.'};
  });
  assert.equal(report.cardTitleCapacity.count,COUNT);assert.equal(report.cardTitleCapacity.overlapFallbackCount,0);assert.equal(report.cardTitleCapacity.distinctSlots,COUNT);
  sameIds(report.cardTitleCapacity.rows.map(r=>r.id),cards.map(c=>c.id));sameIds(report.cardTitleCapacity.positions.map(r=>r.id),cards.map(c=>c.id));for(const p of report.cardTitleCapacity.positions)assert.ok([p.labelX,p.labelY,p.width,p.height].every(Number.isFinite)&&p.width>0&&p.height>0);for(const p of report.cardTitleCapacity.hits)assert.equal(p.hit,p.id);
  for(let i=0;i<report.cardTitleCapacity.positions.length;i++){const p=report.cardTitleCapacity.positions[i],n=report.cardTitleCapacity.insets;assert.ok(p.labelX-p.width/2>=n.left-.1&&p.labelX+p.width/2<=320-n.right+.1&&p.labelY-p.height/2>=n.top-.1&&p.labelY+p.height/2<=568-n.bottom+.1);for(const q of report.cardTitleCapacity.positions.slice(i+1))assert.ok(Math.abs(p.labelX-q.labelX)>=(p.width+q.width)/2-.1||Math.abs(p.labelY-q.labelY)>=(p.height+q.height)/2-.1);}
  console.log('MAX_CARD_LAYOUT',JSON.stringify({minimumTop:report.cardTitleCapacity.minimumCardTop,maximumCards:report.cardTitleCapacity.maximumCards,slots:report.cardTitleCapacity.distinctSlots,overlapFallback:report.cardTitleCapacity.overlapFallbackCount}));save();
  await page.setViewportSize({width:960,height:720});
  await panel(true);report.global.desktopLayout=await layoutReady(960,720,true);await select(ID);await settle(true);
  report.global.defaultDesktop=await globalState();assert.ok(['full','distant'].includes(report.global.defaultDesktop.asset.variant));assertAsset(report.global.defaultDesktop,report.global.defaultDesktop.asset.variant);assertFraming(report.global.defaultDesktop);await capture('global-default-desktop',report.global.defaultDesktop,[960,720]);
  await page.setViewportSize({width:1200,height:900});await panel(false);report.global.nearLayout=await layoutReady(1200,900,true);
  report.global.visualViews={};report.global.visualAcceptance={};
  const applyVisualCamera=async camera=>{await page.evaluate(({camera,padding})=>{const s=window.__SHANGHAI_APP__.scene;s.setVisualQuality({shadows:false,surfaceNormals:true});s.map.setCenterClampedToGround(false);s.map.jumpTo({...camera,padding});s.loadLandmarks();},{camera,padding:ZERO_PADDING});await settle(true);};
  const validateVisualState=(view,state)=>{assertAsset(state,view.expected_variant);assert.equal(state.lighting.enabled,false,'Detail lighting disabled state must be actually sampled');if(view.whole_model)assertFraming(state);const groups=assertNearGroups(state,view.near_group_indices);const projection=state.visualProbes.find(p=>p.key===view.key).projection;assert.ok(projection.insideViewport);assert.deepEqual(projection.uiAtPoint,[]);assert.deepEqual(projection.beaconsAtPoint,[]);return groups;};
  const visualReview=async(view,firstCapture)=>{
   let current=firstCapture,attempt=0,loggedAt=0;const seen=new Set(),controlPath=process.env.QA_VISUAL_REVIEW_PATH||path.join(OUT,'visual-review-control.json');
   while(!report.global.visualAcceptance[view.key]?.accepted){
    if(Date.now()-loggedAt>=30000){loggedAt=Date.now();console.log('REVIEW_VISUAL_IMAGE',JSON.stringify({key:view.key,file:current.file,sha256:current.sha256,scriptSha256:current.captureScript.sha256,runGeneratedAt:report.generatedAt,controlPath}));}
    if(fs.existsSync(controlPath)){const bytes=fs.readFileSync(controlPath),digest=sha(bytes);if(!seen.has(digest)){seen.add(digest);let decision;
     try{decision=JSON.parse(bytes);if(decision.viewKey!==view.key&&report.global.visualAcceptance[decision.viewKey]?.control.sha256===digest)continue;assert.equal(decision.viewKey,view.key);assert.equal(decision.captureFile,current.file);assert.equal(decision.captureSha256,current.sha256);assert.equal(decision.scriptSha256,current.captureScript.sha256);assert.equal(decision.captureControlSha256,current.captureScript.controlSha256||null);assert.equal(decision.runGeneratedAt,report.generatedAt);assert.equal(typeof decision.accepted,'boolean');assert.ok(decision.observation?.trim());if(!decision.accepted){const c=decision.camera;assert.ok(c&&Array.isArray(c.center)&&c.center.length===2&&c.center.every(Number.isFinite)&&Number.isFinite(c.elevation)&&Number.isFinite(c.bearing)&&Number.isFinite(c.pitch)&&c.pitch>=0&&c.pitch<=85&&Number.isFinite(c.zoom)&&c.zoom>=17.3&&c.zoom<=23);}}
     catch(error){report.visualReviewInputErrors??=[];report.visualReviewInputErrors.push({sha256:digest,message:error.message,at:new Date().toISOString()});save();console.error('VISUAL_REVIEW_CONTROL_REJECTED',error.message);continue;}
     const file='visual-review-'+digest.slice(0,16)+'.json';if(!fs.existsSync(path.join(OUT,file)))fs.writeFileSync(path.join(OUT,file),bytes);else assert.equal(sha(fs.readFileSync(path.join(OUT,file))),digest);
     const record={key:view.key,capture:current.file,captureSha256:current.sha256,decision,control:{file,sha256:digest},at:new Date().toISOString()};report.visualPixelReviews??=[];report.visualPixelReviews.push(record);
     if(decision.accepted){report.global.visualAcceptance[view.key]={...record,accepted:true};save();break;}
     await applyVisualCamera(decision.camera);const state=await globalState();state.qaCameraDecision={camera:decision.camera,reason:decision.observation,controlSha256:digest};state.requiredNearGroups=validateVisualState(view,state);report.global.visualViews[view.key]=state;current=await capture(view.label+'-adjusted-'+(++attempt),state,[1200,900]);loggedAt=0;
    }}await new Promise(resolve=>setTimeout(resolve,500));
   }
  };
  Object.assign(continuationContext.helpers,{applyVisualCamera,validateVisualState,visualReview});
  for(const view of CONFIG.visual_views){await applyVisualCamera(view.camera);const state=await globalState();state.requiredNearGroups=validateVisualState(view,state);state.note=view.note;report.global.visualViews[view.key]=state;const image=await capture(view.label,state,[1200,900]);await visualReview(view,image);}
  report.global.groundCollision=await page.evaluate(probes=>{const s=window.__SHANGHAI_APP__.scene;s.getCollisionState();return probes.map(p=>({...p,actual:s.collisionAt(...p.wgs84)}));},CONFIG.ground_probes);for(const p of report.global.groundCollision)assert.equal(p.actual,p.expected,p.name);save();

  await page.setViewportSize({width:960,height:720});await panel(true);await layoutReady(960,720,true);await select(ID);
  // Check only this new building's full/LOD swap; neighbors remain rendered.
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:false,surfaceNormals:true});});
  for(const {variant,zoom,pitch} of CONFIG.variant_views){
   await page.evaluate(({row,zoom,pitch,padding})=>{const s=window.__SHANGHAI_APP__.scene;s.map.jumpTo({center:[row.lng,row.lat],zoom,pitch,bearing:row.heading,padding,elevation:0});s.loadLandmarks();},{row,zoom,pitch,padding:ZERO_PADDING});
   await page.waitForFunction(({id,variant})=>{const s=window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id);return s.visible&&s.status==='loaded'&&s.variant===variant;},{id:ID,variant},{timeout:180000,polling:500});
   await settle(true);const state=await globalState();assertAsset(state,variant);report.global[variant==='full'?'full':'lod']=state;save();
  }
  report.global.registry=await page.evaluate(async()=>{
   const a=window.__SHANGHAI_APP__,{resolveNavigationRoute}=await import('./src/landmark-navigation.js'),o={districts:a.districts,landmarks:a.landmarks,bund:{id:'bund',name:'外滩历史建筑群'}};
   return {ids:a.landmarks.map(r=>r.id),districtIds:a.districts.map(r=>r.id),routes:a.landmarks.map(r=>{const x=resolveNavigationRoute('#landmark='+r.id+'&mode=overview',o);return {id:r.id,matched:x.place?.id,error:x.error||null};})};
  });sameIds(report.global.registry.ids,cards.map(c=>c.id));assert.equal(report.global.registry.districtIds.length,16);for(const r of report.global.registry.routes){assert.equal(r.id,r.matched);assert.equal(r.error,null);}
  await select(ID);await settle(true);const pair=await globalState();
  const newClip=pair.candidate.clips.find(c=>c.id===ID),newSiteClip=row.site_replacement?pair.candidate.clips.find(c=>c.id===row.site_replacement.id):null;assert.ok(newClip);if(row.site_replacement){assert.ok(newSiteClip);assert.deepEqual(newSiteClip.geometry,row.site_replacement.geometry);assert.deepEqual(newSiteClip.source_feature_ids,row.site_replacement.source_feature_ids);assert.deepEqual(newSiteClip.owner,row.site_replacement.owner);}
  const retained=[];
  for(const item of pair.nearbyModelStates){
   if(!item.state.visible)continue;
   assert.equal(item.state.status,'loaded');const record=catalog.models.find(r=>r.id===item.id),variant=item.state.variant==='full'?'web':'lod';
   assert.equal(item.state.verifiedAsset.sha256,record.assets[variant].sha256);
   const clip=pair.candidate.clips.find(c=>c.id===item.id);assert.ok(clip);assert.deepEqual(clip.source_feature_ids,record.source_feature_ids);assert.deepEqual(clip.geometry,record.replacement_geometry);
   retained.push(item.id);
  }
  const legitimatelyReplaced=new Set(pair.candidate.clips.flatMap(c=>Object.entries(c.source_feature_ids||{}).flatMap(([layer,ids])=>ids.map(id=>layer+'/'+id))));for(const n of pair.sourceStates)if(!legitimatelyReplaced.has(n.sourceLayer+'/'+n.id))assert.notEqual(n.state.candidateModel,true,n.id);
  const excludedContextSources=contextIds.map(id=>{const n=pair.sourceStates.find(s=>s.id===id);assert.ok(n,'Required retained context source must be in independent neighbor inventory');if(!legitimatelyReplaced.has(n.sourceLayer+'/'+n.id))assert.notEqual(n.state.candidateModel,true,id);return {...n,legitimateExistingReplacement:legitimatelyReplaced.has(n.sourceLayer+'/'+n.id)};});
  report.global.neighborSeparation={newClip,newSiteClip,excludedContextSources,preservedNeighborProbes:pair.preservedNeighborProbes,nearbyModelStates:pair.nearbyModelStates,visibleExistingModelsVerified:retained,sourceStates:pair.sourceStates,note:'The new correction names only the independently reviewed swimming hall source; the existing stadium and northern gymnasium remain distinct. Any visible pre-existing models keep their own asset hashes and clip geometries. Near-neighbor source IDs outside all legitimate replacement sets are not candidate-hidden. localModel state may refer to retained source geometry in a loaded city tile; it does not mean that neighboring feature was removed.'};save();
  await page.setViewportSize({width:390,height:844});await panel(false);report.global.mobileLayout=await layoutReady(390,844,true);
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:true,surfaceNormals:true});});await select(ID);await settle(true);
  report.global.defaultMobile=await globalState();assert.ok(['full','distant'].includes(report.global.defaultMobile.asset.variant));assertAsset(report.global.defaultMobile,report.global.defaultMobile.asset.variant);assertFraming(report.global.defaultMobile);await capture('global-default-mobile',report.global.defaultMobile,[390,844]);

  report.global.webglAfterModelChecks=await page.evaluate(()=>{const a=window.__SHANGHAI_APP__,gl=a.scene.map.painter.context.gl;return {glError:gl.getError(),contextLost:gl.isContextLost(),clipping:a.scene.getCandidateIntegrationState().shader,note:'Read after actual desktop, explicit near/side/entry, full/LOD and mobile model rendering with the frozen production clip texture.'};});
  assert.equal(report.global.webglAfterModelChecks.glError,0);assert.equal(report.global.webglAfterModelChecks.contextLost,false);assertClipCapacity(report.global.webglAfterModelChecks.clipping);assert.ok(report.global.webglAfterModelChecks.clipping.triangles>0);
  await drainResponses();
  report.global.ownerGroupIsolation={groups:CONFIG.near_groups.map((required,index)=>{const observed=Object.entries(report.global.visualViews).flatMap(([key,state])=>(state.requiredNearGroups||[]).filter(g=>g.index===index).map(g=>({view:key,group:g.group})));assert.ok(observed.length,'Independent near group must be exercised by at least one actual visual view');const nearHTTP=report.citySourceHTTP.find(r=>r.path===required.near_path.replace(/^projects\/shanghai\//,''));assert.ok(nearHTTP);assert.equal(nearHTTP.sha256,required.sha256);assert.equal(nearHTTP.bytes,required.bytes);return {required,observed,nearHTTP};}),note:'Actual near-group owners and source HTTP bytes are checked against independent frozen mapping. Group-wide texture binding is not a claim that every owner is individually clipped.'};save();
  phase='beacons';await page.setViewportSize({width:320,height:568});await panel(false);report.beaconsResize=await layoutReady(320,568,true);await select(TOUCH_FROM);
  await page.evaluate(padding=>{const a=window.__SHANGHAI_APP__,m=a.scene.map;window.__qaOriginalBounds=m.getMaxBounds()?.toArray()||null;a.scene.setVisualQuality({shadows:false,surfaceNormals:true});m.setMaxBounds(null);m.setCenterClampedToGround(true);m.jumpTo({center:[121.45,31.20],zoom:8,pitch:0,bearing:0,elevation:0,padding});a.scene.refreshBuildingBeacons();},ZERO_PADDING);
  await settle(false);
  const beaconScene=()=>page.evaluate(()=>{
   const a=window.__SHANGHAI_APP__,m=a.scene.map,s=a.scene.getBuildingBeaconState(),rect=selector=>document.querySelector(selector)?.getBoundingClientRect().toJSON();
   return {viewport:[innerWidth,innerHeight],canvas:[m.getCanvas().clientWidth,m.getCanvas().clientHeight],state:s,map:{center:m.getCenter(),zoom:m.getZoom(),padding:m.getPadding(),elevation:m.transform.elevation,maxBounds:m.getMaxBounds()},sources:s.sourceIds.map(id=>({id,count:m.getSource(id).serialize().data.features.length,ids:m.getSource(id).serialize().data.features.map(f=>f.properties.id)})),picks:s.labelPositions.map(p=>({id:p.id,hit:a.scene.pickBuildingBeacon({x:p.x,y:p.y})})),ui:{card:rect('#location-card'),tools:rect('.map-tools'),legend:rect('#building-beacon-legend')},layers:s.layerIds.map(id=>m.getLayer(id).serialize()),allSpritesPresent:s.spriteIds.every(id=>m.hasImage(id))};
  });
  const assertLabelLayout=state=>{
   const labels=state.state.labelPositions;for(let i=0;i<labels.length;i++){
    const p=labels[i];assert.ok(p.x-p.width/2>=0&&p.x+p.width/2<=320&&p.y-p.height/2>=0&&p.y+p.height/2<=state.viewport[1]);
    for(const rect of Object.values(state.ui))if(rect)assert.ok(p.x+p.width/2<=rect.left+.1||p.x-p.width/2>=rect.right-.1||p.y+p.height/2<=rect.top+.1||p.y-p.height/2>=rect.bottom-.1,`UI overlaps ${p.id}`);
    for(const q of labels.slice(i+1))assert.ok(Math.abs(p.x-q.x)>=(p.width+q.width)/2-.1||Math.abs(p.y-q.y)>=(p.height+q.height)/2-.1,`Overlap ${p.id}/${q.id}`);
   }
   for(const p of state.picks)assert.equal(p.hit,p.id);
   assert.equal(state.state.overlapFallbackCount,0);
  };
  const assertDenseBeacons=(b,expectedHeight=568)=>{
   assert.deepEqual(b.viewport,[320,expectedHeight]);assert.deepEqual(b.canvas,b.viewport);assert.equal(b.map.zoom,8);assert.equal(b.state.count,COUNT);assert.equal(b.state.districtCount,16);assert.equal(b.state.viewportLabelCount,COUNT);assert.equal(b.state.labelMode,'numbers');assert.equal(b.state.labelPixelSize,12);assert.equal(b.state.anchorPixelSize,20);assert.ok(b.allSpritesPresent);
   assert.equal(b.state.spriteIds.length,CONFIG.beacon_sprite_ids.length);sameIds(b.state.spriteIds,CONFIG.beacon_sprite_ids);assert.ok(b.state.spriteIds.includes('shanghai-building-beacons-number-dense'));
   sameIds(b.state.ids,cards.map(c=>c.id));sameIds(b.state.labelPositions.map(p=>p.id),b.state.ids);for(const source of b.sources)sameIds(source.ids,b.state.ids);
   for(const p of b.state.labelPositions)assert.ok(['20x18','22x18','22x20','24x20'].includes(`${p.width}x${p.height}`),`Unexpected dense sprite bounds ${p.width}x${p.height}`);
   assertLabelLayout(b);
  };
  Object.assign(continuationContext.helpers,{beaconScene,assertLabelLayout,assertDenseBeacons});
  const b=await beaconScene();assertDenseBeacons(b);let labels=b.state.labelPositions;
  report.beacons={...b,quality:'Shadows disabled for marker-only matrix; buildings retained. maxBounds temporarily removed to permit exact zoom8, restored after touch.',compactWidths:[...new Set(labels.map(p=>p.width))],compactSizes:[...new Set(labels.map(p=>`${p.width}x${p.height}`))]};
  await capture('beacons-320-city-80',report.beacons,[320,568]);
  // Exercise a smaller production viewport when the worst real title needs
  // more height than the actual TOUCH_FROM card. Do not select an old model.
  const lostHeight=Math.max(0,Math.ceil(b.ui.card.top-report.cardTitleCapacity.minimumCardTop));
  if(lostHeight>0){
   const height=568-lostHeight;await page.setViewportSize({width:320,height});await panel(false);await layoutReady(320,height,true);await settle(false);
   const short=await beaconScene();assertDenseBeacons(short,height);assert.ok(short.ui.card.top<=report.cardTitleCapacity.minimumCardTop+.5);
   report.beacons.worstTitleViewport={scene:short,simulatedCardTop:report.cardTitleCapacity.minimumCardTop,actualSelected:TOUCH_FROM,note:'A real smaller viewport reproduces the worst current title free area without selecting that historical model or changing the live card.'};
   await capture(`beacons-320x${height}-worst-title-${COUNT}`,short,[320,height]);
   await page.setViewportSize({width:320,height:568});await panel(false);await layoutReady(320,568,true);await settle(false);
   const restored=await beaconScene();assertDenseBeacons(restored);labels=restored.state.labelPositions;report.beacons.worstTitleViewport.restored={viewport:restored.viewport,map:restored.map,card:restored.ui.card};
  }
  const before=await page.evaluate(()=>({hash:location.hash,title:document.querySelector('#location-name').textContent,center:window.__SHANGHAI_APP__.scene.map.getCenter()}));assert.equal(new URLSearchParams(before.hash.slice(1)).get('landmark'),TOUCH_FROM);
  const point=labels.find(p=>p.id===ID);assert.ok(point);const touch=await page.context().newCDPSession(page);
  await touch.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1});await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{id:1,x:point.x,y:point.y}]});await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id&&document.querySelector('#location-name').textContent===window.__SHANGHAI_APP__.landmarks.find(r=>r.id===id).name&&window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id).visible&&window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id).status==='loaded',ID,{timeout:180000});await touch.detach();
  const after=await page.evaluate(()=>({hash:location.hash,title:document.querySelector('#location-name').textContent,center:window.__SHANGHAI_APP__.scene.map.getCenter()}));assert.notEqual(before.hash,after.hash);assert.notEqual(before.title,after.title);assert.notDeepEqual(before.center,after.center);
  report.beacons.touch={method:'native CDP touchStart/touchEnd',id:ID,point:[point.x,point.y],before,after,changedDestination:true,targetAssetVisibleAfterTouch:true};
  await settle(true);const postTouchLayout=await beaconScene();assertLabelLayout(postTouchLayout);
  report.beacons.postTouchLayout={...postTouchLayout,note:'Actual selected Jiangwan Swimming Hall overview after native touch. Only the geographically visible labels are checked here; this does not claim that all current anchors are in this close viewport.'};
  const testedCardTop=Math.min(b.ui.card.top,report.beacons.worstTitleViewport?.scene.ui.card.top??Infinity);
  const requiresLargerCardProof=postTouchLayout.ui.card.top<testedCardTop-.5;
  report.beacons.postTouchCardComparison={beforeTop:b.ui.card.top,afterTop:postTouchLayout.ui.card.top,testedMinimumTop:testedCardTop,afterUsesMoreVerticalSpace:postTouchLayout.ui.card.top<b.ui.card.top-.5,requiresAdditionalCityCapture:requiresLargerCardProof};
  if(requiresLargerCardProof){
   await page.evaluate(padding=>{const a=window.__SHANGHAI_APP__,m=a.scene.map;a.scene.setVisualQuality({shadows:false,surfaceNormals:true});m.setCenterClampedToGround(true);m.jumpTo({center:[121.45,31.20],zoom:8,pitch:0,bearing:0,elevation:0,padding});a.scene.refreshBuildingBeacons();},ZERO_PADDING);
   await settle(false);report.beacons.postTouchCity=await beaconScene();assertDenseBeacons(report.beacons.postTouchCity);
   await capture('beacons-320-swimming-hall-city-80',report.beacons.postTouchCity,[320,568]);
  }else report.beacons.postTouchCardComparison.additionalCityCapture='Not needed: the selected target card leaves at least the free space already validated by the actual dense viewport captures.';
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.map.setMaxBounds(window.__qaOriginalBounds);});
  await drainResponses();assert.equal(report.catalog.http?.sha256,report.catalog.sha256);assert.equal(report.catalog.http?.status,200);assert.deepEqual(report.errors,[]);assert.deepEqual(report.warnings,[]);assert.deepEqual(report.http,[]);
  for(const binding of report.expectedSourceBindings)assert.equal(report.sourceBindings[binding.file.slice(4)]?.sha256,binding.sha256,`Served source does not match freeze: ${binding.file}`);
  for(const binding of [report.catalog,report.manifest,report.footprint,report.qaScript,report.viewerRegistry,report.placementBinding,report.qaContract,...report.expectedSourceBindings,...report.documentBindings])assert.equal(sha(fs.readFileSync(path.join(PROJECT,binding.file))),binding.sha256,`Frozen file changed during QA: ${binding.file}`);for(const binding of staticDirectories)assert.equal(sha(fs.readFileSync(path.join(REPO,binding.file))),binding.sha256,`README changed during QA: ${binding.file}`);
  await finalizeChecks();console.log('COMPLETE Jiangwan Swimming Hall incremental browser checks; final PNG review remains separate');
 }catch(error){report.completed=false;report.failure=error.stack;report.failures??=[];report.failures.push({at:new Date().toISOString(),phase,message:error.stack,script:structuredClone(activeCaptureProvenance)});save();console.error(error);if(process.env.QA_KEEP_ON_FAILURE==='0')throw error;console.error('Original Playwright host retained; use a SHA-bound continuation module, never a second controller.');await waitForContinuation({controlPath:process.env.QA_CONTINUATION_CONTROL||path.join(OUT,'continuation-control.json'),context:continuationContext,report,save,verifyFrozenInputs,onProgress:(message,detail)=>console.log('CONTINUATION',message,JSON.stringify(detail))});delete report.failure;save();
 }finally{await browser.close();report.browserClosed=true;report.browserClosedAt=new Date().toISOString();save();}
}
if(require.main===module)run().catch(e=>{console.error(e);process.exitCode=1;});
module.exports={readDirectory};
