// Final-only incremental gymnasium integration. Run from repository root after asset/placement freeze.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import vm from 'node:vm';
const project=resolve(process.argv[2]||'projects/shanghai'),root=resolve(project,'../..');
const id='yangpu-jiangwan-gymnasium',baselineCommit='a47e69e9cbde689266855d573aa8d1f25b02944d';
const read=path=>readFileSync(resolve(project,path)),json=path=>JSON.parse(read(path));
const original=path=>execFileSync('git',['show',`${baselineCommit}:projects/shanghai/${path}`],{cwd:root,maxBuffer:12*1024*1024});
const sha=b=>createHash('sha256').update(b).digest('hex');
const THREE=await import(pathToFileURL(resolve(project,'vendor/three.module.js')));
const {mergeCandidateCityModels,candidateGeometryContains,validCandidateGeometry}=await import(pathToFileURL(resolve(project,'src/candidate-city-integrations.js')));
const {CandidateCityClipper}=await import(pathToFileURL(resolve(project,'src/candidate-city-clipping.js')));
const oldClipperModule=await import('data:text/javascript;base64,'+original('src/candidate-city-clipping.js').toString('base64'));
const {planCandidateVectorClipping}=await import(pathToFileURL(resolve(project,'src/candidate-vector-clipping.js')));
const {resolveNavigationRoute}=await import(pathToFileURL(resolve(project,'src/landmark-navigation.js')));
const {walkingPose}=await import(pathToFileURL(resolve(project,'src/precise-registration-ui.js')));
const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};context.exports=context.module.exports;context.self=context;context.globalThis=context;
vm.runInNewContext(read('vendor/maplibre-gl.js').toString(),context);const maplibre=context.module.exports;
const origin=maplibre.MercatorCoordinate.fromLngLat([121.4737,31.2304]),unit=origin.meterInMercatorCoordinateUnits();
const geographicPosition=(lng,lat)=>{const p=maplibre.MercatorCoordinate.fromLngLat([lng,lat]);return new THREE.Vector3((p.x-origin.x)/unit,0,(p.y-origin.y)/unit);};
const base=json('data/landmarks.json'),catalog=json('data/candidate-city-integrations.json'),old=JSON.parse(original('data/candidate-city-integrations.json'));
const footprintPath='data/audit/jiangwan-gymnasium-v1/footprint-review.json',footprint=json(footprintPath),contract=footprint.proposed_placement_contract;
const evidence=footprint.runtime_validation;assert(evidence?.final_model_geometry_verified===true,'Require final actual-model runtime evidence');
const placement=json('data/global-models/additional-placement.json'),inventory=json('data/global-models/candidate-inventory.json'),manifest=json(`assets/models/candidates/${id}/manifest.json`);
const checks=[];function check(name,fn){fn();checks.push(name);}
const parts=g=>g?.type==='Polygon'?[g.coordinates]:g?.type==='MultiPolygon'?g.coordinates:[];
const area=g=>parts(g).reduce((total,rings)=>total+rings.reduce((sum,r,k)=>{let a=0;for(let i=1;i<r.length;i++)a+=(r[i-1][0]-r[0][0])*(r[i][1]-r[0][1])-(r[i][0]-r[0][0])*(r[i-1][1]-r[0][1]);return sum+(k?-1:1)*Math.abs(a)/2;},0),0);
const anchor=maplibre.MercatorCoordinate.fromLngLat([contract.lng,contract.lat]),metre=anchor.meterInMercatorCoordinateUnits();
const metricArea=g=>area({type:'MultiPolygon',coordinates:parts(g).map(rings=>rings.map(ring=>ring.map(([lng,lat])=>{const p=maplibre.MercatorCoordinate.fromLngLat([lng,lat]);return[(p.x-anchor.x)/metre,(p.y-anchor.y)/metre];})))});
function fromLocal([x,y]){const a=contract.heading*Math.PI/180,c=Math.cos(a),s=Math.sin(a);const p=new maplibre.MercatorCoordinate(anchor.x+(c*x+s*y)*metre,anchor.y+(s*x-c*y)*metre).toLngLat();return[p.lng,p.lat];}
function clips(models){const result=new Map();for(const row of models){if(row.replacement_geometry)result.set(row.id,{id:row.id,geometry:row.replacement_geometry,owner:row.owner,owners:row.owners,source_feature_ids:row.source_feature_ids});if(row.site_replacement)result.set(row.site_replacement.id,row.site_replacement);}return[...result.values()];}
const sourceId='adde8d71-bc6d-497a-a682-3bb158c1f160',localId=1558,macroId='14-13722-6690',expectedAddition=10,limit=224;
const actualNearIds=[1709,112,1672,2097,349,337,480,1558,143,2066,2020,1639];
let merged,added,newClips,beforeTriangles,addedTriangles,afterTriangles,historicalTextureRowsEqual,nearChecks=[],vectorChecks,groundChecks;

