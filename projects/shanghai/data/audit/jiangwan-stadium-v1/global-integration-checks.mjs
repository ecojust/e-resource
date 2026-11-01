// Incremental Jiangwan Stadium registration, separate source clips and open-ground checks.
// Run only after the reviewed contract and final model have entered the shared catalogue.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
import * as THREE from '../../../vendor/three.module.js';
import {mergeCandidateCityModels,candidateGeometryContains,validCandidateGeometry} from '../../../src/candidate-city-integrations.js';
import {CandidateCityClipper} from '../../../src/candidate-city-clipping.js';
import {planCandidateVectorClipping} from '../../../src/candidate-vector-clipping.js';
import {resolveNavigationRoute} from '../../../src/landmark-navigation.js';
import {walkingPose} from '../../../src/precise-registration-ui.js';

const project=new URL('../../../',import.meta.url),id='yangpu-jiangwan-stadium';
const baselineCommit='96e4dfaff588222475c25a66af1c84a24b45a475';
const read=path=>readFileSync(new URL(path,project)),json=path=>JSON.parse(read(path));
const original=path=>execFileSync('git',['show',`${baselineCommit}:projects/shanghai/${path}`],{cwd:project,maxBuffer:8*1024*1024});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};
context.exports=context.module.exports;context.self=context;context.globalThis=context;
vm.runInNewContext(read('vendor/maplibre-gl.js').toString(),context);const maplibre=context.module.exports;
const origin=maplibre.MercatorCoordinate.fromLngLat([121.4737,31.2304]),unit=origin.meterInMercatorCoordinateUnits();
const geographicPosition=(lng,lat)=>{const p=maplibre.MercatorCoordinate.fromLngLat([lng,lat]);return new THREE.Vector3((p.x-origin.x)/unit,0,(p.y-origin.y)/unit);};
const base=json('data/landmarks.json'),catalog=json('data/candidate-city-integrations.json'),old=JSON.parse(original('data/candidate-city-integrations.json'));
const footprintPath='data/audit/jiangwan-stadium-v1/footprint-review.json',footprint=json(footprintPath),contract=footprint.proposed_placement_contract;
// This evidence is derived from actual frozen city sources and final model geometry.
// Missing evidence must fail: no provisional source or collision fixtures are substituted.
const evidence=footprint.runtime_validation;
assert(evidence&&evidence.final_model_geometry_verified===true,'Require final actual-model runtime evidence');
const placement=json('data/global-models/additional-placement.json'),inventory=json('data/global-models/candidate-inventory.json');
const manifest=json(`assets/models/candidates/${id}/manifest.json`);
const checks=[];function check(name,fn){fn();checks.push(name);}
const parts=g=>g?.type==='Polygon'?[g.coordinates]:g?.type==='MultiPolygon'?g.coordinates:[];
const area=g=>parts(g).reduce((total,rings)=>total+rings.reduce((sum,r,k)=>{let a=0;for(let i=1;i<r.length;i++)a+=(r[i-1][0]-r[0][0])*(r[i][1]-r[0][1])-(r[i][0]-r[0][0])*(r[i-1][1]-r[0][1]);return sum+(k?-1:1)*Math.abs(a)/2;},0),0);
const anchor=maplibre.MercatorCoordinate.fromLngLat([contract.lng,contract.lat]),metre=anchor.meterInMercatorCoordinateUnits();
const metricArea=g=>area({type:'MultiPolygon',coordinates:parts(g).map(rings=>rings.map(ring=>ring.map(([lng,lat])=>{const p=maplibre.MercatorCoordinate.fromLngLat([lng,lat]);return[(p.x-anchor.x)/metre,(p.y-anchor.y)/metre];})))});
function fromLocal([x,y]){const a=contract.heading*Math.PI/180,c=Math.cos(a),s=Math.sin(a);const p=new maplibre.MercatorCoordinate(anchor.x+(c*x+s*y)*metre,anchor.y+(s*x-c*y)*metre).toLngLat();return[p.lng,p.lat];}
function clips(models){const result=new Map();for(const row of models){if(row.replacement_geometry)result.set(row.id,{id:row.id,geometry:row.replacement_geometry,owner:row.owner,owners:row.owners,source_feature_ids:row.source_feature_ids});if(row.site_replacement)result.set(row.site_replacement.id,row.site_replacement);}return[...result.values()];}
const expectedOwners=new Map([[1646,{source_id:'b773143c-051f-411b-86bf-281e395a0576',triangles:25}],[1816,{source_id:'c8ecf662-6618-4e44-881a-91f99f08907b',triangles:20}]]);
let merged,added,newClips,beforeTriangles,addedTriangles,afterTriangles,historicalTextureRowsEqual,nearChecks=[],vectorChecks,groundChecks;

