import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {SourceGeometryCorrectionState} from '../src/source-geometry-correction.js';
import {planOSMBuildingReplacement} from '../src/osm-building-suppression.js';
import {fixture,ID,clone,makeRecord,makeBoundary,loadVerified,rect,syntheticCollision} from './source-correction-fixtures.mjs';

// Run production map-scene closures, not a duplicate implementation of cache,
// collision tests, revision invalidation or OSM coverage construction.
const source=fs.readFileSync(new URL('../src/map-scene.js',import.meta.url),'utf8');
function section(from,to,start=0) {
  const a=source.indexOf(from,start);assert(a>=0,`missing production section ${from}`);
  const b=source.indexOf(to,a+from.length);assert(b>a,`missing production end ${to}`);return source.slice(a,b);
}
const geographic=section('function ringContains(','function configureStyle(');
const correctionInitialization=section('  const sourceGeometryCorrections =','  let ordinaryCatalog=');
const collisionBody=section('  function sourceFeatures(','  async function waitForData(');
const suppressorStart=source.indexOf('osmSuppression = new OSMBuildingSuppressor(');
const coverageBody=section('    getCoverage() {','    onChange()',suppressorStart);
assert(collisionBody.includes('filterFeature') && correctionInitialization.includes('collisionUpdated=-Infinity'));

function harness() {
  const f=makeRecord();const records=new Map([[ID,f.record]]),boundaries=new Map([[ID,makeBoundary(f.record)]]);
  const ordinary={type:'Feature',source:'openmaptiles',sourceLayer:'building',id:999,properties:{render_height:9},
    featureState:{localModel:true},geometry:rect(121.31710,30.72052,121.31714,30.72056)};
  const water={type:'Feature',id:'water-test-only',properties:{},geometry:rect(121.3196,30.7202,121.3199,30.7206)};
  const bridge={type:'Feature',properties:{class:'minor',brunnel:'bridge'},geometry:{type:'LineString',coordinates:[[121.3196,30.7204],[121.3199,30.7204]]}};
  const samples=new Map([
    ['openmaptiles:building',[clone(fixture.osm),ordinary]],['openmaptiles:water',[water]],['openmaptiles:transportation',[bridge]],
    ['overture-buildings:building',[clone(fixture.overture),{...ordinary,source:'overture-buildings',id:'neighbor-uuid',properties:{id:'neighbor-uuid'}}]],
    ['overture-buildings:building_part',[]],
  ]);
  const events=[];const clock={value:1000};const map={getZoom:()=>19,triggerRepaint(){events.push('repaint');},
    querySourceFeatures:(id,{sourceLayer})=>samples.get(`${id}:${sourceLayer}`)||[]};
  const localStreamer={getVisible:()=>[]},staticLandmarkIds=new Set();
  const env={SourceGeometryCorrectionState,scene:f.sceneRoot,landmarkRecords:records,landmarkBoundaries:boundaries,
    map,performance:{now:()=>clock.value},osmSuppression:{schedule(){events.push('OSM scheduled');}},localStreamer,staticLandmarkIds};
  const names=Object.keys(env);
  const factory=new Function(...names,`const DEG=Math.PI/180,EARTH=6378137,clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
    let destroyed=false,buildingMode='osm',buildingSourceId='openmaptiles';const sourceId='openmaptiles';
    let collisionDirty=true,collisionUpdated=0,collisionRevision=0,polygons=[],largePolygons=[],grid=new Map(),roadLines=[];
    ${geographic}\n${correctionInitialization}\n${collisionBody}
    const coverageProvider={${coverageBody}};
    return {collisionAt,rebuild:rebuildCollisionCache,sync:syncSourceGeometryCorrections,state:sourceGeometryCorrections,
      coverage:()=>coverageProvider.getCoverage(),isLandmarkSourceActive,
      setMode(mode){buildingMode=mode;buildingSourceId=mode==='overture'?'overture-buildings':'openmaptiles';},
      cache:()=>({revision:collisionRevision,dirty:collisionDirty,updated:collisionUpdated,polygons,roadLines})};`);
  return {...f,records,boundaries,samples,ordinary,water,bridge,events,clock,localStreamer,staticLandmarkIds,...factory(...names.map(n=>env[n]))};
}
const front=[121.31839,30.72090],newObstacle=[121.31833,30.72053],neighbor=[121.31712,30.72054];

