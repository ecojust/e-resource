import assert from 'node:assert/strict';
import test from 'node:test';
import {OSMResidualLayer} from '../src/osm-residual-layer.js';

const tick=()=>new Promise(resolve=>setImmediate(resolve));
const clone=value=>JSON.parse(JSON.stringify(value));
const SOURCE='shanghai-osm-building-residuals';
const LAYER='shanghai-osm-building-residuals-3d';
const collection=(features=[])=>({type:'FeatureCollection',features});
const building=(id=7)=>({type:'Feature',id,originalSourceId:23809960,
  properties:{render_height:26,render_min_height:0,nested:{preserve:'yes'}},
  geometry:{type:'Polygon',coordinates:[[[121,31],[121.01,31],[121.01,31.01],[121,31.01],[121,31]]]}});

class Events {
  constructor(){this.listeners=new Map();}
  on(type,listener){if(!this.listeners.has(type))this.listeners.set(type,new Set());this.listeners.get(type).add(listener);return this;}
  off(type,listener){this.listeners.get(type)?.delete(listener);return this;}
  once(type,listener){if(!listener)return new Promise(resolve=>this.once(type,resolve));const wrapper=event=>{this.off(type,wrapper);listener(event);};return this.on(type,wrapper);}
  emit(type,event={}){for(const listener of [...(this.listeners.get(type)||[])])listener({type,...event});}
}

class FakeMap extends Events {
  constructor(){
    super();this.sources=new Map();this.layers=new Map();this.writes=[];this.operations=[];this.renderCount=0;
    this.template={id:'osm-template',type:'fill-extrusion',source:'original-osm','source-layer':'building',
      filter:['==',['get','kept'],true],minzoom:13,maxzoom:24,
      layout:{visibility:'none'},paint:{'fill-extrusion-height':['get','render_height'],
        'fill-extrusion-base':['get','render_min_height'],'fill-extrusion-color':'#d3d8d4'}};
    this.layers.set(this.template.id,this.template);
  }
  getSource(id){return this.sources.get(id);}
  getLayer(id){return this.layers.get(id);}
  getStyle(){return {layers:[...this.layers.values()]};}
  isSourceLoaded(id){return this.sources.get(id)?.loaded()===true;}
  addSource(id,options){
    assert.equal(this.sources.has(id),false);this.operations.push(['addSource',id]);
    const source=new Events();source.ready=false;source.options=options;source.loaded=()=>source.ready;
    source.setData=(data,waitForCompletion)=>{
      source.ready=false;source.data=data;
      let resolve;const promise=new Promise(done=>{resolve=done;});
      this.writes.push({id,source,data,resolve,waitForCompletion,render:this.renderCount});
      this.operations.push(['setData',id,this.writes.length]);return waitForCompletion?promise:source;
    };
    this.sources.set(id,source);
  }
  addLayer(layer,beforeId){assert.equal(this.layers.has(layer.id),false);this.layers.set(layer.id,layer);this.operations.push(['addLayer',layer.id,beforeId]);}
  removeLayer(id){this.operations.push(['removeLayer',id]);this.layers.delete(id);}
  removeSource(id){this.operations.push(['removeSource',id]);this.sources.delete(id);}
  triggerRepaint(){this.operations.push(['repaint']);}
  render(){this.renderCount++;this.operations.push(['render',this.renderCount]);this.emit('render');}
  sourceData(sourceId=SOURCE,sourceDataType='content'){
    const event={sourceId,dataType:'source',sourceDataType,isSourceLoaded:this.isSourceLoaded(sourceId)};
    this.getSource(sourceId)?.emit('data',event);this.emit('sourcedata',event);
  }
  completeInitial(){this.getSource(SOURCE).ready=true;this.sourceData();}
  completeWrite(index,{content=true,loaded=true}={}){
    const write=this.writes[index];write.source.ready=loaded;
    if(content)this.sourceData(write.id);write.resolve();
  }
  sourceError(sourceId=SOURCE){const error=new Error('Residual source failed');const event={sourceId,error};this.getSource(sourceId)?.emit('error',event);this.emit('error',event);}
  setFeatureState(){assert.fail('residual layer must not write original feature state');}
  removeFeatureState(){assert.fail('residual layer must not remove original feature state');}
}

function tracked(promise){const status={settled:false,error:null};status.promise=promise.then(value=>{status.settled=true;return value;},error=>{status.settled=true;status.error=error;throw error;});status.promise.catch(()=>{});return status;}
async function until(predicate,label='condition',renderMap){
  for(let attempt=0;attempt<60;attempt++){if(predicate())return;if(renderMap)renderMap.render();await tick();}
  assert.fail(`Did not reach ${label}`);
}
function setup(t,options={}){
  const map=new FakeMap();
  const layer=new OSMResidualLayer({map,templateLayerId:'osm-template',beforeId:'labels',timeoutMs:500,...options});
  t.after(()=>layer.destroy());return {map,layer};
}
async function startFirst(map,layer,data=collection([building()])){
  const work=tracked(layer.replace(data));
  await until(()=>map.getSource(SOURCE),'lazy source creation',map);
  return work;
}
async function initialWrite(map){map.completeInitial();await until(()=>map.writes.length===1,'first data write',map);}
async function finish(map,work,index=map.writes.length-1){map.completeWrite(index);await tick();map.render();await work.promise;}

