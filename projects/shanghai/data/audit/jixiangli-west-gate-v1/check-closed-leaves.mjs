// Replay ordinary walking and sprinting into the photographed closed gate with the actual controller.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const audit = path.dirname(fileURLToPath(import.meta.url));
const project = path.resolve(process.argv[2]);
const file = path.resolve(process.argv[3] || path.join(audit, 'final-placement-contract.json'));
const contract = JSON.parse(fs.readFileSync(file));
const source = path.join(project, 'src/walk-controller.js');
const {WalkController, offsetPosition} = await import(pathToFileURL(source));
const {candidateGeometryContains} = await import(pathToFileURL(path.join(project, 'src/candidate-city-integrations.js')));
const angle = contract.heading * Math.PI / 180;
const origin = {lng: contract.lng, lat: contract.lat};
const forward = (x,y) => offsetPosition(origin, x * Math.cos(angle) + y * Math.sin(angle), -x * Math.sin(angle) + y * Math.cos(angle));
const scale = 6371008.8 * Math.PI / 180;
function local(p) {
  const east = (p.lng - origin.lng) * Math.cos(origin.lat * Math.PI / 180) * scale;
  const north = (p.lat - origin.lat) * scale;
  return [east * Math.cos(angle) - north * Math.sin(angle), east * Math.sin(angle) + north * Math.cos(angle)];
}
globalThis.window = new EventTarget();
globalThis.document = new EventTarget();
const scene = {setPlayer() {}, collisionAt(lng,lat) {
  return candidateGeometryContains(contract.collision_geometry, [lng,lat]) ? 'building' : null;
}};
const runs = [];
for (const fps of [20,25,30,45,60]) {
  for (const sprint of [false,true]) {
    for (const x of [-1.1,0,1.1]) {
      for (const phase of [0,.06,.13,.21,.32]) {
        const controller = new WalkController(scene, {requestAnimationFrame: () => 0, cancelAnimationFrame: () => {}});
        controller.enabled = true;
        controller.bearing = contract.heading;
        controller.position = forward(x, -1.8-phase);
        controller.keys.add('KeyW');
        if (sprint) controller.keys.add('ShiftLeft');
        let largest = -Infinity;
        for (let frame = 0; frame < fps * 1.2; frame++) {
          controller._move(1/fps, frame*1000/fps);
          largest = Math.max(largest, local(controller.position)[1]);
        }
        runs.push({fps, sprint, x, phase, maximumInwardM: largest, passed: largest < .61});
        controller.destroy();
      }
    }
  }
}
const failed = runs.filter(r => !r.passed);
const hash = p => createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const output = {id:contract.id, passed:failed.length===0, tests:runs.length, crossingCount:failed.length,
  contractSHA256:hash(file), walkControllerSHA256:hash(source), checkerSHA256:hash(fileURLToPath(import.meta.url)), runs};
fs.writeFileSync(process.argv[4] || path.join(audit, 'closed-leaves-walk.json'), JSON.stringify(output, null, 2)+'\n');
console.log(runs.length, failed.length);
assert.equal(failed.length,0);
