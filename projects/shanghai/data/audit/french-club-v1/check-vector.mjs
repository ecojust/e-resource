/** Run the shipped OSM clipper on the real low podium aggregate alongside the separate 125 m hotel tower. */
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
const merged=read(process.argv[2]);assert.equal(merged.features.length,2);assert.equal(merged.tile_sha256,source.fallback_vector.sha256);
const moduleFile=path.join(release,'src/candidate-vector-clipping.js');
const {planCandidateVectorClipping}=await import(pathToFileURL(moduleFile));
const rule={id:contract.id,geometry:contract.replacement_geometry,osm_replacement_geometry:contract.osm_replacement_geometry,owner:contract.owner,source_feature_ids:contract.source_feature_ids};
const plan=planCandidateVectorClipping(merged.features,{candidateClips:[rule]},{source:'openmaptiles',sourceLayer:'building'});
const input=merged.features.find(f=>f.id===38934830);const other=merged.features.find(f=>f.id===7575068970);assert.ok(input&&other);assert.equal(plan.stats.clippingErrors,0);
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
const next=plan.residualData.features[0];
const ownerBefore=overlap(input,source.source_outline),ownerAfter=overlap(next,source.source_outline);
const osm=contract.osm_replacement_geometry;
const tower=source.retained_neighbors.find(n=>n.id===3550);
const across=source.retained_neighbors.find(n=>n.id===3385);
const towerInOriginal=overlap(other,source.source_outline);
assert(ownerBefore>4800 && ownerAfter<1);
assert.equal(overlap(other,osm),0);
assert(overlap(next,osm)<.00001);
assert.equal(plan.desired.size,1);
assert.equal([...plan.desired.values()][0].id,input.id);
const preserved=[tower,across].map(n=>{
  const before=overlap(input,n.geometry)+overlap(other,n.geometry),after=overlap(next,n.geometry)+overlap(other,n.geometry);
  assert(Math.abs(before-after)<.0001);
  return {local_id:n.id,before_m2:before,after_m2:after};
});
assert(preserved.every(n=>n.before_m2>900));
const result={id:contract.id,source_url:merged.url,tile_sha256:merged.tile_sha256,source_id:input.id,unchanged_source_id:other.id,
  properties:input.properties,tower_properties:other.properties,stats:plan.stats,owner_before_m2:ownerBefore,owner_after_m2:ownerAfter,
  tower_mvt_overlap_before_correction_m2:towerInOriginal,tower_mvt_overlap_with_source_specific_mask_m2:overlap(other,osm),
  untouched_tower_surface_m2:overlap(other,other.geometry),retained_neighbors:preserved,clipper_sha256:sha(moduleFile),
  contract_sha256:sha(path.join(audit,'final-placement-contract.json')),passed:true};
fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2)+'\n');
