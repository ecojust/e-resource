import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../vendor/three.module.js';
import {CityDetailStreamer} from '../src/city-detail-streamer.js';
import {LocalModelStreamer} from '../src/local-model-streamer.js';
import {countExpandedTriangles,disposeModelResources} from '../src/model-resources.js';
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {triangleGLB} from './fixtures/city-model-fixture.mjs';
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(predicate){const end=performance.now()+2000;while(!predicate()){if(performance.now()>end)throw Error('Lifecycle fixture did not settle');await pause(2);}}
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject};}
function farObject(count=2){
 const group=new THREE.Group(),geometry=new THREE.BufferGeometry(),ids=[],positions=[];
 for(let i=1;i<=count;i++)for(let j=0;j<3;j++){ids.push(i);positions.push(j,i,0);}
 geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute('_feature_id_0',new THREE.Float32BufferAttribute(ids,1));
 const material=new THREE.MeshStandardMaterial();material.name='CityWalls';group.add(new THREE.Mesh(geometry,material));return group;
}
function nearObject({triangles=12,instances=0,texture=false}={}){
 const group=new THREE.Group();let geometry;
 if(triangles===12)geometry=new THREE.BoxGeometry();
 else {geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(new Float32Array(triangles*9),3));geometry.setAttribute('normal',new THREE.Float32BufferAttribute(new Float32Array(triangles*9),3));}
 const material=new THREE.MeshStandardMaterial();
 if(texture)material.map=new THREE.DataTexture(new Uint8Array(256*256*4),256,256);
 group.add(instances?new THREE.InstancedMesh(geometry,material,instances):new THREE.Mesh(geometry,material));return group;
}
const bounds=[121,31,121.0001,31.0001],view={lng:121,lat:31,zoom:18,mode:'walk'};
function index(count=2,overrides={}){return {feature_count:count,near:Array.from({length:count},(_,i)=>({id:'n'+i,file:'n'+i+'.glb',feature_local_ids:[i+1],geographic_bbox:bounds,expanded_triangles:12,size_bytes:100,geometry_bytes:100,...overrides}))};}
function harness(t,{count=2,metadata=index(count),fetchIndex,fetchModel,parse,options={},prepare}={}){
 const scene=new THREE.Scene(),far=farObject(count);scene.add(far);const parent={id:'macro',object:far,detailURL:'https://example.test/city/macro/index.json'};
 const calls=[],disposed=[],errors=[],states=[],objects=[],parses=[];
 const disposeObject=object=>{disposed.push(object);scene.remove(object);disposeModelResources(object)};
 const fetchFunction=async(url,{signal})=>{
  calls.push({url,signal});
  if(url.endsWith('.json'))return fetchIndex?fetchIndex(url,signal):new Response(JSON.stringify(metadata));
  return fetchModel?fetchModel(url,signal):new Response(new TextEncoder().encode(url));
 };
 const loader={async parseAsync(buffer,url){parses.push({buffer,url});const object=parse?await parse(buffer,url):nearObject();objects.push(object);return {scene:object};}};
 const streamer=new CityDetailStreamer({THREE,scene,loader,fetchFunction,prepareObject:prepare||(()=>{}),disposeObject,
  onError:error=>errors.push(error.message),onChange:state=>states.push(state),...options});
 t.after(()=>streamer.destroy());
 return {streamer,parent,far,scene,calls,disposed,errors,states,objects,parses,activate(){streamer.update(view);streamer.syncParents([parent]);},get owner(){return streamer.parents.get(far);}};
}

test('far wall stays visible until parse is ready; hide/resume switches ownership synchronously',async t=>{
 const pending=deferred(),h=harness(t,{count:1,parse:()=>pending.promise});h.activate();await until(()=>h.parses.length);
 assert.equal(h.owner.mask.data[1],0);assert.equal(h.streamer.getState().visible,0);
 const near=nearObject();pending.resolve(near);await until(()=>h.streamer.getState().visible===1);
 assert.equal(h.owner.mask.data[1],255);assert.equal(near.visible,true);
 h.streamer.syncParents([]);assert.equal(near.visible,false);assert.equal(h.owner.mask.data[1],0);assert.equal(h.streamer.getState().visible,0);
 h.streamer.syncParents([h.parent]);assert.equal(near.visible,true);assert.equal(h.owner.mask.data[1],255);assert.equal(h.streamer.stats.requests,1);
});

