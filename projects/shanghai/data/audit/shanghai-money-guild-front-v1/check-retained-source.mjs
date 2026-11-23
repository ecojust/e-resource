// Test the door recess, projecting piers, original host and public pavement at both city-model detail levels.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';

const audit=path.dirname(fileURLToPath(import.meta.url)),project=path.resolve(audit,'../../..');
const runtime=process.env.SHANGHAI_PROJECT_ROOT||project;
const read=file=>JSON.parse(fs.readFileSync(file));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const load=file=>import(pathToFileURL(path.join(runtime,file)));
const THREE=await load('vendor/three.module.js');
const {CandidateCityClipper}=await load('src/candidate-city-clipping.js');
const {mergeCandidateCityModels,CandidateCityState,candidateGeometryContains}=await load('src/candidate-city-integrations.js');
const {markVerifiedOrdinaryAsset}=await load('src/ordinary-asset-verification.js');
const contract=read(path.join(audit,'final-placement-contract.json'));
const measured=read(path.join(audit,'map-case.json'));
const folder='assets/models/candidates/'+contract.id+'/';
const manifest=read(path.join(project,folder,'manifest.json'));
const catalogFile=path.join(runtime,'data/candidate-city-integrations.json');
const catalog=read(catalogFile);
const registered=catalog.models.find(row=>row.id===contract.id);
assert.ok(registered||process.argv.includes('--preflight'));
const assets=Object.fromEntries(['web','lod'].map((role,i)=>{
 const entry=manifest.assets[['full','lod'][i]],file=folder+entry.file,b=fs.readFileSync(path.join(project,file));
 assert.equal(hash(b),entry.sha256);assert.equal(b.length,entry.bytes);
 return [role,{...entry,file}];
}));
const target=registered||{...contract,kind:'building',name:manifest.name,height_m:contract.bounds_glb.max[1],assets};
assert.equal(target.replacement_geometry,null);
assert.equal(target.site_replacement,undefined);
assert.deepEqual(target.source_feature_ids,{building:[],building_part:[]});
assert.deepEqual(target.owner,contract.owner);
assert.deepEqual(target.collision_geometry,contract.collision_geometry);
const [door]=mergeCandidateCityModels([],{schema:'candidate-city-integrations-v1',models:[target]});
const scene=new THREE.Scene(),entry=new Map([[door.id,door]]);
const state=new CandidateCityState({getRecords:()=>entry,getScene:()=>scene});
const rad=Math.PI/180,k=6371008.8*Math.cos(target.lat*rad),h=target.heading*rad,ml=Math.asinh(Math.tan(target.lat*rad));
function toWGS(x,y){
 const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
 return [target.lng+east/(k*rad),Math.atan(Math.sinh(ml+north/k))/rad];
}
const reports={};
for(const [role,variant] of [['web','full'],['lod','distant']]){
 door.object=new THREE.Group();door.status='loaded';door.activeVariant=variant;scene.add(door.object);
 markVerifiedOrdinaryAsset(door.object,{modelId:door.id,variant:role,asset:assets[role]});state.sync();
 assert.equal(state.active.length,1);assert.deepEqual(state.clips,[]);assert.deepEqual(state.displayClips,[]);
 const gpu=new CandidateCityClipper({THREE,geographicPosition:()=>new THREE.Vector3()});
 gpu.update(state.displayClips);assert.equal(gpu.getState().triangles,0);gpu.dispose();
 const [floor]=state.collisions();
 const probes=measured.ground.map(p=>{
  const point=toWGS(...p.xy);
  assert.ok(Math.hypot(point[0]-p.wgs84[0],point[1]-p.wgs84[1])<1e-8);
  const occupied=candidateGeometryContains(floor.geometry,point);
  assert.equal(occupied,p.modelObstacle,p.name);
  for(const source of ['overture-buildings','openmaptiles']){
   for(const owner of [182,378,...p.original_native]){
    assert.equal(state.clipsPoint(...point,{name:source,layer:'building',id:owner}),false);
   }
  }
  return {...p,candidate_occupied:occupied};
 });
 assert.equal(probes.filter(p=>p.candidate_occupied && !p.before_near).length,measured.new_model_only_probe_count);
 assert.equal(probes.length,227);
 door.object.visible=false;state.sync();assert.deepEqual(state.collisions(),[]);
 assert.deepEqual(state.displayClips,[]);scene.remove(door.object);
 reports[role]={sha256:assets[role].sha256,triangles:assets[role].triangles,source_clip_triangles:0,probes};
}
fs.writeFileSync(process.argv[2],JSON.stringify({id:target.id,preflight:!registered,catalog_count:catalog.resulting_city_count,
 catalog_sha256:hash(fs.readFileSync(catalogFile)),checker_sha256:hash(fs.readFileSync(fileURLToPath(import.meta.url))),
 clipping_module_sha256:hash(fs.readFileSync(path.join(runtime,'src/candidate-city-clipping.js'))),reports},null,2)+'\n');
