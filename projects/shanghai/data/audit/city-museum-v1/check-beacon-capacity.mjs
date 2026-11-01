// Run from the repository root; an optional first argument selects projects/shanghai.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const project=resolve(process.argv[2]||'projects/shanghai'),root=resolve(project,'../..');
const baseline='93e3cb2d0ddeba1a7db7d435bf66c2f61492326e',id='yangpu-former-shanghai-city-museum';
const sha=b=>createHash('sha256').update(b).digest('hex');
const oldBytes=execFileSync('git',['show',baseline+':projects/shanghai/src/building-beacons.js'],{cwd:root});
const currentBytes=readFileSync(resolve(project,'src/building-beacons.js'));
const old=await import('data:text/javascript;base64,'+oldBytes.toString('base64'));
const {layoutBeaconLabels,hitTestBeaconLabels}=await import(pathToFileURL(resolve(project,'src/building-beacons.js')));
const original=name=>JSON.parse(execFileSync('git',['show',baseline+':projects/shanghai/'+name],{cwd:root}));
const previous=[...original('data/landmarks.json'),...original('data/candidate-city-integrations.json').models];
const queue=original('data/model-todo/queue.json'),museum=queue.production_queue.find(row=>row.id===id);
assert(museum);assert.equal(previous.length,80);assert.equal(sha(currentBytes),sha(oldBytes),'81 entries should use the existing sprite implementation unchanged');
const next=[...previous,{...museum,lng:121,lat:31,districtId:'310110'}];assert.equal(next.length,81);
const items=rows=>rows.map((r,i)=>({id:r.id,name:r.name,number:i+1,x:160+(i%7),y:240+(i%9),width:176,height:62}));
const viewports=[
 {width:1200,height:900,insets:{left:360,right:88,top:154,bottom:152}},
 {width:390,height:844,insets:{left:12,right:65,top:182,bottom:190}},
 {width:320,height:568,insets:{left:12,right:65,top:182,bottom:228}},
 {width:320,height:548,insets:{left:12,right:65,top:182,bottom:228}},
];
const preserved=viewports.map(viewport=>{
 const before=old.layoutBeaconLabels(items(previous),viewport),after=layoutBeaconLabels(items(previous),viewport);
 assert.deepEqual(after,before,'Previous80 supported layout changed');
 return {viewport,positions_sha256:sha(JSON.stringify(after)),layout_equal:true};
});
const nextChecks=viewports.map(viewport=>{
 const placed=layoutBeaconLabels(items(next),viewport);assert.equal(placed.length,81);assert.equal(placed.filter(r=>r.overlapFallback).length,0);
 const bounds={left:viewport.insets.left,right:viewport.width-viewport.insets.right,top:viewport.insets.top,bottom:viewport.height-viewport.insets.bottom};
 for(let i=0;i<placed.length;i++){
  const a=placed[i];assert(a.labelX-a.width/2>=bounds.left&&a.labelX+a.width/2<=bounds.right);
  assert(a.labelY-a.height/2>=bounds.top&&a.labelY+a.height/2<=bounds.bottom);
  assert.equal(hitTestBeaconLabels(placed,{x:a.labelX,y:a.labelY}),a.id);
  for(let j=0;j<i;j++){const b=placed[j];assert(Math.abs(a.labelX-b.labelX)>=(a.width+b.width)/2||Math.abs(a.labelY-b.labelY)>=(a.height+b.height)/2);}
 }
 return {viewport,positions:placed,independent_hits:81,overlap_fallbacks:0};
});
const worst=nextChecks.at(-1);assert(worst.positions.every(p=>p.width===20&&p.height===18));
const report={schema:'city-museum-beacon-capacity-preflight-v1',passed:true,baseline,
 scope:'Prospective81 entries use the actual queued city-museum identity and frozen80 catalogue. Four pure production layout/hit-test fixtures, conservatively assigning every name the largest badge. These are not browser pixels or real map projection; final DOM/glyph/touch checks remain separate.',
 production_script:{file:'src/building-beacons.js',bytes:currentBytes.length,sha256:sha(currentBytes),identical_to_baseline:true},
 previous80_layouts:preserved,prospective81_layouts:nextChecks,
 worst:{viewport:worst.viewport,safe_rectangle:{left:12,right:255,top:182,bottom:320},sprite_css_px:[20,18],font_css_px:12,capacity:84,remaining_slots:3,independent_hits:81,overlap_fallbacks:0}};
writeFileSync(new URL('beacon-capacity-preflight.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,old80_layouts_preserved:preserved.length,prospective81_layouts:nextChecks.length,capacity:84,remaining_slots:3,production_code_unchanged:true}));