test('lazy residual source clones paint and visible layout without source-layer/filter, preserving exact data',async t=>{
  const {map,layer}=setup(t);assert.equal(map.getSource(SOURCE),undefined);
  const features=[building(7),building('original'),building(7),building()];delete features[3].id;
  const input=collection(features),snapshot=clone(input);const work=await startFirst(map,layer,input);
  assert.equal(map.writes.length,0,'initial empty source must finish loading first');
  assert.deepEqual(map.getSource(SOURCE).options.data,collection());
  const residual=map.getLayer(LAYER);assert.equal(residual.source,SOURCE);assert.equal(residual.type,'fill-extrusion');
  assert.equal(residual['source-layer'],undefined);assert.equal(residual.filter,undefined);
  assert.deepEqual(residual.paint,map.template.paint);assert.notEqual(residual.paint,map.template.paint);
  assert.equal(residual.layout.visibility,'visible');assert.equal(map.template.layout.visibility,'none');
  assert.ok(map.operations.some(op=>op[0]==='addLayer'&&op[2]==='labels'));
  await initialWrite(map);
  const sent=map.writes[0].data;
  assert.deepEqual(input,snapshot);assert.equal(sent.features[0].id,7);assert.equal(sent.features[1].id,'original');
  assert.equal(new Set(sent.features.map(f=>String(f.id))).size,features.length);
  assert.ok(sent.features.every(f=>f.id!==undefined&&f.id!==null));
  for(let i=0;i<features.length;i++){
    assert.deepEqual(sent.features[i].properties,snapshot.features[i].properties);
    assert.deepEqual(sent.features[i].geometry,snapshot.features[i].geometry);
    assert.equal(sent.features[i].originalSourceId,23809960);
  }
  input.features[0].properties.nested.preserve='mutated';input.features[0].geometry.coordinates[0][0][0]=0;
  assert.equal(sent.features[0].properties.nested.preserve,'yes');assert.equal(sent.features[0].geometry.coordinates[0][0][0],121);
  await finish(map,work);assert.equal(typeof layer.getState(),'object');
});

test('worker completion alone is insufficient: require scoped content, loaded source and a later render',async t=>{
  const {map,layer}=setup(t);const work=await startFirst(map,layer);await initialWrite(map);
  map.completeWrite(0,{content:false,loaded:true});await tick();map.render();await tick();assert.equal(work.settled,false);
  map.emit('sourcedata',{sourceId:'unrelated',sourceDataType:'content',isSourceLoaded:true});map.render();await tick();assert.equal(work.settled,false);
  map.getSource(SOURCE).ready=false;map.sourceData();map.render();await tick();assert.equal(work.settled,false);
  map.getSource(SOURCE).ready=true;map.sourceData();await tick();assert.equal(work.settled,false,'content/loaded is not a rendered frame');
  map.render();await work.promise;
});

test('each replacement and clear waits a restoration render before changing existing residual data',async t=>{
  const {map,layer}=setup(t);const first=await startFirst(map,layer);await initialWrite(map);await finish(map,first);
  const count=map.writes.length;const replacement=tracked(layer.replace(collection([building('next')])));
  await tick();assert.equal(map.writes.length,count);map.render();await until(()=>map.writes.length===count+1,'second setData');
  await finish(map,replacement);
  const empty=tracked(layer.clear());await tick();assert.equal(map.writes.length,count+1);
  map.render();await until(()=>map.writes.length===count+2,'clear setData');
  assert.deepEqual(map.writes.at(-1).data,collection());await finish(map,empty);
});

test('concurrent replacements are serialized through rendered completion',async t=>{
  const {map,layer}=setup(t);const first=await startFirst(map,layer);await initialWrite(map);
  const second=tracked(layer.replace(collection([building('queued')])));await tick();map.render();await tick();
  assert.equal(map.writes.length,1);assert.equal(second.settled,false);
  await finish(map,first);await tick();assert.equal(map.writes.length,1,'queued replacement still needs its own restoration frame');
  map.render();await until(()=>map.writes.length===2,'serialized second data');await finish(map,second);
});

test('a residual-source error rejects the update while unrelated source errors do not',async t=>{
  const {map,layer}=setup(t);const work=await startFirst(map,layer);await initialWrite(map);
  map.sourceError('unrelated');await tick();assert.equal(work.settled,false);
  map.sourceError();await assert.rejects(work.promise,/failed|error/i);
});

