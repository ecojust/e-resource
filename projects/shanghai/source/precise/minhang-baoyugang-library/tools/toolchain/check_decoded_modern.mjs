/** Actual vendored GLTFLoader+Meshopt CPU decode. No renderer, browser or model generation. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {registerHooks} from 'node:module';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {triangleKey,addTriangle,compareTriangles,compareValues,materialState,compareProtectedGroups,glbTriplesToENU} from './decode_core.mjs';

if(process.argv.includes('--help')){console.log('Usage: node check_decoded_modern.mjs PROJECT READY_TARGET PACKAGE_DIRECTORY NEW_REPORT [--keep-evidence]');process.exit(0);}
const keepEvidence=process.argv.includes('--keep-evidence');
const [projectArg,targetArg,packageArg,outputArg]=process.argv.slice(2).filter(x=>x!=='--keep-evidence');
assert(projectArg&&targetArg&&packageArg&&outputArg,'Usage: node check_decoded_modern.mjs PROJECT READY_TARGET PACKAGE_DIRECTORY NEW_REPORT');
const project=path.resolve(projectArg),targetFile=path.resolve(targetArg),packageDir=path.resolve(packageArg),output=path.resolve(outputArg),here=path.dirname(fileURLToPath(import.meta.url));
assert(output!==project&&!output.startsWith(project+path.sep),'Output must be outside MAIN');
for(let q=path.dirname(output);;q=path.dirname(q)){try{assert(!(await fs.lstat(q)).isSymbolicLink(),'Output symlink parent rejected');}catch(e){if(e.code!=='ENOENT')throw e;}if(path.dirname(q)===q)break;}
await assert.rejects(fs.stat(output),{code:'ENOENT'});
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=async p=>JSON.parse(await fs.readFile(p));
async function descriptor(file){const b=await fs.readFile(file);assert(b.length>0&&b.length<100_000_000);return {source:path.resolve(file),bytes:b.length,sha256:sha(b)};}
async function bound(d){assert(d&&typeof d.source==='string'&&path.isAbsolute(d.source),'Actual source descriptor required');for(let p=d.source;;p=path.dirname(p)){assert(!(await fs.lstat(p)).isSymbolicLink(),'Symlink input rejected');if(path.dirname(p)===p)break;}assert.deepEqual(await descriptor(d.source),d,'Source bytes/SHA changed');return d.source;}
const target=await json(targetFile);
assert.equal(target.schema,'modern-building-target-spec-v11');assert.equal(target.status,'ready','Pending template cannot be decoded or accepted');
assert(['jiading-shanghai-auto-museum','minhang-baoyugang-library'].includes(target.id));assert.equal(target.browser_accepted,false);
const upstream=await json(path.join(here,'upstream-lock.json'));
async function checkUpstream(){for(const row of upstream.files){const d=await descriptor(path.join(project,row.project_relative));assert.equal(d.bytes,row.bytes);assert.equal(d.sha256,row.sha256);}}
await checkUpstream();
await bound(target.source_geometry);const sourceGeometry=await json(target.source_geometry.source);assert.equal(sourceGeometry.id,target.id);
for(const name of ['source_freeze','package_spec','raw','raw_geometry','native','probe_set','source_structure_report'])await bound(target.actual[name]);
const packageRecordFile=path.join(packageDir,'packaging-record.json'),packageRecord=await json(packageRecordFile);
assert.equal(packageRecord.schema,'precise-building-packaging-v1');assert.equal(packageRecord.building_id,target.id);assert.equal(packageRecord.packaging_passed,true);
assert.equal(packageRecord.modern_target.sha256,(await descriptor(targetFile)).sha256);
assert.equal(packageRecord.inputs.spec.sha256,target.actual.package_spec.sha256);
const externalToolLock=await descriptor(path.join(here,'external-tool-lock.json'));assert.deepEqual(packageRecord.external_gltfpack_tool_lock,externalToolLock);const externalTools=await json(externalToolLock.source);for(const d of externalTools.files)await bound(d);
assert.equal(packageRecord.assets.raw.sha256,target.actual.raw.sha256);assert.equal(packageRecord.assets.native.sha256,target.actual.native.sha256);
const lodInput=target.lod_policy.mode==='compression-only'?target.actual.raw:target.actual.authored_lod;assert.deepEqual(packageRecord.authored_lod_input,lodInput,'Package LOD source descriptor differs');
assert.equal(packageRecord.lod_policy.automatic_simplification,false);assert.equal(packageRecord.lod_policy.mode,target.lod_policy.mode);
assert.equal(target.decode_policy.normal_angle_degrees_inclusive,.05);assert.equal(target.decode_policy.material_numeric_difference_exclusive,1e-6);
assert.equal(target.decode_policy.web_bounds_difference_m_inclusive,.0001);assert.equal(target.lod_policy.bounds_limit_m_exclusive,.35);
assert.deepEqual(target.lod_policy.allowed_omission_label_patterns,target.id==='jiading-shanghai-auto-museum'?[]:['(?:^|/)fine-tile-joints-[0-9]+$']);
const url=name=>pathToFileURL(path.join(project,name)).href;
const hook=registerHooks({resolve(s,c,next){return s==='three'?{url:url('vendor/three.module.js'),shortCircuit:true}:next(s,c);}});
const THREE=await import(url('vendor/three.module.js'));
const {GLTFLoader}=await import(url('vendor/GLTFLoader.js'));hook.deregister();
const {MeshoptDecoder}=await import(url('vendor/meshopt_decoder.module.js'));await MeshoptDecoder.ready;
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const probes=await json(target.actual.probe_set.source);
assert.equal(probes.schema,'modern-finite-requests-v1');
// The independent finite-check engine owns geometric checks. This decoder only
// reconstructs semantic parts from actual decoded oriented triangle copies.
// It never applies raw index ranges to optimized/compressed accessors.
async function semanticArrays(role,semanticSource,actualAsset,base){
  const out=path.join(base,role);await fs.mkdir(out,{recursive:false});
  const available=new Map([...actualAsset.recordsByKey].map(([key,records])=>[key,[...records]]));
  const metadata=[],chunks=[];let buffer=Buffer.alloc(64*1024*1024),offset=0,totalTriangles=0,chunkIndex=0;
  async function flush(){if(!offset)return;const file=path.join(out,`triangles-${String(chunkIndex++).padStart(3,'0')}.f64`);await fs.writeFile(file,buffer.subarray(0,offset),{flag:'wx'});chunks.push(await descriptor(file));offset=0;}
  for(const [key,part]of semanticSource.groups){
    const first=totalTriangles;
    for(const expected of part.records){
      const candidates=available.get(expected.key);assert(candidates?.length,'Missing semantic triangle in actual decoded asset');
      let best=-1,error=Infinity;for(let i=0;i<candidates.length;i++){const e=Math.max(...expected.normals.map((x,j)=>Math.abs(x-candidates[i].normals[j])));if(e<error){error=e;best=i;}}
      const actual=candidates.splice(best,1)[0];
      if(offset+144>buffer.length)await flush();
      const enu=[...glbTriplesToENU(actual.points),...glbTriplesToENU(actual.normals)];
      for(const v of enu){assert(Number.isFinite(v));buffer.writeDoubleLE(v,offset);offset+=8;}totalTriangles++;
    }
    metadata.push({key,label:part.label,material:part.material,first_triangle:first,triangle_count:totalTriangles-first,primitive_index:-1,source_primitive_index:part.primitive_index,source_first_triangle:part.first_triangle});
  }
  for(const records of available.values())assert.equal(records.length,0,'Decoded triangles outside reconstructed semantic parts');
  await flush();
  const manifest={schema:'modern-decoded-semantic-arrays-v11',building_id:target.id,role,asset:{source:actualAsset.source,bytes:actualAsset.bytes,sha256:actualAsset.sha256},source_geometry_sha256:target.source_geometry.sha256,semantic_source_asset_sha256:semanticSource.sha256,semantic_source_sidecar:semanticSource.semanticSidecar,coordinate_system:'ENU metres',binary_format:'little-endian Float64, each144-byte row=9canonical-oriented triangle positions then9same-corner unit normals',triangle_count:totalTriangles,chunks,parts:metadata,materials:actualAsset.gltfMaterials,decoded_material_properties:actualAsset.materials,extras:actualAsset.extras,identity_method:'Exact cyclic-oriented position/material triangle matching with multiplicity and bounded normal matching; deterministic assignment of coincident indistinguishable copies; no raw indices applied to compressed geometry',chunk_retention:{persistent:keepEvidence,policy:keepEvidence?'Explicit keep-evidence: retain this run derived chunks':'Temporary actual inputs: remove only tool-created chunks after this role finite check; keep SHA/bytes/manifests and actual result'},browser_accepted:false};
  const file=path.join(out,'manifest.json');await fs.writeFile(file,JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});return descriptor(file);
}
function ranges(doc,sidecar){
  if(sidecar.actual_serialized_part_ranges)return sidecar.actual_serialized_part_ranges;
  assert.equal(doc.meshes.length,1,'Semantic range adapter expects the author single-mesh export');
  return doc.meshes[0].primitives.flatMap((p,primitive_index)=>{assert(p.extras?.semanticParts?.length,'Missing actual serialized semanticParts');return p.extras.semanticParts.map(s=>({label:s.label,material:doc.materials[p.material].name,primitive_index,first_triangle:s.firstIndex/3,triangle_count:s.indexCount/3}));});
}
async function decode(file,expected,sidecarFile=null){
  const bytes=await fs.readFile(file),d=await descriptor(file);assert.equal(d.bytes,expected.bytes);assert.equal(d.sha256,expected.sha256);
  assert.equal(bytes.readUInt32LE(0),0x46546c67);assert.equal(bytes.readUInt32LE(4),2);assert.equal(bytes.readUInt32LE(8),bytes.length);
  const n=bytes.readUInt32LE(12),doc=JSON.parse(bytes.subarray(20,20+n));
  assert.equal((doc.images??[]).length,0);assert.equal((doc.textures??[]).length,0);assert((doc.buffers??[]).every(b=>!('uri'in b)));
  assert.equal(doc.extras.id,target.id);assert.equal(doc.extras.source_geometry_sha256,target.source_geometry.sha256);
  const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');gltf.scene.updateWorldMatrix(true,true);
  const triangles=new Map(),groups=new Map(),materials={},primitiveData=new Map(),recordsByKey=new Map(),bounds=new THREE.Box3();let count=0,vertices=0,draws=0;
  gltf.scene.traverse(mesh=>{
    if(!mesh.isMesh)return;assert(!mesh.isInstancedMesh&&!Array.isArray(mesh.material));
    const p=mesh.geometry.getAttribute('position'),normal=mesh.geometry.getAttribute('normal'),index=mesh.geometry.index,m=mesh.material;
    assert(p&&normal&&!mesh.geometry.getAttribute('uv'));const state=materialState(m);
    if(materials[m.name])compareValues(materials[m.name],state);else materials[m.name]=state;
    const nm=new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld),total=index?index.count:p.count,records=[];
    assert.equal(total%3,0);count+=total/3;vertices+=p.count;draws++;
    for(let i=0;i<p.count;i++){const pos=new THREE.Vector3().fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld);assert(pos.toArray().every(Number.isFinite));bounds.expandByPoint(pos);const len=new THREE.Vector3().fromBufferAttribute(normal,i).length();assert(len>.99&&len<1.01);}
    for(let i=0;i<total;i+=3){
      const points=[],normals=[];
      for(let k=0;k<3;k++){const j=index?index.getX(i+k):i+k;points.push(new THREE.Vector3().fromBufferAttribute(p,j).applyMatrix4(mesh.matrixWorld).toArray());normals.push(new THREE.Vector3().fromBufferAttribute(normal,j).applyMatrix3(nm).normalize().toArray());}
      const a=new THREE.Vector3(...points[1]).sub(new THREE.Vector3(...points[0])),b=new THREE.Vector3(...points[2]).sub(new THREE.Vector3(...points[0]));assert(a.cross(b).length()>1e-12,'Actual zero-area triangle');
      const {key,rotation}=triangleKey(points,m.name),nn=[0,1,2].flatMap(k=>normals[(k+rotation)%3]);addTriangle(triangles,key,nn);const actualRecord={key,normals:nn,points:[0,1,2].flatMap(k=>points[(k+rotation)%3])};if(!recordsByKey.has(key))recordsByKey.set(key,[]);recordsByKey.get(key).push(actualRecord);if(sidecarFile)records.push(actualRecord);
    }
    if(sidecarFile){const association=gltf.parser.associations.get(mesh);assert.equal(association.meshes,0);assert(Number.isInteger(association.primitives));assert(!primitiveData.has(association.primitives));primitiveData.set(association.primitives,{material:m.name,records});}
  });
  assert(count>0);if(expected.triangles!==undefined)assert.equal(count,expected.triangles);
  if(sidecarFile){
    const sidecar=await json(sidecarFile);assert.equal(sidecar.sha256,d.sha256);assert.equal(sidecar.bytes,d.bytes);assert.equal(sidecar.triangles,count);
    const ordinal=new Map(),rr=ranges(doc,sidecar),coverage=new Map([...primitiveData].map(([k,v])=>[k,new Uint8Array(v.records.length)]));assert(rr.length>0);
    for(const part of rr){
      const primitive=primitiveData.get(part.primitive_index);assert(primitive&&primitive.material===part.material);assert(Number.isInteger(part.first_triangle)&&Number.isInteger(part.triangle_count)&&part.first_triangle>=0&&part.triangle_count>0);
      const pair=JSON.stringify([part.label,part.material]),number=ordinal.get(pair)??0;ordinal.set(pair,number+1);const key=JSON.stringify([part.label,part.material,number]);assert(!groups.has(key));groups.set(key,{label:part.label,material:part.material,primitive_index:part.primitive_index,first_triangle:part.first_triangle,triangles:new Map(),records:[],count:0});const g=groups.get(key);
      for(let i=part.first_triangle;i<part.first_triangle+part.triangle_count;i++){assert(i<primitive.records.length);assert.equal(coverage.get(part.primitive_index)[i],0,'Overlapping semantic ranges');coverage.get(part.primitive_index)[i]=1;const record=primitive.records[i];addTriangle(g.triangles,record.key,record.normals);g.records.push(record);g.count++;}
    }
    for(const seen of coverage.values())assert(seen.every(x=>x===1),'Semantic map fails to cover actual raw triangles');
  }
  const lo=bounds.min.toArray(),hi=bounds.max.toArray();
  gltf.scene.traverse(m=>{if(m.isMesh){m.geometry.dispose();m.material.dispose();}});
  return {...d,triangles:count,vertices,draw_calls:draws,bounds_glb:{min:lo,max:hi},bounds_enu_m:[[lo[0],-hi[2],lo[1]],[hi[0],-lo[2],hi[1]]],materials,gltfMaterials:Object.fromEntries(doc.materials.map(m=>[m.name,m])),extras:doc.extras,semanticSidecar:sidecarFile?await descriptor(sidecarFile):null,embedded_images:0,recordsByKey,triangleMap:triangles,groups};
}
const assetPath=role=>{const a=packageRecord.assets[role];assert.equal(a.file,target.paths[role]);const file=path.resolve(packageDir,a.file);assert(file.startsWith(packageDir+path.sep));return file;};
const raw=await decode(assetPath('raw'),packageRecord.assets.raw,target.actual.raw_geometry.source);
const web=await decode(assetPath('web'),packageRecord.assets.web);const rawWeb=compareTriangles(raw.triangleMap,web.triangleMap);
compareValues(raw.materials,web.materials);web.triangleMap.clear();
let authored=raw,protectedResult;
if(target.lod_policy.mode==='authored-subtraction'){
  await bound(target.actual.authored_lod);await bound(target.actual.authored_lod_geometry);
  authored=await decode(target.actual.authored_lod.source,target.actual.authored_lod,target.actual.authored_lod_geometry.source);
  protectedResult=compareProtectedGroups(raw.groups,authored.groups,target.lod_policy.allowed_omission_label_patterns);
  for(const name of Object.keys(authored.materials)){assert(raw.materials[name]);compareValues(raw.materials[name],authored.materials[name]);}
}else{assert.equal(target.lod_policy.mode,'compression-only');protectedResult=compareProtectedGroups(raw.groups,raw.groups,[]);}
const lod=await decode(assetPath('lod'),packageRecord.assets.lod);const authoredLod=compareTriangles(authored.triangleMap,lod.triangleMap);compareValues(authored.materials,lod.materials);
const delta=a=>Math.max(...raw.bounds_glb.min.map((v,i)=>Math.abs(v-a.bounds_glb.min[i])),...raw.bounds_glb.max.map((v,i)=>Math.abs(v-a.bounds_glb.max[i])));
assert(delta(web)<=.0001);assert(delta(lod)<.35);assert.equal(packageRecord.lod_policy.geometric_reduction_claimed,lod.triangles<raw.triangles);
for(const role of ['raw','web','lod','native']){const d=await descriptor(assetPath(role)),a=packageRecord.assets[role];assert.equal(d.sha256,a.sha256);assert.equal(d.bytes,a.bytes);}
await checkUpstream();await bound(externalToolLock);for(const d of externalTools.files)await bound(d);for(const d of [target.source_geometry,...Object.values(target.actual).filter(x=>x&&typeof x==='object'&&'source'in x)])await bound(d);
// All comparisons are complete before finite checking. Release duplicate maps;
// retain actual per-triangle records only for the semantic array bridge.
for(const a of new Set([raw,web,authored,lod])){a.triangleMap.clear();for(const part of a.groups.values())part.triangles.clear();}
const evidenceDir=output+'.evidence';await fs.mkdir(evidenceDir,{recursive:false});
const arrays={},finiteRoles={},cleanup=[];
const finiteRunner=path.join(here,'run_decoded_finite.py'),finiteReport=path.join(evidenceDir,'finite-checks.json');
const roleJobs=[['raw',raw,raw],['web',raw,web],['lod',authored,lod]];if(authored!==raw)roleJobs.push(['authored_lod',authored,authored]);
for(const [role,source,actual] of roleJobs){
  const array=await semanticArrays(role,source,actual,evidenceDir);arrays[role]=array;
  const roleDir=path.dirname(array.source),input=path.join(roleDir,'finite-input.json'),result=path.join(roleDir,'finite-report.json');
  await fs.writeFile(input,JSON.stringify({schema:'modern-decoded-finite-role-input-v11',role,target:await descriptor(targetFile),requests:target.actual.probe_set,decoded_array_manifest:array},null,2)+'\n',{flag:'wx'});
  let child;
  try{
    child=spawnSync('python',[finiteRunner,'--input',input,'--output',result],{encoding:'utf8',maxBuffer:2*1024*1024});
  }finally{
    const manifest=await json(array.source);
    for(const chunk of manifest.chunks){assert(chunk.source.startsWith(roleDir+path.sep));await bound(chunk);if(!keepEvidence)await fs.unlink(chunk.source);cleanup.push({...chunk,persistent:keepEvidence,removed_after_finite_invocation:!keepEvidence});}
    const log=path.join(roleDir,'chunk-retention.json');await fs.writeFile(log,JSON.stringify({schema:'modern-decoded-temporary-array-retention-v11',role,keep_evidence:keepEvidence,chunks:cleanup.filter(x=>x.source.startsWith(roleDir+path.sep)),no_preexisting_files_removed:true},null,2)+'\n',{flag:'wx'});
  }
  assert.equal(child.status,0,'Independent finite engine rejected actual decoded mesh: '+child.stderr);
  const finite=await json(result);assert.equal(finite.schema,'modern-actual-decoded-finite-role-v11');assert.equal(finite.passed,true);assert.equal(finite.building_id,target.id);assert.equal(finite.role,role);
  assert.equal(finite.current_asset.sha256,actual.sha256);
  finiteRoles[role]={passed:true,current_asset:{source:actual.source,bytes:actual.bytes,sha256:actual.sha256},array_manifest:array,finite_report:await descriptor(result),chunk_retention:await descriptor(path.join(roleDir,'chunk-retention.json'))};
}
const finiteSuite={schema:'modern-actual-decoded-finite-suite-v11',passed:true,building_id:target.id,source_geometry_sha256:target.source_geometry.sha256,raw_sha256:target.actual.raw.sha256,source_structure_report:target.actual.source_structure_report,probe_set:target.actual.probe_set,decoder:await descriptor(fileURLToPath(import.meta.url)),decoder_core:await descriptor(path.join(here,'decode_core.mjs')),bridge:await descriptor(finiteRunner),independent_engine_lock:await descriptor(path.join(here,'independent-engine-lock.json')),roles:finiteRoles,all_actual_roles_checked:true,temporary_array_policy:keepEvidence?'Explicitly retained derived arrays':'Actual arrays were input only; each tool-created chunk removed after its role finite check, SHA/bytes and actual reports retained',browser_accepted:false,native_visual_accepted:false};
await fs.writeFile(finiteReport,JSON.stringify(finiteSuite,null,2)+'\n',{flag:'wx'});
const publicAsset=a=>{const {triangleMap,groups,recordsByKey,...record}=a;return record;};
const report={schema:'modern-actual-decoded-package-v11',passed:true,building_id:target.id,target_sha256:(await descriptor(targetFile)).sha256,package_record_sha256:(await descriptor(packageRecordFile)).sha256,source_geometry_sha256:target.source_geometry.sha256,source_freeze_sha256:target.actual.source_freeze.sha256,external_gltfpack_tool_lock:externalToolLock,assets:{raw:publicAsset(raw),web:publicAsset(web),lod:publicAsset(lod)},authored_lod:authored===raw?null:publicAsset(authored),raw_web:rawWeb,authored_to_compressed_lod:authoredLod,lod_protected_geometry:protectedResult,web_exact_oriented_position_material_triangle_multiset:true,modern_material_properties_preserved:true,modern_material_scope:'All actual present loaded PBR/alpha/transmission/IOR/volume/attenuation properties compared; absent optical features are not invented and photometric correctness is not certified',lod_mode:target.lod_policy.mode,geometric_reduction_applied:lod.triangles<raw.triangles,actual_lod_triangle_ratio:lod.triangles/raw.triangles,web_bounds_difference_m:delta(web),lod_bounds_difference_m:delta(lod),finite_probe_set:target.actual.probe_set,finite_actual_decoded_report:await descriptor(finiteReport),actual_decoded_semantic_arrays:arrays,decoder:'Actual locked project Three GLTFLoader and MeshoptDecoder, CPU only',browser_accepted:false,native_visual_accepted:false,limitations:['Exact triangle comparisons concern exported reconstruction geometry, not architectural measurement accuracy.','Authored LOD is verified by retained semantic geometry and finite probes; no global collision, navigability or photometric proof.','Compression-only LOD means no triangle reduction; no low-poly optimization is claimed.','Native and browser acceptance require separate actual reviews.']};
await fs.writeFile(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,building_id:target.id,triangles:{raw:raw.triangles,web:web.triangles,lod:lod.triangles},finite_actual_decoded_passed:true,report:output,browser_accepted:false}));
