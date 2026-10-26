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
const calibration=JSON.parse(await fs.readFile(path.join(model,'calibration.json')));
const geometryReport=JSON.parse(await fs.readFile(path.join(plan,'raw/geometry-report.json')));
const rawMetadata=JSON.parse(await fs.readFile(path.join(plan,'raw/asset-metadata.json')));
assert.equal(parameters.id,'putuo-zhenru-main-hall');assert.equal(record.building_id,parameters.id);
assert.equal(rawMetadata.raw.sha256,record.assets.raw.sha256);
assert.equal(geometryReport.source_geometry_sha256,sha(await fs.readFile(path.join(model,'geometry-input.json'))));
assert.equal(calibration.source_geometry_sha256,geometryReport.source_geometry_sha256);
assert.equal(geometryReport.calibration_sha256,sha(await fs.readFile(path.join(model,'calibration.json'))));
const enu=v=>new THREE.Vector3(v[0],v[2],-v[1]);
const inventory={};

function triangleKey(points,name){
 const enc=points.map(v=>{const b=Buffer.alloc(24);v.forEach((x,i)=>b.writeDoubleLE(Object.is(x,-0)?0:x,i*8));return b.toString('hex');});
 const rotations=enc.map((_,i)=>[enc[i],enc[(i+1)%3],enc[(i+2)%3]].join(''));
 const rotation=rotations.indexOf([...rotations].sort()[0]);
 return {key:name+'|'+rotations[rotation],rotation};
}

