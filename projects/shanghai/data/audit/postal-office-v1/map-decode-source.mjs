import path from 'node:path';
import fs from 'node:fs';import zlib from 'node:zlib';import crypto from 'node:crypto';import{registerHooks}from'node:module';
const project=path.resolve(process.env.POSTAL_REPO||'/workspace/e-resource')+'/projects/shanghai/',out=path.resolve(process.env.POSTAL_MAPPING_WORK||'/workspace/shanghai-postal-mapping')+'/',cache=out;
registerHooks({resolve(specifier,context,next){return specifier==='three'?{url:'file://'+project+'vendor/three.module.js',shortCircuit:true}:next(specifier,context);}});
const{GLTFLoader}=await import(project+'vendor/GLTFLoader.js');const{MeshoptDecoder}=await import(project+'vendor/meshopt_decoder.module.js');const{Matrix4,Vector3}=await import(project+'vendor/three.module.js');
const config=JSON.parse(fs.readFileSync(out+'initial-local-frame.json')).anchor;const macro=JSON.parse(fs.readFileSync(cache+'macro-READY.json'));const DEG=Math.PI/180,R=6378137,kMacro=R*Math.cos(macro.origin_latitude*DEG),kTarget=6371008.8*Math.cos(config.lat*DEG),logMacro=Math.log(Math.tan(Math.PI/4+macro.origin_latitude*DEG/2)),logTarget=Math.log(Math.tan(Math.PI/4+config.lat*DEG/2));
const context=JSON.parse(fs.readFileSync(out+'context-features.json'));const wanted=new Set(context.map(x=>x.localId));const results=[];
for(const [variant,path]of[['far',cache+'baseline-far.glb'],['near',out+'baseline-near.glb.gz']]){
 const bytes=fs.readFileSync(path),decoded=path.endsWith('.gz')?zlib.gunzipSync(bytes):bytes,loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);const gltf=await loader.parseAsync(decoded.buffer.slice(decoded.byteOffset,decoded.byteOffset+decoded.byteLength),'');gltf.scene.updateMatrixWorld(true);
 const meshRecords=[],triangles=[],triangleOwners=[];let total=0;const selectedFarCounts={};const v=new Vector3(),mat=new Matrix4(),instance=new Matrix4();
 gltf.scene.traverse(mesh=>{
  if(!mesh.isMesh)return;const pos=mesh.geometry.getAttribute('position'),fid=mesh.geometry.getAttribute('_feature_id_0'),index=mesh.geometry.getIndex(),count=index?.count??pos.count,instances=mesh.isInstancedMesh?mesh.count:1;
  meshRecords.push({name:mesh.name,mesh_type:mesh.type,attributes:Object.keys(mesh.geometry.attributes),vertices:pos.count,index_count:count,instances,material_names:(Array.isArray(mesh.material)?mesh.material:[mesh.material]).map(m=>m.name)});
  for(let j=0;j<instances;j++){
   if(mesh.isInstancedMesh){mesh.getMatrixAt(j,instance);mat.multiplyMatrices(mesh.matrixWorld,instance);}else mat.copy(mesh.matrixWorld);
   for(let i=0;i<count;i+=3){total++;const ids=[0,1,2].map(n=>index?index.getX(i+n):i+n);if(variant==='far'&&!ids.every(k=>wanted.has(fid?.getX(k))))continue;
    if(variant==='far'){for(const id of ids)if(fid.getX(id)!==fid.getX(ids[0]))throw Error('Mixed-owner triangle');const id=fid.getX(ids[0]);selectedFarCounts[id]=(selectedFarCounts[id]??0)+1;}
    const vertices=ids.map(n=>{v.fromBufferAttribute(pos,n).applyMatrix4(mat);return[kTarget*((macro.origin_longitude-config.lng)*DEG+v.x/kMacro),kTarget*(logMacro-logTarget-v.z/kMacro),v.y];});
    triangles.push(...vertices.flat());triangleOwners.push(variant==='far'?fid.getX(ids[0]):0);
   }
  }
 });
 fs.writeFileSync(out+`baseline-${variant}-owners.u32`,Buffer.from(new Uint32Array(triangleOwners).buffer));const buffer=new Float64Array(triangles);fs.writeFileSync(out+`baseline-${variant}-triangles.f64`,Buffer.from(buffer.buffer));results.push({variant,path,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length,decoded_sha256:crypto.createHash('sha256').update(decoded).digest('hex'),decoded_bytes:decoded.length,expanded_triangles_total:total,selected_far_triangle_counts:variant==='far'?selectedFarCounts:null,preselected_triangles:buffer.length/9,meshes:meshRecords,coordinates:'Each output vertex is [Postal local east, local north, native baseline up-m]. Complete mesh/instance matrices applied, production EPSG3857 horizontal map scaling inverted.',triangle_file:out+`baseline-${variant}-triangles.f64`});
}
fs.writeFileSync(out+'source-decode.json',JSON.stringify(results,null,2)+'\n');process.stdout.write(JSON.stringify(results.map(({variant,preselected_triangles,selected_far_triangle_counts})=>({variant,preselected_triangles,selected_far_triangle_counts})),null,2)+'\n');
