import assert from 'node:assert/strict';
import test from 'node:test';
import {bridgeInteraction, bridgePosition, CandidateBridgeWalks, validBridgeWalk} from '../src/candidate-bridge-walk.js';
import {DEFAULT_GROUND_HEIGHT, StreetInteraction} from '../src/street-interaction.js';
import {CandidateCityState} from '../src/candidate-city-integrations.js';
import {markVerifiedOrdinaryAsset} from '../src/ordinary-asset-verification.js';

function fixture() {
  const row={id:'test-bridge',lng:121.48,lat:31.24,scale:1,heading:15,altitude:0,city_integration:true,
    collision_geometry:null,assets:{web:{sha256:'1'.repeat(64),file:'assets/full.glb',bytes:123},
    lod:{sha256:'2'.repeat(64),file:'assets/lod.glb',bytes:64}},bridge_walk:{version:1,longitudinal_axis:'x',
    shear:-.26,half_deck_m:9.1,half_road_m:6.4,sidewalk_rise_m:.145,stations_m:[[-30,.075],[0,.75],[30,.075]],
    rails:[-8.9,8.9].map(offset_m=>({offset_m,radius_m:.2,base_above_road_m:0,top_above_road_m:1.1})),
    transportation_feature_ids:[123,456],posts:[{station_m:0,offset_m:8.5,half_length_m:1,half_width_m:.5,top_above_road_m:3}]}};
  const scene={visible:true},street=new StreetInteraction(),bridge=new CandidateBridgeWalks(street);
  const records=new Map([[row.id,row]]),state=new CandidateCityState({getRecords:()=>records,getScene:()=>scene,onChange:s=>bridge.sync(s.active)});
  const activate=(variant,valid=true)=>{
    row.object={visible:true,parent:scene};row.status='loaded';row.activeVariant=variant==='web'?'full':'distant';
    if(valid)markVerifiedOrdinaryAsset(row.object,{modelId:row.id,variant,asset:row.assets[variant]});
    state.sync();
  };
  const at=(s,v)=>{const [lng,lat]=bridgePosition(row,s,v);return {lng,lat};};
  const ground=(s,v)=>{const p=at(s,v);return street.groundAt(p.lng,p.lat);};
  return {row,scene,street,bridge,state,activate,at,ground};
}

test('sloped deck follows the model-local frame and the two existing banks',()=>{
  const {row,street,activate,at,ground}=fixture();activate('web');
  for(const s of [-30,-15,0,15,30])for(const v of [-7.5,0,7.5]){
    const expected=.75-.675*Math.abs(s/30)+(v ? .145 : 0);
    assert.ok(Math.abs(ground(s,v).height-expected)<1e-7);
  }
  for(const s of [-31,31])assert.equal(ground(s,7.5),null);
  const p=at(-30.2,7.5),q=at(-29.8,7.5);
  assert.equal(street.sweep(p,q,{groundHeight:DEFAULT_GROUND_HEIGHT}),null);
  assert.equal(street.sweep(at(17,7.5),at(17,9))?.type,'street-obstacle');
  assert.equal(street.sweep(at(0,8.1),at(0,8.1))?.id,'post-0');
  assert.equal(street.cameraCollision({...at(17,7.5),alt:.9},{...at(17,9),alt:.9})?.type,'street-obstacle');
  assert.equal(street.cameraCollision({...at(17,7.5),alt:9},{...at(17,9),alt:9}),null);
  const g=bridgeInteraction(row);g.features[0].geometry.coordinates[0][3][2]+=1;
  assert.equal(street.setOwner(row.id,g,{modelSha256:row.assets.web.sha256}),false);
});

test('only verified, visible full and distant models enable the deck and retarget their own frozen transport IDs',()=>{
  const {row,street,bridge,state,activate,at,ground}=fixture();
  const permitted=(id,s,v)=>{const p=at(s,v);return bridge.allowsNativeRoad(id,p.lng,p.lat);};
  activate('web',false);assert.equal(ground(4,7.5),null);assert.equal(permitted(123,0,14),true);
  for(const variant of ['web','lod','web']){
    activate(variant);assert.equal(ground(5,7.5).ownerId,row.id);assert.equal(street.getState().activeOwners,1);
    assert.equal(permitted(123,0,14),false);assert.equal(permitted(456,0,14),false);
    assert.equal(permitted(789,0,14),true);assert.equal(permitted(123,34,14),true);assert.equal(permitted(123,0,150),true);
    const water=at(0,14),deck=at(0,7.5);assert.equal(bridge.coversWater(water.lng,water.lat),false);assert.equal(bridge.coversWater(deck.lng,deck.lat),true);
  }
  row.object.visible=false;state.sync();assert.equal(ground(0,7.5),null);assert.equal(permitted(123,0,14),true);
  activate('lod');row.object.parent=null;state.sync();assert.equal(street.getState().activeOwners,0);
  activate('web');row.catalogDisposed=true;state.sync();assert.equal(street.getState().owners,0);
});

test('rejects collapsed stations, unbound road IDs, conflicting source cuts and missing guardrails',()=>{
  for(const transform of [r=>r.bridge_walk.stations_m.reverse(),r=>r.bridge_walk.stations_m[1][1]=Infinity,
    r=>r.bridge_walk.transportation_feature_ids=[123,123],r=>r.bridge_walk.transportation_feature_ids=[],
    r=>r.bridge_walk.rails.pop(),r=>r.source_feature_ids={building:[4]},r=>r.collision_geometry={},r=>r.bridge_walk.posts[0].offset_m=19]){
    const {row}=fixture();transform(row);assert.equal(validBridgeWalk(row),false);
  }
});
