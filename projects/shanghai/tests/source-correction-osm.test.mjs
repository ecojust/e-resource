import test from 'node:test';
import assert from 'node:assert/strict';
import {SourceGeometryCorrectionState} from '../src/source-geometry-correction.js';
import {planOSMBuildingReplacement,OSMBuildingSuppressor} from '../src/osm-building-suppression.js';
import {fixture,ID,clone,makeRecord,makeBoundary,loadVerified,retainedGeometrySet,tick} from './source-correction-fixtures.mjs';

const context={source:fixture.osm.source,sourceLayer:fixture.osm.sourceLayer};
async function setup({loaded=true}={}) {
  const f=makeRecord();if(loaded)await loadVerified(f);
  const records=new Map([[ID,f.record]]),boundaries=new Map([[ID,makeBoundary(f.record)]]);
  const state=new SourceGeometryCorrectionState({getRecords:()=>records,getBoundaries:()=>boundaries,getMode:()=> 'osm',getScene:()=>f.sceneRoot,onChange(){}});state.sync();
  const coverage=()=>({cells:[],landmarks:[],reserved:[],sourceGeometryCorrections:state.getOSMCorrections(context.source,context.sourceLayer)});
  return {...f,records,boundaries,state,coverage};
}
const expected=()=>fixture.osm.geometry.coordinates.slice(1).map(p=>JSON.stringify(p)).sort();

test('real OSM aggregate explicit correction retains exact five components even under all-covering generic cells',async()=>{
  const h=await setup();const cov={...h.coverage(),cells:[{id:'synthetic-visible-city',bounds:[120,30,122,32]}]};
  const plan=planOSMBuildingReplacement([fixture.osm],cov,context);
  assert.deepEqual(plan.hideIDs,[5607522290]);assert.equal(plan.removedComponents,1);assert.equal(plan.residualComponents,5);
  assert.deepEqual(retainedGeometrySet(plan.residualData.features),expected());
  for(const f of plan.residualData.features){assert.deepEqual(f.properties,fixture.osm.properties);assert.equal(f.originalSourceId,5607522290);}
});

test('inactive verified target cannot fall through to broad generic coverage, but ordinary unrelated feature retains baseline behavior',async()=>{
  const h=await setup({loaded:false});const cov={...h.coverage(),cells:[{id:'wide-generic',bounds:[120,30,122,32]}]};
  const ordinary={...clone(fixture.osm),id:123456};
  const plan=planOSMBuildingReplacement([fixture.osm,ordinary],cov,context);
  assert.deepEqual(plan.hideIDs,[123456]);assert.equal(plan.residualComponents,0,'target stays original; no invented residual');
  h.records.delete(ID);h.state.sync();
  const absent=h.coverage();assert.equal(absent.sourceGeometryCorrections.length,1);assert.equal(absent.sourceGeometryCorrections[0].active,false);
  assert.deepEqual(planOSMBuildingReplacement([fixture.osm],{...cov,...absent},context).hideIDs,[],'boundary keeps exact inactive guard when record absent');
  h.records.set(ID,h.record);h.state.sync();
  const changed=clone(fixture.osm);changed.geometry.coordinates[0][0][1][0]+=1e-5;
  h.record.object={visible:true,parent:{},userData:{}};h.record.status='loaded';h.record.activeVariant='full';h.state.sync();
  assert.deepEqual(planOSMBuildingReplacement([changed],{...cov,...h.coverage()},context).hideIDs,[]);
});

test('identity/source-context mismatch cannot authorize explicit removal',async()=>{
  const h=await setup();
  for(const f of [{...fixture.osm,id:1074070665},{...fixture.osm,id:String(fixture.osm.id)}])
    assert.deepEqual(planOSMBuildingReplacement([f],h.coverage(),context).hideIDs,[]);
  assert.deepEqual(planOSMBuildingReplacement([fixture.osm],h.coverage(),{source:'wrong',sourceLayer:'building'}).hideIDs,[]);
  assert.deepEqual(planOSMBuildingReplacement([fixture.osm],h.coverage(),{source:'openmaptiles',sourceLayer:'building_part'}).hideIDs,[]);
});