check('stadium adds one overview destination to the existing77-entry map and retains all37 candidate rows',()=>{
 assert.equal(base.length,40);assert.equal(old.models.length,37);assert.equal(catalog.models.length,38);
 assert.deepEqual(catalog.models.filter(r=>r.id!==id),old.models);
 merged=mergeCandidateCityModels(base,catalog);assert.equal(merged.length,78);assert.equal(new Set(merged.map(r=>r.id)).size,78);
 added=merged.find(r=>r.id===id);assert(added?.city_integration);assert.equal(walkingPose(added),null);
 for(const r of merged){const route=resolveNavigationRoute(`#landmark=${r.id}&mode=overview`,{landmarks:merged});assert.equal(route.place.id,r.id);assert.equal(route.mode,'overview');}
 assert.equal(read('index.html').toString().match(/id="landmark-count">(\d+)<\/span>/)?.[1],'78','Static index count must match the shared catalogue');
 assert.equal(merged.filter(r=>r.districtId==='310110').length,3);assert.equal(merged.filter(r=>r.districtId==='310101').length,28);
});

const unchangedFiles=['data/landmarks.json','data/global-models/urban-placement.json','data/global-models/chongming-placement.json','data/model-todo/named-map-leads.json','vendor/maplibre-gl.js','data/audit/global-model-integration-v1/inventory.json',
 ...['new-wing-on-company','xinxin-company','daxin-company','cathay-mansions','grosvenor-house','municipal-council','yangpu-city-hall'].map(name=>`data/audit/${name}-v1/inventory-increment.json`),
 'src/candidate-city-clipping.js','src/candidate-vector-clipping.js','src/map-scene.js','src/candidate-overview-camera.js','tests/candidate-city-clipping.test.mjs'];
check('new four-asset inventory inherits39 frozen manifests and leaves previous placements, assets and audits unchanged',()=>{
 const previousInventory=JSON.parse(original('data/global-models/candidate-inventory.json'));
 assert.deepEqual(inventory.records.filter(r=>r.id!==id),previousInventory.records);
 assert.deepEqual(inventory.current_delivery_manifests,[`projects/shanghai/assets/models/candidates/${id}/manifest.json`]);
 const frozen=inventory.prior_incremental_inventory;assert.equal(frozen.file,'data/audit/yangpu-city-hall-v1/inventory-increment.json');const frozenBytes=read(frozen.file);assert.equal(frozenBytes.length,frozen.bytes);assert.equal(sha(frozenBytes),frozen.sha256);
 assert.equal(Object.keys(manifest.assets).length,4);const addedBytes=Object.values(manifest.assets).reduce((sum,a)=>sum+a.bytes,0);
 assert.equal(inventory.verification.current_run_added_files,4);assert.equal(inventory.verification.inherited_incremental_files,28);assert.equal(inventory.candidate_manifest_count,40);assert.equal(inventory.verification.files,160);assert.equal(inventory.verification.bytes,623518100+addedBytes);
 const previousPlacement=JSON.parse(original('data/global-models/additional-placement.json'));
 assert.deepEqual(placement.records.filter(r=>r.id!==id),previousPlacement.records);assert.deepEqual(placement.source_contracts.filter(r=>r.file!==footprintPath),previousPlacement.source_contracts);
 for(const file of unchangedFiles)assert.equal(sha(read(file)),sha(original(file)),file);
 for(const [directory,allowed] of [['data/audit','data/audit/jiangwan-stadium-v1/'],['assets/models/candidates',`assets/models/candidates/${id}/`],['source/precise',`source/precise/${id}/`]]){
  const changes=execFileSync('git',['diff','--name-status',baselineCommit,'--',`:(top)projects/shanghai/${directory}`],{cwd:project}).toString().trim().split('\n').filter(Boolean);
  for(const line of changes){const [status,file]=line.split('\t');assert(['A','M'].includes(status));assert(file.startsWith('projects/shanghai/'+allowed),line);}
 }
});

