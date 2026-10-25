import assert from 'node:assert/strict';
import test from 'node:test';
import {geometryFullyCovered, OSMBuildingSuppressor} from '../src/osm-building-suppression.js';

const ring = (w, s, e, n) => [[w,s],[e,s],[e,n],[w,n],[w,s]];
const rect = (w, s, e, n) => ({type:'Polygon', coordinates:[ring(w,s,e,n)]});
const cell = (id, bounds) => ({id, bounds});
const landmark = (id, geometry) => ({id, geometry});
const coverage = (cells=[], landmarks=[], reserved=[]) => ({cells, landmarks, reserved});
const block = coverage([cell('visible-local', [0,0,10,10])]);
const donut = {type:'Polygon', coordinates:[ring(0,0,10,10), [...ring(4,4,6,6)].reverse()]};
const concave = {type:'Polygon', coordinates:[[[0,0],[10,0],[10,10],[7,10],[7,3],[3,3],[3,10],[0,10],[0,0]]]};

test('cell coverage includes polygon boundary contact but preserves outside and crossing buildings', () => {
  assert.equal(geometryFullyCovered(rect(1,1,3,3), block), true);
  assert.equal(geometryFullyCovered(rect(0,0,10,10), block), true);
  assert.equal(geometryFullyCovered(rect(10,2,12,4), block), false);
  assert.equal(geometryFullyCovered(rect(9,2,11,4), block), false);
  assert.equal(geometryFullyCovered(rect(11,2,12,4), block), false);
});

test('active adjacent cells may jointly cover a building; a missing cell or gap must preserve it', () => {
  const building = rect(4,2,6,8);
  assert.equal(geometryFullyCovered(building, coverage([
    cell('left',[0,0,5,10]), cell('right',[5,0,10,10]),
  ])), true);
  assert.equal(geometryFullyCovered(building, coverage([cell('left',[0,0,5,10])])), false);
  assert.equal(geometryFullyCovered(building, coverage([
    cell('left',[0,0,4.9,10]), cell('right',[5.1,0,10,10]),
  ])), false);
});

test('coverage union must cover the building interior, not merely every boundary segment', () => {
  const frame = coverage([
    cell('bottom',[0,0,10,4]), cell('top',[0,6,10,10]),
    cell('left',[0,4,4,6]), cell('right',[6,4,10,6]),
  ]);
  assert.equal(geometryFullyCovered(rect(2,2,8,8), frame), false);
});

test('concave landmark does not cover a polygon bridging its notch even when all vertices are inside', () => {
  const active = coverage([], [landmark('concave',concave)]);
  assert.equal(geometryFullyCovered(rect(1,5,9,7), active), false);
  assert.equal(geometryFullyCovered(rect(0,3,3,9), active), true);
});

test('landmark holes remain uncovered, including holes wholly enclosed by a candidate building', () => {
  const active = coverage([], [landmark('courtyard',donut)]);
  assert.equal(geometryFullyCovered(rect(2,2,8,8), active), false);
  assert.equal(geometryFullyCovered(rect(4.2,4.2,5.8,5.8), active), false);
  assert.equal(geometryFullyCovered(rect(1,1,4,4), active), true);
  assert.equal(geometryFullyCovered(donut, active), true);
});

test('MultiPolygon requires every component to have coverage', () => {
  assert.equal(geometryFullyCovered({type:'MultiPolygon',coordinates:[rect(1,1,2,2).coordinates,rect(8,8,9,9).coordinates]},block),true);
  assert.equal(geometryFullyCovered({type:'MultiPolygon',coordinates:[rect(1,1,2,2).coordinates,rect(11,1,12,2).coordinates]},block),false);
});

test('missing, unsupported and empty geometries cannot suppress a building', () => {
  for (const geometry of [null, undefined, {type:'Point',coordinates:[2,2]}, {type:'Polygon',coordinates:[]}]) {
    assert.equal(geometryFullyCovered(geometry, block), false);
  }
  assert.equal(geometryFullyCovered(rect(1,1,2,2), coverage()), false);
});

