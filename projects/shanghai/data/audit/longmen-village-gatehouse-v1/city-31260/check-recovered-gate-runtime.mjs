import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';

const host='/tmp/shanghai-main-260';
const audit='/workspace/e-resource/projects/shanghai/data/audit/longmen-village-gatehouse-v1';
const load=file=>JSON.parse(fs.readFileSync(file));
const sha=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const spec=load(path.join(host,'case260.json'));
const historical=load(path.join(host,'dispatch.json'));
const contract=load(path.join(audit,'final-placement-contract.json'));
assert.equal(sha(path.join(audit,'final-placement-contract.json')),load(path.join(host,'two-transitions.json'))['260'].contract_sha256);
const groundTargets=load(path.join(audit,'map-ground-witnesses.json')).ground_probes;
assert.equal(groundTargets.length,53);
const states={};
const ground=[];
const shader={};
const vector=[];
let previous=null;
for (const n of [259,260]) {
  const root=path.join(host,'stage'+n);
  const local=key=>path.join(root,key);
  const imported=key=>import(pathToFileURL(local(key)));
  const THREE=await imported('vendor/three.module.js');
  const {CandidateCityState,mergeCandidateCityModels,candidateGeometryContains}=await imported('src/candidate-city-integrations.js');
  const {markVerifiedOrdinaryAsset}=await imported('src/ordinary-asset-verification.js');
  const {CandidateCityClipper}=await imported('src/candidate-city-clipping.js');
  const {planCandidateVectorClipping}=await imported('src/candidate-vector-clipping.js');
  const catalog=load(local('data/candidate-city-integrations.json'));
  const signature=load(path.join(host,n+'-bindings.json'));
  assert.equal(sha(local('data/candidate-city-integrations.json')),signature.files['data/candidate-city-integrations.json']);
  assert.equal(catalog.resulting_city_count,n+35);
  if (previous) assert.deepEqual(previous,catalog.models.slice(0,-1));
  previous=catalog.models;
  const models=mergeCandidateCityModels([],catalog);
  const selected=models.find(m=>m.id===signature.model);
  const record=selected.kind==='building'?selected:models.findLast(m=>m.kind==='building');
  assert.equal(models.some(m=>m.id===contract.id),n===260);
  const scene=new THREE.Scene();
  const active=new CandidateCityState({getScene:()=>scene,getRecords:()=>new Map([[record.id,record]])});
  const review=load(path.join(host,'stage260/source/precise',contract.id,'footprint-review.json'));
  const neighbors=[...review.owners,...review.adjacent_macro.owners].filter(r=>[353,1608,1726].includes(r.local_id));
  assert.deepEqual(neighbors.map(r=>r.local_id).sort((a,b)=>a-b),[353,1608,1726]);
  const groups=[...review.near_tiles.map(item=>[review.frozen_macro,item]),...review.adjacent_macro.near_tiles.map(item=>[review.adjacent_macro.frozen_macro,item])];
  const rad=Math.PI/180,scale=6371008.8*Math.cos(contract.lat*rad);
  const geographicPosition=(lng,lat,height=0)=>new THREE.Vector3((lng-contract.lng)*rad*scale,height*scale/(6371008.8*Math.cos(lat*rad)),(Math.asinh(Math.tan(contract.lat*rad))-Math.asinh(Math.tan(lat*rad)))*scale);
  const clipper=new CandidateCityClipper({THREE,geographicPosition});
  const subjects=[];
  for(const [macro,tile] of groups) {
    const mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial());
    clipper.bindObject(mesh,{id:tile.id,parent:{id:macro},ids:tile.feature_local_ids}); subjects.push(mesh);
  }
  const declared=new Map();
  for(const r of models) {
    if(r.replacement_geometry) declared.set(r.id,{...r,geometry:r.replacement_geometry});
    if(r.site_replacement)declared.set(r.site_replacement.id,r.site_replacement);
  }
  clipper.update([...declared.values(),...models.flatMap(r=>r.display_height_clips||[])]);
  const table=clipper.getState();
  assert.equal(table.ownerScopedSources.length,2);
  for(const scope of table.ownerScopedSources) {
    assert.equal(scope.triangles,0);
    assert.equal(scope.clip_feature_local_ids.length,0);
  }
  shader[n]={triangles:table.triangles,groups:table.ownerScopedSources};
  if(n===260)assert.deepEqual(shader[n],shader[259]);
  const newGroup=()=>{const object=new THREE.Group();scene.add(object);return object;};
  let currentObject=newGroup();
  record.object=currentObject;record.status='loaded';record.activeVariant='full';
  states[n]=[];
  for (const [name,variant,visible,detached] of [
      ['unverified','full',true,false],['visible-full','full',true,false],['hidden','full',false,false],
      ['visible-distant','distant',true,false],['detached','distant',true,true],['reinserted','full',true,false]]) {
    if (name==='visible-distant'||name==='reinserted') {scene.remove(currentObject);currentObject=newGroup();record.object=currentObject;}
    const key=variant==='full'?'web':'lod', asset=record.assets[key];
    assert.equal(sha(local(asset.file)),asset.sha256);assert.equal(fs.statSync(local(asset.file)).size,asset.bytes);
    if(name!=='unverified')markVerifiedOrdinaryAsset(currentObject,{modelId:record.id,variant:key,asset});
    record.activeVariant=variant;currentObject.visible=visible;if(detached)scene.remove(currentObject);
    active.sync();
    const detail=active.getState();
    const shown=name!=='unverified' && visible && !detached;
    assert.equal(detail.active.length,shown?1:0,JSON.stringify([n,name,record.id,record.kind,record.city_integration]));
    if(shown) assert.equal(detail.active[0].assetSha256,asset.sha256);
    assert.ok(!detail.clips.some(c=>c.id===contract.id));
    states[n].push({name,active:detail.active.map(v=>v.id),asset:shown?asset.sha256:null,variant,visible,inScene:currentObject.parent===scene});
  }
  if(n===260) {
    for(const key of ['owner','source_feature_ids','replacement_geometry','collision_geometry','model_geometry_sha256']) assert.deepEqual(contract[key],record[key]);
    assert.equal(contract.replacement_geometry,null);assert.equal(contract.owner,undefined);
    assert.ok(Object.values(contract.source_feature_ids).every(ids=>ids.length===0));
    for(const probe of groundTargets) {
      const candidate=active.collisions().some(item=>candidateGeometryContains(item.geometry,probe.wgs84));
      const cut=candidateGeometryContains(contract.replacement_geometry,probe.wgs84);
      const owners=neighbors.filter(r=>candidateGeometryContains(r.geometry,probe.wgs84)).map(r=>r.local_id);
      const blocked=candidate||owners.length>0;
      assert.equal(candidate,Boolean(probe.blocked&&!probe.ownerLocalId),probe.name);
      assert.equal(cut,false,probe.name);assert.equal(blocked,probe.blocked,probe.name);
      if(probe.ownerLocalId)assert.ok(owners.includes(probe.ownerLocalId),probe.name);
      ground.push({name:probe.name,point:probe.wgs84,candidate,cut,old_owner:owners.length?owners:null,blocked});
    }
    for(const source of ['overture-buildings','openmaptiles']) for(const owner of neighbors) {
      const feature={id:owner.local_id,type:'Feature',geometry:owner.geometry,properties:{id:owner.key.slice(9)}};
      const result=planCandidateVectorClipping([feature],{candidateClips:active.clips},{source,sourceLayer:'building'});
      assert.equal(result.stats.clippingErrors,0);assert.equal(result.desired.size,0);assert.equal(result.residualData.features.length,0);
      vector.push({source,owner:owner.local_id,retained:result.stats.retainedCrossingIDs});
    }
  }
  clipper.dispose();for(const mesh of subjects){mesh.geometry.dispose();mesh.material.dispose();}
}
const output={passed:true,id:contract.id,catalogRows:295,states,ground,shader,vector,checker_sha256:sha(fileURLToPath(import.meta.url)),original_checker_sha256:historical.programs['check-gate-runtime.mjs'],original_report_sha256:historical.programs['runtime260/runtime-placement.json']};
const out=path.join(host,'runtime260');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'recovered-runtime-placement.json'),JSON.stringify(output,null,2)+'\n');
console.log(output.id,states[259].length,states[260].length,ground.length,vector.length);
