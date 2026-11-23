import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const payload=JSON.parse(fs.readFileSync(0)), {contract,row,review,spec,catalog}=payload;
const root=process.argv[2],load=f=>import(pathToFileURL(path.join(root,f)));
const THREE=await load('vendor/three.module.js');
const {CandidateCityState,candidateGeometryContains,mergeCandidateCityModels}=await load('src/candidate-city-integrations.js');
const {markVerifiedOrdinaryAsset}=await load('src/ordinary-asset-verification.js');
const {CandidateCityClipper}=await load('src/candidate-city-clipping.js');
const {planCandidateVectorClipping}=await load('src/candidate-vector-clipping.js');
const model=mergeCandidateCityModels([], {...catalog,models:[...catalog.models,row]}).at(-1);
const rad=Math.PI/180,r=6371008.8,metres=r*Math.cos(row.lat*rad);
function xyz(lon,lat,z=0){return new THREE.Vector3((lon-row.lng)*rad*metres,z*metres/(r*Math.cos(lat*rad)),(Math.asinh(Math.tan(row.lat*rad))-Math.asinh(Math.tan(lat*rad)))*metres);}
const prior=new Map();
for(const b of catalog.models){
 if(b.replacement_geometry)prior.set(b.id,{...b,geometry:b.replacement_geometry});
 if(b.site_replacement)prior.set(b.site_replacement.id,b.site_replacement);
 for(const clip of b.display_height_clips||[]) prior.set(clip.id,clip);
}
const scene=new THREE.Scene(),records=new Map(),real=new CandidateCityState({getRecords:()=>records,getScene:()=>scene}),clipper=new CandidateCityClipper({THREE,geographicPosition:xyz});
const tile=review.near_tiles.find(t=>t.feature_local_ids.includes(2172));
const mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());
clipper.bindObject(mesh,{id:tile.id,parent:{id:row.owner.macro_id},ids:tile.feature_local_ids});
function evaluate(){
 real.sync();const state=real.getState();clipper.update([...prior.values(),...state.displayClips]);const gpu=clipper.getState();
 const target=gpu.ownerScopedSources.find(s=>s.id===tile.id),scope=[...clipper.objects.values()][0].scope;
 const bands=[];
 for(let i=0;i<scope.triangles;i++){const p=i*16;if(scope.data[p+12]===2172)bands.push([scope.data[p+6],scope.data[p+7]]);}
 return {active:state.active,clips:state.clips,display:state.displayClips,triangles:gpu.triangles,scopedTargetDraw:target,bands};
}
const before=evaluate();assert.equal(before.bands.length,0);assert.equal(before.active.length,0);
const tests=[];
function check(){
 const out=evaluate();assert.equal(out.triangles-before.triangles,4);assert.equal(out.clips.length,1);assert.equal(out.display.length,2);
 const expected=out.display.flatMap(c=>Array(2).fill([Math.fround(xyz(...c.height_reference,c.min_height).y),Math.fround(xyz(...c.height_reference,c.max_height).y)]));
 assert.deepEqual(out.bands,expected);return out;
}
let after,ground,vector;
for(const [level,role] of [['full','web'],['distant','lod']]){
 const obj=new THREE.Group();scene.add(obj);const rec={...model,status:'loaded',object:obj,activeVariant:level};records.set(model.id,rec);
 assert.deepEqual(evaluate().bands,[]);markVerifiedOrdinaryAsset(obj,{modelId:model.id,variant:role,asset:rec.assets[role]});
 after=check();assert.equal(after.active[0].assetSha256,model.assets[role].sha256);
 const owner=review.owners.find(o=>o.local_id===2172);
 const context={name:'overture-buildings',layer:'building',id:owner.key.slice(9)};
 ground=spec.points.map(p=>{
 const xy=p.wgs84,body=candidateGeometryContains(row.collision_geometry,xy),cut=real.clipsPoint(...xy,context);
 assert.equal(body,p.model_obstacle,p.name);assert.equal(cut,p.source_cut,p.name);const priorWall=candidateGeometryContains(owner.geometry,xy);
 assert.equal((body||(priorWall&&!cut))?'building':null,p.expected_map,p.name);
 return {name:p.name,xy:p.xy,body,cut,priorWall,expected:p.expected_map};});
 for(const n of spec.neighborGround){assert.equal(real.clipsPoint(...n.point,context),false);assert.equal(candidateGeometryContains(row.collision_geometry,n.point),false);ground.push({neighbor:n.id,untouched:true});}
 vector=[];
 for(const src of ['overture-buildings','openmaptiles'])for(const id of [2172,...review.checked_neighbors]){
 const o=review.owners.find(x=>x.local_id===id);const f={type:'Feature',id:1,geometry:o.geometry,properties:{id:o.key.slice(9)}};
 const res=planCandidateVectorClipping([f],{candidateClips:real.clips},{source:src,sourceLayer:'building'});assert.equal(res.stats.clippingErrors,0);assert.equal(res.desired.size,id===2172?1:0);
 if(id===2172){assert.equal(res.residualData.features.length,1);const retained=res.residualData.features[0].geometry;for(const b of spec.points)if(!b.model_obstacle&&candidateGeometryContains(o.geometry,b.wgs84))assert.equal(candidateGeometryContains(retained,b.wgs84),!b.source_cut,b.name);}
 vector.push({source:src,id,partial:res.stats.partialIDs});}
 obj.visible=false;assert.deepEqual(evaluate().bands,[]);obj.visible=true;const old=rec.assets;const bad={...rec,assets:{...old,[role]:{...old[role],sha256:'0'.repeat(64)}}};records.set(model.id,bad);assert.equal(evaluate().active.length,0);records.clear();scene.remove(obj);
 tests.push({role,sha256:old[role].sha256,unverified_hidden_mismatch_rejected:true,bands:after.bands});
}
assert.deepEqual(evaluate(),before);clipper.dispose();mesh.geometry.dispose();mesh.material.dispose();
process.stdout.write(JSON.stringify({id:row.id,before,after,ground,vector,verified_variants:tests,returned_to_before:true}));
