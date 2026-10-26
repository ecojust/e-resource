import test from 'node:test';
import assert from 'node:assert/strict';
import {OrdinaryCityDetailStreamer} from '../src/ordinary-city-detail-streamer.js';
import {createOrdinaryMacroRegistrar,loadOrdinaryLandmarkAsset} from '../src/ordinary-scene-adapter.js';
import {OrdinaryBuildingCatalog,readVerifiedBytes,validateMacroIndex} from '../src/ordinary-building-catalog.js';
import {disposeModelResources} from '../src/model-resources.js';
import {placeDescription,modelSurfaceKind} from '../src/precise-registration-ui.js';
import {THREE,FAR,BASE,OVERRIDE,view,fixture,farObject,nearObject,until,deferred,sha,json,bytes} from './ordinary-fixtures.mjs';

function city(t,{parse}={}) {
  const f=fixture(),scene=new THREE.Scene(),object=farObject(),disposed=[],errors=[],calls=[];
  const streamer=new OrdinaryCityDetailStreamer({THREE,scene,loader:{async parseAsync(buffer){return {scene:parse?await parse(buffer):nearObject({override:new TextDecoder().decode(buffer).includes('complete')})};}},
    prepareObject:()=>{},disposeObject(model){disposed.push(model);scene.remove(model);disposeModelResources(model);},onError:e=>errors.push(e),
    fetchFunction:async url=>{calls.push(url);return new Response(url.endsWith('READY.json')?JSON.stringify(f.index):url.endsWith('override.glb')?OVERRIDE:BASE);}});
  const record={id:f.macro,object,detailURL:`https://example.test/assets/city-detail/macros/${f.macro}/READY.json`,sha256:FAR,buildingCount:2};
  t.after(()=>streamer.destroy());
  return {f,scene,object,record,streamer,disposed,errors,calls,get parent(){return streamer.parents.get(object);},start(){streamer.update(view);streamer.syncParents([record]);}};
}

test('live macro adds exact target ownership, preserves neighbor, and restores baseline on unload',async t=>{
  const h=city(t);h.start();await until(()=>h.streamer.getState().visible===1);
  const old=[...h.streamer.records][0].object;
  h.streamer.installMacroReplacements('catalog',h.f.registry,'https://example.test/');
  await until(()=>h.streamer.getState().precise.overrideTiles===1);
  assert(h.disposed.includes(old));const near=[...h.streamer.records][0];
  assert.equal(near.object.children[1].position.x,3);assert.equal(near.object.children[1].visible,true);
  h.streamer.setVisibleLandmarks([h.f.id]);assert.equal(near.object.children[0].visible,false);assert.equal(near.object.children[1].visible,true);
  h.streamer.syncParents([]);assert.equal(h.parent.mask.data[1],255);assert.equal(h.parent.mask.data[2],0);
  assert.throws(()=>h.streamer.removeMacroReplacements('catalog'),/Hide ordinary/);
  h.streamer.setVisibleLandmarks([]);h.streamer.removeMacroReplacements('catalog');
  assert.equal(h.streamer.getState().ordinaryRegistries,0);h.streamer.syncParents([h.record]);
  await until(()=>h.streamer.getState().visible===1);assert.equal([...h.streamer.records][0].replacement,undefined);
  assert.equal(h.streamer.getState().precise.registered,0);assert.equal(h.errors.length,0);
});

test('wrong loaded far SHA or duplicate macro registration cannot mutate an existing scene',async t=>{
  const h=city(t);h.start();await until(()=>h.streamer.getState().visible===1);const before=[...h.streamer.records][0].object;
  const wrong=structuredClone(h.f.registry);wrong.macros[0].baseline_far_sha256='f'.repeat(64);
  assert.throws(()=>h.streamer.installMacroReplacements('catalog',wrong,'https://example.test/'),/Loaded far/);
  assert.equal([...h.streamer.records][0].object,before);assert.equal(h.disposed.length,0);
  h.streamer.installMacroReplacements('catalog',h.f.registry,'https://example.test/');
  assert.throws(()=>h.streamer.installMacroReplacements('other',h.f.registry,'https://example.test/'),/already has/);
});

test('late baseline parse is disposed after registry transition and never acquires new ownership',async t=>{
  const wait=deferred(),old=nearObject({override:false});let n=0;
  const h=city(t,{parse:()=>++n===1?wait.promise:nearObject()});h.start();await until(()=>n===1);
  h.streamer.installMacroReplacements('catalog',h.f.registry,'https://example.test/');wait.resolve(old);
  await until(()=>h.streamer.getState().precise.overrideTiles===1);
  assert(h.disposed.includes(old));assert.equal(h.streamer.stats.discarded,1);
  assert.equal([...h.streamer.records][0].object.children[1].visible,true);
});

