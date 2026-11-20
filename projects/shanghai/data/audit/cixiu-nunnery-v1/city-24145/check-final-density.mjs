import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [beforeRoot, afterRoot, output] = process.argv.slice(2);
const from = (root, file) => path.join(root, file);
const moduleAt = (root, file) => import(pathToFileURL(from(root, file)));
const {CandidateCityClipper: Previous} = await moduleAt(beforeRoot, 'src/candidate-city-clipping.js');
const {CandidateCityClipper} = await moduleAt(afterRoot, 'src/candidate-city-clipping.js');
const {CandidateSourceSections} = await moduleAt(afterRoot, 'src/candidate-source-sections.js');
const THREE = await moduleAt(afterRoot, 'vendor/three.module.js');
const beforeFile = from(beforeRoot, 'data/candidate-city-integrations.json');
const afterFile = from(afterRoot, 'data/candidate-city-integrations.json');
const fixture = JSON.parse(fs.readFileSync(from(afterRoot,'tests/fixtures/dense-owner-clipping.json')));
const h=b=>createHash('sha256').update(b).digest('hex'),[lng,lat]=fixture.anchor,r=Math.PI/180,k=6371008.8*Math.cos(lat*r);
function parse(file){const bytes=fs.readFileSync(file);return {data:JSON.parse(bytes),sha256:h(bytes)};}
function allCuts(catalog) {
  const byId=new Map();
  for(const row of catalog.models){
    if(row.replacement_geometry)byId.set(row.id,{id:row.id,owner:row.owner,owners:row.owners,geometry:row.replacement_geometry});
    if(row.site_replacement)byId.set(row.site_replacement.id,row.site_replacement);
  }
  return [...byId.values(),...catalog.models.flatMap(row=>row.display_height_clips||[])];
}
const options={THREE,geographicPosition:(x,y,z=0)=>new THREE.Vector3((x-lng)*r*k,z*Math.cos(lat*r)/Math.cos(y*r),(Math.asinh(Math.tan(lat*r))-Math.asinh(Math.tan(y*r)))*k)};
const before=parse(beforeFile),after=parse(afterFile),a=allCuts(before.data),b=allCuts(after.data);
assert.deepEqual(after.data.models.slice(0,-1),before.data.models);assert.equal(after.data.models.at(-1).id,fixture.nunnery.id);
const previous=new Previous(options), current=new CandidateCityClipper(options);
const max=clip=>Math.max(...[...clip.macroTables.values()].map(t=>t.triangles),clip.defaultTable.triangles);
previous.update(a);assert.equal(max(previous),320);let error;
try{previous.update(b);}catch(e){error=e.message;}
assert.match(error,/候选模型局部边界过于复杂/);assert.equal(max(previous),320);
current.update(a);const original=current.getState();
const target=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshBasicMaterial());
current.bindObject(target,{id:fixture.macro+'/near',parent:{id:fixture.macro},ids:fixture.nearMembership});
current.update(b);const state=current.getState();assert.equal(max(current),322);
assert.equal(state.denseMacroTables.length,1);assert.equal(state.denseMacroTables[0].maxFeatureSpan,24);assert.equal(state.ownerScopedSources[0].triangles,2);assert.equal(state.triangles-original.triangles,2);
const report={passed:true,before:{count:before.data.resulting_city_count,catalog:before.sha256,triangles:original.triangles,largest:320},after:{count:after.data.resulting_city_count,catalog:after.sha256,triangles:state.triangles,largest:322,dense:state.denseMacroTables,near:state.ownerScopedSources[0]},oldError:error,oldStatePreservedAfterRejectedUpdate:320,macro:fixture.macro,sourceBindings:fixture.sourceHashes,oldClipper:h(fs.readFileSync(from(beforeRoot,'src/candidate-city-clipping.js'))),newClipper:h(fs.readFileSync(from(afterRoot,'src/candidate-city-clipping.js')))};
const scene = new THREE.Scene(), visibleMacro = new THREE.Group();
scene.add(visibleMacro);
const sections = new CandidateSourceSections(scene, options.geographicPosition);
const row = after.data.models.at(-1);
const caps = row.source_section_caps;
sections.sync([row], [{ id: row.owner.macro_id, sha256: caps.far_sha256, object: visibleMacro }]);
const built = sections.getState();
const declared = caps.geometry.coordinates.reduce((n,line)=>n+line.length-1,0);
assert.equal(declared,2);
assert.equal(built.length,1);
assert.equal(built[0].segments,declared);
assert.equal(built[0].roof_m,caps.roof_m);
report.actualSourceSection = { fixture_expected_before:1, signed_contract_segments:declared, built:built[0], source_sha256:h(fs.readFileSync(from(afterRoot,'src/candidate-source-sections.js'))) };
sections.dispose();
report.checker_sha256 = h(fs.readFileSync(new URL(import.meta.url)));
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');current.dispose();previous.dispose();target.material.dispose();target.geometry.dispose();
