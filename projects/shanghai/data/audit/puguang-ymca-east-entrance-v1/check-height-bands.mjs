// Verify the source-identified triangles selected by the real renderer and preserve the original vector footprint.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const [runtime, catalogFile, contractFile, footprintFile, placementFile, manifestFile, output, mode]=process.argv.slice(2);
const read=f=>JSON.parse(fs.readFileSync(f));
const sha=b=>createHash('sha256').update(b).digest('hex');
const load=f=>import(pathToFileURL(path.resolve(runtime,f)));
const THREE=await load('vendor/three.module.js');
const {CandidateCityClipper}=await load('src/candidate-city-clipping.js');
const {CandidateCityState,mergeCandidateCityModels,candidateGeometryContains}=await load('src/candidate-city-integrations.js');
const {markVerifiedOrdinaryAsset}=await load('src/ordinary-asset-verification.js');
const {planCandidateVectorClipping}=await load('src/candidate-vector-clipping.js');
const contract=read(contractFile), footprints=read(footprintFile), placement=read(placementFile), manifest=read(manifestFile);
const catalog=read(catalogFile), id=contract.id, source=contract.owner;
const assetPath='assets/models/candidates/'+id+'/';
const expected=Object.fromEntries([['web','full'],['lod','lod']].map(([variant,role])=>{
 const row=manifest.assets[role],file=path.join(path.dirname(manifestFile),row.file);
 assert.equal(sha(fs.readFileSync(file)),row.sha256);
 return [variant,{...row,file:assetPath+row.file}];
}));
let row=catalog.models.find(m=>m.id===id);
if(mode==='preflight'){assert.equal(row,undefined);row={...contract,name:manifest.name,assets:expected,kind:'building',height_m:15.04};}
else {assert.equal(catalog.models.at(-1).id,id);for(const role of ['web','lod'])for(const k of ['file','sha256','bytes'])assert.equal(row.assets[role][k],expected[role][k]);}
assert.deepEqual(row.display_height_clips,contract.display_height_clips);
assert.deepEqual(row.source_feature_ids,{building:[],building_part:[]});assert.equal(row.replacement_geometry,null);
assert.equal(row.site_replacement,undefined);
const [registered]=mergeCandidateCityModels([],{schema:'candidate-city-integrations-v1',models:[row]});
const rad=Math.PI/180,k=6371008.8*Math.cos(row.lat*rad),log=v=>Math.asinh(Math.tan(v*rad));
const local=(lon,lat,z=0)=>new THREE.Vector3((lon-row.lng)*rad*k,z*k/(6371008.8*Math.cos(lat*rad)),(log(row.lat)-log(lat))*k);
function geographic([x,y]){
 const h=row.heading*rad, e=x*Math.cos(h)+y*Math.sin(h), n=-x*Math.sin(h)+y*Math.cos(h);
 return [row.lng+e/k/rad,Math.atan(Math.sinh(log(row.lat)+n/k))/rad];
}
const scene=new THREE.Scene(),state=new CandidateCityState({getRecords:()=>new Map([[id,registered]]),getScene:()=>scene});
const report={id,preflight:mode==='preflight',catalogCount:catalog.resulting_city_count,catalogSHA256:sha(fs.readFileSync(catalogFile)),roles:{}};
const original=footprints.owners.find(r=>r.local_id===2382),tile=footprints.near_tiles.find(t=>t.feature_local_ids.includes(2382));
const run=(records)=>{
 const gpu=new CandidateCityClipper({THREE,geographicPosition:local});
 const mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());
 gpu.bindObject(mesh,{id:tile.id,parent:{id:source.macro_id},ids:tile.feature_local_ids});
 gpu.update(records);
 return {gpu,mesh};
};
for(const [active,role] of [['full','web'],['distant','lod']]){
 const obj=new THREE.Group();scene.add(obj);registered.object=obj;registered.status='loaded';registered.activeVariant=active;
 markVerifiedOrdinaryAsset(obj,{modelId:id,variant:role,asset:expected[role]});state.sync();
 assert.equal(state.active.length,1);assert.equal(state.clips.length,0);
 assert.deepEqual(state.displayClips,contract.display_height_clips);
 const {gpu,mesh}=run(state.displayClips), s=gpu.getState();
 assert.equal(s.triangles,4);const draw=s.ownerScopedSources.find(d=>d.id===tile.id);
 assert.deepEqual(draw.clip_feature_local_ids,[2382]);assert.equal(draw.triangles,4);
 const data=gpu.texture.image.data;
 const ranges=state.displayClips.map(b=>[local(...b.height_reference,b.min_height).y,local(...b.height_reference,b.max_height).y]);
 const triRanges=[];
 for(let i=0;i<4;i++){
  const a=16*i;assert.equal(data[a+12],2382);
  assert.ok(ranges.some(([lo,hi])=>Math.abs(lo-data[a+6])<.00001&&Math.abs(hi-data[a+7])<.00001));
  triRanges.push([data[a+6],data[a+7]]);
 }
 for(const [lo,hi] of ranges)assert.equal(triRanges.filter(r=>Math.abs(r[0]-lo)<.00001&&Math.abs(r[1]-hi)<.00001).length,2);
 for(const witness of placement.ground_probes){
  const point=geographic(witness.xy);
  assert.equal(candidateGeometryContains(original.geometry,point),witness.source_obstacle,witness.name);
  assert.equal(state.clipsPoint(...point,{name:'overture-buildings',layer:'building',propertyId:original.key.slice(9)}),false);
  const blocked=state.collisions().some(c=>candidateGeometryContains(c.geometry,point));
  assert.equal(blocked,witness.model_obstacle,witness.name);
  assert.equal(blocked||witness.source_obstacle,witness.expected_map==='building');
 }
 const vectors=[];
 for(const provider of ['overture-buildings','openmaptiles']){
  for(const building of footprints.owners){
   const feature={type:'Feature',id:building.local_id,properties:{id:building.key.slice(9)},geometry:building.geometry};
   const plan=planCandidateVectorClipping([feature],{candidateClips:state.clips},{source:provider,sourceLayer:'building'});
   assert.equal(plan.stats.clippingErrors,0);assert.equal(plan.stats.partialIDs,0);assert.equal(plan.stats.candidateIDs,1);assert.equal(plan.stats.retainedCrossingIDs,1);assert.equal(plan.desired.size,0);
   vectors.push([provider,building.local_id]);
  }
 }
 report.roles[role]={sha256:expected[role].sha256,groundWitnesses:placement.ground_probes.length,unmodifiedVectors:vectors,sourceDraw:draw,sourceTriangleHeightRanges:triRanges};
 obj.visible=false;state.sync();assert.deepEqual(state.displayClips,[]);assert.deepEqual(state.collisions(),[]);scene.remove(obj);
 gpu.dispose();mesh.geometry.dispose();mesh.material.dispose();
}
// Audit the whole catalog using the same renderer, with the predecessor's clips active.
const baseRows=catalog.models.filter(m=>m.id!==id);
const clips=records=>records.flatMap(r=>[...(r.replacement_geometry?[{id:r.id,owner:r.owner,owners:r.owners,geometry:r.replacement_geometry}]:[]),...(r.site_replacement?[r.site_replacement]:[]),...(r.display_height_clips||[])]);
const whole=records=>{
 const {gpu,mesh}=run(clips(records));const state=gpu.getState(),source=state.ownerScopedSources.find(s=>s.id===tile.id);
 const value={totalTriangles:state.triangles,sourceOwners:source.clip_feature_local_ids,sourceTriangles:source.triangles};
 gpu.dispose();mesh.geometry.dispose();mesh.material.dispose();return value;
};
report.before=whole(baseRows);report.after=whole([...baseRows,row]);
assert.equal(report.after.totalTriangles-report.before.totalTriangles,4);
assert.equal(report.after.sourceTriangles-report.before.sourceTriangles,4);
assert.deepEqual(report.after.sourceOwners.filter(v=>v!==2382),report.before.sourceOwners);
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(id,report.before.totalTriangles,report.after.totalTriangles,report.after.sourceTriangles);
