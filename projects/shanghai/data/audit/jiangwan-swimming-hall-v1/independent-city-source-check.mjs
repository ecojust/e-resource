// Direct GLB/instance reader for this delivery's original city source only.
// This intentionally does not use GLTFLoader or the author's construction code.
import fs from 'node:fs';
import zlib from 'node:zlib';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const {MeshoptDecoder} = await import(process.env.REVIEW_MESHOPT_DECODER || new URL('../../../vendor/meshopt_decoder.module.js',import.meta.url));
await MeshoptDecoder.ready;
const [inputDirectory, outputDirectory] = process.argv.slice(2);
assert(inputDirectory && outputDirectory, 'Usage: cached-source-directory private-output-directory');
const read = name => JSON.parse(fs.readFileSync(inputDirectory+'/'+name));
const frame=read('initial-local-frame.json').anchor, macro=read('macro-READY.json');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const rad=Math.PI/180, k0=6378137*Math.cos(macro.origin_latitude*rad), k1=6371008.8*Math.cos(frame.lat*rad);
const psi0=Math.asinh(Math.tan(macro.origin_latitude*rad)), psi1=Math.asinh(Math.tan(frame.lat*rad));
const co=Math.cos(frame.heading*rad), si=Math.sin(frame.heading*rad);
const poolNear=macro.near.filter(row=>row.featureLocalIds.includes(1666));assert.equal(poolNear.length,1);const selectedOwners=new Set(poolNear[0].featureLocalIds);assert.equal(selectedOwners.size,5);
const summaries=[];
fs.mkdirSync(outputDirectory,{recursive:true});
for(const [variant,file] of [['near1666','baseline-near-1666.glb.gz'],['far','baseline-far.glb']]){
  const packed=fs.readFileSync(inputDirectory+'/'+file), bytes=file.endsWith('.gz')?zlib.gunzipSync(packed):packed;
  assert.equal(bytes.toString('ascii',0,4),'glTF');assert.equal(bytes.readUInt32LE(4),2);assert.equal(bytes.readUInt32LE(8),bytes.length);
  const size=bytes.readUInt32LE(12);assert.equal(bytes.readUInt32LE(16),0x4e4f534a);assert.equal(bytes.readUInt32LE(24+size),0x004e4942);
  const doc=JSON.parse(bytes.toString('utf8',20,20+size)),bin=bytes.subarray(28+size),cache=new Map();
  assert(doc.buffers.every(b=>!b.uri));assert.equal(doc.scenes.length,1);
  const view=id=>{
    if(cache.has(id))return cache.get(id);
    const v=doc.bufferViews[id],e=v.extensions?.EXT_meshopt_compression;let b;
    if(e){assert.equal(e.buffer,0);b=new Uint8Array(e.count*e.byteStride);MeshoptDecoder.decodeGltfBuffer(b,e.count,e.byteStride,bin.subarray(e.byteOffset||0,(e.byteOffset||0)+e.byteLength),e.mode,e.filter);}
    else{assert.equal(v.buffer,0);b=bin.subarray(v.byteOffset||0,(v.byteOffset||0)+v.byteLength);}
    cache.set(id,b);return b;
  };
  const accessor=id=>{
    const a=doc.accessors[id],v=doc.bufferViews[a.bufferView],b=view(a.bufferView);assert(!a.sparse);
    const sizes={5122:2,5123:2,5125:4,5126:4},methods={5122:'getInt16',5123:'getUint16',5125:'getUint32',5126:'getFloat32'},counts={SCALAR:1,VEC3:3,VEC4:4};
    const size=sizes[a.componentType],n=counts[a.type],stride=v.byteStride||size*n;assert(size&&n);
    const dv=new DataView(b.buffer,b.byteOffset,b.byteLength),result=[];
    for(let j=0;j<a.count;j++){
      const row=[];for(let k=0;k<n;k++){
        let x=dv[methods[a.componentType]]((a.byteOffset||0)+j*stride+k*size,true);
        if(a.normalized){assert.equal(a.componentType,5122);x=Math.max(-1,x/32767);}
        assert(Number.isFinite(x));row.push(x);
      }result.push(row);
    }return result;
  };
  // EXT_mesh_gpu_instancing is represented by Float32 instance matrices in
  // the production renderer. Reconstruct those coefficients directly.
  const instanceMatrix=(t,q,s)=>{
    const [x,y,z,w]=q,x2=2*x,y2=2*y,z2=2*z,xx=x*x2,xy=x*y2,xz=x*z2,yy=y*y2,yz=y*z2,zz=z*z2,wx=w*x2,wy=w*y2,wz=w*z2;
    return [(1-yy-zz)*s[0],(xy+wz)*s[0],(xz-wy)*s[0],(xy-wz)*s[1],(1-xx-zz)*s[1],(yz+wx)*s[1],(xz+wy)*s[2],(yz-wx)*s[2],(1-xx-yy)*s[2],...t].map(Math.fround);
  };
  const local=p=>{
    const e=k1*((macro.origin_longitude-frame.lng)*rad+p[0]/k0),n=k1*(psi0-psi1-p[2]/k0);
    return [co*e-si*n,si*e+co*n,p[1]];
  };
  let expanded=0;const flattened=[],ownerCounts={},nodes=[];
  for(const nodeId of doc.scenes[doc.scene??0].nodes){
    const node=doc.nodes[nodeId];assert(!node.children?.length&&!node.matrix&&!node.translation&&!node.rotation&&!node.scale,'This original source has identity top-level nodes; fail if that changes');
    const ext=node.extensions?.EXT_mesh_gpu_instancing,ia=ext?.attributes;
    const translations=ia?.TRANSLATION===undefined?null:accessor(ia.TRANSLATION),rotations=ia?.ROTATION===undefined?null:accessor(ia.ROTATION),scales=ia?.SCALE===undefined?null:accessor(ia.SCALE);
    const count=translations?.length||rotations?.length||scales?.length||1;
    for(const values of [translations,rotations,scales])if(values)assert.equal(values.length,count);
    nodes.push({id:nodeId,instances:count,instanceAttributeTypes:ia?Object.fromEntries(Object.entries(ia).map(([k,v])=>[k,{type:doc.accessors[v].componentType,normalized:doc.accessors[v].normalized||false}])):null});
    for(const prim of doc.meshes[node.mesh].primitives){
      assert.equal(prim.mode??4,4);const positions=accessor(prim.attributes.POSITION),indices=prim.indices===undefined?positions.map((_,i)=>i):accessor(prim.indices).map(r=>r[0]);
      const featureId=prim.attributes._FEATURE_ID_0===undefined?null:accessor(prim.attributes._FEATURE_ID_0).map(r=>r[0]);
      assert.equal(indices.length%3,0);assert.equal(Boolean(featureId),variant==='far');
      for(let inst=0;inst<count;inst++){
        const mat=ext?instanceMatrix(translations?.[inst]||[0,0,0],rotations?.[inst]||[0,0,0,1],scales?.[inst]||[1,1,1]):null;
        for(let i=0;i<indices.length;i+=3){
          expanded++;const ids=indices.slice(i,i+3);assert(ids.every(id=>id<positions.length));
          let owner=null;if(featureId){owner=featureId[ids[0]];assert(ids.every(id=>featureId[id]===owner));if(!selectedOwners.has(owner))continue;ownerCounts[owner]=(ownerCounts[owner]||0)+1;}
          for(const id of ids){const [x,y,z]=positions[id],p=mat?[mat[0]*x+mat[3]*y+mat[6]*z+mat[9],mat[1]*x+mat[4]*y+mat[7]*z+mat[10],mat[2]*x+mat[5]*y+mat[8]*z+mat[11]]:[x,y,z];flattened.push(...local(p));}
        }
      }
    }
  }
  const data=Buffer.from(new Float64Array(flattened).buffer),out=variant+'-triangles.f64';fs.writeFileSync(outputDirectory+'/'+out,data);
  summaries.push({variant,input:{file,bytes:packed.length,sha256:sha(packed),decodedBytes:bytes.length,decodedSHA256:sha(bytes)},expandedTriangles:expanded,selectedTriangles:flattened.length/9,selectedFarOwners:ownerCounts,nodes,output:{file:out,bytes:data.length,sha256:sha(data)},coordinates:'local physical Mercator metres [x along block east, y along block north, native up]. Earth radius6371008.8; original tile inverse uses6378137.'});
}
const report={schema:'jiangwan-swimming-hall-independent-original-city-decode-v1',method:'Independent direct GLB buffer/accessor and Meshopt reader; explicit signed-normalized quaternion reconstruction of every EXT_mesh_gpu_instancing matrix. No GLTFLoader, author rebuild or mapper-generated triangles.',frame,sourceDirectory:inputDirectory,variants:summaries};
fs.writeFileSync(outputDirectory+'/city-source-decode.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(summaries.map(r=>({variant:r.variant,expanded:r.expandedTriangles,selected:r.selectedTriangles,owners:r.selectedFarOwners}))));
