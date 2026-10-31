/* Cathay Mansions incremental QA. One browser/page; no old-model matrix. MIT. */
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const {createHash}=require('crypto');
const PROJECT=path.resolve(__dirname,'../../..'),REPO=path.resolve(PROJECT,'../..');
const OUT=process.env.QA_OUTPUT_DIR||__dirname,BASE=process.env.MODEL_BASE_URL||'http://127.0.0.1:8782/';
const ID='huangpu-cathay-mansions',TOUCH_FROM='huangpu-daxin-company';
const COUNT=74;
const EXPECTED_SOURCE='f6e4b883-ed86-4c90-aa96-2c717ff043c5';
const ZERO_PADDING={top:0,right:0,bottom:0,left:0};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=rel=>JSON.parse(fs.readFileSync(path.join(PROJECT,rel),'utf8'));
const sameIds=(a,b)=>assert.deepEqual([...a].sort(),[...b].sort());

function readDirectory(file){
 const text=fs.readFileSync(file,'utf8'),section=text.split(/^## 按区查看主要建筑\s*$/m)[1]?.split(/^## /m)[0];
 assert.ok(section,`missing district directory: ${file}`);
 const groups=[...section.matchAll(/^### ([^\n]+?)（(\d+)处）\s*$/gm)];
 const rows=[...section.matchAll(/^\|[^\n]*\[查看网页\]\((https:\/\/[^\s)]+#landmark=([^&\s)]+)&mode=(walk|overview))\)[^\n]*$/gm)].map(m=>({id:m[2],url:m[1],mode:m[3]}));
 assert.equal(groups.length,16);assert.equal(rows.length,COUNT);assert.equal(new Set(rows.map(r=>r.id)).size,COUNT);
 assert.equal(groups.reduce((n,g)=>n+Number(g[2]),0),COUNT);
 assert.equal(rows.find(r=>r.id===ID)?.mode,'overview');
 assert.equal(groups.find(g=>g[1]==='黄浦区')?.[2],'26');
 assert.equal(rows.filter(r=>r.mode==='walk').length,40);
 for(const row of rows)assert.equal(new URL(row.url).pathname,'/ecojust/e-resource/master/projects/shanghai/index.html');
 for(let i=0;i<groups.length;i++){
  const part=section.slice(groups[i].index,groups[i+1]?.index??section.length);
  assert.equal((part.match(/\[查看网页\]\(https:[^\n]*?#landmark=/g)||[]).length,Number(groups[i][2]),groups[i][1]);
 }
 return {file:path.relative(REPO,file),sha256:sha(text),districts:groups.map(g=>({name:g[1],count:Number(g[2])})),rows};
}

async function run(){
 // Explicit opt-in prevents preparation or syntax checks from starting WebGL.
 assert.ok(process.argv.includes('--run')||process.argv.includes('--preflight'),'Preparation only. Use --preflight for frozen metadata checks; --run starts the one browser after full freeze.');
 fs.mkdirSync(OUT,{recursive:true});
 const catalogPath='data/candidate-city-integrations.json',catalog=read(catalogPath),row=catalog.models.find(r=>r.id===ID),touchFrom=catalog.models.find(r=>r.id===TOUCH_FROM);
 assert.equal(catalog.models.length,34);assert.ok(row&&touchFrom);assert.equal(row.navigation.listed,false);
 const footprint=read('data/audit/cathay-mansions-v1/footprint-review.json');
 const manifest=read(`assets/models/candidates/${ID}/manifest.json`);
 const viewer=read('data/model-viewers.json').find(r=>r.id===ID);assert.ok(viewer,'New model must be in auxiliary viewer directory');assert.equal(viewer.page,'cathay-mansions.html');assert.equal(viewer.manifest,`assets/models/candidates/${ID}/manifest.json`);
 assert.notEqual(EXPECTED_SOURCE,'PENDING_INDEPENDENT_MAPPING','Freeze independent source mapping before WebGL QA');
 assert.equal(manifest.id,ID);assert.equal(footprint.identity.source_id,EXPECTED_SOURCE);
 sameIds(row.source_feature_ids.building,[EXPECTED_SOURCE]);
 assert.ok(Number.isSafeInteger(row.owner.feature_local_id));
 for(const key of ['macro_id','feature_local_id'])assert.equal(row.owner[key],footprint.global_source_owner[key]);
 assert.equal(footprint.global_source_owner.source_feature_id,EXPECTED_SOURCE);
 assert.ok(!touchFrom.source_feature_ids.building.includes(EXPECTED_SOURCE));
 const contract=footprint.proposed_placement_contract;
 assert.ok(contract.replacement_geometry?.type,'Final replacement geometry must be frozen before QA');
 assert.deepEqual(row.replacement_geometry,contract.replacement_geometry);
 assert.deepEqual(row.source_feature_ids,contract.source_feature_ids);
 for(const key of ['lng','lat','heading','scale','overviewBearing','overviewPitch'])assert.equal(row[key],contract[key],key);
 assert.equal(row.partial_model||false,contract.partial_model||false);
 const neighbors=[...new Map([...footprint.exclusions.all_macro_neighbors_within_65m,...footprint.exclusions.required_context_sources].map(n=>[n.source_id,n])).values()];
 const contextIds=Object.values(footprint.identity.excluded_context_sources);assert.equal(contextIds.length,3);for(const id of contextIds)assert.ok(neighbors.some(n=>n.source_id===id),'Missing required retained context source '+id);
 assert.ok(Array.isArray(neighbors)&&neighbors.length>0,'Independent near-neighbor source inventory required');
 assert.ok(neighbors.every(n=>n.source_id&&n.source_id!==EXPECTED_SOURCE));
 const report={generatedAt:new Date().toISOString(),completed:false,modelId:ID,
  scope:'Only Cathay Mansions, its independently documented source ownership, north recess and excluded neighbors, the 74-entry directory and 320px beacon capacity increment. One browser and one page, with sequential auxiliary/directory/main-map documents. No replay of the existing 33-model asset matrix.',
  captureStabilityPolicy:'After viewport changes, wait for DOM/canvas/MapLibre dimensions and UI geometry to agree across two rendered frames before fitting the camera. Wait for map and beacon readiness, finished city far/near loading and queues, all pending feature-state writes, actual owner macro visibility, completed vector corrections, then the same stable source/mesh fingerprint across two rendered frames. Diagnostic attempts are retained privately and excluded from this report.',
  catalog:{file:catalogPath,sha256:sha(fs.readFileSync(path.join(PROJECT,catalogPath))),models:catalog.models.length},
  manifest:{file:`assets/models/candidates/${ID}/manifest.json`,sha256:sha(fs.readFileSync(path.join(PROJECT,`assets/models/candidates/${ID}/manifest.json`)))},
  footprint:{file:'data/audit/cathay-mansions-v1/footprint-review.json',sha256:sha(fs.readFileSync(path.join(PROJECT,'data/audit/cathay-mansions-v1/footprint-review.json')))},
  qaScript:{file:path.relative(PROJECT,__filename),sha256:sha(fs.readFileSync(__filename))},
  sourceBindings:{},citySourceHTTP:[],http:[],auxiliary:{},directory:{},global:{},beacons:{},captures:[],errors:[],warnings:[]};
 report.expectedSourceBindings=['src/candidate-city-clipping.js','src/building-beacons.js','src/cathay-mansions.js'].map(file=>({file,sha256:sha(fs.readFileSync(path.join(PROJECT,file)))}));
 report.viewerRegistry={file:'data/model-viewers.json',sha256:sha(fs.readFileSync(path.join(PROJECT,'data/model-viewers.json'))),entry:viewer};
 const staticDirectories=[readDirectory(path.join(REPO,'README.md')),readDirectory(path.join(PROJECT,'README.md'))];
 sameIds(staticDirectories[0].rows.map(r=>r.id),staticDirectories[1].rows.map(r=>r.id));
 report.preflight={passed:true,directories:staticDirectories.map(d=>({file:d.file,sha256:d.sha256,count:d.rows.length}))};
 if(process.argv.includes('--preflight')){console.log(JSON.stringify({preflight:true,modelId:ID,count:COUNT,catalog:report.catalog.sha256,manifest:report.manifest.sha256,footprint:report.footprint.sha256,script:report.qaScript.sha256}));return;}
 const save=()=>fs.writeFileSync(path.join(OUT,'browser.json'),JSON.stringify(report,null,2)+'\n');
 const existingBrowser=await fetch('http://127.0.0.1:9223/json/version',{signal:AbortSignal.timeout(1000)}).then(r=>r.ok).catch(()=>false);
 assert.equal(existingBrowser,false,'A QA browser is already active. Keep one controller; do not launch a second instance.');
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9223']});
 const page=await browser.newPage({viewport:{width:1200,height:900},hasTouch:true});
 report.browserVersion=browser.version();report.playwrightVersion=require('playwright/package.json').version;report.nodeVersion=process.version;let phase='auxiliary';
 const responses=[];
 page.on('pageerror',e=>{report.errors.push({phase,message:e.message});save();});
 page.on('console',m=>{if(m.type()==='error')report.errors.push({phase,message:m.text()});if(m.type()==='warning')report.warnings.push({phase,message:m.text()});});
 page.on('response',r=>{
  const u=new URL(r.url());
  if(r.status()>=400)report.http.push({phase,status:r.status(),url:r.url()});
  if(u.origin===new URL(BASE).origin&&u.pathname==='/data/candidate-city-integrations.json')responses.push((async()=>{const h=await r.allHeaders(),body=await r.body();report.catalog.http={url:r.url(),status:r.status(),sha256:sha(body),origin:h['x-audit-origin']||'HTTP body'};assert.equal(report.catalog.http.sha256,report.catalog.sha256);})());
  if(u.origin===new URL(BASE).origin&&u.pathname.startsWith('/assets/city-detail/macros/')&&[row.owner.macro_id,...footprint.exclusions.required_context_sources.map(n=>n.macro_id)].some(id=>u.pathname.includes('/'+id+'/')))responses.push((async()=>{
   const h=await r.allHeaders();report.citySourceHTTP.push({url:r.url(),path:u.pathname.slice(1),status:r.status(),sha256:h['x-audit-sha256']||sha(await r.body()),origin:h['x-audit-origin']||'HTTP body',bytes:Number(h['content-length']),phase});
  })());
  if(u.origin===new URL(BASE).origin&&u.pathname.startsWith('/src/'))responses.push((async()=>{
   const h=await r.allHeaders();report.sourceBindings[u.pathname.slice(5)]={sha256:h['x-audit-sha256']||sha(await r.body()),origin:h['x-audit-origin']||'HTTP body',status:r.status()};
  })());
 });
 const layoutReady=async(width,height,main)=>page.evaluate(async({width,height,main})=>{
  const m=main?window.__SHANGHAI_APP__.scene.map:null;
  const state=()=>{const canvas=document.querySelector('canvas'),r=canvas.getBoundingClientRect(),rect=q=>document.querySelector(q)?.getBoundingClientRect().toJSON();return {inner:[innerWidth,innerHeight],canvas:[canvas.clientWidth,canvas.clientHeight],buffer:[canvas.width,canvas.height],rect:[r.width,r.height],transform:m?[m.transform.width,m.transform.height]:null,ui:['#explore-panel','#location-card','.map-tools','#building-beacon-legend'].map(rect)};};
  const dimensions=s=>s.inner[0]===width&&s.inner[1]===height&&(main?s.canvas[0]===width&&s.canvas[1]===height&&s.transform[0]===width&&s.transform[1]===height:s.canvas[0]===s.rect[0]&&s.canvas[1]===s.rect[1]&&s.buffer[0]===Math.round(s.rect[0]*devicePixelRatio)&&s.buffer[1]===Math.round(s.rect[1]*devicePixelRatio));
  const fingerprint=s=>JSON.stringify([s.inner,s.canvas,s.buffer,s.transform,...s.ui.map(r=>r&&[r.left,r.top,r.right,r.bottom].map(v=>Math.round(v*100)/100))]);
  const deadline=performance.now()+240000;let previous=null,consecutive=0;
  while(performance.now()<deadline){
   await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('No layout render for 60s')),60000),done=()=>{clearTimeout(timer);resolve();};if(m){m.once('render',done);m.triggerRepaint();}else requestAnimationFrame(done);});
   const s=state(),next=fingerprint(s);consecutive=dimensions(s)&&next===previous?consecutive+1:0;previous=next;if(consecutive>=2)return s;
  }throw Error('Viewport/canvas/MapLibre/UI dimensions did not stabilize');
 },{width,height,main});
 const capture=async(label,state,expected)=>{
  const size=await page.evaluate(()=>[innerWidth,innerHeight]);assert.deepEqual(size,expected);
  await Promise.all(responses);const sourceVersion=(report.sourceBindings['building-beacons.js']||report.sourceBindings['cathay-mansions.js']).sha256.slice(0,8);
  const version=sourceVersion+'-'+sha(fs.readFileSync(__filename)+report.catalog.sha256+report.manifest.sha256).slice(0,8);
  const file=`browser-${label}-${version}.png`;assert.ok(!fs.existsSync(path.join(OUT,file)),'Refusing to overwrite screenshot: '+file);await page.screenshot({path:path.join(OUT,file),timeout:120000});
  const bytes=fs.readFileSync(path.join(OUT,file));assert.deepEqual([bytes.readUInt32BE(16),bytes.readUInt32BE(20)],expected);
  const result={file,bytes:bytes.length,sha256:sha(bytes),viewport:expected,state,sourceBindings:structuredClone(report.sourceBindings),captureScript:report.qaScript,visualAcceptance:'pending actual image review'};
  report.captures.push(result);save();console.log('SAVED',file);return result;
 };
 try{
  await page.goto(new URL('cathay-mansions.html',BASE).href,{waitUntil:'domcontentloaded',timeout:90000});
  const auxiliaryState=async variant=>{
   await page.waitForFunction(v=>{const s=window.cathayMansionsViewer?.getState();return s?.status==='error'||s?.status==='ready'&&s.variant===v;},variant,{timeout:90000});
   const s=await page.evaluate(()=>window.cathayMansionsViewer.getState());assert.equal(s.status,'ready');assert.equal(s.variant,variant);assert.equal(s.modelId,ID);
   assert.equal(s.triangles,manifest.assets[variant].triangles);assert.ok(s.renderedTriangles>0);
   const b=s.framing?.screenBounds;assert.ok(b&&Object.values(b).every(Number.isFinite));
   assert.ok(b.minX>=-.96&&b.maxX<=.96&&b.minY>=-.96&&b.maxY<=.96&&b.minZ>=0&&b.maxZ<=1,JSON.stringify(b));
   return s;
  };
  report.auxiliary.full=await auxiliaryState('full');
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
  const cards=await page.locator('.landmark-card[data-landmark]').evaluateAll(ns=>ns.map(n=>({id:n.dataset.landmark,district:n.closest('.landmark-group').id,links:[...n.querySelectorAll('a')].map(a=>a.getAttribute('href'))})));
  assert.equal(cards.length,COUNT);assert.equal(new Set(cards.map(c=>c.id)).size,COUNT);assert.equal(new Set(cards.map(c=>c.district)).size,16);
  const newCard=cards.find(c=>c.id===ID);assert.equal(newCard.district,'district-310101');assert.ok(newCard.links.includes(`index.html#landmark=${ID}&mode=overview`));
  assert.ok(!newCard.links.some(l=>l.includes('mode=walk')));assert.ok(newCard.links.includes('cathay-mansions.html'));
  const readmes=[readDirectory(path.join(REPO,'README.md')),readDirectory(path.join(PROJECT,'README.md'))];
  for(const d of readmes)sameIds(d.rows.map(r=>r.id),cards.map(c=>c.id));
  const mainResponse=await page.request.get(new URL('index.html',BASE).href);assert.equal(mainResponse.status(),200);
  const projectReadme=await page.request.get(new URL('README.md',BASE).href);assert.equal(projectReadme.status(),200);assert.equal(sha(await projectReadme.body()),readmes[1].sha256);
  await page.fill('#landmark-search','华懋');const searched=await page.locator('.landmark-card[data-landmark]:visible').evaluateAll(ns=>ns.map(n=>n.dataset.landmark));sameIds(searched,[ID]);
  report.directory={cards,readmes,cathaySearch:searched,mainDocumentHTTP:{status:mainResponse.status(),sha256:sha(await mainResponse.body())},projectReadmeHTTP:{status:projectReadme.status(),sha256:sha(await projectReadme.body())},note:'README link fragments are resolved against the local served final main document and actual runtime registry; root README is read from the worktree, not an unpublished remote cache.'};save();

  phase='global';await page.setViewportSize({width:960,height:720});
  await page.goto(new URL(`index.html#landmark=${ID}&mode=overview`,BASE).href,{waitUntil:'domcontentloaded',timeout:90000});
  await page.waitForFunction(()=>window.__SHANGHAI_APP__,null,{timeout:240000});
  const panel=async open=>{
   if((await page.locator('#panel-toggle').getAttribute('aria-expanded')==='true')!==open)await page.locator('#panel-toggle').click();
   // Finish the CSS transition before fitting the production default camera.
   await page.waitForFunction(open=>{const e=document.querySelector('#explore-panel'),r=e.getBoundingClientRect();return open?Math.abs(r.left-20)<.1:e.classList.contains('closed')&&r.right<=1;},open,{timeout:30000});
  };
  const select=async id=>{
   await page.evaluate(async id=>{const a=window.__SHANGHAI_APP__;await a.selectPlace(a.landmarks.find(r=>r.id===id),{mode:'overview'});},id);
   await page.waitForFunction(id=>{const a=window.__SHANGHAI_APP__,s=a.scene.getLandmarkAssetState(id);return s.visible&&s.status==='loaded'&&new URLSearchParams(location.hash.slice(1)).get('landmark')===id;},id,{timeout:180000,polling:500});
  };
  const settle=async requireReplacement=>{
   await page.evaluate(({requireReplacement,ownerId,ownerMacro})=>{window.__qaCathaySteady=()=>{
    const a=window.__SHANGHAI_APP__,m=a.scene.map,b=a.scene.getBuildingBeaconState(),c=a.scene.getCandidateIntegrationState(),v=c.vector.filter(x=>x.active);
    const owner=m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:ownerId}),stream=a.scene.getStreamingState();
    const city={loading:stream.loading,queued:stream.queued,pendingStates:stream.pendingStates,detailLoading:stream.detail.loading,ownerMacroVisible:stream.active.some(r=>r.id===ownerMacro&&r.visible),active:stream.active.map(r=>[r.id,r.visible]),detailActive:stream.detail.active.map(r=>[r.id,r.triangles])};
    const streamReady=city.loading===0&&city.queued===0&&city.pendingStates===0&&city.detailLoading===0;
    const ready=!m.isMoving()&&m.areTilesLoaded()&&streamReady&&b.sourceIds.every(id=>m.isSourceLoaded(id))&&(!requireReplacement||(city.ownerMacroVisible&&v.every(x=>!x.pending&&!x.residualLayer?.busy&&(!x.partialIDs||x.residualLayer?.ready))&&(owner.localModel===true||owner.candidateModel===true)));
    return {ready,owner,city,fingerprint:JSON.stringify({city,beacons:b.revision,shader:requireReplacement?c.shader:null,vector:requireReplacement?v.map(x=>[x.source,x.coveredIDs,x.partialIDs,x.pending,x.residualLayer?.generation]):null})};
   };},{requireReplacement,ownerId:footprint.identity.source_id,ownerMacro:row.owner.macro_id});
   for(let i=0;i<8;i++){
    await page.waitForFunction(()=>window.__qaCathaySteady().ready,null,{timeout:180000,polling:500});const before=await page.evaluate(()=>window.__qaCathaySteady());
    await page.evaluate(async()=>{const m=window.__SHANGHAI_APP__.scene.map;for(let n=0;n<2;n++)await new Promise(resolve=>{m.once('render',resolve);m.triggerRepaint();});});
    const after=await page.evaluate(()=>window.__qaCathaySteady());if(after.ready&&before.fingerprint===after.fingerprint)return after;
   }throw Error('Source/beacon state did not stabilize across two rendered frames');
  };
  const globalState=()=>page.evaluate(({row,nearbyModels,neighbors,contextIds,recessBox})=>{
   const a=window.__SHANGHAI_APP__,m=a.scene.map,asset=a.scene.getLandmarkAssetState(row.id),c=a.scene.getCandidateIntegrationState(),b=a.scene.getBuildingBeaconState();
   const origin=maplibregl.MercatorCoordinate.fromLngLat([121.4737,31.2304],0),anchor=maplibregl.MercatorCoordinate.fromLngLat([row.lng,row.lat],row.altitude||0),unit=origin.meterInMercatorCoordinateUnits(),factor=anchor.meterInMercatorCoordinateUnits()/unit*row.scale;
   const worldCorners=[],angle=row.heading*Math.PI/180,cos=Math.cos(angle),sin=Math.sin(angle),u=anchor.meterInMercatorCoordinateUnits();
   for(const x of [row.bounds_glb.min[0],row.bounds_glb.max[0]])for(const y of [row.bounds_glb.min[1],row.bounds_glb.max[1]])for(const z of [row.bounds_glb.min[2],row.bounds_glb.max[2]]){
    const q=new maplibregl.MercatorCoordinate(anchor.x+(cos*x-sin*z)*row.scale*u,anchor.y+(sin*x+cos*z)*row.scale*u,anchor.z+y*row.scale*u),p=m.transform.coordinatePoint(q,q.toAltitude(),m.transform._pixelMatrix3D);worldCorners.push({x:p.x,y:p.y});
   }
   const preservedNeighborProbes=neighbors.filter(n=>contextIds.includes(n.source_id)).map(n=>{const [x,y]=n.centroid_local_xy_m,q=new maplibregl.MercatorCoordinate(anchor.x+(cos*x+sin*y)*u,anchor.y+(sin*x-cos*y)*u,(n.map_height_m||0)*u),p=m.transform.coordinatePoint(q,q.toAltitude(),m.transform._pixelMatrix3D);return {id:n.source_id,name:n.name,heightM:q.toAltitude(),lngLat:q.toLngLat(),screen:[p.x,p.y],note:'Projection of mapped neighboring roof centre only; actual visible pixels require image inspection.'};});
   const recessGroundProbe=[[recessBox[0],recessBox[1]],[recessBox[2],recessBox[1]],[recessBox[2],recessBox[3]],[recessBox[0],recessBox[3]]].map(([x,y])=>{const q=new maplibregl.MercatorCoordinate(anchor.x+(cos*x+sin*y)*u,anchor.y+(sin*x-cos*y)*u,0),p=m.transform.coordinatePoint(q,0,m.transform._pixelMatrix3D);return {localXY:[x,y],lngLat:q.toLngLat(),screen:[p.x,p.y]};});
   return {recessGroundProbe,hash:location.hash,title:document.querySelector('#location-name').textContent,preservedNeighborProbes,mode:a.mode,viewport:[innerWidth,innerHeight],canvas:[m.getCanvas().clientWidth,m.getCanvas().clientHeight],map:{center:m.getCenter(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),padding:m.getPadding(),elevation:m.transform.elevation,centerClampedToGround:m.getCenterClampedToGround()},asset,nearbyModelStates:nearbyModels.map(r=>({id:r.id,state:a.scene.getLandmarkAssetState(r.id)})),candidate:c,beacons:b,worldCorners,
    expected:{position:[(anchor.x-origin.x)/unit,anchor.z/unit,(anchor.y-origin.y)/unit],minY:anchor.z/unit+row.bounds_glb.min[1]*factor,maxY:anchor.z/unit+row.bounds_glb.max[1]*factor},sourceStates:neighbors.map(n=>({id:n.source_id,name:n.name,sourceLayer:n.source_layer||'building',state:m.getFeatureState({source:'overture-buildings',sourceLayer:n.source_layer||'building',id:n.source_id})})),walkDisabled:document.querySelector('#walk-mode').disabled&&document.querySelector('#start-walk').disabled,renderer:a.scene.getStreamingState().renderer,streaming:a.scene.getStreamingState(),steady:window.__qaCathaySteady?.()};
  },{row,nearbyModels:catalog.models.filter(r=>r.id!==ID&&Math.hypot((r.lng-row.lng)*95000,(r.lat-row.lat)*111000)<300),neighbors,contextIds,recessBox:footprint.geometry.north_central_recess_test_box_local_xy_m});
  const assertAsset=(s,variant)=>{
   const a=s.asset,record=row.assets[variant==='full'?'web':'lod'];assert.equal(s.mode,'overview');assert.equal(a.status,'loaded');assert.ok(a.visible&&a.cityIntegration);assert.equal(a.variant,variant);assert.equal(a.triangles,record.triangles);
   assert.equal(a.verifiedAsset.sha256,record.sha256);assert.equal(a.verifiedAsset.bytes,record.bytes);assert.equal(s.candidate.active.find(r=>r.id===ID)?.assetSha256,record.sha256);
   assert.deepEqual(a.anchor,[row.lng,row.lat]);assert.equal(a.heading,row.heading);assert.equal(a.scale,row.scale);assert.ok(Math.abs(a.rotation[1]+row.heading*Math.PI/180)<1e-10);
   for(let i=0;i<3;i++)assert.ok(Math.abs(a.position[i]-s.expected.position[i])<1e-6);
   if(variant==='full'){assert.ok(Math.abs(a.worldBounds.min[1]-s.expected.minY)<.1);assert.ok(Math.abs(a.worldBounds.max[1]-s.expected.maxY)<.1);}
   const clip=s.candidate.clips.find(c=>c.id===ID);assert.ok(clip);assert.deepEqual(clip.geometry,row.replacement_geometry);assert.deepEqual(clip.source_feature_ids,row.source_feature_ids);assert.deepEqual(clip.owner,row.owner);
   sameIds(clip.source_feature_ids.building,[EXPECTED_SOURCE]);
  };
  const assertFraming=s=>{
   assert.deepEqual(s.canvas,s.viewport);const p=s.map.padding;
   for(const c of s.worldCorners){assert.ok(Number.isFinite(c.x)&&Number.isFinite(c.y));assert.ok(c.x>=p.left-.5&&c.x<=s.viewport[0]-p.right+.5&&c.y>=p.top-.5&&c.y<=s.viewport[1]-p.bottom+.5,JSON.stringify({c,p,viewport:s.viewport}));}
   assert.equal(s.map.centerClampedToGround,false);assert.ok(s.walkDisabled);
  };
  await panel(true);report.global.desktopLayout=await layoutReady(960,720,true);await select(ID);await settle(true);
  report.global.defaultDesktop=await globalState();assertFraming(report.global.defaultDesktop);await capture('global-default-desktop',report.global.defaultDesktop,[960,720]);
  // The south default cannot expose the north negative space. One additional
  // scope view exposes that recess and retains the independently mapped context.
  await panel(false);report.global.northScopeLayout=await layoutReady(960,720,true);
  const northPose={bearing:footprint.camera_obstruction_review.secondary_north_view.bearing,pitch:20};
  await page.evaluate(async({id,pose})=>{const a=window.__SHANGHAI_APP__,place=a.landmarks.find(r=>r.id===id);await a.selectPlace({...place,overviewBearing:pose.bearing,overviewPitch:pose.pitch},{mode:'overview'});},{id:ID,pose:northPose});
  await settle(true);report.global.northRecessContext=await globalState();assertFraming(report.global.northRecessContext);report.global.northRecessContext.scopeCamera=northPose;
  await capture('global-north-recess-context',report.global.northRecessContext,[960,720]);
  await panel(true);await layoutReady(960,720,true);await select(ID);
  // Check only this new building's full/LOD swap; neighbors remain rendered.
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:false,surfaceNormals:true});});
  for(const [variant,zoom,pitch] of [['full',22.5,0],['distant',17.5,45]]){
   await page.evaluate(({row,zoom,pitch,padding})=>{const s=window.__SHANGHAI_APP__.scene;s.map.jumpTo({center:[row.lng,row.lat],zoom,pitch,bearing:row.heading,padding,elevation:0});s.loadLandmarks();},{row,zoom,pitch,padding:ZERO_PADDING});
   await page.waitForFunction(({id,variant})=>{const s=window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id);return s.visible&&s.status==='loaded'&&s.variant===variant;},{id:ID,variant},{timeout:180000,polling:500});
   await settle(true);const state=await globalState();assertAsset(state,variant);report.global[variant==='full'?'full':'lod']=state;save();
  }
  report.global.registry=await page.evaluate(async()=>{
   const a=window.__SHANGHAI_APP__,{resolveNavigationRoute}=await import('./src/landmark-navigation.js'),o={districts:a.districts,landmarks:a.landmarks,bund:{id:'bund',name:'外滩历史建筑群'}};
   return {ids:a.landmarks.map(r=>r.id),districtIds:a.districts.map(r=>r.id),routes:a.landmarks.map(r=>{const x=resolveNavigationRoute('#landmark='+r.id+'&mode=overview',o);return {id:r.id,matched:x.place?.id,error:x.error||null};})};
  });sameIds(report.global.registry.ids,cards.map(c=>c.id));assert.equal(report.global.registry.districtIds.length,16);for(const r of report.global.registry.routes){assert.equal(r.id,r.matched);assert.equal(r.error,null);}
  await select(ID);await settle(true);const pair=await globalState();
  const newClip=pair.candidate.clips.find(c=>c.id===ID);assert.ok(newClip);
  const retained=[];
  for(const item of pair.nearbyModelStates){
   if(!item.state.visible)continue;
   assert.equal(item.state.status,'loaded');const record=catalog.models.find(r=>r.id===item.id),variant=item.state.variant==='full'?'web':'lod';
   assert.equal(item.state.verifiedAsset.sha256,record.assets[variant].sha256);
   const clip=pair.candidate.clips.find(c=>c.id===item.id);assert.ok(clip);assert.deepEqual(clip.source_feature_ids,record.source_feature_ids);assert.deepEqual(clip.geometry,record.replacement_geometry);
   retained.push(item.id);
  }
  const legitimatelyReplaced=new Set(pair.candidate.clips.flatMap(c=>Object.entries(c.source_feature_ids||{}).flatMap(([layer,ids])=>ids.map(id=>layer+'/'+id))));for(const n of pair.sourceStates)if(!legitimatelyReplaced.has(n.sourceLayer+'/'+n.id))assert.notEqual(n.state.candidateModel,true,n.id);
  const excludedContextSources=contextIds.map(id=>{const n=pair.sourceStates.find(s=>s.id===id);assert.ok(n,'Required retained context source must be in independent neighbor inventory');assert.notEqual(n.state.candidateModel,true,id);return n;});
  report.global.neighborSeparation={newClip,excludedContextSources,preservedNeighborProbes:pair.preservedNeighborProbes,nearbyModelStates:pair.nearbyModelStates,visibleExistingModelsVerified:retained,sourceStates:pair.sourceStates,note:'New correction names only the independently reviewed Cathay source. Any visible pre-existing models keep their own asset hashes and clip geometries. Near-neighbor source IDs outside all legitimate replacement sets are not candidate-hidden. localModel state may refer to retained source geometry in a loaded city tile; it does not mean that neighboring feature was removed.'};save();
  await page.setViewportSize({width:390,height:844});await panel(false);report.global.mobileLayout=await layoutReady(390,844,true);
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:true,surfaceNormals:true});});await select(ID);await settle(true);
  report.global.defaultMobile=await globalState();assertFraming(report.global.defaultMobile);await capture('global-default-mobile',report.global.defaultMobile,[390,844]);

  const isolation=footprint.near_group_owner_isolation_requirement;
  report.global.ownerGroupIsolation={requirement:isolation,observations:[]};
  for(const [label,state] of Object.entries({desktop:report.global.defaultDesktop,north:report.global.northRecessContext,full:report.global.full,lod:report.global.lod,mobile:report.global.defaultMobile})){
   const sources=state.candidate.shader.ownerScopedSources||[],active=new Set(state.streaming.detail.active.map(r=>r.id));
   const own=sources.find(r=>r.macro_id===row.owner.macro_id&&r.feature_local_ids.includes(row.owner.feature_local_id));
   const east=sources.find(r=>r.macro_id===row.owner.macro_id&&r.feature_local_ids.includes(2122));
   if(own){sameIds(own.feature_local_ids,isolation.own_group_source_ids);assert.equal(own.triangles,14);sameIds(own.clip_feature_local_ids,[row.owner.feature_local_id]);}
   if(east){sameIds(east.feature_local_ids,isolation.east_group_source_ids);assert.equal(east.triangles,0);sameIds(east.clip_feature_local_ids,[]);}
   report.global.ownerGroupIsolation.observations.push({label,own:own||null,east:east||null,ownVisible:Boolean(own&&active.has(own.id)),eastVisible:Boolean(east&&active.has(east.id))});
  }
  assert.ok(report.global.ownerGroupIsolation.observations.some(r=>['desktop','north','mobile'].includes(r.label)&&r.ownVisible&&r.eastVisible),'Need actual visible own and east near groups in one settled captured/viewed state');
  await Promise.all(responses);
  const eastHTTP=report.citySourceHTTP.find(r=>r.path.endsWith('/'+row.owner.macro_id+'/'+isolation.east_near_tile));assert.ok(eastHTTP,'Actual eastern near asset must be requested');assert.equal(eastHTTP.sha256,isolation.actual_eastern_near_geometry.binding.sha256);assert.equal(eastHTTP.bytes,isolation.actual_eastern_near_geometry.binding.bytes);report.global.ownerGroupIsolation.eastHTTP=eastHTTP;save();

  phase='beacons';await page.setViewportSize({width:320,height:568});await panel(false);report.beaconsResize=await layoutReady(320,568,true);await select(TOUCH_FROM);
  await page.evaluate(padding=>{const a=window.__SHANGHAI_APP__,m=a.scene.map;window.__qaOriginalBounds=m.getMaxBounds()?.toArray()||null;a.scene.setVisualQuality({shadows:false,surfaceNormals:true});m.setMaxBounds(null);m.setCenterClampedToGround(true);m.jumpTo({center:[121.45,31.20],zoom:8,pitch:0,bearing:0,elevation:0,padding});a.scene.refreshBuildingBeacons();},ZERO_PADDING);
  await settle(false);
  const b=await page.evaluate(()=>{
   const a=window.__SHANGHAI_APP__,m=a.scene.map,s=a.scene.getBuildingBeaconState(),rect=selector=>document.querySelector(selector)?.getBoundingClientRect().toJSON();
   return {viewport:[innerWidth,innerHeight],canvas:[m.getCanvas().clientWidth,m.getCanvas().clientHeight],state:s,map:{center:m.getCenter(),zoom:m.getZoom(),padding:m.getPadding(),elevation:m.transform.elevation,maxBounds:m.getMaxBounds()},sources:s.sourceIds.map(id=>({id,count:m.getSource(id).serialize().data.features.length,ids:m.getSource(id).serialize().data.features.map(f=>f.properties.id)})),picks:s.labelPositions.map(p=>({id:p.id,hit:a.scene.pickBuildingBeacon({x:p.x,y:p.y})})),ui:{card:rect('#location-card'),tools:rect('.map-tools'),legend:rect('#building-beacon-legend')},layers:s.layerIds.map(id=>m.getLayer(id).serialize()),allSpritesPresent:s.spriteIds.every(id=>m.hasImage(id))};
  });
  assert.deepEqual(b.viewport,[320,568]);assert.deepEqual(b.canvas,b.viewport);assert.equal(b.map.zoom,8);assert.equal(b.state.count,COUNT);assert.equal(b.state.districtCount,16);assert.equal(b.state.viewportLabelCount,COUNT);assert.equal(b.state.overlapFallbackCount,0);assert.equal(b.state.labelMode,'numbers');assert.equal(b.state.labelPixelSize,12);assert.equal(b.state.anchorPixelSize,20);assert.ok(b.allSpritesPresent);
  sameIds(b.state.ids,cards.map(c=>c.id));sameIds(b.state.labelPositions.map(p=>p.id),b.state.ids);for(const s of b.sources)sameIds(s.ids,b.state.ids);for(const p of b.picks)assert.equal(p.hit,p.id);
  const labels=b.state.labelPositions;for(let i=0;i<labels.length;i++){
   const p=labels[i];assert.ok([22,24].includes(p.width));assert.equal(p.height,20);assert.ok(p.x-p.width/2>=0&&p.x+p.width/2<=320&&p.y-p.height/2>=0&&p.y+p.height/2<=568);
   for(const rect of Object.values(b.ui))if(rect)assert.ok(p.x+p.width/2<=rect.left+.1||p.x-p.width/2>=rect.right-.1||p.y+p.height/2<=rect.top+.1||p.y-p.height/2>=rect.bottom-.1,`UI overlaps ${p.id}`);
   for(const q of labels.slice(i+1))assert.ok(Math.abs(p.x-q.x)>=(p.width+q.width)/2-.1||Math.abs(p.y-q.y)>=(p.height+q.height)/2-.1,`Overlap ${p.id}/${q.id}`);
  }
  report.beacons={...b,quality:'Shadows disabled for marker-only matrix; buildings retained. maxBounds temporarily removed to permit exact zoom8, restored after touch.',compactWidths:[...new Set(labels.map(p=>p.width))]};
  await capture('beacons-320-city-74',report.beacons,[320,568]);
  const before=await page.evaluate(()=>({hash:location.hash,title:document.querySelector('#location-name').textContent,center:window.__SHANGHAI_APP__.scene.map.getCenter()}));assert.equal(new URLSearchParams(before.hash.slice(1)).get('landmark'),TOUCH_FROM);
  const point=labels.find(p=>p.id===ID);assert.ok(point);const touch=await page.context().newCDPSession(page);
  await touch.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1});await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{id:1,x:point.x,y:point.y}]});await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id&&document.querySelector('#location-name').textContent===window.__SHANGHAI_APP__.landmarks.find(r=>r.id===id).name&&window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id).visible&&window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id).status==='loaded',ID,{timeout:60000});await touch.detach();
  const after=await page.evaluate(()=>({hash:location.hash,title:document.querySelector('#location-name').textContent,center:window.__SHANGHAI_APP__.scene.map.getCenter()}));assert.notEqual(before.hash,after.hash);assert.notEqual(before.title,after.title);assert.notDeepEqual(before.center,after.center);
  report.beacons.touch={method:'native CDP touchStart/touchEnd',id:ID,point:[point.x,point.y],before,after,changedDestination:true,targetAssetVisibleAfterTouch:true};
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.map.setMaxBounds(window.__qaOriginalBounds);});
  await Promise.all(responses);assert.equal(report.catalog.http?.sha256,report.catalog.sha256);assert.equal(report.catalog.http?.status,200);assert.deepEqual(report.errors,[]);assert.deepEqual(report.warnings,[]);assert.deepEqual(report.http,[]);
  for(const binding of report.expectedSourceBindings)assert.equal(report.sourceBindings[binding.file.slice(4)]?.sha256,binding.sha256,`Served source does not match freeze: ${binding.file}`);
  for(const binding of [report.catalog,report.manifest,report.footprint,report.qaScript,report.viewerRegistry,...report.expectedSourceBindings])assert.equal(sha(fs.readFileSync(path.join(PROJECT,binding.file))),binding.sha256,`Frozen file changed during QA: ${binding.file}`);for(const binding of staticDirectories)assert.equal(sha(fs.readFileSync(path.join(REPO,binding.file))),binding.sha256,`README changed during QA: ${binding.file}`);
  report.completed=true;report.visualAcceptance='Automated capture/checks complete; final image review is separate and must not be inferred from this flag.';save();console.log('COMPLETE Cathay Mansions incremental browser checks; pixels await review');
 }catch(error){report.failure=error.stack;save();console.error(error);if(process.env.QA_KEEP_ON_FAILURE!=='0'){console.error('Failure scene retained on CDP9223. Do not attach another Playwright controller.');await new Promise(()=>{});}throw error;
 }finally{await browser.close();}
}
if(require.main===module)run().catch(e=>{console.error(e);process.exitCode=1;});
module.exports={readDirectory};
