import assert from 'node:assert/strict';
import '../module-resolution.mjs';
import * as THREE from '/workspace/shanghai_project/vendor/three.module.js';
const original = await import('/workspace/shanghai_project/src/realistic-lighting.js');
const fixed = await import('../payload/src/realistic-lighting.js');

const cases = [
  {id: 'opaque-exact-name', name: 'Inferred dark glazing', expected: true, changed: true},
  {id: 'opaque-threshold-.99', name: 'Inferred dark glazing', opacity: .99, expected: true, changed: true},
  {id: 'transparent-exact-name', name: 'Inferred dark glazing', transparent: true, expected: false},
  {id: 'sub-threshold-opacity', name: 'Inferred dark glazing', opacity: .989, expected: false},
  {id: 'zero-opacity', name: 'Inferred dark glazing', opacity: 0, expected: false},
  {id: 'suffix-name-excluded', name: 'Inferred dark glazing.001', expected: false},
  {id: 'case-name-excluded', name: 'inferred dark glazing', expected: false},
  {id: 'precise-glazing-unchanged', name: 'Recessed reflecting glazing', expected: false},
  {id: 'other-glass-unchanged', name: 'Deep_blue_glass', expected: false},
  {id: 'photo-glass-unchanged', name: 'PhotoFacade_test_glass', photographic: true, expected: false},
  {id: 'ordinary-wall-unchanged', name: 'Limestone', expected: true},
  {id: 'filter-veto-still-enforced', name: 'Inferred dark glazing', filter: false, expected: false},
  {id: 'filter-permit-eligible', name: 'Inferred dark glazing', filter: true, expected: true, changed: true},
  {id: 'not-detailed-still-excluded', name: 'Inferred dark glazing', detailed: false, expected: false},
  {id: 'outside-local-radius-still-excluded', name: 'Inferred dark glazing', x: 1000, expected: false},
];

function run(module, value, dispose = false) {
  const renderer = {shadowMap: {enabled: false, autoUpdate: true, type: THREE.BasicShadowMap}};
  const scene = new THREE.Scene();
  const lighting = module.createRealisticLighting({THREE, scene, renderer, reflections: false});
  const material = value.photographic ? new THREE.MeshBasicMaterial({map: new THREE.Texture()})
    : new THREE.MeshStandardMaterial({transparent: value.transparent ?? false, opacity: value.opacity ?? 1});
  material.name = value.name;
  const visibleMaterial = {side: material.side, color: material.color.toArray(), opacity: material.opacity,
    transparent: material.transparent, roughness: material.roughness, metalness: material.metalness};
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(2, 2, 2), material);
  mesh.castShadow = value.priorCast ?? false;
  mesh.receiveShadow = value.priorReceive ?? false;
  const originalFlags = {cast: mesh.castShadow, receive: mesh.receiveShadow, shadowSide: material.shadowSide};
  const group = new THREE.Group(); group.add(mesh); group.position.x = value.x ?? 0; scene.add(group);
  const filtered = [];
  lighting.configureModel(group, {detailed: value.detailed ?? true,
    casterFilter: value.filter === undefined ? null : candidate => {filtered.push(candidate); return value.filter;}});
  lighting.update({position: new THREE.Vector3(), now: 1000});
  const result = {cast: mesh.castShadow, receive: mesh.receiveShadow,
    filterCalls: filtered.length, shadowSize: lighting.stats.shadowSize,
    bias: lighting.stats.shadowBias, normalBias: lighting.stats.shadowNormalBias, radius: lighting.stats.shadowRadius};
  assert.ok(filtered.every(candidate => candidate === mesh));
  assert.deepEqual({side: material.side, color: material.color.toArray(), opacity: material.opacity,
    transparent: material.transparent, roughness: material.roughness, metalness: material.metalness}, visibleMaterial);
  if (dispose) lighting.dispose(); else lighting.releaseModel(group);
  assert.deepEqual({cast: mesh.castShadow, receive: mesh.receiveShadow, shadowSide: material.shadowSide}, originalFlags,
    value.id + ': release/dispose restores original flags');
  if (!dispose) lighting.dispose();
  assert.equal(renderer.shadowMap.enabled, false); assert.equal(renderer.shadowMap.autoUpdate, true);
  assert.equal(renderer.shadowMap.type, THREE.BasicShadowMap);
  assert.equal(lighting.sun.parent, null); assert.equal(lighting.getState().registeredModels, 0);
  mesh.geometry.dispose(); material.map?.dispose(); material.dispose();
  return result;
}

const controls = cases.map(value => {
  const before = run(original, value), after = run(fixed, value);
  assert.equal(after.cast, value.expected, value.id);
  assert.equal(before.cast, value.changed ? false : value.expected, value.id + ': original control');
  for (const key of ['receive', 'shadowSize', 'bias', 'normalBias', 'radius']) assert.equal(before[key], after[key]);
  if (value.filter !== undefined) assert.equal(after.filterCalls, 1);
  return {id: value.id, passed: true, before, after};
});
for (const priorCast of [false, true]) for (const priorReceive of [false, true]) {
  const value = {id: 'dispose-restoration', name: 'Inferred dark glazing', priorCast, priorReceive};
  assert.equal(run(fixed, value, true).cast, true);
}
console.log(JSON.stringify({schema: 'opaque-inferred-shadow-cpu-controls-v1', passed: true,
  controls, disposalFlagCombinations: 4, shaderOrBrowserRun: false,
  scope: 'Actual production lighting module with vendored Three CPU objects; finite eligibility, filtering, state restoration and unchanged lighting/material controls.'}, null, 2));
