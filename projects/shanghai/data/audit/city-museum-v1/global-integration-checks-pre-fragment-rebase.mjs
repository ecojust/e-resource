// Final-only incremental city-museum integration. Run from repository root after asset/placement freeze.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import vm from 'node:vm';
const project=resolve(process.argv[2]||'projects/shanghai'),root=resolve(project,'../..');
const id='yangpu-former-shanghai-city-museum',baselineCommit='93e3cb2d0ddeba1a7db7d435bf66c2f61492326e';
const read=path=>readFileSync(resolve(project,path)),json=path=>JSON.parse(read(path));
const original=path=>execFileSync('git',['show',`${baselineCommit}:projects/shanghai/${path}`],{cwd:root,maxBuffer:12*1024*1024});
const sha=b=>createHash('sha256').update(b).digest('hex');
const navigationReportPath='data/audit/readme-navigation-v1/report.json',navigationReadmePath='data/audit/readme-navigation-v1/README.md';
const navigationBytes=read(navigationReportPath);assert.equal(sha(navigationBytes),'65c7cbcac92d92c48fbfeb1fb648a10f637be0847cf4d14be12b81b40ae63569');
assert.equal(sha(read(navigationReadmePath)),'a2d934338d4f7048f00caba65f7c973a29206e7f84bafa18b4c496671064e006');
const navigation=JSON.parse(navigationBytes),authorizedReadmes=new Set();assert.equal(navigation.baseline_commit,baselineCommit);assert.equal(navigation.files.length,64);
for(const row of navigation.files){
 assert(row.path.startsWith('projects/shanghai/')&&row.path.endsWith('/README.md'));const file=row.path.slice('projects/shanghai/'.length);
 assert(file.startsWith('data/audit/')||file.startsWith('source/precise/')||file==='source/surfaces/README.md');assert(!authorizedReadmes.has(file));
 let before=original(file).toString();assert.equal(sha(before),row.before_sha256);
 for(const op of row.replacement_operations){assert.equal(before.split(op.before_text).length-1,1,`${file}: exact unique navigation operation`);before=before.replace(op.before_text,op.after_text);}
 assert.equal(sha(before),row.after_sha256);assert.equal(sha(read(file)),row.after_sha256);authorizedReadmes.add(file);
}
const authorizedNavigationArtifacts=new Set([navigationReportPath,navigationReadmePath]);
const runtimeChangePath='data/audit/city-museum-v1/runtime-height-source-change.json',runtimeChangeBytes=read(runtimeChangePath);
assert.equal(sha(runtimeChangeBytes),'058bb5878b7dc7afcd7bf35b9f4010dd441613dd55c3473ffa1b2e29ede228d9');
const runtimeChange=JSON.parse(runtimeChangeBytes);
const runtimeChangeFiles=['src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/map-scene.js','src/app.js','index.html','tools/build_candidate_city_integrations.py','tests/candidate-city-clipping.test.mjs','tests/candidate-geometry.test.mjs','tests/candidate-catalog-increment.test.py'];
assert.deepEqual(runtimeChange.files.map(r=>r.file),runtimeChangeFiles.map(f=>'projects/shanghai/'+f));
assert.equal(runtimeChange.baseline_commit,baselineCommit);
for(const row of runtimeChange.files){const bytes=read(row.file.slice('projects/shanghai/'.length));assert.equal(sha(bytes),row.after_sha256,row.file);assert.equal(bytes.length,row.after_bytes,row.file);}


