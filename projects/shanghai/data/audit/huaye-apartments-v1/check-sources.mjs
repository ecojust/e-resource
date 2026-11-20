/** Verify strict two-feature vector replacement, retained neighbors and exact ground probes. */
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import * as THREE from '../../../vendor/three.module.js';
import {CandidateCityClipper} from '../../../src/candidate-city-clipping.js';
import {candidateGeometryContains} from '../../../src/candidate-city-integrations.js';
import {planCandidateVectorClipping} from '../../../src/candidate-vector-clipping.js';

const audit=path.dirname(fileURLToPath(import.meta.url)),project=path.resolve(audit,'../../..');
const read=p=>JSON.parse(fs.readFileSync(p));
const sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const contractFile=path.join(audit,'final-placement-contract.json'),m=read(contractFile);
const placementFile=path.join(audit,'placement-geometry.json'),placement=read(placementFile);
const src=read(path.join(project,'source/precise',m.id,'footprint-review.json'));
const sourceTable=process.argv[2];
assert.equal(sha(sourceTable),src.frozen_bindings['feature-table.json.gz'].sha256);
const data=JSON.parse(gunzipSync(fs.readFileSync(sourceTable)));
const external=[518,2148,1032],records=data.features.filter(f=>external.includes(f.localId)||src.owners.some(o=>o.local_id===f.localId));
assert.equal(records.length,5);
const clip={id:m.id,geometry:m.replacement_geometry,source_feature_ids:m.source_feature_ids,owners:m.owners};
const features=records.map(r=>({type:'Feature',id:r.key.split(':')[1],properties:{},geometry:r.geometry}));
const tests=[];
for(const from of ['openmaptiles','overture-buildings']){
  const plan=planCandidateVectorClipping(features,{candidateClips:[clip]},{source:from,sourceLayer:'building'});
  assert.equal(plan.stats.clippingErrors,0);assert.equal(plan.stats.residualComponents,0);
  assert.deepEqual([...plan.desired.values()].map(x=>x.id).sort(),m.source_feature_ids.building.toSorted());
  tests.push({source:from,removed_source_ids:[...plan.desired.values()].map(r=>r.id),unrelated_retained:external});
}
for(const sample of placement.ground_probes)assert.equal(candidateGeometryContains(m.collision_geometry,sample.world),sample.blocked);
const k=6371008.8*Math.cos(m.lat*Math.PI/180),log=v=>Math.asinh(Math.tan(v*Math.PI/180));
const gc=(lon,lat,z=0)=>new THREE.Vector3((lon-m.lng)*Math.PI/180*k,z,(log(m.lat)-log(lat))*k);
const clipper=new CandidateCityClipper({THREE,geographicPosition:gc});
clipper.update([clip]);
const scopeTests=[];
for(const ids of [...src.near_groups.map(g=>g.ids),external]){
  const group=new THREE.Group();group.add(new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial()));
  clipper.bindObject(group,{parent:{id:src.macro_id},ids});
  const scope=clipper.objects.get(group).scope;
  const selected=m.owners.filter(o=>ids.includes(o.feature_local_id));
  assert.equal(selected.length>0,scope.triangles>0);
  assert.deepEqual([...scope.clipIds].sort(),selected.map(o=>o.feature_local_id).sort());
  scopeTests.push({tile_members:ids,selected_owners:[...scope.clipIds],triangles:scope.triangles});
  clipper.releaseObject(group);
}
const count=clipper.getState().triangles;clipper.dispose();
fs.writeFileSync(path.join(audit,'runtime-source-checks.json'),JSON.stringify({id:m.id,contract_sha256:sha(contractFile),
  placement_sha256:sha(placementFile),script_sha256:sha(fileURLToPath(import.meta.url)),vector:tests,scopes:scopeTests,
  map_shader_triangles:count,collision_probes:placement.ground_probes},null,2)+'\n');
console.log('Verified multi-owner source filtering and collision.');
