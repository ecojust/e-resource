// Exercise the height-limited garden wall, preserved lower floor and nearby source footprints.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';

const audit=path.dirname(fileURLToPath(import.meta.url));
const project=path.resolve(audit,'../../..');
const runtime=process.env.SHANGHAI_PROJECT_ROOT||project;
const read=f=>JSON.parse(fs.readFileSync(f));
const sha=b=>createHash('sha256').update(b).digest('hex');
const load=r=>import(pathToFileURL(path.join(runtime,r)));
const THREE=await load('vendor/three.module.js');
const {CandidateCityClipper}=await load('src/candidate-city-clipping.js');
const {CandidateCityState,mergeCandidateCityModels,candidateGeometryContains}=await load('src/candidate-city-integrations.js');
const {markVerifiedOrdinaryAsset}=await load('src/ordinary-asset-verification.js');
const {planCandidateVectorClipping}=await load('src/candidate-vector-clipping.js');
const contract=read(path.join(audit,'final-placement-contract.json'));
const review=read(path.join(project,'source/precise',contract.id,'footprint-review.json'));
const surfaces=read(path.join(audit,'placement-geometry.json'));
const catalogFile=path.join(runtime,'data/candidate-city-integrations.json');
const catalog=read(catalogFile);
const row=catalog.models.find(r=>r.id===contract.id);
const preflight=process.argv.includes('--preflight');
assert.ok(row||preflight,'Use a registered scene or request the explicit private preflight');
const prefix='assets/models/candidates/'+contract.id+'/';
const manifest=read(path.join(project,prefix,'manifest.json'));
const assets=Object.fromEntries(['web','lod'].map((key,i)=>{
  const entry=manifest.assets[['full','lod'][i]];
  const file=prefix+entry.file,bytes=fs.readFileSync(path.join(project,file));
  assert.equal(sha(bytes),entry.sha256);assert.equal(bytes.length,entry.bytes);
  return [key,{...entry,file}];
}));
const target=row||{...contract,name:manifest.name,assets,kind:'building',height_m:contract.bounds_glb.max[1]};
assert.deepEqual(target.site_replacement,contract.site_replacement);
assert.equal(target.replacement_geometry,null);
const [registered]=mergeCandidateCityModels([],{schema:'candidate-city-integrations-v1',models:[target]});
const scene=new THREE.Scene(),records=new Map([[registered.id,registered]]);
const state=new CandidateCityState({getRecords:()=>records,getScene:()=>scene});
const rad=Math.PI/180,k=6371008.8*Math.cos(target.lat*rad),log=lat=>Math.asinh(Math.tan(lat*rad));
const local=(lng,lat,z=0)=>new THREE.Vector3((lng-target.lng)*rad*k,z*k/(6371008.8*Math.cos(lat*rad)),(log(target.lat)-log(lat))*k);
function geographic(x,y){
  const h=target.heading*rad,e=x*Math.cos(h)+y*Math.sin(h),n=-x*Math.sin(h)+y*Math.cos(h);
  return [target.lng+e/k/rad,Math.atan(Math.sinh(log(target.lat)+n/k))/rad];
}
const original=review.owners.find(r=>r.local_id===673);
const ground=surfaces.ground_probes.map(p=>({...p,position:geographic(...p.xy)}));
const reports={};
for(const [variant,role] of [['full','web'],['distant','lod']]){
  registered.object=new THREE.Group();
  registered.status='loaded';registered.activeVariant=variant;
  scene.add(registered.object);
  markVerifiedOrdinaryAsset(registered.object,{modelId:registered.id,variant:role,asset:assets[role]});
  state.sync();
  assert.equal(state.active.length,1);
  const gpu=new CandidateCityClipper({THREE,geographicPosition:local});gpu.update(state.displayClips);
  assert.equal(gpu.getState().triangles,2);
  const cut=state.displayClips[0], flags=state.getState();
  assert.equal(cut.owner.feature_local_id,673);
  assert.equal(cut.min_height,5.48);assert.ok(cut.max_height>15.90&&cut.max_height<15.92);
  assert.deepEqual(flags.displayClips[0].height_reference,contract.site_replacement.height_reference);
  assert.equal(cut.source_section_caps.roof_m,surfaces.source_variants.far.owner_source_height_m);
  assert.equal(cut.source_section_caps.base_m,5.48);
  // The aggregate texture here contains only this building's two triangles.
  const tex=gpu.texture.image.data;
  const low=local(...cut.height_reference,cut.min_height).y;
  const high=local(...cut.height_reference,cut.max_height).y;
  const texRanges=[];
  for(const offset of [0,16]){
    assert.ok(Math.abs(tex[offset+6]-low)<.00001&&Math.abs(tex[offset+7]-high)<.00001);
    assert.equal(tex[offset+12],673);
    texRanges.push([tex[offset+6],tex[offset+7]]);
  }
  for(const p of ground){
    const existing=candidateGeometryContains(original.geometry,p.position);
    const clipped=state.clipsPoint(...p.position,{name:'overture-buildings',layer:'building',propertyId:original.key.slice(9)});
    const blocked=state.collisions().some(s=>candidateGeometryContains(s.geometry,p.position));
    assert.equal(clipped,p.source_cut,p.name);assert.equal(blocked,p.model_obstacle,p.name);
    assert.equal(blocked||existing&&!clipped,p.expected_map==='building',p.name);
  }
  const vectors=[];
  for(const provider of ['overture-buildings','openmaptiles']){
    for(const footprint of [original,...review.owners.filter(r=>review.selection.checked_neighbors.includes(r.local_id))]){
      const feature={type:'Feature',id:footprint.local_id,properties:{id:footprint.key.slice(9)},geometry:footprint.geometry};
      const plan=planCandidateVectorClipping([feature],{candidateClips:state.clips},{source:provider,sourceLayer:'building'});
      assert.equal(plan.stats.clippingErrors,0);
      assert.equal(plan.stats.partialIDs,footprint.local_id===673?1:0);
      vectors.push({provider,owner:footprint.local_id,partial:plan.stats.partialIDs});
    }
  }
  for(const neighbor of review.selection.checked_neighbors) {
    const item=review.owners.find(r=>r.local_id===neighbor);
    assert.ok(item&&vectors.filter(v=>v.owner===neighbor&&v.partial===0).length===2);
  }
  gpu.dispose();
  reports[role]={sha256:assets[role].sha256,ground:ground.length,vector:vectors,textureHeightRanges:texRanges};
  registered.object.visible=false;state.sync();assert.deepEqual(state.displayClips,[]);assert.deepEqual(state.collisions(),[]);
  scene.remove(registered.object);
}
// A group may already carry clips from other registered sites. Exercise the
// complete production list as well as the per-object, verified-asset state above.
const group=review.near_tiles.find(g=>g.feature_local_ids.includes(contract.owner.feature_local_id));
function groupDraw(rows) {
  const clips=[];
  for(const item of rows) {
    if(item.replacement_geometry)clips.push({id:item.id,owner:item.owner,owners:item.owners,geometry:item.replacement_geometry});
    if(item.site_replacement)clips.push(item.site_replacement);
    clips.push(...(item.display_height_clips||[]));
  }
  const gpu=new CandidateCityClipper({THREE,geographicPosition:local});
  const mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());
  gpu.bindObject(mesh,{id:group.id,parent:{id:review.frozen_macro},ids:group.feature_local_ids});
  gpu.update(clips);
  const state=gpu.getState(), draw=state.ownerScopedSources.find(v=>v.id===group.id);
  const result={global_triangles:state.triangles,texture_tables:state.macroTextures,
                group:draw.id,scoped_triangles:draw.triangles,owners:draw.clip_feature_local_ids};
  gpu.dispose();mesh.geometry.dispose();mesh.material.dispose();
  return result;
}
const predecessor=catalog.models.filter(v=>v.id!==target.id);
const both={before:groupDraw(predecessor),after:groupDraw([...predecessor,target])};
assert.equal(both.after.global_triangles-both.before.global_triangles,2);
assert.equal(both.after.scoped_triangles-both.before.scoped_triangles,2);
assert.deepEqual([...both.after.owners].sort((a,b)=>a-b),[...both.before.owners,contract.owner.feature_local_id].sort((a,b)=>a-b));
const result={id:target.id,preflight:!row,city:both,catalogCount:catalog.resulting_city_count,
  catalogSHA256:sha(fs.readFileSync(catalogFile)),clipperSHA256:sha(fs.readFileSync(path.join(runtime,'src/candidate-city-clipping.js'))),
  checkerSHA256:sha(fs.readFileSync(fileURLToPath(import.meta.url))),reports};
fs.writeFileSync(process.argv[2],JSON.stringify(result,null,2)+'\n');
