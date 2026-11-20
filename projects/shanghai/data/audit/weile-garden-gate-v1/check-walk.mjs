// Walk through the modeled portal and towards the solid gate piers with the production controls.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const local=path.dirname(fileURLToPath(import.meta.url));
const site=path.resolve(process.argv[2]||path.join(local,'../../..'));
const contractPath=process.argv[3]||path.join(local,'final-placement-contract.json');
const contract=JSON.parse(fs.readFileSync(contractPath));
const hash=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const load=f=>import(pathToFileURL(path.join(site,f)));
const {WalkController,offsetPosition}=await load('src/walk-controller.js');
const {candidateGeometryContains}=await load('src/candidate-city-integrations.js');
const h=contract.heading*Math.PI/180, earth=6371008.8*Math.PI/180, origin={lng:contract.lng,lat:contract.lat};
function fromLocal(x,y){
  return offsetPosition(origin,x*Math.cos(h)+y*Math.sin(h),-x*Math.sin(h)+y*Math.cos(h));
}
function toLocal(p){
  const e=(p.lng-origin.lng)*Math.cos(origin.lat*Math.PI/180)*earth;
  const n=(p.lat-origin.lat)*earth;
  return [e*Math.cos(h)-n*Math.sin(h),e*Math.sin(h)+n*Math.cos(h)];
}
globalThis.window=new EventTarget();
globalThis.document=new EventTarget();
const scene={setPlayer(){},collisionAt(lng,lat){
  return candidateGeometryContains(contract.collision_geometry,[lng,lat])?'building':null;
}};
const runs=[];
for(const fps of [20,25,30,45,60]){
  for(const sprint of [false,true]){
    for(const [x,pass] of [[-4.55,false],[-2.80,false],[-1.35,true],[0,true],[1.35,true],[2.80,false],[6.30,false]]){
      for(const inward of [false,true]){
       for(const phase of [0,.06,.13,.21,.32]){
        const walker=new WalkController(scene,{requestAnimationFrame:()=>0,cancelAnimationFrame:()=>{}});
        walker.enabled=true;
        walker.bearing=contract.heading+(inward?0:180);
        walker.position=fromLocal(x,inward?-1.80-phase:2.30+phase);
        walker.keys.add('KeyW');
        if(sprint)walker.keys.add('ShiftLeft');
        const crossings=[];
        let prev=toLocal(walker.position);
        for(let i=0;i<fps*1.35;i++){
          walker._move(1/fps,i*1000/fps);
          const p=toLocal(walker.position);
          if((p[1]>.20)!==(prev[1]>.20)){
            const t=(.20-prev[1])/(p[1]-prev[1]);
            crossings.push(prev[0]+t*(p[0]-prev[0]));
          }
          prev=p;
        }
        assert.ok(crossings.every(x=>Math.abs(x)<2.08));
        if(pass)assert.equal(crossings.length,1);
        if(Math.abs(x)>3.5)assert.equal(crossings.length,0);
        assert.ok(crossings.length<=1);
        walker.destroy();
        runs.push({x,fps,sprint,inward,phase,started_in_lane:pass,crossings,final_local:prev});
       }
      }
    }
  }
}
const report={id:contract.id,passed:true,tests:runs.length,pier_routes_sliding_into_open_lane:runs.filter(r=>!r.started_in_lane&&r.crossings.length).length,runs,contract_sha256:hash(contractPath),checker_sha256:hash(fileURLToPath(import.meta.url)),
  walk_controller_sha256:hash(path.join(site,'src/walk-controller.js'))};
fs.writeFileSync(process.argv[4]||path.join(local,'gate-walk.json'),JSON.stringify(report,null,2)+'\n');
console.log(runs.length,'walk and sprint controls passed');