const THREE=await import(pathToFileURL(resolve(project,'vendor/three.module.js')));
const {mergeCandidateCityModels,candidateGeometryContains,validCandidateGeometry}=await import(pathToFileURL(resolve(project,'src/candidate-city-integrations.js')));
const {CandidateCityClipper}=await import(pathToFileURL(resolve(project,'src/candidate-city-clipping.js')));
const oldClipperModule=await import('data:text/javascript;base64,'+original('src/candidate-city-clipping.js').toString('base64'));
const awaitBeforeHeightModule=await import('data:text/javascript;base64,'+Buffer.from(original('src/candidate-city-clipping.js').toString().replace('const MAX_TRIANGLES=224;','const MAX_TRIANGLES=288;')).toString('base64'));
const {planCandidateVectorClipping}=await import(pathToFileURL(resolve(project,'src/candidate-vector-clipping.js')));
const {resolveNavigationRoute}=await import(pathToFileURL(resolve(project,'src/landmark-navigation.js')));
const {walkingPose}=await import(pathToFileURL(resolve(project,'src/precise-registration-ui.js')));
const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};context.exports=context.module.exports;context.self=context;context.globalThis=context;
vm.runInNewContext(read('vendor/maplibre-gl.js').toString(),context);const maplibre=context.module.exports;
const origin=maplibre.MercatorCoordinate.fromLngLat([121.4737,31.2304]),unit=origin.meterInMercatorCoordinateUnits();
const geographicPosition=(lng,lat,height=0)=>{const p=maplibre.MercatorCoordinate.fromLngLat([lng,lat],height);return new THREE.Vector3((p.x-origin.x)/unit,p.z/unit,(p.y-origin.y)/unit);};
const base=json('data/landmarks.json'),catalog=json('data/candidate-city-integrations.json'),old=JSON.parse(original('data/candidate-city-integrations.json'));
const footprintPath='data/audit/city-museum-v1/footprint-review.json',footprint=json(footprintPath),contract=footprint.proposed_placement_contract;
const evidence=footprint.runtime_validation;assert(evidence?.final_model_geometry_verified===true,'Require final actual-model runtime evidence');
const placement=json('data/global-models/additional-placement.json'),inventory=json('data/global-models/candidate-inventory.json'),manifest=json(`assets/models/candidates/${id}/manifest.json`);
const checks=[];function check(name,fn){fn();checks.push(name);}
const parts=g=>g?.type==='Polygon'?[g.coordinates]:g?.type==='MultiPolygon'?g.coordinates:[];
const area=g=>parts(g).reduce((total,rings)=>total+rings.reduce((sum,r,k)=>{let a=0;for(let i=1;i<r.length;i++)a+=(r[i-1][0]-r[0][0])*(r[i][1]-r[0][1])-(r[i][0]-r[0][0])*(r[i-1][1]-r[0][1]);return sum+(k?-1:1)*Math.abs(a)/2;},0),0);
const anchor=maplibre.MercatorCoordinate.fromLngLat([contract.lng,contract.lat]),metre=anchor.meterInMercatorCoordinateUnits();
const metricArea=g=>area({type:'MultiPolygon',coordinates:parts(g).map(rings=>rings.map(ring=>ring.map(([lng,lat])=>{const p=maplibre.MercatorCoordinate.fromLngLat([lng,lat]);return[(p.x-anchor.x)/metre,(p.y-anchor.y)/metre];})))});
function fromLocal([x,y]){const a=contract.heading*Math.PI/180,c=Math.cos(a),s=Math.sin(a);const p=new maplibre.MercatorCoordinate(anchor.x+(c*x+s*y)*metre,anchor.y+(s*x-c*y)*metre).toLngLat();return[p.lng,p.lat];}
function clips(models){const result=new Map();for(const row of models){if(row.replacement_geometry)result.set(row.id,{id:row.id,geometry:row.replacement_geometry,owner:row.owner,owners:row.owners,source_feature_ids:row.source_feature_ids});if(row.site_replacement)result.set(row.site_replacement.id,row.site_replacement);}return[...result.values()];}
function displayClips(models){return [...clips(models),...models.flatMap(r=>r.display_height_clips||[])];}
const sourceId='cdc86c9b-dee5-4342-a7ee-e962fa0d030e',siteSourceId='d54de774-0952-43c1-98a0-c9cbeaf207b1',localId=1860,siteLocalId=1931,macroId='14-13722-6690',expectedBaseAddition=40,expectedHeightAddition=4,expectedAddition=44,limit=288;
const actualNearIds=[1262,1860,1931,510,958,1061,169,1697],targetIds=[localId,siteLocalId];
let merged,added,newClips,newDisplayClips,beforeTriangles,addedTriangles,afterTriangles,historicalTextureRowsEqual,preHeightTextureRowsEqual,nearChecks=[],vectorChecks,groundChecks;

