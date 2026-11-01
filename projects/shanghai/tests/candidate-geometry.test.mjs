import test from 'node:test';
import assert from 'node:assert/strict';
import {candidateGeometryContains,mergeCandidateCityModels,validCandidateGeometry,CandidateCityState} from '../src/candidate-city-integrations.js';

import {markVerifiedOrdinaryAsset} from '../src/ordinary-asset-verification.js';
import {CandidateCityClipper} from '../src/candidate-city-clipping.js';
import * as THREE from '../vendor/three.module.js';

const center=[121.47,31.23];
function ring(closedPoints,radius=.001,origin=center){
  const points=Array.from({length:closedPoints-1},(_,i)=>[origin[0]+radius*Math.cos(i*2*Math.PI/(closedPoints-1)),origin[1]+radius*Math.sin(i*2*Math.PI/(closedPoints-1))]);
  return [...points,points[0]];
}
const polygon=(...rings)=>({type:'Polygon',coordinates:rings});
const collisionOptions={collision:true};
const complicated=()=>polygon(ring(227),ring(97,.0005));
const model=geometry=>({id:'complex-collision',name:'Open-field collision fixture',kind:'building',lng:center[0],lat:center[1],heading:0,height_m:12,
  assets:{web:{file:'assets/fixture-web.glb',bytes:1,sha256:'1'.repeat(64)},lod:{file:'assets/fixture-lod.glb',bytes:1,sha256:'2'.repeat(64)}},
  placement:{status:'estimated'},navigation:{listed:false},collision_geometry:geometry});

test('complex collision retains its hole while the same geometry remains invalid for display clipping',()=>{
  const geometry=complicated();assert.equal(validCandidateGeometry(geometry),false);
  assert.equal(validCandidateGeometry(geometry,collisionOptions),true);
  assert.equal(candidateGeometryContains(geometry,center),false);
  assert.equal(candidateGeometryContains(geometry,[center[0]+.00075,center[1]]),true);
  assert.equal(candidateGeometryContains(geometry,[center[0]+.002,center[1]]),false);
});

test('only collision opts into the larger budget when models enter the runtime catalogue',()=>{
  const geometry=complicated(),row=model(geometry),manifest={schema:'candidate-city-integrations-v1',models:[row]};
  const before=structuredClone(manifest),merged=mergeCandidateCityModels([],manifest);
  assert.deepEqual(merged[0].collision_geometry,geometry);assert.deepEqual(manifest,before);
  assert.throws(()=>mergeCandidateCityModels([],{...manifest,models:[{...row,replacement_geometry:geometry}]}),/replacement_geometry/);
  assert.throws(()=>mergeCandidateCityModels([],{...manifest,models:[{...row,site_replacement:{id:'display-site',geometry}}]}),/场址修正/);
});

test('the closed-ring limit remains65 by default and is256 only for collision',()=>{
  assert.equal(validCandidateGeometry(polygon(ring(65))),true);
  assert.equal(validCandidateGeometry(polygon(ring(66))),false);
  assert.equal(validCandidateGeometry(polygon(ring(256)),collisionOptions),true);
  assert.equal(validCandidateGeometry(polygon(ring(257)),collisionOptions),false);
});

test('collision keeps a bounded number of holes and polygons',()=>{
  const rings=count=>polygon(ring(33,.02),...Array.from({length:count-1},(_,i)=>ring(5,.0001,[center[0]+(i%8-3.5)*.002,center[1]+(Math.floor(i/8)-1.5)*.002])));
  assert.equal(validCandidateGeometry(rings(8)),true);assert.equal(validCandidateGeometry(rings(9)),false);
  assert.equal(validCandidateGeometry(rings(32),collisionOptions),true);assert.equal(validCandidateGeometry(rings(33),collisionOptions),false);
  const pieces=count=>({type:'MultiPolygon',coordinates:Array.from({length:count},(_,i)=>[ring(5,.0002,[center[0]+i*.001,center[1]])])});
  assert.equal(validCandidateGeometry(pieces(32),collisionOptions),true);assert.equal(validCandidateGeometry(pieces(33),collisionOptions),false);
});