test('hidden parent cancels its index immediately; stale old response cannot install over resumed index',async t=>{
 const pending=[];const h=harness(t,{count:1,fetchIndex:(_url,signal)=>{const d=deferred();pending.push({...d,signal});return d.promise;}});h.activate();
 assert.equal(h.owner.status,'loading');h.streamer.syncParents([]);assert.equal(h.owner.status,'idle');assert.equal(pending[0].signal.aborted,true);
 h.streamer.syncParents([h.parent]);assert.equal(pending.length,2);
 pending[1].resolve(new Response(JSON.stringify(index(1))));await until(()=>h.streamer.getState().visible===1);const mask=h.owner.mask;
 pending[0].resolve(new Response(JSON.stringify(index(2))));await tick();assert.equal(h.owner.mask,mask);assert.equal(h.owner.records.length,1);assert.equal(h.errors.length,0);
});

test('index timeout returns to idle with retry; next visible sync can succeed',async t=>{
 let n=0;const h=harness(t,{count:1,options:{indexTimeoutMs:10,retryDelayMs:0},fetchIndex:(_url,signal)=>{
  if(n++)return new Response(JSON.stringify(index(1)));
  return new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(new Error('aborted')),{once:true}));
 }});h.activate();await until(()=>h.errors.length===1);assert.equal(h.owner.status,'idle');assert.match(h.errors[0],/timed out/);
 h.streamer.syncParents([h.parent]);await until(()=>h.streamer.getState().visible===1);assert.equal(n,2);
});

test('parent detach during nonabortable parse disposes late near model without acquiring ownership',async t=>{
 const pending=deferred(),h=harness(t,{count:1,parse:()=>pending.promise});h.activate();await until(()=>h.parses.length);
 const material=h.far.children[0].material,mask=h.owner.mask;h.streamer.detach(h.far);
 assert.equal(mask.disposed,true);assert.equal(h.streamer.parents.size,0);assert(!material.customProgramCacheKey().includes('city-feature-mask'));
 const near=nearObject();pending.resolve(near);await until(()=>!h.streamer.inflight);
 assert(h.disposed.includes(near));assert.equal(near.parent,null);assert.equal(h.errors.length,0);assert.equal(h.streamer.getState().loaded,0);
});

test('view cancellation leaves original solid building and disposes late parse',async t=>{
 const pending=deferred(),h=harness(t,{count:1,parse:()=>pending.promise});h.activate();await until(()=>h.parses.length);
 h.streamer.update({...view,lng:122});assert.equal(h.owner.mask.data[1],0);assert(h.streamer.inflight.controller.signal.aborted);
 const near=nearObject();pending.resolve(near);await until(()=>!h.streamer.inflight);assert(h.disposed.includes(near));assert.equal(h.owner.mask.data[1],0);
});

test('model HTTP failure preserves far wall and retries after backoff',async t=>{
 let n=0;const h=harness(t,{count:1,options:{retryDelayMs:10000},fetchModel:()=>new Response(new Uint8Array([1]),{status:n++?200:503})});h.activate();
 await until(()=>h.streamer.stats.failed===1);const r=h.owner.records[0];assert.equal(h.owner.mask.data[1],0);assert.equal(r.object,null);assert(r.retryAt>performance.now());
 r.retryAt=0;h.streamer.update(view);await until(()=>h.streamer.getState().visible===1);assert.equal(h.owner.mask.data[1],255);assert.equal(n,2);
});