check('city museum adds one overview destination to80 entries while all40 earlier candidate records remain unchanged',()=>{
 assert.equal(base.length,40);assert.equal(old.models.length,40);assert.equal(catalog.models.length,41);assert.deepEqual(catalog.models.filter(r=>r.id!==id),old.models);
 merged=mergeCandidateCityModels(base,catalog);assert.equal(merged.length,81);assert.equal(new Set(merged.map(r=>r.id)).size,81);
 added=merged.find(r=>r.id===id);assert(added?.city_integration);assert.equal(walkingPose(added),null);
 for(const r of merged){const route=resolveNavigationRoute(`#landmark=${r.id}&mode=overview`,{landmarks:merged});assert.equal(route.place.id,r.id);assert.equal(route.mode,'overview');}
 assert.equal(read('index.html').toString().match(/id="landmark-count">(\d+)<\/span>/)?.[1],'81','Static index count must match registry');
 assert.equal(merged.filter(r=>r.districtId==='310110').length,6);assert.equal(merged.filter(r=>r.districtId==='310101').length,28);
});

const unchangedFiles=['data/landmarks.json','data/global-models/urban-placement.json','data/global-models/chongming-placement.json','data/model-todo/named-map-leads.json','vendor/maplibre-gl.js','data/audit/global-model-integration-v1/inventory.json',
 ...['new-wing-on-company','xinxin-company','daxin-company','cathay-mansions','grosvenor-house','municipal-council','yangpu-city-hall','jiangwan-stadium','jiangwan-gymnasium','jiangwan-swimming-hall'].map(name=>`data/audit/${name}-v1/inventory-increment.json`),
 'src/building-beacons.js','src/candidate-vector-clipping.js','src/candidate-overview-camera.js'];
check('new four assets inherit42 frozen manifests without replaying old model assets or changing old placements',()=>{
 const previousInventory=JSON.parse(original('data/global-models/candidate-inventory.json'));assert.deepEqual(inventory.records.filter(r=>r.id!==id),previousInventory.records);
 assert.deepEqual(inventory.current_delivery_manifests,[`projects/shanghai/assets/models/candidates/${id}/manifest.json`]);
 const frozen=inventory.prior_incremental_inventory;assert.equal(frozen.file,'data/audit/jiangwan-swimming-hall-v1/inventory-increment.json');const bytes=read(frozen.file);assert.equal(bytes.length,frozen.bytes);assert.equal(sha(bytes),frozen.sha256);
 assert.equal(Object.keys(manifest.assets).length,4);const addedBytes=Object.values(manifest.assets).reduce((sum,a)=>sum+a.bytes,0);
 assert.equal(inventory.verification.current_run_added_files,4);assert.equal(inventory.verification.inherited_incremental_files,40);assert.equal(inventory.candidate_manifest_count,43);assert.equal(inventory.verification.files,172);assert.equal(inventory.verification.bytes,684749128+addedBytes);
 const previousPlacement=JSON.parse(original('data/global-models/additional-placement.json'));assert.deepEqual(placement.records.filter(r=>r.id!==id),previousPlacement.records);assert.deepEqual(placement.source_contracts.filter(r=>r.file!==footprintPath),previousPlacement.source_contracts);
 for(const file of unchangedFiles)assert.equal(sha(read(file)),sha(original(file)),file);
 assert.equal(runtimeChange.files.length,9,'Exactly the reviewed runtime source changes are authorized');
 for(const [directory,allowed] of [['data/audit','data/audit/city-museum-v1/'],['assets/models/candidates',`assets/models/candidates/${id}/`],['source/precise',`source/precise/${id}/`]]){
  const changes=execFileSync('git',['diff','--name-status',baselineCommit,'--',`:(top)projects/shanghai/${directory}`],{cwd:root}).toString().trim().split('\n').filter(Boolean);
  for(const line of changes){const [status,file]=line.split('\t');assert(['A','M'].includes(status));const local=file.slice('projects/shanghai/'.length);assert(file.startsWith('projects/shanghai/'+allowed)||(status==='M'&&authorizedReadmes.has(local))||(status==='A'&&authorizedNavigationArtifacts.has(local)),line);}
 }
});

