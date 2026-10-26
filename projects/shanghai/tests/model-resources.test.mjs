import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from '../vendor/three.module.js';
import {disposeModelResources, estimateModelBufferResources, countExpandedTriangles} from '../src/model-resources.js';
import {estimateGeometryBytes} from '../src/local-model-streamer.js';
import {estimateDetailResources} from '../src/detail-model-cache.js';

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

test('shared geometry is resident once while instance capacity and active triangles are independent', () => {
  const geometry = new THREE.BoxGeometry(), material = new THREE.MeshBasicMaterial();
  const first = new THREE.InstancedMesh(geometry, material, 2);
  const second = new THREE.InstancedMesh(geometry, material, 3);
  first.setColorAt(0, new THREE.Color('white'));
  const group = new THREE.Group();
  group.add(first, second, new THREE.Mesh(geometry, material));
  const base = geometry.index.array.byteLength + Object.values(geometry.attributes).reduce((n, a) => n + a.array.byteLength, 0);
  const instanceCapacity = (2 + 3) * 16 * 4 + 2 * 3 * 4;
  const resources = estimateModelBufferResources(group);
  assert.equal(resources.geometryBytes, base, 'do not multiply shared base buffers by mesh or instance count');
  assert.equal(resources.instanceBytes, instanceCapacity, 'matrix and color storage are additional to base geometry');
  assert.equal(estimateGeometryBytes(group), base + instanceCapacity);
  assert.equal(estimateDetailResources(group).totalBytes, base + instanceCapacity);
  assert.equal(countExpandedTriangles(group), 12 * (2 + 3 + 1));
  second.count = 0;
  assert.equal(countExpandedTriangles(group), 12 * (2 + 1), 'zero active instances issue no triangles');
  assert.equal(estimateGeometryBytes(group), base + instanceCapacity, 'zero active instances do not release capacity');
});

test('interleaved and explicitly shared attributes count once across distinct geometries', () => {
  const interleaved = new THREE.InterleavedBuffer(new Float32Array(36), 6);
  const positions = new THREE.InterleavedBufferAttribute(interleaved, 3, 0);
  const normals = new THREE.InterleavedBufferAttribute(interleaved, 3, 3);
  const indices = new THREE.BufferAttribute(new Uint16Array([0, 1, 2, 3, 4, 5]), 1);
  const first = new THREE.BufferGeometry().setAttribute('position', positions).setAttribute('normal', normals).setIndex(indices);
  const second = new THREE.BufferGeometry().setAttribute('position', positions).setIndex(indices);
  const group = new THREE.Group();
  group.add(new THREE.Mesh(first), new THREE.Mesh(second));
  assert.equal(estimateGeometryBytes(group), interleaved.array.byteLength + indices.array.byteLength);
  assert.equal(countExpandedTriangles(group), 4, 'shared storage still draws once per Mesh');
});

test('distinct GPU attributes are not deduplicated merely because their CPU arrays alias', () => {
  const array = new Float32Array(18), geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(array, 3));
  geometry.setAttribute('normal', new THREE.BufferAttribute(array, 3));
  const mesh = new THREE.Mesh(geometry);
  assert.equal(estimateGeometryBytes(mesh), array.byteLength * 2, 'r180 WebGLAttributes keys uploads by BufferAttribute');
  assert.equal(estimateDetailResources(mesh).geometryBytes, array.byteLength * 2);
});

test('instance morph weights and shared skeleton texture are counted once with their real float payload', () => {
  const geometry = new THREE.BoxGeometry(), material = new THREE.MeshBasicMaterial();
  const instance = new THREE.InstancedMesh(geometry, material, 2);
  instance.morphTexture = new THREE.DataTexture(new Float32Array(6), 3, 2, THREE.RedFormat, THREE.FloatType);
  const skeleton = new THREE.Skeleton(Array.from({length: 5}, () => new THREE.Bone()));
  const first = new THREE.SkinnedMesh(geometry, material), second = new THREE.SkinnedMesh(geometry, material);
  first.skeleton = skeleton; second.skeleton = skeleton;
  const group = new THREE.Group(); group.add(instance, first, second);
  let resources = estimateModelBufferResources(group);
  assert.equal(resources.instanceBytes, instance.instanceMatrix.array.byteLength + 6 * 4);
  assert.equal(resources.skeletonBytes, 8 * 8 * 4 * 4, 'first draw reserves r180 padded bone texture');
  assert.equal(skeleton.boneTexture, null, 'accounting does not allocate or modify the model');
  skeleton.computeBoneTexture();
  resources = estimateModelBufferResources(group);
  assert.equal(resources.skeletonBytes, skeleton.boneTexture.image.data.byteLength);
  assert.equal(resources.skeletonBytes, 1024, 'two SkinnedMeshes sharing one skeleton do not double count it');
  assert.equal(estimateGeometryBytes(group), resources.totalBytes);
  assert.equal(estimateDetailResources(group).totalBytes, resources.totalBytes);
  material.map = skeleton.boneTexture;
  const detail = estimateDetailResources(group);
  assert.equal(detail.totalBytes, resources.totalBytes, 'an auxiliary texture also referenced by a material is not counted twice');
  assert.equal(detail.textureBytes, 0);
});

test('expanded triangle count honors index zero, draw range, and finite instanced-geometry capacity', () => {
  const geometry = new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(new Float32Array(27), 3));
  const mesh = new THREE.Mesh(geometry);
  geometry.setDrawRange(3, 6);
  assert.equal(countExpandedTriangles(mesh), 2);
  geometry.setIndex(new THREE.BufferAttribute(new Uint16Array(0), 1));
  assert.equal(countExpandedTriangles(mesh), 0, 'empty index must not fall back to position count');
  const instanced = new THREE.InstancedBufferGeometry();
  instanced.setAttribute('position', new THREE.BufferAttribute(new Float32Array(9), 3));
  instanced.setAttribute('offset', new THREE.InstancedBufferAttribute(new Float32Array(12), 3));
  const instances = new THREE.Mesh(instanced);
  assert.equal(countExpandedTriangles(instances), 4, 'default Infinity is bounded by the allocated instance attribute');
  instanced.instanceCount = 2;
  assert.equal(countExpandedTriangles(instances), 2);
  const group = new THREE.Group(); group.add(instances, new THREE.Line(geometry), new THREE.Points(geometry));
  assert.equal(countExpandedTriangles(group), 2, 'lines and points are not triangles');
});
