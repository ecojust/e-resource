async evidence => {
  // Read-only observation. Capture actual helper instances synchronously and
  // restore their prototype methods even when the public getter throws.
  const app=window.__SHANGHAI_APP__,map=app.scene.map;
  const {OSMBuildingSuppressor}=await import(new URL('src/osm-building-suppression.js',document.baseURI));
  let suppressor=null;const original=OSMBuildingSuppressor.prototype.getState;
  try {OSMBuildingSuppressor.prototype.getState=function(...args){suppressor=this;return original.apply(this,args)};app.scene.getRealismState();}
  finally {OSMBuildingSuppressor.prototype.getState=original;}
  if(!suppressor)throw Error('Cannot observe actual OSM suppressor');
  const helper=suppressor.residualLayer;
  const readiness=()=>{
    const osm=app.scene.getRealismState().osmFallback;
    const layer=osm?.residualLayer;
    const ready=Boolean(osm)&&(!osm.active||(!osm.pending&&!osm.pendingRemovals&&!layer?.busy&&!layer?.queued&&
      (!(osm.renderedResidualComponents||osm.residualComponents)||(osm.residualReady&&layer?.ready))));
    return {ready,source:suppressor.source,osm};
  };
  // No coordinate rounding or geometric expansion. Rotation, winding and hole
  // order are representational only; every original coordinate is retained.
  function ringKey(ring){
    const points=ring.slice();if(points.length>1&&JSON.stringify(points[0])===JSON.stringify(points.at(-1)))points.pop();
    const rotations=[];for(const p of [points,points.slice().reverse()])for(let i=0;i<p.length;i++)rotations.push(JSON.stringify(p.slice(i).concat(p.slice(0,i))));
    return rotations.sort()[0];
  }
  const polygonKey=coordinates=>JSON.stringify([ringKey(coordinates[0]),coordinates.slice(1).map(ringKey).sort()]);
  const polygons=g=>g?.type==='Polygon'?[g.coordinates]:g?.type==='MultiPolygon'?g.coordinates:[];
  const expected=evidence.geometry?.type==='Polygon'?polygonKey(evidence.geometry.coordinates):null;
  const inspect=({target=null}={})=>{
    const state=readiness();
    const out={...state,passed:state.ready,target_requested:target,component_check:null};
    if(!state.ready||!state.osm.active||target!==evidence.landmark_id)return out;
    if(expected===null||evidence.source_id===null||evidence.source_id===undefined){
      out.passed=false;out.evidence_missing=true;out.reason='Active OSM fallback requires this target actual source-ID/component evidence; no prior-building IDs are reused.';return out;
    }
    const all=map.querySourceFeatures(suppressor.source,{sourceLayer:suppressor.sourceLayer});
    const matching=all.filter(f=>String(f.id)===String(evidence.source_id));
    const extracted=[];
    for(const feature of matching)polygons(feature.geometry).forEach((coordinates,index)=>{
      if(polygonKey(coordinates)===expected)extracted.push({fragment_id:feature.id,component_index:index,properties:{...feature.properties},geometry:{type:'Polygon',coordinates:JSON.parse(JSON.stringify(coordinates))}});
    });
    const actualState=map.getFeatureState({source:suppressor.source,sourceLayer:suppressor.sourceLayer,id:evidence.source_id});
    const sourceIsCurrent=Boolean(helper?.source)&&map.getSource(helper.sourceId)===helper.source;
    const residual=sourceIsCurrent?helper.source.serialize().data:null;
    const residualValid=sourceIsCurrent&&residual?.type==='FeatureCollection'&&Array.isArray(residual.features);
    const retained=residualValid?residual.features.filter(f=>polygons(f.geometry).some(c=>polygonKey(c)===expected)):[];
    out.component_check={expected_source_id:evidence.source_id,source:suppressor.source,source_layer:suppressor.sourceLayer,
      queried_id_fragments:matching.length,actual_state:actualState,extracted_components:extracted,
      residual_source_is_current:sourceIsCurrent,residual_data_available:residualValid,residual_feature_count:residualValid?residual.features.length:null,
      matching_residual_components:retained.length,expected_geometry:evidence.geometry,
      scope:'Exact frozen actual-MVT component (rotation/winding invariant); no model/source geometry mutation or guessed radius. A changed source fixture fails closed.'};
    out.passed=state.ready&&matching.length>0&&extracted.length>0&&actualState.localModel===true&&residualValid&&retained.length===0;
    return out;
  };
  window.__OSM_CAPTURE__={readiness,inspect};
  return {read_only:true,prototypes_restored:OSMBuildingSuppressor.prototype.getState===original,source_id:evidence.source_id,
    evidence_schema:evidence.schema,source_geometry_not_modified:true,feature_states_not_modified:true};
}
