// Incremental Municipal Council registration checks. Earlier model evidence is immutable.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
import * as THREE from '../../../vendor/three.module.js';
import {mergeCandidateCityModels} from '../../../src/candidate-city-integrations.js';
import {CandidateCityClipper} from '../../../src/candidate-city-clipping.js';
import {planCandidateVectorClipping} from '../../../src/candidate-vector-clipping.js';
import {resolveNavigationRoute} from '../../../src/landmark-navigation.js';
import {walkingPose} from '../../../src/precise-registration-ui.js';

const project=new URL('../../../',import.meta.url),id='huangpu-shanghai-municipal-council';
const baselineCommit='1a0185ec31a9cf665f80fc6bc2c530d3e273c5b8';
const read=path=>readFileSync(new URL(path,project)),json=path=>JSON.parse(read(path));
const original=path=>execFileSync('git',['show',`${baselineCommit}:projects/shanghai/${path}`],{cwd:project,maxBuffer:8*1024*1024});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const vendorContext={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};
vendorContext.exports=vendorContext.module.exports;vendorContext.self=vendorContext;vendorContext.globalThis=vendorContext;
vm.runInNewContext(read('vendor/maplibre-gl.js').toString(),vendorContext);
const maplibre=vendorContext.module.exports,mapOrigin=maplibre.MercatorCoordinate.fromLngLat([121.4737,31.2304]),mapUnit=mapOrigin.meterInMercatorCoordinateUnits();
const geographicPosition=(lng,lat)=>{const p=maplibre.MercatorCoordinate.fromLngLat([lng,lat]);return new THREE.Vector3((p.x-mapOrigin.x)/mapUnit,0,(p.y-mapOrigin.y)/mapUnit);};

const base=json('data/landmarks.json'),catalog=json('data/candidate-city-integrations.json');
const old=JSON.parse(original('data/candidate-city-integrations.json'));
const footprintPath='data/audit/municipal-council-v1/footprint-review.json',footprint=json(footprintPath);
const placement=json('data/global-models/additional-placement.json'),inventory=json('data/global-models/candidate-inventory.json');
const checks=[];function check(name,fn){fn();checks.push(name);}
let historicalTextureRowsEqual=false,sourceAreaRuntime,sourceRemainderGeographicRatio;
let merged,added,beforeTriangles,afterTriangles,addedTriangles,sourceRemainderRatio,sourceRemainderArea,sourceRemainderRegions,sourceRemainderSymmetricDifferenceRatio,sourceRemainderSymmetricDifferenceArea;
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
check('Municipal Council adds one overview destination to the existing 75-entry shared map',()=>{
 assert.equal(base.length,40);assert.equal(old.models.length,35);assert.equal(catalog.models.length,36);
 merged=mergeCandidateCityModels(base,catalog);assert.equal(merged.length,76);assert.equal(new Set(merged.map(r=>r.id)).size,76);
 added=merged.find(r=>r.id===id);assert(added?.city_integration);assert.equal(walkingPose(added),null);
 for(const r of merged){const route=resolveNavigationRoute(`#landmark=${r.id}&mode=overview`,{landmarks:merged});assert.equal(route.place.id,r.id);assert.equal(route.mode,'overview');}
 assert.match(read('index.html').toString(),/id="landmark-count">76<\/span>/);
 assert.equal(merged.filter(r=>r.districtId==='310101').length,28);
});
check('all 35 earlier candidate rows, additional placements and historical audits remain unchanged',()=>{
 assert.deepEqual(catalog.models.filter(r=>r.id!==id),old.models);assert.equal(catalog.models.at(-1).id,id);
 const oldInventory=JSON.parse(original('data/global-models/candidate-inventory.json'));
 assert.deepEqual(inventory.records.filter(r=>r.id!==id),oldInventory.records);
 assert.deepEqual(inventory.current_delivery_manifests,['projects/shanghai/assets/models/candidates/'+id+'/manifest.json']);
 const frozen=inventory.prior_incremental_inventory;assert.equal(frozen.file,'data/audit/grosvenor-house-v1/inventory-increment.json');
 const frozenBytes=read(frozen.file);assert.equal(frozen.bytes,frozenBytes.length);assert.equal(frozen.sha256,sha(frozenBytes));
 assert.equal(inventory.verification.current_run_added_files,4);assert.equal(inventory.candidate_manifest_count,38);
 assert.equal(inventory.verification.files,152);assert.equal(inventory.verification.inherited_incremental_files,20);
 const prior=JSON.parse(original('data/global-models/additional-placement.json'));
 assert.deepEqual(placement.records.filter(r=>r.id!==id),prior.records);
 assert.deepEqual(placement.source_contracts.filter(r=>r.file!==footprintPath),prior.source_contracts);
 const changes=execFileSync('git',['diff','--name-only',baselineCommit,'--',':(top)projects/shanghai/data/audit'],{cwd:project}).toString().trim().split('\n').filter(Boolean);
 assert(changes.every(p=>p.startsWith('projects/shanghai/data/audit/municipal-council-v1/')));
});
const unchangedFiles=['data/landmarks.json','data/global-models/urban-placement.json','data/global-models/chongming-placement.json',
 'vendor/maplibre-gl.js','data/audit/global-model-integration-v1/inventory.json','data/audit/new-wing-on-company-v1/inventory-increment.json','data/audit/xinxin-company-v1/inventory-increment.json','data/audit/daxin-company-v1/inventory-increment.json','data/audit/cathay-mansions-v1/inventory-increment.json','data/audit/grosvenor-house-v1/inventory-increment.json',
 'src/building-beacons.js','src/candidate-vector-clipping.js','src/map-scene.js','src/candidate-overview-camera.js','tools/build_candidate_city_integrations.py'];
