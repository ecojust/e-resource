/** Check walking permission for every curated location against the prior site's movement logic. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [baseProject, revisedProject, destination] = process.argv.slice(2);
if (!destination) throw Error('Usage: node check-walking-entry.mjs BASE_PROJECT REVISED_PROJECT report.json');
async function loadUI(file) {
  const dependency = pathToFileURL(path.resolve(baseProject, 'src/historical-view.js')).href;
  const source = fs.readFileSync(file, 'utf8').replace(/(['"])\.\/historical-view\.js[^'"]*\1/, JSON.stringify(dependency));
  return import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
}
const old = await loadUI(path.join(baseProject,'src/precise-registration-ui.js'));
const fresh = await loadUI(path.join(revisedProject,'src/precise-registration-ui.js'));
const nav = JSON.parse(fs.readFileSync(path.join(revisedProject, 'data/landmarks.json')));
const original=nav.filter(row => row.id!=='xuhui-xiangyang-313-restored-courtyard-fronts');
const target=nav.filter(row => !original.includes(row));
assert.equal(original.length,40); assert.equal(target.length,1);
const poses = original.map(row => {
  const before=old.walkingPose(row), after=fresh.walkingPose(row);
  assert.ok(before); assert.deepEqual(after,before);
  return {id:row.id,position:after};
});
const current=target[0];
assert.equal(fresh.walkingPose(current),null);
const invalid=[
  {...current,navigation:{listed:true}},
  {...current,walkStart:[121,31]},
  {...current,navigation:{...current.navigation,walkStart:[121,31]}},
  {...current,navigation:{...current.navigation,bearing:42}}
];
for(const row of invalid)assert.throws(()=>fresh.walkingPose(row),/walking pose/);
assert.equal(fresh.walkingPose({kind:'building',id:'unlisted',navigation:{listed:false}}),null);
fs.writeFileSync(destination,JSON.stringify({original_walk_starts:poses,overview_only:current.id,invalid_rows_rejected:invalid.length},null,2)+'\n');
