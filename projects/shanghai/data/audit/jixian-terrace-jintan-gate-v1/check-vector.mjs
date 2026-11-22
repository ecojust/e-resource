/** Compare the actual complete fallback building groups with either gate LOD active. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const audit=path.dirname(fileURLToPath(import.meta.url));
const project=path.resolve(audit,'../../..');
const read=f=>JSON.parse(fs.readFileSync(f));
const sha=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const [vectorFile,manifestFile,contractFile,catalogFile,outFile]=process.argv.slice(2);
const vector=read(vectorFile),mf=read(manifestFile),current=read(contractFile),catalog=read(catalogFile);
assert.equal(current.id,mf.id);
assert.equal(current.replacement_geometry,null);
assert.deepEqual(current.source_feature_ids,{building:[],building_part:[]});
assert.deepEqual(vector.features.map(f=>[f.id,f.geometry.coordinates.length]),[[117595520,743],[3006517100,22],[5056225290,10]]);
const {CandidateCityState}=await import(pathToFileURL(path.join(project,'src/candidate-city-integrations.js')));
const {markVerifiedOrdinaryAsset}=await import(pathToFileURL(path.join(project,'src/ordinary-asset-verification.js')));
const {planCandidateVectorClipping}=await import(pathToFileURL(path.join(project,'src/candidate-vector-clipping.js')));
const existing=catalog.models.filter(r=>r.replacement_geometry).map(r=>({id:r.id,geometry:r.replacement_geometry,osm_replacement_geometry:r.osm_replacement_geometry,owner:r.owner,owners:r.owners,source_feature_ids:r.source_feature_ids}));
assert(!catalog.models.some(r=>r.id===current.id));
const plan=rules=>planCandidateVectorClipping(vector.features,{candidateClips:rules},{source:'openmaptiles',sourceLayer:'building'});
const previous=plan(existing),results={};
assert.equal(previous.stats.clippingErrors,0);
for(const [role,variant,activeVariant] of [['full','web','full'],['lod','lod','distant']]){
  const scene={visible:true},object={visible:true,parent:scene};
  const asset=mf.assets[role];
  assert.equal(sha(path.join(path.dirname(manifestFile),asset.file)),current.model_geometry_sha256[variant]);
  markVerifiedOrdinaryAsset(object,{modelId:current.id,variant,asset});
  const record={...current,city_integration:true,status:'loaded',object,activeVariant,assets:{[variant]:asset}};
  const state=new CandidateCityState({getScene:()=>scene,getRecords:()=>new Map([[current.id,record]])});
  state.sync();
  assert.equal(state.active.length,1);assert.equal(state.active[0].id,current.id);assert.equal(state.clips.length,0);
  const next=plan([...existing,...state.clips]);
  assert.equal(next.signature,previous.signature);assert.deepEqual(next.residualData,previous.residualData);
  assert.deepEqual([...next.desired],[...previous.desired]);assert.equal(next.stats.clippingErrors,0);
  results[role]={active:true,asset_sha256:asset.sha256,added_clips:0,states_unchanged:true,components:775,source_statistics:next.stats};
}
fs.writeFileSync(outFile,JSON.stringify({passed:true,id:current.id,source_sha256:vector.sha256,input_catalog_sha256:sha(catalogFile),signed_meshes:results,groups:3,components:775,source_cut_m2:0},null,2)+'\n');
