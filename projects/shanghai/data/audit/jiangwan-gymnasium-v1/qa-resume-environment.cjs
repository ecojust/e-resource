/* Immutable same-host recovery for baseline HTTP/auth failure and explicit response-reader revalidation. MIT. */
module.exports=async function(ctx){
 const {page,report,save,PROJECT,REPO,OUT,BASE,ID,TOUCH_FROM,COUNT,EXPECTED_CLIP_TRIANGLES,EXPECTED_SOURCE,CONFIG,CLIP_CAPACITY,ZERO_PADDING,sha,sameIds,assertClipCapacity,fs,path,assert,catalog,row,footprint,manifest,neighbors,contextIds,staticDirectories,verifyFrozenInputs,cards}=ctx;
 const {panel,select,settle,globalState,assertAsset,assertFraming,assertNearGroups,layoutReady}=ctx.helpers;
 const continuationContext=ctx,cardsFromReport=()=>report.directory.cards.map(c=>c.id);
 const seedFile=path.join(OUT,'env-recovery-input.json');assert.equal(sha(fs.readFileSync(seedFile)),'1bd2b52bd12aa4171e829d3b2eb0ee989d67f9779870e32d60bc38ff96ab71ee');const seed=JSON.parse(fs.readFileSync(seedFile));
 assert.equal(seed.runGeneratedAt,report.generatedAt);assert.equal(seed.retainedHostPid,process.pid);assert.equal(seed.server.sha256,sha(fs.readFileSync(seed.server.file)));
 const assertRecoveredErrors=()=>{for(const key of ['errors','warnings','http','responseCheckFailures'])assert.deepEqual(report[key],seed.original[key],'New unresolved error in '+key);};
 const drainResponses=async()=>{let count;do{count=ctx.responses.length;await Promise.all(ctx.responses);}while(count!==ctx.responses.length);assertRecoveredErrors();};
 const provenance={file:path.relative(PROJECT,ctx.controlBinding.module),sha256:ctx.controlBinding.moduleSha256,controlSha256:ctx.controlBinding.controlSha256};
 const capture=async(label,state,expected)=>{
  assert.deepEqual(await page.evaluate(()=>[innerWidth,innerHeight]),expected);await drainResponses();
  const sourceVersion=(report.sourceBindings['building-beacons.js']||report.sourceBindings['jiangwan-gymnasium.js']).sha256.slice(0,8),version=sourceVersion+'-'+sha(provenance.sha256+provenance.controlSha256+report.catalog.sha256+report.manifest.sha256).slice(0,8),file=`browser-${label}-${version}.png`;
  assert.ok(!fs.existsSync(path.join(OUT,file)));await page.screenshot({path:path.join(OUT,file),timeout:120000});const bytes=fs.readFileSync(path.join(OUT,file));assert.deepEqual([bytes.readUInt32BE(16),bytes.readUInt32BE(20)],expected);
  const result={label,file,bytes:bytes.length,sha256:sha(bytes),viewport:expected,state:structuredClone(state),sourceBindings:structuredClone(report.sourceBindings),captureScript:provenance,visualAcceptance:'pending actual image review'};report.captures.push(result);save();console.log('SAVED',file);return result;
 };
 ctx.helpers.capture=capture;ctx.drainResponses=drainResponses;
 const recovery={...seed,input:{file:'env-recovery-input.json',sha256:sha(fs.readFileSync(seedFile))},module:provenance,at:new Date().toISOString(),retries:[],unresolved_application_errors:null};
 report.environmentRecovery=recovery;save();ctx.setPhase('environment-recovery');
 for(const source of seed.bodyReverificationSources){
  const data=fs.readFileSync(source.cache_path);assert.equal(sha(data),source.sha256);assert.equal(data.length,source.bytes);assert.equal(require('node:crypto').createHash('sha1').update(Buffer.concat([Buffer.from('blob '+data.length+'\0'),data])).digest('hex'),source.git_blob);
  const retry=await page.evaluate(async rel=>{const response=await fetch(new URL(rel,location.href),{cache:'reload'}),bytes=await response.arrayBuffer(),digest=await crypto.subtle.digest('SHA-256',bytes);return {url:response.url,status:response.status,bytes:bytes.byteLength,sha256:[...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join(''),origin:response.headers.get('x-audit-origin'),method:'Actual fetch and ArrayBuffer SHA-256 in the retained browser page; no second controller.'};},source.path);
  assert.equal(retry.status,200);assert.equal(retry.bytes,source.bytes);assert.equal(retry.sha256,source.sha256);recovery.retries.push({...retry,path:source.path,git_blob:source.git_blob});save();
 }
 await drainResponses();
 await page.setViewportSize({width:960,height:720});await panel(true);await layoutReady(960,720,true);await select(ID);
 await page.evaluate(({row,padding})=>{const s=window.__SHANGHAI_APP__.scene;s.setVisualQuality({shadows:false,surfaceNormals:true});s.map.jumpTo({center:[row.lng,row.lat],zoom:15.5,pitch:45,bearing:row.heading,padding,elevation:0});s.loadLandmarks();},{row,padding:ZERO_PADDING});
 await settle(true);
 recovery.reloadedScene=await page.evaluate(()=>({stream:window.__SHANGHAI_APP__.scene.getStreamingState(),lighting:window.__SHANGHAI_APP__.scene.getRealismState().lighting,glError:window.__SHANGHAI_APP__.scene.map.painter.context.gl.getError(),hash:location.hash}));
 assert.ok(recovery.reloadedScene.stream.active.some(r=>r.id==='14-13723-6690'&&r.visible),'Previously failed neighboring macro must now load and render through the actual streamer');
 for(const key of ['loading','queued','pendingStates'])assert.equal(recovery.reloadedScene.stream[key],0);assert.equal(recovery.reloadedScene.glError,0);
 const recoveredLOD=await globalState();assertAsset(recoveredLOD,'distant');recovery.reloadedScene.lodState=recoveredLOD;report.global.lod=recoveredLOD;
 recovery.sameHostSuccessfulRetry=true;recovery.unresolved_application_errors=0;assertRecoveredErrors();save();
 const writeRecovery=()=>{assertRecoveredErrors();fs.writeFileSync(path.join(OUT,'env-recovery.json'),JSON.stringify(recovery,null,2)+'\n');report.environmentRecoveryBinding={file:'env-recovery.json',sha256:sha(fs.readFileSync(path.join(OUT,'env-recovery.json')))};save();};
 const finalizeChecks=async()=>{
  await drainResponses();await verifyFrozenInputs();assertRecoveredErrors();assert.equal(report.catalog.http?.sha256,report.catalog.sha256);assert.equal(report.originalSourceVerification?.length,CONFIG.source_bindings.length);
  assert.equal(report.auxiliary.downloads?.length,4);sameIds(report.auxiliary.downloads.map(r=>r.role),['raw','full','lod','native']);for(const download of report.auxiliary.downloads){assert.equal(download.status,200);assert.equal(download.sha256,manifest.assets[download.role].sha256);assert.equal(download.bytes,manifest.assets[download.role].bytes);}
  assert.equal(report.directory.cards?.length,COUNT);sameIds(report.global.registry?.ids,cardsFromReport());
  assert.equal(report.global.registry.routes.length,COUNT);for(const r of report.global.registry.routes){assert.equal(r.id,r.matched);assert.equal(r.error,null);}
  assert.ok(report.global.full&&report.global.lod&&report.global.neighborSeparation&&report.global.webglAfterModelChecks,'The new model full/LOD, neighbor and GPU checks must complete');continuationContext.helpers.assertAsset(report.global.full,'full');continuationContext.helpers.assertAsset(report.global.lod,'distant');assert.equal(report.global.webglAfterModelChecks.glError,0);assert.equal(report.global.webglAfterModelChecks.contextLost,false);assertClipCapacity(report.global.webglAfterModelChecks.clipping);
  for(const n of report.global.neighborSeparation.excludedContextSources)if(!n.legitimateExistingReplacement)assert.notEqual(n.state.candidateModel,true,n.id);

  for(const label of ['auxiliary-desktop-full','auxiliary-desktop-lod','auxiliary-mobile-full','global-default-desktop','global-default-mobile','beacons-320-city-79'])assert.ok(report.captures.some(c=>c.label===label),'Required capture missing: '+label);
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
  if(report.beacons.postTouchCardComparison?.requiresAdditionalCityCapture){assert.ok(report.beacons.postTouchCity);continuationContext.helpers.assertDenseBeacons(report.beacons.postTouchCity);assert.ok(report.captures.some(c=>c.label==='beacons-320-gymnasium-city-79'));}
  sameIds(report.cardTitleCapacity.rows.map(r=>r.id),cardsFromReport());sameIds(report.cardTitleCapacity.positions.map(r=>r.id),cardsFromReport());for(const hit of report.cardTitleCapacity.hits)assert.equal(hit.id,hit.hit);
  for(const b of report.expectedSourceBindings)assert.equal(report.sourceBindings[b.file.slice(4)]?.sha256,b.sha256,b.file);
  report.completed=true;report.visualAcceptance='Automated checks and required side/entry pixel decisions are complete; all PNGs still require separate QA/root review.';save();
 };
 ctx.validateContinuationResult=async()=>{await finalizeChecks();writeRecovery();};
  await page.setViewportSize({width:390,height:844});await panel(false);report.global.mobileLayout=await layoutReady(390,844,true);
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:true,surfaceNormals:true});});await select(ID);await settle(true);
  report.global.defaultMobile=await globalState();assert.ok(['full','distant'].includes(report.global.defaultMobile.asset.variant));assertAsset(report.global.defaultMobile,report.global.defaultMobile.asset.variant);assertFraming(report.global.defaultMobile);await capture('global-default-mobile',report.global.defaultMobile,[390,844]);

  report.global.webglAfterModelChecks=await page.evaluate(()=>{const a=window.__SHANGHAI_APP__,gl=a.scene.map.painter.context.gl;return {glError:gl.getError(),contextLost:gl.isContextLost(),clipping:a.scene.getCandidateIntegrationState().shader,note:'Read after actual desktop, explicit near/side/entry, full/LOD and mobile model rendering with the frozen production clip texture.'};});
  assert.equal(report.global.webglAfterModelChecks.glError,0);assert.equal(report.global.webglAfterModelChecks.contextLost,false);assertClipCapacity(report.global.webglAfterModelChecks.clipping);assert.ok(report.global.webglAfterModelChecks.clipping.triangles>0);
  await drainResponses();
  report.global.ownerGroupIsolation={groups:CONFIG.near_groups.map((required,index)=>{const observed=Object.entries(report.global.visualViews).flatMap(([key,state])=>(state.requiredNearGroups||[]).filter(g=>g.index===index).map(g=>({view:key,group:g.group})));assert.ok(observed.length,'Independent near group must be exercised by at least one actual visual view');const nearHTTP=report.citySourceHTTP.find(r=>r.path===required.near_path.replace(/^projects\/shanghai\//,''));assert.ok(nearHTTP);assert.equal(nearHTTP.sha256,required.sha256);assert.equal(nearHTTP.bytes,required.bytes);return {required,observed,nearHTTP};}),note:'Actual near-group owners and source HTTP bytes are checked against independent frozen mapping. Group-wide texture binding is not a claim that every owner is individually clipped.'};save();
  ctx.setPhase('beacons');await page.setViewportSize({width:320,height:568});await panel(false);report.beaconsResize=await layoutReady(320,568,true);await select(TOUCH_FROM);
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
  await capture('beacons-320-city-79',report.beacons,[320,568]);
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
  report.beacons.postTouchLayout={...postTouchLayout,note:'Actual selected Jiangwan Gymnasium overview after native touch. Only the geographically visible labels are checked here; this does not claim that all current anchors are in this close viewport.'};
  const testedCardTop=Math.min(b.ui.card.top,report.beacons.worstTitleViewport?.scene.ui.card.top??Infinity);
  const requiresLargerCardProof=postTouchLayout.ui.card.top<testedCardTop-.5;
  report.beacons.postTouchCardComparison={beforeTop:b.ui.card.top,afterTop:postTouchLayout.ui.card.top,testedMinimumTop:testedCardTop,afterUsesMoreVerticalSpace:postTouchLayout.ui.card.top<b.ui.card.top-.5,requiresAdditionalCityCapture:requiresLargerCardProof};
  if(requiresLargerCardProof){
   await page.evaluate(padding=>{const a=window.__SHANGHAI_APP__,m=a.scene.map;a.scene.setVisualQuality({shadows:false,surfaceNormals:true});m.setCenterClampedToGround(true);m.jumpTo({center:[121.45,31.20],zoom:8,pitch:0,bearing:0,elevation:0,padding});a.scene.refreshBuildingBeacons();},ZERO_PADDING);
   await settle(false);report.beacons.postTouchCity=await beaconScene();assertDenseBeacons(report.beacons.postTouchCity);
   await capture('beacons-320-gymnasium-city-79',report.beacons.postTouchCity,[320,568]);
  }else report.beacons.postTouchCardComparison.additionalCityCapture='Not needed: the selected target card leaves at least the free space already validated by the actual dense viewport captures.';
  await page.evaluate(()=>{window.__SHANGHAI_APP__.scene.map.setMaxBounds(window.__qaOriginalBounds);});
  await drainResponses();assert.equal(report.catalog.http?.sha256,report.catalog.sha256);assert.equal(report.catalog.http?.status,200);assertRecoveredErrors();
  for(const binding of report.expectedSourceBindings)assert.equal(report.sourceBindings[binding.file.slice(4)]?.sha256,binding.sha256,`Served source does not match freeze: ${binding.file}`);
  for(const binding of [report.catalog,report.manifest,report.footprint,report.qaScript,report.viewerRegistry,report.placementBinding,report.qaContract,...report.expectedSourceBindings,...report.documentBindings])assert.equal(sha(fs.readFileSync(path.join(PROJECT,binding.file))),binding.sha256,`Frozen file changed during QA: ${binding.file}`);for(const binding of staticDirectories)assert.equal(sha(fs.readFileSync(path.join(REPO,binding.file))),binding.sha256,`README changed during QA: ${binding.file}`);
  await finalizeChecks();console.log('COMPLETE Jiangwan Gymnasium incremental browser checks; final PNG review remains separate');

 recovery.finalScene=await page.evaluate(()=>({stream:window.__SHANGHAI_APP__.scene.getStreamingState(),hash:location.hash,asset:window.__SHANGHAI_APP__.scene.getLandmarkAssetState('yangpu-jiangwan-gymnasium'),glError:window.__SHANGHAI_APP__.scene.map.painter.context.gl.getError()}));
 assert.equal(recovery.finalScene.glError,0);writeRecovery();return {completed:true};
};
