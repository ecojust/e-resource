import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';

const root=process.argv[2];
const site=process.argv[3];
const base=process.argv[4];
const target=process.argv[5];
if(!target) throw Error('Usage: node check-model-masks.mjs PROJECT INSTALLED_PROJECT EVIDENCE OUTPUT.json');
const sha=b=>createHash('sha256').update(b).digest('hex');
const load=(f)=>JSON.parse(fs.readFileSync(f,'utf8'));
const route=p=>pathToFileURL(path.join(root,p)).href;
registerHooks({resolve(specifier,context,next){if(specifier==='three')return {shortCircuit:true,url:route('vendor/three.module.js')};return next(specifier,context)}});
const THREE=await import(route('vendor/three.module.js'));
const {GLTFLoader}=await import(route('vendor/GLTFLoader.js'));
const {MeshoptDecoder}=await import(route('vendor/meshopt_decoder.module.js'));
const {CityDetailStreamer}=await import(route('src/city-detail-streamer.js'));
const {countExpandedTriangles}=await import(route('src/model-resources.js'));
const {OrdinaryCityDetailStreamer}=await import(route('src/ordinary-city-detail-streamer.js'));
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const parentURL='https://example.invalid/project/'; // All buffers are read from the installed project.
const s=load(path.join(base,'public-baseline.json'));
const reg=load(path.join(site,'data/precise-buildings/macros/'+s.macro_id+'/replacement.json'));
const descriptor=reg.macros[0].near.find(item=>item.id===s.ordinary_near.id);
const id=descriptor.groups[0].landmark_id;
async function parse(buffer){return (await loader.parseAsync(buffer.buffer.slice(buffer.byteOffset,buffer.byteOffset+buffer.byteLength),parentURL)).scene}
const raw=fs.readFileSync(path.join(site,descriptor.model.file));assert.equal(sha(raw),descriptor.model.sha256);
const near=await parse(gunzipSync(raw));
const originPrefix='assets/city-detail/macros/'+s.macro_id+'/';
const farFile=fs.readFileSync(path.join(root,originPrefix,s.ordinary_far.file));
assert.equal(sha(farFile),s.ordinary_far.sha256);
const far=await parse(farFile);
const scene=new THREE.Scene();scene.add(far);scene.add(near);
const streamer=new OrdinaryCityDetailStreamer({THREE,scene,loader,prepareObject:()=>{},disposeObject:()=>{}});
const manifest=load(path.join(site,'data/precise-buildings-v6.json'));
streamer.setReplacementOverrides(manifest,parentURL);
streamer.prepareFarObject(far,{id:s.macro_id,sha256:s.ordinary_far.sha256,buildingCount:5695,detailURL:parentURL+originPrefix+'READY.json'});
const parent=streamer.parents.get(far);assert.ok(parent);
const record={replacement:descriptor,parent,declaredTriangles:descriptor.model.expandedTriangles,object:near};
streamer.bindReplacementGroups(near,record);parent.records.push(record);
const object=record.replacementGroups[0].object, neighbors=near.getObjectByName('city_preserved_neighbors');
assert.ok(neighbors);assert.equal(countExpandedTriangles(near),72038);assert.equal(countExpandedTriangles(object),4120);assert.equal(countExpandedTriangles(neighbors),67918);
const farOwners=new Map();let shaderTests=0;
far.traverse(mesh=>{
  if(!mesh.isMesh)return;
  const geo=mesh.geometry,attr=geo.getAttribute('_feature_id_0'),inds=geo.index;
  for(let i=0;i<(inds?inds.count:attr.count);i+=3){
    const value=attr.getX(inds?inds.getX(i):i);farOwners.set(value,1+(farOwners.get(value)||0));
  }
  for(const m of [...(Array.isArray(mesh.material)?mesh.material:[mesh.material]),mesh.customDepthMaterial,mesh.customDistanceMaterial]){
    assert.ok(m);const sh={uniforms:{},vertexShader:'#include <common>\nvoid main(){\n#include <begin_vertex>\n}',fragmentShader:'#include <common>\nvoid main() {}'};
    m.onBeforeCompile(sh,{});assert.match(sh.fragmentShader,/discard/);assert.equal(sh.uniforms.cityFeatureMask.value,parent.mask.texture);shaderTests++;
  }
});
assert.ok(farOwners.get(3304)>0);assert.equal([...farOwners.values()].reduce((a,b)=>a+b),s.ordinary_far.triangles);
let samples=[];
for(const [phase,ids] of [['load',[]],['visible full',[id]],['visible distant',[id]],['detached',[]]]){
  streamer.setVisibleLandmarks(ids);assert.equal(Boolean(parent.mask.data[3304]),Boolean(ids.length));assert.equal(object.visible,!ids.length);assert.equal(neighbors.visible,true);
  assert.deepEqual([...parent.mask.references].flatMap((v,i)=>v?[i]:[]),ids.length?[3304]:[]);
  for(const n of s.remain_near_local_ids)assert.equal(parent.mask.data[n],0);
  samples.push({phase,masked:ids.length?[3304]:[],near_target_visible:object.visible,near_neighbors_visible:neighbors.visible,neighbor_count:s.remain_near_local_ids.length});
}
const output={source:farFile.length,near_source_sha256:s.ordinary_near.sha256,near_variant_sha256:descriptor.model.sha256,far_source_sha256:sha(farFile),far_triangles:s.ordinary_far.triangles,far_owner_triangles:farOwners.get(3304),far_retained_triangles:s.ordinary_far.triangles-farOwners.get(3304),near_triangles:72038,near_owner_triangles:4120,near_retained_triangles:67918,far_feature_ids:farOwners.size,color_depth_and_distance_material_hooks:shaderTests,states:samples};
const next=target;fs.writeFileSync(next,JSON.stringify(output,null,2)+'\n');console.log(JSON.stringify(output));
