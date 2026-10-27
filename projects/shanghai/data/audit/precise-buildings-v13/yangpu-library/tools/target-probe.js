async record => {
  const app=window.__SHANGHAI_APP__, p=window.__YANGPU_PROBE__, map=app.scene.map;
  const [{OrdinaryBuildingCatalog},{OSMBuildingSuppressor}]=await Promise.all([
    import(new URL('src/ordinary-building-catalog.js',document.baseURI)),
    import(new URL('src/osm-building-suppression.js',document.baseURI))]);
  function capture(Class, trigger) {
    let instance;const original=Class.prototype.getState;
    try {Class.prototype.getState=function(...args){instance=this;return original.apply(this,args)};trigger();}
    finally {Class.prototype.getState=original;}
    if(!instance)throw Error('Cannot observe '+Class.name);
    return instance;
  }
  p.catalog=capture(OrdinaryBuildingCatalog,()=>app.scene.getOrdinaryCatalogState());
  p.osm=capture(OSMBuildingSuppressor,()=>app.scene.getRealismState());
  p.target=record;
  p.sourceReadiness=()=>{
    const osm=p.osm.getState(),layer=osm.residualLayer;
    const ready=!osm.active||(!osm.pending&&!osm.pendingRemovals&&!layer?.busy&&!layer?.queued&&
      (!(osm.renderedResidualComponents||osm.residualComponents)||(osm.residualReady&&layer?.ready)));
    const source=osm.active?p.osm.source:p.local.suppression.source;
    return {ready,osm,buildingSource:app.scene.getCollisionState().buildingSource,
      sourcePresent:Boolean(map.getSource(source)),sourceLoaded:map.getSource(source)?map.isSourceLoaded(source):false};
  };
  p.catalogState=()=>({
    state:p.catalog.getState(),
    catalogMacroIds:[...p.catalog.entries.keys()],
    entries:[...p.catalog.entries.values()].filter(e=>e.session).map(e=>({id:e.id,status:e.status,
      modelIds:e.models.map(m=>m.id),adoptedIds:e.session.adoptedIds,
      targetModels:e.models.filter(m=>m.id===record.id).map(m=>({id:m.id,owner:m.owner,web_sha256:m.web_sha256,lod_sha256:m.lod_sha256}))})),
    staticOwner:p.detail.staticReplacements.landmarks.has(record.id),
    runtimeTargetCount:app.scene.getLandmarkState().filter(x=>x.id===record.id).length,
    navigationTargetCount:app.landmarks.filter(x=>x.id===record.id).length,
    registrations:[...p.detail.macroRegistrations.values()].map(r=>({macroId:r.macroId,landmarks:[...r.prepared.landmarks]}))
  });
  const polygons=g=>g?.type==='Polygon'?[g.coordinates]:g?.type==='MultiPolygon'?g.coordinates:[];
  const bounds=coordinates=>coordinates.flat().reduce((b,v)=>[Math.min(b[0],v[0]),Math.min(b[1],v[1]),Math.max(b[2],v[0]),Math.max(b[3],v[1])],[Infinity,Infinity,-Infinity,-Infinity]);
  const targetBounds=polygons(record.confirmed_boundary).map(bounds).reduce((a,b)=>[Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[2],b[2]),Math.max(a[3],b[3])],[Infinity,Infinity,-Infinity,-Infinity]);
  const overlaps=c=>{const b=bounds(c),a=targetBounds;return b[0]<=a[2]&&b[2]>=a[0]&&b[1]<=a[3]&&b[3]>=a[1]};
  p.sourceObservation=()=>{
    const readiness=p.sourceReadiness(),components=[],source=readiness.osm.active?p.osm.source:p.local.suppression.source;
    const layer=readiness.osm.active?p.osm.sourceLayer:'building';
    const features=map.getSource(source)?map.querySourceFeatures(source,{sourceLayer:layer}):[];
    for(const f of features)for(const [componentIndex,c]of polygons(f.geometry).entries())if(overlaps(c)){
      components.push({id:f.id,componentIndex,properties:{...f.properties},geometry:{type:'Polygon',coordinates:c},
        featureState:map.getFeatureState({source,sourceLayer:layer,id:f.id})});
    }
    const helper=p.osm.residualLayer;
    const residualCurrent=Boolean(helper?.source)&&map.getSource(helper.sourceId)===helper.source;
    const residual=residualCurrent?helper.source.serialize().data:null;
    const residualComponents=[];
    for(const f of residual?.features||[])for(const [componentIndex,c]of polygons(f.geometry).entries())if(overlaps(c)){
      residualComponents.push({id:f.id,componentIndex,properties:{...f.properties},geometry:{type:'Polygon',coordinates:c}});
    }
    return {readiness,source,sourceLayer:layer,sourcePresent:Boolean(map.getSource(source)),
      sourceLoaded:map.getSource(source)?map.isSourceLoaded(source):false,queriedFeatureCount:features.length,
      components,residualCurrent,residualValid:residual?.type==='FeatureCollection'&&Array.isArray(residual.features),
      residualComponents,targetBoundary:record.confirmed_boundary};
  };
  p.targetAudit=()=>{
    const audit=p.audit(),owner=record.owner;
    const parent=audit.parents.find(r=>r.id===owner.macro_id);
    const near=parent?.near.find(r=>r.id===owner.macro_id+'/'+owner.near_owner_id);
    const active=audit.activePrecise.includes(record.id);
    const errors=[];
    if(!audit.passed)errors.push(...audit.errors);
    if(active&&(!parent?.farVisible||!parent.preciseOwners.some(([id,ids])=>id===record.id&&ids.includes(owner.feature_local_id))))errors.push('Target has no visible far precise owner');
    const present=near?.preservedNeighborIDs||[];
    const expected=owner.preserve_neighbor_local_ids;
    const neighborsExact=present.length===expected.length&&expected.every(id=>present.includes(id));
    const nearGroup=near?.groups.find(g=>g.landmark===record.id);
    const hiddenNear=Boolean(near?.visible&&nearGroup&&nearGroup.visible===!active&&near.passed&&neighborsExact);
    if(near?.visible&&!hiddenNear)errors.push('Near target or preserved neighbors differ');
    return {passed:errors.length===0,errors,active,targetOwner:owner,parent,near,neighborsExact,hiddenNear,
      online:audit.online.find(r=>r.id===record.id),catalog:p.catalogState(),sourceReadiness:p.sourceReadiness()};
  };
  return {readOnly:true,prototypeWrappersRestored:true,target:record.id,
    scope:'Observes existing runtime objects and actual source geometry. No owners, asset bytes, deadlines, feature states or renderer settings are mutated.'};
}
