/** Intersect rays to actual architectural surfaces with original city triangles in the eye corridor. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {registerHooks} from 'node:module';
const here = path.dirname(fileURLToPath(import.meta.url));
const candidateRoot = path.resolve(here, '../../../..');
const root = process.env.SHANGHAI_PROJECT_ROOT || candidateRoot;
const [input, destination, optionalBase] = process.argv.slice(2);
if (!input || !destination) throw Error('Supply the signed sightline input and an output JSON file.');
const read = file => JSON.parse(fs.readFileSync(file));
const u = name => pathToFileURL(path.join(root, name)).href;
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
registerHooks({resolve(spec,ctx,next){return spec==='three'?{url:u('vendor/three.module.js'),shortCircuit:true}:next(spec,ctx)}});
const THREE=await import(u('vendor/three.module.js')), {GLTFLoader}=await import(u('vendor/GLTFLoader.js')),{MeshoptDecoder}=await import(u('vendor/meshopt_decoder.module.js'));
const proof=read(input),contract=proof.contract,md=proof,review={owners:proof.owners};
const owner=contract.owner.feature_local_id,port=proof.source_port;
const base = optionalBase || 'http://127.0.0.1:'+port+'/';
const deg=Math.PI/180,km=6378137*Math.cos(md.origin_latitude*deg),kt=6371008.8*Math.cos(contract.lat*deg),n=n=>Math.log(Math.tan(Math.PI/4+n*deg/2)),dx=kt*(md.origin_longitude-contract.lng)*deg,dy=kt*(n(md.origin_latitude)-n(contract.lat)),c=Math.cos(contract.heading*deg),s=Math.sin(contract.heading*deg),owners=new Set(proof.all_ids);
const rings=new Map(review.owners.map(o=>[o.local_id,o.geometry_wgs84.coordinates[0].map(([lng,lat])=>{const e=(lng-contract.lng)*deg*kt,north=(n(lat)-n(contract.lat))*kt;return [e*c-north*s,e*s+north*c];})]));
function distance(ring,x,y){let inside=false,minimum=Infinity;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const [xi,yi]=ring[i],[xj,yj]=ring[j];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi)+xi)inside=!inside;const dx=xj-xi,dy=yj-yi,len=dx*dx+dy*dy,t=len?Math.min(1,Math.max(0,((x-xi)*dx+(y-yi)*dy)/len)):0;minimum=Math.min(minimum,(x-xi-t*dx)**2+(y-yi-t*dy)**2);}return inside?0:minimum;}
function isNearestTarget(x,y){let closest=Infinity,mine=null;for(const [id,ring] of rings){const d=distance(ring,x,y);if(d<closest){closest=d;mine=id;}}return mine===owner;}
const localMask=proof.ground_mask;
function contains(ring,x,y){let inside=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const [a,b]=ring[i],[c,d]=ring[j];if((b>y)!==(d>y)&&x<(c-a)*(y-b)/(d-b)+a)inside=!inside;}return inside;}
const cut=(x,y)=>contains(localMask[0],x,y)&&!localMask.slice(1).some(r=>contains(r,x,y));
const vector=()=>new THREE.Vector3();const a=vector(),b=vector(),d=vector(),hitp=vector(),v=vector(),m=new THREE.Matrix4(),ins=new THREE.Matrix4(),loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const rays=[];for(const [device,rec]of Object.entries(proof.views))for(const p of rec.sightlines){const o=vector().fromArray(rec.eye),t=vector().fromArray(p.target),L=o.distanceTo(t);rays.push({device,feature:p.feature,ray:new THREE.Ray(o,t.clone().sub(o).normalize()),max:L,occluders:[],first:{near:null,far:null},scoped_target_cut:{near:0,far:0}});}
const sources=[];const rows=[{file:'far.glb',signed_sha256:proof.far_sha256,id:'far'},...proof.groups];
for(const entry of rows){const url=new URL('assets/city-detail/macros/'+proof.macro+'/'+entry.file,base).href;const res=await fetch(url);let bytes=Buffer.from(await res.arrayBuffer());if(res.status!==200||sha(bytes)!==entry.signed_sha256)throw Error('Source changed '+entry.id);sources.push({id:entry.id,url,sha256:sha(bytes),bytes:bytes.length});if(entry.file.endsWith('.gz'))bytes=zlib.gunzipSync(bytes);
 const level=entry.id==='far'?'far':'near';const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');gltf.scene.updateMatrixWorld(true);
 let total=0,selected=0;gltf.scene.traverse(mesh=>{if(!mesh.isMesh)return;const pos=mesh.geometry.getAttribute('position'),fid=mesh.geometry.getAttribute('_feature_id_0'),ind=mesh.geometry.index,count=ind?.count??pos.count,N=mesh.isInstancedMesh?mesh.count:1;const buf=new Float64Array(pos.count*3);for(let instance=0;instance<N;instance++){if(mesh.isInstancedMesh){mesh.getMatrixAt(instance,ins);m.multiplyMatrices(mesh.matrixWorld,ins);}else m.copy(mesh.matrixWorld);
  for(let i=0;i<pos.count;i++){v.fromBufferAttribute(pos,i).applyMatrix4(m);const e=dx+v.x*kt/km,nn=dy-v.z*kt/km;buf[3*i]=e*c-nn*s;buf[3*i+1]=e*s+nn*c;buf[3*i+2]=v.y;}
  for(let i=0;i<count;i+=3){const i0=ind?ind.getX(i):i,i1=ind?ind.getX(i+1):i+1,i2=ind?ind.getX(i+2):i+2;total++;const id=level==='far'?fid.getX(i0):null;if(level==='far'&&!owners.has(id))continue;selected++;
   a.fromArray(buf,3*i0);b.fromArray(buf,3*i1);d.fromArray(buf,3*i2);
   let isTarget=level==='far'?id===owner:null;
   for(const r of rays){if(!r.ray.intersectTriangle(a,b,d,false,hitp))continue;const dist=r.ray.origin.distanceTo(hitp);if(dist>=r.max-.015)continue;if(isTarget===null){isTarget=entry.members.includes(owner)&&isNearestTarget((a.x+b.x+d.x)/3,(a.y+b.y+d.y)/3);}if(isTarget&&cut(hitp.x,hitp.y)){r.scoped_target_cut[level]++;continue;}
    const gap=r.max-dist,entryHit={distance_m:dist,gap_m:gap,point_local:hitp.toArray(),source:entry.id,feature_id:id};if(!r.first[level]||r.first[level].distance_m>dist)r.first[level]=entryHit;
   }
  }
 }});Object.assign(sources.at(-1),{triangles_considered:total,triangles_tested:selected});}
const results=rays.map(({device,feature,max,first,scoped_target_cut})=>({device,feature,max_m:max,first,scoped_target_cut,city_mesh_sight_clear:!first.near&&!first.far}));fs.writeFileSync(destination,JSON.stringify({contract_sha256:proof.contract_sha256,source_port:port,catalog_sha256:proof.catalog_sha256,sources,results},null,1)+'\n');console.log(sources.map(x=>[x.id,x.triangles_tested]),results.filter(x=>!x.city_mesh_sight_clear).map(x=>[x.device,x.feature]));

if(results.some(ray => !ray.city_mesh_sight_clear)) process.exitCode = 1;
