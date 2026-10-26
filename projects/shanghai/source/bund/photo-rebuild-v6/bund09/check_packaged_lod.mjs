/** Decode the actual packaged LOD with the viewer's Three/Meshopt code. */
import {readFile,writeFile,mkdtemp,rm} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const [projectArg,stageArg]=process.argv.slice(2);
if(!projectArg||!stageArg)throw Error('Usage: node check_packaged_lod.mjs PROJECT BUILDING_STAGE');
const project=resolve(projectArg),stage=resolve(stageArg),scratch=await mkdtemp(join(tmpdir(),'bund09-lod-check-'));
const url=name=>pathToFileURL(join(project,'vendor',name)).href;
try{
 await writeFile(join(scratch,'package.json'),' {"type":"module"}');
 for(const name of ['GLTFLoader.js','BufferGeometryUtils.js']){
  const text=(await readFile(join(project,'vendor',name),'utf8')).replaceAll("from 'three'",`from '${url('three.module.js')}'`);
  await writeFile(join(scratch,name),text);
 }
 const THREE=await import(url('three.module.js'));
 const {GLTFLoader}=await import(pathToFileURL(join(scratch,'GLTFLoader.js')).href);
 const {MeshoptDecoder}=await import(url('meshopt_decoder.module.js'));await MeshoptDecoder.ready;
 const record=JSON.parse(await readFile(join(stage,'package/packaging-record.json'),'utf8'));
 const lod=record.assets.lod,file=join(stage,'package',lod.file),bytes=await readFile(file);
 const sha=createHash('sha256').update(bytes).digest('hex');if(sha!==lod.sha256)throw Error('LOD SHA mismatch');
 const length=bytes.readUInt32LE(12),doc=JSON.parse(bytes.subarray(20,20+length).toString());
 if((doc.images||[]).length||(doc.textures||[]).length)throw Error('Photo-free LOD retained images/textures');
 const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
 const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');gltf.scene.updateMatrixWorld(true);
 const low=[Infinity,Infinity,Infinity],high=[-Infinity,-Infinity,-Infinity];let triangles=0,vertices=0;const materials=[];
 gltf.scene.traverse(mesh=>{
  if(!mesh.isMesh)return;if(Array.isArray(mesh.material)||mesh.isInstancedMesh)throw Error('Unexpected mesh kind');
  const p=mesh.geometry.getAttribute('position'),n=mesh.geometry.getAttribute('normal'),idx=mesh.geometry.index;
  if(!n)throw Error('Missing normal');triangles+=(idx?idx.count:p.count)/3;vertices+=p.count;
  for(let i=0;i<p.count;i++){
   const v=new THREE.Vector3().fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld),a=v.toArray();
   if(!a.every(Number.isFinite))throw Error('Nonfinite position');
   if(!Number.isFinite(n.getX(i))||!Number.isFinite(n.getY(i))||!Number.isFinite(n.getZ(i))||Math.hypot(n.getX(i),n.getY(i),n.getZ(i))<1e-10)throw Error('Invalid normal');
   for(let k=0;k<3;k++){low[k]=Math.min(low[k],a[k]);high[k]=Math.max(high[k],a[k]);}
  }
  const m=mesh.material;if(m.name.startsWith('PhotoFacade_')){
   const color=m.color.toArray();if(m.map||color.some((x,i)=>Math.abs(x-[.26,.30,.31][i])>1e-6)||Math.abs(m.roughness-.32)>1e-6||Math.abs(m.metalness-.1)>1e-6)throw Error('LOD glass fallback differs');
   materials.push({name:m.name,map:null,color_linear:color,roughness:m.roughness,metalness:m.metalness});
  }
 });
 if(triangles!==lod.triangles||materials.length!==1)throw Error('Decoded count/material mismatch');
 const rawBounds=JSON.parse(await readFile(join(stage,'output/photo-uv-check.json'),'utf8')).bounds_glb;
 const delta=Math.max(...low.map((x,i)=>Math.abs(x-rawBounds.min[i])),...high.map((x,i)=>Math.abs(x-rawBounds.max[i])));
 if(delta>=.35)throw Error('Actual decoded LOD bounds exceeded limit');
 const report={schema:'bund09-actual-lod-decode-v1',passed:true,decoder:'Vendored viewer Three GLTFLoader and MeshoptDecoder',file,sha256:sha,bytes:bytes.length,triangles,vertices,actual_decoded_bounds_glb:{min:low,max:high},maximum_actual_bounds_change_m:delta,embedded_images:0,texture_tables:0,decoded_photo_fallback_materials:materials,scope:'Actual CPU geometry decode and material construction; no browser rendering, lighting or performance acceptance.'};
 await writeFile(join(stage,'package/lod-decoded-check.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
}finally{await rm(scratch,{recursive:true,force:true});}
