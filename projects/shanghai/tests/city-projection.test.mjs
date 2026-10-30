import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import * as THREE from '../vendor/three.module.js';

const source=readFileSync(new URL('../src/map-scene.js',import.meta.url),'utf8');
const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,
  setTimeout,clearTimeout,performance};
context.exports=context.module.exports;context.self=context;context.globalThis=context;
vm.runInNewContext(readFileSync(new URL('../vendor/maplibre-gl.js',import.meta.url),'utf8'),context);
const maplibre=context.module.exports, M=maplibre.MercatorCoordinate;
const ORIGIN=[121.4737,31.2304], R=6378137, rad=Math.PI/180;

// Exact immutable effective-source footprint, macro14-13701-6700/local1148,
// building89f6310b-5602-4121-92c5-ac67809118a5. Overture2026-10-21,
// Zenodo EastAsianBuildings source; project data/SOURCES.md attribution applies.
const qingpu={origin:[121.058349609375,31.11879392996346], points:[
  [121.05110765,31.11289289],[121.05107546,31.11296179],
  [121.05128467,31.11302149],[121.05131686,31.1129526]]};
const oldEye=[121.05109969688647,31.112890395423506];

/** Execute the actual production preparation and coordinate functions. */
function production() {
  const coordinates=source.slice(source.indexOf('  const mercatorOrigin ='),source.indexOf('  const scene = new THREE.Scene();'));
  const far=source.slice(source.indexOf('  function prepareCityObject('),source.indexOf('  function handleStreamingChange('));
  const near=source.slice(source.indexOf('  function prepareCityDetailObject('),source.indexOf('  async function setCityManifest('));
  const calls=[];
  const value=new Function('THREE','maplibregl','calls',`
    const ORIGIN=${JSON.stringify(ORIGIN)},EARTH=6378137,DEG=Math.PI/180;
    const cityDetails={prepareFarObject:(object,record)=>calls.push({object,record})};
    const surfaces={apply(){}},lighting={configureModel(){}},candidateClipper={bindObject(){}};
    function applyBuildingMaterial(){}
    ${coordinates}\n${far}\n${near}
    return {prepareCityObject,prepareCityDetailObject,geographicPosition,worldToMercator,metreScale};
  `)(THREE,maplibre,calls);
  return {...value,calls};
}

// This is the frozen Python builder local_coordinates definition translated
// literally, including nonlinear Mercator northing (not latitude*metres).
function authored(point,origin,height=0) {
  const c=Math.cos(origin[1]*rad);
  return new THREE.Vector3(
    Math.fround(R*(point[0]-origin[0])*rad*c),Math.fround(height),
    Math.fround(-R*(Math.asinh(Math.tan(point[1]*rad))-Math.asinh(Math.tan(origin[1]*rad)))*c));
}
function worldGeographic(local,group,env) {
  group.updateMatrixWorld(true);
  const p=local.clone().applyMatrix4(group.matrixWorld).applyMatrix4(env.worldToMercator);
  const m=new M(p.x,p.y,p.z),ll=m.toLngLat();return {lng:ll.lng,lat:ll.lat,alt:m.toAltitude()};
}
function distance(a,b) {
  return Math.hypot((a[0]-b[0])*rad*R*Math.cos((a[1]+b[1])*.5*rad),(a[1]-b[1])*rad*R);
}
function contains(points,p) {
  let yes=false;
  for(let i=0,j=points.length-1;i<points.length;j=i++) {
    const [x,y]=points[i],[u,v]=points[j];
    if((y>p[1])!==(v>p[1])&&p[0]<(u-x)*(p[1]-y)/(v-y)+x)yes=!yes;
  }
  return yes;
}
function prepared(origin) {
  const env=production(), group=new THREE.Group(), record={id:'test-macro',name:'test',lng:origin[0],lat:origin[1]};
  env.prepareCityObject(group,record);return {env,group,record};
}

