import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {SourceGeometryCorrectionState} from '../src/source-geometry-correction.js';
import {fixture,ID,clone,makeRecord,makeBoundary,loadVerified,rect} from './source-correction-fixtures.mjs';

// Extract actual production navigation, desired-variant selection, geographic
// helpers and collision cache. No duplicate wait/fallback implementation and no
// WebGL/browser acceptance claim. Fake sleep advances scheduled load outcomes.
const source=fs.readFileSync(new URL('../src/map-scene.js',import.meta.url),'utf8');
function section(from,to) {
  const a=source.indexOf(from),b=source.indexOf(to,a+from.length);
  assert(a>=0 && b>a,`missing production section: ${from} -> ${to}`);return source.slice(a,b);
}
const geography=section('function distanceMetres(','function configureStyle(');
const initialization=section('  const sourceGeometryCorrections =','  let ordinaryCatalog=');
const chooseVariant=section('  function desiredVariant(','  async function loadLandmark(');
const collisionAndNavigation=section('  function sourceFeatures(','  function setPlayer(');
assert(collisionAndNavigation.includes('async function findSafePosition('));
assert(collisionAndNavigation.includes('function pendingSourceCorrectionAt('));
assert(collisionAndNavigation.includes('async function waitForData('));
const front={lng:121.31839,lat:30.72090};
const outside={lng:121.32000,lat:30.72200};
const insideObstacle={lng:121.31833,lat:30.72053};
const context={source:'openmaptiles',sourceLayer:'building'};

function harness({tilesReadyAt=0,roads=true}={}) {
  const f=makeRecord();f.record.detailWanted=true;f.record.status='loading';f.record.loadingModel=true;
  const records=new Map([[ID,f.record]]),boundaries=new Map([[ID,makeBoundary(f.record)]]);
  const ordinary={type:'Feature',id:999,properties:{},geometry:rect(121.3199,30.7219,121.3201,30.7221)};
  const road={type:'Feature',properties:{class:'minor'},geometry:{type:'LineString',coordinates:[[121.3182,30.72165],[121.3186,30.72165]]}};
  const samples=new Map([
    ['openmaptiles:building',[clone(fixture.osm),ordinary]],['openmaptiles:water',[]],
    ['openmaptiles:transportation',roads?[road]:[]],
    ['overture-buildings:building',[clone(fixture.overture),ordinary]],['overture-buildings:building_part',[]],
  ]);
  const clock={now:0},sleeps=[],schedule=[],queries=[],sweeps=[];
  const sleep=async ms=>{
    assert(Number.isFinite(ms) && ms>0,'production waits must advance finite positive time');
    sleeps.push({at:clock.now,ms});const end=clock.now+ms;
    while(schedule.length && schedule[0].at<=end){const event=schedule.shift();clock.now=event.at;await event.run();}
    clock.now=end;
  };
  const map={getZoom:()=>19,triggerRepaint(){},areTilesLoaded:()=>clock.now>=tilesReadyAt,
    querySourceFeatures(id,{sourceLayer}){queries.push({at:clock.now,source:id,sourceLayer});return samples.get(`${id}:${sourceLayer}`)||[];}};
  const streetInteraction={sweep(a,b,dimensions){sweeps.push({a,b,dimensions});return null;}};
  const env={SourceGeometryCorrectionState,scene:f.sceneRoot,landmarkRecords:records,landmarkBoundaries:boundaries,
    map,performance:{now:()=>clock.now},sleep,streetInteraction,osmSuppression:{schedule(){} }};
  const names=Object.keys(env),factory=new Function(...names,`
    const DEG=Math.PI/180,EARTH=6378137,clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
    let destroyed=false,buildingMode='osm',buildingSourceId='openmaptiles';const sourceId='openmaptiles';
    let current=${JSON.stringify(front)},explicitCamera=null;
    let collisionDirty=true,collisionUpdated=0,collisionRevision=0,polygons=[],largePolygons=[],grid=new Map(),roadLines=[];
    ${geography}\n${initialization}\n${chooseVariant}\n${collisionAndNavigation}
    return {state:sourceGeometryCorrections,findSafePosition,waitForData,collisionAt,pendingSourceCorrectionAt,desiredVariant,
      setMode(mode){buildingMode=mode;buildingSourceId=mode==='overture'?'overture-buildings':'openmaptiles';},
      destroy(){destroyed=true;},cache:()=>({revision:collisionRevision,polygons,roadLines})};`);
  return {...f,records,boundaries,samples,clock,sleeps,queries,sweeps,...factory(...names.map(n=>env[n])),
    at(at,run){schedule.push({at,run});schedule.sort((a,b)=>a.at-b.at);}};
}
const config=h=>h.boundaries.get(ID).source_geometry_correction;
function pending(h,point=front,extra={}) {
  let calls=0;
  const result=h.state.pendingAt(point,{...context,getFeatures:()=>{calls++;return h.samples.get('openmaptiles:building');},
    getDesiredVariant:r=>h.desiredVariant(r),...extra});
  return {result,calls};
}
async function originalFallback(point=front,options={}) {
  const h=harness(options);config(h).enabled=false;
  const result=await h.findSafePosition({...point,timeout:1000});
  assert.equal(result.adjusted,true,'control must exercise an actual blocked-source fallback');
  assert.equal(h.collisionAt(result.lng,result.lat),null);return result;
}

