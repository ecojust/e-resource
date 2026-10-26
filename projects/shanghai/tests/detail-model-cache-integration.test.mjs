import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import * as cache from '../src/detail-model-cache.js';

// Exercise the actual edited scheduler/load bodies with lightweight geographic
// and renderer adapters. No WebGL, network or copied reimplementation of logic.
const source=await readFile(new URL('../src/map-scene.js',import.meta.url),'utf8');
const section=(from,to)=>source.slice(source.indexOf(from),source.indexOf(to,source.indexOf(from)));
const loadBody=section('  async function loadLandmark(','  function updateStreetBasemap(');
const updateBody=section('  function updateLandmarkVisibility(','  function updateBuildingExclusions(');
assert.ok(loadBody.includes('retainDetailResult') && updateBody.includes('selectHiddenDetailEvictions'));

function group(name,{photo=false}={}) {
  const mesh={isMesh:true,geometry:{attributes:{position:{array:new Float32Array(9)}},computeBoundingSphere(){}},material:{}};
  if(photo)mesh.material.map={isTexture:true,userData:{},generateMipmaps:true,source:{data:{width:6000,height:4000}}};
  return {name,visible:true,position:{copy(){}},scale:{multiplyScalar(){}},rotation:{},traverse(fn){fn(this);fn(mesh);}};
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));
function harness({maxCount=2,maxBytes=32*cache.MIB}={}) {
  const events=[], requests=[], records=new Map(), current={lng:0,lat:0}, variant={value:'full'};
  const scene={add(object){events.push({type:'add',object});}};
  const disposeModel=object=>{assert.equal(object.disposed,undefined,'object disposed twice');object.disposed=true;events.push({type:'dispose',object});};
  const boundary=new Map();
  const env={...cache,events,current,landmarkRecords:records,scene,disposeModel,
    loader:{loadAsync(url){return new Promise((resolve,reject)=>requests.push({url,resolve,reject}));}},
    detailCacheLimits:{maxCount,maxBytes},detailCacheStats:{evicted:0,discardedLate:0},
    map:{getCenter(){return current;},getZoom(){return 20;},triggerRepaint(){}},walker:{group:{visible:true}},
    distanceMetres(a,b){return Math.abs(a.lng-b.lng);},desiredVariant(){return variant.value;},
    geographicPosition(){return {};},maplibregl:{MercatorCoordinate:{fromLngLat(){return {meterInMercatorCoordinateUnits(){return 1;}};}}},metreScale:1,DEG:Math.PI/180,
    THREE:{},correctPhotographicTexture(){},surfaces:{apply(){}},lighting:{configureModel(){},invalidate(){}},
    reportLandmarks(){},onLoadError(error){events.push({type:'error',error});},
    landmarkBoundaries:boundary,landmarkSuppression:{setOwner(id,ids){events.push({type:'owner',id,ids});return Promise.resolve();}},
    updateBuildingExclusions(){events.push({type:'coverage',visible:[...records.values()].filter(r=>r.object?.visible).map(r=>r.id)});},
    updateStreetBasemap(){},updateLocalModels(){},
  };
  const names=Object.keys(env);
  const factory=new Function(...names,`let destroyed=false;\n${loadBody}\n${updateBody}\nreturn {update:updateLandmarkVisibility,load:loadLandmark,shutdown(){destroyed=true;}};`);
  const methods=factory(...names.map(n=>env[n]));
  return {...env,...methods,events,requests,records,variant,
    add(id='one',extra={}){const r={id,name:id,lng:0,lat:0,maxDistance:100,status:'idle',url:id+'-full',lodUrl:id+'-lod',...extra};records.set(id,r);boundary.set(id,{building_ids:[id+'-gers'],building_part_ids:[]});return r;},
    move(lng){current.lng=lng;methods.update();},
    resolve(index,object){requests[index].resolve({scene:object});return settle();},
  };
}

test('far teleport restores exact ownership/OSM coverage before disposing a large hidden photograph; return reloads once',async()=>{
  const h=harness(),r=h.add();h.update();assert.equal(h.requests.length,1);
  const first=group('first',{photo:true});await h.resolve(0,first);
  assert.equal(r.object,first);assert.equal(first.visible,true);assert.ok(r.resourceEstimate.textureBytes>100*cache.MIB);
  h.events.length=0;h.move(10000);
  assert.equal(r.object,null);assert.equal(r.status,'idle');assert.equal(h.detailCacheStats.evicted,1);
  const restoration=h.events.findIndex(e=>e.type==='owner' && e.ids===null);
  const coverage=h.events.findIndex(e=>e.type==='coverage' && e.visible.length===0);
  const disposal=h.events.findIndex(e=>e.type==='dispose');
  assert.ok(restoration>=0 && restoration<disposal);assert.ok(coverage>=0 && coverage<disposal);
  h.move(0);h.update();h.update();assert.equal(h.requests.length,2,'one new fetch despite repeated updates');
  await h.resolve(1,group('second',{photo:true}));assert.equal(r.status,'loaded');assert.equal(r.object.visible,true);
});

