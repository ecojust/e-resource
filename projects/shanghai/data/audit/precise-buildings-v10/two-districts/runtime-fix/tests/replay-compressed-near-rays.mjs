import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import '../module-resolution.mjs';
import * as THREE from '/workspace/shanghai_project/vendor/three.module.js';
const {GLTFLoader} = await import('/workspace/shanghai_project/vendor/GLTFLoader.js');
const {MeshoptDecoder} = await import('/workspace/shanghai_project/vendor/meshopt_decoder.module.js');
const original = await import('/workspace/shanghai_project/src/realistic-lighting.js');
const fixed = await import('../payload/src/realistic-lighting.js');
const here = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const file = path.join(here, '../candidate27-app/assets/city-overrides-v6/14-13716-6693/3_-1-s0-s0.glb.gz');
const packed = await fs.readFile(file), binary = gunzipSync(packed);
const sha256 = value => createHash('sha256').update(value).digest('hex');
const describe = async source => {const b = await fs.readFile(source); return {source, bytes: b.length, sha256: sha256(b)};};
assert.equal(packed.length, 63098);
assert.equal(sha256(packed), 'ab5cd230bc5ce3fa9678e547560801a86909956dd05353266ab84ce13e441d4d');
const origin = [121.387939453125, 31.250377682707793];
const anchor = [121.39653056849184, 31.251712691858646];
const radians = Math.PI / 180, radius = 6378137, scale = Math.cos(origin[1] * radians);
const anchorPosition = new THREE.Vector3(radius * (anchor[0] - origin[0]) * radians * scale, 0,
  -radius * (Math.log(Math.tan(Math.PI / 4 + anchor[1] * radians / 2))
    - Math.log(Math.tan(Math.PI / 4 + origin[1] * radians / 2))) * scale);
const solarDirection = new THREE.Vector3(.76, .87, .50).normalize();

async function replay(module) {
  const group = (await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder)
    .parseAsync(binary.buffer.slice(binary.byteOffset, binary.byteOffset + binary.byteLength), '')).scene;
  const scene = new THREE.Scene(); scene.add(group);
  const renderer = {shadowMap: {enabled: false, autoUpdate: true, type: THREE.BasicShadowMap}};
  const lighting = module.createRealisticLighting({THREE, scene, renderer, reflections: false});
  lighting.configureModel(group, {detailed: true});
  group.traverse(object => {if (object.name === 'city_target_putuo-zhenru-main-hall') object.visible = false;});
  lighting.update({position: anchorPosition, now: 1000}); group.updateMatrixWorld(true);
  const visible = [], eligible = [], glazing = [];
  let hiddenTargetMeshes = 0;
  group.traverse(mesh => {
    if (!mesh.isMesh) return;
    for (let node = mesh; node; node = node.parent) if (!node.visible) {hiddenTargetMeshes++; return;}
    visible.push(mesh); if (mesh.castShadow) eligible.push(mesh);
    if (mesh.material.name === 'Inferred dark glazing') glazing.push({name: mesh.material.name,
      transparent: mesh.material.transparent, opacity: mesh.material.opacity, casts: mesh.castShadow});
  });
  assert.equal(hiddenTargetMeshes, 8); assert.equal(visible.length, 18); assert.equal(glazing.length, 4);
  const ray = new THREE.Raycaster(); ray.far = 80;
  const samples = [];
  for (let north = 6; north >= -6; north--) for (let east = -6; east <= 6; east++) {
    ray.set(new THREE.Vector3(anchorPosition.x + east, 6, anchorPosition.z - north), solarDirection);
    const full = ray.intersectObjects(visible, false), shadow = ray.intersectObjects(eligible, false);
    samples.push({east, north, height: 6, visibleHit: full[0]?.object.material.name ?? null,
      visibleDistance: full[0]?.distance ?? null, shadowHit: shadow[0]?.object.material.name ?? null,
      shadowDistance: shadow[0]?.distance ?? null, opaqueGlazingLeak: full.length > 0 && shadow.length === 0});
  }
  const stats = lighting.getState(); lighting.dispose();
  const result = {hiddenTargetMeshes, visibleNeighborMeshes: visible.length, casterMeshes: eligible.length,
    glazing, samples, counts: {leaks: samples.filter(x => x.opaqueGlazingLeak).length,
      blocked: samples.filter(x => x.shadowHit !== null).length,
      noNeighborHit: samples.filter(x => x.visibleHit === null).length},
    lighting: {shadowSize: stats.shadowSize, halfExtent: stats.shadowHalfExtent,
      bias: stats.shadowBias, normalBias: stats.shadowNormalBias, radius: stats.shadowRadius}};
  const materials = new Set();
  group.traverse(mesh => {if (!mesh.isMesh) return; mesh.geometry.dispose(); materials.add(mesh.material);});
  materials.forEach(material => material.dispose());
  return result;
}

const before = await replay(original), after = await replay(fixed);
assert.deepEqual(before.counts, {leaks: 50, blocked: 101, noNeighborHit: 18});
assert.deepEqual(after.counts, {leaks: 0, blocked: 151, noNeighborHit: 18});
assert.deepEqual(before.lighting, after.lighting);
assert.equal(after.casterMeshes - before.casterMeshes, 4);
for (let index = 0; index < before.samples.length; index++) {
  assert.equal(before.samples[index].visibleHit, after.samples[index].visibleHit);
  assert.equal(before.samples[index].visibleDistance, after.samples[index].visibleDistance);
  if (before.samples[index].shadowHit) assert.ok(after.samples[index].shadowHit);
}
console.log(JSON.stringify({schema: 'actual-compressed-near-shadow-ray-differential-v1', passed: true,
  compressed_near: {source: path.resolve(file), bytes: packed.length, sha256: sha256(packed)},
  original_runtime: await describe('/workspace/shanghai_project/src/realistic-lighting.js'),
  patched_runtime: await describe(path.join(here, 'payload/src/realistic-lighting.js')),
  checker: await describe(fileURLToPath(import.meta.url)), original_macro_origin: origin, anchor,
  solar_direction_xyz: solarDirection.toArray(), probe_grid: {east: [-6, 6], north: [-6, 6], step: 1,
    height: 6, maximum_ray_distance: 80, count: 169}, before, after,
  scope: 'Finite CPU solar rays through actual decoded compressed near geometry, using old/new production caster eligibility. Hidden target group excluded; all18 preserved-neighbor meshes retained. Points at6m are a diagnostic roof-region plane, not registered screenshot pixels. Front-side ray tests from receiver toward sun correspond to back-side shadow casting of these front-sided opaque facade meshes.',
  limitations: ['No GPU raster, shadow-depth sampling or browser A/B acceptance is claimed.',
    'No neighbor geometry, real window transparency, interior floors or model material data are changed.',
    'Actual full11-frame rerun and root image review remain required.'], browser_passed: false}, null, 2));