test('pending correction queries actual source lazily only inside the exact configured component',()=>{
  const h=harness();assert.deepEqual(pending(h),{result:true,calls:1});
  assert.deepEqual(pending(h,outside),{result:false,calls:0},'ordinary point does not query source for correction');
  assert.deepEqual(pending(h,{lng:NaN,lat:front.lat}),{result:false,calls:0});
  assert.deepEqual(pending(h,front,{source:'wrong-source'}),{result:false,calls:0});
  assert.deepEqual(pending(h,front,{sourceLayer:'water'}),{result:false,calls:0});
  for(const status of ['idle','loading']){h.record.status=status;h.record.loadingModel=false;assert.equal(pending(h).result,true,status);}
  h.record.status='loaded';h.record.activeVariant='distant';assert.equal(pending(h).result,true,'unverified variant upgrade may be pending');
  h.record.activeVariant='full';assert.equal(pending(h).result,false,'already loaded same variant without a valid receipt is not a pending upgrade');
});

test('pending correction rejects invalid binding or no-longer-requested asset without querying source',()=>{
  const cases=[
    ['disabled',h=>config(h).enabled=false],['invalid schema',h=>config(h).schema='unsupported'],
    ['foreign model',h=>config(h).model_id='other'],['bad provenance',h=>config(h).provenance.evidence_sha256='bad'],
    ['wrong asset SHA',h=>config(h).variants.web.asset_sha256='f'.repeat(64)],
    ['missing asset SHA',h=>config(h).variants.web.asset_sha256=null],['missing asset file',h=>h.record.assets.web.file=''],
    ['excess asset bytes',h=>h.record.assets.web.bytes=100000000],['nonbuilding',h=>h.record.kind='water'],
    ['wrong anchor',h=>h.record.anchor=[121,30]],['no detail request',h=>h.record.detailWanted=false],
    ['disposed',h=>h.record.catalogDisposed=true],['failed variant',h=>h.record.failedVariants=new Set(['full'])],
    ['error',h=>h.record.status='error'],['aborted',h=>{h.record.catalogController=new AbortController();h.record.catalogController.abort();}],
    ['absent record',h=>h.records.delete(ID)],['absent boundary',h=>h.boundaries.delete(ID)],
    ['invalid obstacle',h=>config(h).collision_geometry=null],
    ['whole park obstacle',h=>config(h).collision_geometry=clone(fixture.overture.geometry)],
  ];
  for(const [name,change] of cases){const h=harness();change(h);assert.deepEqual(pending(h),{result:false,calls:0},name);}
  assert.deepEqual(pending(harness(),front,{getDesiredVariant:()=> 'unsupported'}),{result:false,calls:0});
});

