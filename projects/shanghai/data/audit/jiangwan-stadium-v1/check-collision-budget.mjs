// Recheck the immutable previous77-entry catalogue without reading model assets.
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {mergeCandidateCityModels,validCandidateGeometry} from '../../../src/candidate-city-integrations.js';

const project=new URL('../../../',import.meta.url),baseline='96e4dfaff588222475c25a66af1c84a24b45a475';
const old=path=>execFileSync('git',['show',baseline+':projects/shanghai/'+path],{cwd:project,maxBuffer:8*1024*1024});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const verifier=new URL('src/ordinary-asset-verification.js',project).href;
const oldSource=old('src/candidate-city-integrations.js').toString().replace("'./ordinary-asset-verification.js'",JSON.stringify(verifier));
const previous=await import('data:text/javascript;base64,'+Buffer.from(oldSource).toString('base64'));
const base=JSON.parse(old('data/landmarks.json')),catalog=JSON.parse(old('data/candidate-city-integrations.json'));
const before=previous.mergeCandidateCityModels(base,catalog),after=mergeCandidateCityModels(base,catalog);
assert.equal(catalog.models.length,37);assert.equal(after.length,77);assert.deepEqual(after,before);
for(const row of catalog.models){
  assert.equal(validCandidateGeometry(row.collision_geometry,{collision:true}),true);
  if(row.replacement_geometry)assert.equal(validCandidateGeometry(row.replacement_geometry),true);
  if(row.site_replacement)assert.equal(validCandidateGeometry(row.site_replacement.geometry),true);
}
const files=['src/candidate-city-integrations.js','tools/build_candidate_city_integrations.py','tests/candidate-geometry.test.mjs','tests/candidate-catalog-increment.test.py'];
const report={passed:true,baseline_commit:baseline,candidate_rows:catalog.models.length,total_destinations:after.length,merged_records_deep_equal:true,merged_records_sha256:sha(JSON.stringify(after)),scope:'Metadata-only actual previous37 records and40 baseline rows. No previous GLB/native assets were opened.',bindings:files.map(file=>({file,sha256:sha(readFileSync(new URL(file,project)))})),reproducer:{file:'check-collision-budget.mjs',sha256:sha(readFileSync(new URL(import.meta.url)))}};
writeFileSync(new URL('collision-budget-previous-models.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,previous_candidates:37,total_destinations:77,merged_records_deep_equal:true}));
