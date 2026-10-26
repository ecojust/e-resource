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
assert.equal(parameters.id,'songjiang-fangta-pagoda');assert.equal(record.building_id,parameters.id);
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
 const walls=[];scene.traverse(m=>{if(m.isMesh&&m.material.name==='warm white plaster')walls.push(m);});
 assert(walls.length>0,'No actual white plaster wall geometry');
 const source=geometryReport.model_square_ring_enu,ray=new THREE.Raycaster(),records=[];
 ray.near=1e-7;
 for(const v of calibration.levels){
  const ring=source.map(p=>new THREE.Vector2(p[0]*v.wall_scale,p[1]*v.wall_scale));
  for(let edge=0;edge<4;edge++){
   const a=ring[(edge+1)%4],b=ring[edge],t=b.clone().sub(a).normalize(),out=new THREE.Vector2(t.y,-t.x),center=a.clone().add(b).multiplyScalar(.5);
   const normal=enu([out.x,out.y,0]);
   const at=(u,z,d)=>enu([center.x+t.x*u+out.x*d,center.y+t.y*u+out.y*d,z]);
   const opening=geometryReport.openings.find(x=>x.level===v.level&&x.source_edge_id===edge);assert(opening);
   let rays=0,hits=0,distances=[];
   ray.far=v.wall_thickness+.25;
   const offsets=opening.type==='through-cusped-door'?[-.15,0,.15]:[0];
   for(const offset of offsets)for(const height of [.25,.5,.65]){
    ray.set(at(offset*opening.width_m,opening.bottom_m+height*opening.height_m,.1),normal.clone().negate());
    const result=ray.intersectObjects(walls,false);rays++;hits+=result.length;
    if(opening.type==='through-cusped-door')assert.equal(result.length,0,`L${v.level}/e${edge}: wall blocks through opening`);
    else {assert(result.length>0,`L${v.level}/e${edge}: blind panel lost backing`);distances.push(result[0].distance);}
   }
   const negativeZ=opening.bottom_m+opening.height_m*.5;
   ray.set(at(a.distanceTo(b)*.42,negativeZ,.1),normal.clone().negate());
   const negative=ray.intersectObjects(walls,false);assert(negative.length>0,`L${v.level}/e${edge}: solid-wall negative control missed`);
   records.push({level:v.level,source_edge:edge,type:opening.type,rays,hits,blind_first_distances_m:distances,solid_wall_negative_hits:negative.length,geographic_phase_verified:false});
  }
 }
 return records;
}

function finialHoleChecks(scene){
 const metal=[];scene.traverse(m=>{if(m.isMesh&&m.material.name==='iron finial')metal.push(m);});
 assert(metal.length>0,'No actual iron finial geometry');
 assert.equal(geometryReport.open_finial_rings.length,9);
 const ray=new THREE.Raycaster(),records=[];ray.near=1e-6;
 for(const hoop of geometryReport.open_finial_rings){
  const samples=[],half=hoop.height_m/2,margin=.08;
  ray.far=2*(half+margin);
  for(const angle of [Math.PI/8,Math.PI*5/8,Math.PI*9/8,Math.PI*13/8]){
   const innerProbe=(hoop.inner_hole_radius_m+.10)/2;
   const annulusProbe=(hoop.inner_hole_radius_m+hoop.outer_radius_m)/2;
   const cast=radius=>{
    ray.set(enu([Math.cos(angle)*radius,Math.sin(angle)*radius,hoop.center_z+half+margin]),new THREE.Vector3(0,-1,0));
    return ray.intersectObjects(metal,false);
   };
   const empty=cast(innerProbe),solid=cast(annulusProbe);
   assert.equal(empty.length,0,`Finial ring ${hoop.ring}: bounded hole ray blocked`);
   assert(solid.length>0,`Finial ring ${hoop.ring}: annulus negative control missed`);
   samples.push({angle_radians:angle,void_radius_m:innerProbe,annulus_radius_m:annulusProbe,void_hits:empty.length,annulus_hits:solid.length});
  }
  records.push({ring:hoop.ring,center_z:hoop.center_z,height_m:hoop.height_m,samples});
 }
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
 const aperture=apertureChecks(scene),finial=finialHoleChecks(scene);
 assert.equal(aperture.length,36);assert(aperture.every(x=>x.type==='through-cusped-door'&&x.hits===0));
 inventory[role]={sha256:asset.sha256,bytes:bytes.length,triangles:count,vertices,draw_calls:drawCalls,
  materials,triangleMap:triangles,bounds_glb:{min:bounds.min.toArray(),max:bounds.max.toArray()},
  normal_length_range:[minimumNormalLength,maximumNormalLength],embedded_images:0,texture_tables:0,aperture_samples:aperture,open_finial_ring_samples:finial};
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
const report={schema:'fangta-actual-decoded-package-check-v10',passed:true,
 decoder:'Actual vendored Three GLTFLoader + MeshoptDecoder; CPU only',
 package_record_sha256:sha(await fs.readFile(path.join(plan,'package/packaging-record.json'))),assets:inventory,
 web_exact_oriented_position_material_triangle_multiset:true,web_triangle_copies_compared:triangleCopies,
 maximum_web_normal_component_difference:normalMaximumComponentDifference,maximum_material_numeric_difference:maximumMaterialNumericDifference,
 normal_angle_tolerance_degrees:normalAngleToleranceDegrees,maximum_normal_angle_degrees:maximumNormalAngleDegrees,
 nonidentical_normal_triangles:nonidenticalNormalTriangles,normal_angles_above_tolerance:normalAnglesAboveTolerance,
 normal_policy_source:'Existing tools/qa/compare_model_compression.mjs used for prior accepted building packages; per-corner normals need not be byte identical.',
 normal_processing_source:'gltfpack 1.3.0 -cc -noq -km -ke; actual raw and decoded web NORMAL accessors are FLOAT32. Measured exporter normal rounding/optimization is reported separately from exact positions; no integer-normal quantization bit depth is asserted.',
 web_actual_bounds_difference_m:boundsDifference(web),lod_actual_bounds_difference_m:boundsDifference(lod),
 aperture_scope:'Each actual raw/web/LOD: 36 through doors x9 interior rays and 36 solid wall negative controls across nine levels/four model faces; nine finial rings each tested with four void and four annulus rays. Rays target the wall shell only, not legitimate separate rails/columns. Phase is explicitly estimated; this is not compass verification or complete LOD Hausdorff equivalence.',
 limitations:['No browser, native rendering, optics/material match or full geometric Hausdorff comparison of simplified LOD.','The 0-image state is intentional: original photos remain unmodified geometry references.'],
 main_candidate_changed:false};
await fs.writeFile(path.join(plan,'decoded-package-check.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,triangles:{raw:raw.triangles,web:web.triangles,lod:lod.triangles},normal_max:normalMaximumComponentDifference,lod_bounds_m:boundsDifference(lod),through_rays_per_role:324,negative_rays_per_role:36,finial_void_rays_per_role:36,finial_annulus_rays_per_role:36}));
