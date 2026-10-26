/** Actual vendored Three/Meshopt decode, immutable old + appended street geometry. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
const [project,stage]=process.argv.slice(2);assert(project&&stage,'Usage: node verify_street_web.mjs PROJECT STAGE');
const url=p=>pathToFileURL(path.join(project,p)).href;
const hooks=registerHooks({resolve(s,c,next){return s==='three'?{url:url('vendor/three.module.js'),shortCircuit:true}:next(s,c);}});
const {GLTFLoader}=await import(url('vendor/GLTFLoader.js'));hooks.deregister();
const THREE=await import(url('vendor/three.module.js'));
const {MeshoptDecoder}=await import(url('vendor/meshopt_decoder.module.js'));
const {disposeModelResources}=await import(url('src/model-resources.js'));
const {StreetInteraction}=await import(url('src/street-interaction.js'));
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder),sha=b=>createHash('sha256').update(b).digest('hex');
function key(triangle,material){
 const points=triangle.map(v=>{const b=Buffer.alloc(24);v.forEach((x,i)=>b.writeDoubleLE(Object.is(x,-0)?0:x,i*8));return b.toString('hex')});
 return material+'|'+points.map((_,i)=>[points[i],points[(i+1)%3],points[(i+2)%3]].join('')).sort()[0];
}
async function inventory(file){
 const bytes=await fs.readFile(file),object=(await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')).scene;
 object.updateWorldMatrix(true,true);const triangles=new Map(),materials=new Map();let count=0;
 const p=new THREE.Vector3();
 object.traverse(mesh=>{
  if(!mesh.isMesh)return;assert(!mesh.isInstancedMesh,'Unexpected instanced street output');
  const g=mesh.geometry,index=g.index,groups=g.groups.length?g.groups:[{start:0,count:index?.count??g.attributes.position.count,materialIndex:0}];
  for(const group of groups){const material=Array.isArray(mesh.material)?mesh.material[group.materialIndex]:mesh.material;
   materials.set(material.name,{color:material.color.toArray(),roughness:material.roughness,metalness:material.metalness,opacity:material.opacity,side:material.side});
   for(let i=group.start;i<group.start+group.count;i+=3){const points=[];
    for(let j=0;j<3;j++){p.fromBufferAttribute(g.attributes.position,index?index.getX(i+j):i+j).applyMatrix4(mesh.matrixWorld);points.push(p.toArray())}
    const k=key(points,material.name);triangles.set(k,(triangles.get(k)||0)+1);count++;
   }
  }
 });disposeModelResources(object);return {sha256:sha(bytes),bytes:bytes.length,triangles,materials,count};
}
const old=await inventory(path.join(stage,'inputs/assets/models/bund/web/bund-streets.glb'));
const raw=await inventory(path.join(stage,'output/bund-streets.glb'));
const web=await inventory(path.join(stage,'output/bund-streets-web.glb'));
const f32Materials=map=>new Map([...map].map(([name,p])=>[name,{...p,color:p.color.map(Math.fround),roughness:Math.fround(p.roughness),metalness:Math.fround(p.metalness)}]));
assert.equal(raw.count,web.count);assert.deepEqual(f32Materials(raw.materials),f32Materials(web.materials));assert.deepEqual(old.materials,web.materials);
let rawMissing=0,rawExtra=0,oldMissing=0;
for(const [k,n] of raw.triangles)rawMissing+=Math.max(0,n-(web.triangles.get(k)||0));
for(const [k,n] of web.triangles)rawExtra+=Math.max(0,n-(raw.triangles.get(k)||0));
for(const [k,n] of old.triangles)oldMissing+=Math.max(0,n-(web.triangles.get(k)||0));
assert.equal(rawMissing+rawExtra,0,'New web lost/changed raw positions, winding or material');assert.equal(oldMissing,0,'New web changed old street geometry');
const sidecar=JSON.parse(await fs.readFile(path.join(stage,'output/street-interaction-v5.json'))),oldSidecar=JSON.parse(await fs.readFile(path.join(stage,'inputs/data/bund/street-interaction-v5.json')));
assert.deepEqual(sidecar.features.slice(0,oldSidecar.features.length),oldSidecar.features);assert.deepEqual(sidecar.local_obstacles,oldSidecar.local_obstacles);
assert.equal(sidecar.raw_model_sha256,raw.sha256);assert.equal(sidecar.web_model_sha256,web.sha256);
const interaction=new StreetInteraction();assert(interaction.setOwner('bund-streets',sidecar,{modelSha256:web.sha256,active:true}));
const probes=JSON.parse(await fs.readFile(path.join(stage,'output/support-probes.json'))),support=[];
for(const f of sidecar.features.slice(oldSidecar.features.length)){
 const point=probes.find(p=>p.id===f.properties.id)?.point;assert(point,'Missing guaranteed-interior support probe');
 const sample=interaction.groundAt(...point);assert.equal(sample?.id,f.properties.id);assert.equal(sample.height,.075);
 support.push({id:f.properties.id,found:{point,sample}});
}
interaction.setOwnerActive('bund-streets',false);
for(const s of support)if(s.found)assert.equal(interaction.groundAt(...s.found.point),null,'Hidden street still supplies ground');
const result={schema:'street-frontage-actual-web-audit-v1',passed:true,old_web_sha256:old.sha256,new_raw_sha256:raw.sha256,new_web_sha256:web.sha256,
 old_triangles:old.count,new_triangles:web.count,added_triangles:web.count-old.count,old_materials_unchanged:true,
 actual_decoded_positions_float64_winding_material_multiset_exact:true,old_triangles_missing:oldMissing,new_raw_missing:rawMissing,new_raw_extra:rawExtra,
 sidecar_old_features_unchanged:oldSidecar.features.length,sidecar_old_obstacles_unchanged:oldSidecar.local_obstacles.length,support_samples:support,
 scope:'Actual production Three/Meshopt geometry decode plus real StreetInteraction, no browser or scene changes. Normal bit identity is not asserted.'};
await fs.writeFile(path.join(stage,'output/web-validation.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({passed:result.passed,oldTriangles:old.count,newTriangles:web.count,oldMissing,rawMissing,rawExtra,support}));
