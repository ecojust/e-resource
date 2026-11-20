/* Decode the source geometry with the same MeshOptimizer WASM decoder shipped by the project. */
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const [library,input,output]=process.argv.slice(2);
const {MeshoptDecoder}=await import(pathToFileURL(path.resolve(library)));
await MeshoptDecoder.ready;
const data=await readFile(input), length=data.readUInt32LE(12);
const doc=JSON.parse(data.subarray(20,20+length)), original=data.subarray(28+length);
const buffers=[original];
let total=original.length, count=0;
for(const view of doc.bufferViews){
  const extension=view.extensions?.EXT_meshopt_compression;
  if(!extension)continue;
  assert.equal(extension.buffer,0);
  const bytes=Buffer.alloc(extension.count*extension.byteStride);
  const begin=extension.byteOffset??0;
  MeshoptDecoder.decodeGltfBuffer(bytes,extension.count,extension.byteStride,
    original.subarray(begin,begin+extension.byteLength),extension.mode,extension.filter);
  const alignment=(4-total%4)%4;
  buffers.push(Buffer.alloc(alignment),bytes);
  total+=alignment;
  view.buffer=0;view.byteOffset=total;view.byteLength=bytes.length;
  total+=bytes.length;count++;
  delete view.extensions.EXT_meshopt_compression;
  if(!Object.keys(view.extensions).length)delete view.extensions;
}
assert.ok(count>0);
doc.buffers=[{byteLength:total}];
for(const key of ['extensionsUsed','extensionsRequired']){
  if(doc[key])doc[key]=doc[key].filter(name=>name!=='EXT_meshopt_compression');
  if(doc[key]?.length===0)delete doc[key];
}
const json=Buffer.from(JSON.stringify(doc)), padding=(4-json.length%4)%4, binPadding=(4-total%4)%4;
const header=Buffer.alloc(20);header.write('glTF');header.writeUInt32LE(2,4);
header.writeUInt32LE(28+json.length+padding+total+binPadding,8);header.writeUInt32LE(json.length+padding,12);
header.writeUInt32LE(0x4e4f534a,16);
const binHeader=Buffer.alloc(8);binHeader.writeUInt32LE(total+binPadding);binHeader.writeUInt32LE(0x004e4942,4);
await writeFile(output,Buffer.concat([header,json,Buffer.alloc(padding,32),binHeader,...buffers,Buffer.alloc(binPadding)]));
console.log(input,count);
