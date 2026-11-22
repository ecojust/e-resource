import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {CandidateBridgeWalks,bridgePosition} from '../src/candidate-bridge-walk.js';
import {StreetInteraction} from '../src/street-interaction.js';
const orders=[221,223,230],shared=14679321220;
const inputs=orders.map(n=>JSON.parse(readFileSync(new URL('../evidence/'+n+'-input.json',import.meta.url))));
const rows=inputs.map(f=>f.record);
const street=new StreetInteraction(),walks=new CandidateBridgeWalks(street),counts={};
const runs=[];
for(const variant of ['full','distant']){
 for(let mask=0;mask<8;mask++){
  const selected=rows.filter((_,i)=>mask&(1<<i));
  for(const r of selected)r.activeVariant=variant;
  walks.sync(selected);
  const results=[];
  for(const [i,r]of rows.entries()){
   const fs=inputs[i].frozen.rows.filter(f=>f.id===shared&&f.layer==='transportation');
   if(i>0)assert(fs.length>=2,'joined west/east sidewalk parts');
   const enabled=selected.includes(r);
   for(const s of [-20,0,18])for(const side of [-1,1]){
    const width=(r.bridge_walk.half_road_m+r.bridge_walk.half_deck_m)/2;
    const pos=bridgePosition(r,s,side*width);
    for(const id of r.bridge_walk.transportation_feature_ids){
     const allowed=walks.allowsNativeRoad(id,...pos,6);
     assert.equal(allowed,!enabled,[variant,mask,r.id,s,side,id]);
     results.push([r.id,id,s,side,allowed]);
    }
    const foreign=r.bridge_walk.transportation_feature_ids.includes(shared)?274981172:shared;
    assert(walks.allowsNativeRoad(foreign,...pos,6));
    assert.equal(street.groundAt(...pos)?.ownerId,enabled?r.id:undefined);
   }
   for(const id of r.bridge_walk.transportation_feature_ids){
    assert(walks.allowsNativeRoad(id,...bridgePosition(r,r.bridge_walk.stations_m.at(-1)[0]+8,0),6));
    assert(walks.allowsNativeRoad(id,...bridgePosition(r,0,r.bridge_walk.half_deck_m+20),6));
   }
  }
  runs.push({variant,mask,active:selected.map(x=>x.id),observations:results});
 }
}
walks.sync([]);assert.equal(street.getState().activeOwners,0);
const dir=new URL('../evidence/',import.meta.url);
const checksum=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(new URL('shared-sidewalk-id.json',dir),JSON.stringify({passed:true,shared,verified_walk_module_sha256:checksum(readFileSync(new URL('../src/candidate-bridge-walk.js',import.meta.url))),inputs:inputs.map((x,i)=>({order:orders[i],id:x.record.id,tile:x.frozen.tile_sha256,full:x.record.assets.web.sha256,lod:x.record.assets.lod.sha256})),walks:runs,observations:runs.reduce((n,v)=>n+v.observations.length,0),comment:'All eight loaded/unloaded combinations, full and distant. The local deck only claims samples beside its own span. Each other bridge retains its own frozen transportation feature when that other bridge is inactive.'},null,2)+'\n');
console.log(runs.length,runs.reduce((n,v)=>n+v.observations.length,0));
