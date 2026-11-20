/** Exercise the ordinary vector clipping code on both complete original aggregates. */
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
const sources=read(process.argv[2]);
assert.deepEqual(sources.map(s=>s.tile),review.osm_fallback_tiles);
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
const rule={id:contract.id,geometry:contract.replacement_geometry,source_feature_ids:contract.source_feature_ids,owner:contract.owner};
const cut=polygons(contract.replacement_geometry);
const result=[];
for(const {tile,features} of sources) {
  const [item]=features,all=polygons(item.geometry);
  const west=tile.x===13718;
  assert.equal(item.id,west?147898520:38934830);
  assert.equal(all.length,west?2426:3535);
  const original=clip.union(...all);
  const planned=planCandidateVectorClipping(features,{candidateClips:[rule]},{source:'openmaptiles',sourceLayer:'building'});
  assert.equal(planned.stats.clippingErrors,0);
  assert(planned.desired.has('number:'+item.id));
  const [residual]=planned.residualData.features;
  assert.deepEqual(residual.properties,item.properties);
  const remaining=polygons(residual.geometry);
  const erased=area(clip.intersection(original,cut));
  assert(west ? erased>1440 && erased<1460 : erased>55 && erased<58);
  const underMask=area(clip.intersection(remaining,cut));
  const retained=polygons(review.retained_northern_extension);
  const northBefore=area(clip.intersection(original,retained));
  const northAfter=area(clip.intersection(remaining,retained));
  assert(underMask<.00001 && Math.abs(northBefore-northAfter)<.03);
  const actualDifference=area(clip.xor(remaining,clip.difference(original,cut)));
  assert(actualDifference<.002);
  result.push({id:item.id,tile:tile.sha256,source_height_m:item.properties.render_height,
    source_components:all.length,source_union_m2:area(original),residual_m2:area(remaining),
    removed_local_m2:erased,remaining_under_mask_m2:underMask,unintended_total_difference_m2:actualDifference,
    retained_north_wing_before_m2:northBefore,retained_north_wing_after_m2:northAfter});
}
fs.writeFileSync(process.argv[3],JSON.stringify({id:contract.id,contract_sha256:sha(contractPath),module_sha256:sha(module),results:result,passed:true},null,2)+'\n');