test('pending wait requires actual source ID, layer and canonical geometry, not merely configured POI',()=>{
  const mutations=[
    ['missing source feature',()=>[]],
    ['native ID',f=>[{...f,id:f.id+1}]],['native ID type',f=>[{...f,id:String(f.id)}]],
    ['source',f=>[{...f,source:'other-source'}]],['source layer',f=>[{...f,sourceLayer:'water'}]],
    ['geometry',f=>{f.geometry.coordinates[0][0][1][0]+=0.0001;return [f];}],
    ['only unrelated components',f=>{f.geometry.coordinates=f.geometry.coordinates.slice(1);return [f];}],
  ];
  for(const [name,mutate] of mutations){const h=harness();h.samples.set('openmaptiles:building',mutate(clone(fixture.osm)));
    assert.deepEqual(pending(h),{result:false,calls:1},name);}
  const h=harness();assert.equal(pending(h,front,{getFeatures:()=>{throw Error('source unavailable');}}).result,false);
  assert.equal(pending(h,front,{getFeatures:()=>null}).result,false);
  h.setMode('overture');assert.equal(h.pendingSourceCorrectionAt(front.lng,front.lat),true);
  h.samples.get('overture-buildings:building')[0].properties.id='foreign-uuid';
  assert.equal(h.pendingSourceCorrectionAt(front.lng,front.lat),false,'actual helper uses mode namespace and property ID');
});

test('delayed verified GLB success preserves requested starting point after tiles finish',async()=>{
  for(const mode of ['osm','overture']){
    const h=harness();h.setMode(mode);let loadedAt;
    h.at(430,async()=>{assert.equal(h.collisionAt(front.lng,front.lat),'building','collision remains until receipt activation');
      await loadVerified(h);h.record.loadingModel=false;loadedAt=h.clock.now;});
    const result=await h.findSafePosition({...front,timeout:1000});
    assert.deepEqual(result,{...front,adjusted:false,verified:true},mode);assert.equal(loadedAt,430);assert.equal(h.clock.now,480);
    assert.deepEqual(h.sleeps.map(s=>s.ms),[180,100,100,100]);assert.equal(h.state.isActive(ID),true);
    assert.equal(h.collisionAt(front.lng,front.lat),null);assert.equal(h.collisionAt(insideObstacle.lng,insideObstacle.lat),'building');
  }
});

test('delayed successful loading never bypasses the finite replacement obstacle',async()=>{
  const h=harness();h.at(230,async()=>{await loadVerified(h);h.record.loadingModel=false;});
  const result=await h.findSafePosition({...insideObstacle,timeout:1000});
  assert.equal(h.clock.now,280);assert.equal(result.adjusted,true);assert.equal(h.collisionAt(insideObstacle.lng,insideObstacle.lat),'building');
  assert.equal(h.collisionAt(result.lng,result.lat),null);assert.equal(h.state.isActive(ID),true);
});

test('failed SHA or parse stops waiting and retains the original source-safe fallback',async()=>{
  const expected=await originalFallback();
  for(const failure of ['SHA','parse']){
    const h=harness();h.at(330,async()=>{
      const options=failure==='SHA'?{fetchFunction:async()=>new Response(Buffer.from('bad bytes'))}
        :{loader:{async parseAsync(){throw Error('parse failed');}}};
      await assert.rejects(loadVerified(h,options));h.record.loadingModel=false;h.record.status='error';h.record.failedVariants=new Set(['full']);
    });
    const result=await h.findSafePosition({...front,timeout:1000});assert.deepEqual(result,expected,failure);
    assert.equal(h.clock.now,380);assert.equal(h.state.isActive(ID),false);assert.equal(h.collisionAt(front.lng,front.lat),'building');
  }
});

test('pending model timeout uses remaining original budget and falls back without weakening collision',async()=>{
  const expected=await originalFallback();const h=harness();
  const result=await h.findSafePosition({...front,timeout:425});
  assert.deepEqual(result,expected);assert.equal(h.clock.now,425);assert.deepEqual(h.sleeps.map(s=>s.ms),[180,100,100,45]);
  assert.equal(h.state.isActive(ID),false);assert.equal(h.collisionAt(front.lng,front.lat),'building');
  assert.equal(h.record.status,'loading');assert(h.sleeps.slice(1).every(s=>s.ms<=100));
});

test('tile waiting consumes navigation budget instead of granting another full model timeout',async()=>{
  const expected=await originalFallback();const h=harness({tilesReadyAt:330});
  const result=await h.findSafePosition({...front,timeout:425});
  assert.deepEqual(result,expected);assert.equal(h.clock.now,425);assert.deepEqual(h.sleeps.map(s=>s.ms),[180,150,95]);
  const late=harness({tilesReadyAt:1000});const lateResult=await late.findSafePosition({...front,timeout:200});
  assert.equal(lateResult.adjusted,true);assert.equal(lateResult.verified,false);
  assert.deepEqual(late.sleeps.map(s=>s.ms),[180,150,150],'retains original tile-timeout behavior without added model waits');
});

