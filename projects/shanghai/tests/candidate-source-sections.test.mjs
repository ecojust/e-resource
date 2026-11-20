import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../vendor/three.module.js';
import {CandidateCityState} from '../src/candidate-city-integrations.js';
import {CandidateSourceSections, validSourceSection} from '../src/candidate-source-sections.js';
import {markVerifiedOrdinaryAsset} from '../src/ordinary-asset-verification.js';

const farHash = 'b'.repeat(64);
const anchor = [121.4, 31.2];
const [x, y] = anchor;
const corners = [[x, y], [x, y+.001], [x+.002, y+.001], [x+.002, y], [x, y]];
const contract = {
  owner: {macro_id: 'macro', feature_local_id: 2764},
  replacement_geometry: {type: 'Polygon', coordinates: [corners]},
  source_section_caps: {
    geometry: {type: 'MultiLineString', coordinates: [corners.slice(0, 4)]},
    base_m: 0, roof_m: 24.1, height_reference: anchor, far_sha256: farHash,
  },
};

test('a cut section requires both the verified candidate and its visible source macro', () => {
  const scene = new THREE.Scene();
  const project = (lng, lat, altitude=0) => new THREE.Vector3((lng-x)*100000, altitude*2, (y-lat)*100000);
  const sections = new CandidateSourceSections(scene, project);
  const source = {id: 'macro', sha256: farHash, object: new THREE.Group()};
  const row = {...contract, id: 'example', city_integration: true, status: 'loaded', activeVariant: 'full',
    object: new THREE.Group(), assets: {web: {sha256: 'a'.repeat(64), file: 'model.glb', bytes: 100}}};
  scene.add(row.object, source.object);
  const records = new Map([[row.id, row]]);
  const state = new CandidateCityState({getRecords: () => records, getScene: () => scene});
  const update = () => {
    state.sync();
    sections.sync(state.active, [source]);
  };
  update();
  assert.deepEqual(sections.getState(), []);
  markVerifiedOrdinaryAsset(row.object, {modelId: row.id, variant: 'web', asset: row.assets.web});
  source.sha256='c'.repeat(64);
  update();
  assert.deepEqual(sections.getState(), []);
  source.sha256=farHash;
  update();
  assert.deepEqual(sections.getState(), [{id:row.id, ...row.owner, segments:3, roof_m:24.1}]);
  const mesh=scene.getObjectByName('example · coarse source cut');
  const position=mesh.geometry.getAttribute('position');
  assert.equal(position.count,8);
  assert.equal(mesh.geometry.index.count,18, 'only the three open seam segments have faces');
  assert.ok(Math.abs(position.getY(1)-48.2)<1e-5, 'macro-latitude height scale matches source');
  assert.equal(position.getY(0),0);
  update();
  assert.equal(scene.getObjectByName(mesh.name),mesh);
  let disposed=0;
  mesh.geometry.addEventListener('dispose',()=>disposed++);
  mesh.material.addEventListener('dispose',()=>disposed++);
  source.object.visible=false;
  update();
  assert.equal(disposed,2);
  assert.deepEqual(sections.getState(),[]);
  source.object.visible=true;
  update();
  assert.equal(sections.getState().length,1);
  row.object.visible=false;
  update();
  assert.deepEqual(sections.getState(),[]);
  row.object.visible=true;
  source.object.removeFromParent();
  update();
  assert.deepEqual(sections.getState(),[]);
});

test('section metadata binds finite lines, a roof elevation and a specific source', () => {
  assert.ok(validSourceSection(contract));
  for (const change of [
    {base_m:25}, {roof_m:NaN}, {height_reference:[121,100]}, {far_sha256:''},
    {geometry:{type:'LineString',coordinates:corners}}, {geometry:{type:'MultiLineString',coordinates:[[[x,y]]]}},
  ]) assert.equal(validSourceSection({...contract,source_section_caps:{...contract.source_section_caps,...change}}),false);
  assert.equal(validSourceSection({...contract,owner:{macro_id:'macro'}}),false);
  assert.equal(validSourceSection({...contract,replacement_geometry:null}),false);
});
