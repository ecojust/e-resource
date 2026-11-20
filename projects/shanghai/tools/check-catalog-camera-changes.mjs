/** Verify two exported city scenes. Pass their repository roots, the comma-separated
 * changed landmark IDs, and a JSON output path. Compare every other map record
 * and the production camera calculations for phone, compact and wide viewports. */
import {readFile,writeFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const [beforeRoot,afterRoot,list,output]=process.argv.slice(2);
const changed=new Set(list.split(','));
const cases=[
 {width:390,height:844,insets:{left:8,right:8,top:100,bottom:208}},
 {width:870,height:660,insets:{left:281,right:8,top:90,bottom:158}},
 {width:1280,height:800,insets:{left:340,right:14,top:85,bottom:146}}];
async function get(root){
 const dir=resolve(root,'projects/shanghai');
 const module=await import(pathToFileURL(join(dir,'src/candidate-overview-camera.js')).href);
 const asset=await readFile(join(dir,'data/candidate-city-integrations.json'));
 return {compute:module.candidateOverviewCamera,models:JSON.parse(asset).models,sha256:createHash('sha256').update(asset).digest('hex')};
}
const [before,after]=await Promise.all([get(beforeRoot),get(afterRoot)]);
assert.deepEqual(before.models.map(r=>r.id),after.models.map(r=>r.id));
const results={};
for(const [index,prior] of before.models.entries()){
 const current=after.models[index];
 const pairs=cases.map(size=>[before.compute({...prior,city_integration:true},size),after.compute({...current,city_integration:true},size)]);
 if(changed.has(prior.id)){
  assert(pairs.every(([a,b])=>JSON.stringify(a)!==JSON.stringify(b)));
  results[prior.id]=pairs;continue;
 }
 assert.deepEqual(prior,current);
 for(const [a,b] of pairs)assert.deepEqual(a,b);
}
assert.equal(Object.keys(results).length,changed.size);
const report={changed_models:[...changed],preceding_sha256:before.sha256,updated_sha256:after.sha256,
 unchanged_model_records:before.models.length-changed.size,unchanged_other_camera_comparisons:(before.models.length-changed.size)*cases.length,
 viewports:cases,changed_target_results:results};
await writeFile(output,JSON.stringify(report,null,2)+'\n');