test('an explicit timeout cancellation during decode still backs off instead of retrying forever',async t=>{
 const pending=deferred(),h=harness(t,{count:1,parse:()=>pending.promise,options:{retryDelayMs:10000}});h.activate();
 await until(()=>h.parses.length);h.streamer.inflight.controller.abort('timeout');const near=nearObject();pending.resolve(near);await until(()=>!h.streamer.inflight);
 assert.equal(h.streamer.stats.failed,1);assert.equal(h.streamer.stats.requests,1);assert(h.disposed.includes(near));assert.equal(h.owner.mask.data[1],0);
});

test('late decoder rejection after destroy cannot report errors or re-add geometry',async t=>{
 const pending=deferred(),h=harness(t,{count:1,parse:()=>pending.promise});h.activate();await until(()=>h.parses.length);h.streamer.destroy();pending.reject(new Error('late failure'));
 await until(()=>!h.streamer.inflight);assert.equal(h.errors.length,0);assert.equal(h.streamer.getState().loaded,0);assert.equal(h.streamer.parents.size,0);
});

test('decoded memory replaces inaccurate estimates before activation; visible plus cached residency stays bounded',async t=>{
 const h=harness(t,{parse:()=>nearObject({triangles:100}),options:{maxVisible:2,maxCache:2,memoryBudget:9000}});h.activate();await until(()=>h.streamer.stats.completed===2&&!h.streamer.inflight);
 const state=h.streamer.getState();assert.equal(state.visible,1);assert.equal(state.loaded,1);assert(state.memoryBytes<=9000);assert.equal(state.metadataMismatches,2);
 assert(h.states.every(s=>s.memoryBytes<=9000));assert.equal(h.owner.mask.data[1],255);assert.equal(h.owner.mask.data[2],0);assert.equal(h.streamer.stats.evicted,1);
});

test('actual instance-expanded triangle count enforces target while one indivisible building may exceed it',async t=>{
 const h=harness(t,{parse:()=>nearObject({instances:100}),options:{maxVisible:2,triangleBudget:1000}});h.activate();await until(()=>h.streamer.getState().visible===1&&!h.streamer.inflight);
 const state=h.streamer.getState();assert.equal(state.triangles,1200);assert.equal(state.visible,1);assert.equal(h.streamer.stats.requests,1);assert.equal(h.owner.records[0].triangles,1200);
 assert.equal(countExpandedTriangles(h.owner.records[0].object),1200);assert.equal(state.metadataMismatches,1);
});

test('actual owned texture memory is included and an oversized near model never masks far geometry',async t=>{
 const h=harness(t,{count:1,parse:()=>nearObject({texture:true}),options:{memoryBudget:10000}});h.activate();await until(()=>h.streamer.stats.failed===1);
 assert.equal(h.streamer.getState().visible,0);assert.equal(h.owner.mask.data[1],0);assert.equal(h.disposed.length,1);assert.equal(h.streamer.getState().loaded,0);assert.match(h.errors[0],/memory budget/);
});

for(const [name,mutate] of [
 ['nonfinite resource',j=>{j.near[0].geometry_bytes='NaN'}],
 ['zero explicit resource',j=>{j.near[0].geometryBytes=0}],
 ['zero explicit triangle count',j=>{j.near[0].expandedTriangles=0}],
 ['inverted bounds',j=>{j.near[0].geographic_bbox=[122,31,121,31]}],
 ['duplicate local IDs',j=>{j.near[1].feature_local_ids=[1]}],
 ['duplicate model IDs',j=>{j.near[1].id='n0'}],
 ['missing model URL',j=>{delete j.near[0].file}],
 ['incomplete ownership',j=>{j.near.pop()}],
])test(`invalid index (${name}) never binds a mask or suppresses source`,async t=>{
 const metadata=index(2);mutate(metadata);const h=harness(t,{metadata});const original=h.far.children[0].material.onBeforeCompile;h.activate();await until(()=>h.errors.length===1);
 assert.equal(h.owner.mask,undefined);assert.equal(h.owner.status,'idle');assert.equal(h.streamer.records.size,0);assert.equal(h.far.children[0].material.onBeforeCompile,original);
});

