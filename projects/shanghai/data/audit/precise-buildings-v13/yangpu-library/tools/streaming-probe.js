async registry=>{
 const app=__SHANGHAI_APP__;
 const [{CityDetailStreamer},{LocalModelStreamer},{countExpandedTriangles},THREE]=await Promise.all([
   import(new URL('src/city-detail-streamer.js',document.baseURI).href),
   import(new URL('src/local-model-streamer.js',document.baseURI).href),
   import(new URL('src/model-resources.js',document.baseURI).href),
   import(new URL('vendor/three.module.js',document.baseURI).href)]);
 function capture(Class){let instance;const original=Class.prototype.getState;
   try{Class.prototype.getState=function(...args){instance=this;return original.apply(this,args)};app.scene.getStreamingState()}
   finally{Class.prototype.getState=original}if(!instance)throw Error('Cannot inspect '+Class.name);return instance}
 const detail=capture(CityDetailStreamer),local=capture(LocalModelStreamer);
 const probe=window.__YANGPU_PROBE__={detail,local,registry,heldMasks:[],farLoadFailures:[]};
 // Preserve the real callback and scheduling; retain unthrottled diagnostics
 // before map-scene's notice throttle discards repeated transient failures.
 const notifyFarError=local.onError;
 local.onError=function(error,record){
   const request=local.inflight.get(record.id);
   probe.farLoadFailures.push({at:performance.now(),id:record.id,message:String(error?.message||error),
     status:record.status,aborted:request?.controller.signal.aborted??false,
     abortReason:request?.controller.signal.reason??null,wanted:local.wanted.has(record.id),
     hasObject:Boolean(record.object),visible:Boolean(record.object?.visible)});
   return notifyFarError.call(this,error,record);
 };
 // Synchronous, restored interception: the first traversal is the real
 // imported root used by countExpandedTriangles inside the public asset API.
 probe.assetState=id=>{
   const original=THREE.Object3D.prototype.traverse;let group=null,state;
   try{
     THREE.Object3D.prototype.traverse=function(...args){if(!group)group=this;return original.apply(this,args)};
     state=app.scene.getLandmarkAssetState(id);
   }finally{THREE.Object3D.prototype.traverse=original;}
   const glass=[],otherPhoto=[];
   if(group){
     let root=group;while(root.parent)root=root.parent;probe.sceneRoot=root;
     original.call(group,mesh=>{
       if(!mesh.isMesh)return;
       for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]){
         if(!material?.map||!/^PhotoFacade_/i.test(material.name||''))continue;
         const row={mesh:mesh.name,meshUUID:mesh.uuid,material:material.name,type:material.type,
           isMeshBasicMaterial:material.isMeshBasicMaterial===true,
           actualMeshBasicInstance:material instanceof THREE.MeshBasicMaterial,
           receiveShadow:mesh.receiveShadow,castShadow:mesh.castShadow,
           envMap:material.envMap?{name:material.envMap.name,uuid:material.envMap.uuid}:null,
           envMapIsNull:material.envMap===null,
           photographicRendering:material.userData?.photographicRendering||null};
         (/^PhotoFacade_.*(?:glass|glazing)/i.test(material.name)?glass:otherPhoto).push(row);
       }
     });
   }
   return {...state,actualPhotographicMaterials:{rootFound:Boolean(group),
     traverseRestored:THREE.Object3D.prototype.traverse===original,glass,otherPhoto}};
 };
 probe.shadowState=()=>{
   const sun=probe.sceneRoot?.children.find(o=>o.isDirectionalLight&&o.name==='Bund cached morning sun');
   const gl=app.scene.map.painter?.context?.gl;
   const maxTextureSize=gl?.getParameter(gl.MAX_TEXTURE_SIZE)??null;
   const lowMemory=Boolean(navigator.deviceMemory&&navigator.deviceMemory<=4),requestedSize=lowMemory?1024:4096;
   const expectedSize=Number.isFinite(maxTextureSize)&&maxTextureSize>0
     ?Math.min(requestedSize,2**Math.floor(Math.log2(maxTextureSize))):requestedSize;
   const camera=sun?.shadow.camera;
   return {found:Boolean(sun),deviceMemory:navigator.deviceMemory??null,lowMemory,maxTextureSize,requestedSize,expectedSize,
     mapSize:sun?[sun.shadow.mapSize.x,sun.shadow.mapSize.y]:null,
     camera:camera?{left:camera.left,right:camera.right,top:camera.top,bottom:camera.bottom,near:camera.near,far:camera.far}:null};
 };
 const exact=()=>new Set(registry.landmarks.filter(r=>{
   const a=app.scene.getLandmarkAssetState(r.id);return a.status==='loaded'&&a.visible;
 }).map(r=>r.id));
 const same=(a,b)=>a.length===b.length&&[...a].sort().every((x,i)=>x===[...b].sort()[i]);
 probe.holdMasks=()=>{probe.heldMasks=[...detail.parents.values()].filter(p=>p.mask).map(p=>({id:p.id,mask:p.mask}));
   return probe.heldMasks.map(p=>({id:p.id,owners:p.mask.owners.size}))};
 probe.audit=()=>{
   const active=exact(),errors=[],parents=[],neighborIDs=new Set();
   if(!same([...active],[...detail.visibleLandmarks]))errors.push('Precise visible IDs differ from actual loaded-visible landmarks');
   for(const p of detail.parents.values()){
     if(!p.mask)continue;
     const visible=p.records.filter(r=>r.object?.visible),expected=new Map();
     for(const r of visible)for(const id of r.ids)expected.set(id,(expected.get(id)||0)+1);
     const expectedPrecise=new Map();
     for(const [id,landmark] of p.replacement?.owners||[])if(active.has(landmark)){
       expected.set(id,(expected.get(id)||0)+1);
       if(!expectedPrecise.has(landmark))expectedPrecise.set(landmark,[]);expectedPrecise.get(landmark).push(id);
     }
     let badReferences=0,badBits=0;
     for(let id=0;id<p.mask.references.length;id++){
       if(p.mask.references[id] !== (expected.get(id)||0))badReferences++;
       if(Boolean(p.mask.data[id]) !== expected.has(id))badBits++;
     }
     const missingOwners=visible.some(r=>!p.mask.owners.has(r.owner))||
       [...expectedPrecise].some(([id])=>!p.preciseOwners?.has(id)||!p.mask.owners.has(p.preciseOwners.get(id)));
     const ownerCountWrong=p.mask.owners.size!==visible.length+expectedPrecise.size||
       (p.preciseOwners?.size||0)!==expectedPrecise.size;
     const invalidVisible=visible.some(r=>r.status!=='loaded'||!p.active||!p.object.visible);
     const near=[];
     for(const r of p.records){
       if(!r.object||!r.replacement)continue;
       const groups=(r.replacementGroups||[]).map(({object,landmark})=>({name:object.name,landmark,
         visible:object.visible,triangles:countExpandedTriangles(object),tag:object.userData.cityReplacement}));
       const expectedIDs=r.replacement.featureLocalIds.filter(id=>!r.replacement.groups.some(g=>g.local_ids.includes(id)));
       const kept=[];r.object.traverse(o=>{if(Array.isArray(o.userData?.cityPreservedLocalIds))kept.push(o)});
       const expectedTriangles=r.declaredTriangles-r.replacement.groups.reduce((n,g)=>n+g.expandedTriangles,0);
       const keptIDs=kept.flatMap(o=>o.userData.cityPreservedLocalIds),keptTriangles=kept.reduce((n,o)=>n+countExpandedTriangles(o),0);
       const passed=groups.length===r.replacement.groups.length&&groups.every(g=>{
         const e=r.replacement.groups.find(x=>x.name===g.name);
         return e&&g.landmark===e.landmark_id&&g.triangles===e.expandedTriangles&&g.visible===!active.has(g.landmark)&&
           same(g.tag.local_ids,e.local_ids)&&same(g.tag.feature_keys,e.feature_keys);
       })&&same(keptIDs,expectedIDs)&&kept.every(o=>o.visible)&&keptTriangles===expectedTriangles&&
         countExpandedTriangles(r.object)===r.declaredTriangles;
       if(!passed)errors.push('Complete target or neighbor group differs: '+r.id);
       if(r.object.visible)for(const id of keptIDs)neighborIDs.add(p.id+':'+id);
       near.push({id:r.id,visible:r.object.visible,status:r.status,url:r.url,ids:[...r.ids],groups,
         triangles:countExpandedTriangles(r.object),declaredTriangles:r.declaredTriangles,
         preservedNeighborIDs:keptIDs,preservedNeighborTriangles:keptTriangles,passed});
     }
     if(badReferences||badBits||missingOwners||ownerCountWrong||invalidVisible||p.mask.disposed)errors.push('Far mask ownership differs: '+p.id);
     parents.push({id:p.id,active:p.active,farVisible:p.object.visible,preciseOwners:[...expectedPrecise],
       visibleNear:visible.map(r=>r.id),badReferences,badBits,missingOwners,ownerCountWrong,invalidVisible,
       maskedCount:expected.size,owners:p.mask.owners.size,near});
   }
   const suppression=local.suppression,online=[];
   for(const entry of registry.landmarks){
     const owner='precise:'+entry.id,owned=suppression.owners.get(owner)||new Map();
     const keys=[...(entry.building_ids||[]).map(id=>'building\0'+id),...(entry.building_part_ids||[]).map(id=>'building_part\0'+id)];
     if(!same([...owned.keys()],active.has(entry.id)?keys:[]))errors.push('Dynamic online owner differs: '+entry.id);
     const sources=keys.map(key=>{
       const reference=suppression.references.get(key),[layer,id]=key.split('\0');
       let expected=0;for(const values of suppression.owners.values())if(values.has(key))expected++;
       const actual=reference?.count||0;if(actual!==expected)errors.push('Shared online refcount differs: '+key);
       let state=null;if(suppression.map.getSource(suppression.source))state=suppression.map.getFeatureState({source:suppression.source,sourceLayer:layer,id});
       return {layer,id,expectedReferences:expected,actualReferences:actual,state};
     });
     online.push({id:entry.id,active:active.has(entry.id),owner,keys:[...owned.keys()],sources});
   }
   const held=probe.heldMasks.map(({id,mask})=>({id,disposed:mask.disposed,owners:mask.owners.size,
     remainingReferences:mask.references.reduce((n,v)=>n+(v!==0),0),remainingBits:mask.data.reduce((n,v)=>n+(v!==0),0)}));
   return {passed:errors.length===0,errors,activePrecise:[...active],parents,online,
     onlinePending:suppression.pending.size,visibleNeighborIDs:[...neighborIDs],held,
     heldReleased:held.every(p=>p.disposed&&!p.owners&&!p.remainingReferences&&!p.remainingBits)};
 };
 probe.snapshot=()=>{
   const m=app.scene.map,t=m.transform,eye=t?.getCameraLngLat?.();
   return {mode:app.mode,districts:app.districts.length,controller:app.controller.getState?.()||{position:app.controller.position},
     camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),
       fov:m.getVerticalFieldOfView?.(),eye:eye?{lng:eye.lng,lat:eye.lat,alt:t.getCameraAltitude?.()}:null},
     landmarks:app.scene.getLandmarkState(),assets:Object.fromEntries(registry.landmarks.map(r=>[r.id,probe.assetState(r.id)])),
     actualShadow:probe.shadowState(),
     streaming:app.scene.getStreamingState(),cache:app.scene.getLandmarkCacheState(),
     source:app.scene.getCollisionState(),realism:app.scene.getRealismState(),audit:probe.audit(),
     farDiagnostics:{events:probe.farLoadFailures.slice(),currentErrors:[...local.records.values()].filter(r=>['error','missing'].includes(r.status)).map(r=>({id:r.id,status:r.status,wanted:local.wanted.has(r.id),visible:Boolean(r.object?.visible),retryAt:r.retryAt})),inflight:[...local.inflight].map(([id,r])=>({id,aborted:r.controller.signal.aborted,abortReason:r.controller.signal.reason??null}))}};
 };
 return {read_only_probe:true,restored_prototypes:true,monitored_far_error_callback:true,registered:detail.replacements.landmarks.size};
}