check('gym adds one overview destination to78 entries while all38 earlier candidate records remain unchanged',()=>{
 assert.equal(base.length,40);assert.equal(old.models.length,38);assert.equal(catalog.models.length,39);assert.deepEqual(catalog.models.filter(r=>r.id!==id),old.models);
 merged=mergeCandidateCityModels(base,catalog);assert.equal(merged.length,79);assert.equal(new Set(merged.map(r=>r.id)).size,79);
 added=merged.find(r=>r.id===id);assert(added?.city_integration);assert.equal(walkingPose(added),null);
 for(const r of merged){const route=resolveNavigationRoute(`#landmark=${r.id}&mode=overview`,{landmarks:merged});assert.equal(route.place.id,r.id);assert.equal(route.mode,'overview');}
 assert.equal(read('index.html').toString().match(/id="landmark-count">(\d+)<\/span>/)?.[1],'79','Static index count must match registry');
 assert.equal(merged.filter(r=>r.districtId==='310110').length,4);assert.equal(merged.filter(r=>r.districtId==='310101').length,28);
});

const unchangedFiles=['data/landmarks.json','data/global-models/urban-placement.json','data/global-models/chongming-placement.json','data/model-todo/named-map-leads.json','vendor/maplibre-gl.js','data/audit/global-model-integration-v1/inventory.json',
 ...['new-wing-on-company','xinxin-company','daxin-company','cathay-mansions','grosvenor-house','municipal-council','yangpu-city-hall','jiangwan-stadium'].map(name=>`data/audit/${name}-v1/inventory-increment.json`),
 'src/building-beacons.js','src/candidate-city-integrations.js','src/candidate-vector-clipping.js','src/map-scene.js','src/candidate-overview-camera.js','tools/build_candidate_city_integrations.py'];
check('new four assets inherit40 frozen manifests without replaying old model assets or changing old placements',()=>{
 const previousInventory=JSON.parse(original('data/global-models/candidate-inventory.json'));assert.deepEqual(inventory.records.filter(r=>r.id!==id),previousInventory.records);
 assert.deepEqual(inventory.current_delivery_manifests,[`projects/shanghai/assets/models/candidates/${id}/manifest.json`]);
 const frozen=inventory.prior_incremental_inventory;assert.equal(frozen.file,'data/audit/jiangwan-stadium-v1/inventory-increment.json');const bytes=read(frozen.file);assert.equal(bytes.length,frozen.bytes);assert.equal(sha(bytes),frozen.sha256);
 assert.equal(Object.keys(manifest.assets).length,4);const addedBytes=Object.values(manifest.assets).reduce((sum,a)=>sum+a.bytes,0);
 assert.equal(inventory.verification.current_run_added_files,4);assert.equal(inventory.verification.inherited_incremental_files,32);assert.equal(inventory.candidate_manifest_count,41);assert.equal(inventory.verification.files,164);assert.equal(inventory.verification.bytes,669923028+addedBytes);
 const previousPlacement=JSON.parse(original('data/global-models/additional-placement.json'));assert.deepEqual(placement.records.filter(r=>r.id!==id),previousPlacement.records);assert.deepEqual(placement.source_contracts.filter(r=>r.file!==footprintPath),previousPlacement.source_contracts);
 for(const file of unchangedFiles)assert.equal(sha(read(file)),sha(original(file)),file);
 for(const [directory,allowed] of [['data/audit','data/audit/jiangwan-gymnasium-v1/'],['assets/models/candidates',`assets/models/candidates/${id}/`],['source/precise',`source/precise/${id}/`]]){
  const changes=execFileSync('git',['diff','--name-status',baselineCommit,'--',`:(top)projects/shanghai/${directory}`],{cwd:root}).toString().trim().split('\n').filter(Boolean);
  for(const line of changes){const [status,file]=line.split('\t');assert(['A','M'].includes(status));assert(file.startsWith('projects/shanghai/'+allowed),line);}
 }
});

