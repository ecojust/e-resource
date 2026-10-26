import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const style = JSON.parse(fs.readFileSync(new URL('../data/map-style.json', import.meta.url), 'utf8'));
const bundle = fs.readFileSync(new URL('../vendor/maplibre-gl.js', import.meta.url), 'utf8');
// Exercise the actual shipped compiler without exposing it in the browser bundle.
const entry = 'function si(t,e,n){';
assert.equal(bundle.split(entry).length, 2, 'Vendored compiler entry changed; review this test adapter');
let warnings = [];
const context = {
  module: {exports: {}}, exports: {},
  console: {...console, warn: message => warnings.push(message)},
  TextDecoder, TextEncoder, URL, Blob, performance, setTimeout, clearTimeout, AbortController,
};
vm.runInNewContext(bundle.replace(entry, 'globalThis.__compileStyle=si;' + entry), context);
function compile(expression) {
  const result = context.__compileStyle(expression, {type: 'boolean', default: false});
  assert.equal(result.result, 'success');
  return result.value;
}
function feature(refLength, network = 'cn-national', type = 2) {
  return {id: 1, type, properties: {
    network, ...(refLength === undefined ? {} : {ref_length: refLength}),
  }};
}

for (const [id, accepted, rejected] of [
  ['highway-shield-non-us', 'cn-national', 'us-highway'],
  ['highway-shield-us-interstate', 'us-interstate', 'us-state'],
  ['road_shield_us', 'us-state', 'us-interstate'],
]) {
  test(`${id}: missing/non-number lengths are excluded without worker warnings`, () => {
    const compiled = compile(style.layers.find(layer => layer.id === id).filter);
    warnings = [];
    for (const length of [undefined, null, '3', false, [], {}]) {
      const f = feature(length, accepted);
      assert.equal(compiled.evaluateWithoutErrorHandling({zoom: 18}, f), false);
      assert.equal(compiled.evaluate({zoom: 18}, f), false);
    }
    assert.deepEqual(warnings, []);
  });

  test(`${id}: valid numeric lengths, network and geometry rules remain effective`, () => {
    const compiled = compile(style.layers.find(layer => layer.id === id).filter);
    warnings = [];
    for (const length of [0, 1, 6]) {
      assert.equal(compiled.evaluateWithoutErrorHandling({zoom: 18}, feature(length, accepted)), true);
    }
    assert.equal(compiled.evaluateWithoutErrorHandling({zoom: 18}, feature(7, accepted)), false);
    assert.equal(compiled.evaluateWithoutErrorHandling({zoom: 18}, feature(3, rejected)), false);
    assert.equal(compiled.evaluateWithoutErrorHandling({zoom: 18}, feature(3, accepted, 1)), false);
    assert.equal(compiled.evaluateWithoutErrorHandling({zoom: 18}, feature(3, accepted, 3)), false);
    assert.deepEqual(warnings, []);
  });
}

test('negative control: an unguarded numeric comparison reproduces the old warning', () => {
  const original = compile(['<=', ['get', 'ref_length'], 6]);
  warnings = [];
  assert.throws(() => original.evaluateWithoutErrorHandling({zoom: 18}, feature(undefined)), /number.*null/);
  assert.equal(original.evaluate({zoom: 18}, feature(undefined)), false);
  assert.equal(warnings.length, 1);
  assert.match(warnings[0], /number.*null/);
});
