import test from 'node:test';
import assert from 'node:assert/strict';
import {candidateGeometryContains,mergeCandidateCityModels,validCandidateGeometry} from '../src/candidate-city-integrations.js';

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
