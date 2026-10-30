/* Pure collision and configurable outdoor-bound regression checks. MIT. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  // This repository serves browser modules without a package.json module type.
  const source = fs.readFileSync(path.resolve(__dirname, '../../../src/candidate-walk-motion.js'), 'utf8');
  const {BODY_RADIUS, WALK_LIMIT, blockedAt, moveOutside, cameraFraction, validateWalkLimits} =
    await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
  const checks = [];
  const check = (name, run) => { run(); checks.push(name); };
  const close = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} != ${expected}`);
  const box = {minX: -2, maxX: 2, minZ: -2, maxZ: 2};

  check('existing defaults remain 46m with a 0.35m body', () => {
    assert.equal(WALK_LIMIT, 46);
    assert.equal(BODY_RADIUS, .35);
    assert.deepEqual(validateWalkLimits(), {modelExtentLimit: 35, walkLimit: 46});
  });
  check('the previous 40m extent override remains accepted', () => {
    assert.deepEqual(validateWalkLimits({modelExtentLimit: 40}), {modelExtentLimit: 40, walkLimit: 46});
  });
  check('Race Club can opt into a 60m model extent and 80m walk boundary', () => {
    assert.deepEqual(validateWalkLimits({modelExtentLimit: 60, walkLimit: 80}), {modelExtentLimit: 60, walkLimit: 80});
  });
  check('bounded finite configuration and start clearance are enforced', () => {
    for (const walkLimit of [0, 121, NaN, Infinity, -Infinity, '80', null]) {
      assert.throws(() => validateWalkLimits({walkLimit}), `walkLimit ${walkLimit} must fail`);
    }
    for (const modelExtentLimit of [0, 81, NaN, Infinity, -Infinity, '60', null]) {
      assert.throws(() => validateWalkLimits({modelExtentLimit}), `modelExtentLimit ${modelExtentLimit} must fail`);
    }
    assert.throws(() => validateWalkLimits({modelExtentLimit: 46, walkLimit: 46}));
    assert.throws(() => validateWalkLimits({modelExtentLimit: 60, walkLimit: 60.5}));
    assert.deepEqual(validateWalkLimits({modelExtentLimit: 45, walkLimit: 46}), {modelExtentLimit: 45, walkLimit: 46});
    assert.deepEqual(validateWalkLimits({modelExtentLimit: 80, walkLimit: 120}), {modelExtentLimit: 80, walkLimit: 120});
  });
  check('default outer boundary remains closed beyond each axis', () => {
    for (const sign of [-1, 1]) {
      assert.equal(blockedAt(sign * 46, 10, box), false);
      assert.equal(blockedAt(sign * 46.01, 10, box), true);
      assert.equal(blockedAt(10, sign * 46, box), false);
      assert.equal(blockedAt(10, sign * 46.01, box), true);
    }
  });
  check('custom boundary opens the route past 46m but closes past 80m', () => {
    for (const sign of [-1, 1]) {
      assert.equal(blockedAt(sign * 60, 10, box), true);
      assert.equal(blockedAt(sign * 60, 10, box, BODY_RADIUS, 80), false);
      assert.equal(blockedAt(sign * 80, 10, box, BODY_RADIUS, 80), false);
      assert.equal(blockedAt(sign * 80.01, 10, box, BODY_RADIUS, 80), true);
      assert.equal(blockedAt(10, sign * 80.01, box, BODY_RADIUS, 80), true);
    }
  });
  check('body clearance and the existing fourth radius argument are preserved', () => {
    assert.equal(blockedAt(0, 0, box), true);
    assert.equal(blockedAt(2.3, 0, box), true);
    assert.equal(blockedAt(2.4, 0, box), false);
    assert.equal(blockedAt(2.4, 0, box, .5), true);
    assert.equal(blockedAt(2.4, 0, box, .5, 80), true);
  });
  check('zero motion does not move a visitor', () => {
    assert.deepEqual(moveOutside({x: 5, z: 5}, 0, 0, box), {x: 5, z: 5});
  });
  check('unobstructed displacement is preserved', () => {
    const next = moveOutside({x: 5, z: 5}, 3, 4, box);
    close(next.x, 8); close(next.z, 9);
  });
  check('default movement cannot cross the old outer boundary', () => {
    for (const sign of [-1, 1]) {
      const next = moveOutside({x: sign * 45.95, z: 10}, sign, 0, box);
      assert.ok(Math.abs(next.x) <= 46);
      assert.ok(Math.abs(next.x) >= 45.95);
    }
  });
  check('configured movement passes the old outer boundary on both axes', () => {
    for (const sign of [-1, 1]) {
      const nextX = moveOutside({x: sign * 45.9, z: 10}, sign, 0, box, 80);
      const nextZ = moveOutside({x: 10, z: sign * 45.9}, 0, sign, box, 80);
      close(nextX.x, sign * 46.9); close(nextZ.z, sign * 46.9);
    }
  });
  check('configured movement cannot cross the new outer boundary', () => {
    for (const sign of [-1, 1]) {
      const nextX = moveOutside({x: sign * 79.95, z: 10}, sign, 0, box, 80);
      const nextZ = moveOutside({x: 10, z: sign * 79.95}, 0, sign, box, 80);
      assert.ok(Math.abs(nextX.x) <= 80);
      assert.ok(Math.abs(nextZ.z) <= 80);
    }
  });
  check('a long step cannot tunnel through the facade', () => {
    const next = moveOutside({x: -8, z: 0}, 16, 0, box, 80);
    assert.ok(next.x > -8 && next.x <= box.minX - BODY_RADIUS);
    assert.equal(blockedAt(next.x, next.z, box, BODY_RADIUS, 80), false);
  });
  check('substeps also prevent tunneling through a thin wall', () => {
    const wall = {minX: -.02, maxX: .02, minZ: -1, maxZ: 1};
    const next = moveOutside({x: -2, z: 0}, 4, 0, wall, 80);
    assert.ok(next.x > -2 && next.x <= wall.minX - BODY_RADIUS);
  });
  check('oblique movement slides along the facade without entering it', () => {
    const next = moveOutside({x: 0, z: 2.5}, 4, -1, box, 80);
    close(next.x, 4);
    assert.ok(next.z < 2.5);
    assert.equal(blockedAt(next.x, next.z, box, BODY_RADIUS, 80), false);
  });
  check('large Race Club bounds remain closed inside the extended domain', () => {
    const raceBox = {minX: -53, maxX: 53, minZ: -12, maxZ: 12};
    assert.equal(blockedAt(54, 0, raceBox, BODY_RADIUS, 80), false);
    const next = moveOutside({x: 54, z: 0}, -5, 0, raceBox, 80);
    assert.ok(next.x >= raceBox.maxX + BODY_RADIUS);
    assert.ok(next.x < 54);
    assert.equal(blockedAt(next.x, next.z, raceBox, BODY_RADIUS, 80), false);
  });
  check('camera clipping fractions remain unchanged', () => {
    assert.equal(cameraFraction({x: -5, z: 3}, {x: 5, z: 3}, box), 1);
    assert.equal(cameraFraction({x: 0, z: 3}, {x: 0, z: 4}, box), 1);
    close(cameraFraction({x: -5, z: 0}, {x: 5, z: 0}, box), .265);
    close(cameraFraction({x: 0, z: 5}, {x: 0, z: -5}, box), .265);
    assert.equal(cameraFraction({x: 0, z: 0}, {x: 5, z: 0}, box), 0);
  });
  console.log(JSON.stringify({passed: checks.length, checks}, null, 2));
})().catch(error => { console.error(error); process.exit(1); });
