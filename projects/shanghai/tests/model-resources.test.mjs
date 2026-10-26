import assert from 'node:assert/strict';
import * as THREE from '../vendor/three.module.js';
import {disposeModelResources} from '../src/model-resources.js';

let closed = 0, sharedClosed = 0;
const bitmap = {close(){closed++;}};
const color = new THREE.Texture(bitmap), rough = new THREE.Texture(bitmap);
const shared = new THREE.Texture({close(){sharedClosed++;}});
shared.userData.shared = true;
const material = new THREE.MeshStandardMaterial({map:color, roughnessMap:rough, envMap:shared});
const geometry = new THREE.BoxGeometry();
const instances = new THREE.InstancedMesh(geometry, material, 2);
const group = new THREE.Group();
group.add(instances, new THREE.Mesh(geometry, material));
const counts = {geometry:0, material:0, instance:0, color:0, rough:0, shared:0};
for (const [key, value] of Object.entries({geometry, material, instance:instances, color, rough, shared})) {
  value.addEventListener('dispose', () => counts[key]++);
}
disposeModelResources(group);
assert.deepEqual(counts, {geometry:1, material:1, instance:1, color:1, rough:1, shared:0});
assert.equal(closed, 1, 'one bitmap shared by two owned textures is closed once');
assert.equal(sharedClosed, 0, 'viewer-owned reflection stays alive');
console.log('PASS: glTF textures, shared maps, ImageBitmaps and instance buffers');
