/* New Wing On incremental QA. One browser/page; no old-model matrix. MIT. */
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const {createHash}=require('crypto');
const PROJECT=path.resolve(__dirname,'../../..'),REPO=path.resolve(PROJECT,'../..');
const OUT=process.env.QA_OUTPUT_DIR||__dirname,BASE=process.env.MODEL_BASE_URL||'http://127.0.0.1:8782/';
const ID='huangpu-new-wing-on-company',OLD='huangpu-old-wing-on-company';
const ZERO_PADDING={top:0,right:0,bottom:0,left:0};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=rel=>JSON.parse(fs.readFileSync(path.join(PROJECT,rel),'utf8'));
const sameIds=(a,b)=>assert.deepEqual([...a].sort(),[...b].sort());

function readDirectory(file){
 const text=fs.readFileSync(file,'utf8'),section=text.split(/^## 按区查看主要建筑\s*$/m)[1]?.split(/^## /m)[0];
 assert.ok(section,`missing district directory: ${file}`);
 const groups=[...section.matchAll(/^### ([^\n]+?)（(\d+)处）\s*$/gm)];
 const rows=[...section.matchAll(/^\|[^\n]*\[查看网页\]\((https:\/\/[^\s)]+#landmark=([^&\s)]+)&mode=(walk|overview))\)[^\n]*$/gm)].map(m=>({id:m[2],url:m[1],mode:m[3]}));
 assert.equal(groups.length,16);assert.equal(rows.length,71);assert.equal(new Set(rows.map(r=>r.id)).size,71);
 assert.equal(groups.reduce((n,g)=>n+Number(g[2]),0),71);
 assert.equal(rows.find(r=>r.id===ID)?.mode,'overview');
 for(let i=0;i<groups.length;i++){
  const part=section.slice(groups[i].index,groups[i+1]?.index??section.length);
  assert.equal((part.match(/\[查看网页\]\(https:[^\n]*?#landmark=/g)||[]).length,Number(groups[i][2]),groups[i][1]);
 }
 return {file:path.relative(REPO,file),sha256:sha(text),districts:groups.map(g=>({name:g[1],count:Number(g[2])})),rows};
}

async function run(){
 // Explicit opt-in prevents preparation or syntax checks from starting WebGL.
 assert.ok(process.argv.includes('--run'),'Preparation only. After assets/catalog/source freeze, run this script with --run.');
 fs.mkdirSync(OUT,{recursive:true});
 const catalogPath='data/candidate-city-integrations.json',catalog=read(catalogPath),row=catalog.models.find(r=>r.id===ID),old=catalog.models.find(r=>r.id===OLD);
 assert.equal(catalog.models.length,31);assert.ok(row&&old);assert.equal(row.navigation.listed,false);
 const footprint=read('data/audit/new-wing-on-company-v1/footprint-review.json');
 const manifest=read(`assets/models/candidates/${ID}/manifest.json`);
 assert.equal(manifest.id,ID);assert.equal(row.owner.feature_local_id,1275);assert.equal(old.owner.feature_local_id,1039);
 sameIds(row.source_feature_ids.building,[footprint.identity.source_id]);
 assert.ok(!row.source_feature_ids.building.includes(footprint.identity.excluded_old_source_id));
 const report={generatedAt:new Date().toISOString(),completed:false,modelId:ID,
  scope:'Only the new building, its separate Old Wing On neighbor, 71-entry directory and 320px beacon capacity increment. One browser and one page, with sequential auxiliary/directory/main-map documents. No replay of the existing 30-model or 60-asset matrix.',
  catalog:{file:catalogPath,sha256:sha(fs.readFileSync(path.join(PROJECT,catalogPath))),models:catalog.models.length},
  manifest:{file:`assets/models/candidates/${ID}/manifest.json`,sha256:sha(fs.readFileSync(path.join(PROJECT,`assets/models/candidates/${ID}/manifest.json`)))},
  sourceBindings:{},http:[],auxiliary:{},directory:{},global:{},beacons:{},captures:[],errors:[],warnings:[]};
 const save=()=>fs.writeFileSync(path.join(OUT,'browser.json'),JSON.stringify(report,null,2)+'\n');
 const existingBrowser=await fetch('http://127.0.0.1:9223/json/version',{signal:AbortSignal.timeout(1000)}).then(r=>r.ok).catch(()=>false);
 assert.equal(existingBrowser,false,'A QA browser is already active. Keep one controller; do not launch a second instance.');
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9223']});
 const page=await browser.newPage({viewport:{width:1200,height:900},hasTouch:true});
 report.browserVersion=browser.version();let phase='auxiliary';
 const responses=[];
 page.on('pageerror',e=>{report.errors.push({phase,message:e.message});save();});
 page.on('console',m=>{if(m.type()==='error')report.errors.push({phase,message:m.text()});if(m.type()==='warning')report.warnings.push({phase,message:m.text()});});
 page.on('response',r=>{
  const u=new URL(r.url());
  if(r.status()>=400)report.http.push({phase,status:r.status(),url:r.url()});
  if(u.origin===new URL(BASE).origin&&u.pathname.startsWith('/src/'))responses.push((async()=>{
   const h=await r.allHeaders();report.sourceBindings[u.pathname.slice(5)]={sha256:h['x-audit-sha256']||sha(await r.body()),origin:h['x-audit-origin']||'HTTP body',status:r.status()};
  })());
 });
 const capture=async(label,state,expected)=>{
  const size=await page.evaluate(()=>[innerWidth,innerHeight]);assert.deepEqual(size,expected);
  await Promise.all(responses);const version=(report.sourceBindings['building-beacons.js']||report.sourceBindings['new-wing-on-company.js']).sha256.slice(0,8);
  const file=`browser-${label}-${version}.png`;await page.screenshot({path:path.join(OUT,file),timeout:120000});
  const bytes=fs.readFileSync(path.join(OUT,file));assert.deepEqual([bytes.readUInt32BE(16),bytes.readUInt32BE(20)],expected);
  const result={file,bytes:bytes.length,sha256:sha(bytes),viewport:expected,state,sourceBindings:structuredClone(report.sourceBindings),visualAcceptance:'pending actual image review'};
  report.captures.push(result);save();console.log('SAVED',file);return result;
 };
 try{
  await page.goto(new URL('new-wing-on-company.html',BASE).href,{waitUntil:'domcontentloaded',timeout:90000});
  const auxiliaryState=async variant=>{
   await page.waitForFunction(v=>{const s=window.newWingOnCompanyViewer?.getState();return s?.status==='error'||s?.status==='ready'&&s.variant===v;},variant,{timeout:90000});
   const s=await page.evaluate(()=>window.newWingOnCompanyViewer.getState());assert.equal(s.status,'ready');assert.equal(s.variant,variant);assert.equal(s.modelId,ID);
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
  await page.setViewportSize({width:390,height:844});report.auxiliary.mobile=await auxiliaryState('full');
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
  assert.equal(cards.length,71);assert.equal(new Set(cards.map(c=>c.id)).size,71);assert.equal(new Set(cards.map(c=>c.district)).size,16);
  const newCard=cards.find(c=>c.id===ID);assert.equal(newCard.district,'district-310101');assert.ok(newCard.links.includes(`index.html#landmark=${ID}&mode=overview`));
  assert.ok(!newCard.links.some(l=>l.includes('mode=walk')));assert.ok(newCard.links.includes('new-wing-on-company.html'));
  const readmes=[readDirectory(path.join(REPO,'README.md')),readDirectory(path.join(PROJECT,'README.md'))];
  for(const d of readmes)sameIds(d.rows.map(r=>r.id),cards.map(c=>c.id));
  const mainResponse=await page.request.get(new URL('index.html',BASE).href);assert.equal(mainResponse.status(),200);
  const projectReadme=await page.request.get(new URL('README.md',BASE).href);assert.equal(projectReadme.status(),200);assert.equal(sha(await projectReadme.body()),readmes[1].sha256);
  await page.fill('#landmark-search','永安');const searched=await page.locator('.landmark-card[data-landmark]:visible').evaluateAll(ns=>ns.map(n=>n.dataset.landmark));sameIds(searched,[ID,OLD]);
  report.directory={cards,readmes,wingOnSearch:searched,mainDocumentHTTP:{status:mainResponse.status(),sha256:sha(await mainResponse.body())},projectReadmeHTTP:{status:projectReadme.status(),sha256:sha(await projectReadme.body())},note:'README link fragments are resolved against the local served final main document and actual runtime registry; root README is read from the worktree, not an unpublished remote cache.'};save();

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
   await page.evaluate(({requireReplacement,ownerId})=>{window.__qaNewWingSteady=()=>{
    const a=window.__SHANGHAI_APP__,m=a.scene.map,b=a.scene.getBuildingBeaconState(),c=a.scene.getCandidateIntegrationState(),v=c.vector.filter(x=>x.active);
    const owner=m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:ownerId});
    const ready=!m.isMoving()&&m.areTilesLoaded()&&b.sourceIds.every(id=>m.isSourceLoaded(id))&&(!requireReplacement||(v.every(x=>!x.pending&&!x.residualLayer?.busy&&(!x.partialIDs||x.residualLayer?.ready))&&(owner.localModel===true||owner.candidateModel===true)));
    return {ready,owner,fingerprint:JSON.stringify({beacons:b.revision,shader:requireReplacement?c.shader:null,vector:requireReplacement?v.map(x=>[x.source,x.coveredIDs,x.partialIDs,x.pending,x.residualLayer?.generation]):null})};
   };},{requireReplacement,ownerId:footprint.identity.source_id});
   for(let i=0;i<8;i++){
    await page.waitForFunction(()=>window.__qaNewWingSteady().ready,null,{timeout:180000,polling:500});const before=await page.evaluate(()=>window.__qaNewWingSteady());
    await page.evaluate(async()=>{const m=window.__SHANGHAI_APP__.scene.map;for(let n=0;n<2;n++)await new Promise(resolve=>{m.once('render',resolve);m.triggerRepaint();});});
    const after=await page.evaluate(()=>window.__qaNewWingSteady());if(after.ready&&before.fingerprint===after.fingerprint)return after;
   }throw Error('Source/beacon state did not stabilize across two rendered frames');
  };
  const globalState=()=>page.evaluate(({row,old,neighbors})=>{
   const a=window.__SHANGHAI_APP__,m=a.scene.map,asset=a.scene.getLandmarkAssetState(row.id),c=a.scene.getCandidateIntegrationState(),b=a.scene.getBuildingBeaconState();
   const origin=maplibregl.MercatorCoordinate.fromLngLat([121.4737,31.2304],0),anchor=maplibregl.MercatorCoordinate.fromLngLat([row.lng,row.lat],row.altitude||0),unit=origin.meterInMercatorCoordinateUnits(),factor=anchor.meterInMercatorCoordinateUnits()/unit*row.scale;
   const worldCorners=[],angle=row.heading*Math.PI/180,cos=Math.cos(angle),sin=Math.sin(angle),u=anchor.meterInMercatorCoordinateUnits();
   for(const x of [row.bounds_glb.min[0],row.bounds_glb.max[0]])for(const y of [row.bounds_glb.min[1],row.bounds_glb.max[1]])for(const z of [row.bounds_glb.min[2],row.bounds_glb.max[2]]){
    const q=new maplibregl.MercatorCoordinate(anchor.x+(cos*x-sin*z)*row.scale*u,anchor.y+(sin*x+cos*z)*row.scale*u,anchor.z+y*row.scale*u),p=m.transform.coordinatePoint(q,q.toAltitude(),m.transform._pixelMatrix3D);worldCorners.push({x:p.x,y:p.y});
   }
   return {hash:location.hash,title:document.querySelector('#location-name').textContent,mode:a.mode,viewport:[innerWidth,innerHeight],canvas:[m.getCanvas().clientWidth,m.getCanvas().clientHeight],map:{center:m.getCenter(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),padding:m.getPadding(),elevation:m.transform.elevation,centerClampedToGround:m.getCenterClampedToGround()},asset,oldAsset:a.scene.getLandmarkAssetState(old.id),candidate:c,beacons:b,worldCorners,
    expected:{position:[(anchor.x-origin.x)/unit,anchor.z/unit,(anchor.y-origin.y)/unit],minY:anchor.z/unit+row.bounds_glb.min[1]*factor,maxY:anchor.z/unit+row.bounds_glb.max[1]*factor},sourceStates:neighbors.map(n=>({id:n.source_id,name:n.name,state:m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:n.source_id})})),walkDisabled:document.querySelector('#walk-mode').disabled&&document.querySelector('#start-walk').disabled,renderer:a.scene.getStreamingState().renderer,steady:window.__qaNewWingSteady?.()};
  },{row,old,neighbors:footprint.exclusions.all_macro_neighbors_within_65m});
  const assertAsset=(s,variant)=>{
   const a=s.asset,record=row.assets[variant==='full'?'web':'lod'];assert.equal(s.mode,'overview');assert.equal(a.status,'loaded');assert.ok(a.visible&&a.cityIntegration);assert.equal(a.variant,variant);assert.equal(a.triangles,record.triangles);
   assert.equal(a.verifiedAsset.sha256,record.sha256);assert.equal(a.verifiedAsset.bytes,record.bytes);assert.equal(s.candidate.active.find(r=>r.id===ID)?.assetSha256,record.sha256);
   assert.deepEqual(a.anchor,[row.lng,row.lat]);assert.equal(a.heading,row.heading);assert.equal(a.scale,row.scale);assert.ok(Math.abs(a.rotation[1]+row.heading*Math.PI/180)<1e-10);
   for(let i=0;i<3;i++)assert.ok(Math.abs(a.position[i]-s.expected.position[i])<1e-6);
   if(variant==='full'){assert.ok(Math.abs(a.worldBounds.min[1]-s.expected.minY)<.1);assert.ok(Math.abs(a.worldBounds.max[1]-s.expected.maxY)<.1);}
   const clip=s.candidate.clips.find(c=>c.id===ID);assert.ok(clip);assert.deepEqual(clip.geometry,row.replacement_geometry);assert.deepEqual(clip.source_feature_ids,row.source_feature_ids);assert.deepEqual(clip.owner,row.owner);
   assert.ok(!clip.source_feature_ids.building.includes(footprint.identity.excluded_old_source_id));
  };
  const assertFraming=s=>{
   assert.deepEqual(s.canvas,s.viewport);const p=s.map.padding;
   for(const c of s.worldCorners){assert.ok(Number.isFinite(c.x)&&Number.isFinite(c.y));assert.ok(c.x>=p.left-.5&&c.x<=s.viewport[0]-p.right+.5&&c.y>=p.top-.5&&c.y<=s.viewport[1]-p.bottom+.5,JSON.stringify({c,p,viewport:s.viewport}));}
   assert.equal(s.map.centerClampedToGround,false);assert.ok(s.walkDisabled);
  };
  await panel(true);await select(ID);await settle(true);
  report.global.defaultDesktop=await globalState();assertFraming(report.global.defaultDesktop);await capture('global-default-desktop',report.global.defaultDesktop,[960,720]);
  // Check only this new building's full/LOD swap; neighbors remain rendered.
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:false,surfaceNormals:true});});
  for(const [variant,zoom,pitch] of [['full',22.5,0],['distant',17.5,45]]){
   await page.evaluate(({row,zoom,pitch,padding})=>{const s=window.__SHANGHAI_APP__.scene;s.map.jumpTo({center:[row.lng,row.lat],zoom,pitch,bearing:row.heading,padding,elevation:0});s.loadLandmarks();},{row,zoom,pitch,padding:ZERO_PADDING});
   await page.waitForFunction(({id,variant})=>{const s=window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id);return s.visible&&s.status==='loaded'&&s.variant===variant;},{id:ID,variant},{timeout:180000,polling:500});
   const state=await globalState();assertAsset(state,variant);report.global[variant==='full'?'full':'lod']=state;save();
  }
  report.global.registry=await page.evaluate(async()=>{
   const a=window.__SHANGHAI_APP__,{resolveNavigationRoute}=await import('./src/landmark-navigation.js'),o={districts:a.districts,landmarks:a.landmarks,bund:{id:'bund',name:'外滩历史建筑群'}};
   return {ids:a.landmarks.map(r=>r.id),districtIds:a.districts.map(r=>r.id),routes:a.landmarks.map(r=>{const x=resolveNavigationRoute('#landmark='+r.id+'&mode=overview',o);return {id:r.id,matched:x.place?.id,error:x.error||null};})};
  });sameIds(report.global.registry.ids,cards.map(c=>c.id));assert.equal(report.global.registry.districtIds.length,16);for(const r of report.global.registry.routes){assert.equal(r.id,r.matched);assert.equal(r.error,null);}
  await select(ID);await settle(true);const pair=await globalState();
  assert.ok(pair.oldAsset.visible);assert.equal(pair.oldAsset.status,'loaded');const oldRecord=old.assets[pair.oldAsset.variant==='full'?'web':'lod'];assert.equal(pair.oldAsset.verifiedAsset.sha256,oldRecord.sha256);
  const oldClip=pair.candidate.clips.find(c=>c.id===OLD),newClip=pair.candidate.clips.find(c=>c.id===ID);assert.ok(oldClip&&newClip);assert.deepEqual(oldClip.source_feature_ids,old.source_feature_ids);assert.deepEqual(oldClip.geometry,old.replacement_geometry);
  const legitimatelyReplaced=new Set(pair.candidate.clips.flatMap(c=>c.source_feature_ids?.building||[]));for(const n of pair.sourceStates)if(!legitimatelyReplaced.has(n.id))assert.notEqual(n.state.candidateModel,true,n.id);
  report.global.neighborSeparation={oldAsset:pair.oldAsset,oldClip,newClip,sourceStates:pair.sourceStates,note:'Distinct owner IDs, assets and clip geometries. localModel state may refer to retained source geometry in a loaded city tile; it does not mean the neighboring feature was removed.'};save();
  await page.setViewportSize({width:390,height:844});await panel(false);
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:true,surfaceNormals:true});});await select(ID);await settle(true);
  report.global.defaultMobile=await globalState();assertFraming(report.global.defaultMobile);await capture('global-default-mobile',report.global.defaultMobile,[390,844]);

  phase='beacons';await page.setViewportSize({width:320,height:568});await panel(false);await select(OLD);
  await page.evaluate(padding=>{const a=window.__SHANGHAI_APP__,m=a.scene.map;window.__qaOriginalBounds=m.getMaxBounds()?.toArray()||null;a.scene.setVisualQuality({shadows:false,surfaceNormals:true});m.setMaxBounds(null);m.setCenterClampedToGround(true);m.jumpTo({center:[121.45,31.20],zoom:8,pitch:0,bearing:0,elevation:0,padding});a.scene.refreshBuildingBeacons();},ZERO_PADDING);
  await settle(false);
  const b=await page.evaluate(()=>{
   const a=window.__SHANGHAI_APP__,m=a.scene.map,s=a.scene.getBuildingBeaconState(),rect=selector=>document.querySelector(selector)?.getBoundingClientRect().toJSON();
   return {viewport:[innerWidth,innerHeight],canvas:[m.getCanvas().clientWidth,m.getCanvas().clientHeight],state:s,map:{center:m.getCenter(),zoom:m.getZoom(),padding:m.getPadding(),elevation:m.transform.elevation,maxBounds:m.getMaxBounds()},sources:s.sourceIds.map(id=>({id,count:m.getSource(id).serialize().data.features.length,ids:m.getSource(id).serialize().data.features.map(f=>f.properties.id)})),picks:s.labelPositions.map(p=>({id:p.id,hit:a.scene.pickBuildingBeacon({x:p.x,y:p.y})})),ui:{card:rect('#location-card'),tools:rect('.map-tools'),legend:rect('#building-beacon-legend')},layers:s.layerIds.map(id=>m.getLayer(id).serialize()),allSpritesPresent:s.spriteIds.every(id=>m.hasImage(id))};
  });
  assert.deepEqual(b.viewport,[320,568]);assert.deepEqual(b.canvas,b.viewport);assert.equal(b.map.zoom,8);assert.equal(b.state.count,71);assert.equal(b.state.districtCount,16);assert.equal(b.state.viewportLabelCount,71);assert.equal(b.state.overlapFallbackCount,0);assert.equal(b.state.labelMode,'numbers');assert.equal(b.state.labelPixelSize,12);assert.equal(b.state.anchorPixelSize,20);assert.ok(b.allSpritesPresent);
  sameIds(b.state.ids,cards.map(c=>c.id));sameIds(b.state.labelPositions.map(p=>p.id),b.state.ids);for(const s of b.sources)sameIds(s.ids,b.state.ids);for(const p of b.picks)assert.equal(p.hit,p.id);
  const labels=b.state.labelPositions;for(let i=0;i<labels.length;i++){
   const p=labels[i];assert.ok([22,24].includes(p.width));assert.equal(p.height,20);assert.ok(p.x-p.width/2>=0&&p.x+p.width/2<=320&&p.y-p.height/2>=0&&p.y+p.height/2<=568);
   for(const rect of Object.values(b.ui))if(rect)assert.ok(p.x+p.width/2<=rect.left+.1||p.x-p.width/2>=rect.right-.1||p.y+p.height/2<=rect.top+.1||p.y-p.height/2>=rect.bottom-.1,`UI overlaps ${p.id}`);
   for(const q of labels.slice(i+1))assert.ok(Math.abs(p.x-q.x)>=(p.width+q.width)/2-.1||Math.abs(p.y-q.y)>=(p.height+q.height)/2-.1,`Overlap ${p.id}/${q.id}`);
  }
  report.beacons={...b,quality:'Shadows disabled for marker-only matrix; buildings retained. maxBounds temporarily removed to permit exact zoom8, restored after touch.',compactWidths:[...new Set(labels.map(p=>p.width))]};
  await capture('beacons-320-city-71',report.beacons,[320,568]);
  const before=await page.evaluate(()=>({hash:location.hash,title:document.querySelector('#location-name').textContent,center:window.__SHANGHAI_APP__.scene.map.getCenter()}));assert.equal(new URLSearchParams(before.hash.slice(1)).get('landmark'),OLD);
  const point=labels.find(p=>p.id===ID);assert.ok(point);const touch=await page.context().newCDPSession(page);
  await touch.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1});await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{id:1,x:point.x,y:point.y}]});await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id&&document.querySelector('#location-name').textContent===window.__SHANGHAI_APP__.landmarks.find(r=>r.id===id).name,ID,{timeout:30000});await touch.detach();
  const after=await page.evaluate(()=>({hash:location.hash,title:document.querySelector('#location-name').textContent,center:window.__SHANGHAI_APP__.scene.map.getCenter()}));assert.notEqual(before.hash,after.hash);assert.notEqual(before.title,after.title);assert.notDeepEqual(before.center,after.center);
  report.beacons.touch={method:'native CDP touchStart/touchEnd',id:ID,point:[point.x,point.y],before,after,changedDestination:true};
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.map.setMaxBounds(window.__qaOriginalBounds);});
  await Promise.all(responses);assert.deepEqual(report.errors,[]);assert.deepEqual(report.warnings,[]);assert.deepEqual(report.http,[]);
  report.completed=true;report.visualAcceptance='Automated capture/checks complete; final image review is separate and must not be inferred from this flag.';save();console.log('COMPLETE New Wing On incremental browser checks; pixels await review');
 }catch(error){report.failure=error.stack;save();console.error(error);if(process.env.QA_KEEP_ON_FAILURE!=='0'){console.error('Failure scene retained on CDP9223. Do not attach another Playwright controller.');await new Promise(()=>{});}throw error;
 }finally{await browser.close();}
}
if(require.main===module)run().catch(e=>{console.error(e);process.exitCode=1;});
module.exports={readDirectory};
