/** Actual production Three/Meshopt decode; no browser, original assets read-only. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
const input=process.argv[2];if(!input)throw Error('Usage: node verify_override_geometry.mjs geometry-comparison-input.json');
const spec=JSON.parse(await fs.readFile(input)),project=spec.project;
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
const report={schema:'city-precise-geometry-comparison-v1',pass:false,codec:'Vendored Three GLTFLoader + MeshoptDecoder; actual instance matrices and material names',checks:[]};
for(const item of spec.checks){
 assert.equal(sha(await fs.readFile(item.baseline)),item.baseline_sha256,'Frozen original near bytes changed');
 const baseline=await load(item.baseline),variant=await load(item.override),baseRows=triangles(baseline),variantRows=triangles(variant);
 const result={id:item.id,baseline_sha256:sha(await fs.readFile(item.baseline)),override_sha256:sha(await fs.readFile(item.override)),triangles:baseRows.length,
  baseline_vs_override_position_f64:equal(baseRows,variantRows),baseline_vs_override_position_f32:equal(baseRows,variantRows,{f32:true}),
  baseline_vs_override_position_normal_f64:equal(baseRows,variantRows,{normal:true}),baseline_vs_override_position_normal_f32:equal(baseRows,variantRows,{normal:true,f32:true}),features:[],groups:[]};
 const references=[],referencesById=new Map();
 for(const feature of item.references){const ref=await load(feature.file),rows=triangles(ref);references.push(...rows);referencesById.set(feature.localId,rows);disposeModelResources(ref);}
 result.frozen_reference_vs_baseline_position_f64=equal(references,baseRows);result.frozen_reference_vs_baseline_position_f32=equal(references,baseRows,{f32:true});
 const remaining=inventory(variantRows,{f32:true});
 for(const feature of item.references){const rows=referencesById.get(feature.localId);let absent=0;for(const tri of rows){const k=key(tri,{f32:true}),count=remaining.get(k)||0;if(!count)absent++;else if(count===1)remaining.delete(k);else remaining.set(k,count-1);}result.features.push({localId:feature.localId,key:feature.key,triangles:rows.length,missing:absent});}
 result.unassigned_triangles=[...remaining.values()].reduce((n,v)=>n+v,0);
 for(const group of item.groups){const matches=[];variant.traverse(o=>{if(o.name===group.name)matches.push(o);});assert.equal(matches.length,1);const node=matches[0];assert.deepEqual(node.userData.cityReplacement,{macro_id:'14-13720-6694',landmark_id:group.landmark_id,local_ids:group.local_ids,feature_keys:group.feature_keys});const actual=triangles(node),expected=group.local_ids.flatMap(id=>referencesById.get(id));result.groups.push({name:group.name,triangles:countExpandedTriangles(node),position_f32:equal(expected,actual,{f32:true}),position_f64:equal(expected,actual)});}
 const neighbors=variant.getObjectByName('preserved_neighbors');assert(neighbors);result.neighbors={ids:item.neighbor_local_ids,position_f32:equal(item.neighbor_local_ids.flatMap(id=>referencesById.get(id)),triangles(neighbors),{f32:true}),position_f64:equal(item.neighbor_local_ids.flatMap(id=>referencesById.get(id)),triangles(neighbors))};
 result.pass=result.baseline_vs_override_position_f64.pass&&result.baseline_vs_override_position_normal_f32.pass&&result.frozen_reference_vs_baseline_position_f32.pass&&result.unassigned_triangles===0&&result.features.every(f=>!f.missing)&&result.groups.every(g=>g.position_f32.pass)&&result.neighbors.position_f32.pass;
 report.checks.push(result);disposeModelResources(baseline);disposeModelResources(variant);console.log(item.id,JSON.stringify({pass:result.pass,f64:result.baseline_vs_override_position_f64,ref:result.frozen_reference_vs_baseline_position_f32,normal:result.baseline_vs_override_position_normal_f64}));
}
report.pass=report.checks.every(x=>x.pass);await fs.writeFile(path.join(spec.output,'geometry-validation.json'),JSON.stringify(report,null,2)+'\n');
assert(report.pass,'Actual decoded near geometry changed; keep draft unpublished');
const manifest=JSON.parse(await fs.readFile(path.join(spec.output,'precise-buildings-v6.draft.json')));manifest.complete=true;manifest.status='independent actual decoded geometry comparison passed';manifest.validation={file:'geometry-validation.json',sha256:sha(await fs.readFile(path.join(spec.output,'geometry-validation.json')))};
await fs.writeFile(path.join(spec.output,'precise-buildings-v6.json'),JSON.stringify(manifest,null,2)+'\n');
