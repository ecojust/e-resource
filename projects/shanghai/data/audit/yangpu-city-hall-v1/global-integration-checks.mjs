// Incremental Yangpu City Hall registration and ground-road collision checks.
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
const project=new URL('../../../',import.meta.url),id='yangpu-former-shanghai-city-hall';
const baselineCommit='c5eadbea297bb9d23d0658b2244d1e17034bbcb6';
const read=path=>readFileSync(new URL(path,project)),json=path=>JSON.parse(read(path));
const original=path=>execFileSync('git',['show',`${baselineCommit}:projects/shanghai/${path}`],{cwd:project,maxBuffer:8*1024*1024});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};context.exports=context.module.exports;context.self=context;context.globalThis=context;
vm.runInNewContext(read('vendor/maplibre-gl.js').toString(),context);const maplibre=context.module.exports;
const origin=maplibre.MercatorCoordinate.fromLngLat([121.4737,31.2304]),unit=origin.meterInMercatorCoordinateUnits();
const geographicPosition=(lng,lat)=>{const p=maplibre.MercatorCoordinate.fromLngLat([lng,lat]);return new THREE.Vector3((p.x-origin.x)/unit,0,(p.y-origin.y)/unit);};
const base=json('data/landmarks.json'),catalog=json('data/candidate-city-integrations.json'),old=JSON.parse(original('data/candidate-city-integrations.json'));
const footprintPath='data/audit/yangpu-city-hall-v1/footprint-review.json',footprint=json(footprintPath),contract=footprint.proposed_placement_contract;
const placement=json('data/global-models/additional-placement.json'),inventory=json('data/global-models/candidate-inventory.json');
const checks=[];function check(name,fn){fn();checks.push(name);}
const parts=g=>g.type==='Polygon'?[g.coordinates]:g.coordinates;
const area=g=>parts(g).reduce((total,rings)=>total+rings.reduce((sum,r,k)=>{let a=0;for(let i=1;i<r.length;i++)a+=(r[i-1][0]-r[0][0])*(r[i][1]-r[0][1])-(r[i][0]-r[0][0])*(r[i-1][1]-r[0][1]);return sum+(k?-1:1)*Math.abs(a)/2;},0),0);
const anchor=maplibre.MercatorCoordinate.fromLngLat([contract.lng,contract.lat]),metre=anchor.meterInMercatorCoordinateUnits();
const metricArea=g=>area({type:'MultiPolygon',coordinates:parts(g).map(rings=>rings.map(ring=>ring.map(([lng,lat])=>{const p=maplibre.MercatorCoordinate.fromLngLat([lng,lat]);return[(p.x-anchor.x)/metre,(p.y-anchor.y)/metre];})))});
function fromLocal([x,y]){const a=contract.heading*Math.PI/180,c=Math.cos(a),s=Math.sin(a);const p=new maplibre.MercatorCoordinate(anchor.x+(c*x+s*y)*metre,anchor.y+(s*x-c*y)*metre).toLngLat();return[p.lng,p.lat];}
function clips(models){const result=new Map();for(const row of models){if(row.replacement_geometry)result.set(row.id,{id:row.id,geometry:row.replacement_geometry,owner:row.owner,owners:row.owners,source_feature_ids:row.source_feature_ids});if(row.site_replacement)result.set(row.site_replacement.id,row.site_replacement);}return[...result.values()];}
let merged,added,beforeTriangles,addedTriangles,afterTriangles,historicalTextureRowsEqual,sourceAreaRuntime,sourceRemainderArea,neighborCount,groundChecks;
check('City Hall adds one overview destination to the existing76-entry shared map',()=>{
 assert.equal(base.length,40);assert.equal(old.models.length,36);assert.equal(catalog.models.length,37);
 merged=mergeCandidateCityModels(base,catalog);assert.equal(merged.length,77);assert.equal(new Set(merged.map(r=>r.id)).size,77);
 added=merged.find(r=>r.id===id);assert(added?.city_integration);assert.equal(walkingPose(added),null);
 for(const r of merged){const route=resolveNavigationRoute(`#landmark=${r.id}&mode=overview`,{landmarks:merged});assert.equal(route.place.id,r.id);assert.equal(route.mode,'overview');}
 assert.match(read('index.html').toString(),/id="landmark-count">77<\/span>/);
 assert.equal(merged.filter(r=>r.districtId==='310110').length,2);assert.equal(merged.filter(r=>r.districtId==='310101').length,28);
});
check('all36 previous candidate rows, placements and historical audits remain unchanged',()=>{
 assert.deepEqual(catalog.models.filter(r=>r.id!==id),old.models);assert.equal(catalog.models.at(-1).id,id);
 assert.deepEqual(inventory.records.filter(r=>r.id!==id),JSON.parse(original('data/global-models/candidate-inventory.json')).records);
 assert.deepEqual(inventory.current_delivery_manifests,['projects/shanghai/assets/models/candidates/'+id+'/manifest.json']);
 const frozen=inventory.prior_incremental_inventory;assert.equal(frozen.file,'data/audit/municipal-council-v1/inventory-increment.json');const bytes=read(frozen.file);assert.equal(bytes.length,frozen.bytes);assert.equal(sha(bytes),frozen.sha256);
 assert.equal(inventory.verification.current_run_added_files,4);assert.equal(inventory.verification.inherited_incremental_files,24);assert.equal(inventory.candidate_manifest_count,39);assert.equal(inventory.verification.files,156);assert.equal(inventory.verification.bytes,623518100);
 const previous=JSON.parse(original('data/global-models/additional-placement.json'));assert.deepEqual(placement.records.filter(r=>r.id!==id),previous.records);assert.deepEqual(placement.source_contracts.filter(r=>r.file!==footprintPath),previous.source_contracts);
 const changes=execFileSync('git',['diff','--name-only',baselineCommit,'--',':(top)projects/shanghai/data/audit'],{cwd:project}).toString().trim().split('\n').filter(Boolean);assert(changes.every(p=>p.startsWith('projects/shanghai/data/audit/yangpu-city-hall-v1/')));
});
const unchangedFiles=['data/landmarks.json','data/global-models/urban-placement.json','data/global-models/chongming-placement.json','vendor/maplibre-gl.js','data/audit/global-model-integration-v1/inventory.json',
 ...['new-wing-on-company','xinxin-company','daxin-company','cathay-mansions','grosvenor-house','municipal-council'].map(name=>`data/audit/${name}-v1/inventory-increment.json`),
 'src/candidate-city-integrations.js','src/candidate-city-clipping.js','src/candidate-vector-clipping.js','src/map-scene.js','src/building-beacons.js','src/candidate-overview-camera.js','tests/candidate-city-clipping.test.mjs'];
