/** Intersect rays to actual architectural surfaces with original city triangles in the eye corridor. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {registerHooks} from 'node:module';
const w=path.dirname(fileURLToPath(import.meta.url)),root=path.join(w,'frozen-259'),u=n=>pathToFileURL(path.join(root,n)).href,read=n=>JSON.parse(fs.readFileSync(n)),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
registerHooks({resolve(spec,ctx,next){return spec==='three'?{url:u('vendor/three.module.js'),shortCircuit:true}:next(spec,ctx)}});
const THREE=await import(u('vendor/three.module.js')), {GLTFLoader}=await import(u('vendor/GLTFLoader.js')),{MeshoptDecoder}=await import(u('vendor/meshopt_decoder.module.js'));
const contract=read(path.join(w,'final-placement-contract.json')),proof=read(path.join(w,'camera-sightline-sources.json')),review=read(path.join(w,'original-review.json')),md=read(path.join(w,'inputs/READY.json'));if(proof.contract_sha256!==sha(fs.readFileSync(path.join(w,'final-placement-contract.json'))))throw Error('Camera changed');
const deg=Math.PI/180,km=6378137*Math.cos(md.origin_latitude*deg),kt=6371008.8*Math.cos(contract.lat*deg),n=n=>Math.log(Math.tan(Math.PI/4+n*deg/2)),dx=kt*(md.origin_longitude-contract.lng)*deg,dy=kt*(n(md.origin_latitude)-n(contract.lat)),c=Math.cos(contract.heading*deg),s=Math.sin(contract.heading*deg),owners=new Set(proof.all_ids);
const rings=new Map(review.owners.map(o=>[o.local_id,o.geometry_wgs84.coordinates[0].map(([lng,lat])=>{const e=(lng-contract.lng)*deg*kt,north=(n(lat)-n(contract.lat))*kt;return [e*c-north*s,e*s+north*c];})]));
function distance(ring,x,y){let inside=false,minimum=Infinity;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const [xi,yi]=ring[i],[xj,yj]=ring[j];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi)+xi)inside=!inside;const dx=xj-xi,dy=yj-yi,len=dx*dx+dy*dy,t=len?Math.min(1,Math.max(0,((x-xi)*dx+(y-yi)*dy)/len)):0;minimum=Math.min(minimum,(x-xi-t*dx)**2+(y-yi-t*dy)**2);}return inside?0:minimum;}
function isNearest1810(x,y){let closest=Infinity,mine=null;for(const [id,ring] of rings){const d=distance(ring,x,y);if(d<closest){closest=d;mine=id;}}return mine===1810;}
const [left,back,right,front]=read(path.join(w,'measured-entrance-ground.json')).mask_xy_m;const cut=(x,y)=>x>=left&&x<=right&&y>=back&&y<=front;
const vector=()=>new THREE.Vector3();const a=vector(),b=vector(),d=vector(),hitp=vector(),v=vector(),m=new THREE.Matrix4(),ins=new THREE.Matrix4(),loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const rays=[];for(const [device,rec]of Object.entries(proof.views))for(const p of rec.sightlines){const o=vector().fromArray(rec.eye),t=vector().fromArray(p.target),L=o.distanceTo(t);rays.push({device,feature:p.feature,ray:new THREE.Ray(o,t.clone().sub(o).normalize()),max:L,occluders:[],first:{near:null,far:null},original1810_masked:{near:0,far:0}});}
const sources=[];const rows=[{file:'far.glb',signed_sha256:review.frozen_bindings.find(i=>i.repository_path.endsWith('/far.glb')).sha256,id:'far'},...proof.groups];
for(const entry of rows){const url='http://127.0.0.1:31259/assets/city-detail/macros/'+review.frozen_macro+'/'+entry.file;const res=await fetch(url);let bytes=Buffer.from(await res.arrayBuffer());if(res.status!==200||sha(bytes)!==entry.signed_sha256)throw Error('Source changed '+entry.id);sources.push({id:entry.id,url,sha256:sha(bytes),bytes:bytes.length});if(entry.file.endsWith('.gz'))bytes=zlib.gunzipSync(bytes);
 const level=entry.id==='far'?'far':'near';const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');gltf.scene.updateMatrixWorld(true);
 let total=0,selected=0;gltf.scene.traverse(mesh=>{if(!mesh.isMesh)return;const pos=mesh.geometry.getAttribute('position'),fid=mesh.geometry.getAttribute('_feature_id_0'),ind=mesh.geometry.index,count=ind?.count??pos.count,N=mesh.isInstancedMesh?mesh.count:1;const buf=new Float64Array(pos.count*3);for(let instance=0;instance<N;instance++){if(mesh.isInstancedMesh){mesh.getMatrixAt(instance,ins);m.multiplyMatrices(mesh.matrixWorld,ins);}else m.copy(mesh.matrixWorld);
  for(let i=0;i<pos.count;i++){v.fromBufferAttribute(pos,i).applyMatrix4(m);const e=dx+v.x*kt/km,nn=dy-v.z*kt/km;buf[3*i]=e*c-nn*s;buf[3*i+1]=e*s+nn*c;buf[3*i+2]=v.y;}
  for(let i=0;i<count;i+=3){const i0=ind?ind.getX(i):i,i1=ind?ind.getX(i+1):i+1,i2=ind?ind.getX(i+2):i+2;total++;const id=level==='far'?fid.getX(i0):null;if(level==='far'&&!owners.has(id))continue;selected++;
   a.fromArray(buf,3*i0);b.fromArray(buf,3*i1);d.fromArray(buf,3*i2);
   let isTarget=level==='far'?id===1810:null;
   for(const r of rays){if(!r.ray.intersectTriangle(a,b,d,false,hitp))continue;const dist=r.ray.origin.distanceTo(hitp);if(dist>=r.max-.015)continue;if(isTarget===null){isTarget=entry.members.includes(1810)&&isNearest1810((a.x+b.x+d.x)/3,(a.y+b.y+d.y)/3);}if(isTarget&&cut(hitp.x,hitp.y)){r.original1810_masked[level]++;continue;}
    const gap=r.max-dist,entryHit={distance_m:dist,gap_m:gap,point_local:hitp.toArray(),source:entry.id,feature_id:id};if(!r.first[level]||r.first[level].distance_m>dist)r.first[level]=entryHit;
   }
  }
 }});Object.assign(sources.at(-1),{triangles_considered:total,triangles_tested:selected});}
const results=rays.map(({device,feature,max,first,original1810_masked})=>({device,feature,max_m:max,first,original1810_masked,city_mesh_sight_clear:!first.near&&!first.far}));fs.writeFileSync(path.join(w,'actual-camera-city-triangles.json'),JSON.stringify({contract_sha256:proof.contract_sha256,modules_from:31259,sources,results},null,1)+'\n');console.log(sources.map(x=>[x.id,x.triangles_tested]),results.filter(x=>!x.city_mesh_sight_clear).map(x=>[x.device,x.feature]));