test('ordinary blocked or free points add no correction wait and retain street interaction fallback',async()=>{
  for(const point of [outside,{lng:121.3205,lat:30.7225}]){
    const h=harness();let correctionQueries=0;
    const realPending=h.state.pendingAt.bind(h.state);
    h.state.pendingAt=(p,options)=>realPending(p,{...options,getFeatures:()=>{correctionQueries++;return options.getFeatures();}});
    const result=await h.findSafePosition({...point,timeout:1000});
    assert.equal(h.clock.now,180);assert.deepEqual(h.sleeps.map(s=>s.ms),[180]);assert.equal(correctionQueries,0);
    assert.equal(result.adjusted,point===outside);assert(h.sweeps.length>0,'original street interaction check remains used');
  }
});

test('real ID or geometry mismatch adds no wait and does not bypass that source building',async()=>{
  const expected=await originalFallback();
  for(const name of ['ID','geometry']){
    const h=harness(),actual=h.samples.get('openmaptiles:building')[0];
    if(name==='ID')actual.id++;
    else actual.geometry.coordinates[0][0][1][0]+=0.0001;
    const result=await h.findSafePosition({...front,timeout:1000});
    assert.equal(h.clock.now,180);assert.deepEqual(h.sleeps.map(s=>s.ms),[180]);assert.deepEqual(result,expected,name);
    assert.equal(h.collisionAt(front.lng,front.lat),'building');
  }
});

test('an already verified visible LOD does not wait for full-detail upgrade',async()=>{
  const h=harness();h.record.lodUrl='synthetic-lod-test-only';await loadVerified(h,{variant:'distant'});
  h.record.loadingModel=true;assert.equal(h.desiredVariant(h.record),'full','nearby actual desiredVariant requests full');
  assert.deepEqual(pending(h),{result:false,calls:0});
  const result=await h.findSafePosition({...front,timeout:1000});
  assert.deepEqual(result,{...front,adjusted:false,verified:true});assert.equal(h.clock.now,180);
  assert.deepEqual(h.sleeps.map(s=>s.ms),[180]);assert.equal(h.state.getState().active[0].variant,'lod');
});

test('leaving, removal, disposal, abort or destruction stops pending wait and restores original fallback',async()=>{
  const expected=await originalFallback();
  for(const [name,stop] of [
    ['leave',h=>h.record.detailWanted=false],['record removal',h=>h.records.delete(ID)],
    ['boundary removal',h=>h.boundaries.delete(ID)],['disposal',h=>h.record.catalogDisposed=true],
    ['abort',h=>{h.record.catalogController=new AbortController();h.record.catalogController.abort();}],
    ['destroy',h=>h.destroy()],
  ]){
    const h=harness();h.at(230,()=>stop(h));const result=await h.findSafePosition({...front,timeout:1000});
    assert.deepEqual(result,expected,name);assert.equal(h.clock.now,280,name);assert.equal(h.state.isActive(ID),false);
    assert.equal(h.collisionAt(front.lng,front.lat),'building');
  }
});

test('source feature disappearing mid-wait stops waiting and uses current source-safe result',async()=>{
  const h=harness();h.at(230,()=>h.samples.set('openmaptiles:building',[]));
  const result=await h.findSafePosition({...front,timeout:1000});
  assert.equal(h.clock.now,280);assert.deepEqual(result,{...front,adjusted:false,verified:false});
  assert.equal(h.state.isActive(ID),false,'not mistaken for receipt activation');
});

test('radial fallback remains unchanged when there is no road candidate',async()=>{
  const expected=await originalFallback(front,{roads:false});const h=harness({roads:false});
  const result=await h.findSafePosition({...front,timeout:250});
  assert.deepEqual(result,expected);assert.equal(result.adjusted,true);assert.equal(h.clock.now,250);
  assert.equal(h.collisionAt(result.lng,result.lat),null);assert.equal(h.collisionAt(front.lng,front.lat),'building');
});
