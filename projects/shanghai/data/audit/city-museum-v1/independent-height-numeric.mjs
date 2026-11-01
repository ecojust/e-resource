// Preparation artifact: execute only after explicit parent/Root GO.
// Independent source decoder and binary32 error bounds. No GLTFLoader/THREE imports.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {pathToFileURL,fileURLToPath} from 'node:url';

assert.equal(process.argv[2], '--go', 'PREPARED ONLY: explicit parent/Root GO is required before running.');
const [exportName, outputName] = process.argv.slice(3);
assert(exportName && outputName, 'Usage after GO: --go runtime-numeric-export.json output.json');
const exportPath=path.resolve(exportName), base=path.dirname(exportPath);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const resolve=p=>path.resolve(base,p);
const readJSON=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const binding=p=>{p=path.resolve(p);const b=fs.readFileSync(p);return {file:p,bytes:b.length,sha256:sha(b)};};
const exportBytes=fs.readFileSync(exportPath), cfg=JSON.parse(exportBytes);
assert.equal(cfg.schema,'city-museum-height-runtime-numeric-export-v1');
const inputs=[{file:exportPath,bytes:exportBytes.length,sha256:sha(exportBytes)}];
function bound(record){
  assert(record&&typeof record.file==='string'&&/^[a-f0-9]{64}$/.test(record.sha256));
  const p=resolve(record.file),b=fs.readFileSync(p);
  assert.equal(b.length,record.bytes,p+' bytes');assert.equal(sha(b),record.sha256,p+' SHA');
  inputs.push({file:p,bytes:b.length,sha256:sha(b)});return b;
}
const spec=JSON.parse(bound(cfg.preflight));
assert.equal(spec.candidate_id,'yangpu-former-shanghai-city-museum');
assert.equal(spec.display_height_clips.length,2);
const runtime=JSON.parse(bound(cfg.runtime_report));
assert.equal(runtime.schema,'city-museum-height-clipping-runtime-v1');assert(runtime.passed);
assert.equal(runtime.total_rows,262);assert.equal(runtime.preflight_sha256,cfg.preflight.sha256);
assert.equal(runtime.data_payload.sha256,cfg.rows.sha256);assert.equal(runtime.data_payload.bytes,cfg.rows.bytes);
const rowBytes=bound(cfg.rows);
assert.equal(cfg.rows.count,262);assert.equal(cfg.rows.stride,16);assert.equal(cfg.rows.byte_order,'little-endian');
assert.equal(rowBytes.length,262*16*4);
const rows=Array.from({length:262},(_,i)=>Array.from({length:16},(_,j)=>rowBytes.readFloatLE((i*16+j)*4)));
assert(rows.flat().every(Number.isFinite));
for(let i=0;i<258;i++)assert.deepEqual(rows[i].slice(6,8),[-100,1000],'Old default slab changed');
assert.equal(cfg.added_row_ranges.length,2);
assert.deepEqual(cfg.added_row_ranges.map(r=>[r.first,r.count]),[[258,2],[260,2]]);
assert.deepEqual(cfg.added_row_ranges.map(r=>r.id),spec.display_height_clips.map(c=>c.id));
assert.deepEqual(runtime.height_clip_ids,spec.display_height_clips.map(c=>c.id));
assert.deepEqual(rows.slice(258),runtime.rows);
assert.equal(sha(rowBytes.subarray(0,218*64)),runtime.data_payload.old218_prefix_sha256);
assert.equal(sha(rowBytes.subarray(0,258*64)),runtime.data_payload.base258_prefix_sha256);
for(const r of cfg.bindings||[])bound(r);
const clippingBinding=(cfg.bindings||[]).find(r=>r.file.endsWith('/candidate-city-clipping.js'));
assert(clippingBinding,'Bind the actual frozen candidate-city-clipping.js');
const shaderSource=fs.readFileSync(resolve(clippingBinding.file),'utf8');
for(const token of ['candidatePosition=instanceMatrix*candidatePosition','vCandidatePosition=(modelMatrix*candidatePosition).xyz',
  'if(p.x<box.x||p.y<box.y||p.x>box.z||p.y>box.w)continue;',
  'if(vCandidatePosition.y<cy.z||vCandidatePosition.y>cy.w)continue;',
  '(a>=-0.001&&b>=-0.001&&c>=-0.001)||(a<=0.001&&b<=0.001&&c<=0.001)'])assert(shaderSource.includes(token),'Shader changed: '+token);

