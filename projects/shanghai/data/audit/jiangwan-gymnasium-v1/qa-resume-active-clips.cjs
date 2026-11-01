/* Same retained host. Correct a QA global-versus-active row-count assertion; no production input changes. MIT. */
module.exports=async function(ctx){
 const {page,report,save,PROJECT,REPO,OUT,BASE,ID,TOUCH_FROM,COUNT,EXPECTED_CLIP_TRIANGLES,EXPECTED_SOURCE,CONFIG,CLIP_CAPACITY,ZERO_PADDING,sha,sameIds,assertClipCapacity,fs,path,assert,catalog,row,footprint,manifest,neighbors,contextIds,staticDirectories,verifyFrozenInputs,finalizeChecks,drainResponses,cards}=ctx;
 const {panel,select,settle,globalState,assertFraming,assertNearGroups,layoutReady,capture}=ctx.helpers;
 const continuationContext=ctx;
 const catalogueRows=await page.evaluate(async({models})=>{
  const THREE=await import('./vendor/three.module.js');const origin=maplibregl.MercatorCoordinate.fromLngLat([121.4737,31.2304]),unit=origin.meterInMercatorCoordinateUnits();
  const records=new Map();for(const model of models){if(model.replacement_geometry)records.set(model.id,{id:model.id,geometry:model.replacement_geometry,owner:model.owner,owners:model.owners});if(model.site_replacement){const q=model.site_replacement;if(records.has(q.id)&&JSON.stringify(records.get(q.id).geometry)!==JSON.stringify(q.geometry))throw Error('Shared site id with different geometry');records.set(q.id,q);}}
  const rows=[];for(const [id,clip]of records){let count=0;for(const rings of clip.geometry.type==='Polygon'?[clip.geometry.coordinates]:clip.geometry.coordinates){const contour=rings.map(r=>r.slice(0,-1).map(p=>{const q=maplibregl.MercatorCoordinate.fromLngLat(p);return new THREE.Vector2((q.x-origin.x)/unit,(q.y-origin.y)/unit);}));count+=THREE.ShapeUtils.triangulateShape(contour[0],contour.slice(1)).length*(clip.owners?.length||1);}rows.push({id,triangles:count});}return {rows,total:rows.reduce((n,r)=>n+r.triangles,0),method:'CPU triangulation of final catalogue geometry using the shipped THREE triangulator in the existing page; no historical GLB loaded and no second WebGL context created.'};
 },{models:catalog.models});assert.equal(catalogueRows.total,CONFIG.expected_global_clip_triangles);const clipRows=Object.fromEntries(catalogueRows.rows.map(r=>[r.id,r.triangles]));
 report.qaCorrection={reason:'The first QA assertion incorrectly equated all-catalogue202 rows to the current visible correction set. The existing runtime intentionally loads only nearby candidate clips. The default view actually has stadium45 plus gym10, totaling55. No model/production code change was needed.',initialObservedActiveRows:report.global.defaultDesktop.candidate.shader.triangles,globalCatalogueRows:catalogueRows.total,capacity:CLIP_CAPACITY,catalogueRows,correctedRule:'Each captured asset state compares shader.triangles with the sum of its actual active clip IDs; the full catalogue count is a separate metadata-only calculation. Actual shader compilation/rendering uses the224-row capacity.'};save();
  const assertAsset=(s,variant)=>{
   assertClipCapacity(s.candidate.shader);
   const a=s.asset,record=row.assets[variant==='full'?'web':'lod'];assert.equal(s.mode,'overview');assert.equal(a.status,'loaded');assert.ok(a.visible&&a.cityIntegration);assert.equal(a.variant,variant);assert.equal(a.triangles,record.triangles);
   assert.equal(a.verifiedAsset.sha256,record.sha256);assert.equal(a.verifiedAsset.bytes,record.bytes);assert.equal(s.candidate.active.find(r=>r.id===ID)?.assetSha256,record.sha256);
   assert.deepEqual(a.anchor,[row.lng,row.lat]);assert.equal(a.heading,row.heading);assert.equal(a.scale,row.scale);assert.ok(Math.abs(a.rotation[1]+row.heading*Math.PI/180)<1e-10);
   for(let i=0;i<3;i++)assert.ok(Math.abs(a.position[i]-s.expected.position[i])<1e-6);
   if(variant==='full'){assert.ok(Math.abs(a.worldBounds.min[1]-s.expected.minY)<.1);assert.ok(Math.abs(a.worldBounds.max[1]-s.expected.maxY)<.1);}
   const clip=s.candidate.clips.find(c=>c.id===ID);assert.ok(clip);assert.deepEqual(clip.geometry,row.replacement_geometry);assert.deepEqual(clip.source_feature_ids,row.source_feature_ids);assert.deepEqual(clip.owner,row.owner);
   sameIds(clip.source_feature_ids.building,CONFIG.source_feature_ids.building);if(row.site_replacement){const site=s.candidate.clips.find(c=>c.id===row.site_replacement.id);assert.ok(site,'Expected site clip missing');for(const key of ['geometry','owner','source_feature_ids'])assert.deepEqual(site[key],row.site_replacement[key],key);}const expectedActive=s.candidate.clips.reduce((n,c)=>{assert.ok(clipRows[c.id]!==undefined,'Unknown active clip '+c.id);return n+clipRows[c.id];},0);assert.equal(s.candidate.shader.triangles,expectedActive,'Visible candidate clipping must match only the active correction records');assert.ok(expectedActive>=EXPECTED_CLIP_TRIANGLES&&expectedActive<=CONFIG.expected_global_clip_triangles);
  };
  ctx.helpers.assertAsset=assertAsset;
  report.global.defaultDesktop=await globalState();assert.ok(['full','distant'].includes(report.global.defaultDesktop.asset.variant));assertAsset(report.global.defaultDesktop,report.global.defaultDesktop.asset.variant);assertFraming(report.global.defaultDesktop);await capture('global-default-desktop',report.global.defaultDesktop,[960,720]);
  await page.setViewportSize({width:1200,height:900});await panel(false);report.global.nearLayout=await layoutReady(1200,900,true);
  report.global.visualViews={};report.global.visualAcceptance={};
  const applyVisualCamera=async camera=>{await page.evaluate(({camera,padding})=>{const s=window.__SHANGHAI_APP__.scene;s.setVisualQuality({shadows:false,surfaceNormals:true});s.map.setCenterClampedToGround(false);s.map.jumpTo({...camera,padding});s.loadLandmarks();},{camera,padding:ZERO_PADDING});await settle(true);};
  const validateVisualState=(view,state)=>{assertAsset(state,view.expected_variant);if(view.whole_model)assertFraming(state);const groups=assertNearGroups(state,view.near_group_indices);const projection=state.visualProbes.find(p=>p.key===view.key).projection;assert.ok(projection.insideViewport);assert.deepEqual(projection.uiAtPoint,[]);assert.deepEqual(projection.beaconsAtPoint,[]);return groups;};
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
  report.global.neighborSeparation={newClip,newSiteClip,excludedContextSources,preservedNeighborProbes:pair.preservedNeighborProbes,nearbyModelStates:pair.nearbyModelStates,visibleExistingModelsVerified:retained,sourceStates:pair.sourceStates,note:'The new correction names only the independently reviewed gymnasium source; the existing stadium and swimming hall remain distinct. Any visible pre-existing models keep their own asset hashes and clip geometries. Near-neighbor source IDs outside all legitimate replacement sets are not candidate-hidden. localModel state may refer to retained source geometry in a loaded city tile; it does not mean that neighboring feature was removed.'};save();
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
  await drainResponses();assert.equal(report.catalog.http?.sha256,report.catalog.sha256);assert.equal(report.catalog.http?.status,200);assert.deepEqual(report.errors,[]);assert.deepEqual(report.warnings,[]);assert.deepEqual(report.http,[]);
  for(const binding of report.expectedSourceBindings)assert.equal(report.sourceBindings[binding.file.slice(4)]?.sha256,binding.sha256,`Served source does not match freeze: ${binding.file}`);
  for(const binding of [report.catalog,report.manifest,report.footprint,report.qaScript,report.viewerRegistry,report.placementBinding,report.qaContract,...report.expectedSourceBindings,...report.documentBindings])assert.equal(sha(fs.readFileSync(path.join(PROJECT,binding.file))),binding.sha256,`Frozen file changed during QA: ${binding.file}`);for(const binding of staticDirectories)assert.equal(sha(fs.readFileSync(path.join(REPO,binding.file))),binding.sha256,`README changed during QA: ${binding.file}`);
  await finalizeChecks();console.log('COMPLETE Jiangwan Gymnasium incremental browser checks; final PNG review remains separate');

 return {completed:true};
};
