/** Compare every actual fallback polygon before and after the detached gate is appended. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const audit=path.dirname(fileURLToPath(import.meta.url)),project=path.resolve(audit,'../../..');
const root=process.env.SHANGHAI_PROJECT_ROOT || project;
const read=f=>JSON.parse(fs.readFileSync(f));
const sha=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const file=process.env.MODEL_VERIFIED_CONTRACT || path.join(audit,'final-placement-contract.json');
const current=read(file),source=read(path.join(project,'source/precise',current.id,'footprint-review.json'));
const vector=read(process.argv[2]);
assert.equal(vector.sha256,'1fdad607f7b21b88e0ad7de7768cd646aba6c88aca481544ba3409575d5e2bb2');
const entries=vector.features;
const {planCandidateVectorClipping}=await import(pathToFileURL(path.join(root,'src/candidate-vector-clipping.js')));
const clip=globalThis.polygonClipping;
const polygons=g=>g.type==='Polygon'?[g.coordinates]:g.coordinates;
const rad=Math.PI/180,k=6371008.8*Math.cos(current.lat*rad),yOrigin=Math.asinh(Math.tan(current.lat*rad));
const xy=([lon,lat])=>[(lon-current.lng)*rad*k,(Math.asinh(Math.tan(lat*rad))-yOrigin)*k];
function area(parts){
  return parts.reduce((sum,poly)=>sum+poly.reduce((a,r,j)=>{
    const pts=r.map(xy),v=pts.slice(1).reduce((n,[x,y],i)=>n+pts[i][0]*y-pts[i][1]*x,0);
    return a+(j?-1:1)*Math.abs(v)*.5;
  },0),0);
}
const rule=c=>({id:c.id,geometry:c.replacement_geometry,owner:c.owner,owners:c.owners,
    source_feature_ids:c.source_feature_ids,osm_replacement_geometry:c.osm_replacement_geometry});
const inputCatalog=read(process.argv[4]);
assert(!inputCatalog.models.some(r=>r.id===current.id));
const previous=inputCatalog.models.filter(r=>r.replacement_geometry).map(rule);
const plan=rules=>planCandidateVectorClipping(entries,{candidateClips:rules},{source:'openmaptiles',sourceLayer:'building'});
const before=plan(previous),after=plan([...previous,rule(current)]),solo=plan([rule(current)]);
assert.equal(before.stats.clippingErrors,0);assert.equal(after.stats.clippingErrors,0);assert.equal(solo.stats.clippingErrors,0);
function geometry(feature,plan){
  const key=typeof feature.id+':'+feature.id;
  if(!plan.desired.has(key))return feature.geometry;
  const id='candidate-residual:building:'+encodeURIComponent(key);
  return plan.residualData.features.find(f=>f.id===id)?.geometry || {type:'MultiPolygon',coordinates:[]};
}
const beforeParts=entries.reduce((n,f)=>n+polygons(f.geometry).length,0);
assert.equal(beforeParts,1335);
assert.equal(solo.desired.size,0);
for(const feature of entries)assert.deepEqual(geometry(feature,before),geometry(feature,after));
const lots=source.owners.map(r=>({type:'Feature',id:r.source_key.slice(9),properties:{id:r.source_key.slice(9)},geometry:r.geometry_wgs84}));
const originalPlan=planCandidateVectorClipping(lots,{candidateClips:[rule(current)]},{source:'overture-buildings',sourceLayer:'building'});
assert.equal(originalPlan.stats.clippingErrors,0);
assert.equal(originalPlan.desired.size,1);
const originalOwner=source.owners.find(row=>row.local_id===2100);
const lot=lots.find(row=>row.id===originalOwner.source_key.slice(9));
const removed=area(polygons(lot.geometry))-area(polygons(geometry(lot,originalPlan)));
assert(removed>13.8 && removed<14.3);
for(const other of lots.filter(f=>f.id!==lot.id))assert.deepEqual(geometry(other,originalPlan),other.geometry);
fs.writeFileSync(process.argv[3],JSON.stringify({id:current.id,passed:true,contract_sha256:sha(file),catalog_sha256:sha(process.argv[4]),tile_sha256:vector.sha256,original_features:entries.length,overture_owner:2100,overture_original_uuid:lot.id,overture_removed_m2:removed,overture_other_features_retained:lots.length-1,original_components:beforeParts,unchanged_by_this_gate:beforeParts,legacy_plan_replacements:before.desired.size,extended_plan_replacements:after.desired.size,isolated_plan_replacements:solo.desired.size,vector_clipper_sha256:sha(path.join(root,'src/candidate-vector-clipping.js'))},null,2)+'\n');
