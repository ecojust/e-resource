import { registerHooks } from 'node:module';
import { pathToFileURL } from 'node:url';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const [project,assetDir]=process.argv.slice(2);
registerHooks({resolve(name,context,next) {
  return name==='three'?{url:pathToFileURL(path.join(project,'vendor/three.module.js')).href,shortCircuit:true}:next(name,context);
}});
globalThis.self=globalThis;
const { spawnSync } = await import('node:child_process');
globalThis.createImageBitmap=async function(blob) {
  const file=Buffer.from(await blob.arrayBuffer());
  const result=spawnSync('python',['-c','import sys,io,json; from PIL import Image; im=Image.open(io.BytesIO(sys.stdin.buffer.read())).convert("RGB"); im.load(); print(json.dumps(im.size))'],{input:file,encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);
  const [width,height]=JSON.parse(result.stdout);
  return {width,height,close(){}};
};
const {GLTFLoader}=await import(pathToFileURL(path.join(project,'vendor/GLTFLoader.js')));
const {MeshoptDecoder}=await import(pathToFileURL(path.join(project,'vendor/meshopt_decoder.module.js')));
const T=await import(pathToFileURL(path.join(project,'vendor/three.module.js')));
const loader=new GLTFLoader();loader.setMeshoptDecoder(MeshoptDecoder);
const manifest=JSON.parse(await fs.readFile(path.join(assetDir,'manifest.json'))),results={};
for (const [role,asset] of Object.entries(manifest.assets)) {
  const bytes=await fs.readFile(path.join(assetDir,asset.file));
  const scene=(await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'' )).scene;
  const textured=new Set();const material=new Set();let triangles=0,meshcount=0;
  scene.traverse(obj=>{if(obj.isMesh) {++meshcount;triangles+=(obj.geometry.index?.count??obj.geometry.attributes.position.count)/3;material.add(obj.material.name);if(obj.material.map){assert(obj.material.map.image.width>1);assert(obj.geometry.attributes.uv);textured.add(obj.material.name);}}});
  assert.equal(triangles,asset.triangles);assert.equal(textured.size,3);
  const box=new T.Box3().setFromObject(scene);
  results[role]={meshes:meshcount,triangles,materials:material.size,loaded_texture_materials:[...textured],bounds:[box.min.toArray(),box.max.toArray()]};
}
process.stdout.write(JSON.stringify({passed:true,results},null,2)+'\n');
