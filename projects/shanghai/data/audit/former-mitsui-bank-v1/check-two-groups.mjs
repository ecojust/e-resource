/* Check each of the two independent near meshes streamed for 50 Jiujiang Road. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const args=process.argv.slice(2);
const caseFile=path.resolve(args[0]);
const proofDir=path.dirname(caseFile);
const contractFile=process.env.MITSUI_CONTRACT||path.join(proofDir,'final-placement-contract.json');
const project=process.env.SHANGHAI_PROJECT_ROOT||path.resolve(proofDir,'../../..');
const read=f=>JSON.parse(fs.readFileSync(f));
const digest=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const contract=read(contractFile),spec=read(caseFile);
const geometryDir=process.env.MITSUI_SOURCE_PROJECT||project;
const review=read(path.join(geometryDir,'source/precise',contract.id,'footprint-review.json'));
const catalogFile=path.join(project,'data/candidate-city-integrations.json');
const catalog=read(catalogFile);
const model=catalog.models.find(m=>m.id===contract.id);
const preflight=args.includes('--fixture');
if(preflight)assert.equal(model,undefined);else{
 assert.ok(model);for(const k of ['owner','owners','source_feature_ids','replacement_geometry','collision_geometry','model_geometry_sha256'])assert.deepEqual(model[k],contract[k],k);
}
const row=preflight?contract:model;
const local=f=>path.join(project,f);
const THREE=await import(pathToFileURL(local('vendor/three.module.js')));
const {CandidateCityClipper}=await import(pathToFileURL(local('src/candidate-city-clipping.js')));
const {candidateGeometryContains}=await import(pathToFileURL(local('src/candidate-city-integrations.js')));
const {planCandidateVectorClipping}=await import(pathToFileURL(local('src/candidate-vector-clipping.js')));
const ids=contract.owners.map(o=>o.feature_local_id);
assert.deepEqual([...ids].sort((a,b)=>a-b),[88,2301]);
const rad=Math.PI/180,k=6371008.8*Math.cos(row.lat*rad),l0=Math.asinh(Math.tan(row.lat*rad)),h=row.heading*rad;
function position(lng,lat,height=0){
 return new THREE.Vector3((lng-row.lng)*rad*k,height*k/(6371008.8*Math.cos(lat*rad)),(l0-Math.asinh(Math.tan(lat*rad)))*k);
}
function point(x,y){
 const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
 return [row.lng+east/k/rad,Math.atan(Math.sinh(l0+north/k))/rad];
}
function inspect(models){
 const clipper=new CandidateCityClipper({THREE,geographicPosition:position});
 const objects=[];
 const groups=review.near_tiles.filter(g=>g.feature_local_ids.some(i=>ids.includes(i)));
 assert.equal(groups.length,2);
 const clips=new Map();
 for(const m of models){
  if(m.replacement_geometry)clips.set(m.id,{id:m.id,owner:m.owner,owners:m.owners,geometry:m.replacement_geometry});
  if(m.site_replacement)clips.set(m.site_replacement.id,m.site_replacement);
 }
 for(const g of groups){
  const cube=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());
  clipper.bindObject(cube,{id:g.id,parent:{id:review.frozen_macro},ids:g.feature_local_ids});objects.push(cube);
 }
 clipper.update([...clips.values(),...models.flatMap(m=>m.display_height_clips||[])]);
 const s=clipper.getState(),tables=[...clipper.macroTables.values()].map(t=>t.triangles);
 const out={triangles:s.triangles,perDrawLimit:s.triangleLimit,maxMacroTriangles:Math.max(...tables),groups:s.ownerScopedSources};
 for(const obj of objects){clipper.releaseObject(obj);obj.geometry.dispose();obj.material.dispose();}clipper.dispose();
 return out;
}
const initial=catalog.models.filter(m=>m.id!==row.id);
const before=inspect(initial),after=inspect([...initial,row]);
assert.equal(after.triangles-before.triangles,spec.addedTriangles);
assert.ok(after.maxMacroTriangles<=after.perDrawLimit);
for(const g of spec.ownerGroups){
 const b=before.groups.find(t=>t.id===g.id),a=after.groups.find(t=>t.id===g.id);
 assert.deepEqual(b.clip_feature_local_ids,g.existingOwners);
 assert.deepEqual(a.clip_feature_local_ids,[...g.existingOwners,...g.targetOwners]);
 assert.equal(a.triangles,g.triangles);assert.equal(a.triangles-b.triangles,g.triangles);
}
const vector=[];
const targets=new Set(ids);
for(const source of ['overture-buildings','openmaptiles']){
 for(const owner of review.owners.filter(o=>targets.has(o.local_id)||spec.neighbors.includes(o.local_id))){
  const geometry=owner.geometry_wgs84??owner.geometry;
  const feature={type:'Feature',id:1,properties:{id:owner.key.slice(9)},geometry};
  const plan=planCandidateVectorClipping([feature],{candidateClips:[{...row,geometry:row.replacement_geometry}]},{source,sourceLayer:'building'});
  const target=targets.has(owner.local_id);assert.equal(plan.stats.clippingErrors,0);
  assert.equal(plan.desired.size,Number(target));assert.equal(plan.residualData.features.length,Number(target));
  if(target){
   const residual=plan.residualData.features[0].geometry;
   for(const witness of spec.ground.filter(v=>v.ownerLocalId===owner.local_id&&v.modelObstacle===false))assert.ok(candidateGeometryContains(residual,point(...witness.xy)),witness.name);
   assert.equal(candidateGeometryContains(residual,point(0,2.0)),false);
  }
  vector.push({source,owner:owner.local_id,hidden:!!plan.desired.size,residual:!!plan.residualData.features.length});
 }
}
const ground=spec.ground.map(w=>{
 const location=point(...w.xy),collision=candidateGeometryContains(contract.collision_geometry,location),cut=candidateGeometryContains(contract.replacement_geometry,location);
 assert.equal(collision,w.modelObstacle??(w.expected==='building'),w.name);assert.equal(cut,w.cut??(w.expected==='building'),w.name);
 return {name:w.name,location,collision,cut};
});
const out=process.env.QA_OUTPUT_DIR||proofDir;fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,preflight?'two-group-preflight.json':'runtime-placement.json'),JSON.stringify({id:contract.id,preflight,
 originalCatalogRows:catalog.resulting_city_count,catalogSha256:digest(catalogFile),checkerSha256:digest(fileURLToPath(import.meta.url)),contractSha256:digest(contractFile),
 modules:Object.fromEntries(['src/candidate-vector-clipping.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js'].map(f=>[f,digest(local(f))])),before,after,ground,vector},null,2)+'\n');
console.log(preflight?'fixture':'frozen city',after.groups.map(v=>[v.feature_local_ids,v.clip_feature_local_ids,v.triangles]),ground.length,vector.length);