test('actual MapLibre/Three city projection puts1148 source points back within2mm',()=>{
  const {env,group,record}=prepared(qingpu.origin);
  const projected=qingpu.points.map(p=>worldGeographic(authored(p,qingpu.origin),group,env));
  for(let i=0;i<projected.length;i++)
    assert.ok(distance(qingpu.points[i],[projected[i].lng,projected[i].lat])<.002,
      'Float32 authored geometry must align with source, not the mean-earth radius-scaled outline');
  assert.equal(contains(projected.map(p=>[p.lng,p.lat]),oldEye),false,
    'The diagnosed v2 eye must not move inside1148 merely due to model-to-map unit conversion');
  assert.equal(env.calls.length,1);assert.equal(env.calls[0].object,group);assert.equal(env.calls[0].record,record);
});

test('the former uniform metre conversion reproduces the diagnosed>1m offset/inside-eye negative control',()=>{
  const {env,group}=prepared(qingpu.origin);
  const oldScale=M.fromLngLat(qingpu.origin).meterInMercatorCoordinateUnits()/env.metreScale;
  group.scale.setScalar(oldScale);
  const projected=qingpu.points.map(p=>worldGeographic(authored(p,qingpu.origin),group,env));
  assert.ok(Math.max(...projected.map((p,i)=>distance(qingpu.points[i],[p.lng,p.lat])))>1);
  assert.equal(contains(projected.map(p=>[p.lng,p.lat]),oldEye),true);
});

test('geographic anchor and vertical scale remain exactly the old values',()=>{
  const {env,group}=prepared(qingpu.origin);
  const oldAnchor=env.geographicPosition(...qingpu.origin,0);
  assert.deepEqual(group.position.toArray(),oldAnchor.toArray());
  assert.equal(group.scale.y,M.fromLngLat(qingpu.origin).meterInMercatorCoordinateUnits()/env.metreScale);
  const atAnchor=worldGeographic(new THREE.Vector3(0,18.7,0),group,env);
  assert.ok(Math.abs(atAnchor.alt-18.7)<1e-8);
});

test('far, ordinary near, and owner override groups copy one corrected transform without changing child IDs/geometry',()=>{
  const {env,group:far}=prepared(qingpu.origin);
  for(const replacement of [false,true]) {
    const near=new THREE.Group(),target=new THREE.Group();target.name='precise_target_25';target.userData={featureLocalIds:[25]};
    target.visible=false;near.add(target);near.userData={featureLocalIds:[25,9,28],replacement};
    env.prepareCityDetailObject(near,far,{id:'test-near'});
    assert.deepEqual(near.position.toArray(),far.position.toArray());
    assert.deepEqual(near.scale.toArray(),far.scale.toArray());
    assert.deepEqual(near.quaternion.toArray(),far.quaternion.toArray());
    assert.deepEqual(near.userData,{featureLocalIds:[25,9,28],replacement});
    assert.deepEqual(target.userData.featureLocalIds,[25]);assert.equal(target.visible,false);
    const point=authored(qingpu.points[0],qingpu.origin);
    assert.deepEqual(worldGeographic(point,near,env),worldGeographic(point,far,env));
  }
});

test('16district anchor samples bound Float32 horizontal and existing uniform-Y nonlinear residuals',()=>{
  const districts=JSON.parse(readFileSync(new URL('../data/districts.json',import.meta.url),'utf8')).districts;
  assert.equal(districts.length,16);
  for(const district of districts) {
    const origin=district.center,{env,group}=prepared(origin),c=Math.cos(origin[1]*rad);
    for(const east of [-1500,0,1500])for(const north of [-1500,0,1500]) {
      const point=[origin[0]+east/(R*c)/rad,
        Math.atan(Math.sinh(Math.asinh(Math.tan(origin[1]*rad))+north/(R*c)))/rad];
      const result=worldGeographic(authored(point,origin,300),group,env);
      assert.ok(distance(point,[result.lng,result.lat])<.002,'Ground projection tolerance2mm includes authored Float32 rounding');
      // The existing single-origin vertical metre scale is intentionally kept.
      // It is not exactly geographic altitude at another latitude. For this
      // +-1.5km,300m-high envelope, its residual must remain below6cm.
      assert.ok(Math.abs(result.alt-300)<.06,'Do not claim exact altitude at every latitude');
    }
  }
});
