/** Actual viewer CPU decode and bounded aperture checks; no browser/renderer. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';

const [projectArg,planArg,modelArg]=process.argv.slice(2);
assert(projectArg&&planArg&&modelArg,'Usage: node check_decoded_package.mjs PROJECT PACKAGE_PLAN MODEL_SOURCE');
const project=path.resolve(projectArg),plan=path.resolve(planArg),model=path.resolve(modelArg);
const url=p=>pathToFileURL(path.join(project,p)).href;
const hook=registerHooks({resolve(s,c,next){return s==='three'?{url:url('vendor/three.module.js'),shortCircuit:true}:next(s,c);}});
const THREE=await import(url('vendor/three.module.js'));
const {GLTFLoader}=await import(url('vendor/GLTFLoader.js'));hook.deregister();
const {MeshoptDecoder}=await import(url('vendor/meshopt_decoder.module.js'));
const {disposeModelResources}=await import(url('src/model-resources.js'));
await MeshoptDecoder.ready;
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const sha=b=>createHash('sha256').update(b).digest('hex');
const record=JSON.parse(await fs.readFile(path.join(plan,'package/packaging-record.json')));
const parameters=JSON.parse(await fs.readFile(path.join(model,'geometry-input.json')));
const enu=v=>new THREE.Vector3(v[0],v[2],-v[1]);
const inventory={};

function triangleKey(points,name){
 const enc=points.map(v=>{const b=Buffer.alloc(24);v.forEach((x,i)=>b.writeDoubleLE(Object.is(x,-0)?0:x,i*8));return b.toString('hex');});
 const rotations=enc.map((_,i)=>[enc[i],enc[(i+1)%3],enc[(i+2)%3]].join(''));
 const rotation=rotations.indexOf([...rotations].sort()[0]);
 return {key:name+'|'+rotations[rotation],rotation};
}

function apertureChecks(scene){
 const walls=[],all=[];scene.traverse(m=>{if(m.isMesh){all.push(m);if(m.material.name.startsWith('grey brick'))walls.push(m);}});
 assert(walls.length>0,'No actual masonry geometry');
 const ray=new THREE.Raycaster();ray.near=1e-8;ray.far=.80;
 const edge=parameters.front_edge,W=edge.length_m;
 const origin=enu([...edge.center_local_east_north_m,0]);
 const tangent=enu([-edge.tangent_east_north[0],-edge.tangent_east_north[1],0]);
 const normal=enu([...edge.outward_normal_east_north,0]).normalize();
 const records=[];
 const sample=(label,u,heights,halfwidth,depth=0)=>{
  let count=0;
  for(const dx of [-halfwidth,0,halfwidth])for(const z of heights){
   const point=origin.clone().addScaledVector(tangent,u+dx).addScaledVector(normal,.20-depth);point.y=z;
   ray.set(point,normal.clone().negate());assert.equal(ray.intersectObjects(walls,false).length,0,label+' masonry blocks opening');count++;
  }
  records.push({label,masonry_interior_rays:count,hits:0});
 };
 sample('entry-arch',0,[1.0,2.0,3.3],.4);
 for(const [i,u] of [-2,0,2].entries())sample('middle-window-'+i,u,[6.35,7.35,8.5],.30);
 for(const [i,u] of [-1.22,0,1.22].entries())sample('upper-window-'+i,u,[10.9,11.5,12.0],.15);
 for(const side of [-1,1]){
  const u=side*(7.25/2+(W/2-7.25/2)*.54);
  sample('wing-arched-window-'+side,u,[1.0,2.3,3.2],.30,1.15);
  sample('wing-round-window-'+side,u,[4.87,5.12,5.37],.25,1.15);
 }
 const p=origin.clone().addScaledVector(tangent,3.10).addScaledVector(normal,.20);p.y=5.0;
 ray.set(p,normal.clone().negate());const hit=ray.intersectObjects(walls,false).length;assert(hit>0,'Adjacent masonry negative control missed');
 records.push({label:'adjacent-masonry-negative-control',hits:hit});
 const entry=origin.clone().addScaledVector(normal,.20);entry.y=2;
 ray.far=1.7;ray.set(entry,normal.clone().negate());assert.equal(ray.intersectObjects(all,false).length,0,'Entry opening blocked before inner room');
 records.push({label:'actual-open-entry',all_geometry_hits:0});
 return records;
}

for(const role of ['raw','web','lod']){
 const asset=record.assets[role],file=path.join(plan,'package',asset.file),bytes=await fs.readFile(file);
 assert.equal(bytes.length,asset.bytes);assert.equal(sha(bytes),asset.sha256);assert(bytes.length<100_000_000);
 assert.equal(bytes.readUInt32LE(0),0x46546c67);assert.equal(bytes.readUInt32LE(4),2);assert.equal(bytes.readUInt32LE(8),bytes.length);
 const n=bytes.readUInt32LE(12),doc=JSON.parse(bytes.subarray(20,20+n));
 assert.equal((doc.images||[]).length,0);assert.equal((doc.textures||[]).length,0);
 assert((doc.buffers||[]).every(x=>!('uri'in x)));
 const scene=(await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')).scene;
 scene.updateWorldMatrix(true,true);
 const triangles=new Map(),materials=new Map(),bounds=new THREE.Box3(),p=new THREE.Vector3(),normal=new THREE.Vector3();
 let count=0,vertices=0,minimumNormalLength=Infinity,maximumNormalLength=0,drawCalls=0;
 scene.traverse(mesh=>{
  if(!mesh.isMesh)return;assert(!mesh.isInstancedMesh,'Unexpected instanced model');assert(!Array.isArray(mesh.material),'Unexpected material array');
  const g=mesh.geometry,index=g.index,positions=g.getAttribute('position'),normals=g.getAttribute('normal');
  assert(positions&&normals);assert(!g.getAttribute('uv'),'Unexpected UVs in explicitly untextured model');
  const m=mesh.material,nm=new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld);assert(!m.map&&!m.normalMap&&!m.roughnessMap);
  materials.set(m.name,{color:m.color.toArray(),roughness:m.roughness,metalness:m.metalness,opacity:m.opacity,side:m.side});drawCalls++;
  vertices+=positions.count;
  for(let i=0;i<positions.count;i++){
   p.fromBufferAttribute(positions,i).applyMatrix4(mesh.matrixWorld);assert(p.toArray().every(Number.isFinite));bounds.expandByPoint(p);
   normal.fromBufferAttribute(normals,i);const len=normal.length();assert(Number.isFinite(len)&&len>.99&&len<1.01);
   minimumNormalLength=Math.min(minimumNormalLength,len);maximumNormalLength=Math.max(maximumNormalLength,len);
  }
  const total=index?index.count:positions.count;assert.equal(total%3,0);count+=total/3;
  if(role!=='lod')for(let i=0;i<total;i+=3){
   const points=[],nn=[];
   for(let k=0;k<3;k++){
    const j=index?index.getX(i+k):i+k;
    points.push(p.fromBufferAttribute(positions,j).applyMatrix4(mesh.matrixWorld).toArray());
    nn.push(normal.fromBufferAttribute(normals,j).applyMatrix3(nm).normalize().toArray());
   }
   const {key,rotation}=triangleKey(points,m.name),values=[0,1,2].flatMap(k=>nn[(k+rotation)%3]);
   if(!triangles.has(key))triangles.set(key,[]);triangles.get(key).push(values);
  }
 });
 assert.equal(count,asset.triangles);
 const aperture=apertureChecks(scene);
 inventory[role]={sha256:asset.sha256,bytes:bytes.length,triangles:count,vertices,draw_calls:drawCalls,
  materials,triangleMap:triangles,bounds_glb:{min:bounds.min.toArray(),max:bounds.max.toArray()},
  normal_length_range:[minimumNormalLength,maximumNormalLength],embedded_images:0,texture_tables:0,aperture_samples:aperture};
 disposeModelResources(scene);
}
const raw=inventory.raw,web=inventory.web,lod=inventory.lod;
assert.deepEqual([...raw.materials.keys()].sort(),[...web.materials.keys()].sort());
assert.deepEqual([...raw.materials.keys()].sort(),[...lod.materials.keys()].sort());
let normalMaximumComponentDifference=0,maximumNormalAngleDegrees=0,triangleCopies=0,nonidenticalNormalTriangles=0,normalAnglesAboveTolerance=0;
const normalAngleToleranceDegrees=.05;
assert.equal(raw.triangleMap.size,web.triangleMap.size,'Triangle/material/winding key set differs');
for(const [key,rawCopies] of raw.triangleMap){
 const webCopies=web.triangleMap.get(key);assert(webCopies&&webCopies.length===rawCopies.length,'Triangle multiplicity differs');
 const remaining=[...webCopies];
 for(const a of rawCopies){
  let best=-1,error=Infinity;
  for(let i=0;i<remaining.length;i++){
   const e=Math.max(...a.map((x,k)=>Math.abs(x-remaining[i][k])));if(e<error){best=i;error=e;}
  }
  const b=remaining.splice(best,1)[0];
  if(error)nonidenticalNormalTriangles++;
  for(let corner=0;corner<3;corner++){
   const aa=new THREE.Vector3(...a.slice(corner*3,corner*3+3)),bb=new THREE.Vector3(...b.slice(corner*3,corner*3+3));
   const angle=Math.atan2(new THREE.Vector3().crossVectors(aa,bb).length(),aa.dot(bb))*180/Math.PI;
   maximumNormalAngleDegrees=Math.max(maximumNormalAngleDegrees,angle);
   if(angle>normalAngleToleranceDegrees)normalAnglesAboveTolerance++;
  }
  normalMaximumComponentDifference=Math.max(normalMaximumComponentDifference,error);triangleCopies++;
 }
}
assert.equal(triangleCopies,raw.triangles);
assert.equal(normalAnglesAboveTolerance,0,'Exporter normal drift exceeds existing 0.05 degree policy');
let maximumMaterialNumericDifference=0;
for(const [name,a] of raw.materials)for(const role of ['web','lod']){
 const b=inventory[role].materials.get(name);assert.equal(a.side,b.side);
 const aa=[...a.color,a.roughness,a.metalness,a.opacity],bb=[...b.color,b.roughness,b.metalness,b.opacity];
 const difference=Math.max(...aa.map((v,i)=>Math.abs(v-bb[i])));assert(difference<1e-6);
 maximumMaterialNumericDifference=Math.max(maximumMaterialNumericDifference,difference);
}
const boundsDifference=b=>Math.max(...raw.bounds_glb.min.map((v,i)=>Math.abs(v-b.bounds_glb.min[i])),...raw.bounds_glb.max.map((v,i)=>Math.abs(v-b.bounds_glb.max[i])));
assert(boundsDifference(web)<=.0001);assert(boundsDifference(lod)<.35);
for(const role of ['raw','web','lod']){
 inventory[role].materials=Object.fromEntries(inventory[role].materials);delete inventory[role].triangleMap;
}
const report={schema:'hongde-v2-actual-decoded-package-check-v8',passed:true,
 decoder:'Actual vendored Three GLTFLoader + MeshoptDecoder; CPU only',
 package_record_sha256:sha(await fs.readFile(path.join(plan,'package/packaging-record.json'))),assets:inventory,
 web_exact_oriented_position_material_triangle_multiset:true,web_triangle_copies_compared:triangleCopies,
 maximum_web_normal_component_difference:normalMaximumComponentDifference,maximum_material_numeric_difference:maximumMaterialNumericDifference,
 normal_angle_tolerance_degrees:normalAngleToleranceDegrees,maximum_normal_angle_degrees:maximumNormalAngleDegrees,
 nonidentical_normal_triangles:nonidenticalNormalTriangles,normal_angles_above_tolerance:normalAnglesAboveTolerance,
 normal_policy_source:'Existing tools/qa/compare_model_compression.mjs used for prior accepted building packages; per-corner normals need not be byte identical.',
 normal_processing_source:'gltfpack 1.3.0 -cc -noq -km -ke; actual raw and decoded web NORMAL accessors are FLOAT32. Measured exporter normal rounding/optimization is reported separately from exact positions; no integer-normal quantization bit depth is asserted.',
 web_actual_bounds_difference_m:boundsDifference(web),lod_actual_bounds_difference_m:boundsDifference(lod),
 aperture_scope:'Each raw/web/LOD has99 masonry interior rays over11 real facade openings,1 adjacent masonry negative control and1 full-scene open-entry ray. This does not prove every curved boundary or complete LOD Hausdorff equivalence.',
 limitations:['No browser, native rendering, optics/material match or full geometric Hausdorff comparison of simplified LOD.','The 0-image state is intentional: original photos remain unmodified geometry references.'],
 main_candidate_changed:false};
await fs.writeFile(path.join(plan,'decoded-package-check.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,triangles:{raw:raw.triangles,web:web.triangles,lod:lod.triangles},normal_max:normalMaximumComponentDifference,lod_bounds_m:boundsDifference(lod),opening_rays:3*11*9}));
