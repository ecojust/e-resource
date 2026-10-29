import test from 'node:test';
import assert from 'node:assert/strict';
import {createArchitecturalMaterials} from '../src/architectural-material.js';

function harness() {
  const requests = [];
  const THREE = {TextureLoader: class {
    loadAsync(url) { return new Promise((resolve, reject) => requests.push({url, resolve, reject})); }
  }};
  const makeTexture = () => ({userData: {}, disposed: 0, dispose() { this.disposed++; }});
  return {THREE, requests, makeTexture};
}

test('complete texture set remains usable until explicitly disposed', async () => {
  const h = harness(), ready = createArchitecturalMaterials(h.THREE, {timeoutMs: 1000});
  assert.equal(h.requests.length, 12);
  const textures = h.requests.map(r => { const t = h.makeTexture(); r.resolve(t); return t; });
  const materials = await ready;
  assert.equal(materials.stats.textures, 12);
  assert(textures.every(t => t.disposed === 0));
  materials.dispose(); materials.dispose();
  assert(textures.every(t => t.disposed === 1));
});

test('one permanently pending image times out and late arrival is disposed once', {timeout: 2000}, async () => {
  const h = harness(), ready = createArchitecturalMaterials(h.THREE, {timeoutMs: 25});
  const textures = h.requests.slice(1).map(r => { const t = h.makeTexture(); r.resolve(t); return t; });
  await assert.rejects(ready, /timed out/);
  assert(textures.every(t => t.disposed === 1));
  const late = h.makeTexture(); h.requests[0].resolve(late);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(late.disposed, 1);
  assert(textures.every(t => t.disposed === 1));
});

test('a rejected image cleans the rest of a completed set without applying a partial set', async () => {
  const h = harness(), ready = createArchitecturalMaterials(h.THREE, {timeoutMs: 1000});
  h.requests[0].reject(new Error('image unavailable'));
  const textures = h.requests.slice(1).map(r => { const t = h.makeTexture(); r.resolve(t); return t; });
  await assert.rejects(ready, /image unavailable/);
  assert(textures.every(t => t.disposed === 1));
});