function apertureChecks(scene){
 const byMaterial=name=>{const result=[];scene.traverse(m=>{if(m.isMesh&&m.material.name===name)result.push(m);});assert(result.length>0,`Missing ${name}`);return result;};
 const timber=byMaterial('aged dark timber'),white=byMaterial('white lime infill'),doors=byMaterial('door timber'),grilles=byMaterial('worn timber edge');
 const ray=new THREE.Raycaster();ray.near=1e-6;
 const angle=calibration.orientation.model_x_axis_degrees_ccw_from_east*Math.PI/180;
 const tangent=new THREE.Vector3(Math.cos(angle),Math.sin(angle),0),up=new THREE.Vector3(0,0,1);
 const outward=new THREE.Vector3(Math.sin(angle),-Math.cos(angle),0);
 const records=[],wallRecords=[];
 const cast=(objects,origin,direction,far)=>{ray.far=far;ray.set(enu(origin.toArray()),enu(direction.toArray()).normalize());return ray.intersectObjects(objects,false);};
 const leaves=geometryReport.openings.filter(x=>x.kind==='door_leaf_lattice');assert.equal(leaves.length,12);
 for(const leaf of leaves){
  const sign=leaf.label.startsWith('south/')?1:-1,a=leaf.angle_degrees*Math.PI/180;
  const along=tangent.clone().multiplyScalar(sign*Math.cos(a)).addScaledVector(outward,sign*Math.sin(a));
  const normal=new THREE.Vector3().crossVectors(along,up).normalize(),hinge=new THREE.Vector3(...leaf.hinge_enu);
  const at=(u,z,d)=>hinge.clone().addScaledVector(along,u).addScaledVector(up,z).addScaledVector(normal,d);
  const bottom=calibration.estimated.door_bottom_z_m,top=calibration.estimated.door_top_z_m;
  let rays=0,hits=0;
  for(const column of [0,2,4])for(const row of [2,7,12]){
   const u=.065+(leaf.width_m-.13)*(column+.5)/5,z=bottom+.64+(top-bottom-.75)*(row+.5)/15;
   const result=cast(doors,at(u,z,.075),normal.clone().negate(),.15);rays++;hits+=result.length;
   assert.equal(result.length,0,`${leaf.label}: lattice cell blocked`);
  }
  const negative=cast(doors,at(.033,(bottom+top)/2,.075),normal.clone().negate(),.15);
  assert(negative.length>0,`${leaf.label}: timber stile negative control missed`);
  records.push({type:'door-leaf-lattice',label:leaf.label,rays,hits,solid_stile_negative_hits:negative.length,configuration_measured:false});
 }
 const windows=geometryReport.openings.filter(x=>x.kind==='through_flame_window');assert.equal(windows.length,2);
 for(const window of windows){
  const center=new THREE.Vector3(...window.wall_only_ray_point_enu),inward=new THREE.Vector3(...window.inward_direction_enu);
  const at=(u,z)=>center.clone().addScaledVector(tangent,u-window.center_u).setZ(z);
  let rays=0,hits=0,latticeVoidHits=0,barNegativeHits=0;
  for(const fraction of [-.2,0,.2])for(const height of [.25,.4,.55]){
   const result=cast(timber,at(window.center_u+fraction*window.width_m,window.bottom_z_m+(window.top_z_m-window.bottom_z_m)*height),inward,.65);rays++;hits+=result.length;
   assert.equal(result.length,0,'South flame window is blocked by wall timber');
  }
  const x0=window.center_u-window.width_m/2,z=window.bottom_z_m+.45*(window.top_z_m-window.bottom_z_m);
  for(const bar of [2,6,10]){
   const solid=cast(grilles,at(x0+.12+bar*.135,z),inward,.30);
   const empty=cast(grilles,at(x0+.12+(bar+.5)*.135,z),inward,.30);
   assert(solid.length>0,'Flame window straight-bar negative control missed');assert.equal(empty.length,0,'Flame window real lattice gap blocked');
   barNegativeHits+=solid.length;latticeVoidHits+=empty.length;
  }
  const solidWall=cast(timber,at(window.center_u,.9),inward,.65);assert(solidWall.length>0,'Flame window wall negative control missed');
  records.push({type:'through-flame-window',center_u:window.center_u,rays,hits,lattice_void_rays:3,lattice_void_hits:latticeVoidHits,bar_negative_rays:3,bar_negative_hits:barNegativeHits,solid_wall_negative_hits:solidWall.length});
 }
 for(const opening of geometryReport.openings.filter(x=>x.kind==='through_door_wall')){
  const center=new THREE.Vector3(...opening.wall_only_ray_point_enu),inward=new THREE.Vector3(...opening.inward_direction_enu),walls=opening.edge===0?timber:white;
  let hits=0,rays=0;
  for(const offset of [-.7,0,.7])for(const height of [1.6,2.1,2.7]){
   const result=cast(walls,center.clone().addScaledVector(tangent,offset).setZ(height),inward,.65);rays++;hits+=result.length;assert.equal(result.length,0,'Central six-leaf opening wall is blocked');
  }
  const negative=cast(walls,center.clone().addScaledVector(tangent,5.9).setZ(2.1),inward,.65);assert(negative.length>0,'Central opening solid-wall negative control missed');
  wallRecords.push({type:'central-six-leaf-wall-opening',edge:opening.edge,rays,hits,solid_wall_negative_hits:negative.length});
 }
 assert.equal(wallRecords.length,2);return {apertures:records,centralWalls:wallRecords};
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
 const checks=apertureChecks(scene),aperture=checks.apertures;
 assert.equal(aperture.length,14);assert(aperture.every(x=>x.hits===0));
 inventory[role]={sha256:asset.sha256,bytes:bytes.length,triangles:count,vertices,draw_calls:drawCalls,
  materials,triangleMap:triangles,bounds_glb:{min:bounds.min.toArray(),max:bounds.max.toArray()},
  normal_length_range:[minimumNormalLength,maximumNormalLength],embedded_images:0,texture_tables:0,aperture_samples:aperture,central_wall_aperture_samples:checks.centralWalls};
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
const report={schema:'zhenru-actual-decoded-package-check-v10',passed:true,
 decoder:'Actual vendored Three GLTFLoader + MeshoptDecoder; CPU only',
 package_record_sha256:sha(await fs.readFile(path.join(plan,'package/packaging-record.json'))),assets:inventory,
 web_exact_oriented_position_material_triangle_multiset:true,web_triangle_copies_compared:triangleCopies,
 maximum_web_normal_component_difference:normalMaximumComponentDifference,maximum_material_numeric_difference:maximumMaterialNumericDifference,
 normal_angle_tolerance_degrees:normalAngleToleranceDegrees,maximum_normal_angle_degrees:maximumNormalAngleDegrees,
 nonidentical_normal_triangles:nonidenticalNormalTriangles,normal_angles_above_tolerance:normalAnglesAboveTolerance,
 normal_policy_source:'Existing tools/qa/compare_model_compression.mjs used for prior accepted building packages; per-corner normals need not be byte identical.',
 normal_processing_source:'gltfpack 1.3.0 -cc -noq -km -ke; actual raw and decoded web NORMAL accessors are FLOAT32. Measured exporter normal rounding/optimization is reported separately from exact positions; no integer-normal quantization bit depth is asserted.',
 web_actual_bounds_difference_m:boundsDifference(web),lod_actual_bounds_difference_m:boundsDifference(lod),
 aperture_scope:'Each actual raw/web/LOD:12 door leaves x9 real lattice-cell rays plus12 stile negative controls;2 flame windows x9 wall rays plus6 grille-gap and6 grille-bar rays;2 central wall openings x9 rays and2 solid-wall negative controls. Bounded material-role checks; no whole-assembly collision freedom or complete LOD Hausdorff equivalence.',
 limitations:['No browser, native rendering, optics/material match or full geometric Hausdorff comparison of simplified LOD.','The 0-image state is intentional: original photos remain unmodified geometry references.'],
 main_candidate_changed:false};
await fs.writeFile(path.join(plan,'decoded-package-check.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,triangles:{raw:raw.triangles,web:web.triangles,lod:lod.triangles},normal_max:normalMaximumComponentDifference,lod_bounds_m:boundsDifference(lod),door_leaves_per_role:12,flame_windows_per_role:2,door_lattice_void_rays_per_role:108,window_lattice_void_rays_per_role:6,central_wall_void_rays_per_role:18}));
