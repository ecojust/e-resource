import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import {OSMBuildingSuppressor, planOSMBuildingReplacement} from '../src/osm-building-suppression.js';

const source = JSON.parse(fs.readFileSync(new URL('./fixtures/osm-bund18-23809960.geojson', import.meta.url)));
const fixture = source.features[0];
const detail = JSON.parse(fs.readFileSync(new URL('../data/landmark-exclusions.json', import.meta.url)))
  .landmark_sources.find(item => item.landmark_id === 'bund18').confirmed_boundary;
const targetIndex = 44, target = fixture.geometry.coordinates[targetIndex];
const points = target.flat();
const ownerBounds = [Math.min(...points.map(p => p[0])), Math.min(...points.map(p => p[1])),
  Math.max(...points.map(p => p[0])), Math.max(...points.map(p => p[1]))];
const coverage = {cells: [{id: 'isolated-fixture-owner', bounds: ownerBounds}],
  landmarks: [{id: 'bund18', geometry: detail}], reserved: [{id: 'bund18', geometry: detail}]};
const empty = () => ({cells: [], landmarks: [], reserved: []});
const rect = (w,s,e,n) => ({type:'Polygon',coordinates:[[[w,s],[e,s],[e,n],[w,n],[w,s]]]});
const squareCoverage = {cells:[{id:'local',bounds:[0,0,10,10]}],landmarks:[],reserved:[]};
const multipart = {type:'Feature',id:7,properties:{render_height:26,render_min_height:2},
  geometry:{type:'MultiPolygon',coordinates:[rect(1,1,2,2).coordinates,rect(11,1,12,2).coordinates]}};
function area(coordinates) {
  return coordinates.reduce((total,ring,index) => {
    const [x0,y0] = ring[0]; let sum=0;
    for(let i=1;i<ring.length;i++)sum+=(ring[i-1][0]-x0)*(ring[i][1]-y0)-(ring[i][0]-x0)*(ring[i-1][1]-y0);
    return total+(index ? -1 : 1)*Math.abs(sum/2);
  },0);
}

test('actual OSM 23809960 keeps 45 exact components while removing Bund18 component 44', () => {
  assert.equal(fixture.id,23809960); assert.equal(fixture.geometry.coordinates.length,46);
  const plan = planOSMBuildingReplacement(source.features,coverage);
  assert.deepEqual(plan.hideIDs,[23809960]); assert.equal(plan.partialIDs,1);
  assert.equal(plan.removedComponents,1); assert.equal(plan.residualComponents,45);
  const expected = fixture.geometry.coordinates.filter((_,i)=>i!==targetIndex);
  assert.deepEqual(plan.residualData.features.map(f=>JSON.stringify(f.geometry.coordinates)).sort(), expected.map(p=>JSON.stringify(p)).sort());
  for(const f of plan.residualData.features) {
    assert.deepEqual(f.properties,fixture.properties);
    assert.equal(f.originalSourceId,fixture.id);
    assert.equal(f.geometry.type,'Polygon');
  }
  assert.equal(new Set(plan.residualData.features.map(f=>f.id)).size,45);
  const retainedArea = plan.residualData.features.reduce((sum,f)=>sum+area(f.geometry.coordinates),0);
  const originalArea = fixture.geometry.coordinates.reduce((sum,p)=>sum+area(p),0);
  assert.ok(Math.abs(retainedArea+area(target)-originalArea)<1e-18,'covered + residual area equals the original; no clipping');
});

test('actual detailed component stays online when its detailed owner is unavailable', () => {
  const plan = planOSMBuildingReplacement(source.features,{...coverage,landmarks:[]});
  assert.deepEqual(plan.hideIDs,[]); assert.equal(plan.residualComponents,0);
});

test('exact duplicated buffer components deduplicate despite ring start and winding differences', () => {
  const repeated = structuredClone(fixture); repeated.id=String(fixture.id);
  repeated.geometry.coordinates=repeated.geometry.coordinates.map(poly=>poly.map(ring=>[...ring].reverse()));
  const plan=planOSMBuildingReplacement([fixture,repeated],coverage);
  assert.deepEqual(plan.hideIDs,[23809960]); assert.equal(plan.duplicateComponents,46);
  assert.equal(plan.residualComponents,45); assert.equal(plan.removedComponents,1);
});