const sourceDir=resolve(cfg.source_directory), receiptPath=resolve(cfg.decode_receipt), cachePath=resolve(cfg.cached_triangles);
const receipt=readJSON(receiptPath), prior=receipt.variants.find(v=>v.variant==='near1860');
assert.equal(prior.expandedTriangles,122780);assert.equal(prior.selectedTriangles,122780);
const packed=fs.readFileSync(path.join(sourceDir,prior.input.file));
assert.equal(packed.length,66904);assert.equal(sha(packed),'f313d6472b3bbfb3384dd9472f298664134f9347b3cca82acc7df78ba9e08a3c');
assert.equal(sha(packed),prior.input.sha256);
const bytes=zlib.gunzipSync(packed);assert.equal(sha(bytes),prior.input.decodedSHA256);
const cache=fs.readFileSync(cachePath);assert.equal(cache.length,122780*9*8);assert.equal(sha(cache),prior.output.sha256);
const possibleOwner=cfg.possible_owner_indices?JSON.parse(bound(cfg.possible_owner_indices)):null;
let owner1262=null;
if(possibleOwner){
  assert.equal(possibleOwner.original_near_payload_sha256,sha(cache));
  const indices=possibleOwner.indices['1262'];assert(Array.isArray(indices)&&indices.length===7314);
  assert(indices.every(i=>Number.isInteger(i)&&i>=0&&i<122780));owner1262=new Set(indices);assert.equal(owner1262.size,7314);
}
const macroPath=path.join(sourceDir,'macro-READY.json'),framePath=path.join(sourceDir,'initial-local-frame.json');
const macro=readJSON(macroPath),frame=readJSON(framePath).anchor;
assert.deepEqual(frame,receipt.frame);assert.equal(macro.id,'14-13722-6690');
for(const p of [receiptPath,cachePath,macroPath,framePath,path.join(sourceDir,prior.input.file)])inputs.push(binding(p));
const tr=cfg.source_transform, ref=[macro.origin_longitude,macro.origin_latitude], origin=[121.4737,31.2304];
assert.equal(tr.macro_id,macro.id);assert.deepEqual(tr.height_reference,ref);assert.deepEqual(ref,[121.519775390625,31.306714687449947]);
assert.deepEqual(tr.scene_origin,origin);assert.equal(tr.near_copies_far_transform,true);assert(tr.matrix_observation?.length>20);
const M=tr.matrix_column_major_f64,F=tr.matrix_column_major_f32;
assert.deepEqual(M,runtime.source_transform.model_matrix_double);assert.deepEqual(F,runtime.source_transform.model_matrix_float32);
assert.deepEqual(tr.height_reference,runtime.source_transform.height_reference);
assert.deepEqual(tr.scene_origin,runtime.source_transform.scene_origin);
assert.equal(runtime.source_transform.near_inherits_far_matrix,true);
for(const m of [M,F])assert(Array.isArray(m)&&m.length===16&&m.every(Number.isFinite));
assert.deepEqual(F,M.map(Math.fround),'Source matrix f32 upload must exactly equal actual matrix f32');
// This delivery uses an unrotated macro transform. Fail on a future changed transform.
for(const i of [1,2,3,4,6,7,8,9,11,13])assert.equal(M[i],0,'Expected actual diagonal source macro matrix');
assert.equal(M[15],1);assert(M[0]>0&&M[5]>0&&M[10]>0);
const DEG=Math.PI/180,R=6371008.8,RENDER_R=6378137;
const cosOrigin=Math.cos(origin[1]*DEG),unit=1/(2*Math.PI*R*cosOrigin);
const mercator=(lng,lat)=>[(lng+180)/360,(1-Math.asinh(Math.tan(lat*DEG))/Math.PI)/2];
const originMerc=mercator(...origin);
const geo=(lng,lat,h=0)=>{const q=mercator(lng,lat);return[(q[0]-originMerc[0])/unit,h*cosOrigin/Math.cos(lat*DEG),(q[1]-originMerc[1])/unit];};
const expectedXYZ=geo(...ref),expectedYScale=cosOrigin/Math.cos(ref[1]*DEG);
const expectedXZScale=R/RENDER_R*expectedYScale;
assert(Math.abs(M[0]-expectedXZScale)<1e-12&&Math.abs(M[10]-expectedXZScale)<1e-12);
assert(Math.abs(M[5]-expectedYScale)<1e-12);
assert(Math.abs(M[12]-expectedXYZ[0])<2e-7&&Math.abs(M[14]-expectedXYZ[2])<2e-7,'Actual source anchor differs from independently derived Mercator frame');
for(let k=0;k<2;k++){
  const c=spec.display_height_clips[k];assert.deepEqual(c.height_reference,ref);
  assert.equal(c.owner.feature_local_id,1860);assert.equal(c.owner.macro_id,macro.id);
  assert.equal(c.min_height,28.705);assert.equal(c.max_height,30.11);
  const expected=[Math.fround(c.min_height*M[5]),Math.fround(c.max_height*M[5])];
  let ownerHash=2166136261;for(const ch of macro.id){ownerHash^=ch.charCodeAt(0);ownerHash=Math.imul(ownerHash,16777619);}ownerHash=(ownerHash>>>0)%16777215;
  for(let i=258+k*2;i<260+k*2;i++){
    assert.deepEqual(rows[i].slice(6,8),expected,'Wrong native→world slab');
    assert.deepEqual(rows[i].slice(12),[1860,ownerHash,0,0],'Height row scope differs from the actual source');
  }
}

