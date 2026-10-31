// Targeted delivery delta. Original integration evidence remains untouched.
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

const project=new URL('../../../',import.meta.url),id='huangpu-new-wing-on-company',baselineCommit='d3306a4';
const read=path=>readFileSync(new URL(path,project));
const json=path=>JSON.parse(read(path));
const original=path=>execFileSync('git',['show',`${baselineCommit}:projects/shanghai/${path}`],{cwd:project});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const base=json('data/landmarks.json'),catalog=json('data/candidate-city-integrations.json');
const old=JSON.parse(original('data/candidate-city-integrations.json'));
const checks=[];function check(name,fn){fn();checks.push(name);}
let merged,added,beforeTriangles,afterTriangles;

check('the new entry joins 40 original and 30 prior candidates through the existing shared-map route',()=>{
  assert.equal(base.length,40);assert.equal(catalog.models.length,31);
  merged=mergeCandidateCityModels(base,catalog);assert.equal(merged.length,71);
  assert.equal(new Set(merged.map(row=>row.id)).size,71);
  added=merged.find(row=>row.id===id);assert(added?.city_integration);assert.equal(walkingPose(added),null);
  const route=resolveNavigationRoute(`#landmark=${id}&mode=overview`,{landmarks:merged});
  assert.equal(route.place.id,id);assert.equal(route.mode,'overview');
});
check('all thirty previously integrated model records remain unchanged and in their existing order',()=>{
  assert.deepEqual(catalog.models.filter(row=>row.id!==id),old.models);
  assert.equal(catalog.models.at(-1).id,id);
});
const unchangedFiles=['data/landmarks.json','data/global-models/urban-placement.json','data/global-models/chongming-placement.json',
  'data/audit/global-model-integration-v1/inventory.json','src/candidate-city-clipping.js','src/candidate-vector-clipping.js','src/map-scene.js'];
check('the earlier inventory, placements, base entries and clipping implementation retain their historical bytes',()=>{
  for(const file of unchangedFiles)assert.equal(sha(read(file)),sha(original(file)),file);
});
function clips(models){
  const result=new Map();
  for(const row of models){
    if(row.replacement_geometry)result.set(row.id,{id:row.id,geometry:row.replacement_geometry,owner:row.owner,owners:row.owners,source_feature_ids:row.source_feature_ids});
    if(row.site_replacement)result.set(row.site_replacement.id,row.site_replacement);
  }
  return [...result.values()];
}
check('the real clipping triangulator adds six triangles and stays inside the existing 128-triangle budget',()=>{
  const clipper=new CandidateCityClipper({THREE,geographicPosition:(lng,lat)=>new THREE.Vector3((lng-121)*100000,0,-(lat-31)*100000)});
  clipper.update(clips(old.models));beforeTriangles=clipper.getState().triangles;
  clipper.update(clips(catalog.models));afterTriangles=clipper.getState().triangles;
  assert.equal(beforeTriangles,56);assert.equal(afterTriangles,62);clipper.dispose();
});
check('the new vector correction recognizes only its declared building owner and preserves an overlapping foreign-ID fixture',()=>{
  assert.deepEqual(added.source_feature_ids,{building:['708d0e95-d551-414d-a3be-897a9fe2fb6b'],building_part:[]});
  assert.equal(added.owner.macro_id,'14-13720-6694');assert.equal(added.owner.feature_local_id,1275);
  const own=added.source_feature_ids.building[0],foreign='5d94b317-649b-4e66-8805-639274d488c7';
  const features=[own,foreign].map(id=>({type:'Feature',id,properties:{id,height:32.9},geometry:added.replacement_geometry}));
  const result=planCandidateVectorClipping(features,{candidateClips:clips([added])},{source:'overture-buildings',sourceLayer:'building'});
  assert.deepEqual([...result.desired.values()].map(row=>row.id),[own]);
  assert.equal(result.residualData.features.length,0);assert.equal(result.stats.clippingErrors,0);
});
const bindings=[...new Set([...unchangedFiles,'data/candidate-city-integrations.json','data/global-models/additional-placement.json',
  'data/global-models/candidate-inventory.json','src/building-beacons.js','src/candidate-overview-camera.js',
  'tools/build_candidate_city_integrations.py','tests/building-beacons.test.mjs','tests/candidate-overview-camera.test.mjs',
  'tests/candidate-catalog-increment.test.py'])].map(file=>{const bytes=read(file);return{file,bytes:bytes.length,sha256:sha(bytes)};});
const report={schema:'new-wing-on-global-integration-delta-v1',passed:checks.length,failed:0,checks,
  baseline_commit:baselineCommit,entry_id:id,total_destinations:71,candidate_models:31,
  route:`index.html#landmark=${id}&mode=overview`,walking_enabled:false,
  clipping_triangles:{before:beforeTriangles,after:afterTriangles,limit:128},
  scope:'Static integration delta using the production merge, route, geometry triangulator and vector ownership planner. The overlapping foreign-ID input is an intentional ownership fixture, not a representation of the old building geometry. Actual placement separation is documented by footprint-review.json. Actual loading, GPU visibility and phone input require the separate browser report.',
  related_targeted_runs:[{command:'node --test tests/building-beacons.test.mjs tests/candidate-overview-camera.test.mjs',passed:33,failed:0},
    {command:'python tests/candidate-catalog-increment.test.py',passed:5,failed:0},
    {command:'python tools/build_candidate_city_integrations.py --check',result:'passed; four incremental asset files read; original inventory reused'}],bindings};
writeFileSync(new URL('global-integration-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:checks.length,total:71,candidates:31,triangles:afterTriangles}));
