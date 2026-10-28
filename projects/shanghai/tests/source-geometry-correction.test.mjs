import test from 'node:test';
import assert from 'node:assert/strict';
import {SourceGeometryCorrectionState,canonicalComponentKey} from '../src/source-geometry-correction.js';
import {getVerifiedOrdinaryAsset} from '../src/ordinary-asset-verification.js';
import {loadOrdinaryLandmarkAsset} from '../src/ordinary-scene-adapter.js';
import {fixture,ID,clone,makeRecord,makeBoundary,loadVerified,rotateClosed,syntheticCollision} from './source-correction-fixtures.mjs';

const context={source:fixture.osm.source,sourceLayer:fixture.osm.sourceLayer,kind:'building'};
const otContext={source:fixture.overture.source,sourceLayer:fixture.overture.sourceLayer,kind:'building'};
function harness(f=makeRecord()) {
  const records=new Map([[ID,f.record]]),boundaries=new Map([[ID,makeBoundary(f.record)]]);
  let mode='osm';const events=[];
  const state=new SourceGeometryCorrectionState({getRecords:()=>records,getBoundaries:()=>boundaries,getMode:()=>mode,getScene:()=>f.sceneRoot,onChange:(...args)=>events.push(args)});
  return {...f,records,boundaries,state,events,setMode:value=>{mode=value;}};
}
const reduced=h=>h.state.filterFeature(fixture.osm,context);
const remaining=()=>fixture.osm.geometry.coordinates.slice(1);

test('actual native six-component feature loses only exact component0; five coordinate arrays remain unchanged',async()=>{
  const h=harness();await loadVerified(h);h.state.sync();assert.equal(h.state.isActive(ID),true);
  const result=reduced(h);assert.equal(result.type,'MultiPolygon');assert.deepEqual(result.coordinates,remaining());
  assert.deepEqual(fixture.osm.geometry.coordinates.length,6,'fixture never mutated');
  assert.deepEqual(h.state.getCollisionGeometries().map(x=>x.geometry),[syntheticCollision()]);
  h.setMode('overture');h.state.sync();assert.equal(h.state.filterFeature(fixture.overture,otContext),null);
});

test('component identity survives ring rotation/winding and numerical 8-decimal serialization, not displaced geometry',async()=>{
  const h=harness();await loadVerified(h);h.state.sync();
  const reverse=clone(fixture.osm);reverse.geometry.coordinates[0][0]=rotateClosed(reverse.geometry.coordinates[0][0].slice().reverse(),2);
  assert.deepEqual(h.state.filterFeature(reverse,context).coordinates,remaining());
  const rounded=clone(fixture.osm);rounded.geometry.coordinates[0]=rounded.geometry.coordinates[0].map(ring=>ring.map(p=>p.map(v=>Number(v.toFixed(8)))));
  assert.deepEqual(h.state.filterFeature(rounded,context).coordinates,remaining());
  assert.equal(canonicalComponentKey(reverse.geometry.coordinates[0]),canonicalComponentKey(fixture.osm.geometry.coordinates[0]));
  const displaced=clone(fixture.osm);displaced.geometry.coordinates[0][0][1][0]+=1e-6;
  assert.deepEqual(h.state.filterFeature(displaced,context),displaced.geometry,'matching bounding region is insufficient');
  const holes=clone(fixture.osm);holes.geometry.coordinates[0].push([[121.317,30.7204],[121.3171,30.7204],[121.3171,30.7205],[121.317,30.7205],[121.317,30.7204]]);
  assert.deepEqual(h.state.filterFeature(holes,context),holes.geometry,'additional hole changes exact component');
});

test('actual target may move within MultiPolygon order; observed index is evidence rather than arbitrary removal index',async()=>{
  const h=harness();await loadVerified(h);h.state.sync();const f=clone(fixture.osm);
  f.geometry.coordinates=[...f.geometry.coordinates.slice(1),f.geometry.coordinates[0]];
  assert.deepEqual(h.state.filterFeature(f,context).coordinates,remaining());
});

test('wrong source/sourceLayer/native type/property ID and water are never corrected',async()=>{
  const h=harness();await loadVerified(h);h.state.sync();
  for(const patch of [{source:'other-source'},{sourceLayer:'building_part'},{kind:'water'}])
    assert.deepEqual(h.state.filterFeature(fixture.osm,{...context,...patch}),fixture.osm.geometry);
  for(const id of [1074070665,5607522291,String(fixture.osm.id),undefined]) {
    const f={...fixture.osm,id};assert.deepEqual(h.state.filterFeature(f,context),f.geometry);
  }
  h.setMode('overture');h.state.sync();const wrong={...fixture.overture,properties:{...fixture.overture.properties,id:'different-uuid'}};
  assert.deepEqual(h.state.filterFeature(wrong,otContext),wrong.geometry);
  const ordinary={...fixture.overture,id:'other-uuid',properties:{id:'other-uuid'}};
  assert.deepEqual(h.state.filterFeature(ordinary,otContext),ordinary.geometry);
});

test('unconfigured ordinary object and forged userData cannot activate replacement',async()=>{
  const h=harness();h.boundaries.get(ID).source_geometry_correction=undefined;await loadVerified(h);h.state.sync();
  assert.equal(h.state.isActive(ID),false);assert.deepEqual(reduced(h),fixture.osm.geometry);
  h.boundaries.set(ID,makeBoundary(h.record));const genuine=h.record.object;
  h.record.object={visible:true,parent:h.sceneRoot,userData:genuine.userData};h.state.sync();
  assert.equal(getVerifiedOrdinaryAsset(h.record.object),null);assert.equal(h.state.isActive(ID),false);
  h.record.object=genuine;h.state.sync();assert.equal(h.state.isActive(ID),true);
});

