/** Verify removal of Bund 24 from the same 26 m OSM object as Bund 26 and 27. */
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
const entries=vector.features, target=entries.find(f=>f.id===116367860);
assert.equal(target.properties.render_height,26);
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
const previous=['jardine-matheson-v1','glen-line-building-v1'].map(tag=>rule(read(path.join(project,'data/audit',tag,'final-placement-contract.json'))));
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
assert.equal(polygons(target.geometry).length,28);
assert.equal(polygons(soloTarget).length,27);
assert(overlap(beforeTarget,region)>2400);
assert(overlap(afterTarget,region)<.00001);
const expected=clip.difference(polygons(beforeTarget),region);
assert(area(clip.xor(polygons(afterTarget),expected))<.00001);
for(const other of entries.filter(f=>f.id!==target.id))assert.deepEqual(geometry(other,before),geometry(other,after));
const otherOwners=source.other_original_owners_in_group.map(o=>{
  const neighbor=polygons(o.geometry);
  const areaBefore=entries.reduce((s,f)=>s+overlap(geometry(f,before),neighbor),0);
  const areaAfter=entries.reduce((s,f)=>s+overlap(geometry(f,after),neighbor),0);
  assert(areaBefore>300 && Math.abs(areaAfter-areaBefore)<.00001);
  return {local_feature_id:o.id,area_before_m2:areaBefore,area_after_m2:areaAfter};
});
const result={site:current.id,tile_sha256:vector.sha256,contract_sha256:sha(file),module_sha256:sha(path.join(root,'src/candidate-vector-clipping.js')),source_id:target.id,
 src_height_m:target.properties.render_height,original_parts:28,after_solo_parts:27,combined_before_owner_area_m2:overlap(beforeTarget,region),
 combined_after_owner_area_m2:overlap(afterTarget,region),other_aggregate_ids_equal:entries.filter(f=>f.id!==target.id).map(f=>f.id),previously_active:previous.map(r=>r.id),other_owners:otherOwners,passed:true};
fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2)+'\n');