test('reserved detailed footprints require their visible owner before generic cells may cover the remainder', () => {
  const reserved = [landmark('detailed',rect(4,4,6,6))];
  const local = [cell('loaded-local',[0,0,10,10])];
  const building = rect(3,3,7,7);
  assert.equal(geometryFullyCovered(building,coverage(local,[],reserved)),false,
    'a generic loaded model cannot stand in for a failed detailed model');
  assert.equal(geometryFullyCovered(building,coverage(local,[landmark('detailed',rect(4,4,6,6))],reserved)),true,
    'the visible detailed owner and its generic owner cell may jointly replace the OSM feature');
  assert.equal(geometryFullyCovered(building,coverage(local,[landmark('detailed',rect(3,3,7,7))],reserved)),true);
  assert.equal(geometryFullyCovered(rect(1,1,2,2),coverage(local,[],reserved)),true);
});

test('a slight OSM footprint overshoot is covered by generic cells only while the matching detailed owner is active', () => {
  const local=[cell('generic',[0,0,10,10])];
  const reserved=[landmark('detail',rect(4,4,6,6))];
  const building=rect(3.9,3.9,6.1,6.1);
  assert.equal(geometryFullyCovered(building,coverage(local,[landmark('detail',rect(4,4,6,6))],reserved)),true);
  assert.equal(geometryFullyCovered(building,coverage(local,[],reserved)),false);
  assert.equal(geometryFullyCovered(building,coverage(local,[landmark('different-detail',rect(4,4,6,6))],reserved)),false,
    'an unrelated active landmark cannot satisfy the reserved owner ID');
});

test('a compound OSM feature can use both active detailed and generic coverage', () => {
  const local=[cell('generic',[0,0,10,10])];
  const reserved=[landmark('detail',rect(4,4,6,6))];
  const compound={type:'MultiPolygon',coordinates:[rect(3.9,3.9,6.1,6.1).coordinates,rect(7,1,9,3).coordinates]};
  assert.equal(geometryFullyCovered(compound,coverage(local,[landmark('detail',rect(4,4,6,6))],reserved)),true);
  assert.equal(geometryFullyCovered(compound,coverage(local,[],reserved)),false);
});

test('every intersected reserved owner must be active, including two details inside one generic cell', () => {
  const local=[cell('generic',[0,0,10,10])];
  const first=landmark('first',rect(2,2,4,4)), second=landmark('second',rect(6,2,8,4));
  const reserved=[first,second], building=rect(1,1,9,5);
  assert.equal(geometryFullyCovered(building,coverage(local,[first],reserved)),false);
  assert.equal(geometryFullyCovered(building,coverage(local,[first,second],reserved)),true);
  assert.equal(geometryFullyCovered(rect(1,1,4.5,5),coverage(local,[first],reserved)),true,
    'a nonintersecting failed reserved owner must not block an unrelated building');
});

test('active reserved owners do not authorize hiding a feature outside the whole generic coverage', () => {
  const detail=landmark('detail',rect(8,4,9,6));
  assert.equal(geometryFullyCovered(rect(7,3,11,7),coverage(
    [cell('generic',[0,0,10,10])],[detail],[detail],
  )),false);
});

test('ID-less reserved regions require complete reserved geometry coverage by the active landmark union', () => {
  const local=[cell('generic',[0,0,10,10])];
  const reserved=[{geometry:rect(4,4,6,6)}];
  const left=landmark('left',rect(4,4,5,6)), right=landmark('right',rect(5,4,6,6));
  assert.equal(geometryFullyCovered(rect(4.1,4.1,4.9,5.9),coverage(local,[left],reserved)),false,
    'covering the feature itself is insufficient while part of its ID-less reservation has no active owner');
  assert.equal(geometryFullyCovered(rect(3,3,7,7),coverage(local,[left],reserved)),false);
  assert.equal(geometryFullyCovered(rect(3,3,7,7),coverage(local,[left,right],reserved)),true);
});

