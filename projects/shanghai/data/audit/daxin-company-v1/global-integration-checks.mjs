// Incremental Daxin registration checks. Earlier model evidence is immutable.
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

const project=new URL('../../../',import.meta.url),id='huangpu-daxin-company';
const baselineCommit='248df5c15988bba05f073485cacc93083fb581e8';
const read=path=>readFileSync(new URL(path,project)),json=path=>JSON.parse(read(path));
const original=path=>execFileSync('git',['show',`${baselineCommit}:projects/shanghai/${path}`],{cwd:project});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const base=json('data/landmarks.json'),catalog=json('data/candidate-city-integrations.json');
const old=JSON.parse(original('data/candidate-city-integrations.json'));
const footprintPath='data/audit/daxin-company-v1/footprint-review.json',footprint=json(footprintPath);
const placement=json('data/global-models/additional-placement.json');
const checks=[];function check(name,fn){fn();checks.push(name);}
let merged,added,beforeTriangles,afterTriangles,addedTriangles,sourceRemainderRatio;
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
check('Daxin adds one overview destination to the existing 72-entry shared map',()=>{
 assert.equal(base.length,40);assert.equal(old.models.length,32);assert.equal(catalog.models.length,33);
 merged=mergeCandidateCityModels(base,catalog);assert.equal(merged.length,73);assert.equal(new Set(merged.map(r=>r.id)).size,73);
 added=merged.find(r=>r.id===id);assert(added?.city_integration);assert.equal(walkingPose(added),null);
 for(const r of merged){const route=resolveNavigationRoute(`#landmark=${r.id}&mode=overview`,{landmarks:merged});assert.equal(route.place.id,r.id);assert.equal(route.mode,'overview');}
 assert.match(read('index.html').toString(),/id="landmark-count">73<\/span>/);
 assert.equal(merged.filter(r=>r.districtId==='310101').length,25);
});
check('all 32 earlier candidate rows, additional placements and historical audits remain unchanged',()=>{
 assert.deepEqual(catalog.models.filter(r=>r.id!==id),old.models);assert.equal(catalog.models.at(-1).id,id);
 const prior=JSON.parse(original('data/global-models/additional-placement.json'));
 assert.deepEqual(placement.records.filter(r=>r.id!==id),prior.records);
 assert.deepEqual(placement.source_contracts.filter(r=>r.file!==footprintPath),prior.source_contracts);
 const changes=execFileSync('git',['diff','--name-only',baselineCommit,'--',':(top)projects/shanghai/data/audit'],{cwd:project}).toString().trim().split('\n').filter(Boolean);
 assert(changes.every(p=>p.startsWith('projects/shanghai/data/audit/daxin-company-v1/')));
});
const unchangedFiles=['data/landmarks.json','data/global-models/urban-placement.json','data/global-models/chongming-placement.json',
 'data/audit/global-model-integration-v1/inventory.json','data/audit/new-wing-on-company-v1/inventory-increment.json','data/audit/xinxin-company-v1/inventory-increment.json',
 'src/candidate-city-clipping.js','src/candidate-vector-clipping.js','src/map-scene.js','src/building-beacons.js','src/candidate-overview-camera.js','tools/build_candidate_city_integrations.py'];
