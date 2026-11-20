/** Compare the new owner against the full prior catalogue and all 17 OSM components. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const audit=path.dirname(fileURLToPath(import.meta.url));
const project=path.resolve(audit,'../../..');
const root=process.env.SHANGHAI_PROJECT_ROOT || project;
const read=file=>JSON.parse(fs.readFileSync(file));
const sha=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const contractPath=process.env.MODEL_VERIFIED_CONTRACT || path.join(audit,'final-placement-contract.json');
const contract=read(contractPath);
const review=read(path.join(project,'source/precise',contract.id,'footprint-review.json'));
const source=read(process.argv[2]);
assert.equal(source.sha256,'36448c327185ab13a8d07e723bda4d00dec0c1d36c6831a4c6aa50de13a07893');
const module=path.join(root,'src/candidate-vector-clipping.js');
const {planCandidateVectorClipping}=await import(pathToFileURL(module));
const clip=globalThis.polygonClipping;
const polygons=g=>g.type==='Polygon'?[g.coordinates]:g.coordinates;
const center=[contract.lng,contract.lat], rad=Math.PI/180;
const scale=6371008.8*Math.cos(center[1]*rad);
const north=Math.asinh(Math.tan(center[1]*rad));
function ringArea(ring) {
  const points=ring.map(([lon,lat])=>[(lon-center[0])*rad*scale,(Math.asinh(Math.tan(lat*rad))-north)*scale]);
  let twice=0;
  for(let i=1;i<points.length;i++)twice+=(points[i-1][0]-points[0][0])*(points[i][1]-points[0][1])-(points[i-1][1]-points[0][1])*(points[i][0]-points[0][0]);
  return Math.abs(twice)/2;
}
const area=parts=>parts.reduce((sum,rings)=>sum+rings.reduce((a,r,i)=>a+(i?-1:1)*ringArea(r),0),0);
const rules=entry=>({id:entry.id,owner:entry.owner,owners:entry.owners,source_feature_ids:entry.source_feature_ids,geometry:entry.replacement_geometry,...(entry.osm_replacement_geometry && {osm_replacement_geometry:entry.osm_replacement_geometry})});
const catalog=read(process.argv[3]);
assert(Number.isInteger(catalog.resulting_city_count));
assert(!catalog.models.some(m=>m.id===contract.id));
const previous=catalog.models.filter(m=>m.replacement_geometry).map(rules);
const [item]=source.features;
assert.equal(item.id,1658263140);
const components=polygons(item.geometry);
assert.equal(components.length,17);
const ownerIndex=components.findIndex(p=>area(clip.intersection([p],polygons(review.source_outline)))>320);
assert.equal(ownerIndex,9);
const neighbors=Object.entries(review.named_neighbors).map(([id,row])=>({id:+id,name:'neighbor '+id,geometry:row.geometry}));
function residual(list){
  const plan=planCandidateVectorClipping([item],{candidateClips:list},{source:'openmaptiles',sourceLayer:'building'});
  assert.equal(plan.stats.clippingErrors,0);
  if(!plan.desired.has('number:'+item.id))return components;
  const [rest]=plan.residualData.features;
  assert.deepEqual(rest.properties,item.properties);
  return polygons(rest.geometry);
}
const before=residual(previous),after=residual([...previous,rules(contract)]);
const mask=polygons(contract.replacement_geometry);
const residence=[components[ownerIndex]];
const ownerBefore=area(clip.intersection(residence,before)),ownerAfter=area(clip.intersection(residence,after));
assert(ownerBefore>320 && ownerBefore<410 && ownerAfter<.00001);
const nearbyBefore=[],nearbyAfter=[];
for (const feature of source.nearby_additional_features) {
  const original=polygons(feature.geometry);
  const plans=[previous,[...previous,rules(contract)]].map(list=>{
    const state=planCandidateVectorClipping([feature],{candidateClips:list},{source:'openmaptiles',sourceLayer:'building'});
    assert.equal(state.stats.clippingErrors,0);
    if (!state.desired.has('number:'+feature.id)) return original;
    return state.residualData.features.length ? polygons(state.residualData.features[0].geometry) : [];
  });
  assert(area(clip.xor(plans[0],plans[1]))<.0002,'Neighbor feature changed '+feature.id);
  nearbyBefore.push(...plans[0]);nearbyAfter.push(...plans[1]);
}
const residues=[clip.union(before,nearbyBefore),clip.union(after,nearbyAfter)];
const residences=neighbors.map(({id,name,geometry})=>{
  const old=area(clip.intersection(polygons(geometry),residues[0]));
  const retained=area(clip.intersection(polygons(geometry),residues[1]));
  assert(Math.abs(old-retained)<.0002,'Neighbor coverage changed '+id);
  if (id===470) assert(old>325 && old<340,'Unexpected coverage for No 175');
  else assert(old<.0002,'Unexpected fallback coverage for a native-only neighboring residence');
  return {id,name,before_m2:old,after_m2:retained, present_in_this_fallback_tile:old>.0002};
});
const unexpected=area(clip.xor(after,clip.difference(before,residence)));
assert(unexpected<.002);
const overlap=area(clip.intersection(after,mask));
assert(overlap<.00001);
const report={id:contract.id,previous_count:catalog.resulting_city_count,previous_catalog_sha256:sha(process.argv[3]),
  source_sha256:source.sha256,contract_sha256:sha(contractPath),module_sha256:sha(module),source_id:item.id,
  total_tile_buildings:source.total_tile_buildings,additional_neighbor_features:source.nearby_additional_features.map(v=>v.id),source_components:components.length,residence_component:ownerIndex,residence_before_m2:ownerBefore,residence_after_m2:ownerAfter,
  preserved_neighbors:residences,unintended_citywide_difference_m2:unexpected,under_mask_after_m2:overlap,passed:true};
fs.writeFileSync(process.argv[4],JSON.stringify(report,null,2)+'\n');
