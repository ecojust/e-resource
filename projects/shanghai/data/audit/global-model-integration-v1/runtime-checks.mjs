// Run: node data/audit/global-model-integration-v1/runtime-checks.mjs
// These exercise source-preservation contracts independently of browser loading.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import * as THREE from '../../../vendor/three.module.js';
import {markVerifiedOrdinaryAsset} from '../../../src/ordinary-asset-verification.js';
import {mergeCandidateCityModels,candidateAssetVisible,candidateGeometryContains,CandidateCityState} from '../../../src/candidate-city-integrations.js';
import {planCandidateVectorClipping} from '../../../src/candidate-vector-clipping.js';
import {CandidateCityClipper} from '../../../src/candidate-city-clipping.js';

const checks=[];
function check(name,fn){fn();checks.push(name);}
const rectangle=(x1,y1,x2,y2)=>({type:'Polygon',coordinates:[[[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]]]});
const polygon=rectangle(121,31,121.001,31.001);
const assets={web:{file:'assets/full.glb',bytes:40,sha256:'a'.repeat(64)},lod:{file:'assets/lod.glb',bytes:30,sha256:'b'.repeat(64)}};
const sample=()=>({id:'test',kind:'building',lng:121,lat:31,heading:0,height_m:12,scale:1,placement:{status:'estimated'},
  navigation:{listed:true,walkStart:[121.002,31],bearing:270},assets,collision_geometry:polygon,replacement_geometry:polygon,
  source_feature_ids:{building:['source-a'],building_part:[]}});
const manifest=row=>({schema:'candidate-city-integrations-v1',models:[row]});

check('catalogue rejects duplicate IDs, unsafe asset paths, mismatched hashes and invalid walking poses',()=>{
  assert.equal(mergeCandidateCityModels([{id:'old'}],manifest(sample())).length,2);
  assert.throws(()=>mergeCandidateCityModels([{id:'test'}],manifest(sample())));
  for(const file of ['https://example.com/model.glb','assets/../hidden.glb']){
    const row=structuredClone(sample());row.assets.web.file=file;
    assert.throws(()=>mergeCandidateCityModels([],manifest(row)));
  }
  const hash=structuredClone(sample());hash.assets.web.sha256='wrong';assert.throws(()=>mergeCandidateCityModels([],manifest(hash)));
  const pose=sample();pose.navigation.walkStart=[121];assert.throws(()=>mergeCandidateCityModels([],manifest(pose)));
});

const scene=new THREE.Scene();
const group=new THREE.Group();scene.add(group);
const record={...mergeCandidateCityModels([],manifest(sample()))[0],status:'loaded',activeVariant:'full',object:group};
const records=new Map([[record.id,record]]);
const state=new CandidateCityState({getRecords:()=>records,getScene:()=>scene});

