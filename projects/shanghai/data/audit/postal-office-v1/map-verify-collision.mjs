/** Check the serialized final WGS84 collision with actual production functions. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const project=path.resolve(process.env.POSTAL_REPO||'/workspace/e-resource')+'/projects/shanghai/';
const out=path.resolve(process.env.POSTAL_MAPPING_WORK||'/workspace/shanghai-postal-mapping')+'/';
const {validCandidateGeometry,candidateGeometryContains}=await import(project+'src/candidate-city-integrations.js');
const contract=JSON.parse(fs.readFileSync(out+'final-placement-contract.json'));
const probes=JSON.parse(fs.readFileSync(out+'ground-probes.json')).ground_probes;
const qa=JSON.parse(fs.readFileSync(out+'qa-map-input.json'));
assert.equal(contract.id,'hongkou-general-post-office');
assert.equal(contract.collision_geometry.type,'Polygon');
assert(validCandidateGeometry(contract.collision_geometry,{collision:true}));
const results=[];
for(const probe of probes){
 const expected=probe.expected==='building',actual=candidateGeometryContains(contract.collision_geometry,probe.wgs84);
 assert.equal(actual,expected,probe.name);
 results.push({name:probe.name,wgs84:probe.wgs84,expected,actual});
}
const sourceResults=[];
for(const probe of [...qa.actual_source_roof_probes,qa.source_joint_retained_roof_probe]){
 const actual=candidateGeometryContains(contract.replacement_geometry,probe.position_wgs84);
 assert.equal(actual,probe.expected_target_clip);
 sourceResults.push({feature_local_id:probe.feature_local_id,scope:probe===qa.source_joint_retained_roof_probe?'retained shared joint':'actual roof sample',expected:probe.expected_target_clip,actual});
}
const report={schema:'postal-collision-runtime-semantics-v1',geometry_type:contract.collision_geometry.type,closed_ring_point_counts:contract.collision_geometry.coordinates.map(r=>r.length),production_geometry_validator_passed:true,production_contains_ground_probes:results,source_mask_contains_probes:sourceResults,all_passed:true,contract_sha256:crypto.createHash('sha256').update(fs.readFileSync(out+'final-placement-contract.json')).digest('hex'),runtime_module_sha256:crypto.createHash('sha256').update(fs.readFileSync(project+'src/candidate-city-integrations.js')).digest('hex'),scope:'Production serialized geometry validation and point containment only; actual GLB structural coverage is independently checked by map-finalize-placement.py. No browser input or GPU pixels claimed.'};
fs.writeFileSync(out+'collision-runtime-verification.json',JSON.stringify(report,null,2)+'\n');
const footprint=JSON.parse(fs.readFileSync(out+'footprint-review.json'));
footprint.runtime_validation.serialized_geometry_and_containment={
 report:'data/audit/postal-office-v1/collision-runtime-verification.json',
 bytes:fs.statSync(out+'collision-runtime-verification.json').size,
 sha256:crypto.createHash('sha256').update(fs.readFileSync(out+'collision-runtime-verification.json')).digest('hex'),
 all_passed:report.all_passed,
 scope:report.scope,
};
fs.writeFileSync(out+'footprint-review.json',JSON.stringify(footprint,null,2)+'\n');
process.stdout.write(JSON.stringify({passed:true,ground_probes:results.length,source_probes:sourceResults.length})+'\n');