check('gym asset binds its independent1558 source and does not claim stadium or swimming-hall sources',()=>{
 const binding=placement.source_contracts.find(r=>r.file===footprintPath),bytes=read(footprintPath);assert(binding);assert.equal(binding.bytes,bytes.length);assert.equal(binding.sha256,sha(bytes));assert.equal(binding.record,'proposed_placement_contract');assert.deepEqual(placement.records.find(r=>r.id===id),contract);
 for(const key of ['replacement_geometry','source_feature_ids','collision_geometry','owner','partial_model'])assert.deepEqual(added[key],contract[key],key);
 assert.equal(added.owner.feature_local_id,localId);assert.equal(added.owner.macro_id,macroId);assert(!added.site_replacement);assert(!added.owners?.length);
 newClips=clips([added]);assert.equal(newClips.length,1);assert.deepEqual(newClips[0].source_feature_ids,{building:[sourceId],building_part:[]});assert(validCandidateGeometry(newClips[0].geometry));
 for(const [role,key] of [['raw','raw'],['web','full'],['lod','lod']])assert.equal(contract.model_geometry_sha256[role],manifest.assets[key].sha256);
 const named=json('data/model-todo/named-map-leads.json');assert.equal(named.records.length,1036);assert(!named.records.some(r=>r.id===sourceId),'No invented new association in frozen named snapshot');
});

check('ten added display triangles use202 of224 rows while the old192 rows remain byte-identical',()=>{
 const {CandidateCityClipper:OldClipper}=oldClipperModule;
 const previous=new OldClipper({THREE,geographicPosition});previous.update(clips(old.models));assert.equal(previous.triangleCount,192);const oldPayload=Buffer.from(previous.data.buffer,0,192*64);
 const clipper=new CandidateCityClipper({THREE,geographicPosition});clipper.update(clips(old.models));beforeTriangles=clipper.triangleCount;assert.equal(beforeTriangles,192);assert(oldPayload.equals(Buffer.from(clipper.data.buffer,0,192*64)));
 clipper.update(newClips);addedTriangles=clipper.triangleCount;assert.equal(addedTriangles,expectedAddition);assert.equal(contract.expected_replacement_triangle_count,expectedAddition);assert(clipper.triangleOwners.every(r=>r.localId===localId));
 clipper.update(clips(catalog.models));afterTriangles=clipper.triangleCount;assert.equal(afterTriangles,202);assert.equal(afterTriangles,beforeTriangles+addedTriangles);assert.equal(clipper.getState().triangleLimit,limit);assert.equal(contract.expected_global_clip_capacity,limit);assert.equal(contract.expected_global_clip_triangle_count,202);
 assert.equal(clipper.texture.image.height,limit);assert.equal(clipper.data.byteLength,14336);
 historicalTextureRowsEqual=oldPayload.equals(Buffer.from(clipper.data.buffer,0,192*64));assert(historicalTextureRowsEqual);assert(clipper.data.subarray(202*16).every(x=>x===0));previous.dispose();clipper.dispose();
});

