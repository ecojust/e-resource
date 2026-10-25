import assert from 'node:assert/strict';
import * as THREE from '../vendor/three.module.js';
import {createRealisticLighting, isArchitecturalGlazing} from '../src/realistic-lighting.js';

const renderer = {shadowMap: {enabled: false, autoUpdate: true, type: THREE.BasicShadowMap, needsUpdate: false}};
const scene = new THREE.Scene();
const oldBackground = new THREE.Color('#123456');
const oldEnvironment = new THREE.Texture();
scene.background = oldBackground;
scene.environment = oldEnvironment;
const lighting = createRealisticLighting({THREE, scene, renderer, reflections: false});
assert.equal(scene.background, oldBackground);
assert.equal(scene.environment, oldEnvironment);
assert.equal(lighting.getState().groundReceiverPolygons, 0);
assert.equal(lighting.stats.shadowSize, 1024);
assert.equal(renderer.shadowMap.autoUpdate, false);
assert.equal(lighting.sun.shadow.autoUpdate, false);

function model(x, name = 'Limestone') {
  const group = new THREE.Group();
  const wall = new THREE.Mesh(new THREE.BoxGeometry(15, 30, 12), new THREE.MeshStandardMaterial());
  wall.material.name = name;
  wall.material.side = THREE.DoubleSide;
  wall.position.y = 15;
  group.add(wall);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(8, 15), new THREE.MeshStandardMaterial());
  glass.material.name = 'Recessed reflecting glazing';
  glass.material.side = THREE.DoubleSide;
  glass.position.set(0, 15, 6.1);
  group.add(glass);
  group.position.x = x;
  scene.add(group);
  return {group, wall, glass};
}

for (const name of ['recessed blue grey glazing.001', 'Recessed reflecting glazing', 'Deep_blue_glass', 'Reflected_slate_glass']) {
  const material = new THREE.MeshStandardMaterial(); material.name = name;
  assert.equal(isArchitecturalGlazing(material), true, name);
}
for (const name of ['Clock opal glass', 'BundLampGlass', 'Bronze window framing', 'glazed bronze divisions', 'Sandstone cornice', 'window frame']) {
  const material = new THREE.MeshStandardMaterial(); material.name = name;
  assert.equal(isArchitecturalGlazing(material), false, name);
}

const near = model(20);
const far = model(1200);
const generic = model(5);
const street = model(0, 'BundRoadSurface');
lighting.configureModel(near.group, {detailed: true});
lighting.configureModel(far.group, {detailed: true});
lighting.configureModel(generic.group);
lighting.configureModel(street.group, {ground: true});
assert.equal(lighting.update({position: new THREE.Vector3(0, 2, 0), now: 0}), true);
assert.equal(near.wall.castShadow, true);
assert.equal(near.glass.castShadow, false);
assert.equal(near.wall.receiveShadow, true);
assert.equal(near.wall.material.shadowSide, THREE.BackSide, 'double-sided closed stone casts with back faces');
assert.equal(near.wall.material.side, THREE.DoubleSide, 'visible material side is preserved');
assert.equal(near.glass.material.shadowSide, null, 'glass depth side is untouched');
assert.equal(far.wall.castShadow, false);
assert.equal(generic.wall.castShadow, false);
assert.equal(generic.wall.receiveShadow, false);
assert.equal(street.wall.castShadow, false, 'ground-only road never enters static caster pass');
assert.equal(street.wall.receiveShadow, true, 'ground-only road receives building shadows');
assert.equal(street.wall.material.shadowSide, null, 'ground-only material depth side is untouched');
assert.equal(lighting.getState().activeCasterModels, 1);
assert.equal(lighting.sun.shadow.needsUpdate, true);
assert.equal(renderer.shadowMap.needsUpdate, true);

function consumeShadow() {
  // Three clears both flags when its shadow render has completed.
  lighting.sun.shadow.needsUpdate = false;
  renderer.shadowMap.needsUpdate = false;
}
consumeShadow();
const firstTarget = lighting.sun.target.position.clone();
for (let frame = 1; frame <= 120; frame++) {
  assert.equal(lighting.update({position: new THREE.Vector3(3, 2, 2), now: frame * 16}), false);
}
assert.equal(lighting.getState().shadowRefreshRequests, 1);
assert.equal(renderer.shadowMap.needsUpdate, false);
assert.deepEqual(lighting.sun.target.position, firstTarget);
assert.equal(lighting.update({position: new THREE.Vector3(13, 2, 0), now: 2000}), true);
consumeShadow();
assert.equal(lighting.update({position: new THREE.Vector3(26, 2, 0), now: 2100}), false);
assert.equal(lighting.update({position: new THREE.Vector3(26, 2, 0), now: 2300}), true);
consumeShadow();
lighting.invalidate();
assert.equal(lighting.update({position: new THREE.Vector3(26, 2, 0), now: 2600}), true);
consumeShadow();

const beforeOutside = lighting.getState().shadowRefreshRequests;
for (let i = 1; i <= 20; i++) {
  assert.equal(lighting.update({position: new THREE.Vector3(3000 + i * 50, 2, 0), now: 3000 + i * 300}), false);
}
assert.equal(lighting.getState().shadowRefreshRequests, beforeOutside);
assert.equal(lighting.sun.shadow.intensity, 0);
assert.equal(near.wall.castShadow, false);
assert.equal(far.wall.castShadow, false);
assert.equal(renderer.shadowMap.needsUpdate, false);
assert.equal(lighting.update({position: new THREE.Vector3(20, 2, 0), now: 10000}), true);
consumeShadow();