check('existing base entries, placement evidence and production integrations retain their previous bytes',()=>{
 for(const file of unchangedFiles)assert.equal(sha(read(file)),sha(original(file)),file);
});
check('new placement matches the exact reviewed source contract and unique old-building owner',()=>{
 const binding=placement.source_contracts.find(r=>r.file===footprintPath);assert(binding);const raw=read(footprintPath);
 assert.equal(binding.bytes,raw.length);assert.equal(binding.sha256,sha(raw));assert.equal(binding.record,'proposed_placement_contract');
 assert.deepEqual(placement.records.find(r=>r.id===id),footprint.proposed_placement_contract);
 assert.deepEqual(added.source_feature_ids,{building:['ca6dccd6-0c72-4376-8978-e6e660629037'],building_part:[]});
 assert.equal(added.owner.macro_id,'14-13720-6694');assert.equal(added.owner.feature_local_id,2372);
 assert.deepEqual(added.replacement_geometry,footprint.proposed_placement_contract.replacement_geometry);
 assert.deepEqual(added.collision_geometry,footprint.proposed_placement_contract.collision_geometry);
});
check('the production shader triangulator stays within its 128-triangle budget after this one addition',()=>{
 const clipper=new CandidateCityClipper({THREE,geographicPosition:(lng,lat)=>new THREE.Vector3((lng-121)*100000,0,-(lat-31)*100000)});
 clipper.update(clips(old.models));beforeTriangles=clipper.getState().triangles;assert.equal(beforeTriangles,66);
 clipper.update(clips([added]));addedTriangles=clipper.getState().triangles;assert(addedTriangles>0);
 clipper.update(clips(catalog.models));afterTriangles=clipper.getState().triangles;
 assert.equal(afterTriangles,beforeTriangles+addedTriangles);assert(afterTriangles<=128);clipper.dispose();
});
check('the production vector correction affects only the identified old-building source and defers when its city GLB is active',()=>{
 const own=added.source_feature_ids.building[0],foreign='daxin-foreign-owner-fixture';
 const geometry=footprint.proposed_placement_contract.source_limit_geometry||footprint.geometry.source_geometry;assert(geometry);
 const features=[own,foreign].map(id=>({type:'Feature',id,properties:{id,height:1},geometry}));
 const result=planCandidateVectorClipping(features,{candidateClips:clips([added])},{source:'overture-buildings',sourceLayer:'building'});
 assert.equal(result.desired.size,1);assert.equal([...result.desired.values()][0].id,own);assert.equal(result.stats.clippingErrors,0);
 assert(result.residualData.features.every(f=>f.properties.id===own));assert(result.residualData.features.length<=1);
 sourceRemainderRatio=result.residualData.features.reduce((sum,f)=>sum+area(f.geometry),0)/area(geometry);
 assert.equal(footprint.proposed_placement_contract.source_retained_fraction,0);
 assert.equal(footprint.proposed_placement_contract.source_retained_area_runtime_m2,0);
 assert(sourceRemainderRatio>=0&&sourceRemainderRatio<1e-8,'The independently bounded whole old-building source must be covered, without a residual sliver');
 const alreadyCovered=planCandidateVectorClipping(features,{candidateClips:clips([added]),alreadyCovered:id=>id===own},{source:'overture-buildings',sourceLayer:'building'});
 assert.equal(alreadyCovered.desired.size,0);assert.equal(alreadyCovered.residualData.features.length,0);
});
const bindings=[...new Set([...unchangedFiles,'index.html','data/candidate-city-integrations.json','data/global-models/additional-placement.json',
 'data/global-models/candidate-inventory.json',footprintPath,'data/audit/daxin-company-v1/global-integration-checks.mjs','tests/building-beacons.test.mjs','tests/candidate-overview-camera.test.mjs'])]
 .map(file=>{const bytes=read(file);return{file,bytes:bytes.length,sha256:sha(bytes)};});
const report={schema:'daxin-global-integration-delta-v1',passed:checks.length,failed:0,checks,baseline_commit:baselineCommit,entry_id:id,
 total_destinations:73,candidate_models:33,huangpu_count:25,route:`index.html#landmark=${id}&mode=overview`,walking_enabled:false,
 clipping_triangles:{before:beforeTriangles,addition:addedTriangles,after:afterTriangles,limit:128},source_remainder_ratio:sourceRemainderRatio,
 scope:'Static production merge/navigation, exact placement evidence binding, shader triangulation and vector ownership checks for the new old-building source only. The foreign-ID duplicate and height=1 are identity fixtures, not observed geometry. Actual model visibility and neighboring B/C preservation require the separate browser check. Existing city GLB owners defer to shader correction instead of vector duplication.',bindings};
writeFileSync(new URL('global-integration-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:checks.length,total:73,candidates:33,triangles:afterTriangles,sourceRemainderRatio}));
