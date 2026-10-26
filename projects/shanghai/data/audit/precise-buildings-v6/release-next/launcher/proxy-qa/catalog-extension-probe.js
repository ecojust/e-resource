async ({target,macroId,owner})=>{
 const app=__SHANGHAI_APP__,p=__V6_CAPTURE__;
 const [{OrdinaryBuildingCatalog},THREE]=await Promise.all([
   import(new URL('src/ordinary-building-catalog.js',document.baseURI).href),
   import(new URL('vendor/three.module.js',document.baseURI).href)]);
 let catalog;const old=OrdinaryBuildingCatalog.prototype.getState;
 try{OrdinaryBuildingCatalog.prototype.getState=function(...a){catalog=this;return old.apply(this,a)};app.scene.getOrdinaryCatalogState()}
 finally{OrdinaryBuildingCatalog.prototype.getState=old}
 if(!catalog)throw Error('The accepted ordinary catalog is not enabled');
 p.catalog=catalog;p.target=target;p.macroId=macroId;p.targetOwner=owner;p.heldTarget=null;
 p.targetRoot=()=>{let root;const original=THREE.Object3D.prototype.traverse;
   try{THREE.Object3D.prototype.traverse=function(...a){root||=this;return original.apply(this,a)};app.scene.getLandmarkAssetState(target)}
   finally{THREE.Object3D.prototype.traverse=original}return root||null;};
 p.holdTarget=()=>{const root=p.targetRoot();if(!root)throw Error('No target model to observe disposal');
   const geometries=new Set();root.traverse(o=>{if(o.isMesh&&o.geometry)geometries.add(o.geometry)});
   const held={root,uuid:root.uuid,geometryCount:geometries.size,disposed:new Set()};
   for(const g of geometries)g.addEventListener('dispose',()=>held.disposed.add(g));p.heldTarget=held;
   return {uuid:held.uuid,geometryCount:held.geometryCount};};
 p.ordinaryState=()=>{
   const entry=catalog.entries.get(macroId),root=p.targetRoot(),states=app.scene.getLandmarkState();
   const macroParents=[...p.detail.parents.values()].filter(parent=>parent.id===macroId);
   return {state:app.scene.getOrdinaryCatalogState(),staticNavigationCount:app.landmarks.length,
     staticTargetCount:app.landmarks.filter(r=>r.id===target).length,
     targetRecords:states.filter(r=>r.id===target),totalRuntimeRecords:states.length,
     actualGroupUUID:root?.uuid||null,ordinaryRegistries:p.detail.macroRegistrations?.size||0,
     staticReplacementIds:[...p.detail.staticReplacements.landmarks],
     entry:entry?{id:entry.id,status:entry.status,hasSession:!!entry.session,
       adoptedIds:entry.session?.adoptedIds||[],modelIds:entry.models.map(r=>r.id)}:null,
     targetMacroNear:macroParents.flatMap(parent=>parent.records.filter(r=>r.ids.includes(owner.feature_local_id)).map(r=>({id:r.id,
       visible:!!r.object?.visible,status:r.status,ids:[...r.ids],replacement:!!r.replacement,
       declaredTriangles:r.declaredTriangles,triangles:r.triangles}))),
     held:p.heldTarget?{uuid:p.heldTarget.uuid,detached:p.heldTarget.root.parent===null,
       geometryCount:p.heldTarget.geometryCount,geometriesDisposed:p.heldTarget.disposed.size}:null};
 };
 p.catalogSnapshot=()=>({...p.snapshot(),ordinary:p.ordinaryState()});
 return {read_only_prototypes_restored:OrdinaryBuildingCatalog.prototype.getState===old,
   catalogMacros:catalog.entries.size,sourceOwnerNeverMutated:true};
}
