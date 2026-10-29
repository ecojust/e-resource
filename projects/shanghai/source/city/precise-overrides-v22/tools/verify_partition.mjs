/** Actual production Three/Meshopt decode; no browser, original assets read-only. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
const project=path.resolve(process.argv[2]),baselineFile=process.argv[3],partitionFile=process.argv[4],output=process.argv[5];
const url=p=>pathToFileURL(path.join(project,p)).href;
const hooks=registerHooks({resolve(s,c,next){return s==='three'?{url:url('vendor/three.module.js'),shortCircuit:true}:next(s,c);}});
const {GLTFLoader}=await import(url('vendor/GLTFLoader.js'));hooks.deregister();
const THREE=await import(url('vendor/three.module.js'));
const {MeshoptDecoder}=await import(url('vendor/meshopt_decoder.module.js'));
const {disposeModelResources,countExpandedTriangles}=await import(url('src/model-resources.js'));
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const sha=b=>createHash('sha256').update(b).digest('hex');
async function load(file){let b=await fs.readFile(file);if(file.endsWith('.gz'))b=gunzipSync(b);return (await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;}
const matrix=new THREE.Matrix4(),instance=new THREE.Matrix4(),v=new THREE.Vector3(),normalMatrix=new THREE.Matrix3(),normal=new THREE.Vector3();
function triangles(root){
 root.updateWorldMatrix(true,true);const result=[];
 root.traverse(mesh=>{
  if(!mesh.isMesh)return;const g=mesh.geometry,p=g.attributes.position,n=g.attributes.normal,index=g.index;
  const groups=g.groups.length?g.groups:[{start:0,count:index?.count??p.count,materialIndex:0}];
  for(let instanceIndex=0;instanceIndex<(mesh.isInstancedMesh?mesh.count:1);instanceIndex++){
   matrix.copy(mesh.matrixWorld);if(mesh.isInstancedMesh){mesh.getMatrixAt(instanceIndex,instance);matrix.multiply(instance);}normalMatrix.getNormalMatrix(matrix);
   for(const group of groups){const material=Array.isArray(mesh.material)?mesh.material[group.materialIndex]:mesh.material;
    for(let i=group.start;i<group.start+group.count;i+=3){const vertices=[];
     for(let j=0;j<3;j++){const vertex=index?index.getX(i+j):i+j;v.fromBufferAttribute(p,vertex).applyMatrix4(matrix);normal.fromBufferAttribute(n,vertex).applyMatrix3(normalMatrix).normalize();vertices.push({p:[v.x,v.y,v.z],n:[normal.x,normal.y,normal.z]});}
     result.push({material:material.name,vertices});
    }
   }
  }
 });return result;
}
function key(tri,{normal=false,f32=false}={}){
 const vertices=tri.vertices.map(v=>{
  const values=normal?[...v.p,...v.n]:v.p,b=Buffer.alloc(values.length*(f32?4:8));
  values.forEach((x,i)=>f32?b.writeFloatLE(Object.is(x,-0)?0:x,i*4):b.writeDoubleLE(Object.is(x,-0)?0:x,i*8));return b.toString('hex');
 });
 // Preserve winding, ignore only a harmless cyclic starting-index change.
 const cycle=[vertices.join(''),[vertices[1],vertices[2],vertices[0]].join(''),[vertices[2],vertices[0],vertices[1]].join('')].sort()[0];return tri.material+'|'+cycle;
}
function inventory(rows,options={}){const m=new Map();for(const tri of rows){const k=key(tri,options);m.set(k,(m.get(k)||0)+1);}return m;}
function difference(expected,actual){let missing=0,extra=0;for(const[k,v]of expected)missing+=Math.max(0,v-(actual.get(k)||0));for(const[k,v]of actual)extra+=Math.max(0,v-(expected.get(k)||0));return {missing,extra};}
function equal(expected,actual,options){const diff=difference(inventory(expected,options),inventory(actual,options));return {...diff,pass:diff.missing===0&&diff.extra===0};}
const NORMAL_COMPONENT_LIMIT=1e-7,NORMAL_ANGLE_LIMIT_DEGREES=1e-5;
function oriented(tri){
 const pos=tri.vertices.map(v=>{const b=Buffer.alloc(24);v.p.forEach((x,i)=>b.writeDoubleLE(Object.is(x,-0)?0:x,i*8));return b.toString('hex')});
 const cycles=pos.map((_,i)=>({i,key:[pos[i],pos[(i+1)%3],pos[(i+2)%3]].join('')})).sort((a,b)=>a.key.localeCompare(b.key));
 const i=cycles[0].i;return {key:tri.material+'|'+cycles[0].key,n:[tri.vertices[i].n,tri.vertices[(i+1)%3].n,tri.vertices[(i+2)%3].n]};
}
function normalDirections(expectedRows,actualRows){
 const expected=new Map();for(const row of expectedRows){const o=oriented(row);if(!expected.has(o.key))expected.set(o.key,[]);expected.get(o.key).push(o.n)}
 let maxComponent=0,maxAngle=0,nonidentical=0,compared=0,missing=0;
 for(const row of actualRows){
  const o=oriented(row),list=expected.get(o.key);if(!list?.length){missing++;continue;}
  const errors=list.map(ns=>Math.max(...ns.flatMap((n,j)=>n.map((x,k)=>Math.abs(x-o.n[j][k])))));
  const best=errors.indexOf(Math.min(...errors)),norms=list.splice(best,1)[0],err=errors[best];
  if(err)nonidentical++;maxComponent=Math.max(maxComponent,err);
  for(let i=0;i<3;i++){const a=new THREE.Vector3(...norms[i]),b=new THREE.Vector3(...o.n[i]);
   maxAngle=Math.max(maxAngle,Math.atan2(new THREE.Vector3().crossVectors(a,b).length(),a.dot(b))*180/Math.PI)}
  compared++;
 }
 const remaining=[...expected.values()].reduce((n,v)=>n+v.length,0);
 return {compared_triangles:compared,nonidentical_normal_triangles:nonidentical,missing_geometry:missing,remaining_geometry:remaining,
  max_component_difference:maxComponent,max_direction_difference_degrees:maxAngle,
  component_limit:NORMAL_COMPONENT_LIMIT,direction_limit_degrees:NORMAL_ANGLE_LIMIT_DEGREES,
  pass:!missing&&!remaining&&maxComponent<=NORMAL_COMPONENT_LIMIT&&maxAngle<=NORMAL_ANGLE_LIMIT_DEGREES};
}
const base=await load(baselineFile),variant=await load(partitionFile);
const before=triangles(base),after=triangles(variant);
const report={baseline_sha256:sha(await fs.readFile(baselineFile)),partition_sha256:sha(await fs.readFile(partitionFile)),triangles:before.length,position_material_winding:equal(before,after),position_normal_material_winding:equal(before,after,{normal:true}),groups:[]};
for(const node of variant.children){report.groups.push({name:node.name,extras:node.userData,triangles:triangles(node).length});}
assert(report.position_material_winding.pass && report.position_normal_material_winding.pass);
assert.ok(report.groups.length>=2);assert.equal(report.groups.filter(g=>g.extras.cityReplacement).length,1);
const owner=report.groups.find(g=>g.extras.cityReplacement);assert.deepEqual(owner.extras.cityReplacement.local_ids,[Number(process.argv[6]||1595)]);
const removed=variant.children.find(n=>n.userData.cityPreservedLocalIds);variant.remove(removed);
report.negative_removed_neighbor_rejected=!equal(before,triangles(variant)).pass;assert(report.negative_removed_neighbor_rejected);
await fs.writeFile(output,JSON.stringify(report,null,2)+'\n');console.log('PASS exact decoded positions, normals, materials, winding and neighbor removal negative control');
