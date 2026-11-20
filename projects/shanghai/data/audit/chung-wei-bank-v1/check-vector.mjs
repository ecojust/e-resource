/** Verify the 41 m bank component, the remote component in its aggregate, and the adjacent 5 m source. */
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
assert.equal(vector.sha256,source.fallback_vector.tile_sha256);
const entries=vector.features, target=entries.find(f=>f.id===23763660);
assert.equal(target.properties.render_height,41);
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
const rule=c=>({id:c.id,geometry:c.replacement_geometry,owner:c.owner,source_feature_ids:c.source_feature_ids});
const previous=['texaco-building-v1'].map(tag=>rule(read(path.join(project,'data/audit',tag,'final-placement-contract.json'))));
const plan=rules=>planCandidateVectorClipping(entries,{candidateClips:rules},{source:'openmaptiles',sourceLayer:'building'});
const before=plan(previous),after=plan([...previous,rule(current)]),solo=plan([rule(current)]);
assert.equal(before.stats.clippingErrors,0);assert.equal(after.stats.clippingErrors,0);assert.equal(solo.stats.clippingErrors,0);
function geometry(feature,plan){
  const key=typeof feature.id+':'+feature.id;
  if(!plan.desired.has(key))return feature.geometry;
  const id='candidate-residual:building:'+encodeURIComponent(key);
  return plan.residualData.features.find(f=>f.id===id)?.geometry || {type:'MultiPolygon',coordinates:[]};
}
const region=polygons(current.replacement_geometry);
const overlap=(g,r)=>area(clip.intersection(polygons(g),r));
const beforeTarget=geometry(target,before),afterTarget=geometry(target,after),soloTarget=geometry(target,solo);
assert.equal(polygons(target.geometry).length,2);
assert.equal(polygons(soloTarget).length,1);
assert(overlap(beforeTarget,region)>2100);
assert(overlap(afterTarget,region)<.00001);
const expected=clip.difference(polygons(beforeTarget),region);
assert(area(clip.xor(polygons(afterTarget),expected))<.00001);
for(const other of entries.filter(f=>f.id!==target.id))assert.deepEqual(geometry(other,before),geometry(other,after));
const remote=polygons(target.geometry).find(p=>area(clip.intersection([p],region))<.00001);
assert(remote);assert(area(clip.xor(polygons(afterTarget),[remote]))<.00001);
const low=entries.find(f=>f.id===106284410);
assert.equal(low.properties.render_height,5);
assert.deepEqual(geometry(low,before),geometry(low,after));
const result={site:current.id,tile_sha256:vector.sha256,contract_sha256:sha(file),module_sha256:sha(path.join(root,'src/candidate-vector-clipping.js')),source_id:target.id,
 source_height_m:target.properties.render_height,source_parts:2,retained_parts:1,original_target_m2:overlap(beforeTarget,region),remaining_target_m2:overlap(afterTarget,region),
 remote_before_m2:area([remote]),remote_after_m2:area(polygons(afterTarget)),adjoining_5m_source:low.id,adjoining_parts_unchanged:polygons(low.geometry).length,
 previously_active:previous.map(r=>r.id),passed:true};
fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2)+'\n');