test('large visible photograph is retained even when it exceeds the hidden budget',async()=>{
  const h=harness({maxCount:0,maxBytes:0}),r=h.add();h.update();await h.resolve(0,group('visible',{photo:true}));
  h.update();assert.equal(r.object.visible,true);assert.equal(h.detailCacheStats.evicted,0);
});

test('small hidden cached model returns without fetching and fringe prevents edge churn',async()=>{
  const h=harness(),r=h.add();h.update();await h.resolve(0,group('small'));
  h.move(200);assert.equal(r.object.visible,true,'retained inside 300m exit fringe');
  h.move(401);assert.equal(r.object.visible,false);assert.equal(r.status,'loaded');
  h.move(200);assert.equal(r.object.visible,false,'hidden entries must cross enter threshold');
  h.move(0);assert.equal(r.object.visible,true);assert.equal(h.requests.length,1);
});

test('late decode after leaving is disposed without ever acquiring source ownership or immediately reloading',async()=>{
  const h=harness(),r=h.add();h.update();h.move(10000);const late=group('late',{photo:true});await h.resolve(0,late);
  assert.equal(late.disposed,true);assert.equal(r.object,undefined);assert.equal(r.status,'idle');assert.equal(r.loadingModel,false);
  assert.equal(h.detailCacheStats.discardedLate,1);assert.equal(h.requests.length,1);
  assert.equal(h.events.some(e=>e.type==='owner' && e.ids),false);assert.equal(h.events.some(e=>e.type==='add'),false);
  h.move(0);assert.equal(h.requests.length,2);
});

test('late rejected request outside range does not poison a future retry',async()=>{
  const h=harness(),r=h.add();h.update();h.move(10000);h.requests[0].reject(new Error('connection ended'));await settle();
  assert.equal(r.status,'idle');assert.equal(r.failedVariants,undefined);assert.equal(h.events.some(e=>e.type==='error'),false);
  h.move(0);assert.equal(h.requests.length,2);
});

test('evicting an old hidden LOD during its upgrade neither duplicates loads nor keeps the late full model',async()=>{
  const h=harness({maxCount:0,maxBytes:0}),r=h.add();h.variant.value='distant';h.update();const old=group('old');await h.resolve(0,old);
  h.variant.value='full';h.update();assert.equal(h.requests.length,2);assert.equal(r.loadingModel,true);
  h.move(10000);assert.equal(old.disposed,true);assert.equal(r.object,null);assert.equal(r.loadingModel,true);
  const late=group('upgrade',{photo:true});await h.resolve(1,late);assert.equal(late.disposed,true);assert.equal(r.status,'idle');assert.equal(h.requests.length,2);
});

test('failed full upgrade keeps valid visible distant object and its source ownership',async()=>{
  const h=harness(),r=h.add();h.variant.value='distant';h.update();const old=group('distant');await h.resolve(0,old);
  h.events.length=0;h.variant.value='full';h.update();h.requests[1].reject(new Error('404'));await settle();
  assert.equal(r.object,old);assert.equal(old.visible,true);assert.equal(old.disposed,undefined);
  assert.equal(r.status,'loaded');assert.equal(h.events.some(e=>e.type==='owner' && e.ids===null),false);
});

test('manual refresh cannot force distant loads; shutdown rejects decoded results',async()=>{
  const h=harness(),r=h.add('far',{lng:10000});h.update(true);assert.equal(h.requests.length,0);
  r.lng=0;h.update();h.shutdown();const late=group('destroyed',{photo:true});await h.resolve(0,late);
  assert.equal(late.disposed,true);assert.equal(h.events.some(e=>e.type==='add'),false);
});

test('visiting sixteen separated locations never accumulates hidden full photographs',async()=>{
  const h=harness();for(let i=0;i<16;i++)h.add(`district-${i}`,{lng:i*10000});
  for(let i=0;i<16;i++){
    h.move(i*10000);assert.equal(h.requests.length,i+1);
    await h.resolve(i,group(`photo-${i}`,{photo:true}));
    const state=cache.detailCacheState(h.records.values(),h.detailCacheLimits,h.detailCacheStats);
    assert.equal(state.resident,1);assert.equal(state.visible,1);assert.equal(state.hidden,0);
    assert.ok(state.hiddenEstimatedBytes<=state.maxHiddenEstimatedBytes);
  }
  h.move(1000000);const state=cache.detailCacheState(h.records.values(),h.detailCacheLimits,h.detailCacheStats);
  assert.equal(state.resident,0);assert.equal(state.evicted,16);assert.equal(h.requests.length,16);
});