check('existing base entries, placement evidence and unaffected production integrations retain their previous bytes',()=>{
 for(const file of unchangedFiles)assert.equal(sha(read(file)),sha(original(file)),file);
});
check('new placement matches the exact reviewed source contract and unique old-building owner',()=>{
 const binding=placement.source_contracts.find(r=>r.file===footprintPath);assert(binding);const raw=read(footprintPath);
 assert.equal(binding.bytes,raw.length);assert.equal(binding.sha256,sha(raw));assert.equal(binding.record,'proposed_placement_contract');
 assert.deepEqual(placement.records.find(r=>r.id===id),footprint.proposed_placement_contract);
 assert.deepEqual(added.source_feature_ids,{building:['86e8b002-5e0e-4912-9807-086c2afeb27c'],building_part:[]});
 assert.equal(added.owner.macro_id,'14-13720-6694');assert.equal(added.owner.feature_local_id,1554);
 assert.deepEqual(added.replacement_geometry,footprint.proposed_placement_contract.replacement_geometry);
 assert.deepEqual(added.collision_geometry,footprint.proposed_placement_contract.collision_geometry);
});
const {CandidateCityClipper:LegacyClipper}=await import('data:text/javascript;base64,'+original('src/candidate-city-clipping.js').toString('base64'));
check('raising texture capacity preserves all113 historical triangle rows byte for byte',()=>{
 const config={THREE,geographicPosition};
 const prior=new LegacyClipper(config),current=new CandidateCityClipper(config);prior.update(clips(old.models));current.update(clips(old.models));
 assert.equal(prior.getState().triangles,113);assert.equal(current.getState().triangles,113);
 assert.equal(prior.texture.image.height,128);assert.equal(current.texture.image.height,192);
 historicalTextureRowsEqual=Buffer.from(prior.data.buffer,0,113*64).equals(Buffer.from(current.data.buffer,0,113*64));assert(historicalTextureRowsEqual);
 assert.deepEqual(current.getState().clippingTexture,{width:4,height:192,bytes:12288,type:'FloatType',format:'RGBAFormat',minFilter:'NearestFilter',magFilter:'NearestFilter',generateMipmaps:false});
 prior.dispose();current.dispose();
});
check('the production shader triangulator stays within its 192-triangle budget after this one addition',()=>{
 const clipper=new CandidateCityClipper({THREE,geographicPosition});
 clipper.update(clips(old.models));beforeTriangles=clipper.getState().triangles;assert.equal(beforeTriangles,113);
 clipper.update(clips([added]));addedTriangles=clipper.getState().triangles;assert.equal(addedTriangles,footprint.proposed_placement_contract.expected_replacement_triangle_count);
 const ownerIds=new Set(Array.from({length:addedTriangles},(_,i)=>clipper.data[i*16+12]));
 assert.deepEqual([...ownerIds],[1554]);assert(!ownerIds.has(1754));
 assert(Array.from({length:addedTriangles},(_,i)=>clipper.data[i*16+13]).every(value=>value>0));
 clipper.update(clips(catalog.models));afterTriangles=clipper.getState().triangles;
 assert.equal(afterTriangles,beforeTriangles+addedTriangles);assert(afterTriangles<=192);clipper.dispose();
});
check('the reviewed near owner groups retain the Municipal clip only for its own partial source group',()=>{
 const requirement=footprint.near_group_owner_isolation_requirement;
 assert.equal(requirement.own_group_has_per_feature_attribute,false);assert(requirement.own_group_ids.includes(1554));
 const foreign=footprint.baseline_foreign_native_group_preservation.groups;assert(foreign.some(g=>g.representative_owner===1754));
 assert(foreign.every(g=>!g.group_owner_ids.includes(1554)));
 const clipper=new CandidateCityClipper({THREE,geographicPosition});
 clipper.update(clips([added]));
 const groups=[requirement.own_group_ids,...foreign.map(g=>g.group_owner_ids)].map((ids,index)=>{
  const group=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());group.add(mesh);
  clipper.bindObject(group,{id:index?'reviewed-foreign-group-fixture-'+index:'reviewed-municipal-group-fixture',parent:{id:added.owner.macro_id},ids});
  for(const [material,kind] of [[mesh.material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']]){
   const lib=THREE.ShaderLib[kind],shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:{}};material.onBeforeCompile(shader,{});
   assert.equal(shader.uniforms.candidateHasFeatureIds.value,0);assert.equal(shader.uniforms.candidateClipCount.value,index?0:addedTriangles);
  }
  return {group,mesh};
 });
 const states=clipper.getState().ownerScopedSources;assert.equal(states.length,1+foreign.length);
 assert.equal(states[0].triangles,addedTriangles);assert.deepEqual(states[0].clip_feature_local_ids,[1554]);
 for(const state of states.slice(1)){assert.equal(state.triangles,0);assert.deepEqual(state.clip_feature_local_ids,[]);}
 clipper.dispose();for(const {mesh} of groups){mesh.geometry.dispose();mesh.material.dispose();}
});
check('the production vector correction affects only the identified old-building source and defers when its city GLB is active',()=>{
 const own=added.source_feature_ids.building[0],foreign='municipal-foreign-owner-fixture';
 const geometry=footprint.proposed_placement_contract.source_limit_geometry||footprint.geometry.source_geometry;assert(geometry);
 const neighbors=footprint.exclusions.context_sources_within_80m;assert(neighbors.some(r=>r.local_id===1754));
 const features=[own,foreign].map(id=>({type:'Feature',id,properties:{id,height:1},geometry}));
 features.push(...neighbors.map(r=>({type:'Feature',id:r.source_id,properties:{id:r.source_id,height:r.map_height_m},geometry:r.source_geometry_wgs84})));
 const frozenFeatures=JSON.stringify(features);
 const result=planCandidateVectorClipping(features,{candidateClips:clips([added])},{source:'overture-buildings',sourceLayer:'building'});
 assert.equal(JSON.stringify(features),frozenFeatures);
 assert(neighbors.every(r=>![...result.desired.values()].some(value=>value.id===r.source_id)));
 assert.equal(result.desired.size,1);assert.equal([...result.desired.values()][0].id,own);assert.equal(result.stats.clippingErrors,0);
 assert(result.residualData.features.every(f=>f.properties.id===own));assert(result.residualData.features.length<=1);
 const metricArea=g=>{
  const anchor=maplibre.MercatorCoordinate.fromLngLat([added.lng,added.lat]),unit=anchor.meterInMercatorCoordinateUnits();
  return area({type:'MultiPolygon',coordinates:parts(g).map(rings=>rings.map(ring=>ring.map(([lng,lat])=>{
   const point=maplibre.MercatorCoordinate.fromLngLat([lng,lat]);return[(point.x-anchor.x)/unit,(point.y-anchor.y)/unit];
  })))});
 };
 const sourceArea=sourceAreaRuntime=metricArea(geometry);assert(Math.abs(sourceArea-footprint.geometry.source_area_runtime_m2)<0.001);
 sourceRemainderGeographicRatio=result.residualData.features.reduce((sum,f)=>sum+area(f.geometry),0)/area(geometry);
 sourceRemainderArea=result.residualData.features.reduce((sum,f)=>sum+metricArea(f.geometry),0);
 sourceRemainderRatio=sourceRemainderArea/sourceArea;
 const contract=footprint.proposed_placement_contract;assert.equal(added.partial_model,true);
 assert(contract.source_retained_fraction>0);assert(contract.source_retained_area_runtime_m2>0);
 assert.equal(result.residualData.features.length,1);const retained=result.residualData.features[0].geometry;
 sourceRemainderRegions=parts(retained).length;assert.equal(sourceRemainderRegions,parts(contract.remaining_source_geometry).length);assert(sourceRemainderRegions>0);
 assert(Math.abs(sourceRemainderRatio-contract.source_retained_fraction)<1e-7,'The independently reviewed modern western remainder must remain with its measured source-area fraction');
 assert(Math.abs(sourceRemainderArea-contract.source_retained_area_runtime_m2)<0.001);
 const symmetricDifference=globalThis.polygonClipping.xor(parts(retained),parts(contract.remaining_source_geometry));
 sourceRemainderSymmetricDifferenceArea=metricArea({type:'MultiPolygon',coordinates:symmetricDifference});
 sourceRemainderSymmetricDifferenceRatio=sourceRemainderSymmetricDifferenceArea/sourceArea;
 assert(sourceRemainderSymmetricDifferenceArea<0.002,'WGS84 vector Boolean output must match the physical-frame retained polygon within0.002m² numerical projection tolerance');
 const alreadyCovered=planCandidateVectorClipping(features,{candidateClips:clips([added]),alreadyCovered:id=>id===own},{source:'overture-buildings',sourceLayer:'building'});
 assert.equal(alreadyCovered.desired.size,0);assert.equal(alreadyCovered.residualData.features.length,0);
});
const bindings=[...new Set([...unchangedFiles,'index.html','data/candidate-city-integrations.json','data/global-models/additional-placement.json',
 'data/global-models/candidate-inventory.json',footprintPath,'data/audit/municipal-council-v1/global-integration-checks.mjs','src/candidate-city-clipping.js','tests/candidate-city-clipping.test.mjs','src/building-beacons.js','tests/building-beacons.test.mjs','tests/candidate-overview-camera.test.mjs'])]
 .map(file=>{const bytes=read(file);return{file,bytes:bytes.length,sha256:sha(bytes)};});