test('SHA mismatch and parser failure never create a usable verified object; successful parser needs one fetch only',async()=>{
  for(const failure of ['hash','parse']) {
    const h=harness();let parses=0;const scene={visible:true,parent:h.sceneRoot,userData:{__ordinaryVerifiedAsset:{sha256:h.record.assets.web.sha256}}};
    const corrupt=Buffer.from(h.bytes.web);corrupt[corrupt.length-1]^=1;
    await assert.rejects(loadOrdinaryLandmarkAsset({record:h.record,variant:'full',
      fetchFunction:async()=>new Response(failure==='hash'?corrupt:h.bytes.web),
      loader:{async parseAsync(){parses++;throw Error('synthetic parse failure');}}}));
    assert.equal(parses,failure==='hash'?0:1);assert.equal(getVerifiedOrdinaryAsset(scene),null);
    h.record.object=scene;h.record.status='loaded';h.record.activeVariant='full';h.state.sync();assert.equal(h.state.isActive(ID),false);
  }
  const h=harness();let fetches=0,parses=0;
  const scene={visible:true,parent:h.sceneRoot,userData:{__ordinaryVerifiedAsset:{sha256:'f'.repeat(64)}}};
  await loadVerified(h,{scene,fetchFunction:async()=>{fetches++;return new Response(h.bytes.web);},loader:{async parseAsync(){parses++;return {scene};}}});
  assert.equal(fetches,1);assert.equal(parses,1);assert.ok(getVerifiedOrdinaryAsset(scene));h.state.sync();assert.equal(h.state.isActive(ID),true);
});

test('unsupported/hash-wrong variants fail closed; web and LOD use their own successful actual byte receipts',async()=>{
  const h=harness();await loadVerified(h);h.state.sync();assert.equal(h.state.isActive(ID),true);
  h.record.activeVariant='distant';h.state.sync();assert.equal(h.state.isActive(ID),false,'web object cannot masquerade asLOD');
  await loadVerified(h,{variant:'distant'});h.state.sync();assert.equal(h.state.isActive(ID),true);
  h.record.failedVariants=new Set(['full']);h.state.sync();assert.equal(h.state.isActive(ID),true,'valid visibleLOD survives a failed full upgrade');
  h.record.activeVariant='unknown';h.state.sync();assert.equal(h.state.isActive(ID),false);
  h.record.activeVariant='distant';h.boundaries.get(ID).source_geometry_correction.variants.lod.asset_sha256='f'.repeat(64);
  h.state.sync();assert.equal(h.state.isActive(ID),false);assert.deepEqual(reduced(h),fixture.osm.geometry);
});

test('visibility, attachment, loading state, disposal, catalog removal and mode transitions synchronously invalidate cached activation',async()=>{
  const h=harness();await loadVerified(h);h.state.sync();let previousEvents=h.events.length;
  for(const [disable,enable] of [
    [()=>h.record.object.visible=false,()=>h.record.object.visible=true],
    [()=>h.record.object.parent=null,()=>h.record.object.parent=h.sceneRoot],
    [()=>h.record.object.parent={name:'foreign-scene'},()=>h.record.object.parent=h.sceneRoot],
    [()=>h.record.status='error',()=>h.record.status='loaded'],
    [()=>h.record.catalogDisposed=true,()=>h.record.catalogDisposed=false],
  ]) {
    disable();assert.equal(h.state.sync(),true);assert.equal(h.state.isActive(ID),false);assert.deepEqual(reduced(h),fixture.osm.geometry);
    assert.deepEqual(h.state.getCollisionGeometries(),[]);assert.ok(h.events.length>previousEvents);previousEvents=h.events.length;
    enable();assert.equal(h.state.sync(),true);assert.equal(h.state.isActive(ID),true);
  }
  const boundary=h.boundaries.get(ID);h.boundaries.delete(ID);assert.equal(h.state.sync(),true);assert.equal(h.state.isActive(ID),false);
  h.boundaries.set(ID,boundary);assert.equal(h.state.sync(),true);assert.equal(h.state.isActive(ID),true);
  h.records.delete(ID);assert.equal(h.state.sync(),true);assert.equal(h.state.isActive(ID),false);
  h.records.set(ID,h.record);h.state.sync();h.setMode('overture');assert.equal(h.state.sync(),true);assert.equal(h.state.isActive(ID),true);
  assert.equal(h.state.sync(),false,'stable activation does not continuously churn revision');
});

test('disabled placeholder, bad schema, foreign model/anchor, absent SHA and invalid obstacle never remove source',async()=>{
  const edits=[c=>c.enabled=false,c=>c.schema='source-geometry-correction-v999',c=>c.model_id='other-model',c=>c.anchor[0]+=0.01,
    c=>c.variants.web.asset_sha256=null,c=>c.collision_geometry={type:'Polygon',coordinates:[]},
    c=>c.collision_geometry=clone(fixture.overture.geometry),
    c=>c.matches[0].component.coordinates[0].pop()];
  for(const edit of edits) {
    const h=harness();await loadVerified(h);edit(h.boundaries.get(ID).source_geometry_correction);h.state.sync();
    assert.equal(h.state.isActive(ID),false);assert.deepEqual(reduced(h),fixture.osm.geometry);assert.deepEqual(h.state.getCollisionGeometries(),[]);
  }
});
