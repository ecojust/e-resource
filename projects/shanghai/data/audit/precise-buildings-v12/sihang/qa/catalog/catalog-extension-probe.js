async ({targets,macroId,owners})=>{
 const app=__SHANGHAI_APP__,p=__V6_CAPTURE__,targetSet=new Set(targets);
 const [{OrdinaryBuildingCatalog},THREE]=await Promise.all([
   import(new URL('src/ordinary-building-catalog.js',document.baseURI).href),
   import(new URL('vendor/three.module.js',document.baseURI).href)]);
 let catalog;const old=OrdinaryBuildingCatalog.prototype.getState;
 try{OrdinaryBuildingCatalog.prototype.getState=function(...a){catalog=this;return old.apply(this,a)};app.scene.getOrdinaryCatalogState()}
 finally{OrdinaryBuildingCatalog.prototype.getState=old}
 if(!catalog)throw Error('The accepted ordinary catalog is not enabled');
 p.catalog=catalog;p.targets=targets;p.macroId=macroId;p.heldTargets=new Map();
 p.targetRoot=id=>{let root;const original=THREE.Object3D.prototype.traverse;
   try{THREE.Object3D.prototype.traverse=function(...a){root||=this;return original.apply(this,a)};app.scene.getLandmarkAssetState(id)}
   finally{THREE.Object3D.prototype.traverse=original}return root||null;};
 p.holdTarget=id=>{if(!targetSet.has(id))throw Error('Unreviewed target ID');
   const root=p.targetRoot(id);if(!root)throw Error('No target model to observe disposal: '+id);
   const geometries=new Set();root.traverse(o=>{if(o.isMesh&&o.geometry)geometries.add(o.geometry)});
   const held={root,uuid:root.uuid,geometryCount:geometries.size,disposed:new Set()};
   for(const g of geometries)g.addEventListener('dispose',()=>held.disposed.add(g));p.heldTargets.set(id,held);
   return {id,uuid:held.uuid,geometryCount:held.geometryCount};};
 p.ordinaryState=()=>{
   const entry=catalog.entries.get(macroId),states=app.scene.getLandmarkState();
   const macroParents=[...p.detail.parents.values()].filter(parent=>parent.id===macroId);
   const localIds=new Set(Object.values(owners).map(owner=>owner.feature_local_id));
   return {state:app.scene.getOrdinaryCatalogState(),staticNavigationCount:app.landmarks.length,
     staticTargetIds:app.landmarks.filter(r=>targetSet.has(r.id)).map(r=>r.id),
     targetRecords:states.filter(r=>targetSet.has(r.id)),totalRuntimeRecords:states.length,
     actualGroupUUIDs:Object.fromEntries(targets.map(id=>[id,p.targetRoot(id)?.uuid||null])),
     ordinaryRegistries:p.detail.macroRegistrations?.size||0,
     selectedMacroRegistryRegistered:[...(p.detail.macroRegistrations?.values()||[])].some(row=>row.macroId===macroId),
     staticReplacementIds:[...p.detail.staticReplacements.landmarks],
     entry:entry?{id:entry.id,status:entry.status,hasSession:!!entry.session,
       adoptedIds:entry.session?.adoptedIds||[],modelIds:entry.models.map(r=>r.id)}:null,
     targetMacroNear:macroParents.flatMap(parent=>parent.records.filter(r=>r.ids.some(id=>localIds.has(id))).map(r=>({id:r.id,
       visible:!!r.object?.visible,status:r.status,ids:[...r.ids],replacement:!!r.replacement,
       declaredTriangles:r.declaredTriangles,triangles:r.triangles}))),
     heldTargets:Object.fromEntries([...p.heldTargets].map(([id,held])=>[id,{uuid:held.uuid,detached:held.root.parent===null,
       geometryCount:held.geometryCount,geometriesDisposed:held.disposed.size}]))};
 };
 p.catalogSnapshot=()=>({...p.snapshot(),ordinary:p.ordinaryState()});
 return {read_only_prototypes_restored:OrdinaryBuildingCatalog.prototype.getState===old,
   catalogMacros:catalog.entries.size,sourceOwnerNeverMutated:true,targetIds:targets};
}