test('reserved intersections include edge crossings and contained footprints, not just building vertices', () => {
  const local = [cell('loaded-local',[0,0,10,10])];
  const reserved = [landmark('detailed',rect(4,4,6,6))];
  assert.equal(geometryFullyCovered(rect(1,4.5,9,5.5),coverage(local,[],reserved)),false);
  assert.equal(geometryFullyCovered(rect(1,1,9,9),coverage(local,[],reserved)),false);
  assert.equal(geometryFullyCovered(rect(2,4,4,6),coverage(local,[],reserved)),false,
    'touching a reserved footprint does not authorize generic-cell suppression');
});

test('a reserved footprint inside a building courtyard does not intersect the actual building area', () => {
  assert.equal(geometryFullyCovered(donut, coverage(
    [cell('loaded-local',[0,0,10,10])], [], [landmark('inside-courtyard',rect(4.2,4.2,5.8,5.8))],
  )), true);
});

const feature = (id, geometry=rect(1,1,2,2)) => ({type:'Feature', ...(id === undefined ? {} : {id}), properties:{}, geometry});
// MapLibre indexes state with String(id), even though API targets retain their
// original number/string type. The fake must reproduce these aliases.
const identity = target => JSON.stringify([target.source,target.sourceLayer,String(target.id)]);

function fakeMap(features=[]) {
  const listeners = new Map();
  return {
    source:{generation:1}, features, states:new Map(), writes:[], removals:[], queries:0, queryError:false, writeError:false, removeError:false,
    getSource(name) { assert.equal(name,'osm'); return this.source; },
    querySourceFeatures(source, options) {
      assert.equal(source,'osm'); assert.equal(options.sourceLayer,'building'); this.queries++;
      if (this.queryError) throw new Error('Source query temporarily failed');
      return this.features;
    },
    setFeatureState(target, value) {
      assert.equal(target.source,'osm'); assert.equal(target.sourceLayer,'building');
      assert.ok(typeof target.id === 'number' || typeof target.id === 'string');
      if (this.writeError) throw new Error('State write temporarily failed');
      this.writes.push({...target});
      this.states.set(identity(target),{...this.states.get(identity(target)),...value});
    },
    removeFeatureState(target, key) {
      if (this.removeError) throw new Error('State removal temporarily failed');
      this.removals.push({...target,key});
      const current = this.states.get(identity(target));
      if (!current) return;
      if (key === undefined) this.states.delete(identity(target));
      else { delete current[key]; if (!Object.keys(current).length) this.states.delete(identity(target)); }
    },
    getFeatureState(target) { return this.states.get(identity(target)) || {}; },
    on(name, listener) { if (!listeners.has(name)) listeners.set(name,new Set()); listeners.get(name).add(listener); return this; },
    off(name, listener) { listeners.get(name)?.delete(listener); return this; },
    emit(name, event={}) { for (const listener of [...(listeners.get(name)||[])]) listener(event); },
    triggerRepaint() {},
  };
}

const target = id => ({source:'osm',sourceLayer:'building',id});
const hidden = (map,id) => map.getFeatureState(target(id)).localModel === true;

function setup(t, {features=[],currentCoverage=block,getCoverage,useCoverageSetter=false}={}) {
  const map=fakeMap(features);
  const provider=getCoverage ? {getCoverage} : useCoverageSetter ? {} : {getCoverage:()=>currentCoverage};
  const suppression=new OSMBuildingSuppressor({map,source:'osm',...provider,onChange(){}});
  t.after(()=>suppression.destroy());
  return {map,suppression};
}