check('unverified model and forged GLB extras never enable clipping or collisions',()=>{
  group.userData.__ordinaryVerifiedAsset={modelId:'test',variant:'web',...assets.web};
  assert.equal(candidateAssetVisible(record,scene),false);state.sync();assert.equal(state.clips.length,0);assert.equal(state.collisions().length,0);
});
check('correct byte-verification receipt enables one source clip and one collision',()=>{
  markVerifiedOrdinaryAsset(group,{modelId:'test',variant:'web',asset:assets.web});
  assert.equal(candidateAssetVisible(record,scene),true);state.sync();assert.equal(state.clips.length,1);assert.equal(state.collisions().length,1);
  const source={name:'overture-buildings',layer:'building',id:'source-a'};
  assert.equal(state.clipsPoint(121.0005,31.0005,source),true);assert.equal(state.clipsPoint(121.002,31.0005,source),false);
  assert.equal(state.clipsPoint(121.0005,31.0005,{...source,id:'unrelated'}),false);
  assert.equal(state.clipsPoint(121.0005,31.0005),false);
});
check('hidden model, hidden ancestor, detached object, disposal and receipt mismatch restore source state',()=>{
  group.visible=false;state.sync();assert.equal(state.clips.length,0);group.visible=true;
  scene.visible=false;state.sync();assert.equal(state.active.length,0);scene.visible=true;
  scene.remove(group);state.sync();assert.equal(state.active.length,0);scene.add(group);
  record.catalogDisposed=true;state.sync();assert.equal(state.active.length,0);record.catalogDisposed=false;
  record.activeVariant='distant';state.sync();assert.equal(state.active.length,0);record.activeVariant='full';
  markVerifiedOrdinaryAsset(group,{modelId:'other',variant:'web',asset:assets.web});state.sync();assert.equal(state.active.length,0);
  markVerifiedOrdinaryAsset(group,{modelId:'test',variant:'web',asset:{...assets.web,sha256:'c'.repeat(64)}});state.sync();assert.equal(state.active.length,0);
  markVerifiedOrdinaryAsset(group,{modelId:'test',variant:'web',asset:assets.web});state.sync();assert.equal(state.active.length,1);
});
check('verified LOD remains active and triggers a variant-bound revision',()=>{
  const revision=state.revision;record.activeVariant='distant';markVerifiedOrdinaryAsset(group,{modelId:'test',variant:'lod',asset:assets.lod});
  state.sync();assert.equal(state.active.length,1);assert.ok(state.revision>revision);
  assert.equal(state.getState().active[0].assetSha256,assets.lod.sha256);
});
check('shared-site clipping is deduplicated and removed only after its last visible verified model',()=>{
  record.site_replacement={id:'shared-site',geometry:polygon,source_feature_ids:{building:['site-source'],building_part:[]}};
  const other=new THREE.Group();scene.add(other);
  const second={...record,id:'second',object:other};markVerifiedOrdinaryAsset(other,{modelId:'second',variant:'lod',asset:assets.lod});records.set('second',second);
  state.sync();assert.equal(state.clips.filter(x=>x.id==='shared-site').length,1);
  group.visible=false;state.sync();assert.equal(state.clips.filter(x=>x.id==='shared-site').length,1);
  other.visible=false;state.sync();assert.equal(state.clips.length,0);assert.equal(state.collisions().length,0);
});
check('polygon holes and MultiPolygon membership remain open',()=>{
  const hole={...polygon,coordinates:[polygon.coordinates[0],rectangle(121.0003,31.0003,121.0007,31.0007).coordinates[0]]};
  assert.equal(candidateGeometryContains(hole,[121.0005,31.0005]),false);
  assert.equal(candidateGeometryContains(hole,[121.0001,31.0001]),true);
  const multi={type:'MultiPolygon',coordinates:[hole.coordinates,rectangle(121.002,31,121.003,31.001).coordinates]};
  assert.equal(candidateGeometryContains(multi,[121.0025,31.0005]),true);
});

const source={type:'Feature',id:'source-a',properties:{id:'source-a',height:30},geometry:rectangle(121,31,121.002,31.002)};
const clip={id:'partial',geometry:rectangle(121,31,121.001,31.002),source_feature_ids:{building:['source-a'],building_part:[]}};
const context={source:'overture-buildings',sourceLayer:'building'};
check('partial vector replacement retains the other half of its source geometry and properties',()=>{
  const result=planCandidateVectorClipping([source],{candidateClips:[clip]},context);
  assert.equal(result.desired.size,1);assert.equal(result.residualData.features.length,1);assert.equal(result.stats.clippingErrors,0);
  const residual=result.residualData.features[0];assert.deepEqual(residual.properties,source.properties);
  assert.equal(candidateGeometryContains(residual.geometry,[121.0015,31.001]),true);
  assert.equal(candidateGeometryContains(residual.geometry,[121.0005,31.001]),false);
});
check('unrelated Overture IDs, empty source IDs and already-rendered city coverage are not clipped',()=>{
  const unrelated={...source,id:'source-b',properties:{id:'source-b'}};
  assert.equal(planCandidateVectorClipping([unrelated],{candidateClips:[clip]},context).desired.size,0);
  assert.equal(planCandidateVectorClipping([source],{candidateClips:[{...clip,source_feature_ids:{building:[],building_part:[]}}]},context).desired.size,0);
  assert.equal(planCandidateVectorClipping([source],{candidateClips:[clip]},{...context,sourceLayer:'building_part'}).desired.size,0);
  assert.equal(planCandidateVectorClipping([source],{candidateClips:[clip],alreadyCovered:()=>true},context).desired.size,0);
});
check('vector hole preservation and source-provider fallback retain source fragments',()=>{
  const centerCut={...clip,geometry:rectangle(121.0005,31.0005,121.0015,31.0015)};
  const result=planCandidateVectorClipping([source],{candidateClips:[centerCut]},context);
  assert.equal(result.residualData.features[0].geometry.coordinates[0].length,2);
  const osm=planCandidateVectorClipping([{...source,id:123}],{candidateClips:[clip]},{source:'openmaptiles',sourceLayer:'building'});
  assert.equal(osm.desired.size,1);assert.equal(osm.residualData.features.length,1);
});
check('shader clipping triangulates a polygon hole without filling it and returns to zero',()=>{
  const clipper=new CandidateCityClipper({THREE,geographicPosition:(x,z)=>({x,z})});
  const outer=rectangle(0,0,10,10),hole=rectangle(3,3,7,7);
  clipper.update([{id:'hole',geometry:{...outer,coordinates:[outer.coordinates[0],hole.coordinates[0]]},owner:{macro_id:'macro',feature_local_id:7}}]);
  let area=0;for(let i=0;i<clipper.triangleCount;i++){const d=clipper.data.slice(i*16,i*16+6);area+=Math.abs((d[2]-d[0])*(d[5]-d[1])-(d[4]-d[0])*(d[3]-d[1]))/2;assert.equal(clipper.data[i*16+12],7);}
  assert.equal(area,84);clipper.update([]);assert.equal(clipper.triangleCount,0);clipper.dispose();
});

