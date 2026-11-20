// Verify both actual gate variants in the city state and retain every existing source and adjacent house.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';

const audit=path.dirname(fileURLToPath(import.meta.url));
const project=path.resolve(audit,'../../..');
const site=path.resolve(process.argv[2]||project);
const read=p=>JSON.parse(fs.readFileSync(p)),hash=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const load=p=>import(pathToFileURL(path.join(site,p)));
const THREE=await load('vendor/three.module.js');
const {mergeCandidateCityModels,CandidateCityState,candidateGeometryContains}=await load('src/candidate-city-integrations.js');
const {markVerifiedOrdinaryAsset}=await load('src/ordinary-asset-verification.js');
const {CandidateCityClipper}=await load('src/candidate-city-clipping.js');
const catPath=path.join(site,'data/candidate-city-integrations.json'),cat=read(catPath);
const contract=read(path.join(audit,'final-placement-contract.json'));
const geom=read(path.join(audit,'placement-geometry.json'));
const root='assets/models/candidates/'+contract.id+'/',mf=read(path.join(project,root,'manifest.json'));
const assets={};
for(const [variant,role] of [['web','full'],['lod','lod']]){
  const a=mf.assets[role],file=root+a.file;
  assert.equal(hash(path.join(project,file)),a.sha256);
  assets[variant]={...a,file};
}
const found=cat.models.find(m=>m.id===contract.id);
assert.ok(found||process.argv.includes('--preflight'));
const row=found||{...contract,kind:'building',name:mf.name,assets,height_m:mf.reference_height_m};
assert.ok(!row.owner&&!row.owners&&!row.replacement_geometry&&!row.site_replacement&&!row.display_height_clips);
assert.deepEqual(row.source_feature_ids,{building:[],building_part:[]});
assert.deepEqual(row.collision_geometry,contract.collision_geometry);
const [gate]=mergeCandidateCityModels([],{schema:'candidate-city-integrations-v1',models:[row]});
const scene=new THREE.Scene(),directory=new Map([[row.id,gate]]);
const state=new CandidateCityState({getRecords:()=>directory,getScene:()=>scene});
const rad=Math.PI/180,scale=6371008.8*Math.cos(row.lat*rad),h=row.heading*rad,lat0=Math.asinh(Math.tan(row.lat*rad));
function pos(x,y){return [row.lng+(x*Math.cos(h)+y*Math.sin(h))/scale/rad,
  Math.atan(Math.sinh(lat0+(-x*Math.sin(h)+y*Math.cos(h))/scale))/rad];}
const variants=[];
for(const [mode,key] of [['full','web'],['distant','lod']]){
  gate.status='loaded';gate.activeVariant=mode;gate.object=new THREE.Group();scene.add(gate.object);
  markVerifiedOrdinaryAsset(gate.object,{modelId:gate.id,variant:key,asset:assets[key]});state.sync();
  assert.equal(state.active.length,1);assert.deepEqual(state.clips,[]);assert.deepEqual(state.displayClips,[]);
  const gpu=new CandidateCityClipper({THREE,geographicPosition:()=>new THREE.Vector3()});
  gpu.update(state.displayClips);assert.equal(gpu.getState().triangles,0);gpu.dispose();
  const [floor]=state.collisions();
  const ground=geom.ground_samples.map(p=>{
    const xy=pos(p.x,p.y);assert.equal(candidateGeometryContains(floor.geometry,xy),p.blocked);
    return {...p,wgs84:xy};
  });
  const footprint=read(path.join(project,'source/precise',row.id,'footprint-review.json'));
  const neighborPoints=footprint.owners.map(o=>{
    const ring=o.geometry_wgs84.coordinates[0].slice(0,-1);
    const point=ring.reduce((q,t)=>[q[0]+t[0]/ring.length,q[1]+t[1]/ring.length],[0,0]);
    assert.equal(candidateGeometryContains(floor.geometry,point),false);
    for(const source of ['openmaptiles','overture-buildings'])
      assert.equal(state.clipsPoint(...point,{name:source,layer:'building',id:o.local_id}),false);
    return {id:o.local_id,point};
  });
  gate.object.visible=false;state.sync();
  assert.deepEqual(state.collisions(),[]);assert.deepEqual(state.displayClips,[]);
  variants.push({assetSHA256:assets[key].sha256,variant:key,ground,neighborPoints,sourceClipTriangles:0});
  scene.remove(gate.object);
}
const result={id:row.id,preflight:!found,cityCount:cat.resulting_city_count,catalogSHA256:hash(catPath),
  checkerSHA256:hash(fileURLToPath(import.meta.url)),clipperSHA256:hash(path.join(site,'src/candidate-city-clipping.js')),variants};
fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2)+'\n');
console.log('two verified variants',variants[0].ground.length,variants[0].neighborPoints.length,'no source clips');
