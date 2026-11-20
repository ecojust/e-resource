/** Compare the new owner against the full prior catalogue and all 755 OSM components. */
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
assert.equal(source.sha256,'01127bf6cc584c8be8a8bd880b6178e8f8e52da9d7855a117fed0c8ec3a877ac');
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
assert.equal(item.id,117811070);
const components=polygons(item.geometry);
assert.equal(components.length,755);
const hallIndex=components.findIndex(p=>area(clip.intersection([p],polygons(review.source_outline)))>670);
assert.equal(hallIndex,537);
const neighbors=Object.entries(review.retained_hall_features).map(([id,name])=>{
  const rec=review.owners.find(o=>o.local_id===Number(id));
  return rec && {id,name,geometry:rec.geometry};
}).filter(Boolean);
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
const hall=[components[hallIndex]];
const hallBefore=area(clip.intersection(hall,before)),hallAfter=area(clip.intersection(hall,after));
assert(hallBefore>680 && hallBefore<690 && hallAfter<.00001);
const templeNeighbors=neighbors.map(({id,name,geometry})=>{
  const old=area(clip.intersection(polygons(geometry),before));
  const retained=area(clip.intersection(polygons(geometry),after));
  assert(Math.abs(old-retained)<.00001);
  return {id,name,before_m2:old,after_m2:retained};
});
const unexpected=area(clip.xor(after,clip.difference(before,hall)));
assert(unexpected<.002);
const overlap=area(clip.intersection(after,mask));
assert(overlap<.00001);
const report={id:contract.id,previous_count:catalog.resulting_city_count,previous_catalog_sha256:sha(process.argv[3]),
  source_sha256:source.sha256,contract_sha256:sha(contractPath),module_sha256:sha(module),source_id:item.id,
  source_components:components.length,hall_component:hallIndex,hall_before_m2:hallBefore,hall_after_m2:hallAfter,
  preserved_neighbors:templeNeighbors,unintended_citywide_difference_m2:unexpected,under_mask_after_m2:overlap,passed:true};
fs.writeFileSync(process.argv[4],JSON.stringify(report,null,2)+'\n');