test('crossing single Polygon, unknown ID, and conflicting source properties remain unmasked', () => {
  const crossing={...multipart,geometry:rect(9,1,12,2)};
  assert.deepEqual(planOSMBuildingReplacement([crossing],squareCoverage).hideIDs,[]);
  assert.deepEqual(planOSMBuildingReplacement([{...multipart,id:undefined}],squareCoverage).hideIDs,[]);
  assert.deepEqual(planOSMBuildingReplacement([{...multipart,id:Number.MAX_SAFE_INTEGER+1}],squareCoverage).hideIDs,[]);
  assert.deepEqual(planOSMBuildingReplacement([multipart,{...multipart,properties:{render_height:40}}],squareCoverage).hideIDs,[]);
});

test('intersecting uncovered fragments stay exact without blocking an independent covered component', () => {
  const fragment={...multipart,geometry:{type:'MultiPolygon',coordinates:[rect(11.5,1,12.5,2).coordinates]}};
  const plan=planOSMBuildingReplacement([multipart,fragment],squareCoverage);
  assert.deepEqual(plan.hideIDs,[7]); assert.equal(plan.ambiguousFragments,1); assert.equal(plan.residualComponents,2);
  assert.deepEqual(plan.residualData.features.map(f=>JSON.stringify(f.geometry.coordinates)).sort(), [multipart.geometry.coordinates[1],fragment.geometry.coordinates[0]].map(p=>JSON.stringify(p)).sort());
});

test('uncovered component holes and source minimum/top heights are preserved exactly', () => {
  const holed=structuredClone(multipart); holed.geometry.coordinates[1].push(rect(11.2,1.2,11.8,1.8).coordinates[0].reverse());
  const plan=planOSMBuildingReplacement([holed],squareCoverage);
  assert.deepEqual(plan.residualData.features[0].geometry.coordinates,holed.geometry.coordinates[1]);
  assert.deepEqual(plan.residualData.features[0].properties,{render_height:26,render_min_height:2});
});

