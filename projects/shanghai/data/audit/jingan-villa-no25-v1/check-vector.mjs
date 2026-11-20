/** Compare the restored front court against its complete old row and every original OSM component. */
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
assert.equal(source.sha256,review.osm_fallback_tiles[0].sha256);
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
assert.equal(item.id,64634100);
const components=polygons(item.geometry);
assert.equal(components.length,1813);
const targetIndex=components.findIndex(part=>area(clip.intersection([part],polygons(review.source_outline)))>400);
assert.ok(targetIndex>=0);
const target=[components[targetIndex]];
const neighbors=review.owners.filter(r=>r.local_id!==1954);
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
const beforeArea=area(clip.intersection(target,before));
const afterArea=area(clip.intersection(target,after));
const intendedCut=clip.intersection(target,mask);
const intendedArea=area(intendedCut);
assert.ok(beforeArea>440 && beforeArea<442);
assert.ok(afterArea>419 && afterArea<421);
// Independently integrating the three WGS84 rings in local Mercator differs
// by 0.000028 m² at their split edges. One cm² covers that numerical effect.
const areaBudgetM2=.0001;
const conservationError=Math.abs(beforeArea-afterArea-intendedArea);
assert.ok(conservationError<areaBudgetM2,JSON.stringify({beforeArea,afterArea,intendedArea}));
const unintended=area(clip.xor(after,clip.difference(before,intendedCut)));
assert.ok(unintended<.002);
assert.ok(area(clip.intersection(after,mask))<.00001);
const preserved=neighbors.map(row=>{
  const near=polygons(row.geometry);
  const beforeArea=area(clip.intersection(near,before)),afterArea=area(clip.intersection(near,after));
  assert.ok(Math.abs(beforeArea-afterArea)<.00001);
  return {id:row.local_id,before_m2:beforeArea,after_m2:afterArea};
});
const report={id:contract.id,previous_count:catalog.resulting_city_count,previous_catalog_sha256:sha(process.argv[3]),source_sha256:source.sha256,contract_sha256:sha(contractPath),module_sha256:sha(module),source_id:item.id,source_components:components.length,target_component:targetIndex,row_before_m2:beforeArea,row_after_m2:afterArea,removed_only_front_court_m2:intendedArea,independent_metric_conservation_error_m2:conservationError,metric_tolerance_m2:areaBudgetM2,unintended_citywide_difference_m2:unintended,other_near_tile_owners:preserved,passed:true};
fs.writeFileSync(process.argv[4],JSON.stringify(report,null,2)+'\n');
