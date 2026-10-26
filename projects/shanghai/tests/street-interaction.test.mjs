import test from 'node:test';
import assert from 'node:assert/strict';
import {StreetInteraction, DEFAULT_GROUND_HEIGHT} from '../src/street-interaction.js';

const origin=[121.4862,31.2385],hash='a'.repeat(64),R=6378137,rad=Math.PI/180;
function point(x,north,alt) {
  const scale=R*Math.cos(origin[1]*rad);
  return {lng:origin[0]+x/scale/rad,lat:(2*Math.atan(Math.exp(Math.log(Math.tan(Math.PI/4+origin[1]*rad/2))+north/scale))-Math.PI/2)/rad,...(alt===undefined?{}:{alt})};
}
const coords=(x,y)=>{const p=point(x,y);return[p.lng,p.lat];};
const ring=(w,s,e,n)=>[[w,s],[e,s],[e,n],[w,n],[w,s]].map(([x,y])=>coords(x,y));
const polygon=(w,s,e,n,holes=[])=>({type:'Polygon',coordinates:[ring(w,s,e,n),...holes]});
const surface=(id,geometry,height)=>({type:'Feature',properties:{id,role:'walk-surface',height_world_m:height},geometry});
const obstacle=(id,geometry,extra={})=>({type:'Feature',properties:{id,role:'obstacle',base_world_m:0,top_world_m:1.16,blocks_walk:true,blocks_camera:true,...extra},geometry});
function fixture(features,local_obstacles=[]) {
  return {type:'FeatureCollection',schema_version:1,owner:'bund-streets',origin,web_model_sha256:hash,features,local_obstacles};
}
function active(features,local=[]) {
  const interaction=new StreetInteraction();
  assert.equal(interaction.setOwner('bund-streets',fixture(features,local),{modelSha256:hash,active:true}),true);
  return interaction;
}
const ground=(interaction,p)=>interaction.groundAt(p.lng,p.lat);

test('model SHA, explicit activation and removal bound all local ground/collision behavior',()=>{
  const data=fixture([surface('paving',polygon(-4,-4,4,4),.035),obstacle('bed',polygon(1,-1,2,1))]);
  const interaction=new StreetInteraction();
  assert.equal(interaction.setOwner('bund-streets',data,{modelSha256:hash}),true);
  assert.equal(ground(interaction,point(0,0)),null);
  assert.equal(interaction.sweep(point(0,0),point(3,0)),null);
  interaction.setOwnerActive('bund-streets',true);
  assert.equal(ground(interaction,point(0,0)).height,.035);
  assert.equal(interaction.sweep(point(0,0),point(3,0)).id,'bed');
  interaction.setOwnerActive('bund-streets',false);
  assert.equal(ground(interaction,point(0,0)),null);
  assert.equal(interaction.cameraCollision(point(0,0,.5),point(3,0,.5)),null);
  interaction.setOwnerActive('bund-streets',true);
  assert.equal(interaction.setOwner('bund-streets',data,{modelSha256:'b'.repeat(64),active:true}),false);
  assert.equal(interaction.getState().activeOwners,0,'hash mismatch cannot retain stale interaction');
  assert.equal(ground(interaction,point(0,0)),null);
});

test('exact Polygon holes and separate MultiPolygon components remain unsupported',()=>{
  const first=polygon(-5,-5,5,5,[ring(-1,-1,1,1)]);
  const multi={type:'MultiPolygon',coordinates:[first.coordinates,polygon(8,-1,10,1).coordinates]};
  const interaction=active([surface('paving',multi,.035)]);
  assert.equal(ground(interaction,point(0,0)),null,'courtyard/opening is not filled');
  assert.equal(ground(interaction,point(6,0)),null,'separate polygon components are not bridged');
  assert.equal(ground(interaction,point(9,0)).height,.035);
  assert.equal(ground(interaction,point(30,0)),null,'outside exact coverage stays baseline');
});

test('highest overlapping real surface supports low curbs; a narrow high step cannot be tunneled',()=>{
  const interaction=active([surface('ground',polygon(-5,-3,5,3),.035),surface('curb',polygon(0,-2,.1,2),.235)]);
  assert.equal(ground(interaction,point(.05,0)).height,.235);
  assert.equal(interaction.sweep(point(-.2,0),point(.2,0)),null,'exactly 20 cm rise/drop is supported');
  const blocked=active([surface('ground',polygon(-5,-3,5,3),.035),surface('high',polygon(0,-2,.02,2),.336)]);
  const hit=blocked.sweep(point(-.2,0),point(.225,0));
  assert.equal(hit.type,'street-step','both endpoints can be low while an interior stripe is impassable');
  assert.equal(hit.id,'high');
});

