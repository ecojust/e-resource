// Incremental Xinxin registration checks. Earlier model evidence is immutable.
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

const project=new URL('../../../',import.meta.url),id='huangpu-xinxin-company';
const baselineCommit='7b85c03efc436527efeb803b0743e4b2580e78d7';
const read=path=>readFileSync(new URL(path,project)),json=path=>JSON.parse(read(path));
const original=path=>execFileSync('git',['show',`${baselineCommit}:projects/shanghai/${path}`],{cwd:project});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const base=json('data/landmarks.json'),catalog=json('data/candidate-city-integrations.json');
const old=JSON.parse(original('data/candidate-city-integrations.json'));
const footprint=json('data/audit/xinxin-company-v1/footprint-review.json');
const checks=[];function check(name,fn){fn();checks.push(name);}
let merged,added,beforeTriangles,afterTriangles,addedTriangles,partialRatio;

function clips(models){
  const result=new Map();
  for(const row of models){
    if(row.replacement_geometry)result.set(row.id,{id:row.id,geometry:row.replacement_geometry,owner:row.owner,owners:row.owners,source_feature_ids:row.source_feature_ids});
    if(row.site_replacement)result.set(row.site_replacement.id,row.site_replacement);
  }
  return [...result.values()];
}
const parts=geometry=>geometry.type==='Polygon'?[geometry.coordinates]:geometry.coordinates;
const area=geometry=>parts(geometry).reduce((sum,rings)=>sum+rings.reduce((s,ring,j)=>{
  let a=0;for(let i=1;i<ring.length;i++)a+=(ring[i-1][0]-ring[0][0])*(ring[i][1]-ring[0][1])-(ring[i][0]-ring[0][0])*(ring[i-1][1]-ring[0][1]);
  return s+(j?-1:1)*Math.abs(a)/2;
},0),0);

check('the southern store exterior adds one overview destination to the existing 71-entry shared map',()=>{
  assert.equal(base.length,40);assert.equal(old.models.length,31);assert.equal(catalog.models.length,32);
  merged=mergeCandidateCityModels(base,catalog);assert.equal(merged.length,72);assert.equal(new Set(merged.map(row=>row.id)).size,72);
  added=merged.find(row=>row.id===id);assert(added?.city_integration);assert.equal(walkingPose(added),null);
  assert.equal(added.partial_model,true);
  for(const record of merged){const route=resolveNavigationRoute(`#landmark=${record.id}&mode=overview`,{landmarks:merged});assert.equal(route.place.id,record.id);assert.equal(route.mode,'overview');}
  assert.match(read('index.html').toString(),/id="landmark-count">72<\/span>/);
});
check('all 31 earlier candidate rows and the earlier delivery audit remain unchanged',()=>{
  assert.deepEqual(catalog.models.filter(row=>row.id!==id),old.models);assert.equal(catalog.models.at(-1).id,id);
  const changes=execFileSync('git',['diff','--name-only',baselineCommit,'--',':(top)projects/shanghai/data/audit/new-wing-on-company-v1'],{cwd:project}).toString().trim();
  assert.equal(changes,'');
});
const unchangedFiles=['data/landmarks.json','data/global-models/urban-placement.json','data/global-models/chongming-placement.json',
  'data/audit/global-model-integration-v1/inventory.json','data/audit/new-wing-on-company-v1/inventory-increment.json',
  'src/candidate-city-clipping.js','src/candidate-vector-clipping.js','src/map-scene.js','src/building-beacons.js','src/candidate-overview-camera.js'];
check('existing placements, base entries, sprites, cameras and clipping implementations retain their previous bytes',()=>{
  for(const file of unchangedFiles)assert.equal(sha(read(file)),sha(original(file)),file);
});
check('the production shader triangulator adds only the new bounded southern correction within its 128-triangle budget',()=>{
  const clipper=new CandidateCityClipper({THREE,geographicPosition:(lng,lat)=>new THREE.Vector3((lng-121)*100000,0,-(lat-31)*100000)});
  clipper.update(clips(old.models));beforeTriangles=clipper.getState().triangles;
  clipper.update(clips([added]));addedTriangles=clipper.getState().triangles;
  clipper.update(clips(catalog.models));afterTriangles=clipper.getState().triangles;
  assert.equal(beforeTriangles,62);assert(addedTriangles>0);assert.equal(afterTriangles,beforeTriangles+addedTriangles);assert(afterTriangles<=128);clipper.dispose();
});
check('the production vector plan retains the northern source remainder and ignores a geometrically overlapping foreign ID',()=>{
  assert.deepEqual(added.source_feature_ids,{building:[footprint.identity.source_id],building_part:[]});
  assert.equal(added.owner.macro_id,'14-13720-6694');assert.equal(added.owner.feature_local_id,1453);
  const own=footprint.identity.source_id,foreign='6312d66f-e7fa-43b1-a1cc-63f920d1f53d',geometry=footprint.geometry.source_geometry;
  assert.equal(own,'7e69180c-6b22-4417-a40b-f5dcd2235bb9');
  const features=[own,foreign].map(id=>({type:'Feature',id,properties:{id,height:24.726},geometry}));
  const result=planCandidateVectorClipping(features,{candidateClips:clips([added])},{source:'overture-buildings',sourceLayer:'building'});
  assert.deepEqual([...result.desired.values()],[{id:own,residual:true}]);
  assert.equal(result.residualData.features.length,1);assert.equal(result.stats.partialIDs,1);assert.equal(result.stats.clippingErrors,0);
  partialRatio=area(result.residualData.features[0].geometry)/area(geometry);
  assert(partialRatio>.59&&partialRatio<1,'The unmodeled north must remain, with a nonempty modeled south');
  const alreadyCovered=planCandidateVectorClipping(features,{candidateClips:clips([added]),alreadyCovered:id=>id===own},{source:'overture-buildings',sourceLayer:'building'});
  assert.equal(alreadyCovered.desired.size,0);assert.equal(alreadyCovered.residualData.features.length,0);
});
const bindings=[...new Set([...unchangedFiles,'index.html','data/candidate-city-integrations.json','data/global-models/additional-placement.json',
  'data/global-models/candidate-inventory.json','data/audit/xinxin-company-v1/footprint-review.json','tools/build_candidate_city_integrations.py',
  'tests/building-beacons.test.mjs','tests/candidate-overview-camera.test.mjs','tests/candidate-catalog-increment.test.py'])]
  .map(file=>{const bytes=read(file);return{file,bytes:bytes.length,sha256:sha(bytes)};});
const report={schema:'xinxin-global-integration-delta-v1',passed:checks.length,failed:0,checks,
  baseline_commit:baselineCommit,entry_id:id,total_destinations:72,candidate_models:32,
  route:`index.html#landmark=${id}&mode=overview`,walking_enabled:false,
  clipping_triangles:{before:beforeTriangles,addition:addedTriangles,after:afterTriangles,limit:128},
  northern_source_remainder_ratio:partialRatio,
  scope:'Static production merge, navigation, shader triangulation and vector plan checks. The foreign-ID duplicate is an ownership fixture. The actual northern source difference must also remain visible in browser QA. When an existing city GLB covers the owner, the vector plan correctly defers to its shader correction instead of adding a duplicate residual.',
  bindings};
writeFileSync(new URL('global-integration-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:checks.length,total:72,candidates:32,triangles:afterTriangles,northernSourceRemainder:partialRatio}));