test('inactive suppressor never queries or hides fallback features', t => {
  const {map,suppression}=setup(t,{features:[feature(1)]});
  suppression.setActive(false); suppression.setCoverage(block); suppression.refresh();
  assert.equal(map.queries,0); assert.equal(map.states.size,0);
});

test('numeric and string aliases of one MapLibre ID require every fragment to be covered', t => {
  const {map,suppression}=setup(t,{features:[feature(1),feature('1',rect(11,1,12,2))]});
  suppression.setActive(true); suppression.refresh();
  assert.equal(hidden(map,1),false); assert.equal(hidden(map,'1'),false);
  map.features=[feature(1),feature('1',rect(3,3,4,4))]; suppression.refresh();
  assert.equal(hidden(map,1),true); assert.equal(hidden(map,'1'),true);
  map.features=[feature(1,rect(11,1,12,2)),feature('1')]; suppression.refresh();
  assert.equal(hidden(map,1),false); assert.equal(hidden(map,'1'),false);
});

test('different source IDs retain their original API types, including numeric zero; missing IDs are preserved', t => {
  const {map,suppression}=setup(t,{features:[feature(1),feature('two'),feature(0),feature(undefined),feature(null)]});
  suppression.setActive(true); suppression.refresh();
  assert.equal(hidden(map,1),true); assert.equal(hidden(map,'two'),true); assert.equal(hidden(map,0),true);
  assert.ok(map.writes.some(entry=>entry.id===1 && typeof entry.id==='number'));
  assert.ok(map.writes.some(entry=>entry.id==='two' && typeof entry.id==='string'));
  assert.ok(map.writes.every(entry=>entry.id!==null && entry.id!==undefined));
  map.features=[feature(1,rect(11,1,12,2)),feature('two')]; suppression.refresh();
  assert.equal(hidden(map,1),false); assert.equal(hidden(map,'two'),true);
  assert.ok(map.removals.some(entry=>entry.id===1 && typeof entry.id==='number'));
});

test('all loaded fragments sharing an ID must be covered before that ID is hidden', t => {
  const {map,suppression}=setup(t,{features:[feature('same'),feature('same',rect(9,2,11,4))]});
  suppression.setActive(true); suppression.refresh(); assert.equal(hidden(map,'same'),false);
  map.features=[feature('same'),feature('same',rect(3,3,4,4))]; suppression.refresh();
  assert.equal(hidden(map,'same'),true);
  map.features.push(feature('same',null)); suppression.refresh(); assert.equal(hidden(map,'same'),false);
});

test('dynamic successful-visible coverage controls suppression, eviction restores OSM', t => {
  let current=coverage();
  const {map,suppression}=setup(t,{features:[feature(1)],getCoverage:()=>current});
  suppression.setActive(true); suppression.refresh(); assert.equal(hidden(map,1),false);
  current=block; suppression.refresh(); assert.equal(hidden(map,1),true);
  current=coverage(); suppression.refresh(); assert.equal(hidden(map,1),false);
});

test('setCoverage removes stale state when a different local model becomes visible', t => {
  const {map,suppression}=setup(t,{features:[feature(1),feature(2,rect(21,1,22,2))],useCoverageSetter:true});
  suppression.setActive(true); suppression.setCoverage(block); suppression.refresh(); assert.equal(hidden(map,1),true);
  suppression.setCoverage(coverage([cell('new-local',[20,0,30,10])])); suppression.refresh();
  assert.equal(hidden(map,1),false); assert.equal(hidden(map,2),true);
});

test('detailed-model failure preserves its reserved OSM building even beside loaded generic cells', t => {
  let current=coverage([cell('generic',[0,0,10,10])],[],[landmark('detail',rect(4,4,6,6))]);
  const {map,suppression}=setup(t,{features:[feature('detail',rect(3.9,3.9,6.1,6.1)),feature('ordinary')],getCoverage:()=>current});
  suppression.setActive(true); suppression.refresh();
  assert.equal(hidden(map,'detail'),false); assert.equal(hidden(map,'ordinary'),true);
  current={...current,landmarks:[landmark('detail',rect(4,4,6,6))]}; suppression.refresh();
  assert.equal(hidden(map,'detail'),true);
  current={...current,landmarks:[]}; suppression.refresh(); assert.equal(hidden(map,'detail'),false);
});

