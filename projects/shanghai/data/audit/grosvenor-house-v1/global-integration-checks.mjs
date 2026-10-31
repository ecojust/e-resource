// Incremental Grosvenor House registration checks. Earlier model evidence is immutable.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import * as THREE from '../../../vendor/three.module.js';
import {mergeCandidateCityModels} from '../../../src/candidate-city-integrations.js';
import {CandidateCityClipper} from '../../../src/candidate-city-clipping.js';
import {planCandidateVectorClipping} from '../../../src/candidate-vector-clipping.js';
import {resolveNavigationRoute} from '../../../src/landmark-navigation.js';
import {walkingPose} from '../../../src/precise-registration-ui.js';

const project=new URL('../../../',import.meta.url),id='huangpu-grosvenor-house';
const baselineCommit='653cb8386d667774c5624b0684aab5dad1cdd68a';
assert.notEqual(baselineCommit,'__PENDING_CATHAY_RELEASE_BASELINE__','Wait for the parent-authorized published Cathay baseline before installing or running this private template');
const read=path=>readFileSync(new URL(path,project)),json=path=>JSON.parse(read(path));
const original=path=>execFileSync('git',['show',`${baselineCommit}:projects/shanghai/${path}`],{cwd:project});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const base=json('data/landmarks.json'),catalog=json('data/candidate-city-integrations.json');
const old=JSON.parse(original('data/candidate-city-integrations.json'));
const footprintPath='data/audit/grosvenor-house-v1/footprint-review.json',footprint=json(footprintPath);
const placement=json('data/global-models/additional-placement.json'),inventory=json('data/global-models/candidate-inventory.json');
const checks=[];function check(name,fn){fn();checks.push(name);}
let merged,added,beforeTriangles,afterTriangles,addedTriangles,sourceRemainderRatio,sourceRemainderArea,sourceRemainderRegions,sourceRemainderSymmetricDifferenceRatio;
function clips(models){
 const result=new Map();
 for(const row of models){
  if(row.replacement_geometry)result.set(row.id,{id:row.id,geometry:row.replacement_geometry,owner:row.owner,owners:row.owners,source_feature_ids:row.source_feature_ids});
  if(row.site_replacement)result.set(row.site_replacement.id,row.site_replacement);
 }
 return [...result.values()];
}
const parts=g=>g.type==='Polygon'?[g.coordinates]:g.coordinates;
const area=g=>parts(g).reduce((sum,rings)=>sum+rings.reduce((s,r,j)=>{
 let a=0;for(let i=1;i<r.length;i++)a+=(r[i-1][0]-r[0][0])*(r[i][1]-r[0][1])-(r[i][0]-r[0][0])*(r[i-1][1]-r[0][1]);return s+(j?-1:1)*Math.abs(a)/2;
},0),0);
check('Grosvenor House adds one overview destination to the existing 74-entry shared map',()=>{
 assert.equal(base.length,40);assert.equal(old.models.length,34);assert.equal(catalog.models.length,35);
 merged=mergeCandidateCityModels(base,catalog);assert.equal(merged.length,75);assert.equal(new Set(merged.map(r=>r.id)).size,75);
 added=merged.find(r=>r.id===id);assert(added?.city_integration);assert.equal(walkingPose(added),null);
 for(const r of merged){const route=resolveNavigationRoute(`#landmark=${r.id}&mode=overview`,{landmarks:merged});assert.equal(route.place.id,r.id);assert.equal(route.mode,'overview');}
 assert.match(read('index.html').toString(),/id="landmark-count">75<\/span>/);
 assert.equal(merged.filter(r=>r.districtId==='310101').length,27);
});
check('all 34 earlier candidate rows, additional placements and historical audits remain unchanged',()=>{
 assert.deepEqual(catalog.models.filter(r=>r.id!==id),old.models);assert.equal(catalog.models.at(-1).id,id);
 const oldInventory=JSON.parse(original('data/global-models/candidate-inventory.json'));
 assert.deepEqual(inventory.records.filter(r=>r.id!==id),oldInventory.records);
 assert.deepEqual(inventory.current_delivery_manifests,['projects/shanghai/assets/models/candidates/'+id+'/manifest.json']);
 const frozen=inventory.prior_incremental_inventory;assert.equal(frozen.file,'data/audit/cathay-mansions-v1/inventory-increment.json');
 const frozenBytes=read(frozen.file);assert.equal(frozen.bytes,frozenBytes.length);assert.equal(frozen.sha256,sha(frozenBytes));
 assert.equal(inventory.verification.current_run_added_files,4);assert.equal(inventory.candidate_manifest_count,37);
 assert.equal(inventory.verification.files,148);assert.equal(inventory.verification.inherited_incremental_files,16);
 const prior=JSON.parse(original('data/global-models/additional-placement.json'));
 assert.deepEqual(placement.records.filter(r=>r.id!==id),prior.records);
 assert.deepEqual(placement.source_contracts.filter(r=>r.file!==footprintPath),prior.source_contracts);
 const changes=execFileSync('git',['diff','--name-only',baselineCommit,'--',':(top)projects/shanghai/data/audit'],{cwd:project}).toString().trim().split('\n').filter(Boolean);
 assert(changes.every(p=>p.startsWith('projects/shanghai/data/audit/grosvenor-house-v1/')));
});
const unchangedFiles=['data/landmarks.json','data/global-models/urban-placement.json','data/global-models/chongming-placement.json',
 'data/audit/global-model-integration-v1/inventory.json','data/audit/new-wing-on-company-v1/inventory-increment.json','data/audit/xinxin-company-v1/inventory-increment.json','data/audit/daxin-company-v1/inventory-increment.json','data/audit/cathay-mansions-v1/inventory-increment.json',
 'src/candidate-city-clipping.js','tests/candidate-city-clipping.test.mjs','src/candidate-vector-clipping.js','src/map-scene.js','src/candidate-overview-camera.js','tools/build_candidate_city_integrations.py'];
