// Expand a GLB's actual Meshopt buffer views for independent geometry checking.
import fs from 'node:fs';
import {MeshoptDecoder} from '../../../../vendor/meshopt_decoder.module.js';
await MeshoptDecoder.ready;
const [input,output]=process.argv.slice(2);
const raw=fs.readFileSync(input);const length=raw.readUInt32LE(12);const doc=JSON.parse(raw.subarray(20,20+length));
const binary=raw.subarray(28+length);const chunks=[];let offset=0;
for(const view of doc.bufferViews){
 const ext=view.extensions?.EXT_meshopt_compression;let bytes;
 if(ext){
  bytes=new Uint8Array(ext.count*ext.byteStride);
  MeshoptDecoder.decodeGltfBuffer(bytes,ext.count,ext.byteStride,binary.subarray(ext.byteOffset||0,(ext.byteOffset||0)+ext.byteLength),ext.mode,ext.filter||'NONE');
 }else bytes=binary.subarray(view.byteOffset||0,(view.byteOffset||0)+view.byteLength);
 const padding=(4-offset%4)%4;if(padding){chunks.push(Buffer.alloc(padding));offset+=padding;}
 view.buffer=0;view.byteOffset=offset;view.byteLength=bytes.length;delete view.extensions;
 chunks.push(Buffer.from(bytes));offset+=bytes.length;
}
const padding=(4-offset%4)%4;if(padding){chunks.push(Buffer.alloc(padding));offset+=padding;}
doc.buffers=[{byteLength:offset}];for(const key of ['extensionsUsed','extensionsRequired'])if(doc[key])doc[key]=doc[key].filter(x=>x!=='EXT_meshopt_compression');
let json=Buffer.from(JSON.stringify(doc));json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);
const head=Buffer.alloc(20);head.write('glTF');head.writeUInt32LE(2,4);head.writeUInt32LE(28+json.length+offset,8);head.writeUInt32LE(json.length,12);head.writeUInt32LE(0x4e4f534a,16);
const binHead=Buffer.alloc(8);binHead.writeUInt32LE(offset);binHead.writeUInt32LE(0x004e4942,4);fs.writeFileSync(output,Buffer.concat([head,json,binHead,...chunks]));
console.log(JSON.stringify({output,bytes:28+json.length+offset,views:doc.bufferViews.length}));