near.group.visible = false;
assert.equal(lighting.update({position: new THREE.Vector3(20, 2, 0), now: 10300}), false);
assert.equal(lighting.getState().activeCasterModels, 0);
assert.equal(near.wall.castShadow, false);
near.group.visible = true;
assert.equal(lighting.update({position: new THREE.Vector3(20, 2, 0), now: 10600}), true);
consumeShadow();
assert.equal(lighting.update({position: new THREE.Vector3(20, 2, 0), enabled: false, now: 10900}), false);
assert.equal(lighting.sun.shadow.intensity, 0);
assert.equal(lighting.update({position: new THREE.Vector3(20, 2, 0), enabled: true, now: 11200}), true);
consumeShadow();

// Explicit land polygon has an excluded water/courtyard hole; no rectangle is
// inserted by the helper when the caller has no mapped footprint to supply.
lighting.setGroundFootprints([[
  [[0, 0], [100, 0], [100, 100], [0, 100]],
  [[40, 40], [60, 40], [60, 60], [40, 60]],
]]);
assert.equal(lighting.getState().groundReceiverPolygons, 1);
const receiver = scene.children.find(object => object.name === 'Mapped land-only shadow receiver');
assert.equal(receiver.receiveShadow, true);
assert.equal(receiver.castShadow, false);
assert.equal(receiver.material.transparent, true);
assert.equal(receiver.material.depthWrite, false);
const positions = receiver.geometry.getAttribute('position');
const indices = receiver.geometry.getIndex();
let area = 0;
for (let i = 0; i < indices.count; i += 3) {
  const a = new THREE.Vector3().fromBufferAttribute(positions, indices.getX(i));
  const b = new THREE.Vector3().fromBufferAttribute(positions, indices.getX(i + 1));
  const c = new THREE.Vector3().fromBufferAttribute(positions, indices.getX(i + 2));
  area += new THREE.Vector3().subVectors(b, a).cross(new THREE.Vector3().subVectors(c, a)).length() / 2;
}
assert.ok(Math.abs(area - 9600) < .01, `excluded hole preserved, area=${area}`);
const shader = {uniforms: {}, vertexShader: THREE.ShaderLib.shadow.vertexShader, fragmentShader: THREE.ShaderLib.shadow.fragmentShader};
receiver.material.onBeforeCompile(shader);
assert.ok(shader.vertexShader.includes('vGroundShadowXZ=(modelMatrix*vec4(position,1.0)).xz;'));
assert.ok(shader.fragmentShader.includes('distance(vGroundShadowXZ,uGroundShadowCenter)'));
assert.ok(shader.uniforms.uGroundShadowRadius.value > 0);
lighting.setGroundFootprints([]);
assert.equal(lighting.getState().groundReceiverPolygons, 0);
assert.equal(receiver.parent, null);

// Explicit LOD release restores owned flags; detached groups are also pruned.
lighting.releaseModel(near.group);
assert.equal(near.wall.castShadow, false);
assert.equal(near.wall.receiveShadow, false);
assert.equal(near.wall.material.shadowSide, null, 'LOD release restores original shadow side');
scene.remove(far.group);
lighting.update({position: new THREE.Vector3(20, 2, 0), now: 12000});
assert.equal(lighting.getState().registeredModels, 2);
assert.equal(far.wall.receiveShadow, false);
assert.equal(far.wall.material.shadowSide, null, 'detached group restores original shadow side');
lighting.dispose();
assert.equal(renderer.shadowMap.enabled, false);
assert.equal(renderer.shadowMap.autoUpdate, true);
assert.equal(renderer.shadowMap.type, THREE.BasicShadowMap);
assert.equal(lighting.sun.parent, null);
assert.equal(lighting.update(), false);
assert.equal(scene.environment, oldEnvironment);
assert.equal(scene.background, oldBackground);

const lowRenderer = {shadowMap: {enabled: false, autoUpdate: true, type: THREE.BasicShadowMap}};
const low = createRealisticLighting({THREE, scene: new THREE.Scene(), renderer: lowRenderer, reflections: false, lowMemory: true});
assert.equal(low.getState().shadowSize, 512);
low.dispose();

// Two loaded LOD groups can share a material: release must restore its shadow
// side only after the last registered user stops using it.
const sharedScene = new THREE.Scene();
const shared = createRealisticLighting({THREE, scene: sharedScene, renderer: lowRenderer, reflections: false});
const sharedStone = new THREE.MeshStandardMaterial({side: THREE.DoubleSide});
sharedStone.name = 'Closed limestone trim';
const sharedGroups = [0, 1].map(index => {
  const group = new THREE.Group();
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(2, 2, 2), sharedStone);
  group.position.x = index * 5;
  group.add(mesh); sharedScene.add(group);
  shared.configureModel(group, {detailed: true});
  return group;
});
assert.equal(sharedStone.shadowSide, THREE.BackSide);
shared.releaseModel(sharedGroups[0]);
assert.equal(sharedStone.shadowSide, THREE.BackSide);
shared.releaseModel(sharedGroups[1]);
assert.equal(sharedStone.shadowSide, null);
const flagMaterial = new THREE.MeshStandardMaterial({side: THREE.DoubleSide});
flagMaterial.name = 'Flag red';
const flag = new THREE.Mesh(new THREE.PlaneGeometry(3, 2), flagMaterial);
sharedScene.add(flag); shared.configureModel(flag, {detailed: true});
assert.equal(flagMaterial.shadowSide, null, 'thin flag retains both depth faces');
shared.dispose();
console.log('Lighting checks passed: cached local shadows, caster filtering, LOD release, land-only receiver holes, shader hook, glazing selector and disposal.');