const report={schema:'municipal-global-integration-delta-v1',passed:checks.length,failed:0,checks,baseline_commit:baselineCommit,entry_id:id,
 total_destinations:76,candidate_models:36,huangpu_count:28,route:`index.html#landmark=${id}&mode=overview`,walking_enabled:false,
 clipping_triangles:{before:beforeTriangles,addition:addedTriangles,after:afterTriangles,limit:192},historical_texture_rows_equal:historicalTextureRowsEqual,historical_texture_payload_bytes_compared:113*64,source_remainder_ratio:sourceRemainderRatio,source_remainder_area_runtime_m2:sourceRemainderArea,source_remainder_regions:sourceRemainderRegions,source_remainder_symmetric_difference_ratio:sourceRemainderSymmetricDifferenceRatio,source_remainder_symmetric_difference_area_runtime_m2:sourceRemainderSymmetricDifferenceArea,source_remainder_symmetric_difference_tolerance_m2:0.002,
 area_measurement:{method:'Actual shipped MapLibre MercatorCoordinate at the model anchor; rotation preserves area. Production vector Boolean geometry is computed in WGS84 before physical-area measurement.',source_area_runtime_m2:sourceAreaRuntime,reviewed_source_area_runtime_m2:footprint.geometry.source_area_runtime_m2,reviewed_retained_area_runtime_m2:footprint.proposed_placement_contract.source_retained_area_runtime_m2,rejected_degree_plane_ratio:sourceRemainderGeographicRatio,reviewed_metric_ratio:footprint.proposed_placement_contract.source_retained_fraction,degree_plane_ratio_error:Math.abs(sourceRemainderGeographicRatio-footprint.proposed_placement_contract.source_retained_fraction),unchanged_metric_ratio_tolerance:1e-7,retained_area_tolerance_m2:0.001,symmetric_difference_tolerance_basis:'The independent review intersects in physical Mercator coordinates while production vector Boolean operations intersect WGS84 straight segments. The resulting conversion difference is bounded explicitly in square metres:0.002m² is less than2.8e-7 of this source. The metric ratio and retained-area checks retain their existing tolerances; the previous degree-plane ratio check remains recorded as rejected. This numeric tolerance is separate from authored placement uncertainty.'},
 scope:'Static production merge/navigation, exact placement evidence binding, shipped MapLibre Mercator projection and shader triangulation, reviewed near-group ownership filtering on synthetic untagged meshes, and vector ownership checks for the new old-building source only. The foreign-ID duplicate and height=1 are identity fixtures; actual neighboring source geometry is also checked without mutation. Near-group fixtures use the actual reviewed tile owner arrays but do not claim loaded native geometry or rendered pixels. Actual model visibility and the retained modern western wing and independent neighboring source preservation require the separate browser check. Existing city GLB owners defer to shader correction instead of vector duplication.',bindings};
writeFileSync(new URL('global-integration-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:checks.length,total:76,candidates:36,triangles:afterTriangles,sourceRemainderRatio}));