// Standard binary32 error model: gamma(n) bounds n normal rounded operations.
// Zeros and multiplication by +/-1 are exact, and are excluded from n.
// The envelope includes any association and FMA (which needs fewer roundings).
const U=2**-24, gamma=n=>n*U/(1-n*U);
const PAD=1e-10; // Deliberately dominates binary64 bookkeeping error at this scale.
// Maximum RNE absolute error over all normal binary32 values with |x|<=m.
const halfULP=m=>m===0?0:2**(Math.floor(Math.log2(m))-24);
const sumRoundBound=(m,n)=>n*halfULP(m/(1-n*U));
function dotEnvelope(coeff,values,radii=[0,0,0,0]){
  let value=0,propagated=0,magnitude=0,terms=0,mults=0,productError=0;
  for(let i=0;i<4;i++){
    const a=coeff[i],b=values[i],r=radii[i];
    if(a===0)continue;
    value+=a*b;propagated+=Math.abs(a)*r;magnitude+=Math.abs(a)*(Math.abs(b)+r);
    terms++;if(Math.abs(a)!==1&&!(Math.abs(b)===1&&r===0)){mults++;productError+=halfULP(Math.abs(a)*(Math.abs(b)+r));}
  }
  const operations=mults+Math.max(0,terms-1);
  const absoluteBound=productError+sumRoundBound(magnitude+productError,Math.max(0,terms-1));
  return {value,radius:propagated+Math.min(gamma(operations)*magnitude,absoluteBound)+PAD,operations};
}
const rowOf=(m,i)=>[m[i],m[4+i],m[8+i],m[12+i]];
const transformExact=(m,p)=>[0,1,2].map(i=>rowOf(m,i).reduce((s,v,k)=>s+v*(k===3?1:p[k]),0));
function expandedEnvelope(model,instance,p,axis){
  let value=0,magnitude=0,operations=0,terms=0,productError=0;
  for(let j=0;j<4;j++)for(let k=0;k<4;k++){
    const factors=[model[j*4+axis],instance[k*4+j],p[k]];
    if(factors.some(x=>x===0))continue;
    const product=factors[0]*factors[1]*factors[2];
    value+=product;magnitude+=Math.abs(product);terms++;
    const products=Math.max(0,factors.filter(x=>Math.abs(x)!==1).length-1);
    operations+=products;productError+=gamma(products)*Math.abs(product);
  }
  operations+=Math.max(0,terms-1);
  const absoluteBound=productError+sumRoundBound(magnitude+productError,Math.max(0,terms-1));
  return {value,radius:Math.min(gamma(operations)*magnitude,absoluteBound)+PAD,operations};
}
const identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const instanceMatrix=(t,q,s)=>{
  const [x,y,z,w]=q,x2=2*x,y2=2*y,z2=2*z,xx=x*x2,xy=x*y2,xz=x*z2,yy=y*y2,yz=y*z2,zz=z*z2,wx=w*x2,wy=w*y2,wz=w*z2;
  return [(1-yy-zz)*s[0],(xy+wz)*s[0],(xz-wy)*s[0],0,
    (xy-wz)*s[1],(1-xx-zz)*s[1],(yz+wx)*s[1],0,
    (xz+wy)*s[2],(yz-wx)*s[2],(1-xx-yy)*s[2],0,...t,1].map(Math.fround);
};
const k0=RENDER_R*Math.cos(ref[1]*DEG),k1=R*Math.cos(frame.lat*DEG);
const psi0=Math.asinh(Math.tan(ref[1]*DEG)),psi1=Math.asinh(Math.tan(frame.lat*DEG));
const co=Math.cos(frame.heading*DEG),si=Math.sin(frame.heading*DEG);
const toCached=p=>{const e=k1*((ref[0]-frame.lng)*DEG+p[0]/k0),n=k1*(psi0-psi1-p[2]/k0);return[co*e-si*n,si*e+co*n,p[1]];};
const fromCached=(p,up=0)=>{
  const e=co*p[0]+si*p[1],n=-si*p[0]+co*p[1];
  return [(e/k1-(ref[0]-frame.lng)*DEG)*k0,up,(psi0-psi1-n/k1)*k0];
};

