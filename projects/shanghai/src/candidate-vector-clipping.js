import '../vendor/polygon-clipping.umd.min.js';
const clipping=globalThis.polygonClipping;
const polygons=g=>g?.type==='Polygon'?[g.coordinates]:g?.type==='MultiPolygon'?g.coordinates:[];
const area=parts=>parts.reduce((sum,rings)=>sum+rings.reduce((s,r,j)=>{
  let a=0;for(let i=1;i<r.length;i++)a+=(r[i-1][0]-r[0][0])*(r[i][1]-r[0][1])-(r[i][0]-r[0][0])*(r[i-1][1]-r[0][1]);
  return s+(j?-1:1)*Math.abs(a)/2;
},0),0);

/** Retain every visible source fragment outside the registered local correction.
 * Features already supplied by a loaded city GLB need no duplicate residual.
 */
export function planCandidateVectorClipping(features,coverage,context){
  const groups=new Map();
  for(const f of features){
    if(f.id===undefined||!polygons(f.geometry).length)continue;
    const key=`${typeof f.id}:${f.id}`;
    if(!groups.has(key))groups.set(key,{id:f.id,properties:f.properties||{},parts:[],invalid:false});
    const g=groups.get(key);
    if(JSON.stringify(g.properties)!==JSON.stringify(f.properties||{}))g.invalid=true;
    g.parts.push(...polygons(f.geometry));
  }
  const desired=new Map(),residual=[];let failed=0;
  for(const [key,g] of groups){
    if(g.invalid||coverage.alreadyCovered?.(g.id))continue;
    const clips=(coverage.candidateClips||[]).filter(c=>{
      const ids=c.source_feature_ids?.[context.sourceLayer];
      return context.source!=='overture-buildings'||Boolean(ids?.includes(String(g.id))||ids?.includes(String(g.properties.id)));
    });
    if(!clips.length)continue;
    try{
      const original=clipping.union(...g.parts),cuts=clips.flatMap(c=>polygons(c.geometry));
      const intersection=clipping.intersection(original,...[clipping.union(...cuts)]);
      if(area(intersection)<1e-17)continue;
      const remaining=clipping.difference(original,...cuts);
      desired.set(key,{id:g.id,residual:remaining.length>0});
      if(remaining.length)residual.push({type:'Feature',id:`candidate-residual:${context.sourceLayer}:${encodeURIComponent(key)}`,
        properties:g.properties,geometry:{type:'MultiPolygon',coordinates:remaining}});
    }catch{failed++;}
  }
  const residualData={type:'FeatureCollection',features:residual};
  return {desired,residualData,signature:JSON.stringify([[...desired.values()].map(x=>x.id),residual]),
    stats:{queriedFeatures:features.length,candidateIDs:groups.size,partialIDs:residual.length,
      residualComponents:residual.length,removedComponents:desired.size,retainedCrossingIDs:groups.size-desired.size,clippingErrors:failed}};
}
