import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {registerHooks} from 'node:module';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const library='file:///workspace/e-resource/projects/shanghai/vendor/';
registerHooks({resolve(s,c,next){return s==='three'?{url:library+'three.module.js',shortCircuit:true}:next(s,c);}});
const THREE=await import(library+'three.module.js');
const {GLTFLoader}=await import(library+'GLTFLoader.js');
const {MeshoptDecoder}=await import(library+'meshopt_decoder.module.js');
const dataFile=new URL('./mesh-view-selection.json',import.meta.url);
const sourceBytes=await readFile(dataFile);
const data=JSON.parse(sourceBytes);
const sha=b=>createHash('sha256').update(b).digest('hex');
const degrees=Math.PI/180, earth=6371008.8, mercator=6378137;
const siteScale=earth*Math.cos(data.origin.lat*degrees),tileScale=mercator*Math.cos(data.cfg.lat*degrees);
const dx=(data.cfg.lng-data.origin.lng)*degrees;
const dy=Math.asinh(Math.tan(data.cfg.lat*degrees))-Math.asinh(Math.tan(data.origin.lat*degrees));
function scene([e,n,u]){return new THREE.Vector3((e/siteScale-dx)*tileScale,u,(dy-n/siteScale)*tileScale);}
function local(p){return [siteScale*(dx+p.x/tileScale),siteScale*(dy-p.z/tileScale),p.y];}
function inside(point,polygon){
 let inside=false;
 for(let i=0,j=polygon.length-1;i<polygon.length;j=i++){
  const [x,y]=polygon[i],[xx,yy]=polygon[j];
  if((y>point[1])!==(yy>point[1]) && point[0]<(xx-x)*(point[1]-y)/(yy-y)+x)inside=!inside;
 }
 return inside;
}
const probes=new Map();
for(const [viewport,v] of Object.entries(data.rays)){
 for(const [name,target] of v.targets){
  const origin=scene(v.origin),end=scene(target);
  probes.set(viewport+' '+name,{viewport,name,target,origin,end,ray:new THREE.Raycaster(origin,end.clone().sub(origin).normalize(),0,end.distanceTo(origin)-.04),masks:[]});
 }
}
const negative=data.negative;
const nOrigin=scene(negative.start),nEnd=scene(negative.target);
probes.set('cross-street preserved roof',{target:negative.target,origin:nOrigin,end:nEnd,ray:new THREE.Raycaster(nOrigin,nEnd.clone().sub(nOrigin).normalize(),0,nEnd.distanceTo(nOrigin)-.04)});
const files=[],byLod={near:{},far:{}};
assert.equal(data.repacked.length,0);
for(const item of [data.far,...data.groups]){
 const lod=item===data.far?'far':'near';
 const url='http://127.0.0.1:31198/'+data.source_dir+item.file;
 const response=await fetch(url);assert.equal(response.status,200);
 const raw=Buffer.from(await response.arrayBuffer());assert.equal(sha(raw),item.sha256);
 const glb=raw[0]===0x1f&&raw[1]===0x8b?gunzipSync(raw):raw;
 const obj=(await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(glb.buffer.slice(glb.byteOffset,glb.byteOffset+glb.byteLength),'')).scene;
 obj.updateMatrixWorld(true);
 obj.traverse(o=>{if(o.isMesh)for(const m of (Array.isArray(o.material)?o.material:[o.material]))m.side=THREE.DoubleSide;});
 const file={url,sha256:sha(raw),bytes:raw.length,paths:0,clippedContacts:0};
 for(const [label,p] of probes){
  const contacts=p.ray.intersectObject(obj,true);
  file.paths++;
  for(const hit of contacts){
   const loc=local(hit.point),fid=hit.object.geometry.getAttribute('_feature_id_0');
   const owner=fid?fid.getX(hit.face.a):null;
   const inRegisteredCut=inside(loc,data.cut_en) && (owner===4415 || (owner===null&&item.featureLocalIds?.includes(4415)));
   if(inRegisteredCut){file.clippedContacts++;continue;}
   const current=byLod[lod][label];
   if(!current || current.distance>hit.distance)byLod[lod][label]={distance:hit.distance,hit:loc,owner,file:item.file,distanceBeforeTarget:p.end.distanceTo(p.origin)-hit.distance};
   break;
  }
 }
 files.push(file);
 obj.traverse(o=>{o.geometry?.dispose();});
}
const control={};
for(const lod of ['near','far']){
 control[lod]=byLod[lod]['cross-street preserved roof'];
 assert.ok(control[lod] && control[lod].hit[2]>0.2);
 if(lod==='far')assert.equal(control[lod].owner,negative.owner);
 delete byLod[lod]['cross-street preserved roof'];
 assert.deepEqual(Object.keys(byLod[lod]),[]);
}
const result={crossStreetRoofControl:control,selection_sha256:sha(sourceBytes),driver_sha256:sha(await readFile(fileURLToPath(import.meta.url))),byLod,files,perViewport:10,viewports:Object.keys(data.rays),source:'Live signed baseline geometry interpreted with only owner 4415 street clipping; other buildings, map HUD and the delivered frontage have separate checks.'};
await writeFile(new URL('./mesh-view-result.json',import.meta.url),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({files:files.length,nearMasked:Object.keys(byLod.near),farMasked:Object.keys(byLod.far)}));