check('museum binds main1860 and overlapping tower1931 as separate masks while preserving independent hospital links',()=>{
 const binding=placement.source_contracts.find(r=>r.file===footprintPath),bytes=read(footprintPath);assert(binding);assert.equal(binding.bytes,bytes.length);assert.equal(binding.sha256,sha(bytes));assert.equal(binding.record,'proposed_placement_contract');assert.deepEqual(placement.records.find(r=>r.id===id),contract);
 for(const key of ['replacement_geometry','source_feature_ids','collision_geometry','site_replacement','owner','partial_model','display_height_clips'])assert.deepEqual(added[key],contract[key],key);
 assert.equal(added.owner.feature_local_id,localId);assert.equal(added.site_replacement.owner.feature_local_id,siteLocalId);
 assert.equal(added.owner.macro_id,macroId);assert.equal(added.site_replacement.owner.macro_id,macroId);
 assert(!added.owners?.length&&!added.site_replacement.owners?.length,'Each different mask must have its own single owner');
 newClips=clips([added]);assert.equal(newClips.length,2);assert.deepEqual(newClips[0].source_feature_ids,{building:[sourceId],building_part:[]});assert.deepEqual(newClips[1].source_feature_ids,{building:[siteSourceId],building_part:[]});assert(newClips.every(c=>validCandidateGeometry(c.geometry)));
 newDisplayClips=displayClips([added]);assert.deepEqual(newDisplayClips.slice(0,2),newClips);assert.equal(newDisplayClips.length,4);assert(newDisplayClips.slice(2).every(c=>c.owner.feature_local_id===localId&&c.owner.macro_id===macroId&&!('source_feature_ids' in c)));
 for(const [role,key] of [['raw','raw'],['web','full'],['lod','lod']])assert.equal(contract.model_geometry_sha256[role],manifest.assets[key].sha256);
 const named=json('data/model-todo/named-map-leads.json');assert.equal(named.records.length,1036);assert(!named.records.some(r=>[sourceId,siteSourceId].includes(r.id)),'Neither reviewed UUID occurs in the frozen named snapshot');
});

check('new museum display rows fit the reviewed capacity while the old218 rows remain byte-identical',()=>{
 const {CandidateCityClipper:OldClipper}=oldClipperModule;
 const previous=new OldClipper({THREE,geographicPosition});previous.update(clips(old.models));assert.equal(previous.triangleCount,218);const oldPayload=Buffer.from(previous.data.buffer,0,218*64);
 const clipper=new CandidateCityClipper({THREE,geographicPosition});clipper.update(clips(old.models));beforeTriangles=clipper.triangleCount;assert.equal(beforeTriangles,218);assert(oldPayload.equals(Buffer.from(clipper.data.buffer,0,218*64)));
 clipper.update(newClips);assert.equal(clipper.triangleCount,expectedBaseAddition);assert.equal(contract.expected_replacement_triangle_count,expectedBaseAddition);
 assert.equal(clipper.triangleOwners.filter(r=>r.localId===localId).length,38);assert.equal(clipper.triangleOwners.filter(r=>r.localId===siteLocalId).length,2);
 clipper.update(newDisplayClips);addedTriangles=clipper.triangleCount;assert.equal(addedTriangles,expectedAddition);assert.equal(contract.expected_display_height_triangle_count,expectedHeightAddition);assert.equal(contract.expected_model_gpu_clip_triangle_count,expectedAddition);assert.deepEqual([...new Set(clipper.triangleOwners.map(r=>r.localId))].sort((a,b)=>a-b),targetIds);
 const {CandidateCityClipper:BeforeHeightClipper}=awaitBeforeHeightModule;
 const beforeHeight=new BeforeHeightClipper({THREE,geographicPosition});beforeHeight.update(clips(catalog.models));assert.equal(beforeHeight.triangleCount,258);const beforeHeightPayload=Buffer.from(beforeHeight.data.buffer,0,258*64);
 clipper.update(displayClips(catalog.models));afterTriangles=clipper.triangleCount;assert.equal(afterTriangles,218+expectedAddition);assert.equal(afterTriangles,beforeTriangles+addedTriangles);assert.equal(clipper.getState().triangleLimit,limit);assert.equal(contract.expected_global_clip_capacity,limit);assert.equal(contract.expected_global_clip_triangle_count,218+expectedAddition);
 assert.equal(clipper.texture.image.height,limit);assert.equal(clipper.data.byteLength,limit*64);
 historicalTextureRowsEqual=oldPayload.equals(Buffer.from(clipper.data.buffer,0,218*64));assert(historicalTextureRowsEqual);preHeightTextureRowsEqual=beforeHeightPayload.equals(Buffer.from(clipper.data.buffer,0,258*64));assert(preHeightTextureRowsEqual);beforeHeight.dispose();assert(clipper.data.subarray((218+expectedAddition)*16).every(x=>x===0));previous.dispose();clipper.dispose();
});

