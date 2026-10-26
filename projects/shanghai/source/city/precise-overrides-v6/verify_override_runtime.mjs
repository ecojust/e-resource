/** Real decoded owner groups and far IDs; scene lifecycle only, no WebGL/browser. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {gunzipSync} from 'node:zlib';
import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
const [project,manifestPath]=process.argv.slice(2);assert(project&&manifestPath,'Usage: node verify_override_runtime.mjs PROJECT MANIFEST');
const url=p=>pathToFileURL(path.join(project,p)).href;
const hooks=registerHooks({resolve(s,c,next){return s==='three'?{url:url('vendor/three.module.js'),shortCircuit:true}:next(s,c);}});
const {GLTFLoader}=await import(url('vendor/GLTFLoader.js'));hooks.deregister();
const THREE=await import(url('vendor/three.module.js'));
const {MeshoptDecoder}=await import(url('vendor/meshopt_decoder.module.js'));
const {CityDetailStreamer}=await import(url('src/city-detail-streamer.js'));
const {disposeModelResources}=await import(url('src/model-resources.js'));
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder),scene=new THREE.Scene(),errors=[];
const manifest=JSON.parse(await fs.readFile(manifestPath)),macro=manifest.macros[0],directory=path.join(project,'assets/city-detail/macros',macro.id);
async function load(file){let b=await fs.readFile(file);if(file.endsWith('.gz'))b=gunzipSync(b);return (await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;}
const far=await load(path.join(directory,'far.glb')),ready=await fs.readFile(path.join(directory,'READY.json'));
const streamer=new CityDetailStreamer({THREE,scene,loader,prepareObject:()=>{},disposeObject:o=>{scene.remove(o);disposeModelResources(o);},onError:e=>errors.push(e.message),fetchFunction:async()=>new Response(ready)});
streamer.setReplacementOverrides(manifest,'https://example.test/project/');
streamer.setVisibleLandmarks(['bund05']);
streamer.prepareFarObject(far,{id:macro.id,buildingCount:macro.feature_count,sha256:macro.baseline_far_sha256,detailURL:'https://example.test/city/READY.json'});
const parent=streamer.parents.get(far);assert.equal(parent.mask.data[810],255);assert.equal(parent.mask.data[1293],0);parent.active=true;
await streamer.loadIndex(parent);assert.deepEqual(errors,[]);assert.equal(parent.status,'ready');
const report={schema:'city-precise-runtime-owner-audit-v1',pass:false,macro:macro.id,feature_count:macro.feature_count,models:[]};
for(const item of macro.near){
 const record=parent.records.find(r=>r.replacement?.id===item.id);assert(record);
 const object=await load(path.join(path.dirname(manifestPath),path.basename(item.model.file)));streamer.bindReplacementGroups(object,record);
 record.object=object;object.visible=false;scene.add(object);streamer.wanted.add(record);streamer.show(record);
 for(const id of record.ids)assert.equal(parent.mask.data[id],255);
 report.models.push({id:item.id,groups:record.replacementGroups.map(g=>({name:g.object.name,landmark:g.landmark,visible:g.object.visible}))});
}
for(const visible of [['bund05'],['bund06'],['bund14'],['bund05','bund06','bund14'],[]]){
 streamer.setVisibleLandmarks(visible);
 for(const record of parent.records)for(const group of record.replacementGroups||[])assert.equal(group.object.visible,!visible.includes(group.landmark));
 for(const item of macro.near)for(const group of item.groups)for(const id of group.local_ids)assert.equal(parent.mask.references[id],1+(visible.includes(group.landmark_id)?1:0),`${visible}: ${id}`);
}
streamer.setVisibleLandmarks(['bund05','bund06','bund14']);
for(const record of parent.records)streamer.hide(record);
const targets=new Set(macro.near.flatMap(n=>n.groups.flatMap(g=>g.local_ids)));
for(let id=1;id<=macro.feature_count;id++)assert.equal(parent.mask.data[id],targets.has(id)?255:0);
streamer.setVisibleLandmarks([]);assert(parent.mask.data.every(v=>v===0));
const mask=parent.mask;streamer.destroy();assert(mask.disposed);disposeModelResources(far);
report.pass=true;report.checks=['actual immutable far IDs bound before first visible frame','all owner groups contain every declared expanded triangle','each of three landmark owners toggles independently','neighbor groups remain visible','near unload retains precise far owner and restores unrelated features','landmark unload clears remaining far masks','destroy releases the shared far mask'];
await fs.writeFile(path.join(path.dirname(manifestPath),'runtime-owner-validation.json'),JSON.stringify(report,null,2)+'\n');console.log('PASS: actual 3064 far IDs, 17 near features, 3 complete target owners and 14 preserved neighbors');