check('all existing production code and frozen placement evidence retain their baseline bytes; builder only gains Yangpu',()=>{
 for(const file of unchangedFiles)assert.equal(sha(read(file)),sha(original(file)),file);
 const builder='tools/build_candidate_city_integrations.py';
 assert.equal(read(builder).toString(),original(builder).toString().replace('"xuhui": ("310104", "徐汇区")}','"xuhui": ("310104", "徐汇区"),\n             "yangpu": ("310110", "杨浦区")}'));
});
check('the new placement exactly binds the reviewed main-building-only source correction',()=>{
 const binding=placement.source_contracts.find(r=>r.file===footprintPath),raw=read(footprintPath);assert(binding);assert.equal(binding.bytes,raw.length);assert.equal(binding.sha256,sha(raw));assert.equal(binding.record,'proposed_placement_contract');assert.deepEqual(placement.records.find(r=>r.id===id),contract);
 assert.deepEqual(added.source_feature_ids,{building:['3904106e-f668-46d4-a302-a13ccd00866a'],building_part:[]});assert.equal(added.owner.macro_id,'14-13722-6690');assert.equal(added.owner.feature_local_id,525);
 assert.deepEqual(added.replacement_geometry,contract.replacement_geometry);assert.deepEqual(added.collision_geometry,contract.collision_geometry);assert.equal(added.partial_model,false);assert.equal(contract.ground_collision_excludes_overhead_projection,true);
});
check('ten new clipping rows retain the old137 rows and fit the existing192-row allocation',()=>{
 const clipper=new CandidateCityClipper({THREE,geographicPosition});clipper.update(clips(old.models));beforeTriangles=clipper.getState().triangles;assert.equal(beforeTriangles,137);const oldPayload=Buffer.from(clipper.data.slice(0,beforeTriangles*16).buffer);
 clipper.update(clips([added]));addedTriangles=clipper.getState().triangles;assert.equal(addedTriangles,10);assert.deepEqual([...new Set(Array.from({length:addedTriangles},(_,i)=>clipper.data[i*16+12]))],[525]);
 clipper.update(clips(catalog.models));afterTriangles=clipper.getState().triangles;assert.equal(afterTriangles,147);assert.equal(afterTriangles,beforeTriangles+addedTriangles);assert.equal(clipper.getState().triangleLimit,192);assert(afterTriangles<=192);
 historicalTextureRowsEqual=oldPayload.equals(Buffer.from(clipper.data.buffer,0,beforeTriangles*64));assert(historicalTextureRowsEqual);clipper.dispose();
});
check('the actual seven-owner near group receives the525 clip without whole-tile hiding',()=>{
 const ids=footprint.global_source_owner.near_group_feature_ids;assert.deepEqual(ids,[239,525,534,1005,1047,1850,2006]);assert.equal(footprint.global_source_owner.near_feature_id_attribute_present,false);
 const clipper=new CandidateCityClipper({THREE,geographicPosition});clipper.update(clips([added]));
 // The second array is deliberately a foreign-owner fixture, not a claimed native tile.
 const groups=[ids,ids.filter(x=>x!==525)].map((owners,index)=>{const group=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());group.add(mesh);clipper.bindObject(group,{id:index?'synthetic-foreign-owner-control':'reviewed-seven-owner-group-fixture',parent:{id:added.owner.macro_id},ids:owners});
  for(const [material,kind] of [[mesh.material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']]){const lib=THREE.ShaderLib[kind],shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:{}};material.onBeforeCompile(shader,{});assert.equal(shader.uniforms.candidateClipCount.value,index?0:10);assert.equal(shader.uniforms.candidateHasFeatureIds.value,0);}return{mesh};});
 const state=clipper.getState().ownerScopedSources;assert.deepEqual(state[0].clip_feature_local_ids,[525]);assert.equal(state[1].triangles,0);clipper.dispose();for(const {mesh} of groups){mesh.geometry.dispose();mesh.material.dispose();}
});
check('vector correction covers the entire main source and leaves independent source IDs unchanged',()=>{
 const own=added.source_feature_ids.building[0],geometry=contract.source_limit_geometry,foreign='city-hall-foreign-owner-fixture';
 const neighbors=[...new Map([...footprint.exclusions.context_sources_within_80m,...footprint.exclusions.required_context_sources,...footprint.baseline_native_group_geometry_check.same_group_owner_records].filter(r=>r.source_id!==own).map(r=>[r.source_id,r])).values()];neighborCount=neighbors.length;
 const features=[own,foreign].map(id=>({type:'Feature',id,properties:{id,height:1},geometry}));features.push(...neighbors.map(r=>({type:'Feature',id:r.source_id,properties:{id:r.source_id,height:r.map_height_m??1},geometry:r.source_geometry_wgs84})));const frozen=JSON.stringify(features);
 const result=planCandidateVectorClipping(features,{candidateClips:clips([added])},{source:'overture-buildings',sourceLayer:'building'});assert.equal(JSON.stringify(features),frozen);assert.equal(result.stats.clippingErrors,0);assert.equal(result.desired.size,1);assert.equal([...result.desired.values()][0].id,own);assert.equal(result.residualData.features.length,0);
 sourceAreaRuntime=metricArea(geometry);assert(Math.abs(sourceAreaRuntime-footprint.geometry.source_area_m2)<0.001);sourceRemainderArea=0;assert.equal(contract.source_retained_area_runtime_m2,0);assert.equal(contract.source_retained_fraction,0);
 const covered=planCandidateVectorClipping(features,{candidateClips:clips([added]),alreadyCovered:id=>id===own},{source:'overture-buildings',sourceLayer:'building'});assert.equal(covered.desired.size,0);assert.equal(covered.residualData.features.length,0);
});
check('production ground collision preserves the full underpass while retaining piers, stairs and main interiors',()=>{
 const collision=added.collision_geometry,review=footprint.actual_model_envelope_review.collision_review;assert(validCandidateGeometry(collision));assert.equal(parts(collision).length,2);assert(parts(collision).every(rings=>rings.length===1));assert.deepEqual(parts(collision).map(r=>r[0].length),[58,25]);assert.deepEqual(review.standing_slab_z_m,[0,2]);
 const [x0,y0,x1,y1]=footprint.bridge_and_steps_review.ground_road_test_box_local_xy_m;
 const road={type:'Polygon',coordinates:[[[x0,y0],[x1,y0],[x1,y1],[x0,y1],[x0,y0]].map(fromLocal)]};
 const intersection=globalThis.polygonClipping.intersection(parts(collision),parts(road)),roadArea=metricArea({type:'MultiPolygon',coordinates:intersection});assert(roadArea<1e-8);
 let negatives=0;for(const path of review.negative_complete_X_paths)for(let x=x0;x<=x1;x+=.5){assert.equal(candidateGeometryContains(collision,fromLocal([x,path.y_m])),false);negatives++;}
 for(const probe of review.positive_ground_obstacle_probes)assert.equal(candidateGeometryContains(collision,fromLocal(probe.local_xy_m)),true,probe.name);
 for(const probe of footprint.bridge_and_steps_review.probes.filter(p=>p.name.includes('underpass')||p.name==='south-road-bridge-deck')){assert.equal(candidateGeometryContains(collision,probe.wgs84),false,probe.name);const converted=fromLocal(probe.local_xyz_m);assert(converted.every((v,i)=>Math.abs(v-probe.wgs84[i])<1e-10));}
 const missing=globalThis.polygonClipping.difference(parts(contract.source_limit_geometry),parts(collision)),missingArea=metricArea({type:'MultiPolygon',coordinates:missing});assert(missingArea<1e-6);
 groundChecks={standing_slab_m:[0,2],collision_parts:2,closed_ring_lengths:[58,25],road_intersection_area_m2:roadArea,complete_X_path_sample_points:negatives,positive_ground_probes:review.positive_ground_obstacle_probes.length,main_source_uncovered_area_m2:missingArea,bridge_deck_not_treated_as_ground:true};
});
const bindings=[...new Set([...unchangedFiles,'tools/build_candidate_city_integrations.py','index.html','data/candidate-city-integrations.json','data/global-models/additional-placement.json','data/global-models/candidate-inventory.json',footprintPath,'data/audit/yangpu-city-hall-v1/global-integration-checks.mjs','tests/building-beacons.test.mjs','tests/candidate-overview-camera.test.mjs'])].map(file=>{const b=read(file);return{file,bytes:b.length,sha256:sha(b)};});
const report={schema:'yangpu-city-hall-global-integration-delta-v1',passed:checks.length,failed:0,checks,baseline_commit:baselineCommit,entry_id:id,total_destinations:77,candidate_models:37,yangpu_count:2,huangpu_count:28,route:`index.html#landmark=${id}&mode=overview`,walking_enabled:false,clipping_triangles:{before:beforeTriangles,addition:addedTriangles,after:afterTriangles,limit:192},historical_texture_rows_equal:historicalTextureRowsEqual,historical_texture_payload_bytes_compared:137*64,source_area_runtime_m2:sourceAreaRuntime,source_remainder_area_runtime_m2:sourceRemainderArea,independent_vector_contexts:neighborCount,ground_collision:groundChecks,scope:'Static production merge/navigation, exact placement and source bindings, actual shipped Mercator conversion, immutable historical texture rows, source-specific vector correction and production polygon containment. Near tests use the real seven-owner array and an explicitly synthetic foreign-owner control; actual native overlap measurements belong to the bound mapping audit. Ground road geometry and positive probes are verified without enabling bridge-deck, stair or indoor walking. Actual loading, rendering, source preservation and touch require separate browser evidence.',bindings};
writeFileSync(new URL('global-integration-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:checks.length,total:77,candidates:37,triangles:afterTriangles,groundChecks}));