check('existing base entries, placement evidence and unaffected production integrations retain their previous bytes',()=>{
 for(const file of unchangedFiles)assert.equal(sha(read(file)),sha(original(file)),file);
});
check('new placement matches the exact reviewed source contract and unique old-building owner',()=>{
 const binding=placement.source_contracts.find(r=>r.file===footprintPath);assert(binding);const raw=read(footprintPath);
 assert.equal(binding.bytes,raw.length);assert.equal(binding.sha256,sha(raw));assert.equal(binding.record,'proposed_placement_contract');
 assert.deepEqual(placement.records.find(r=>r.id===id),footprint.proposed_placement_contract);
 assert.deepEqual(added.source_feature_ids,{building:['6fa0e0aa-bfd0-4d9e-a4bb-16e9088d530e'],building_part:[]});
 assert.equal(added.owner.macro_id,'14-13719-6695');assert.equal(added.owner.feature_local_id,2398);
 assert.deepEqual(added.replacement_geometry,footprint.proposed_placement_contract.replacement_geometry);
 assert.deepEqual(added.collision_geometry,footprint.proposed_placement_contract.collision_geometry);
});
check('the production shader triangulator stays within its 128-triangle budget after this one addition',()=>{
 const clipper=new CandidateCityClipper({THREE,geographicPosition:(lng,lat)=>new THREE.Vector3((lng-121)*100000,0,-(lat-31)*100000)});
 clipper.update(clips(old.models));beforeTriangles=clipper.getState().triangles;assert.equal(beforeTriangles,87);
 clipper.update(clips([added]));addedTriangles=clipper.getState().triangles;assert.equal(addedTriangles,26);
 const ownerIds=new Set(Array.from({length:addedTriangles},(_,i)=>clipper.data[i*16+12]));
 assert.deepEqual([...ownerIds],[2398]);assert(!ownerIds.has(4270));
 assert(Array.from({length:addedTriangles},(_,i)=>clipper.data[i*16+13]).every(value=>value>0));
 clipper.update(clips(catalog.models));afterTriangles=clipper.getState().triangles;
 assert.equal(afterTriangles,beforeTriangles+addedTriangles);assert(afterTriangles<=128);clipper.dispose();
});
check('the reviewed near owner groups include the partial Grosvenor clip only in its own untagged tile',()=>{
 const requirement=footprint.near_group_owner_isolation_requirement;
 assert.equal(requirement.native_near_has_per_feature_id_attribute,false);
 assert(footprint.baseline_western_near_preservation_check.actual_native_projection_intersection_with_provisional_expanded_clip_m2>0);
 const clipper=new CandidateCityClipper({THREE,geographicPosition:(lng,lat)=>new THREE.Vector3((lng-121)*100000,0,-(lat-31)*100000)});
 clipper.update(clips([added]));
 const groups=[requirement.own_group_source_ids,requirement.western_group_source_ids].map((ids,index)=>{
  const group=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());group.add(mesh);
  clipper.bindObject(group,{id:index?'reviewed-west-group-fixture':'reviewed-grosvenor-group-fixture',parent:{id:added.owner.macro_id},ids});
  for(const [material,kind] of [[mesh.material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']]){
   const lib=THREE.ShaderLib[kind],shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:{}};material.onBeforeCompile(shader,{});
   assert.equal(shader.uniforms.candidateHasFeatureIds.value,0);assert.equal(shader.uniforms.candidateClipCount.value,index?0:addedTriangles);
  }
  return {group,mesh};
 });
 const states=clipper.getState().ownerScopedSources;assert.equal(states.length,2);
 assert.equal(states[0].triangles,addedTriangles);assert.deepEqual(states[0].clip_feature_local_ids,[2398]);
 assert.equal(states[1].triangles,0);assert.deepEqual(states[1].clip_feature_local_ids,[]);
 clipper.dispose();for(const {mesh} of groups){mesh.geometry.dispose();mesh.material.dispose();}
});
check('the production vector correction affects only the identified old-building source and defers when its city GLB is active',()=>{
 const own=added.source_feature_ids.building[0],foreign='grosvenor-foreign-owner-fixture';
 const geometry=footprint.proposed_placement_contract.source_limit_geometry||footprint.geometry.source_geometry;assert(geometry);
 const neighbors=footprint.exclusions.required_context_sources;assert(neighbors.some(r=>r.feature_local_id===4270));
 const features=[own,foreign].map(id=>({type:'Feature',id,properties:{id,height:1},geometry}));
 features.push(...neighbors.map(r=>({type:'Feature',id:r.source_id,properties:{id:r.source_id,height:r.map_height_m},geometry:r.source_geometry})));
 const frozenFeatures=JSON.stringify(features);
 const result=planCandidateVectorClipping(features,{candidateClips:clips([added])},{source:'overture-buildings',sourceLayer:'building'});
 assert.equal(JSON.stringify(features),frozenFeatures);
 assert(neighbors.every(r=>![...result.desired.values()].some(value=>value.id===r.source_id)));
 assert.equal(result.desired.size,1);assert.equal([...result.desired.values()][0].id,own);assert.equal(result.stats.clippingErrors,0);
 assert(result.residualData.features.every(f=>f.properties.id===own));assert(result.residualData.features.length<=1);
 sourceRemainderRatio=result.residualData.features.reduce((sum,f)=>sum+area(f.geometry),0)/area(geometry);
 const contract=footprint.proposed_placement_contract;assert.equal(added.partial_model,true);
 assert(contract.source_retained_fraction>0);assert(contract.source_retained_area_runtime_m2>35);
 assert.equal(result.residualData.features.length,1);const retained=result.residualData.features[0].geometry;
 sourceRemainderRegions=parts(retained).length;assert.equal(sourceRemainderRegions,2);
 assert(Math.abs(sourceRemainderRatio-contract.source_retained_fraction)<1e-8,'Both reviewed front regions must remain with the measured source-area fraction');
 sourceRemainderArea=sourceRemainderRatio*contract.runtime_plane_area_m2;
 assert(Math.abs(sourceRemainderArea-contract.source_retained_area_runtime_m2)<0.0001);
 const symmetricDifference=globalThis.polygonClipping.xor(parts(retained),parts(contract.remaining_source_geometry));
 sourceRemainderSymmetricDifferenceRatio=area({type:'MultiPolygon',coordinates:symmetricDifference})/area(geometry);
 assert(sourceRemainderSymmetricDifferenceRatio<1e-8,'Runtime fragments must match the two independently reviewed retained polygons, not merely their area');
 const alreadyCovered=planCandidateVectorClipping(features,{candidateClips:clips([added]),alreadyCovered:id=>id===own},{source:'overture-buildings',sourceLayer:'building'});
 assert.equal(alreadyCovered.desired.size,0);assert.equal(alreadyCovered.residualData.features.length,0);
});
const bindings=[...new Set([...unchangedFiles,'index.html','data/candidate-city-integrations.json','data/global-models/additional-placement.json',
 'data/global-models/candidate-inventory.json',footprintPath,'data/audit/grosvenor-house-v1/global-integration-checks.mjs','src/candidate-city-clipping.js','tests/candidate-city-clipping.test.mjs','src/building-beacons.js','tests/building-beacons.test.mjs','tests/candidate-overview-camera.test.mjs'])]
 .map(file=>{const bytes=read(file);return{file,bytes:bytes.length,sha256:sha(bytes)};});