let catalogueChecks;
check('the actual 30-model catalogue merges with all 40 original entries and fits the clipping budget',()=>{
  const existing=JSON.parse(readFileSync(new URL('../../landmarks.json',import.meta.url)));
  const catalogue=JSON.parse(readFileSync(new URL('../../candidate-city-integrations.json',import.meta.url)));
  const snapshot=JSON.stringify(existing),merged=mergeCandidateCityModels(existing,catalogue);
  assert.equal(existing.length,40);assert.equal(merged.length,70);assert.equal(new Set(merged.map(row=>row.id)).size,70);
  assert.equal(JSON.stringify(existing),snapshot);assert.equal(catalogue.models.filter(row=>row.navigation.listed).length,0);
  const clips=new Map();
  for(const row of catalogue.models){if(row.replacement_geometry)clips.set(row.id,{id:row.id,geometry:row.replacement_geometry,owner:row.owner,owners:row.owners});
    if(row.site_replacement)clips.set(row.site_replacement.id,row.site_replacement);}
  const clipperSource=readFileSync(new URL('../../../src/candidate-city-clipping.js',import.meta.url),'utf8');
  const limitDeclaration=clipperSource.match(/\bconst\s+MAX_TRIANGLES\s*=\s*(\d+)\s*;/);
  assert.ok(limitDeclaration,'Runtime must declare its clipping triangle capacity');
  const triangleCapacity=Number(limitDeclaration[1]);assert.ok(Number.isSafeInteger(triangleCapacity)&&triangleCapacity>0);
  const clipper=new CandidateCityClipper({THREE,geographicPosition:(lng,lat)=>({x:(lng-121)*90000,z:-(lat-31)*111000})});
  assert.equal(clipper.texture.image.height,triangleCapacity);assert.equal(clipper.data.length,16*triangleCapacity);
  clipper.update([...clips.values()]);assert.ok(clipper.triangleCount>0&&clipper.triangleCount<=triangleCapacity);
  catalogueChecks={existing:existing.length,new:catalogue.models.length,merged:merged.length,
    new_walk_entries:0,distinct_source_corrections:clips.size,simultaneous_clip_triangles:clipper.triangleCount,
    runtime_clip_triangle_capacity:triangleCapacity};
  clipper.dispose();
});

const bindings=['./runtime-checks.mjs','../../../src/candidate-city-integrations.js','../../../src/candidate-city-clipping.js',
  '../../../src/candidate-vector-clipping.js','../../../src/ordinary-asset-verification.js','../../../vendor/polygon-clipping.umd.min.js',
  '../../candidate-city-integrations.json','../../landmarks.json']
  .map(path=>{const data=readFileSync(new URL(path,import.meta.url));return {path,bytes:data.length,sha256:createHash('sha256').update(data).digest('hex')};});
const output={schema:'candidate-city-runtime-checks-v1',passed:checks.length,checks,catalogueChecks,bindings,
  scope:'Synthetic contract and source-preservation cases; actual city GLB rendering, network failure and browser interaction are checked separately.'};
writeFileSync(new URL('./runtime-checks.json',import.meta.url),JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify(output));
