/** Decode a GLB's meshopt buffer views for independent FLOAT32 surface checks.
 * The decoder is supplied explicitly; it is not bundled into the model source.
 */
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const [input,output,decoderPath]=process.argv.slice(2);
if(!input||!output||!decoderPath)throw new Error('usage: node decode_meshopt.mjs in.glb out.glb /path/to/meshopt_decoder.module.js');
const {MeshoptDecoder}=await import(pathToFileURL(decoderPath));await MeshoptDecoder.ready;
const data=fs.readFileSync(input);const size=data.readUInt32LE(12);const doc=JSON.parse(data.subarray(20,20+size));const source=data.subarray(28+size);let length=0;const chunks=[];
for(const view of doc.bufferViews){
 let bytes;const ext=view.extensions?.EXT_meshopt_compression;
 if(ext){bytes=new Uint8Array(ext.count*ext.byteStride);MeshoptDecoder.decodeGltfBuffer(bytes,ext.count,ext.byteStride,source.subarray(ext.byteOffset,ext.byteOffset+ext.byteLength),ext.mode,ext.filter);delete view.extensions.EXT_meshopt_compression;if(!Object.keys(view.extensions).length)delete view.extensions;}
 else bytes=source.subarray(view.byteOffset||0,(view.byteOffset||0)+view.byteLength);
 const pad=(4-length%4)%4;if(pad){chunks.push(Buffer.alloc(pad));length+=pad;}view.buffer=0;view.byteOffset=length;view.byteLength=bytes.byteLength;chunks.push(Buffer.from(bytes));length+=bytes.byteLength;
}
for(const key of ['extensionsUsed','extensionsRequired']){if(doc[key]){doc[key]=doc[key].filter(n=>n!=='EXT_meshopt_compression');if(!doc[key].length)delete doc[key];}}
doc.buffers=[{byteLength:length}];let json=Buffer.from(JSON.stringify(doc));json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);let binary=Buffer.concat(chunks);binary=Buffer.concat([binary,Buffer.alloc((4-binary.length%4)%4)]);const head=Buffer.alloc(20);head.write('glTF');head.writeUInt32LE(2,4);head.writeUInt32LE(28+json.length+binary.length,8);head.writeUInt32LE(json.length,12);head.writeUInt32LE(0x4e4f534a,16);const bh=Buffer.alloc(8);bh.writeUInt32LE(binary.length,0);bh.writeUInt32LE(0x004e4942,4);fs.writeFileSync(output,Buffer.concat([head,json,bh,binary]));console.log(JSON.stringify({input,output,decoded_bytes:binary.length}));