function fakeMap() {
  const states=new Map();return {source:{},states,features:[clone(fixture.osm)],removeError:false,
    getSource(name){return name===context.source?this.source:null;},querySourceFeatures(){return this.features;},
    getFeatureState(t){return states.get(`${typeof t.id}:${t.id}`)||{};},
    setFeatureState(t,v){states.set(`${typeof t.id}:${t.id}`,v);},
    removeFeatureState(t){if(this.removeError)throw Error('synthetic restore failure');states.delete(`${typeof t.id}:${t.id}`);}};
}
function residual() {
  return {calls:[],current:null,ready:true,destroyed:false,
    replace(data){return new Promise((resolve,reject)=>this.calls.push({data,resolve:()=>{this.current=data;resolve();},reject}));},
    isReady(){return this.ready;},async clear(){this.current={type:'FeatureCollection',features:[]};},
    destroy(){this.destroyed=true;},getState(){return {testOnly:true};}};
}
async function controllerSetup(t) {
  const h=await setup(),map=fakeMap(),layer=residual();
  const controller=new OSMBuildingSuppressor({map,source:context.source,sourceLayer:context.sourceLayer,residualLayer:layer,getCoverage:h.coverage});
  t.after(()=>controller.destroy({mapWillBeRemoved:true}));controller.setActive(true);
  return {...h,map,layer,controller};
}

test('actual controller hides aggregate only after five-component residual ACK, and restores before residual drop',{timeout:5000},async t=>{
  const h=await controllerSetup(t);const first=h.controller.refresh();assert.equal(h.map.states.size,0);
  assert.equal(h.layer.calls.length,1);assert.deepEqual(retainedGeometrySet(h.layer.calls[0].data.features),expected());
  h.layer.calls[0].resolve();await first;assert.equal(h.map.states.size,1);
  h.record.object.visible=false;h.state.sync();const second=h.controller.refresh();
  assert.equal(h.map.states.size,0,'original must restore synchronously');assert.equal(h.layer.current.features.length,5);
  assert.equal(h.layer.calls[1].data.features.length,0);h.layer.calls[1].resolve();await second;assert.equal(h.layer.current.features.length,0);
});

test('late residual ACK after mode/visibility exit cannot re-hide six-component source',{timeout:5000},async t=>{
  const h=await controllerSetup(t);const first=h.controller.refresh();
  h.record.object.visible=false;h.state.sync();h.controller.setActive(false);h.layer.calls[0].resolve();await tick();
  assert.equal(h.map.states.size,0);assert.equal(h.layer.calls[1].data.features.length,0);h.layer.calls[1].resolve();await first;
  assert.equal(h.map.states.size,0);assert.equal(h.layer.current.features.length,0);
});

test('failed residual upload preserves original aggregate; no residual-free partial masking',{timeout:5000},async t=>{
  const h=await controllerSetup(t);const first=h.controller.refresh();h.layer.calls[0].reject(Error('syntheticGPU upload failure'));await first;
  assert.equal(h.map.states.size,0);assert.equal(h.controller.getState().residualReady,false);
  assert.ok(h.controller.getState().residualErrors>0);
  const noRenderer=new OSMBuildingSuppressor({map:fakeMap(),source:context.source,sourceLayer:context.sourceLayer,getCoverage:h.coverage});
  t.after(()=>noRenderer.destroy());noRenderer.setActive(true);noRenderer.refresh();assert.equal(noRenderer.getState().coveredIDs,0);
});

test('source-fragment invalidation restores original and prevents old ACK from authorizing stale geometry',{timeout:5000},async t=>{
  const h=await controllerSetup(t);const first=h.controller.refresh();h.controller.sourceChanged();h.layer.calls[0].resolve();await first;
  assert.equal(h.map.states.size,0);const retry=h.controller.refresh();h.layer.calls[1].resolve();await retry;assert.equal(h.map.states.size,1);
  h.map.features[0].geometry.coordinates[0][0][1][0]+=1e-5;h.controller.sourceChanged();assert.equal(h.map.states.size,0);
  const changed=h.controller.refresh();assert.equal(h.layer.calls[2].data.features.length,0);h.layer.calls[2].resolve();await changed;assert.equal(h.map.states.size,0);
});