test('swept body radius stops a thin pole crossed within a single sprint frame',()=>{
  const interaction=active([obstacle('pole',{type:'Point',coordinates:coords(0,0)},{radius_m:.02,top_world_m:4})]);
  assert.equal(interaction.sweep(point(-.21,0),point(.215,0),{radius:.01}).id,'pole');
  assert.equal(interaction.sweep(point(-.21,.42),point(.215,.42),{radius:.38}),null);
  assert.equal(interaction.sweep(point(-.21,.39),point(.215,.39),{radius:.38}).id,'pole');
});

test('bed and mapped-opening exclusions block walking but low fixtures do not shorten a high camera',()=>{
  const interaction=active([
    obstacle('bed',polygon(0,-1,2,1),{top_world_m:.215}),
    obstacle('opening',polygon(3,-1,4,1),{kind:'unmodeled-opening',base_world_m:-1,top_world_m:2,blocks_camera:false}),
  ]);
  assert.equal(interaction.sweep(point(-1,0),point(1,0)).id,'bed');
  assert.equal(interaction.cameraCollision(point(-1,0,3),point(2,0,4)),null);
  assert.equal(interaction.cameraCollision(point(-1,0,.15),point(2,0,.15)).id,'bed');
  assert.equal(interaction.sweep(point(2.5,0),point(4.5,0)).kind,'unmodeled-opening');
  assert.equal(interaction.cameraCollision(point(2.5,0,.5),point(4.5,0,.5)),null);
});

test('real line thickness is retained and a polygon obstacle hole remains traversable when clear',()=>{
  const interaction=active([
    obstacle('rail',{type:'LineString',coordinates:[coords(-2,2),coords(2,2)]},{radius_m:.013}),
    obstacle('ring-bed',polygon(-3,-3,3,1,[ring(-2,-2,2,0)])),
  ]);
  assert.equal(interaction.sweep(point(-1,-1),point(1,-1),{radius:.3}),null);
  assert.equal(interaction.sweep(point(0,1.5),point(0,2.5),{radius:.1}).id,'rail');
});

test('same-source local furniture keeps square bases and ignores overhead arms for walkers',()=>{
  const primitives=[
    {id:'lamp-base',kind:'road_lamp',type:'box',center:[0,.145,0],size:[.32,.22,.32]},
    {id:'arm',kind:'road_lamp',type:'cylinder_segment',a:[-1,4.9,-2],b:[1,5.2,-2],radius:.042},
    {id:'sloped-bar',kind:'railing',type:'cylinder_segment',a:[0,0,-4],b:[2,4,-4],radius:.013},
    {id:'tree',type:'vertical_frustum',center_xz:[0,-6],bottom:.09,top:3,bottom_radius:.15,top_radius:.08},
    {id:'lamp-head',type:'ellipsoid',center:[0,5.6,-8],radii:[.48,.065,.16],rotation_z_radians:.22},
  ];
  const interaction=active([],primitives);
  assert.equal(interaction.sweep(point(-.5,0),point(.5,0),{radius:.1}).id,'lamp-base');
  assert.equal(interaction.sweep(point(-.5,.4),point(.5,.4),{radius:.1}),null);
  assert.equal(interaction.sweep(point(-.5,2),point(.5,2),{radius:.1}),null,'overhead lamp arm is not a ground wall');
  assert.equal(interaction.sweep(point(1.8,3.5),point(1.8,4.5),{radius:.1}),null,'sloped bar is clipped to the avatar vertical band');
  assert.equal(interaction.sweep(point(.2,3.5),point(.2,4.5),{radius:.1}).id,'sloped-bar');
  assert.equal(interaction.sweep(point(-.5,6),point(.5,6),{radius:.1}).id,'tree');
  assert.equal(interaction.sweep(point(-.5,8),point(.5,8),{radius:.1}),null);
});

test('invalid geometry or missing physical radius disables the entire owner rather than inventing geometry',()=>{
  const interaction=new StreetInteraction();
  const invalid=fixture([obstacle('unknown-pole',{type:'Point',coordinates:coords(0,0)})]);
  assert.equal(interaction.setOwner('bund-streets',invalid,{modelSha256:hash,active:true}),false);
  assert.match(interaction.getState().lastError.message,/radius/);
  assert.equal(interaction.getState().activeOwners,0);
  assert.equal(interaction.sweep(point(0,0),point(.1,0)),null);
  assert.equal(DEFAULT_GROUND_HEIGHT,.075);
});