check('one final stadium asset binds two independent source masks without duplicating their owners',()=>{
 const binding=placement.source_contracts.find(r=>r.file===footprintPath),raw=read(footprintPath);assert(binding);assert.equal(binding.bytes,raw.length);assert.equal(binding.sha256,sha(raw));assert.equal(binding.record,'proposed_placement_contract');assert.deepEqual(placement.records.find(r=>r.id===id),contract);
 for(const key of ['replacement_geometry','source_feature_ids','collision_geometry','site_replacement','owner','partial_model'])assert.deepEqual(added[key],contract[key],key);
 assert.equal(added.owner.feature_local_id,1646);assert.equal(added.site_replacement.owner.feature_local_id,1816);
 assert.equal(added.site_replacement.id,'yangpu-jiangwan-stadium-east-stand-replacement');
 assert(!added.owners?.length&&!added.site_replacement.owners?.length,'Each mask has its own single owner');
 newClips=clips([added]);assert.equal(newClips.length,2);
 for(const clip of newClips){const expected=expectedOwners.get(clip.owner.feature_local_id);assert(expected);assert.deepEqual(clip.source_feature_ids,{building:[expected.source_id],building_part:[]});assert(validCandidateGeometry(clip.geometry));}
 for(const [role,key] of [['raw','raw'],['web','full'],['lod','lod']])assert.equal(contract.model_geometry_sha256[role],manifest.assets[key].sha256);
 const named=json('data/model-todo/named-map-leads.json');assert.equal(named.records.length,1036);for(const source of expectedOwners.values())assert(!named.records.some(r=>r.id===source.source_id),'These sources must not increment the frozen named association count');
});

check('45 new display triangles fit192 rows and preserve the previous147 rows byte for byte',()=>{
 const clipper=new CandidateCityClipper({THREE,geographicPosition});clipper.update(clips(old.models));beforeTriangles=clipper.getState().triangles;assert.equal(beforeTriangles,147);const oldPayload=Buffer.from(clipper.data.slice(0,beforeTriangles*16).buffer);
 clipper.update(newClips);addedTriangles=clipper.getState().triangles;assert.equal(addedTriangles,45);assert.equal(contract.expected_replacement_triangle_count,45);
 for(const [owner,expected] of expectedOwners)assert.equal(Array.from({length:addedTriangles},(_,i)=>clipper.data[i*16+12]).filter(x=>x===owner).length,expected.triangles);
 clipper.update(clips(catalog.models));afterTriangles=clipper.getState().triangles;assert.equal(afterTriangles,192);assert.equal(afterTriangles,beforeTriangles+addedTriangles);assert.equal(clipper.getState().triangleLimit,192);assert.equal(contract.expected_global_clip_capacity,192);
 historicalTextureRowsEqual=oldPayload.equals(Buffer.from(clipper.data.buffer,0,beforeTriangles*64));assert(historicalTextureRowsEqual);clipper.dispose();
});

