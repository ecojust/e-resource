/** Run the shipped OSM clipper on the actual life insurance aggregate and its independent 5 m, 15 m and 26 m neighbors. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const audit=path.dirname(fileURLToPath(import.meta.url));
const project=path.resolve(audit,'../../..'), release=process.env.SHANGHAI_PROJECT_ROOT || project;
const read=f=>JSON.parse(fs.readFileSync(f));
const sha=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const contract=read(path.join(audit,'final-placement-contract.json'));
const source=read(path.join(project,'source/precise',contract.id,'footprint-review.json'));
const merged=read(process.argv[2]);assert.equal(merged.features.length,4);assert.equal(merged.tile_sha256,source.fallback_vector.sha256);
const moduleFile=path.join(release,'src/candidate-vector-clipping.js');
const {planCandidateVectorClipping}=await import(pathToFileURL(moduleFile));
const rule={id:contract.id,geometry:contract.replacement_geometry,osm_replacement_geometry:contract.osm_replacement_geometry,owner:contract.owner,source_feature_ids:contract.source_feature_ids};
const plan=planCandidateVectorClipping(merged.features,{candidateClips:[rule]},{source:'openmaptiles',sourceLayer:'building'});
const input=merged.features.find(f=>f.id===3000545220);
const neighbors=merged.features.filter(f=>[23809960,106284410,2927187770].includes(f.id));
assert(input&&neighbors.length===3);assert.equal(plan.stats.clippingErrors,0);
assert.equal(plan.residualData.features.length,1);
const mask=g=>g.type==='Polygon'?[g.coordinates]:g.coordinates;
const rad=Math.PI/180,k=6371008.8*Math.cos(contract.lat*rad),originY=Math.asinh(Math.tan(contract.lat*rad));
const local=([lon,lat])=>[(lon-contract.lng)*rad*k,(Math.asinh(Math.tan(lat*rad))-originY)*k];
function overlap(feature,region){
  const polygons=globalThis.polygonClipping.intersection(mask(feature.geometry),mask(region));
  return polygons.reduce((sum,polygon)=>sum+polygon.reduce((n,ring,i)=>{
    const xy=ring.map(local);
    return n+(i?-1:1)*Math.abs(xy.slice(1).reduce((s,[x,y],i)=>s+xy[i][0]*y-x*xy[i][1],0))*.5;
  },0),0);
}
const next=plan.residualData.features[0],osm=contract.osm_replacement_geometry;
const ownerBefore=overlap(input,source.source_outline),ownerAfter=overlap(next,source.source_outline);
assert(ownerBefore>1080 && ownerBefore<1110 && ownerAfter<.01);
assert.equal(plan.desired.size,1);assert.equal([...plan.desired.values()][0].id,input.id);
assert(overlap(next,osm)<.00001);
for(const neighbor of neighbors)assert(overlap(neighbor,osm)<.00001);
assert.equal(mask(input.geometry).length,29);
const retained=source.retained_neighbors.map(r=>{
  const before=[input,...neighbors].reduce((sum,f)=>sum+overlap(f,r.geometry),0);
  const after=[next,...neighbors].reduce((sum,f)=>sum+overlap(f,r.geometry),0);
  assert(before>400&&Math.abs(before-after)<.0001);
  return {native_owner:r.id,before_m2:before,after_m2:after};
});
const total=overlap(input,input.geometry),left=overlap(next,input.geometry);
assert(total>14500&&left>13500);assert(Math.abs(total-left-overlap(input,osm))<.001);
const result={id:contract.id,source_url:merged.url,tile_sha256:merged.tile_sha256,source_id:input.id,
 original_polygons:mask(input.geometry).length,unchanged_ids:neighbors.map(f=>f.id),properties:input.properties,stats:plan.stats,
 total_aggregate_m2:total,retained_aggregate_m2:left,owner_before_m2:ownerBefore,owner_after_m2:ownerAfter,
 retained_neighbors:retained,clipper_sha256:sha(moduleFile),contract_sha256:sha(path.join(audit,'final-placement-contract.json')),passed:true};
fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2)+'\n');