test('macro candidate may not erase a pre-existing curated owner',t=>{
  const h=city(t);h.streamer.setReplacementOverrides(h.f.registry,'https://example.test/');
  const bad=structuredClone(h.f.registry);bad.macros[0].near[0].groups[0].landmark_id='different-building';
  assert.throws(()=>h.streamer.installMacroReplacements('catalog',bad,'https://example.test/'),/curated target/);
  assert(h.streamer.replacements.landmarks.has(h.f.id));
});

function catalogHarness(t,{sources=[fixture()],fetchFunction,registerMacro,baseURL='https://example.test/'}={}) {
  const calls=[],errors=[],sessions=[],files=new Map(sources.flatMap(s=>[...s.files]));
  const catalog=new OrdinaryBuildingCatalog({baseURL,districts:[{id:'test',name:'Explicit district'}],maxMacros:2,maxModels:1,
    fetchFunction:fetchFunction|| (async url=>{calls.push(url);const key=new URL(url).pathname.slice(new URL(baseURL).pathname.length);return new Response(files.get(key)||'',{status:files.has(key)?200:404});}),
    onError:e=>errors.push(e),registerMacro:registerMacro||((args)=>{const s={...args,wanted:new Set(),disposed:false,setWanted(ids){this.wanted=ids;},dispose(){this.disposed=true;}};sessions.push(s);return s;})});
  t.after(()=>catalog.destroy());const manifest={...sources[0].catalog,macro_count:sources.length,record_count:sources.length,macros:sources.map(s=>s.entry)};
  catalog.setCatalog(manifest);return {catalog,calls,errors,sessions,files};
}

test('catalog fetches only nearby macro/index variants and releases metadata when leaving',async t=>{
  const a=fixture(),b=fixture({macro:'14-13701-6700',id:'second-ordinary',lng:122});const h=catalogHarness(t,{sources:[a,b]});
  assert.equal(h.calls.length,0);h.catalog.update(view);await until(()=>h.catalog.getState().completed===1);
  assert.equal(h.calls.length,2);assert(h.calls.every(url=>url.includes(a.macro)));assert.equal(h.sessions[0].wanted.size,1);
  assert.equal(h.sessions[0].models[0].navigation.listed,false);assert.equal(h.sessions[0].models[0].source_provider,a.record.source_provider);
  h.catalog.update({...view,lng:123});assert.equal(h.sessions[0].disposed,true);assert.equal(h.catalog.getState().residentRecords,0);
  h.catalog.update(view);await until(()=>h.catalog.getState().completed===2);assert.equal(h.sessions.length,2);
});

test('changed original index bytes fail SHA and never register an owner',async t=>{
  const h=catalogHarness(t);const key=[...h.files.keys()].find(key=>key.endsWith('index.json'));h.files.set(key,bytes(' '.repeat(h.files.get(key).length)));
  h.catalog.update(view);await until(()=>h.errors.length===1);assert.equal(h.sessions.length,0);assert.equal(h.catalog.getState().failed,1);
});

test('missing audited registry, pending acceptance or removed neighbor fails before scene registration',async t=>{
  for(const issue of ['registry','acceptance','neighbor']) {
    const f=fixture();if(issue==='registry')delete f.shard.replacement_registry;
    if(issue==='acceptance')f.shard.models[0].acceptance.browser_proof.status='pending';
    if(issue==='neighbor')f.shard.models[0].owner.preserve_neighbor_local_ids=[];
    const body=json(f.shard);f.entry.bytes=body.length;f.entry.sha256=sha(body);f.files.set(f.entry.file,body);
    const h=catalogHarness(t,{sources:[f]});h.catalog.update(view);await until(()=>h.errors.length===1);
    assert.equal(h.sessions.length,0,issue);assert.equal(h.catalog.getState().residentRecords,0);
  }
});

test('generation change cancels delayed metadata, prevents a stale session and permits a fresh retry',async t=>{
  const f=fixture(),gate=deferred();let first=true;
  const h=catalogHarness(t,{sources:[f],fetchFunction:async url=>{if(first){first=false;await gate.promise;}return new Response(f.files.get(new URL(url).pathname.slice(1)));}});
  h.catalog.update(view);h.catalog.setCatalog(f.catalog);gate.resolve();await until(()=>h.catalog.getState().completed===1);
  assert.equal(h.sessions.length,1);assert.equal(h.catalog.getState().discarded,1);assert.equal(h.errors.length,0);
});

test('metadata record and visible-model budgets are independent of distant catalog size',async t=>{
  const sources=[fixture(),fixture({macro:'14-13718-6696',id:'other',lng:121.0002}),fixture({macro:'14-13718-6697',id:'third',lng:121.0003})];
  const h=catalogHarness(t,{sources});h.catalog.update(view);await until(()=>h.catalog.getState().completed===2);
  assert.equal(h.catalog.getState().activeMacros.length,2);assert.equal(h.sessions.reduce((n,s)=>n+s.wanted.size,0),1);assert.equal(h.calls.length,4);
});

