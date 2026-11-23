import fs from 'node:fs';
const source = fs.readFileSync(process.argv[2]);
const moduleBytes = fs.readFileSync(process.argv[4]);
const {MeshoptDecoder} = await import('data:text/javascript;base64,' + moduleBytes.toString('base64'));
await MeshoptDecoder.ready;
const jsonLength = source.readUInt32LE(12);
const scene = JSON.parse(source.subarray(20,20+jsonLength).toString());
const binary = source.subarray(28+jsonLength);
const decoded = Buffer.alloc(scene.buffers[1].byteLength);
for (const view of scene.bufferViews) {
  const ext = view.extensions.EXT_meshopt_compression;
  if (view.buffer!==1 || ext.buffer!==0 || view.byteLength!==ext.count*ext.byteStride) throw Error('Unexpected source buffer layout');
  const target = decoded.subarray(view.byteOffset||0,(view.byteOffset||0)+view.byteLength);
  const data = binary.subarray(ext.byteOffset||0,(ext.byteOffset||0)+ext.byteLength);
  MeshoptDecoder.decodeGltfBuffer(target,ext.count,ext.byteStride,data,ext.mode,ext.filter);
  view.buffer = 0;
  delete view.extensions;
}
scene.buffers = [{byteLength: decoded.length}];
for (const key of ['extensionsUsed','extensionsRequired']) scene[key] = scene[key].filter(x=>x!=='EXT_meshopt_compression');
const json = Buffer.from(JSON.stringify(scene));
const padded = (json.length+3)&~3;
const result = Buffer.alloc(28+padded+decoded.length);
result.write('glTF'); result.writeUInt32LE(2,4); result.writeUInt32LE(result.length,8);
result.writeUInt32LE(padded,12); result.write('JSON',16); result.fill(32,20,20+padded); json.copy(result,20);
result.writeUInt32LE(decoded.length,20+padded);result.write('BIN\0',24+padded);decoded.copy(result,28+padded);
fs.writeFileSync(process.argv[3],result);