test('query failure restores previously hidden OSM and a later successful refresh recovers', t => {
  const {map,suppression}=setup(t,{features:[feature(1)]});
  suppression.setActive(true); suppression.refresh(); assert.equal(hidden(map,1),true);
  map.queryError=true; assert.doesNotThrow(()=>suppression.refresh()); assert.equal(hidden(map,1),false);
  map.queryError=false; suppression.refresh(); assert.equal(hidden(map,1),true);
});

test('state-write failure is retried on a later refresh, not cached as success', t => {
  const {map,suppression}=setup(t,{features:[feature(1)]}); map.writeError=true;
  assert.doesNotThrow(()=>{suppression.setActive(true);suppression.refresh();}); assert.equal(hidden(map,1),false);
  map.writeError=false; suppression.refresh(); assert.equal(hidden(map,1),true);
});

test('failed state removal stays tracked and retries after coverage is lost', t => {
  let current=block;
  const {map,suppression}=setup(t,{features:[feature(1)],getCoverage:()=>current});
  suppression.setActive(true); suppression.refresh(); assert.equal(hidden(map,1),true);
  map.removeError=true; current=coverage();
  assert.doesNotThrow(()=>suppression.refresh());
  assert.equal(hidden(map,1),true,'failed removal cannot be reported as restored visibility');
  assert.equal(suppression.getState().pendingRemovals,1,'the failed removal must remain available for retry');
  map.removeError=false; suppression.refresh();
  assert.equal(hidden(map,1),false); assert.equal(suppression.getState().pendingRemovals,0);
});

test('replacement source object receives current suppression despite unchanged features and coverage', t => {
  const {map,suppression}=setup(t,{features:[feature(1)]});
  suppression.setActive(true); suppression.refresh(); assert.equal(hidden(map,1),true);
  const previousWrites=map.writes.length;
  map.source={generation:2}; map.states.clear(); suppression.refresh();
  assert.equal(hidden(map,1),true); assert.ok(map.writes.length>previousWrites);
});

test('source absence does not prevent reapplying current coverage after the source returns', t => {
  const {map,suppression}=setup(t,{features:[feature(1)]});
  map.source=null; suppression.setActive(true); assert.doesNotThrow(()=>suppression.refresh());
  assert.equal(hidden(map,1),false);
  map.source={generation:2}; suppression.refresh(); assert.equal(hidden(map,1),true);
  assert.equal(typeof suppression.getState(),'object');
});

test('clear, deactivation and destroy restore owned state without removing unrelated feature-state', t => {
  const {map,suppression}=setup(t,{features:[feature(1)]});
  map.states.set(identity(target(1)),{selected:true});
  suppression.setActive(true); suppression.refresh(); assert.equal(hidden(map,1),true);
  suppression.clear(); assert.equal(hidden(map,1),false); assert.equal(map.getFeatureState(target(1)).selected,true);
  suppression.refresh(); assert.equal(hidden(map,1),true);
  suppression.setActive(false); assert.equal(hidden(map,1),false);
  const queries=map.queries; suppression.refresh(); assert.equal(map.queries,queries);
  suppression.setActive(true); suppression.refresh(); assert.equal(hidden(map,1),true);
  suppression.destroy(); assert.equal(hidden(map,1),false); assert.equal(map.getFeatureState(target(1)).selected,true);
  const stoppedQueries=map.queries; suppression.refresh(); map.emit('sourcedata',{sourceId:'osm'});
  assert.equal(map.queries,stoppedQueries);
});
