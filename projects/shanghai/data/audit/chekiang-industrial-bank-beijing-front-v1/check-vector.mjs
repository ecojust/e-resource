/** Replay the signed fallback feature with the proposed street-corner detail and all existing clipping rules. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const audit=path.dirname(fileURLToPath(import.meta.url));
const project=process.env.SHANGHAI_PROJECT_ROOT || path.resolve(audit,'../../..');
const read=p=>JSON.parse(fs.readFileSync(p));
const hash=b=>createHash('sha256').update(b).digest('hex');
const modulePath=path.join(project,'src/candidate-vector-clipping.js');
const {planCandidateVectorClipping}=await import(pathToFileURL(modulePath));
const contract=read(path.join(process.env.QA_CONTRACT_DIRECTORY || audit,'final-placement-contract.json'));
const tile=read(process.argv[2]),catalog=read(process.argv[3]);
assert.equal(contract.id,'huangpu-chekiang-industrial-bank-beijing-front');
assert.equal(contract.replacement_geometry,null);
assert.deepEqual(contract.source_feature_ids,{building:[],building_part:[]});
assert.equal(tile.sha256,'e6a2578dd38fdc6ef28737b68ea1e59181efe7d2fbde1d812f76f0a555833495');
assert.equal(tile.nearby_features.length,27);
const subjects=catalog.models.filter(m=>m.id===contract.id);
assert.equal(subjects.length,0);
function rules(models) {
 return models.filter(m=>m.replacement_geometry).map(v=>({id:v.id,geometry:v.replacement_geometry,source_feature_ids:v.source_feature_ids,owner:v.owner,...(v.osm_replacement_geometry&&{osm_replacement_geometry:v.osm_replacement_geometry})}));
}
const before=rules(catalog.models),after=rules([...catalog.models,contract]);
assert.deepEqual(before,after);
const tested=[];
for (const feature of tile.nearby_features) {
 const input={...feature,type:'Feature'};
 const options={source:'openmaptiles',sourceLayer:'building'};
 const a=planCandidateVectorClipping([input],{candidateClips:before},options);
 const b=planCandidateVectorClipping([input],{candidateClips:after},options);
 assert.equal(a.stats.clippingErrors,0);assert.deepEqual(a,b);
 tested.push({feature:feature.id,component:feature.component,geometry_sha256:hash(JSON.stringify(feature.geometry)),result_sha256:hash(JSON.stringify(b))});
}
assert(tested.some(p=>p.feature===116367960 && p.component===17));
assert(tested.some(p=>p.feature===116293700 && p.component===10));
fs.writeFileSync(process.argv[4],JSON.stringify({passed:true,id:contract.id,predecessor_catalog_sha256:hash(fs.readFileSync(process.argv[3])),retained_existing_clip_rules:before.length,original_tile_sha256:tile.sha256,checked_unchanged_components:tested,module_sha256:hash(fs.readFileSync(modulePath)),checker_sha256:hash(fs.readFileSync(fileURLToPath(import.meta.url)))},null,2)+'\n');