// Decode the original GLB independently; only Meshopt decompression is reused.
const decoderPath=resolve(cfg.meshopt_decoder);inputs.push(binding(decoderPath));
const {MeshoptDecoder}=await import(pathToFileURL(decoderPath));await MeshoptDecoder.ready;
assert.equal(bytes.toString('ascii',0,4),'glTF');assert.equal(bytes.readUInt32LE(4),2);assert.equal(bytes.readUInt32LE(8),bytes.length);
const jsonSize=bytes.readUInt32LE(12);assert.equal(bytes.readUInt32LE(16),0x4e4f534a);assert.equal(bytes.readUInt32LE(24+jsonSize),0x004e4942);
const doc=JSON.parse(bytes.toString('utf8',20,20+jsonSize)),bin=bytes.subarray(28+jsonSize),views=new Map(),accessors=new Map();
assert(doc.buffers.every(b=>!b.uri));assert.equal(doc.scenes.length,1);
function view(id){
  if(views.has(id))return views.get(id);
  const v=doc.bufferViews[id],e=v.extensions?.EXT_meshopt_compression;let b;
  if(e){assert.equal(e.buffer,0);b=new Uint8Array(e.count*e.byteStride);MeshoptDecoder.decodeGltfBuffer(b,e.count,e.byteStride,bin.subarray(e.byteOffset||0,(e.byteOffset||0)+e.byteLength),e.mode,e.filter);}
  else{assert.equal(v.buffer,0);b=bin.subarray(v.byteOffset||0,(v.byteOffset||0)+v.byteLength);}
  views.set(id,b);return b;
}
function accessor(id){
  if(accessors.has(id))return accessors.get(id);
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
  }accessors.set(id,result);return result;
}
let triangles=0,vertices=0,instances=0,cacheMaxDifference=0,lowVertexCount=0,lowMaxGPUY=-Infinity,lowMaxNativeY=-Infinity;
let owner1262Vertices=0,owner1262MaxGPUY=-Infinity,owner1262MaxNativeY=-Infinity;
const maxError=[0,0,0],worst=[null,null,null],worldAbsMax=[0,0,0];
const NATIVE_1262_MAX=28.700000762939453;
for(const nodeId of doc.scenes[doc.scene??0].nodes){
  const node=doc.nodes[nodeId];assert(!node.children?.length&&!node.matrix&&!node.translation&&!node.rotation&&!node.scale,'Original source top-level node must remain identity');
  const ext=node.extensions?.EXT_mesh_gpu_instancing,ia=ext?.attributes;
  const translations=ia?.TRANSLATION===undefined?null:accessor(ia.TRANSLATION),rotations=ia?.ROTATION===undefined?null:accessor(ia.ROTATION),scales=ia?.SCALE===undefined?null:accessor(ia.SCALE);
  const count=translations?.length||rotations?.length||scales?.length||1;
  for(const values of [translations,rotations,scales])if(values)assert.equal(values.length,count);
  for(const prim of doc.meshes[node.mesh].primitives){
    assert.equal(prim.mode??4,4);assert(!prim.targets?.length&&!node.skin,'No unmodelled morph/skinning vertex transforms');
    assert.equal(prim.attributes._FEATURE_ID_0,undefined,'Do not invent absent per-vertex source IDs');
    const positions=accessor(prim.attributes.POSITION),indices=prim.indices===undefined?positions.map((_,i)=>i):accessor(prim.indices).map(r=>r[0]);assert.equal(indices.length%3,0);
    for(let inst=0;inst<count;inst++){
      instances++;const I=ext?instanceMatrix(translations?.[inst]||[0,0,0],rotations?.[inst]||[0,0,0,1],scales?.[inst]||[1,1,1]):identity;
      // Cache per source vertex/instance; repeated triangle indices share exactly one shader input.
      const evaluated=new Map();
      for(let i=0;i<indices.length;i+=3){
        const triangleIndex=triangles++;
        for(let corner=0;corner<3;corner++){
          const id=indices[i+corner];assert(id>=0&&id<positions.length);
          let ev=evaluated.get(id);
          if(!ev){
            const p=positions[id],native=transformExact(I,p),world=transformExact(M,native),pf=[...p.map(Math.fround),1];
            const stage1=ext?[0,1,2].map(axis=>dotEnvelope(rowOf(I,axis),pf)):pf.slice(0,3).map(value=>({value,radius:0}));
            const stage2=[0,1,2].map(axis=>{
              const staged=dotEnvelope(rowOf(F,axis),[...stage1.map(x=>x.value),1],[...stage1.map(x=>x.radius),0]);
              const flat=expandedEnvelope(F,I,pf,axis);
              const lo=Math.min(staged.value-staged.radius,flat.value-flat.radius),hi=Math.max(staged.value+staged.radius,flat.value+flat.radius);
              return {value:(lo+hi)/2,radius:(hi-lo)/2+PAD};
            });
            ev={native,world,stage2,cached:toCached(native)};evaluated.set(id,ev);
          }
          for(let axis=0;axis<3;axis++){
            const cachedValue=cache.readDoubleLE((triangleIndex*9+corner*3+axis)*8);
            cacheMaxDifference=Math.max(cacheMaxDifference,Math.abs(ev.cached[axis]-cachedValue));
            const q=ev.stage2[axis],error=Math.abs(q.value-ev.world[axis])+q.radius;
            if(error>maxError[axis]){maxError[axis]=error;worst[axis]={triangle:triangleIndex,corner,node:nodeId,instance:inst,native:ev.native,world:ev.world,lower:q.value-q.radius,upper:q.value+q.radius};}
            worldAbsMax[axis]=Math.max(worldAbsMax[axis],Math.abs(q.value)+q.radius);
          }
          if(ev.native[1]<=NATIVE_1262_MAX+1e-12){lowVertexCount++;lowMaxNativeY=Math.max(lowMaxNativeY,ev.native[1]);lowMaxGPUY=Math.max(lowMaxGPUY,ev.stage2[1].value+ev.stage2[1].radius);}
          if(owner1262?.has(triangleIndex)){
            assert(ev.native[1]<=NATIVE_1262_MAX+1e-12,'A possible1262 vertex lies above the conservative subset');
            owner1262Vertices++;owner1262MaxNativeY=Math.max(owner1262MaxNativeY,ev.native[1]);owner1262MaxGPUY=Math.max(owner1262MaxGPUY,ev.stage2[1].value+ev.stage2[1].radius);
          }
          vertices++;
        }
      }
    }
  }
}
assert.equal(triangles,122780);assert.equal(vertices,122780*3);assert(cacheMaxDifference<1e-8,'Source decode/cache order or coordinate reconstruction changed');
assert(lowVertexCount>0);assert(Math.abs(lowMaxNativeY-NATIVE_1262_MAX)<1e-10,'Protected conservative subset must include the actual 1262 maximum');
if(owner1262)assert.equal(owner1262Vertices,7314*3);

