import assert from 'node:assert/strict';
import fs from 'node:fs';
import {applyStreetWidths, legacyWidthAtZoom, pixelsPerMetre} from '../src/road-width.js';

const style = JSON.parse(fs.readFileSync(new URL('../data/map-style.json', import.meta.url)));
let changedLayers = 0;
let maximumOverviewDifference = 0;
for (const layer of style.layers) {
  const originalLayer = structuredClone(layer);
  if (!applyStreetWidths(layer)) {
    assert.deepEqual(layer, originalLayer, `Unrelated layer changed: ${layer.id}`);
    continue;
  }
  changedLayers++;
  const expression = layer.paint['line-width'];
  const cutoff = expression.findIndex((value, index) => index >= 3 && index % 2 === 1 && value === 16);
  const overviewExpression = expression.slice(0, cutoff + 2);
  for (let zoom = 0; zoom <= 16; zoom += .125) {
    const difference = Math.abs(legacyWidthAtZoom(originalLayer.paint['line-width'], zoom)
      - legacyWidthAtZoom(overviewExpression, zoom));
    maximumOverviewDifference = Math.max(maximumOverviewDifference, difference);
    assert.ok(difference < 1e-10, `${layer.id} changed at overview zoom ${zoom}`);
  }
}
assert.equal(changedLayers, 46);
// Shanghai's Mercator metre scale, including fractional walking-camera zoom.
assert.ok(Math.abs(pixelsPerMetre(17) - 1.95774) < .00001);
assert.ok(Math.abs(pixelsPerMetre(22.5) * 6 - 531.5833) < .001);
assert.equal(pixelsPerMetre(22.5) / pixelsPerMetre(21.5), 2);
console.log('PASS', {changedLayers, maximumOverviewDifference});