function fakeMap(features=[multipart]) {
  const states=new Map();
  return {source:{},features,states,removeError:false,
    getSource(){return this.source;},querySourceFeatures(){return this.features;},
    getFeatureState(t){return states.get(String(t.id))||{};},
    setFeatureState(t,v){states.set(String(t.id),v);},
    removeFeatureState(t){if(this.removeError)throw Error('remove failure');states.delete(String(t.id));}};
}
function deferredResidual() {
  return {calls:[],current:null,destroyed:false,
    replace(data){return new Promise((resolve,reject)=>this.calls.push({data,resolve:()=>{this.current=data;resolve();},reject}));},
    async clear(){this.current={type:'FeatureCollection',features:[]};},
    getState(){return {sourceId:'residual-test',layerId:'residual-layer-test'};},destroy(){this.destroyed=true;}};
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function setup(t) {
  const map=fakeMap(),residual=deferredResidual();let current=squareCoverage;
  const controller=new OSMBuildingSuppressor({map,source:'osm',residualLayer:residual,getCoverage:()=>current});
  t.after(()=>controller.destroy({mapWillBeRemoved:true})); controller.setActive(true);
  return {map,residual,controller,setCoverage:value=>{current=value;}};
}

test('original aggregate hides only after residual render acknowledgement; restore precedes residual drop', async t => {
  const {map,residual,controller,setCoverage}=setup(t);
  const pending=controller.refresh(); assert.equal(map.states.size,0); assert.equal(residual.calls.length,1);
  assert.equal(residual.calls[0].data.features.length,1);
  residual.calls[0].resolve(); await pending; assert.equal(map.states.get('7').localModel,true);
  setCoverage(empty()); controller.refresh(); assert.equal(map.states.size,0,'original restored synchronously before residual clear');
  assert.equal(residual.current.features.length,1,'old residual survives until the replacement renderer acknowledges');
  assert.equal(residual.calls[1].data.features.length,0); residual.calls[1].resolve(); await tick();
  assert.equal(residual.current.features.length,0);
});

test('failed residual readiness keeps original aggregate visible', async t => {
  const {map,residual,controller}=setup(t); const pending=controller.refresh();
  residual.calls[0].reject(Error('tile upload failed')); await pending;
  assert.equal(map.states.size,0); assert.equal(controller.getState().residualReady,false);
  assert.ok(controller.getState().residualErrors>0);
});

test('new original-source fragments immediately restore old ID and invalidate an in-flight snapshot', async t => {
  const {map,residual,controller}=setup(t); const first=controller.refresh();
  controller.sourceChanged(); residual.calls[0].resolve(); await first;
  assert.equal(map.states.size,0,'stale source epoch cannot hide the source');
  const second=controller.refresh(); residual.calls[1].resolve(); await second;
  assert.equal(map.states.get('7').localModel,true);
  controller.sourceChanged(); assert.equal(map.states.size,0,'new fragments are never hidden during debounce');
});

test('coverage change during residual upload cannot apply stale masks', async t => {
  const {map,residual,controller,setCoverage}=setup(t);const first=controller.refresh();
  setCoverage(empty());controller.refresh();residual.calls[0].resolve();await tick();
  assert.equal(map.states.size,0);assert.equal(residual.calls[1].data.features.length,0);
  residual.calls[1].resolve();await first;assert.equal(map.states.size,0);
});

test('failed original restoration retains old residual until removal succeeds', async t => {
  const {map,residual,controller,setCoverage}=setup(t);const first=controller.refresh();residual.calls[0].resolve();await first;
  map.removeError=true;setCoverage(empty());controller.refresh();
  assert.equal(controller.getState().pendingRemovals,1);assert.equal(residual.calls.length,1);
  assert.equal(residual.current.features.length,1,'still-masked ID retains its only uncovered-component representation');
  map.removeError=false;controller.refresh();assert.equal(map.states.size,0);assert.equal(residual.calls.length,2);
  residual.calls[1].resolve();await tick();
});

test('without a residual renderer a partially covered aggregate is never suppressed', () => {
  const map=fakeMap();const c=new OSMBuildingSuppressor({map,source:'osm',getCoverage:()=>squareCoverage});
  c.setActive(true);c.refresh();assert.equal(map.states.size,0);c.destroy();
});

test('loss of an already rendered residual layer restores original IDs immediately', async t => {
  const {map,residual,controller}=setup(t);const first=controller.refresh();residual.calls[0].resolve();await first;
  assert.equal(map.states.get('7').localModel,true);
  residual.isReady=()=>false;controller.residualInvalidated();
  assert.equal(map.states.size,0);assert.equal(controller.getState().residualReady,false);
  const retry=controller.refresh();assert.equal(map.states.size,0,'same-signature fast path cannot re-hide after resource loss');
  residual.calls[1].resolve();await retry;assert.equal(map.states.size,0);
});

const aggregate = polys => ({type:'Feature',id:7,properties:{render_height:5,render_min_height:0},geometry:{type:'MultiPolygon',coordinates:polys}});
const coordinateSet = features => features.map(f=>JSON.stringify(f.geometry.coordinates)).sort();

test('a covered target is independent of a remote touching mixed-coverage cluster', () => {
  const polygons=[rect(1,1,2,2).coordinates,rect(7,1,9,2).coordinates,rect(9,1,11,2).coordinates,rect(11,1,12,2).coordinates];
  const result=planOSMBuildingReplacement([aggregate(polygons)],squareCoverage);
  assert.deepEqual(result.hideIDs,[7]);assert.equal(result.removedComponents,1);
  assert.deepEqual(coordinateSet(result.residualData.features),polygons.slice(1).map(p=>JSON.stringify(p)).sort(),
    'transitive contact retains the covered member along with both crossing/outside members');
});

test('a wholly covered intersecting cluster can be removed while an outside component remains', () => {
  const polygons=[rect(1,1,3,3).coordinates,rect(2,2,4,4).coordinates,rect(11,1,13,3).coordinates];
  const result=planOSMBuildingReplacement([aggregate(polygons)],squareCoverage);
  assert.deepEqual(result.hideIDs,[7]);assert.equal(result.removedComponents,2);
  assert.deepEqual(result.residualData.features[0].geometry.coordinates,polygons[2]);
});

test('retained holes and inside-hole independent covered components keep their original geometry', () => {
  const donut=[rect(6,1,12,8).coordinates[0],rect(7,2,9,6).coordinates[0].reverse()];
  const inHole=rect(7.2,3,8.8,5).coordinates;
  const result=planOSMBuildingReplacement([aggregate([donut,inHole])],squareCoverage);
  assert.deepEqual(result.hideIDs,[7]);assert.equal(result.removedComponents,1);
  assert.deepEqual(result.residualData.features[0].geometry.coordinates,donut);
  assert.deepEqual(result.residualData.features[0].properties,{render_height:5,render_min_height:0});
});

test('mixed-coverage grouping is independent of component order and exact duplicate fragments', () => {
  const polys=[rect(1,1,2,2).coordinates,rect(7,1,9,2).coordinates,rect(9,1,11,2).coordinates,rect(11,1,12,2).coordinates];
  const expected=planOSMBuildingReplacement([aggregate(polys)],squareCoverage);
  const shuffled=aggregate([polys[3],polys[1],polys[0],polys[2],polys[1]]);
  const other={...aggregate([polys[0]]),id:'7'};
  const actual=planOSMBuildingReplacement([shuffled,other],squareCoverage);
  assert.deepEqual(actual.hideIDs,[7]);assert.equal(actual.duplicateComponents,2);
  assert.equal(actual.removedComponents,expected.removedComponents);
  assert.deepEqual(actual.residualData,expected.residualData);
});

test('a mixed connected cluster without any independent covered component stays entirely online', () => {
  const value=aggregate([rect(8,1,10,2).coordinates,rect(10,1,12,2).coordinates]);
  const result=planOSMBuildingReplacement([value],squareCoverage);
  assert.deepEqual(result.hideIDs,[]);assert.equal(result.removedComponents,0);assert.equal(result.residualComponents,0);
});

test('actual Hongde MVT aggregate removes component745 and preserves all45 residual components exactly', () => {
  const file=new URL('./fixtures/osm-hongde-118016460.json',import.meta.url);
  const actual=JSON.parse(fs.readFileSync(file));const feature=actual.features[0];const e=actual.evidence;
  assert.equal(feature.id,118016460);assert.equal(feature.geometry.coordinates.length,1398);
  const plan=planOSMBuildingReplacement(actual.features,actual.coverage);
  assert.deepEqual(plan.hideIDs,[118016460]);assert.equal(plan.duplicateComponents,1);
  assert.equal(plan.removedComponents,1352);assert.equal(plan.residualComponents,45);
  assert.equal(plan.removedComponents+plan.residualComponents,e.unique_components);
  const expected=actual.expected_retained_original_indices.map(i=>feature.geometry.coordinates[i]);
  assert.equal(expected.length,45);assert.equal(new Set(expected.map(p=>JSON.stringify(p))).size,45);
  assert.deepEqual(coordinateSet(plan.residualData.features),expected.map(p=>JSON.stringify(p)).sort());
  const target=JSON.stringify(feature.geometry.coordinates[e.target_original_component_index]);
  assert.ok(!coordinateSet(plan.residualData.features).includes(target));
  for(const i of e.mixed_original_component_indices)assert.ok(coordinateSet(plan.residualData.features).includes(JSON.stringify(feature.geometry.coordinates[i])));
  for(const f of plan.residualData.features){assert.equal(f.originalSourceId,118016460);assert.deepEqual(f.properties,feature.properties);}
  const permuted={...feature,geometry:{...feature.geometry,coordinates:[...feature.geometry.coordinates].reverse()}};
  assert.deepEqual(planOSMBuildingReplacement([permuted],actual.coverage).residualData,plan.residualData);
});
