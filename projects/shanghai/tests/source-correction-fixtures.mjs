import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {loadOrdinaryLandmarkAsset} from '../src/ordinary-scene-adapter.js';

export const fixture = JSON.parse(fs.readFileSync(new URL('./fixtures/jinshan-live.json', import.meta.url)));
export const ID = 'jinshanwei-wengcheng-gatehouse';
export const ANCHOR = [121.31844475865365, 30.720547351191197];
export const hash = bytes => createHash('sha256').update(bytes).digest('hex');
export const clone = value => structuredClone(value);
export const rect = (w, s, e, n) => ({type:'Polygon',coordinates:[[[w,s],[e,s],[e,n],[w,n],[w,s]]]});
export const syntheticCollision = () => rect(121.31830,30.72050,121.31836,30.72056);
export const tick = () => new Promise(resolve => setImmediate(resolve));
export const deferred = () => { let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject}; };

export function minimalGLB(variant='web') {
  const raw=JSON.stringify({asset:{version:'2.0',generator:`synthetic-${variant}-test-only`}});
  const json=Buffer.from(raw.padEnd(Math.ceil(raw.length/4)*4,' '));
  const bytes=Buffer.alloc(20+json.length);bytes.writeUInt32LE(0x46546c67,0);bytes.writeUInt32LE(2,4);
  bytes.writeUInt32LE(bytes.length,8);bytes.writeUInt32LE(json.length,12);bytes.writeUInt32LE(0x4e4f534a,16);json.copy(bytes,20);
  return bytes;
}
export function makeRecord() {
  const web=minimalGLB('web'),lod=minimalGLB('lod');
  const meta=(variant,bytes)=>({file:`assets/models/test-only/${variant}.glb`,bytes:bytes.length,sha256:hash(bytes)});
  return {record:{id:ID,kind:'building',status:'idle',anchor:[...ANCHOR],lng:ANCHOR[0],lat:ANCHOR[1],
    ordinaryBaseURL:'https://fixture.invalid/project/',assets:{web:meta('web',web),lod:meta('lod',lod)},
    catalogDisposed:false},bytes:{web,lod},sceneRoot:{name:'current-scene-test-only'}};
}
export function makeBoundary(record) {
  const target={type:'Polygon',coordinates:clone(fixture.osm.geometry.coordinates[0])};
  return {id:record.id,confirmed_boundary:clone(fixture.overture.geometry),building_ids:[fixture.overture.id],building_part_ids:[],
    source_geometry_correction:{schema:'source-geometry-correction-v1',enabled:true,model_id:record.id,anchor:[...record.anchor],
      provenance:{source_record:'w1074070665@1',evidence_sha256:fixture.provenance.report_sha256},
      matches:[{source:fixture.osm.source,source_layer:fixture.osm.sourceLayer,native_id:fixture.osm.id,
        component:target,observed_component_index:0},
        {source:fixture.overture.source,source_layer:fixture.overture.sourceLayer,native_id:fixture.overture.id,
          property_id:fixture.overture.id,component:clone(fixture.overture.geometry),observed_component_index:0}],
      variants:{web:{asset_sha256:record.assets.web.sha256},lod:{asset_sha256:record.assets.lod.sha256}},
      // Synthetic finite obstacle only: this is NOT final model/collision acceptance.
      collision_geometry:syntheticCollision()}};
}
export async function loadVerified(f,{variant='full',scene=null,fetchFunction,loader,request}={}) {
  scene ||= {visible:true,userData:{},parent:f.sceneRoot};
  const kind=variant==='distant'?'lod':'web';
  const fetcher=fetchFunction|| (async()=>new Response(f.bytes[kind]));
  const parser=loader||{async parseAsync(){return {scene};}};
  const result=await loadOrdinaryLandmarkAsset({record:f.record,variant,fetchFunction:fetcher,loader:parser,request});
  f.record.object=result.scene;f.record.status='loaded';f.record.activeVariant=variant;
  return result;
}
export function retainedGeometrySet(features) {
  return features.map(f=>JSON.stringify(f.geometry.coordinates)).sort();
}
export function rotateClosed(ring, amount=1) {
  const open=ring.slice(0,-1),k=amount%open.length;const result=open.slice(k).concat(open.slice(0,k));
  return [...result,clone(result[0])];
}