test('strict provider/district/owner fields survive; no guessed Bund or Lujiazui UI text',()=>{
  const f=fixture();assert.equal(validateMacroIndex(f.shard,f.entry,f.registry,new Map([['test','Explicit district']]))[0],f.record);
  assert.equal(placeDescription(f.record),'Explicit district · 逐栋复原');assert.equal(modelSurfaceKind(f.record),'architecture');
  const bad=structuredClone(f.shard);bad.models[0].district_name='Wrong district';assert.throws(()=>validateMacroIndex(bad,f.entry,f.registry,new Map([['test','Explicit district']])),/District/);
});

test('verified byte reader still times out a pending response body without publishing partial data',async t=>{
  t.mock.timers.enable({apis:['setTimeout']});let started=false,cancelled=false;
  const promise=readVerifiedBytes({file:'data/x.json',bytes:4,sha256:sha(bytes('data'))},'https://example.test/',{fetchFunction:async()=>new Response(new ReadableStream({start(){started=true;},cancel(){cancelled=true;}}))});
  const outcome=assert.rejects(promise,/timed out/);await until(()=>started);t.mock.timers.tick(35000);await outcome;assert.equal(cancelled,true);
});

function glb(doc) {const raw=bytes(JSON.stringify(doc)),padded=new Uint8Array(Math.ceil(raw.length/4)*4);padded.fill(32);padded.set(raw);const out=new Uint8Array(20+padded.length),v=new DataView(out.buffer);v.setUint32(0,0x46546c67,true);v.setUint32(4,2,true);v.setUint32(8,out.length,true);v.setUint32(12,padded.length,true);v.setUint32(16,0x4e4f534a,true);out.set(padded,20);return out;}
test('ordinary photo GLB bytes are checked before parse; external dependency cannot bypass ownership review',async()=>{
  let parsed=0;const loader={async parseAsync(){parsed++;return {scene:new THREE.Group()};}};
  const data=glb({asset:{version:'2.0'},buffers:[],images:[]}),record={catalogBaseURL:'https://example.test/',assets:{web:{file:'assets/models/precise/a/web.glb',bytes:data.length,sha256:sha(data)}}};
  record.assets.lod={...record.assets.web};
  await loadOrdinaryLandmarkAsset({record,variant:'full',loader,fetchFunction:async()=>new Response(data)});assert.equal(parsed,1);
  const wrong=data.slice();wrong[wrong.length-1]^=1;await assert.rejects(loadOrdinaryLandmarkAsset({record,variant:'full',loader,fetchFunction:async()=>new Response(wrong)}),/SHA/);assert.equal(parsed,1);
  const external=glb({asset:{version:'2.0'},buffers:[{uri:'https://unreviewed.test/external.bin'}],images:[]});record.assets.web={...record.assets.web,bytes:external.length,sha256:sha(external)};
  await assert.rejects(loadOrdinaryLandmarkAsset({record,variant:'full',loader,fetchFunction:async()=>new Response(external)}),/external/);assert.equal(parsed,1);
});

test('scene session restores source/far owners before disposal and keeps unrelated curated models',async t=>{
  const h=city(t);h.start();await until(()=>h.streamer.getState().visible===1);
  const curated={id:'bund17',status:'loaded',object:new THREE.Group()},records=new Map([['bund17',curated]]),boundaries=new Map(),precise=new Set(),events=[];
  const update=()=>{for(const r of records.values())if(r.catalogOwner){r.detailWanted=Boolean(r.catalogWanted&&!r.catalogDisposed);if(r.object)r.object.visible=r.detailWanted;}
    h.streamer.setVisibleLandmarks([...records.values()].filter(r=>r.status==='loaded'&&r.object?.visible).map(r=>r.id));};
  const register=createOrdinaryMacroRegistrar({cityDetails:h.streamer,landmarkRecords:records,landmarkBoundaries:boundaries,preciseLandmarkIds:precise,
    tileSuppression:{setOwner(id,ids){events.push(['source',id,ids]);}},disposeModel(object){assert.equal(h.streamer.visibleLandmarks.has(h.f.id),false);events.push(['dispose']);object.removeFromParent();},
    updateLandmarkVisibility:update,updateBuildingExclusions:()=>events.push(['osm-refresh'])});
  const session=register({owner:'catalog',macroId:h.f.macro,models:[h.f.record],registry:h.f.registry,baseURL:'https://example.test/'});
  const record=records.get(h.f.id);session.setWanted(new Set([h.f.id]));record.object=new THREE.Group();record.status='loaded';update();
  assert(h.streamer.visibleLandmarks.has(h.f.id));session.dispose();assert.equal(records.size,1);assert.equal(records.get('bund17'),curated);
  assert.equal(boundaries.size,0);assert.equal(precise.size,0);assert.equal(h.streamer.getState().ordinaryRegistries,0);
  assert(events.findIndex(e=>e[0]==='source')<events.findIndex(e=>e[0]==='dispose'));
});

