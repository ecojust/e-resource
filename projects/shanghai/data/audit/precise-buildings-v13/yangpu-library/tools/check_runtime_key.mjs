// Pure QA-probe check against a saved actual failure snapshot; no live browser.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const dir=path.dirname(fileURLToPath(import.meta.url));
const fixture=JSON.parse(fs.readFileSync(path.join(dir,'failure-owner-fixture.json'),'utf8'));
const current=fs.readFileSync(path.join(dir,'target-probe.js'),'utf8');
const oldLine="const near=parent?.near.find(r=>r.id===owner.near_owner_id);";
const newLine="const near=parent?.near.find(r=>r.id===owner.macro_id+'/'+owner.near_owner_id);";
assert.equal(current.split(newLine).length,2);
const original=current.replace(newLine,oldLine);
const sha=text=>createHash('sha256').update(text).digest('hex');
assert.equal(sha(original),'d41206dd68c82e8474ea70648121625ca07f42f06235c6826da6dd98a221f580');
function observe(source,record,audit){
  const start=source.indexOf('  p.targetAudit=()=>{');
  const end=source.indexOf('  return {readOnly',start);
  assert.ok(start>=0&&end>start);
  const p={audit:()=>audit,catalogState:()=>({controlOnly:true}),sourceReadiness:()=>({controlOnly:true})};
  return new Function('p','record',source.slice(start,end)+'\nreturn p.targetAudit();')(p,record);
}
function accepted(value){return value.passed&&value.active&&value.hiddenNear;}
const old=observe(original,fixture.record,fixture.actual_audit);
const fixed=observe(current,fixture.record,fixture.actual_audit);
assert.equal(old.hiddenNear,false);assert.equal(accepted(old),false);
assert.equal(accepted(fixed),true);assert.equal(fixed.neighborsExact,true);
assert.equal(fixed.near.preservedNeighborIDs.length,9);
assert.equal(fixed.near.groups.find(g=>g.landmark===fixture.record.id).visible,false);
const cases=[];
for(const name of ['wrong_metadata_macro','wrong_runtime_near_prefix','wrong_near_owner','missing_neighbor','substituted_neighbor','visible_old_target']){
  const record=structuredClone(fixture.record),audit=structuredClone(fixture.actual_audit);
  const parent=audit.parents.find(p=>p.id===record.owner.macro_id);
  const near=parent.near.find(n=>n.id===record.owner.macro_id+'/'+record.owner.near_owner_id);
  if(name==='wrong_metadata_macro')record.owner.macro_id='14-13720-6693';
  if(name==='wrong_runtime_near_prefix')near.id='14-13720-6693/'+record.owner.near_owner_id;
  if(name==='wrong_near_owner')record.owner.near_owner_id+='-wrong';
  if(name==='missing_neighbor')near.preservedNeighborIDs.pop();
  if(name==='substituted_neighbor')near.preservedNeighborIDs[0]=record.owner.feature_local_id;
  if(name==='visible_old_target')near.groups.find(g=>g.landmark===record.id).visible=true;
  const value=observe(current,record,audit);
  assert.equal(accepted(value),false,name+' must fail the same full/near readiness predicate');
  cases.push({name,rejected:true,passed:value.passed,hiddenNear:value.hiddenNear,neighborsExact:value.neighborsExact,errors:value.errors});
}
const report={schema:'runtime-near-key-saved-snapshot-check-v2',passed:true,
  original_probe_sha256:sha(original),fixed_probe_sha256:sha(current),
  failed_browser_report:fixture.provenance.failed_report,
  actual_asset:fixture.actual_asset,actual_runtime_near_id:fixed.near.id,
  original_lookup:{passed:old.passed,hiddenNear:old.hiddenNear,full_near_accepted:accepted(old)},
  fixed_lookup:{passed:fixed.passed,hiddenNear:fixed.hiddenNear,neighborsExact:fixed.neighborsExact,
    neighbor_count:fixed.near.preservedNeighborIDs.length,full_near_accepted:accepted(fixed)},negative_controls:cases,
  scope:'Existing actual failed snapshot proves the QA lookup mismatch. Pure mutated copies exercise six negative controls. No live runtime is changed, no browser is run, and this does not replace a fresh complete browser acceptance.'};
fs.writeFileSync(path.join(dir,'runtime-key-controls.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,actual_runtime_near_id:report.actual_runtime_near_id,original_lookup:report.original_lookup,fixed_lookup:report.fixed_lookup,negative_control_count:cases.length}));
