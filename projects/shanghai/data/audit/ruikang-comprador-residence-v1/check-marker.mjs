// Verify the historical marker against its signed viewer assets and the real city-state merger.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';

const audit=path.dirname(fileURLToPath(import.meta.url));
const project=path.resolve(audit,'../../..');
const runtime=process.env.SHANGHAI_PROJECT_ROOT||project;
const parse=f=>JSON.parse(fs.readFileSync(f));
const digest=b=>createHash('sha256').update(b).digest('hex');
const load=f=>import(pathToFileURL(path.join(runtime,f)));
const {validHistoricalSite}=await load('src/historical-view.js');
const {mergeCandidateCityModels,CandidateCityState}=await load('src/candidate-city-integrations.js');
const {walkingPose}=await load('src/precise-registration-ui.js');
const contract=parse(process.env.SHANGHAI_CONTRACT||path.join(audit,'final-placement-contract.json'));
const folder='assets/models/candidates/'+contract.id+'/';
const assetRoot=process.env.SHANGHAI_ASSETS_ROOT||project;
const manifest=parse(path.join(assetRoot,folder,'manifest.json'));
const assets=Object.fromEntries([['web','full'],['lod','lod']].map(([kind,role])=>{
  const entry=manifest.assets[role];
  const bytes=fs.readFileSync(path.join(assetRoot,folder,entry.file));
  assert.equal(bytes.length,entry.bytes);
  assert.equal(digest(bytes),entry.sha256);
  return [kind,{file:folder+entry.file,bytes:entry.bytes,sha256:entry.sha256}];
}));
const catalogFile=path.join(runtime,'data/candidate-city-integrations.json');
const catalog=parse(catalogFile);
const registered=catalog.models.find(v=>v.id===contract.id);
assert.ok(registered||process.argv.includes('--preflight'));
const row=registered||{
  id:contract.id,name:manifest.name,kind:'historical-site',districtId:'310101',district_name:'黄浦区',
  lng:contract.lng,lat:contract.lat,individual_page:manifest.viewer_page,candidate_manifest:folder+'manifest.json',
  historical_view:contract.historical_view,assets,navigation:contract.navigation,collision_geometry:null,
  replacement_geometry:null,source_feature_ids:contract.source_feature_ids,
};
assert.equal(validHistoricalSite(row),true);
assert.deepEqual(row.historical_view,{"kind":"archival-facade","listed_year":1999,"approximate_loss_year":2000,"evidence_kind":"reprinted-photograph","evidence_years":[2019,2019]});
assert.ok(!('owner' in row));
assert.deepEqual([row.lng,row.lat],[121.469,31.227]);
for(const key of ['lng','lat','historical_view','navigation','collision_geometry','replacement_geometry','source_feature_ids']){
  assert.deepEqual(row[key],contract[key]);
}
for(const role of ['web','lod']){
  assert.equal(row.assets[role].sha256,assets[role].sha256);
  assert.equal(row.assets[role].bytes,assets[role].bytes);
}
const [marker]=mergeCandidateCityModels([],{schema:'candidate-city-integrations-v1',models:[row]});
assert.equal(marker.kind,'historical-site');
assert.equal(marker.model,undefined);
assert.equal(marker.city_integration,undefined);
assert.equal(walkingPose(marker),null);
const state=new CandidateCityState({getRecords:()=>new Map([[marker.id,marker]]),getScene:()=>({})});
state.sync();assert.deepEqual(state.active,[]);assert.deepEqual(state.clips,[]);assert.deepEqual(state.displayClips,[]);
assert.deepEqual(state.collisions(),[]);
const checks={id:row.id,preflight:!registered,catalog_count:catalog.resulting_city_count,catalog_sha256:digest(fs.readFileSync(catalogFile)),
  years:row.historical_view,source_feature_ids:row.source_feature_ids,walking_pose:null,geometry:null,clip_count:state.clips.length,
  collisions:state.collisions().length,visible_city_models:state.active.length,verified_viewer_assets:assets,
  checker_sha256:digest(fs.readFileSync(fileURLToPath(import.meta.url))),runtime_signature:Object.fromEntries(
    ['src/historical-view.js','src/candidate-city-integrations.js','src/precise-registration-ui.js'].map(f=>[f,digest(fs.readFileSync(path.join(runtime,f)))]))};
fs.writeFileSync(process.argv[2],JSON.stringify(checks,null,2)+'\n');
console.log(checks.id,checks.preflight?'unregistered reference':'registered marker',checks.catalog_count,checks.clip_count,checks.collisions);
