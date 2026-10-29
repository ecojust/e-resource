import test from 'node:test';
import assert from 'node:assert/strict';
import {blockedAt, moveOutside, cameraFraction, WALK_LIMIT} from '../src/candidate-walk-motion.js';
const box = {minX: -5, maxX: 5, minZ: -1, maxZ: 1};

test('large movement cannot tunnel through a narrow facade or leave the stage', () => {
  const result = moveOutside({x: 0, z: 5}, 0, -30, box);
  assert.ok(result.z >= 1.35 && result.z < 1.48);
  assert.equal(blockedAt(result.x, result.z, box), false);
  assert.ok(moveOutside({x: 20, z: 20}, 100, 0, box).x <= WALK_LIMIT);
});
test('diagonal movement slides along a closed model and can walk around it', () => {
  let result = moveOutside({x: 0, z: 1.4}, 8, -4, box);
  assert.ok(result.x > 7.9);
  assert.equal(blockedAt(result.x, result.z, box), false);
  result = moveOutside(result, 0, -10, box);
  assert.ok(result.z < -5);
});
test('camera boom is shortened before entering a model, including grazing paths', () => {
  const fraction = cameraFraction({x: 0, z: 2}, {x: 0, z: -2}, box);
  assert.ok(fraction > 0 && fraction < .22);
  assert.equal(cameraFraction({x: 8, z: 2}, {x: 8, z: -2}, box), 1);
  assert.equal(cameraFraction({x: 0, z: 2}, {x: 0, z: 6}, box), 1);
  assert.ok(cameraFraction({x: 5.1, z: 2}, {x: 5.1, z: -2}, box) < 1);
});