const issues=[];
if(maxError.some(e=>e>=.003))issues.push('The conservative source vertex envelope reaches the separately reviewed3mm geometric margin.');
const radius=maxError.map(v=>v+2e-7); // independently derived Mercator/frame comparison budget, no invented raster interpolation budget
const lower=Math.min(...rows.slice(258).map(r=>r[6])),protectedUpper=lowMaxGPUY;
const protectedGap=lower-protectedUpper;
if(!(protectedGap>0))issues.push('Conservative possible-1262 vertex height envelope reaches the clipping slab.');

// Exact quantized triangle union proof. The bound covers every point of each
// actual roof polygon plus its XYZ numeric envelope; no point sampling is used.
const EPS=Math.fround(.001),cross=(a,b,p)=>(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]);
const pointKey=p=>p.join(','),edgeKey=(a,b)=>[pointKey(a),pointKey(b)].sort().join('|');
const samePoint=(a,b)=>a[0]===b[0]&&a[1]===b[1];
function sterbenz(a,lo,hi){return lo*hi>0&&a*lo>0&&Math.min(Math.abs(lo),Math.abs(hi))>=Math.abs(a)/2&&Math.max(Math.abs(lo),Math.abs(hi))<=Math.abs(a)*2;}
function crossError(edge,box){
  const [a,b]=edge,dx=b[0]-a[0],dz=b[1]-a[1];
  // Row coordinates and evaluated fragment positions are binary32. Their
  // close, same-sign subtractions are exact by Sterbenz's lemma.
  assert(sterbenz(a[0],b[0],b[0])&&sterbenz(a[1],b[1],b[1]));
  assert(sterbenz(a[0],box[0],box[2])&&sterbenz(a[1],box[1],box[3]));
  const px=Math.max(Math.abs(box[0]-a[0]),Math.abs(box[2]-a[0])),pz=Math.max(Math.abs(box[1]-a[1]),Math.abs(box[3]-a[1]));
  return gamma(3)*(Math.abs(dx)*pz+Math.abs(dz)*px)+PAD;
}
const coverage=[];
for(let k=0;k<2;k++){
  const range=cfg.added_row_ranges[k],r2=rows.slice(range.first,range.first+range.count);
  const tris=r2.map(r=>[[r[0],r[1]],[r[2],r[3]],[r[4],r[5]]]);
  const expectedClipPoints=spec.display_height_clips[k].geometry.coordinates[0].slice(0,-1).map(([lng,lat])=>{const p=geo(lng,lat);return[Math.fround(p[0]),Math.fround(p[2])];});
  assert.deepEqual([...new Set(tris.flat().map(pointKey))].sort(),[...new Set(expectedClipPoints.map(pointKey))].sort(),'Actual row vertices differ from independently projected declared clip');
  const edgeMap=new Map();
  for(const [i,t]of tris.entries()){
    const area=cross(t[0],t[1],t[2]);assert(Math.abs(area)>1e-9);const sign=Math.sign(area);
    for(let j=0;j<3;j++){const a=t[j],b=t[(j+1)%3],key=edgeKey(a,b);if(!edgeMap.has(key))edgeMap.set(key,[]);edgeMap.get(key).push({a,b,sign,triangle:i});}
    assert.deepEqual(r2[i].slice(8,12),[Math.min(...t.map(p=>p[0])),Math.min(...t.map(p=>p[1])),Math.max(...t.map(p=>p[0])),Math.max(...t.map(p=>p[1]))]);
  }
  const exterior=[...edgeMap.values()].filter(e=>e.length===1).flat(),shared=[...edgeMap.values()].filter(e=>e.length===2);
  assert.equal(exterior.length,4);assert.equal(shared.length,1);assert.equal(edgeMap.size,5);
  const all=[...new Map(tris.flat().map(p=>[pointKey(p),p])).values()];assert.equal(all.length,4);
  for(const e of exterior)for(const p of all)assert(e.sign*cross(e.a,e.b,p)>=-1e-10,'Quantized pair is not a convex quad');
  const diag=shared[0],third=tris.map(t=>t.find(p=>!samePoint(p,diag[0].a)&&!samePoint(p,diag[0].b)));
  assert(cross(diag[0].a,diag[0].b,third[0])*cross(diag[0].a,diag[0].b,third[1])<0,'Triangles do not straddle their common diagonal');
  const patch=spec.patches[k],ring=patch.actual_main_roof_retained_geometry_wgs84.coordinates[0].slice(0,-1);
  const localRing=patch.actual_main_roof_retained_geometry_local_enu.coordinates[0].slice(0,-1);
  assert.equal(localRing.length,ring.length);
  const target=localRing.map(p=>transformExact(M,fromCached(p))).map(p=>[p[0],p[2]]);
  let frameAgreement=0;
  for(let i=0;i<ring.length;i++){
    const geographic=geo(...ring[i]);frameAgreement=Math.max(frameAgreement,Math.abs(target[i][0]-geographic[0]),Math.abs(target[i][1]-geographic[2]));
  }
  assert(frameAgreement<2e-7,'Actual decoded ENU polygon and declared WGS84 polygon disagree');
  const envelope=target.flatMap(p=>[-1,1].flatMap(sx=>[-1,1].map(sz=>[p[0]+sx*radius[0],p[1]+sz*radius[2]])));
  const box=[Math.min(...envelope.map(p=>p[0])),Math.min(...envelope.map(p=>p[1])),Math.max(...envelope.map(p=>p[0])),Math.max(...envelope.map(p=>p[1]))];
  const bbox=[Math.min(...all.map(p=>p[0])),Math.min(...all.map(p=>p[1])),Math.max(...all.map(p=>p[0])),Math.max(...all.map(p=>p[1]))];
  const bboxMargins=[box[0]-bbox[0],box[1]-bbox[1],bbox[2]-box[2],bbox[3]-box[3]];
  const outer=exterior.map(e=>{const exactMargin=Math.min(...envelope.map(p=>e.sign*cross(e.a,e.b,p))),roundError=crossError([e.a,e.b],box);return{row:range.first+e.triangle,a:e.a,b:e.b,exact_signed_cross_margin:exactMargin,arithmetic_error_bound:roundError,shader_tolerance_margin:exactMargin+EPS-roundError};});
  const diagonal=diag.map(e=>({row:range.first+e.triangle,error_bound:crossError([e.a,e.b],box),available_tolerance:EPS}));
  const roofY=patch.actual_original_main_top_native_m*M[5],heightMargins=[roofY-radius[1]-r2[0][6],r2[0][7]-(roofY+radius[1])];
  const passed=bboxMargins.every(x=>x>0)&&outer.every(e=>e.exact_signed_cross_margin>0&&e.shader_tolerance_margin>0)&&diagonal.every(e=>e.error_bound<EPS)&&heightMargins.every(x=>x>0);
  if(!passed)issues.push(patch.interface+': whole-polygon bbox/cross/height envelope not certified; inspect margins, do not replace with successful samples.');
  coverage.push({interface:patch.interface,rows:[range.first,range.first+1],passed,enu_to_wgs84_world_agreement:frameAgreement,global_bbox_margins:bboxMargins,outer_edges:outer,shared_diagonal:diagonal,target_roof_height_margins:heightMargins,
    proof:'Expanded target polygon is inside the exact convex union of the two quantized row triangles. Every point therefore lies in at least one exact triangle and its strict bbox. Outer cross margins and each shared-diagonal arithmetic error stay within the existing ±0.001 shader tolerance.'});
}
const result={schema:'city-museum-independent-height-numeric-v1',passed:issues.length===0,
  reviewer:'/root/museum_review/gate_static_review',script:binding(fileURLToPath(import.meta.url)),
  pass_scope:'Original source-to-world vertex/row binary32 arithmetic and geometric-boundary numeric checks only; no hardware raster interpolation certificate.',
  fragment_interpolation_certified:false,actual_final_browser_pixels_required:true,prepared_script_executed_after_explicit_go:true,
  reviewed_utc:new Date().toISOString(),inputs,source_triangles:triangles,source_triangle_vertices:vertices,source_instances_or_primitives:instances,
  final_bridge_inputs:{runtime_receipt:cfg.runtime_report,gpu_row_payload:cfg.rows,preflight:cfg.preflight,
    actual_production_code_bindings:cfg.bindings,source_decode_receipt:binding(receiptPath),source_near_input:binding(path.join(sourceDir,prior.input.file)),
    possible_owner_indices:cfg.possible_owner_indices||null,rows:262,old_rows:218,pre_height_rows:258,added_rows:4,capacity:288,
    original218_prefix_sha256:runtime.data_payload.old218_prefix_sha256,pre_height258_prefix_sha256:runtime.data_payload.base258_prefix_sha256,
    catalogue_overlay_scope:runtime.private_preflight?'Runtime rows use an explicitly declared private catalog overlay. Production code is bound, but final published contract/catalog equality needs a later final receipt.':'Runtime receipt used the actual published catalog.'},
  cached_payload_sha256:sha(cache),cache_max_coordinate_difference:cacheMaxDifference,
  arithmetic_model:{unit_roundoff:U,rounding:'binary32 round-to-nearest; normal finite values',
    multiply_add:'Union of staged dot-product and expanded nonzero source→world polynomial envelopes includes separate multiplication/addition, reassociation and FMA. Each uses the tighter of gamma(n) and a conservative absolute half-ULP/product error bound. Source accessor input and instance/model matrix uploads are explicitly rounded.',
    fragment_interpolation_certified:false,bookkeeping_padding:PAD},
  source_transform:tr,runtime_private_preflight:runtime.private_preflight,max_vertex_world_error_xyz:maxError,max_world_absolute_xyz:worldAbsMax,worst_vertices:worst,
  mapping_three_mm_margin_comparison:{margin_world_units:0.003,vertex_error_below_margin_xyz:maxError.map(e=>e<0.003),remaining_world_margin_xyz:maxError.map(e=>0.003-e)},
  vertex_and_row_numeric_envelope_xyz:radius,protected_height:{selection:'All original near vertices whose independently decoded native Y is at or below1262 maximum; conservative superset, no invented owner labels.',
    native_max:NATIVE_1262_MAX,vertices:lowVertexCount,actual_selected_native_max:lowMaxNativeY,vertex_world_y_upper:lowMaxGPUY,
    possible_owner1262:owner1262?{triangles:owner1262.size,vertices:owner1262Vertices,max_native_y:owner1262MaxNativeY,max_world_y_upper:owner1262MaxGPUY,all_within_conservative_subset:true}:null,
    vertex_world_y_upper_for_comparison:protectedUpper,minimum_clip_world_y:lower,strict_remaining_world_gap:protectedGap,passed:protectedGap>0},
  whole_target_polygon_coverage:coverage,issues,
  limits:'This certifies the stated source vertex/row binary32 and geometric-boundary numeric model only. Fragment interpolation is not certified. Actual final browser pixels remain required. It does not assign labels to ambiguous near triangles or replace foreign-owner geometry review.'};
const outputPath=path.resolve(outputName);
if(fs.existsSync(outputPath)){
  const old=fs.readFileSync(outputPath),ext=path.extname(outputPath),archive=outputPath.slice(0,-ext.length)+'-before-'+sha(old).slice(0,12)+ext;
  if(!fs.existsSync(archive))fs.writeFileSync(archive,old);
}
fs.writeFileSync(outputPath,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({passed:result.passed,source_triangles:triangles,max_vertex_world_error_xyz:maxError,protected_height_gap:protectedGap,issues}));
if(!result.passed)process.exitCode=1;
