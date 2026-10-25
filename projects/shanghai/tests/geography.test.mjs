import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {districtAt} from '../src/geography.js';
const read = path => JSON.parse(readFileSync(new URL(path,import.meta.url),'utf8'));
const boundaries = read('../data/districts-display.geojson');
const checks = read('../data/audit/checkpoints.geojson');
for(const feature of checks.features) {
  const result=districtAt(boundaries,...feature.geometry.coordinates);
  assert.equal(String(result?.id),feature.properties.district_id,feature.properties.name);
}
assert.equal(districtAt(boundaries,116.4,39.9),null,'outside Shanghai');
assert.equal(districtAt(boundaries,NaN,31.2),null,'invalid coordinate');
const withHole={features:[{properties:{id:'courtyard'},geometry:{type:'Polygon',coordinates:[[[0,0],[10,0],[10,10],[0,10],[0,0]],[[3,3],[7,3],[7,7],[3,7],[3,3]]]}}]};
assert.equal(districtAt(withHole,2,2)?.id,'courtyard');
assert.equal(districtAt(withHole,5,5),null,'polygon hole excluded');
console.log(`PASS ${checks.features.length} published checkpoints, outside bounds, and holes`);
