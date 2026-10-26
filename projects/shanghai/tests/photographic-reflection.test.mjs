import assert from 'node:assert/strict';
import * as RealTHREE from '../vendor/three.module.js';
import {HDRLoader} from '../vendor/HDRLoader.js';
import {createRealisticLighting} from '../src/realistic-lighting.js';

// Exercise asynchronous texture ownership and shared-context preservation
// without opening a second browser on the software-rendered QA machine.
const loaded = [];
const originalLoader = HDRLoader.prototype.loadAsync;
HDRLoader.prototype.loadAsync = () => new Promise((resolve, reject) => loaded.push({resolve, reject}));
const originalDocument = globalThis.document;
globalThis.document = {createElement: () => ({getContext: () => ({
  createImageData: (w, h) => ({data: new Uint8ClampedArray(w * h * 4)}),
  putImageData() {},
})})};
const targets = [];
const framebuffer = {draw: {name: 'map-draw'}, read: {name: 'map-read'},
  viewport: [3, 4, 800, 600], scissor: [5, 6, 700, 500], scissorTest: true};
const before = {...framebuffer, viewport: [...framebuffer.viewport], scissor: [...framebuffer.scissor]};
const gl = {
  DRAW_FRAMEBUFFER_BINDING: 1, READ_FRAMEBUFFER_BINDING: 2, VIEWPORT: 3,
  SCISSOR_BOX: 4, SCISSOR_TEST: 5, DRAW_FRAMEBUFFER: 6, READ_FRAMEBUFFER: 7,
  getParameter(key) { return ({1:framebuffer.draw, 2:framebuffer.read, 3:framebuffer.viewport, 4:framebuffer.scissor})[key]; },
  isEnabled() { return framebuffer.scissorTest; },
  bindFramebuffer(key, value) { framebuffer[key === 6 ? 'draw' : 'read'] = value; },
  viewport(...value) { framebuffer.viewport = value; },
  scissor(...value) { framebuffer.scissor = value; },
  enable() { framebuffer.scissorTest = true; },
  disable() { framebuffer.scissorTest = false; },
};
let throwOnHDR = false;
class PMREMGenerator {
  fromCubemap() { return this.convert('fallback'); }
  fromEquirectangular() {
    if (throwOnHDR) throw new Error('mock unsupported HDR target');
    return this.convert('photo');
  }
  convert(name) {
    framebuffer.draw = {}; framebuffer.read = {};
    framebuffer.viewport = [0, 0, 256, 256]; framebuffer.scissor = [0, 0, 256, 256];
    framebuffer.scissorTest = false;
    const result = {name, texture: new RealTHREE.Texture(), disposed: 0, dispose() { this.disposed++; }};
    targets.push(result); return result;
  }
  dispose() {}
}
const THREE = {...RealTHREE, PMREMGenerator};
function setup() {
  const renderer = {getContext: () => gl, resetState() {},
    shadowMap: {enabled: false, autoUpdate: true, type: THREE.BasicShadowMap}};
  const scene = new THREE.Scene();
  const material = new THREE.MeshStandardMaterial(); material.name = 'Deep blue glass';
  const originalEnvironment = new THREE.Texture(); material.envMap = originalEnvironment;
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(10, 10, 10), material); scene.add(mesh);
  let ready = 0;
  const lighting = createRealisticLighting({THREE, scene, renderer, reflectionURL: 'mock.hdr', onReflectionReady: () => ready++});
  lighting.configureModel(mesh, {detailed: true}); lighting.update({position: new THREE.Vector3()});
  return {lighting, mesh, material, originalEnvironment, ready: () => ready};
}
function rawTexture() {
  const texture = new THREE.DataTexture(); let disposals = 0;
  texture.addEventListener('dispose', () => disposals++);
  return {texture, disposals: () => disposals};
}
try {
  const first = setup(); const fallback = targets.at(-1);
  assert.equal(first.lighting.stats.reflectionSource, 'procedural-fallback');
  assert.deepEqual(framebuffer, before, 'initial PMREM restores map framebuffer and viewport');
  const raw = rawTexture(); loaded.shift().resolve(raw.texture); await Promise.resolve();
  assert.equal(first.ready(), 1);
  assert.equal(targets.at(-1), fallback, 'download continuation does no GL work');
  first.lighting.update(); const photographic = targets.at(-1);
  assert.equal(first.lighting.stats.reflectionSource, 'photographic');
  assert.equal(first.material.envMap, photographic.texture);
  assert.equal(fallback.disposed, 1); assert.equal(raw.disposals(), 1);
  assert.deepEqual(framebuffer, before, 'HDR PMREM restores map GL state');
  assert.equal(photographic.texture.userData.shared, true);
  first.lighting.dispose(); first.lighting.dispose();
  assert.equal(first.material.envMap, first.originalEnvironment);
  assert.equal(photographic.disposed, 1);

  const late = setup(); late.lighting.dispose();
  const lateRaw = rawTexture(); loaded.shift().resolve(lateRaw.texture); await Promise.resolve();
  assert.equal(lateRaw.disposals(), 1, 'late source is disposed after viewer shutdown');
  assert.equal(late.ready(), 0);

  const failed = setup(); const retained = targets.at(-1);
  const badRaw = rawTexture(); loaded.shift().resolve(badRaw.texture); await Promise.resolve();
  throwOnHDR = true; failed.lighting.update(); throwOnHDR = false;
  assert.equal(failed.material.envMap, retained.texture, 'failed HDR keeps existing fallback');
  assert.equal(retained.disposed, 0); assert.equal(badRaw.disposals(), 1);
  assert.match(failed.lighting.stats.photographicReflectionError, /unsupported/);
  assert.deepEqual(framebuffer, before, 'failed conversion also restores map GL state');
  failed.lighting.dispose();

  const network = setup(); loaded.shift().reject(new Error('offline')); await Promise.resolve(); await Promise.resolve();
  assert.match(network.lighting.stats.photographicReflectionError, /offline/);
  assert.equal(network.lighting.stats.reflectionSource, 'procedural-fallback');
  network.lighting.dispose();
  console.log('Photographic reflection checks passed: deferred GL conversion, exact state restore, fallback retention, late load and disposal.');
} finally {
  HDRLoader.prototype.loadAsync = originalLoader;
  globalThis.document = originalDocument;
}
