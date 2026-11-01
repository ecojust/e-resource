import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {layoutBeaconLabels,hitTestBeaconLabels} from '../../../src/building-beacons.js';

const project=new URL('../../../',import.meta.url),root=fileURLToPath(new URL('../../',project)),baseline='96e4dfaff588222475c25a66af1c84a24b45a475';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const oldBytes=execFileSync('git',['show',baseline+':projects/shanghai/src/building-beacons.js'],{cwd:root});
const old=await import('data:text/javascript;base64,'+oldBytes.toString('base64'));
const readOld=name=>JSON.parse(execFileSync('git',['show',baseline+':projects/shanghai/'+name],{cwd:root}));
const previous=[...readOld('data/landmarks.json'),...readOld('data/candidate-city-integrations.json').models];
const queue=readOld('data/model-todo/queue.json'),stadium=queue.production_queue.find(row=>row.id==='yangpu-jiangwan-stadium');
const next=[...previous,{...stadium,lng:121,lat:31,districtId:'310110'}];
assert.equal(previous.length,77);assert.equal(next.length,78);
const items=rows=>rows.map((r,i)=>({id:r.id,name:r.name,number:i+1,x:160+(i%7),y:240+(i%9),width:176,height:62}));
const viewports=[
  {width:1200,height:900,insets:{left:360,right:88,top:154,bottom:152}},
  {width:390,height:844,insets:{left:12,right:65,top:182,bottom:190}},
  {width:320,height:568,insets:{left:12,right:65,top:182,bottom:228}},
  {width:320,height:548,insets:{left:12,right:65,top:182,bottom:228}},
];
const preserved=viewports.map(viewport=>{
  const before=old.layoutBeaconLabels(items(previous),viewport),after=layoutBeaconLabels(items(previous),viewport);
  assert.deepEqual(after,before,'previous77 supported layout must remain unchanged');
  return {viewport,positions_sha256:sha(JSON.stringify(after)),layout_equal:true};
});
const worst=viewports.at(-1),oldNext=old.layoutBeaconLabels(items(next),worst),placed=layoutBeaconLabels(items(next),worst);
assert.equal(oldNext.filter(row=>row.overlapFallback).length,1);
assert.equal(placed.filter(row=>row.overlapFallback).length,0);
for(let i=0;i<placed.length;i++){
  const a=placed[i];assert.equal(a.width,20);assert.equal(a.height,18);
  assert(a.labelX-a.width/2>=12&&a.labelX+a.width/2<=255);
  assert(a.labelY-a.height/2>=182&&a.labelY+a.height/2<=320);
  assert.equal(hitTestBeaconLabels(placed,{x:a.labelX,y:a.labelY}),a.id);
  for(let j=0;j<i;j++){
    const b=placed[j];assert(Math.abs(a.labelX-b.labelX)>=(a.width+b.width)/2||Math.abs(a.labelY-b.labelY)>=(a.height+b.height)/2);
  }
}
const report={baseline,scope:'Prospective78-record layout using the queued stadium identity and existing77 immutable records. Pure production layout/hit checks; actual DOM, SDF pixels and touch navigation remain separate browser QA.',
  production_script:{path:'projects/shanghai/src/building-beacons.js',sha256:sha(readFileSync(root+'/projects/shanghai/src/building-beacons.js'))},
  old_script_sha256:sha(oldBytes),preserved_previous77:preserved,previous_failure:{count:78,overlap_fallbacks:1},
  current:{count:78,viewport:worst,safe_rectangle:{left:12,right:255,top:182,bottom:320},sprite_css_px:[20,18],font_css_px:12,
    capacity:84,remaining_slots:6,independent_hit_count:78,overlap_fallbacks:0,positions:placed},passed:true};
writeFileSync(new URL('beacon-capacity-preflight.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,preserved_previous77_layouts:preserved.length,prospective_count:78,previous_fallbacks:1,current_fallbacks:0,capacity:84,remaining_slots:6}));
