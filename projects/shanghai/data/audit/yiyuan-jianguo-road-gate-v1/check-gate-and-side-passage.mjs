// Replay ordinary walking and sprinting into the closed main gate and the open adjacent pedestrian arch with the actual controller.
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
// The two central sashes are closed. The adjacent pedestrian arch is open.
const mainDoorTests = [-1.1, 0, 1.1].map(x => ({x, inward:true, passage:false}));
const routes = [...mainDoorTests, {x:-2.76,inward:true,passage:true}, {x:-2.76,inward:false,passage:true}];
const runs = [];
for (const fps of [20,25,30,45,60]) {
  for (const sprint of [false,true]) {
    for (const route of routes) {
      for (const phase of [0,.06,.13,.21,.32]) {
        const controller = new WalkController(scene, {requestAnimationFrame: () => 0, cancelAnimationFrame: () => {}});
        controller.enabled = true;
        controller.bearing = contract.heading + (route.inward ? 0 : 180);
        controller.position = forward(route.x, route.inward ? -1.8-phase : 2.3+phase);
        controller.keys.add('KeyW');
        if (sprint) controller.keys.add('ShiftLeft');
        const crossings = [];
        let prior = local(controller.position);
        for (let frame=0; frame<fps*1.2; frame++) {
          controller._move(1/fps, frame*1000/fps);
          const point = local(controller.position);
          // Intersect each actual step with the leaf plane in either direction.
          if ((prior[1]<.25) !== (point[1]<.25)) {
            const fraction=(.25-prior[1])/(point[1]-prior[1]);
            crossings.push(prior[0]+fraction*(point[0]-prior[0]));
          }
          prior=point;
        }
        const insidePassage=x=>x> -3.25 && x< -2.27;
        const completedPassage=crossings.length===1 && (route.inward ? prior[1]>.64 : prior[1]<-.12);
        const passed = crossings.every(insidePassage) && (!route.passage || completedPassage);
        runs.push({fps,sprint,...route,phase,crossings,finalLocal:prior,passed});
        controller.destroy();
      }
    }
  }
}
const failed=runs.filter(row=>!row.passed);
const hash = p => createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const output = {id:contract.id, passed:failed.length===0, tests:runs.length, blockedOpeningCrossings:runs.flatMap(r=>r.crossings).filter(x=>x>=-1.65 && x<=1.65).length,
  requestedPedestrianRoutes:runs.filter(r=>r.passage).length, approvedSidePassageDiversions:runs.filter(r=>!r.passage && r.crossings.length).length,
  contractSHA256:hash(file), walkControllerSHA256:hash(source), checkerSHA256:hash(fileURLToPath(import.meta.url)), runs};
fs.writeFileSync(process.argv[4] || path.join(audit, 'closed-leaves-walk.json'), JSON.stringify(output, null, 2)+'\n');
console.log(runs.length, failed.length);
assert.equal(failed.length,0);