test('timeout rejects rather than treating unresolved source readiness as success',async t=>{
  const {map,layer}=setup(t,{timeoutMs:35});
  const work=tracked(layer.replace(collection([building()])));
  await assert.rejects(work.promise,/time|timeout/i);
});

test('source identity replacement cancels the in-flight transaction',async t=>{
  const {map,layer}=setup(t);const work=await startFirst(map,layer);await initialWrite(map);
  const replacement=new Events();replacement.ready=true;replacement.loaded=()=>true;map.sources.set(SOURCE,replacement);
  map.sourceData();map.render();await assert.rejects(work.promise,/source|replac|identity/i);
});

test('destroy rejects active and queued waits, removes only owned layer/source, and stops future work',async t=>{
  const {map,layer}=setup(t);const first=await startFirst(map,layer);await initialWrite(map);
  const queued=tracked(layer.replace(collection([building('queued')])));layer.destroy();
  await assert.rejects(first.promise,/destroy|cancel|abort/i);await assert.rejects(queued.promise,/destroy|cancel|abort/i);
  assert.equal(map.getSource(SOURCE),undefined);assert.equal(map.getLayer(LAYER),undefined);assert.ok(map.getLayer('osm-template'));
  const operations=map.operations.length;map.render();map.emit('sourcedata',{sourceId:SOURCE,sourceDataType:'content',isSourceLoaded:true});await tick();
  assert.equal(map.writes.length,1);assert.ok(map.operations.length>=operations);
  await assert.rejects(layer.replace(collection()),/destroy|cancel|abort/i);
  layer.destroy();
});

for(const scenario of [
  {name:'removed layer',mutate:map=>map.layers.delete(LAYER),event:'styledata'},
  {name:'hidden layer',mutate:map=>{map.getLayer(LAYER).layout.visibility='none';},event:'styledata'},
  {name:'replaced layer object',mutate:map=>map.layers.set(LAYER,{...map.getLayer(LAYER)}),event:'styledata'},
  {name:'layer targeting a different source',mutate:map=>{map.getLayer(LAYER).source='unrelated';},event:'styledata'},
  {name:'missing source',mutate:map=>map.sources.delete(SOURCE),event:'sourcedata'},
]) {
  test(`ready residual invalidates synchronously and only once after ${scenario.name}`,async t=>{
    let invalidated=0;
    const {map,layer}=setup(t,{onInvalidated(){invalidated++;}});
    const work=await startFirst(map,layer);await initialWrite(map);await finish(map,work);
    assert.equal(layer.isReady(),true);
    scenario.mutate(map);
    map.emit(scenario.event,{sourceId:SOURCE,sourceDataType:'content',isSourceLoaded:false});
    assert.equal(invalidated,1,'ownership loss must notify the caller before it can hide originals');
    assert.equal(layer.isReady(),false);
    map.emit('styledata');map.emit('sourcedata',{sourceId:SOURCE,sourceDataType:'content'});map.render();
    assert.equal(invalidated,1,'an already-invalid source must not repeatedly notify');
  });
}

test('setInvalidationHandler replaces the callback and destroy removes persistent watches',async t=>{
  let oldCalls=0,newCalls=0;
  const {map,layer}=setup(t,{onInvalidated(){oldCalls++;}});
  const work=await startFirst(map,layer);await initialWrite(map);await finish(map,work);
  layer.setInvalidationHandler(()=>{newCalls++;});
  map.getLayer(LAYER).layout.visibility='none';map.emit('styledata');
  assert.equal(oldCalls,0);assert.equal(newCalls,1);assert.equal(layer.isReady(),false);
  const source=map.getSource(SOURCE);
  layer.destroy();map.emit('styledata');map.emit('sourcedata',{sourceId:SOURCE});map.sourceError();
  assert.equal(oldCalls,0);assert.equal(newCalls,1);
  assert.ok([...map.listeners.values()].every(listeners=>listeners.size===0));
  assert.ok([...source.listeners.values()].every(listeners=>listeners.size===0));
});

test('persistent source errors invalidate only the residual source after successful readiness',async t=>{
  let invalidated=0;
  const {map,layer}=setup(t,{onInvalidated(){invalidated++;}});
  const work=await startFirst(map,layer);await initialWrite(map);await finish(map,work);
  map.sourceError('unrelated');assert.equal(layer.isReady(),true);assert.equal(invalidated,0);
  map.sourceError();assert.equal(invalidated,1);assert.equal(layer.isReady(),false);
  map.sourceError();assert.equal(invalidated,1);
});

test('a layer hidden during a replacement cannot become render-ready',async t=>{
  const {map,layer}=setup(t);const work=await startFirst(map,layer);await initialWrite(map);
  map.getLayer(LAYER).layout.visibility='none';map.emit('styledata');
  map.completeWrite(0);await tick();map.render();
  await assert.rejects(work.promise,/hidden|visible|layer/i);assert.equal(layer.isReady(),false);
});
