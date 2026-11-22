const assert = require('node:assert/strict');

function sorted(ids) {
  return [...ids].sort((a, b) => a - b);
}

function sourceGroups(review, contract, spec) {
  const all = (contract.owners || [contract.owner]).map(owner => owner.feature_local_id);
  const primary = review.near_tiles.find(tile => tile.feature_local_ids.includes(contract.owner.feature_local_id));
  assert.ok(primary, 'Primary owner has no streamed group');
  const supplied = spec.groups || [{
    id: primary.id, addedOwners: spec.addedOwners || all,
    existingOwners: spec.existingGroupOwners || [],
    addedTriangles: spec.addedTriangles ?? spec.groupTriangles,
    groupTriangles: spec.groupTriangles
  }];
  assert.equal(new Set(supplied.map(row => row.id)).size, supplied.length, 'Duplicate source group');
  const groups = supplied.map(row => {
    const tile = review.near_tiles.find(tile => tile.id === row.id);
    assert.ok(tile, 'Missing source group '+row.id);
    assert.ok(row.addedOwners.length && row.addedOwners.every(id => tile.feature_local_ids.includes(id)), 'Owner missing in '+row.id);
    if (spec.groups) {
      assert.ok(Number.isInteger(row.addedTriangles) && row.addedTriangles > 0, 'Invalid increase in '+row.id);
      assert.ok(Number.isInteger(row.groupTriangles) && row.groupTriangles >= row.addedTriangles, 'Invalid total in '+row.id);
    }
    return {...row, tile, existingOwners:row.existingOwners || []};
  });
  assert.deepEqual(sorted(groups.flatMap(g => g.addedOwners)), sorted(all), 'Coverage must include each contract owner once');
  if (spec.groups) assert.equal(groups.reduce((sum,g) => sum + g.addedTriangles,0), spec.addedTriangles, 'Group deltas differ from catalog increase');
  return groups;
}

function assertGroupDraws(groups, draws, control) {
  for (const group of groups) {
    const draw = draws.find(value => value && (value.id === group.id || value.id.endsWith('/'+group.id)));
    assert.ok(draw, 'Group was not drawn '+group.id);
    assert.deepEqual(draw.feature_local_ids, group.tile.feature_local_ids, group.id);
    const owners = control ? group.existingOwners : [...group.existingOwners, ...group.addedOwners];
    assert.deepEqual(sorted(draw.clip_feature_local_ids), sorted(owners), group.id);
    assert.equal(draw.triangles, group.groupTriangles - (control ? group.addedTriangles : 0), group.id);
  }
}
module.exports = {sourceGroups, assertGroupDraws};