check('the12-owner near group receives only1558 clipping in colour, depth and distance passes',()=>{
 assert.equal(evidence.near_groups.length,1);const spec=evidence.near_groups[0];assert.deepEqual([...spec.feature_local_ids].sort((a,b)=>a-b),[...actualNearIds].sort((a,b)=>a-b));assert.deepEqual(spec.clip_feature_local_ids,[localId]);assert.equal(spec.triangles,expectedAddition);
 const clipper=new CandidateCityClipper({THREE,geographicPosition});clipper.update(newClips);const meshes=[];
 for(const foreign of [false,true]){
  const ids=foreign?spec.feature_local_ids.filter(x=>x!==localId):spec.feature_local_ids,group=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());group.add(mesh);meshes.push(mesh);
  clipper.bindObject(group,{id:foreign?'foreign-owners-only-control':spec.group_id,parent:{id:spec.macro_id},ids});
  for(const [material,kind] of [[mesh.material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']]){const lib=THREE.ShaderLib[kind],shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:{}};material.onBeforeCompile(shader,{});assert.equal(shader.uniforms.candidateClipCount.value,foreign?0:expectedAddition);assert.equal(shader.uniforms.candidateHasFeatureIds.value,0);assert.equal(shader.uniforms.candidateClipTexture.value.image.height,limit);}
 }
 nearChecks=clipper.getState().ownerScopedSources;const real=nearChecks.find(r=>r.id===spec.group_id);assert.deepEqual(real.clip_feature_local_ids,[localId]);assert.equal(real.triangles,10);
 clipper.dispose();for(const mesh of meshes){mesh.geometry.dispose();mesh.material.dispose();}
});

check('vector replacement removes only the complete gym source and leaves all supplied real context identities untouched',()=>{
 assert.equal(evidence.source_features.length,1);assert(evidence.context_sources.length>0);
 const source=evidence.source_features[0];assert.equal(source.source_id,sourceId);const main={type:'Feature',id:sourceId,properties:{id:sourceId,height:source.map_height_m??1},geometry:source.geometry_wgs84};
 const features=[main,{...structuredClone(main),id:'synthetic-same-footprint-foreign',properties:{id:'synthetic-same-footprint-foreign',height:1}},...evidence.context_sources.map(r=>({type:'Feature',id:r.source_id,properties:{id:r.source_id,height:r.map_height_m??1},geometry:r.geometry_wgs84}))];
 const frozen=JSON.stringify(features),result=planCandidateVectorClipping(features,{candidateClips:newClips},{source:'overture-buildings',sourceLayer:'building'});assert.equal(JSON.stringify(features),frozen);assert.equal(result.stats.clippingErrors,0);assert.equal(result.desired.size,1);assert.deepEqual([...result.desired.values()].map(r=>r.id),[sourceId]);assert.equal(result.residualData.features.length,0);
 const covered=planCandidateVectorClipping(features,{candidateClips:newClips,alreadyCovered:id=>id===sourceId},{source:'overture-buildings',sourceLayer:'building'});assert.equal(covered.desired.size,0);assert.equal(covered.residualData.features.length,0);
 vectorChecks={source_id:sourceId,source_area_runtime_m2:metricArea(main.geometry),residual_area_m2:0,real_context_features:evidence.context_sources.length,synthetic_same_footprint_foreign_controls:1};
});

check('production ground collision covers actual low structure and retains reviewed open entrance and road areas',()=>{
 assert(validCandidateGeometry(added.collision_geometry,{collision:true}));assert(evidence.ground_probes.some(p=>p.expected===null));assert(evidence.ground_probes.some(p=>p.expected==='building'));
 for(const p of evidence.ground_probes){assert.equal(candidateGeometryContains(added.collision_geometry,p.wgs84),p.expected==='building',p.name);if(p.local_xy_m){const point=fromLocal(p.local_xy_m);assert(point.every((v,i)=>Math.abs(v-p.wgs84[i])<1e-10),p.name);}}
 assert(evidence.open_ground_areas.length>=1,'Require reviewed real open ground');
 const openAreas=evidence.open_ground_areas.map(p=>{const intersection=globalThis.polygonClipping.intersection(parts(added.collision_geometry),parts(p.geometry_wgs84)),intersectionArea=metricArea({type:'MultiPolygon',coordinates:intersection});assert(intersectionArea<1e-6,p.name);return{name:p.name,ground_collision_intersection_m2:intersectionArea};});
 groundChecks={collision_parts:parts(added.collision_geometry).length,closed_ring_lengths:parts(added.collision_geometry).map(rings=>rings.map(r=>r.length)),positive_probes:evidence.ground_probes.filter(p=>p.expected==='building').length,negative_probes:evidence.ground_probes.filter(p=>p.expected===null).length,open_areas:openAreas,note:'Production2D containment complements actual-triangle low-occupancy checks. No gym interior or elevated walking is enabled.'};
});

const bindings=[...new Set([...unchangedFiles,'src/candidate-city-clipping.js','tests/candidate-city-clipping.test.mjs','index.html','data/candidate-city-integrations.json','data/global-models/additional-placement.json','data/global-models/candidate-inventory.json',footprintPath,`assets/models/candidates/${id}/manifest.json`,'data/audit/jiangwan-gymnasium-v1/global-integration-checks.mjs'])].map(file=>{const b=read(file);return{file,bytes:b.length,sha256:sha(b)};});
const report={schema:'jiangwan-gymnasium-global-integration-delta-v1',passed:checks.length,failed:0,checks,baseline_commit:baselineCommit,entry_id:id,total_destinations:79,candidate_models:39,yangpu_count:4,huangpu_count:28,route:`index.html#landmark=${id}&mode=overview`,walking_enabled:false,clipping_triangles:{before:beforeTriangles,addition:addedTriangles,after:afterTriangles,limit},historical_texture_rows_equal:historicalTextureRowsEqual,historical_texture_payload_bytes_compared:192*64,near_group_fixture_checks:nearChecks,vector_checks:vectorChecks,ground_collision:groundChecks,scope:'Final production merge/navigation, unchanged historical catalogue and actual old/new clipper payload, reviewed exact source identity and near owners, frozen model contract, source vector correction and production collision. Near meshes in these shader tests are explicit fixtures; actual decoded source/asset geometry belongs to mapping/independent evidence and browser rendering. No historical model asset matrix replay.',bindings};
writeFileSync(new URL('global-integration-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:checks.length,total:79,candidates:39,triangles:afterTriangles,limit,groundChecks}));
