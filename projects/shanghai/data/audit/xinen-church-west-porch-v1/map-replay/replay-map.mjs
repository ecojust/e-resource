/** Re-run on a signed predecessor (private model) or the real successor (published catalog). */
import fs from 'node:fs';
import os from 'node:os';
import {gunzipSync} from 'node:zlib';
import path from 'node:path';
import assert from 'node:assert/strict';
import http from 'node:http';
import crypto from 'node:crypto';
import vm from 'node:vm';
import {registerHooks,createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
const work=path.dirname(fileURLToPath(import.meta.url)),proj=path.resolve(process.env.SHANGHAI_PROJECT_ROOT || path.join(work,'../../../..'));
const [stage, result='runtime-output.json'] = process.argv.slice(2);
assert(['322','323'].includes(stage),'Expected 322 or 323');
const argPlacement=path.join(proj,'data/audit/xinen-church-west-porch-v1/final-placement-contract.json');
const pilot=path.join(proj,'assets/models/candidates/jingan-xinen-church-west-porch');
const base=(process.env.SHANGHAI_ORIGIN || ('http://127.0.0.1:'+String(31000+Number(stage)))).replace(/\/+$/,'')+'/', read=p=>JSON.parse(fs.readFileSync(p)),sha=b=>crypto.createHash('sha256').update(b).digest('hex'), digest=x=>sha(Buffer.from(JSON.stringify(x)));
const placement=read(argPlacement),footprint=read(path.join(work,'original-review.json')),ground=read(path.join(work,'ground-cases.json')).ground,manifest=read(path.join(pilot,'manifest.json'));
const signedPath=path.join(work,stage+'-comparison.json'),signed=read(signedPath),httpInputs={};assert(signed.passed&&signed.order===Number(stage));
const complete=gunzipSync(fs.readFileSync(path.join(work,stage+'-production.json.gz')));
assert.equal(sha(complete),signed.production_receipt_sha256);
const files=JSON.parse(complete).files;
const sources=read(path.join(work,'checked-'+stage+'.json')).input_modules_and_assets;
const get=async name=>{const u=new URL(name,base);const r=await fetch(u);assert.equal(r.status,200,u.href);const b=Buffer.from(await r.arrayBuffer());assert.equal(sha(b),files[name] || sources[name].sha256,name);httpInputs[name]={url:u.href,bytes:b.length,sha256:sha(b)};return b};
const catalog=JSON.parse(await get('data/candidate-city-integrations.json'));assert.equal(httpInputs['data/candidate-city-integrations.json'].sha256,signed.catalog_sha256);
for(const binding of footprint.frozen_bindings){const name=binding.repository_path.replace('projects/shanghai/','');assert.equal(sha(await get(name)),binding.sha256,name);}
const modules=['src/candidate-city-clipping.js','src/candidate-bridge-walk.js','src/candidate-city-integrations.js','src/candidate-vector-clipping.js','src/candidate-vector-geometry.js','src/candidate-source-sections.js','src/historical-view.js','src/ordinary-scene-adapter.js','src/ordinary-building-catalog.js','src/ordinary-contracts.js','src/model-resources.js','src/local-model-streamer.js','src/ordinary-asset-verification.js','vendor/polygon-clipping.umd.min.js','vendor/three.module.js','vendor/three.core.js','vendor/GLTFLoader.js','vendor/BufferGeometryUtils.js','vendor/meshopt_decoder.module.js','vendor/maplibre-gl.js'];
const frozen=fs.mkdtempSync(path.join(process.env.XINEN_RUNTIME_SCRATCH || os.tmpdir(),'xinen-renderer-'));fs.mkdirSync(frozen,{recursive:true});fs.writeFileSync(path.join(frozen,'package.json'),'{"type":"module"}');
for(const name of modules){
 const bytes=await get(name),dest=path.join(frozen,name),local=path.join(proj,name);fs.mkdirSync(path.dirname(dest),{recursive:true});
 if(fs.existsSync(dest)){assert.equal(sha(fs.readFileSync(dest)),sha(bytes),name);continue;}
 if(fs.existsSync(local)&&sha(bytes)===sha(fs.readFileSync(local))){try{fs.linkSync(local,dest)}catch(e){if(e.code!=='EXDEV')throw e;fs.symlinkSync(local,dest)}}else fs.writeFileSync(dest,bytes,{flag:'wx'});
 assert.equal(sha(bytes),sha(fs.readFileSync(dest)),name);
}
const mapSource=(await get('src/map-scene.js')).toString();assert.match(mapSource,/const ORIGIN = \[121\.4737, 31\.2304\]/);assert.match(mapSource,/p\.z \/ metreScale/);
const moduleURL=p=>pathToFileURL(path.join(frozen,p)).href,load=p=>import(moduleURL(p));
registerHooks({resolve(specifier,ctx,next){return specifier==='three'?{url:moduleURL('vendor/three.module.js'),shortCircuit:true}:next(specifier,ctx)}});
const THREE=await load('vendor/three.module.js'),{CandidateCityClipper}=await load('src/candidate-city-clipping.js'),{CandidateCityState,candidateGeometryContains:inside}=await load('src/candidate-city-integrations.js'),{planCandidateVectorClipping:planVectors}=await load('src/candidate-vector-clipping.js'),{loadOrdinaryLandmarkAsset}=await load('src/ordinary-scene-adapter.js');
const {GLTFLoader}=await load('vendor/GLTFLoader.js'),{MeshoptDecoder}=await load('vendor/meshopt_decoder.module.js');
const ctx={console,URL,Blob,performance,TextDecoder,TextEncoder,AbortController,ImageData:class {},setTimeout,clearTimeout};ctx.self=ctx;ctx.window=ctx;vm.runInNewContext(fs.readFileSync(path.join(frozen,'vendor/maplibre-gl.js'),'utf8'),ctx);
const merc=ctx.maplibregl.MercatorCoordinate,merc0=merc.fromLngLat([121.4737,31.2304],0),scale=merc0.meterInMercatorCoordinateUnits(),scenePos=(lng,lat,alt=0)=>{const q=merc.fromLngLat([lng,lat],alt);return new THREE.Vector3((q.x-merc0.x)/scale,q.z/scale,(q.y-merc0.y)/scale);};
const h=placement.heading*Math.PI/180,deg=Math.PI/180,k=6371008.8*Math.cos(placement.lat*deg),log=lat=>Math.asinh(Math.tan(lat*deg));
function wgs([x,y]){return [placement.lng+(x*Math.cos(h)+y*Math.sin(h))/k/deg,Math.atan(Math.sinh(log(placement.lat)+(-x*Math.sin(h)+y*Math.cos(h))/k))/deg];}
const published=catalog.models.some(m=>m.id===placement.id),actual=catalog.models.find(m=>m.id===placement.id);
if(Number(stage)===323)assert(published);else assert(!published);
if(actual){for(const key of ['lng','lat','heading','owner','source_feature_ids','replacement_geometry','collision_geometry','display_height_clips','source_section_caps','model_geometry_sha256'])assert.deepEqual(actual[key],placement[key],key);}
const parents=catalog.models.filter(m=>m.id!==placement.id),groundRows=parents.flatMap(m=>[...(m.replacement_geometry?[{...m,geometry:m.replacement_geometry}]:[]),...(m.site_replacement?[m.site_replacement]:[])]),oldRows=[...groundRows,...parents.flatMap(m=>m.display_height_clips??[])];
let server;let address=base,assets=actual?.assets;
if(!actual){const def={web:manifest.assets.full.file,lod:manifest.assets.lod.file};assets={};for(const [key,file] of Object.entries(def)){const bytes=fs.readFileSync(path.join(pilot,file));assert.equal(sha(bytes),placement.model_geometry_sha256[key]);assets[key]={file,sha256:sha(bytes),bytes:bytes.length};}
 server=http.createServer((req,res)=>{const f=req.url.slice(1);if(!Object.values(def).includes(f)){res.writeHead(404);res.end();return;}const b=fs.readFileSync(path.join(pilot,f));res.writeHead(200,{'Content-Length':b.length,'Content-Type':'model/gltf-binary'});res.end(b);});
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});address='http://127.0.0.1:'+server.address().port+'/';}
const records=new Map(),scene=new THREE.Scene(),group=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial()),record={...placement,...(actual||{}),assets,id:placement.id,city_integration:true,catalogBaseURL:address};
records.set(record.id,record);const st=new CandidateCityState({getRecords:()=>records,getScene:()=>scene});const clipper=new CandidateCityClipper({THREE,geographicPosition:scenePos}),groupData=footprint.near_tiles[0];clipper.bindObject(group,{id:groupData.id,parent:{id:footprint.frozen_macro},ids:groupData.feature_local_ids});
const scope=clipper.objects.get(group).scope;
const {CandidateSourceSections}=await load('src/candidate-source-sections.js');
const section=new CandidateSourceSections(scene,scenePos);
const macroMesh=new THREE.Group();scene.add(macroMesh);
const macroWitness={id:footprint.frozen_macro,sha256:footprint.frozen_bindings.find(q=>q.repository_path.endsWith('far.glb')).sha256,object:macroMesh};
const rowsFor=(table,id)=>{const rows=[];for(let i=0;i<table.triangles;i++)if(table.data[16*i+12]===id||table.data[16*i+12]===0)rows.push(Array.from(table.data.slice(16*i,16*i+16)));return rows;};
function hit(rows,p,z){const pos=scenePos(...p,z);return rows.some(([ax,ay,bx,by,cx,cy,low,high])=>{if(pos.y<low||pos.y>high)return false;const side=(a,b,c,d)=>(b-a)*(pos.z-c)-(d-c)*(pos.x-a),e=[side(ax,bx,ay,by),side(bx,cx,by,cy),side(cx,ax,cy,ay)];return e.every(x=>x>=0)||e.every(x=>x<=0);});}
const features=read(path.join(work,'map-visible-components.json')),source=footprint.owners.find(o=>o.local_id===3149),other=footprint.owners.find(o=>o.local_id===1683);
const bounds=g=>{const pts=(g.type==='Polygon'?g.coordinates:g.coordinates.flat()).flat();return [Math.min(...pts.map(p=>p[0])),Math.min(...pts.map(p=>p[1])),Math.max(...pts.map(p=>p[0])),Math.max(...pts.map(p=>p[1]))];};
const intersects=(a,b)=>a[0]<=b[2]&&a[2]>=b[0]&&a[1]<=b[3]&&a[3]>=b[1],window=features.map(f=>bounds(f.geometry)).reduce((a,b)=>[Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[2],b[2]),Math.max(a[3],b[3])]);const localParents=groundRows.filter(c=>intersects(window,bounds(c.osm_replacement_geometry||c.geometry)));
const vecContext={source:'openmaptiles',sourceLayer:'building'},ovContext={source:'overture-buildings',sourceLayer:'building'},ov=footprint.owners.map(o=>({id:o.key.split(':').at(-1),properties:{id:o.key.split(':').at(-1)},geometry:o.geometry_wgs84,type:'Feature'}));
const results=[],assetReceipts={};
function outputPerPart(features,clips,context){return features.map(f=>{const v=planVectors([f],{candidateClips:clips},context);assert.equal(v.stats.clippingErrors,0);return {id:f.id,component:f.component??null,changed:v.desired.size>0,geometry:v.desired.size?v.residualData.features[0]?.geometry??null:f.geometry};});}
function capture(step){
 st.sync();const state=st.getState(),enabled=state.active.length===1;const cuts=[...localParents,...state.clips];clipper.update([...oldRows,...state.displayClips]);
 const ownNear=rowsFor(scope,3149),ownFar=rowsFor(clipper.tableFor(scope.macro),3149),targets=groupData.feature_local_ids.map(id=>{const nr=rowsFor(scope,id),fr=rowsFor(clipper.tableFor(scope.macro),id);return {id,near:digest(nr),far:digest(fr),near_rows:nr.length,far_rows:fr.length}});
 assert.deepEqual(ownNear,ownFar);const courtyard=[];
 for(const x of [-6.81,-6.59,-6.41,-4.33,-3.22,-.66,.83,2.19,4.17,6.34,6.61]){
  for(const y of [-2.10,-.64,-.32,.27,.83,2.96,3.81,5.72,7.40,7.77,8.11]){
   const xy=[x,y],pos=wgs(xy),masked=x>-6.53&&x<6.46&&y>-.40&&y<7.63;
   for(const z of [.1,1.75,2.61,4.2,6.5,8.25,8.73,9.37,11,12.93,17.99,20]){
    const want=enabled&&masked;assert.equal(hit(ownNear,pos,z),want,JSON.stringify({step,xy,z}));assert.equal(hit(ownFar,pos,z),want);
    courtyard.push({xy,height:z,clipped:want});
   }
  }
 }
 const vec=outputPerPart(features,cuts,vecContext);const nativeVector=outputPerPart(ov,[...groundRows,...state.clips],ovContext);assert.equal(nativeVector.filter(x=>x.changed).some(x=>x.id===other.key.split(':').at(-1)),false);
 const combined=planVectors(features,{candidateClips:cuts},vecContext);assert.equal(combined.stats.clippingErrors,0);
 const oldId=source.key.split(':').at(-1),gout=ground.map(q=>{
  const xy=q.lonlat,cut=st.clipsPoint(...xy,{name:'overture-buildings',layer:'building',id:oldId});assert.equal(cut,enabled&&q.mask);
  assert.equal(st.collisions().length,enabled?1:0);
  const collides=st.collisions().some(c=>inside(c.geometry,xy));assert.equal(collides,enabled&&q.model);const blocked=collides||(!cut&&inside(source.geometry_wgs84,xy)),vectorBlocked=vec.some(v=>v.geometry&&inside(v.geometry,xy));
  if(enabled)assert.equal(blocked,q.map);return {xy:q.xy,cut,blocked,vectorBlocked};
 });
 section.sync(enabled?[record]:[],[macroWitness]);const sections=section.getState();assert.equal(sections.length,0);
 const result={step,sections,active:state.active,revision:state.revision,groundCutCount:state.clips.length,displayCutCount:state.displayClips.length,targets,texture_triangle_count:clipper.getState().triangles,source_height_cell_sha256:digest(courtyard),source_height_cells:courtyard.length,ground:gout,vector_parts:vec.map(q=>({...q,geometry:digest(q.geometry)})),native_vector_parts:nativeVector.map(q=>({...q,geometry:digest(q.geometry)})),grouped_vector:combined.stats,grouped_signature:digest(combined.signature)};
 results.push(result);
}
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
async function install(variant){if(record.object)scene.remove(record.object);const response=await loadOrdinaryLandmarkAsset({record,variant,loader}),o=response.scene;scene.add(o);record.object=o;record.status='loaded';record.activeVariant=variant;let meshes=0,tris=0;o.traverse(n=>{if(n.isMesh){meshes++;tris+=(n.geometry.index?.count??n.geometry.attributes.position.count)/3;}});assert.equal(tris,manifest.assets[variant==='full'?'full':'lod'].triangles);assetReceipts[variant]={...o.userData.__ordinaryVerifiedAsset,meshes,triangles:tris,transfer:actual?'frozen-model-http':'private-signed-geometry-http'};}
try{capture('before');await install('full');capture('full');record.object.visible=false;capture('hidden');record.object.visible=true;capture('restored');await install('distant');capture('distant');scene.remove(record.object);capture('unloaded');}finally{if(server){server.closeAllConnections();await new Promise(r=>server.close(r));}}
for(const o of results){const enabled=['full','restored','distant'].includes(o.step),before=results[0];assert.equal(o.displayCutCount,enabled?1:0);assert.equal(o.groundCutCount,enabled?1:0);for(const r of o.targets.filter(m=>m.id!==3149))assert.deepEqual(r,before.targets.find(m=>m.id===r.id));
 const changed=o.vector_parts.filter((q,i)=>q.geometry!==before.vector_parts[i].geometry);assert.deepEqual(changed.map(x=>[x.id,x.component]),[]);
 const changedNative=o.native_vector_parts.filter((q,i)=>q.geometry!==before.native_vector_parts[i].geometry);assert.deepEqual(changedNative.map(x=>x.id),enabled?[source.key.split(':').at(-1)]:[]);
 assert.equal(o.grouped_signature,before.grouped_signature);if(!enabled){assert.equal(o.grouped_signature,before.grouped_signature);assert.deepEqual(o.ground,before.ground);}
}
section.dispose();clipper.releaseObject(group);assert.equal(clipper.getState().sourceObjects,0);
fs.writeFileSync(result,JSON.stringify({passed:true,stage:Number(stage),published,model:placement.id,port:signed.port,production_sha256:signed.production_receipt_sha256,catalog_sha256:signed.catalog_sha256,comparison_receipt_sha256:sha(fs.readFileSync(signedPath)),prior_catalog_items:parents.length,placement_sha256:sha(fs.readFileSync(argPlacement)),input_modules_and_assets:httpInputs,models:assetReceipts,vector_feature_count:features.length,local_parent_vector_clips:localParents.map(c=>c.id),ground_cases:ground.length,height_cases_per_state:results[0].source_height_cells,results},null,2)+'\n');
console.log(result,results.map(x=>[x.step,x.ground.length,x.source_height_cells,x.texture_triangle_count]),assetReceipts);

fs.rmSync(frozen,{recursive:true,force:true});