test('detaching a ready parent restores shader and removes all near objects, including hidden cache',async t=>{
 const h=harness(t);h.activate();await until(()=>h.streamer.getState().visible===2);const mask=h.owner.mask;
 h.streamer.syncParents([]);assert(mask.data.every(x=>x===0));h.streamer.detach(h.far);
 assert.equal(h.streamer.getState().loaded,0);assert.equal(h.streamer.records.size,0);assert.equal(h.disposed.length,2);assert.equal(mask.disposed,true);assert.equal(h.scene.children.length,1);
});

test('detail URL replacement creates new ownership and old mask cannot affect the new parent',async t=>{
 const h=harness(t,{count:1});h.activate();await until(()=>h.streamer.getState().visible===1);const old=h.owner;
 h.parent.detailURL='https://example.test/city/replacement/index.json';h.streamer.syncParents([h.parent]);await until(()=>h.owner!==old&&h.streamer.getState().visible===1);
 assert(old.mask.disposed);assert.equal(old.mask.data[1],0);assert.equal(h.owner.mask.data[1],255);assert.equal(h.disposed.length,1);
});

test('local manifest detailURL resolves from the pinned manifest directory, preserving absent-detail compatibility',async t=>{
 const suppression={clear:async()=>{},getState:()=>({}),destroy(){},removeOwner(){},setOwner:async()=>{}};
 const streamer=new LocalModelStreamer({scene:new THREE.Scene(),loader:{},suppression,prepareObject(){},disposeObject(){}});t.after(()=>streamer.destroy());
 const tile={origin_longitude:121,origin_latitude:31,geographic_bbox:bounds,featureIds:['a'],triangles:12,size_bytes:100};
 await streamer.setManifest({tiles:[{...tile,id:'new',file:'far/new.glb',near_manifest_file:'near/new/index.json'},{...tile,id:'old',file:'old.glb'}]}, {baseURL:'https://cdn.example/repo@fixed/assets/city/'});
 assert.equal(streamer.records.get('new').detailURL,'https://cdn.example/repo@fixed/assets/city/near/new/index.json');assert.equal(streamer.records.get('old').detailURL,null);
});

const gzipGLB=triangleGLB(),gzipBytes=gzipSync(gzipGLB,{level:6,mtime:0});
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
function gzipIndex(fields={}){return index(1,{file:'n0.glb.gz',content_encoding:'gzip',size_bytes:gzipBytes.length,sha256:hash(gzipBytes),decoded_size_bytes:gzipGLB.length,decoded_sha256:hash(gzipGLB),...fields});}

test('gzip near model reaches parser only as fully verified original GLB bytes',async t=>{
 const h=harness(t,{count:1,metadata:gzipIndex(),fetchModel:()=>new Response(gzipBytes),parse:buffer=>{assert.deepEqual(new Uint8Array(buffer),gzipGLB);return nearObject();}});
 h.activate();await until(()=>h.streamer.getState().visible===1);assert.equal(h.parses.length,1);assert.equal(h.owner.mask.data[1],255);assert.equal(h.errors.length,0);
});

test('HTTP already-decoded gzip model follows the same verified activation path',async t=>{
 const h=harness(t,{count:1,metadata:gzipIndex(),fetchModel:()=>new Response(gzipGLB,{headers:{'Content-Encoding':'gzip'}})});
 h.activate();await until(()=>h.streamer.getState().visible===1);assert.deepEqual(new Uint8Array(h.parses[0].buffer),gzipGLB);assert.equal(h.owner.mask.data[1],255);
});

test('bad gzip hash never parses or hides the far wall',async t=>{
 const h=harness(t,{count:1,metadata:gzipIndex({decoded_sha256:'0'.repeat(64)}),fetchModel:()=>new Response(gzipBytes)});
 h.activate();await until(()=>h.streamer.stats.failed===1);assert.equal(h.parses.length,0);assert.equal(h.owner.mask.data[1],0);assert.equal(h.streamer.getState().visible,0);assert.match(h.errors[0],/Decoded city model SHA-256/);
});