const report={schema:'grosvenor-global-integration-delta-v1',passed:checks.length,failed:0,checks,baseline_commit:baselineCommit,entry_id:id,
 total_destinations:75,candidate_models:35,huangpu_count:27,route:`index.html#landmark=${id}&mode=overview`,walking_enabled:false,
 clipping_triangles:{before:beforeTriangles,addition:addedTriangles,after:afterTriangles,limit:128},source_remainder_ratio:sourceRemainderRatio,source_remainder_area_runtime_m2:sourceRemainderArea,source_remainder_regions:sourceRemainderRegions,source_remainder_symmetric_difference_ratio:sourceRemainderSymmetricDifferenceRatio,
 scope:'Static production merge/navigation, exact placement evidence binding, shader triangulation, reviewed near-group ownership filtering on synthetic untagged meshes, and vector ownership checks for the new old-building source only. The foreign-ID duplicate and height=1 are identity fixtures; actual neighboring source geometry is also checked without mutation. Near-group fixtures use the actual reviewed tile owner arrays but do not claim loaded native geometry or rendered pixels. Actual model visibility and two unresolved front-source regions, neighboring western source, auditorium and Cathay Mansions preservation require the separate browser check. Existing city GLB owners defer to shader correction instead of vector duplication.',bindings};
writeFileSync(new URL('global-integration-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:checks.length,total:75,candidates:35,triangles:afterTriangles,sourceRemainderRatio}));