test('accepted curated ordinary navigation reuses its exact record; catalog release leaves its owner intact',t=>{
  const h=city(t);h.streamer.setReplacementOverrides(h.f.registry,'https://example.test/');
  const record={...h.f.record,status:'loaded',object:new THREE.Group()},records=new Map([[record.id,record]]);h.streamer.setVisibleLandmarks([record.id]);
  const register=createOrdinaryMacroRegistrar({cityDetails:h.streamer,landmarkRecords:records,landmarkBoundaries:new Map([[record.id,h.f.registry.landmarks[0]]]),preciseLandmarkIds:new Set([record.id]),
    tileSuppression:{setOwner(){throw Error('An adopted curated owner must not be released');}},disposeModel(){throw Error('An adopted curated model must not be disposed');},updateLandmarkVisibility:()=>{},updateBuildingExclusions:()=>{}});
  const session=register({owner:'catalog',macroId:h.f.macro,models:[h.f.record],registry:h.f.registry,baseURL:'https://example.test/'});
  assert.deepEqual(session.adoptedIds,[record.id]);session.setWanted(new Set());session.dispose();
  assert.equal(records.size,1);assert.equal(records.get(record.id),record);assert(h.streamer.visibleLandmarks.has(record.id));
});

test('catalog may reuse an audited predeclared static boundary without removing it when its own model leaves',t=>{
  const h=city(t);h.streamer.setReplacementOverrides(h.f.registry,'https://example.test/');
  const records=new Map(),boundary=h.f.registry.landmarks[0],boundaries=new Map([[h.f.id,boundary]]),ids=new Set([h.f.id]);
  const register=createOrdinaryMacroRegistrar({cityDetails:h.streamer,landmarkRecords:records,landmarkBoundaries:boundaries,preciseLandmarkIds:ids,
    tileSuppression:{setOwner(){}},disposeModel:()=>{},updateLandmarkVisibility:()=>{},updateBuildingExclusions:()=>{}});
  const session=register({owner:'catalog',macroId:h.f.macro,models:[h.f.record],registry:h.f.registry,baseURL:'https://example.test/'});
  assert.equal(records.size,1);session.dispose();assert.equal(records.size,0);assert.equal(boundaries.get(h.f.id),boundary);assert(ids.has(h.f.id));
});

test('synchronous visibility callback cannot recursively unload/reset the same catalog session',async t=>{
  let catalog,disposeCount=0;
  const h=catalogHarness(t,{registerMacro:()=>({setWanted(){catalog.update(catalog.view);},dispose(){disposeCount++;catalog.update(catalog.view);}})});
  catalog=h.catalog;catalog.update(view);await until(()=>catalog.getState().completed===1);
  catalog.update({...view,lng:123});assert.equal(disposeCount,1);assert.equal(catalog.getState().residentRecords,0);
  catalog.update(view);await until(()=>catalog.getState().completed===2);catalog.reset();assert.equal(disposeCount,2);
});

test('canonical registration JSON key order does not change geometry or curated owner equality',t=>{
  const reverse=value=>Array.isArray(value)?value.map(reverse):value&&typeof value==='object'
    ?Object.fromEntries(Object.entries(value).reverse().map(([k,v])=>[k,reverse(v)])):value;
  const h=city(t);h.streamer.setReplacementOverrides(h.f.registry,'https://example.test/');
  const reversed=reverse(h.f.registry);
  assert.doesNotThrow(()=>validateMacroIndex(h.f.shard,h.f.entry,reversed,new Map([['test','Explicit district']])));
  assert.doesNotThrow(()=>h.streamer.installMacroReplacements('ordinary',reversed,'https://example.test/'));
  const wrong=structuredClone(reversed);wrong.landmarks[0].confirmed_boundary.coordinates[0].reverse();
  assert.throws(()=>validateMacroIndex(h.f.shard,h.f.entry,wrong,new Map([['test','Explicit district']])),/boundary/);
});

test('launcher commit root resolves unchanged hashed catalog children without rewriting their JSON',async t=>{
  const baseURL='https://raw.githubusercontent.com/ecojust/e-resource/'+'a'.repeat(40)+'/projects/shanghai/';
  const h=catalogHarness(t,{baseURL});h.catalog.update(view);await until(()=>h.catalog.getState().completed===1);
  assert.equal(h.calls.length,2);assert(h.calls.every(url=>url.startsWith(baseURL)));assert.equal(h.errors.length,0);
  assert.deepEqual(h.catalog.getState().requestedModelIds,['ordinary-test']);
});
