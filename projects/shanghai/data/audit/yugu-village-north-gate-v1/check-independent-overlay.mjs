/** Compare whole-city clipping, neighboring vector features and ground collisions for a freestanding model. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const audit = path.resolve(process.argv[4] || path.dirname(fileURLToPath(import.meta.url)));
const project = path.resolve(process.argv[2]);
const prior = path.resolve(process.argv[3]);
const read = file => JSON.parse(fs.readFileSync(file));
const sha = file => createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const load = name => import(pathToFileURL(path.join(project, name)));
const THREE = await load('vendor/three.module.js');
const {CandidateCityClipper} = await load('src/candidate-city-clipping.js');
const {candidateGeometryContains} = await load('src/candidate-city-integrations.js');
const {planCandidateVectorClipping} = await load('src/candidate-vector-clipping.js');
const file = 'data/candidate-city-integrations.json';
const current = read(path.join(project, file));
const previous = read(path.join(prior, file));
const row = current.models.at(-1);
const contract = read(path.join(audit, 'final-placement-contract.json'));
assert.equal(row.id, contract.id);
assert.equal(previous.resulting_city_count + 1, current.resulting_city_count);
assert.deepEqual(previous.models, current.models.slice(0, -1));
assert.equal(row.replacement_geometry, null);
assert.deepEqual(row.source_feature_ids, {building: [], building_part: []});
for (const key of ['owner', 'owners', 'site_replacement', 'source_section_caps', 'display_height_clips']) {
  assert.ok(!row[key], key);
}
assert.deepEqual(row.collision_geometry, contract.collision_geometry);
const review = read(path.join(project, 'source/precise', row.id, 'footprint-review.json'));
const geo = read(path.join(audit, 'placement-geometry.json'));
const retained = new Set(geo.ground_probes.flatMap(probe => probe.ownerLocalId == null ? [] : [probe.ownerLocalId]));
assert.ok(retained.size > 0);
const radians = Math.PI / 180;
const radius = 6371008.8 * Math.cos(row.lat * radians);
const mercator = latitude => Math.asinh(Math.tan(latitude * radians));
function position(lng, lat, z = 0) {
  return new THREE.Vector3((lng - row.lng) * radians * radius,
    z * Math.cos(row.lat * radians) / Math.cos(lat * radians),
    (mercator(row.lat) - mercator(lat)) * radius);
}
function evaluate(models) {
  const base = new Map();
  for (const m of models) {
    if (m.replacement_geometry) base.set(m.id, {...m, geometry: m.replacement_geometry});
    if (m.site_replacement) base.set(m.site_replacement.id, m.site_replacement);
  }
  const clips = [...base.values()];
  const clipper = new CandidateCityClipper({THREE, geographicPosition: position});
  const meshes = review.near_tiles.map(group => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial());
    clipper.bindObject(mesh, {id: group.id, parent: {id: review.frozen_macro}, ids: group.feature_local_ids});
    return mesh;
  });
  clipper.update([...clips, ...models.flatMap(m => m.display_height_clips || [])]);
  const state = clipper.getState();
  const result = {triangles: state.triangles, macros: state.macroTextures,
    largestMacro: Math.max(clipper.defaultTable.triangles, ...[...clipper.macroTables.values()].map(t => t.triangles)),
    near: state.ownerScopedSources, vectors: []};
  for (const owner of review.owners.filter(o => retained.has(o.local_id))) {
    const feature = {type: 'Feature', id: owner.local_id, properties: {id: owner.key.slice(9)}, geometry: owner.geometry};
    for (const source of ['openmaptiles', 'overture-buildings']) {
      const plan = planCandidateVectorClipping([feature], {candidateClips: clips}, {source, sourceLayer: 'building'});
      assert.equal(plan.stats.clippingErrors, 0);
      assert.equal(plan.desired.size, 0);
      assert.equal(plan.residualData.features.length, 0);
      result.vectors.push({source, owner: owner.local_id, retained: true});
    }
  }
  clipper.dispose();
  for (const mesh of meshes) {
    mesh.geometry.dispose();
    mesh.material.dispose();
  }
  return result;
}
const before = evaluate(previous.models);
const after = evaluate(current.models);
assert.deepEqual(after, before);
const ground = geo.ground_probes.map(probe => {
  const blocked = candidateGeometryContains(row.collision_geometry, probe.wgs84);
  assert.equal(blocked, probe.modelObstacle, probe.name);
  assert.equal(candidateGeometryContains(row.replacement_geometry, probe.wgs84), false);
  return {name: probe.name, wgs84: probe.wgs84, addedGroundCollision: blocked, cut: false};
});
const report = {id: row.id, catalogCount: current.resulting_city_count,
  beforeCatalog: sha(path.join(prior, file)), afterCatalog: sha(path.join(project, file)),
  checkerSHA256: sha(fileURLToPath(import.meta.url)), before, after, ground, passed: true};
fs.writeFileSync(path.join(audit, 'runtime-overlay.json'), JSON.stringify(report, null, 2) + '\n');