test('actual collision cache removes exact source component, installs finite reviewed obstacle, and retains other buildings/water/bridge',async()=>{
  const h=harness();assert.equal(h.collisionAt(...front),'building');const oldRevision=h.cache().revision;
  await loadVerified(h);assert.equal(h.collisionAt(...front),null,'walkway becomes free without waiting850ms ormoveend');
  assert.ok(h.cache().revision>oldRevision);assert.equal(h.clock.value,1000);
  assert.equal(h.collisionAt(...newObstacle),'building','finite replacement obstacle remains blocked');
  assert.equal(h.collisionAt(...neighbor),'building','unrelatedUUID andfeature-state.localModel do not bypasscollision');
  assert.equal(h.collisionAt(121.33055,30.72050),'building','remote retainedcomponent stillcollides');
  const remainder=h.cache().polygons.find(p=>p.geometry.type==='MultiPolygon');
  assert.deepEqual(remainder.geometry.coordinates,fixture.osm.geometry.coordinates.slice(1));
  assert(h.cache().polygons.some(p=>JSON.stringify(p.geometry)===JSON.stringify(syntheticCollision())));
  assert.equal(h.collisionAt(121.31975,30.72055),'water');
  assert.equal(h.collisionAt(121.31975,30.72040),null,'existing bridge exemption still applies towater');
});

test('actual activation callback bypasses throttle and revises cache immediately on hidden/wrong variant/dispose/catalog removal',async()=>{
  const h=harness();await loadVerified(h);assert.equal(h.collisionAt(...front),null);let rev=h.cache().revision;
  for(const [disable,restore] of [
    [()=>h.record.object.visible=false,()=>h.record.object.visible=true],
    [()=>h.record.activeVariant='distant',()=>h.record.activeVariant='full'],
    [()=>h.record.catalogDisposed=true,()=>h.record.catalogDisposed=false],
  ]) {
    disable();assert.equal(h.collisionAt(...front),'building');assert.ok(h.cache().revision>rev);rev=h.cache().revision;
    assert.equal(h.cache().polygons.some(p=>JSON.stringify(p.geometry)===JSON.stringify(syntheticCollision())),false);
    restore();assert.equal(h.collisionAt(...front),null);assert.ok(h.cache().revision>rev);rev=h.cache().revision;
  }
  const boundary=h.boundaries.get(ID);h.boundaries.delete(ID);assert.equal(h.collisionAt(...front),'building');
  h.boundaries.set(ID,boundary);assert.equal(h.collisionAt(...front),null,'dynamicre-registration works withoutstartupcache');
  h.records.delete(ID);assert.equal(h.collisionAt(...front),'building');
  assert(h.events.includes('OSM scheduled'));assert(h.events.includes('repaint'));
});

test('actual mode transition uses correct source namespace and new variant receipt without changing water or ordinary behavior',async()=>{
  const h=harness();await loadVerified(h);assert.equal(h.collisionAt(...front),null);const rev=h.cache().revision;
  h.setMode('overture');assert.equal(h.collisionAt(...front),null);assert.ok(h.cache().revision>rev);
  assert.equal(h.collisionAt(...neighbor),'building');assert.equal(h.collisionAt(121.31975,30.72055),'water');
  h.record.activeVariant='distant';assert.equal(h.collisionAt(...front),'building');
  await loadVerified(h,{variant:'distant'});assert.equal(h.collisionAt(...front),null);
  h.setMode('osm');assert.equal(h.collisionAt(...front),null);
  h.boundaries.get(ID).source_geometry_correction.variants.lod.asset_sha256='f'.repeat(64);
  assert.equal(h.collisionAt(...front),'building','wrongLOD contract restores exact originalmodecollision');
});

test('actual OSM coverage excludes special compound boundary and reads dynamic registries while preserving generic ordinary coverage',async()=>{
  const h=harness();await loadVerified(h);
  const other={id:'ordinary-other',kind:'building',status:'loaded',object:{visible:true,parent:h.sceneRoot}};
  h.records.set(other.id,other);h.boundaries.set(other.id,{id:other.id,confirmed_boundary:h.ordinary.geometry});
  const coverage=h.coverage();assert.deepEqual(coverage.landmarks.map(v=>v.id),['ordinary-other']);
  assert(!coverage.reserved.some(v=>v.id===ID),'special wholepark boundary must not broadly reserve other ordinary owners');
  assert.equal(coverage.sourceGeometryCorrections.length,1);assert.equal(coverage.sourceGeometryCorrections[0].active,true);
  const plan=planOSMBuildingReplacement([fixture.osm,h.ordinary],coverage,{source:'openmaptiles',sourceLayer:'building'});
  assert(plan.hideIDs.includes(5607522290));assert(plan.hideIDs.includes(999),'ordinary owner stillusesexistingcoverage');
  const unknown={...h.ordinary,id:1000,geometry:rect(121.31720,30.72052,121.31724,30.72056)};
  const unknownPlan=planOSMBuildingReplacement([unknown],coverage,{source:'openmaptiles',sourceLayer:'building'});
  assert.deepEqual(unknownPlan.hideIDs,[],'wholepark boundary mustnot cover anunrelated building');
  h.boundaries.delete(ID);assert.equal(h.coverage().sourceGeometryCorrections.length,0);assert.equal(h.isLandmarkSourceActive(other),true);
});
