/** Small deterministic GLB with actual floating-point geometry, no external assets. */
export function triangleGLB() {
 const binary=new Uint8Array(80);
 new Float32Array(binary.buffer,0,9).set([0.123456789,0,0,1.123456789,0,0,0.123456789,1,0]);
 new Float32Array(binary.buffer,36,9).set([0,0,1,0,0,1,0,0,1]);
 new Uint16Array(binary.buffer,72,3).set([0,1,2]);
 const document={asset:{version:'2.0',generator:'deterministic city codec fixture'},scene:0,scenes:[{nodes:[0]}],nodes:[{mesh:0}],
  meshes:[{primitives:[{attributes:{POSITION:0,NORMAL:1},indices:2,material:0}]}],materials:[{name:'InferredPlaster',pbrMetallicRoughness:{baseColorFactor:[.4,.4,.4,1],metallicFactor:0,roughnessFactor:.9}}],
  buffers:[{byteLength:80}],bufferViews:[{buffer:0,byteOffset:0,byteLength:36},{buffer:0,byteOffset:36,byteLength:36},{buffer:0,byteOffset:72,byteLength:6}],
  accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3',min:[.123456789,0,0],max:[1.123456789,1,0]},{bufferView:1,componentType:5126,count:3,type:'VEC3'},{bufferView:2,componentType:5123,count:3,type:'SCALAR'}]};
 const text=new TextEncoder().encode(JSON.stringify(document)),jsonSize=Math.ceil(text.length/4)*4;
 const output=new Uint8Array(12+8+jsonSize+8+binary.length),view=new DataView(output.buffer);
 view.setUint32(0,0x46546c67,true);view.setUint32(4,2,true);view.setUint32(8,output.length,true);
 view.setUint32(12,jsonSize,true);view.setUint32(16,0x4e4f534a,true);output.fill(32,20,20+jsonSize);output.set(text,20);
 view.setUint32(20+jsonSize,binary.length,true);view.setUint32(24+jsonSize,0x004e4942,true);output.set(binary,28+jsonSize);
 return output;
}
