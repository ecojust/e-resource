// Compare the actual accessor bytes in each delivered GLB, after meshopt decoding.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const decoder=fs.readFileSync(path.resolve(here,'../../../../../vendor/meshopt_decoder.module.js'));
const {MeshoptDecoder}=await import('data:text/javascript;base64,'+decoder.toString('base64'));
await MeshoptDecoder.ready;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const [prior,revised,out]=process.argv.slice(2);const report={};
function inspect(file) {
 const glb=fs.readFileSync(file);
 const len=glb.readUInt32LE(12),doc=JSON.parse(glb.subarray(20,20+len));
 const bin=glb.subarray(28+len),views=doc.bufferViews.map(v=>{
  const e=v.extensions?.EXT_meshopt_compression;
  if (!e)return bin.subarray(v.byteOffset||0,(v.byteOffset||0)+v.byteLength);
  const arr=new Uint8Array(e.count*e.byteStride);
  MeshoptDecoder.decodeGltfBuffer(arr,e.count,e.byteStride,bin.subarray(e.byteOffset||0,(e.byteOffset||0)+e.byteLength),e.mode,e.filter||'NONE');
  return Buffer.from(arr.buffer);
 });
 const records=doc.accessors.map(a=>{
  const size=({5120:1,5121:1,5122:2,5123:2,5125:4,5126:4})[a.componentType]*({SCALAR:1,VEC2:2,VEC3:3,VEC4:4})[a.type];
  const v=doc.bufferViews[a.bufferView],stride=v.byteStride||size,buf=views[a.bufferView],all=crypto.createHash('sha256');assert(size&&stride);
  if(stride===size)all.update(buf.subarray(a.byteOffset||0,(a.byteOffset||0)+size*a.count));
  else for(let i=0;i<a.count;i++){const off=(a.byteOffset||0)+i*stride;all.update(buf.subarray(off,off+size));}
  return [a.type,a.componentType,a.count,all.digest('hex')];
 });
 const tris=doc.meshes.flatMap(m=>m.primitives.map(v=>doc.accessors[v.indices].count/3));
 return {doc,records,tris,sha:sha(glb),bytes:glb.length,bin,images:(doc.images||[]).map(v=>sha(views[v.bufferView]))};
}
for(const role of ['raw','web','lod']){
 const a=inspect(path.join(prior,role+'.glb'));const b=inspect(path.join(revised,role+'.glb'));
 assert.deepEqual(b.records.slice(0,a.records.length),a.records);
 assert(a.bin.equals(b.bin.subarray(0,a.bin.length)));
 for(const k of ['meshes','nodes','materials','bufferViews','accessors'])assert.deepEqual(b.doc[k].slice(0,a.doc[k].length),a.doc[k]);
 for(const k of ['images','textures','samplers'])assert.deepEqual(b.doc[k],a.doc[k]);
 assert.deepEqual(a.images,b.images);assert.deepEqual(b.tris.slice(0,a.tris.length),a.tris);
 if(role!=='lod')assert.deepEqual(b.images,['b768d0cf0099d3443b8d52b40830f3c983c96be846eea6e4e58a13e0844fe5d9']);
 const apertureMat=a.doc.materials.findIndex(v=>v.name==='PhotoFacade_Bund14Glass');assert(apertureMat>=0);
 const sum=v=>v.reduce((x,y)=>x+y,0);const add=b.tris.slice(a.tris.length);
 report[role]={old_triangles:sum(a.tris),triangles:sum(b.tris),added_triangles:sum(add),added_parts:b.doc.nodes.slice(a.doc.nodes.length).map((n,i)=>[n.name,add[i]]),source_accessor_digest:sha(JSON.stringify(a.records)),unchanged_original_accessors:a.records.length,unchanged_original_binary_sha256:sha(a.bin),unchanged_embedded_images:b.images,original_materials:a.doc.materials.length,sha256:b.sha,bytes:b.bytes,draw_primitives:b.tris.length};
}
fs.writeFileSync(out,JSON.stringify({passed:true,decoder_sha256:sha(decoder),variants:report},null,2)+'\n');
