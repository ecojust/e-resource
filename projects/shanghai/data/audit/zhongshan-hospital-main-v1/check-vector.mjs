/* Run the shipped vector clipper against the hospital campus aggregate and two independent neighboring source IDs. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const audit=path.dirname(fileURLToPath(import.meta.url)),project=path.resolve(audit,'../../..');
const release=process.env.SHANGHAI_PROJECT_ROOT || project;
const read=file=>JSON.parse(fs.readFileSync(file));
const digest=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const input=read(process.argv[2]),contract=read(path.join(audit,'final-placement-contract.json'));
const source=read(path.join(project,'source/precise',contract.id,'footprint-review.json'));
await import(pathToFileURL(path.join(release,'vendor/polygon-clipping.umd.min.js')));
const clipper=path.join(release,'src/candidate-vector-clipping.js');
const {planCandidateVectorClipping}=await import(pathToFileURL(clipper));
const plan=planCandidateVectorClipping(input.features,{candidateClips:[{id:contract.id,geometry:contract.replacement_geometry,
  source_feature_ids:contract.source_feature_ids,owner:contract.owner}]},{source:'openmaptiles',sourceLayer:'building'});
const primary=input.features.find(f=>f.id===38934830);
assert.equal(plan.stats.clippingErrors,0);assert.equal(plan.desired.size,1);
assert.equal([...plan.desired.values()][0].id,primary.id);assert.equal(plan.residualData.features.length,1);
const retained=plan.residualData.features[0];
const polygons=g=>g.type==='Polygon'?[g.coordinates]:g.coordinates;
const rad=Math.PI/180,k=6371008.8*Math.cos(contract.lat*rad),y0=Math.asinh(Math.tan(contract.lat*rad));
const local=([x,y])=>[(x-contract.lng)*rad*k,(Math.asinh(Math.tan(y*rad))-y0)*k];
function overlap(a,b){
  return globalThis.polygonClipping.intersection(polygons(a),polygons(b)).reduce((sum,p)=>sum+p.reduce((total,ring,index)=>{
    const points=ring.map(local);
    const area=Math.abs(points.slice(1).reduce((n,[x,y],i)=>n+points[i][0]*y-x*points[i][1],0))*.5;
    return total+(index?-area:area);
  },0),0);
}
const old=overlap(primary.geometry,source.source_outline),remaining=overlap(retained.geometry,source.source_outline);
const cut=overlap(primary.geometry,contract.replacement_geometry);
assert(old>3000 && remaining>1850 && old-remaining>940 && old-remaining<1050);
assert(cut>940 && overlap(retained.geometry,contract.replacement_geometry)<.0001);
const untouched=input.features.filter(f=>f!==primary);
for(const f of untouched)assert.equal(overlap(f.geometry,contract.replacement_geometry),0);
const neighbors=source.retained_neighbors.map(item=>{
  const source=sum=>sum.reduce((a,g)=>a+overlap(g,item.geometry),0);
  const before=source(input.features.map(f=>f.geometry)),after=source([retained.geometry,...untouched.map(f=>f.geometry)]);
  assert(Math.abs(before-after)<.0001);
  return {local_id:item.id,name:item.name,source_overlap_before_m2:before,source_overlap_after_m2:after};
});
const report={id:contract.id,source_url:input.url,tile_sha256:input.sha256,clipper_sha256:digest(clipper),
  contract_sha256:digest(path.join(audit,'final-placement-contract.json')),replaced_source:primary.id,unchanged_sources:untouched.map(f=>f.id),
  stats:plan.stats,original_owner_vector_area_m2:old,retained_owner_vector_area_m2:remaining,
  cut_vector_area_m2:cut,neighbors,passed:true};
fs.writeFileSync(process.argv[3],JSON.stringify(report,null,2)+'\n');