test('the total collision budget is4096 closed points across every component and hole',()=>{
  const geometry={type:'MultiPolygon',coordinates:Array.from({length:16},(_,i)=>[ring(256,.001,[center[0]+(i%4)*.003,center[1]+Math.floor(i/4)*.003])])};
  assert.equal(validCandidateGeometry(geometry,collisionOptions),true);
  geometry.coordinates.push([ring(5,.0002,[center[0]+.02,center[1]])]);
  assert.equal(validCandidateGeometry(geometry,collisionOptions),false,'4101 points must fail even though every ring and polygon fits separately');
});

test('collision retains finite coordinates, closed rings and geographic bounds',()=>{
  for(const mutate of [g=>g.coordinates[0][1][0]=Infinity,g=>g.coordinates[0][1][1]=86,g=>g.coordinates[0][1][0]=181,g=>g.coordinates[0].pop()]){
    const geometry=polygon(ring(227));mutate(geometry);assert.equal(validCandidateGeometry(geometry,collisionOptions),false);
  }
});

test('detailed opposing C-shaped stands leave their central field and both end passages open',()=>{
  const half=(start,end)=>{
    const arc=(radius,a,b)=>Array.from({length:100},(_,i)=>{const angle=(a+(b-a)*i/99)*Math.PI/180;return[center[0]+radius*Math.cos(angle),center[1]+radius*Math.sin(angle)];});
    const points=[...arc(.001,start,end),...arc(.0005,end,start)];return [...points,points[0]];
  };
  const geometry={type:'MultiPolygon',coordinates:[[half(100,260)],[half(-80,80)]]};
  assert.equal(validCandidateGeometry(geometry,collisionOptions),true);assert.equal(validCandidateGeometry(geometry),false);
  for(const y of [-.002,-.001,-.0005,0,.0005,.001,.002])assert.equal(candidateGeometryContains(geometry,[center[0],center[1]+y]),false);
  for(const x of [-.00075,.00075])assert.equal(candidateGeometryContains(geometry,[center[0]+x,center[1]]),true);
});


const heightClip=()=>({id:'north-upper-source',geometry:polygon(ring(5,.0002,[center[0]+.005,center[1]])),
  owner:{macro_id:'14-13722-6690',feature_local_id:1860},min_height:28.705,max_height:30.11,
  height_reference:[121.519775390625,31.306714687449947]});

test('height display clips require paired finite heights, a reference, one owner and distinct IDs',()=>{
  const row={...model(polygon(ring(5))),replacement_geometry:polygon(ring(5)),display_height_clips:[heightClip()]};
  const manifest={schema:'candidate-city-integrations-v1',models:[row]},before=structuredClone(manifest);
  assert.deepEqual(mergeCandidateCityModels([],manifest)[0].display_height_clips,row.display_height_clips);
  assert.deepEqual(manifest,before);
  for(const patch of [{min_height:undefined},{max_height:undefined},{min_height:null},{min_height:'28'},
    {min_height:NaN},{max_height:Infinity},{min_height:30.11},{min_height:32},
    {height_reference:undefined},{height_reference:[121,86]},{height_reference:[121,31,0]},
    {owner:undefined},{owner:{macro_id:'x',feature_local_id:0}},{owners:[]},
    {source_feature_ids:{building:['source'],building_part:[]}},{id:row.id}]){
    const invalid={...manifest,models:[{...row,display_height_clips:[{...heightClip(),...patch}]}]};
    assert.throws(()=>mergeCandidateCityModels([],invalid),/高度裁剪/);
  }
  for(const entries of [null,{},Array.from({length:9},(_,i)=>({...heightClip(),id:`height-${i}`})),[heightClip(),heightClip()]]){
    assert.throws(()=>mergeCandidateCityModels([],{...manifest,models:[{...row,display_height_clips:entries}]}),/高度裁剪/);
  }
  assert.throws(()=>mergeCandidateCityModels([],{...manifest,models:[row,{...row,id:'second'}]}),/高度裁剪/);
  assert.throws(()=>mergeCandidateCityModels([],{...manifest,models:[row,{...row,id:'second',display_height_clips:[],site_replacement:{id:heightClip().id,geometry:row.replacement_geometry}}]}),/高度裁剪/);
});

