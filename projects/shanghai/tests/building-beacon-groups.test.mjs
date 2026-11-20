import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {layoutBeaconLabels,hitTestBeaconLabels} from '../src/building-beacons.js';

const read=name=>JSON.parse(readFileSync(new URL('../data/'+name,import.meta.url),'utf8'));
const catalog=[...read('landmarks.json'),...read('candidate-city-integrations.json').models];
const room={width:320,height:568,insets:{left:12,right:65,top:182,bottom:248}};
const rad=Math.PI/180,merc=lat=>Math.asinh(Math.tan(lat*rad)),world=512*2**8;
function point(row,index){
  return {id:row.id,number:index+1,width:140,height:34,
    x:160+(row.lng-121.45)*world/360,y:284-(merc(row.lat)-merc(31.2))*world/(2*Math.PI)};
}
function checkLayout(items,expectGroups){
  const layout=layoutBeaconLabels(items,room);
  assert.equal(Boolean(layout[0].memberIds),expectGroups);
  const ids=layout.flatMap(slot=>slot.memberIds??[slot.id]);
  assert.deepEqual(ids.sort(),items.map(i=>i.id).sort());
  for(const slot of layout){
    assert(!slot.overlapFallback);
    if(expectGroups){assert(slot.width>=44&&slot.height>=44);assert(slot.memberIds.includes(slot.representative));}
    for(const dx of [-.49,0,.49])for(const dy of [-.49,0,.49])
      assert.equal(hitTestBeaconLabels(layout,{x:slot.labelX+dx*slot.width,y:slot.labelY+dy*slot.height}),slot.id);
  }
}
for(const count of [125,126,132,138,1058])test('citywide selection reaches '+count+' sites above a long phone card',()=>{
  // Start with the actual registered coordinates. Future sites use distinct
  // fixture IDs at the same anchors so identical projections cannot hide them.
  const rows=Array.from({length:count},(_,i)=>{
    const sample=catalog[i%catalog.length];return point(i<catalog.length?sample:{...sample,id:'fixture-'+(i+1)},i);
  });
  checkLayout(rows,count>125);
});
test('full names for a single visible four-digit site use the ordinary sign',()=>{
  const row={...point(catalog[0],1057),x:160,y:250};
  const [slot]=layoutBeaconLabels([row],room);
  assert.equal(slot.id,row.id);
  assert.equal(slot.compact,false);
});