check('the reviewed real near group receives only museum clipping in colour, depth and distance passes',()=>{
 assert.equal(evidence.near_groups.length,1);const spec=evidence.near_groups[0];assert.deepEqual([...spec.feature_local_ids].sort((a,b)=>a-b),[...actualNearIds].sort((a,b)=>a-b));assert.deepEqual(spec.clip_feature_local_ids,targetIds);assert.equal(spec.triangles,expectedAddition);assert.equal(spec.base_triangles,expectedBaseAddition);assert.equal(spec.display_height_triangles,expectedHeightAddition);
 const clipper=new CandidateCityClipper({THREE,geographicPosition});clipper.update(newDisplayClips);const meshes=[];
 for(const foreign of [false,true]){
  const ids=foreign?spec.feature_local_ids.filter(x=>!targetIds.includes(x)):spec.feature_local_ids,group=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());group.add(mesh);meshes.push(mesh);
  clipper.bindObject(group,{id:foreign?'foreign-owners-only-control':spec.group_id,parent:{id:spec.macro_id},ids});
  for(const [material,kind] of [[mesh.material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']]){const lib=THREE.ShaderLib[kind],shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:{}};material.onBeforeCompile(shader,{});assert.equal(shader.uniforms.candidateClipCount.value,foreign?0:expectedAddition);assert.equal(shader.uniforms.candidateHasFeatureIds.value,0);assert.equal(shader.uniforms.candidateClipTexture.value.image.height,limit);}
 }
 nearChecks=clipper.getState().ownerScopedSources;const real=nearChecks.find(r=>r.id===spec.group_id);assert.deepEqual(real.clip_feature_local_ids,targetIds);assert.equal(real.triangles,expectedAddition);
 clipper.dispose();for(const mesh of meshes){mesh.geometry.dispose();mesh.material.dispose();}
});

check('vector replacement respects reviewed interface residuals and leaves all supplied context identities untouched',()=>{
 assert.equal(evidence.source_features.length,2);assert(evidence.context_sources.length>0);
 assert.deepEqual(evidence.source_features.map(r=>r.source_id).sort(),[sourceId,siteSourceId].sort());
 const real=evidence.source_features.map(r=>({type:'Feature',id:r.source_id,properties:{id:r.source_id,height:r.map_height_m??1},geometry:r.geometry_wgs84}));
 const features=[...real,...real.map((r,i)=>({...structuredClone(r),id:`synthetic-same-footprint-foreign-${i}`,properties:{id:`synthetic-same-footprint-foreign-${i}`,height:1}})),...evidence.context_sources.map(r=>({type:'Feature',id:r.source_id,properties:{id:r.source_id,height:r.map_height_m??1},geometry:r.geometry_wgs84}))];
 const frozen=JSON.stringify(features),result=planCandidateVectorClipping(features,{candidateClips:newClips},{source:'overture-buildings',sourceLayer:'building'});assert.equal(JSON.stringify(features),frozen);assert.equal(result.stats.clippingErrors,0);assert.equal(result.desired.size,2);assert.deepEqual([...result.desired.values()].map(r=>r.id).sort(),[sourceId,siteSourceId].sort());assert(result.residualData.features.every(r=>[sourceId,siteSourceId].includes(r.properties.id)));
 const residuals=evidence.source_features.map(r=>{assert(Number.isFinite(r.expected_vector_residual_area_m2),'Require explicit final residual contract');const found=result.residualData.features.filter(f=>f.properties.id===r.source_id),area=found.reduce((sum,f)=>sum+metricArea(f.geometry),0);assert(Math.abs(area-r.expected_vector_residual_area_m2)<0.002,r.source_id);return{id:r.source_id,source_area_runtime_m2:metricArea(r.geometry_wgs84),residual_area_m2:area,expected_residual_area_m2:r.expected_vector_residual_area_m2};});
 const covered=planCandidateVectorClipping(features,{candidateClips:newClips,alreadyCovered:fid=>[sourceId,siteSourceId].includes(fid)},{source:'overture-buildings',sourceLayer:'building'});assert.equal(covered.desired.size,0);assert.equal(covered.residualData.features.length,0);
 vectorChecks={source_areas:residuals,real_context_features:evidence.context_sources.length,synthetic_same_footprint_foreign_controls:2,reviewed_interface_residuals_preserved:true};
});

check('production ground collision covers actual low structure and retains reviewed open entrance and road areas',()=>{
 assert(validCandidateGeometry(added.collision_geometry,{collision:true}));assert(evidence.ground_probes.some(p=>p.expected===null));assert(evidence.ground_probes.some(p=>p.expected==='building'));
 for(const p of evidence.ground_probes){assert.equal(candidateGeometryContains(added.collision_geometry,p.wgs84),p.expected==='building',p.name);if(p.local_xy_m){const point=fromLocal(p.local_xy_m);assert(point.every((v,i)=>Math.abs(v-p.wgs84[i])<1e-10),p.name);}}
 assert(evidence.open_ground_areas.length>=1,'Require reviewed real open ground');
 const openAreas=evidence.open_ground_areas.map(p=>{const intersection=globalThis.polygonClipping.intersection(parts(added.collision_geometry),parts(p.geometry_wgs84)),intersectionArea=metricArea({type:'MultiPolygon',coordinates:intersection});assert(intersectionArea<1e-6,p.name);return{name:p.name,ground_collision_intersection_m2:intersectionArea};});
 groundChecks={collision_parts:parts(added.collision_geometry).length,closed_ring_lengths:parts(added.collision_geometry).map(rings=>rings.map(r=>r.length)),positive_probes:evidence.ground_probes.filter(p=>p.expected==='building').length,negative_probes:evidence.ground_probes.filter(p=>p.expected===null).length,open_areas:openAreas,note:'Production2D containment complements actual-triangle low-occupancy checks. No museum interior or elevated walking is enabled.'};
});

const bindings=[...new Set([...unchangedFiles,...runtimeChangeFiles,runtimeChangePath,...authorizedReadmes,...authorizedNavigationArtifacts,'src/candidate-city-clipping.js','tests/candidate-city-clipping.test.mjs','index.html','data/candidate-city-integrations.json','data/global-models/additional-placement.json','data/global-models/candidate-inventory.json',footprintPath,`assets/models/candidates/${id}/manifest.json`,'data/audit/city-museum-v1/global-integration-checks.mjs'])].map(file=>{const b=read(file);return{file,bytes:b.length,sha256:sha(b)};});
const report={schema:'city-museum-global-integration-delta-v1',passed:checks.length,failed:0,checks,baseline_commit:baselineCommit,entry_id:id,total_destinations:81,candidate_models:41,yangpu_count:6,huangpu_count:28,route:`index.html#landmark=${id}&mode=overview`,walking_enabled:false,clipping_triangles:{before:beforeTriangles,addition:addedTriangles,after:afterTriangles,limit},historical_texture_rows_equal:historicalTextureRowsEqual,historical_texture_payload_bytes_compared:218*64,pre_height_texture_rows_equal:preHeightTextureRowsEqual,pre_height_texture_payload_bytes_compared:258*64,display_height_clipping:{base_addition:expectedBaseAddition,height_addition:expectedHeightAddition,gpu_model_rows:expectedAddition,source_change_report_sha256:sha(runtimeChangeBytes)},authorized_readme_navigation_migration:{old_readmes:authorizedReadmes.size,each_exact_operation_replayed:true,report_sha256:sha(navigationBytes)},near_group_fixture_checks:nearChecks,vector_checks:vectorChecks,ground_collision:groundChecks,scope:'Final production merge/navigation, unchanged historical catalogue and actual old/new clipper payload, reviewed exact source identity and near owners, frozen model contract, source vector correction and production collision. Near meshes in these shader tests are explicit fixtures; actual decoded source/asset geometry belongs to mapping/independent evidence and browser rendering. No historical model asset matrix replay.',bindings};
writeFileSync(new URL('global-integration-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:checks.length,total:81,candidates:41,triangles:afterTriangles,limit,groundChecks}));