test('verified display height clips are GPU-only, append after base rows, and retire with visibility',t=>{
  const base=polygon(ring(5)),extra=heightClip(),scene=new THREE.Scene(),object=new THREE.Group();scene.add(object);
  const row={...model(base),replacement_geometry:base,source_feature_ids:{building:['main-source'],building_part:[]},
    owner:extra.owner,status:'loaded',object,activeVariant:'full',city_integration:true,display_height_clips:[extra]};
  const secondObject=new THREE.Group();scene.add(secondObject);
  const second={...row,id:'second',object:secondObject,display_height_clips:[],replacement_geometry:polygon(ring(5,.0002,[center[0]-.005,center[1]]))};
  markVerifiedOrdinaryAsset(object,{modelId:row.id,variant:'web',asset:row.assets.web});
  markVerifiedOrdinaryAsset(secondObject,{modelId:second.id,variant:'web',asset:second.assets.web});
  const records=new Map([[row.id,row],[second.id,second]]),events=[];
  const state=new CandidateCityState({getRecords:()=>records,getScene:()=>scene,onChange:s=>events.push(s.revision)});
  assert.equal(state.sync(),true);assert.equal(state.sync(),false);
  assert.deepEqual(state.clips.map(c=>c.id),[row.id,second.id]);
  assert.deepEqual(state.displayClips.map(c=>c.id),[row.id,second.id,extra.id]);
  assert.equal(state.clipsPoint(center[0]+.005,center[1],{name:'overture-buildings',layer:'building',id:'main-source'}),false);
  assert.equal(state.clipsPoint(...center,{name:'overture-buildings',layer:'building',id:'main-source'}),true);
  assert.deepEqual(state.collisions(),[{id:row.id,geometry:base},{id:second.id,geometry:base}]);
  assert.equal(state.getState().clips.length,2);assert.deepEqual(state.getState().displayClips[2].height_reference,extra.height_reference);
  const clipper=new CandidateCityClipper({THREE,geographicPosition:(x,z,y=0)=>new THREE.Vector3(x,y,z)});
  t.after(()=>clipper.dispose());clipper.update(state.clips);const basePayload=new Float32Array(clipper.data.subarray(0,4*16));
  clipper.update(state.displayClips);assert.equal(clipper.triangleCount,6);assert.deepEqual(clipper.data.subarray(0,4*16),basePayload);
  extra.min_height=28.71;assert.equal(state.sync(),true,'height-only edits enter the sync signature');
  object.visible=false;assert.equal(state.sync(),true);assert.deepEqual(state.displayClips,state.clips);
  assert.equal(state.displayClips.length,1);clipper.update(state.displayClips);assert.equal(clipper.triangleCount,2);
  secondObject.visible=false;assert.equal(state.sync(),true);assert.deepEqual(state.clips,[]);assert.deepEqual(state.displayClips,[]);
  assert.deepEqual(state.collisions(),[]);clipper.update(state.displayClips);assert.equal(clipper.triangleCount,0);
  assert.equal(events.length,4);
});

test('records without height clips retain exactly their existing display and source clips',()=>{
  const scene=new THREE.Scene(),object=new THREE.Group();scene.add(object);
  const row={...model(polygon(ring(5))),replacement_geometry:polygon(ring(5)),status:'loaded',object,activeVariant:'full',city_integration:true};
  markVerifiedOrdinaryAsset(object,{modelId:row.id,variant:'web',asset:row.assets.web});
  const state=new CandidateCityState({getRecords:()=>new Map([[row.id,row]]),getScene:()=>scene});state.sync();
  assert.deepEqual(state.displayClips,state.clips);assert.deepEqual(state.getState().displayClips,state.getState().clips);
});
