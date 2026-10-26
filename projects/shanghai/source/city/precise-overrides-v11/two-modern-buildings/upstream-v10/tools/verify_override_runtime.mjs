/** Actual decoded far/near owner lifecycle, no WebGL/browser or baseline writes. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
const [project,manifestPath]=process.argv.slice(2);
assert(project&&manifestPath,'Usage: node verify_override_runtime.mjs PROJECT CANDIDATE_MANIFEST');
const manifest=JSON.parse(await fs.readFile(manifestPath));assert(manifest.complete,'Geometry audit must pass first');
const evidence=JSON.parse(await fs.readFile(path.join(path.dirname(manifestPath),'geometry-comparison-input.json')));
const modelPaths=new Map(evidence.checks.map(c=>[c.id,c.override]));
const url=p=>pathToFileURL(path.join(project,p)).href;
const hooks=registerHooks({resolve(s,c,next){return s==='three'?{url:url('vendor/three.module.js'),shortCircuit:true}:next(s,c);}});
const {GLTFLoader}=await import(url('vendor/GLTFLoader.js'));hooks.deregister();
const THREE=await import(url('vendor/three.module.js'));
const {MeshoptDecoder}=await import(url('vendor/meshopt_decoder.module.js'));
const {CityDetailStreamer}=await import(url('src/city-detail-streamer.js'));
const {disposeModelResources,countExpandedTriangles}=await import(url('src/model-resources.js'));
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder),sha=b=>createHash('sha256').update(b).digest('hex');
async function load(file,expected){let b=await fs.readFile(file);assert.equal(sha(b),expected);if(file.endsWith('.gz'))b=gunzipSync(b);return (await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;}
const report={schema:'city-precise-runtime-owner-audit-v2',pass:false,registry_sha256:sha(await fs.readFile(manifestPath)),checks:[]};
for(const macro of manifest.macros){
 const scene=new THREE.Scene(),errors=[],directory=path.join(project,'assets/city-detail/macros',macro.id),ready=await fs.readFile(path.join(directory,'READY.json'));
 const streamer=new CityDetailStreamer({THREE,scene,loader,prepareObject(){},disposeObject(o){scene.remove(o);disposeModelResources(o)},onError:e=>errors.push(e.message),fetchFunction:async()=>new Response(ready)});
 streamer.setReplacementOverrides(manifest,'https://fixture.invalid/project/');
 const far=await load(path.join(directory,'far.glb'),macro.baseline_far_sha256),identities=[...new Set(macro.near.flatMap(n=>n.groups.map(g=>g.landmark_id)))];
 streamer.setVisibleLandmarks(identities);
 streamer.prepareFarObject(far,{id:macro.id,buildingCount:macro.feature_count,sha256:macro.baseline_far_sha256,detailURL:'https://fixture.invalid/city/'+macro.id+'/READY.json'});
 const parent=streamer.parents.get(far),targets=new Map(macro.near.flatMap(n=>n.groups.flatMap(g=>g.local_ids.map(id=>[id,g.landmark_id]))));
 for(let id=1;id<=macro.feature_count;id++)assert.equal(parent.mask.references[id],targets.has(id)?1:0,'Precise ownership must exist before near loading');
 parent.active=true;await streamer.loadIndex(parent);assert.deepEqual(errors,[]);
 const near=[];
 for(const item of macro.near){
  const record=parent.records.find(r=>r.replacement?.id===item.id);assert(record);
  const object=await load(modelPaths.get(item.id),item.model.sha256);streamer.bindReplacementGroups(object,record);
  record.object=object;object.visible=false;scene.add(object);streamer.wanted.add(record);streamer.show(record);near.push(record);
 }
 const states=[...identities.map(id=>[id]),identities,[]];
 for(const active of states){
  streamer.setVisibleLandmarks(active);
  const nearCounts=new Map();for(const r of near)for(const id of r.ids)nearCounts.set(id,(nearCounts.get(id)||0)+1);
  for(let id=1;id<=macro.feature_count;id++)assert.equal(parent.mask.references[id],(nearCounts.get(id)||0)+(active.includes(targets.get(id))?1:0));
  for(const record of near){
   for(const group of record.replacementGroups)assert.equal(group.object.visible,!active.includes(group.landmark));
   const kept=record.object.getObjectByName('preserved_neighbors');if(kept)assert.equal(kept.visible,true,'A precise owner cannot hide neighbors');
  }
 }
 const summary={macro:macro.id,feature_count:macro.feature_count,target_ids:identities,near:near.map(r=>({id:r.id,features:r.ids.length,triangles:countExpandedTriangles(r.object),groups:r.replacementGroups.map(g=>g.landmark)})),independent_visibility_states:states.length};
 streamer.setVisibleLandmarks(identities);for(const r of near)streamer.hide(r);
 for(let id=1;id<=macro.feature_count;id++)assert.equal(parent.mask.references[id],targets.has(id)?1:0,'Near eviction must retain precise owners only');
 streamer.setVisibleLandmarks([]);assert(parent.mask.data.every(v=>v===0));assert(parent.mask.references.every(v=>v===0));
 const mask=parent.mask;streamer.destroy();assert(mask.disposed);disposeModelResources(far);assert.deepEqual(errors,[]);
 summary.pass=true;report.checks.push(summary);
}
report.pass=true;
await fs.writeFile(path.join(path.dirname(manifestPath),'runtime-owner-validation.json'),JSON.stringify(report,null,2)+'\n');
console.log('PASS: actual far + candidate near models; each target independent, all neighbors retained, eviction/restoration/destroy checked');
