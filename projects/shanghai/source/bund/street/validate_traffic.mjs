import fs from 'node:fs';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const PROJECT=process.argv[2] ? pathToFileURL(path.resolve(process.argv[2])+path.sep) : new URL('../../../',import.meta.url);
const THREE=await import(new URL('vendor/three.module.js',PROJECT));
const {createStreetTraffic}=await import(new URL('src/street-traffic.js',PROJECT));
const data=JSON.parse(fs.readFileSync(new URL('data/bund/traffic-v4.json',PROJECT),'utf8'));
const R=6378137, lat0=31.2385*Math.PI/180, scale=Math.cos(lat0), y0=Math.asinh(Math.tan(lat0));
const geographicPosition=(lng,lat,alt=0)=>new THREE.Vector3(R*(lng-121.4862)*Math.PI/180*scale,alt,-R*(Math.asinh(Math.tan(lat*Math.PI/180))-y0)*scale);
const traffic=await createStreetTraffic({THREE,geographicPosition,data});
assert.equal(traffic.stats.vehicles,10);assert(traffic.stats.drawCalls<=20);assert.equal(traffic.stats.animationLoops,0);
const bounds=Object.fromEntries(data.vehicles.map(v=>[v.id,{min:[Infinity,Infinity,Infinity],max:[-Infinity,-Infinity,-Infinity]}]));
const transforms=Object.fromEntries(data.vehicles.map(v=>{
 const object=new THREE.Object3D();object.position.copy(geographicPosition(v.lng,v.lat,v.ground_altitude_m));object.rotation.y=Math.PI-v.heading_degrees*Math.PI/180;object.updateMatrix();return [v.id,object.matrix.clone().invert()];
}));
const matrix=new THREE.Matrix4(), point=new THREE.Vector3();
for(const mesh of traffic.group.children){
 assert(mesh.isInstancedMesh);assert(mesh.boundingSphere && Number.isFinite(mesh.boundingSphere.radius));
 for(let i=0;i<mesh.count;i++){
  mesh.getMatrixAt(i,matrix);const id=mesh.userData.vehicleIds[i], box=bounds[id];const full=transforms[id].clone().multiply(matrix);
  for(let n=0;n<mesh.geometry.attributes.position.count;n++){
   point.fromBufferAttribute(mesh.geometry.attributes.position,n).applyMatrix4(full);
   assert(point.toArray().every(Number.isFinite));
   for(let axis=0;axis<3;axis++){const v=point.getComponent(axis);box.min[axis]=Math.min(box.min[axis],v);box.max[axis]=Math.max(box.max[axis],v);}
  }
 }
}
const vehicleChecks=[];
for(const v of data.vehicles){
 const b=bounds[v.id];
 assert(b.min[1]>-.0001,`${v.id} below road`);
 assert(Math.max(Math.abs(b.min[0]),Math.abs(b.max[0]))<=v.width_m/2+.12+.0001,`${v.id} width exceeds envelope`);
 assert(Math.max(Math.abs(b.min[2]),Math.abs(b.max[2]))<=v.length_m/2+.12+.0001,`${v.id} length exceeds envelope`);
 assert(b.max[1]<=v.height_m+.02,`${v.id} height exceeds metadata ${b.max[1]} vs ${v.height_m}`);
 vehicleChecks.push({id:v.id,local_bounds:b,wheels_on_surface:true,within_validated_road_envelope:true});
}
let geometryDisposals=0,materialDisposals=0,instanceDisposals=0;
const geometries=new Set(traffic.group.children.map(m=>m.geometry)),materials=new Set(traffic.group.children.map(m=>m.material));
for(const g of geometries)g.addEventListener('dispose',()=>geometryDisposals++);
for(const m of materials)m.addEventListener('dispose',()=>materialDisposals++);
for(const m of traffic.group.children)m.addEventListener('dispose',()=>instanceDisposals++);
traffic.dispose();traffic.dispose();assert.equal(traffic.group.children.length,0);assert.equal(geometryDisposals,geometries.size);assert.equal(materialDisposals,materials.size);assert.equal(instanceDisposals,traffic.stats.drawCalls);
const result={passed:true,stats:traffic.stats,vehicle_checks:vehicleChecks,disposal:{geometryDisposals,materialDisposals,instanceDisposals,idempotent:true},browser_test:'Not run; integrated visual QA owned by root.'};
fs.writeFileSync(new URL('data/bund/validation/traffic-v4.json',PROJECT),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({passed:true,stats:traffic.stats,disposal:result.disposal}));