check('each reviewed near group receives only its own source mask, including depth and distance materials',()=>{
 assert.equal(evidence.near_groups.length,2);const clipper=new CandidateCityClipper({THREE,geographicPosition});clipper.update(newClips);const meshes=[];
 for(const groupSpec of evidence.near_groups){
  const expected=expectedOwners.get(groupSpec.clip_feature_local_ids[0]);assert(expected);assert.equal(groupSpec.clip_feature_local_ids.length,1);assert.equal(groupSpec.triangles,expected.triangles);
  assert(groupSpec.feature_local_ids.includes(groupSpec.clip_feature_local_ids[0]));
  for(const foreign of [false,true]){
   const ids=foreign?[999999]:groupSpec.feature_local_ids,group=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());group.add(mesh);meshes.push(mesh);
   clipper.bindObject(group,{id:foreign?'synthetic-foreign-control-'+groupSpec.group_id:groupSpec.group_id,parent:{id:groupSpec.macro_id},ids});
   for(const [material,kind] of [[mesh.material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']]){const lib=THREE.ShaderLib[kind],shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:{}};material.onBeforeCompile(shader,{});assert.equal(shader.uniforms.candidateClipCount.value,foreign?0:expected.triangles);assert.equal(shader.uniforms.candidateHasFeatureIds.value,0);}
  }
 }
 nearChecks=clipper.getState().ownerScopedSources;
 for(const spec of evidence.near_groups){const state=nearChecks.find(r=>r.id===spec.group_id);assert.deepEqual([...state.feature_local_ids].sort((a,b)=>a-b),[...spec.feature_local_ids].sort((a,b)=>a-b));assert.deepEqual(state.clip_feature_local_ids,spec.clip_feature_local_ids);}
 clipper.dispose();for(const mesh of meshes){mesh.geometry.dispose();mesh.material.dispose();}
});

check('vector replacement removes both complete main sources and retains unrelated source identities',()=>{
 assert.equal(evidence.source_features.length,2);assert(evidence.context_sources.length>0);
 const real=evidence.source_features.map(r=>({type:'Feature',id:r.source_id,properties:{id:r.source_id,height:r.map_height_m??1},geometry:r.geometry_wgs84}));
 assert.deepEqual(real.map(r=>r.id).sort(),[...expectedOwners.values()].map(r=>r.source_id).sort());
 const features=[...real,...real.map((r,i)=>({...structuredClone(r),id:'synthetic-same-footprint-foreign-'+i,properties:{id:'synthetic-same-footprint-foreign-'+i,height:1}})),...evidence.context_sources.map(r=>({type:'Feature',id:r.source_id,properties:{id:r.source_id,height:r.map_height_m??1},geometry:r.geometry_wgs84}))];
 const frozen=JSON.stringify(features),result=planCandidateVectorClipping(features,{candidateClips:newClips},{source:'overture-buildings',sourceLayer:'building'});
 assert.equal(JSON.stringify(features),frozen);assert.equal(result.stats.clippingErrors,0);assert.equal(result.desired.size,2);assert.deepEqual([...result.desired.values()].map(r=>r.id).sort(),real.map(r=>r.id).sort());assert.equal(result.residualData.features.length,0);
 const sourceAreas=real.map(r=>({id:r.id,source_area_runtime_m2:metricArea(r.geometry),residual_area_m2:0}));
 const covered=planCandidateVectorClipping(features,{candidateClips:newClips,alreadyCovered:id=>real.some(r=>r.id===id)},{source:'overture-buildings',sourceLayer:'building'});assert.equal(covered.desired.size,0);assert.equal(covered.residualData.features.length,0);
 vectorChecks={source_areas:sourceAreas,real_context_features:evidence.context_sources.length,synthetic_same_footprint_controls:2,zero_residual_for_both_main_sources:true};
});

check('production collision keeps the field and reviewed passages open while covering actual low obstacles',()=>{
 assert(validCandidateGeometry(added.collision_geometry,{collision:true}));assert(evidence.ground_probes.some(p=>p.expected===null));assert(evidence.ground_probes.some(p=>p.expected==='building'));
 for(const p of evidence.ground_probes){assert.equal(candidateGeometryContains(added.collision_geometry,p.wgs84),p.expected==='building',p.name);if(p.local_xy_m){const point=fromLocal(p.local_xy_m);assert(point.every((v,i)=>Math.abs(v-p.wgs84[i])<1e-10),p.name);}}
 assert(evidence.open_ground_areas.length>=2,'Require actual open field and at least one reviewed entrance/passage area');
 const openAreas=evidence.open_ground_areas.map(p=>{const intersection=globalThis.polygonClipping.intersection(parts(added.collision_geometry),parts(p.geometry_wgs84)),intersectionArea=metricArea({type:'MultiPolygon',coordinates:intersection});assert(intersectionArea<1e-6,p.name);return{name:p.name,ground_collision_intersection_m2:intersectionArea};});
 groundChecks={collision_parts:parts(added.collision_geometry).length,closed_ring_lengths:parts(added.collision_geometry).map(rings=>rings.map(r=>r.length)),positive_probes:evidence.ground_probes.filter(p=>p.expected==='building').length,negative_probes:evidence.ground_probes.filter(p=>p.expected===null).length,open_areas:openAreas,note:'Production two-dimensional containment and area intersections complement independent actual-triangle occupancy checks. No stadium interior or elevated walking mode is enabled.'};
});

const bindings=[...new Set([...unchangedFiles,'src/building-beacons.js','src/candidate-city-integrations.js','tools/build_candidate_city_integrations.py','tests/building-beacons.test.mjs','tests/candidate-geometry.test.mjs','tests/candidate-catalog-increment.test.py','index.html','data/candidate-city-integrations.json','data/global-models/additional-placement.json','data/global-models/candidate-inventory.json',footprintPath,`assets/models/candidates/${id}/manifest.json`,'data/audit/jiangwan-stadium-v1/global-integration-checks.mjs'])].map(file=>{const b=read(file);return{file,bytes:b.length,sha256:sha(b)};});
const report={schema:'jiangwan-stadium-global-integration-delta-v1',passed:checks.length,failed:0,checks,baseline_commit:baselineCommit,entry_id:id,total_destinations:78,candidate_models:38,yangpu_count:3,huangpu_count:28,route:`index.html#landmark=${id}&mode=overview`,walking_enabled:false,clipping_triangles:{before:beforeTriangles,addition:addedTriangles,after:afterTriangles,limit:192},historical_texture_rows_equal:historicalTextureRowsEqual,historical_texture_payload_bytes_compared:147*64,near_group_fixture_checks:nearChecks,vector_checks:vectorChecks,ground_collision:groundChecks,scope:'Static production merge/navigation, immutable previous catalogue and texture rows, independent source and near ownership, exact frozen contract, real source vector correction and production collision. Near meshes here are explicit shader fixtures using independently decoded native owner lists; actual native geometry preservation belongs to mapping evidence and final browser HTTP/rendering. No historical asset matrix or fake model is replayed.',bindings};
writeFileSync(new URL('global-integration-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:checks.length,total:78,candidates:38,triangles:afterTriangles,groundChecks}));