test('truncated gzip preserves far ownership even when its damaged transport hash is declared',async t=>{
 const truncated=gzipBytes.subarray(0,gzipBytes.length-3);
 const h=harness(t,{count:1,metadata:gzipIndex({size_bytes:truncated.length,sha256:hash(truncated)}),fetchModel:()=>new Response(truncated)});
 h.activate();await until(()=>h.streamer.stats.failed===1);assert.equal(h.parses.length,0);assert.equal(h.owner.mask.data[1],0);assert.equal(h.streamer.getState().loaded,0);
});

test('late cancellation after verified gzip parsing disposes the decoded scene before any mask ownership',async t=>{
 const pending=deferred(),h=harness(t,{count:1,metadata:gzipIndex(),fetchModel:()=>new Response(gzipBytes),parse:()=>pending.promise});h.activate();await until(()=>h.parses.length);
 const mask=h.owner.mask;assert.equal(mask.data[1],0);h.streamer.detach(h.far);const near=nearObject();pending.resolve(near);await until(()=>!h.streamer.inflight);
 assert(h.disposed.includes(near));assert.equal(mask.data[1],0);assert.equal(mask.disposed,true);assert.equal(h.streamer.getState().loaded,0);assert.equal(h.errors.length,0);
});

test('cancellation while gzip body is incomplete cancels its stream without invoking the parser',async t=>{
 let cancelled=false;
 const h=harness(t,{count:1,metadata:gzipIndex(),fetchModel:()=>new Response(new ReadableStream({start(c){c.enqueue(gzipBytes.subarray(0,10));},cancel(){cancelled=true;}}))});
 h.activate();await until(()=>h.streamer.inflight);h.streamer.syncParents([]);await until(()=>!h.streamer.inflight);
 assert.equal(cancelled,true);assert.equal(h.parses.length,0);assert.equal(h.owner.mask.data[1],0);assert.equal(h.errors.length,0);
});

async function settleDeadline(predicate){for(let i=0;i<1000&&!predicate();i++)await tick();assert(predicate(),'Network deadline fixture did not settle');}

test('verified gzip model survives CPU parsing beyond the unchanged network deadline',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});const pending=deferred();
 const h=harness(t,{count:1,metadata:gzipIndex(),fetchModel:()=>new Response(gzipBytes),parse:()=>pending.promise});h.activate();await settleDeadline(()=>h.parses.length===1);
 const signal=h.streamer.inflight.controller.signal;t.mock.timers.tick(35001);assert.equal(signal.aborted,false);
 const near=nearObject();pending.resolve(near);await settleDeadline(()=>!h.streamer.inflight);h.streamer.update(view);
 assert.equal(h.streamer.getState().visible,1);assert.equal(h.streamer.stats.requests,1);assert.equal(h.streamer.stats.failed,0);assert.equal(h.streamer.stats.discarded,0);assert.equal(h.owner.mask.data[1],255);assert.equal(h.disposed.length,0);
});

test('incomplete gzip network body still times out and preserves the far wall',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});let body,cancelled=false;
 const h=harness(t,{count:1,metadata:gzipIndex(),fetchModel:()=>{
  body=new ReadableStream({start(c){c.enqueue(gzipBytes.subarray(0,10));},cancel(){cancelled=true;}});return new Response(body);
 }});h.activate();await settleDeadline(()=>body?.locked);const signal=h.streamer.inflight.controller.signal;
 t.mock.timers.tick(34999);assert.equal(signal.aborted,false);t.mock.timers.tick(1);await settleDeadline(()=>!h.streamer.inflight);
 assert.equal(signal.reason,'timeout');assert.equal(cancelled,true);assert.equal(h.parses.length,0);assert.equal(h.streamer.stats.failed,1);assert.equal(h.streamer.stats.requests,1);assert.equal(h.streamer.getState().visible,0);assert.equal(h.owner.mask.data[1],0);assert(h.owner.records[0].retryAt>performance.now());
});
