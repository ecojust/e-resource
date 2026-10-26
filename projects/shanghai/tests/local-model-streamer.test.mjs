import assert from 'node:assert/strict';
import test from 'node:test';
import {SpatialTileIndex, FeatureStateSuppressor, LocalModelStreamer} from '../src/local-model-streamer.js';
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,timeout=4000){const end=performance.now()+timeout;while(!fn()){if(performance.now()>end)throw Error('Timed out');await pause(5);}}
const states=new Map();let invalidRemovals=0;
const map={getSource:()=>true,setFeatureState(t,v){states.set(t.sourceLayer+':'+t.id,v);},removeFeatureState(t){const key=t.sourceLayer+':'+t.id;if(!states.has(key))invalidRemovals++;states.delete(key);}};
const suppression=new FeatureStateSuppressor(map,'overture',{budgetMs:10,batchSize:600});
const pendingHide=suppression.setOwner('cancelled',{building:['never-applied']});const pendingShow=suppression.removeOwner('cancelled');await Promise.all([pendingHide,pendingShow]);assert.equal(invalidRemovals,0);
await suppression.setOwner('a',{building:['shared','a']});await suppression.setOwner('b',{building:['shared','b']});
await suppression.removeOwner('a');assert.equal(states.get('building:shared').localModel,true);assert.equal(states.has('building:a'),false);
await suppression.removeOwner('b');assert.equal(states.size,0);assert.equal(suppression.getState().owners,0);
const tiles=Array.from({length:1000},(_,i)=>{const x=i%100,y=Math.floor(i/100),lng=121+x*.022,lat=31+y*.02;return{id:'t'+i,file:'tiles/t'+i+'.glb',origin_longitude:lng,origin_latitude:lat,geographic_bbox:[lng-.009,lat-.008,lng+.009,lat+.008],featureIds:['feature-'+i,'shared'],triangles:100,size_bytes:100};});
const normalized=tiles.map(t=>({bounds:t.geographic_bbox,geometryBounds:t.geographic_bbox,id:t.id}));
const index=new SpatialTileIndex(normalized);assert.ok(index.query(121.1,31.04,1800).length<20);
let activeFetch=0,peakFetch=0,disposed=0,parsing=0;
const scene={objects:new Set(),add(o){this.objects.add(o);},remove(o){this.objects.delete(o);}};
function fakeObject(){return{visible:false,traverse(cb){cb({geometry:{attributes:{position:{array:new Float32Array(300)}},index:{array:new Uint16Array(100)}}});}};}
const loader={async parseAsync(){parsing++;await pause(18);parsing--;return{scene:fakeObject()};}};
async function fetchFunction(url,{signal}){
 activeFetch++;peakFetch=Math.max(peakFetch,activeFetch);
 try{
  await new Promise((resolve,reject)=>{const timer=setTimeout(resolve,12);signal.addEventListener('abort',()=>{clearTimeout(timer);reject(new DOMException('Aborted','AbortError'));},{once:true});});
  if(signal.aborted)throw new DOMException('Aborted','AbortError');
  return new Response(new Uint8Array([1,2,3]),{status:url.includes('missing')?404:200});
 }finally{activeFetch--;}
}
const streamer=new LocalModelStreamer({scene,loader,suppression,prepareObject(){},disposeObject(o){if(!o)return;disposed++;scene.remove(o);},fetchFunction,maxVisible:6,maxCache:8,concurrency:2});
await streamer.setManifest({tiles},{baseURL:'http://localhost/models/'});
streamer.update({lng:121,lat:31,zoom:18,mode:'walk',bearing:0},true);
await pause(3);
streamer.update({lng:122,lat:31.1,zoom:18,mode:'walk',bearing:0},true);
await until(()=>streamer.getState().loading===0&&streamer.getState().queued===0&&streamer.getState().pendingStates===0);
assert.ok(streamer.getState().cancelled>0);assert.ok(streamer.getState().peakConcurrent<=2);assert.ok(peakFetch<=2);
for(let i=0;i<14;i++){
 const tile=tiles[110+i*3];streamer.update({lng:tile.origin_longitude,lat:tile.origin_latitude,zoom:18,mode:'walk',bearing:20},true);
 await until(()=>!streamer.getState().loading&&!streamer.getState().queued&&!streamer.getState().pendingStates);
 assert.ok(streamer.getState().loaded<=8);assert.ok(streamer.getState().visible<=6);
}
assert.ok(streamer.getState().evicted>0);assert.ok(disposed>0);
// A fetch already in the non-abortable parse phase must be discarded on teleport.
streamer.update({lng:121.01,lat:31.18,zoom:18,mode:'walk',bearing:0},true);await until(()=>parsing>0);
streamer.update({lng:122.9,lat:31.18,zoom:18,mode:'walk',bearing:0},true);
await until(()=>!streamer.getState().loading&&!streamer.getState().queued&&!streamer.getState().pendingStates);
assert.ok(streamer.getState().discarded>0);
streamer.update({lng:121.4,lat:31.2,zoom:10,mode:'overview'},true);await until(()=>streamer.getState().pendingStates===0);
assert.equal(streamer.getState().visible,0);assert.equal(states.size,0);
await streamer.setManifest({tiles:[{...tiles[0],id:'missing',file:'missing.glb'}]},{baseURL:'http://localhost/'});
streamer.update({lng:121,lat:31,zoom:18,mode:'walk'},true);await until(()=>streamer.getState().loading===0&&streamer.getState().queued===0);
assert.equal(streamer.getRecords()[0].status,'missing');assert.equal(states.size,0);assert.equal(streamer.getState().visible,0);
// Last manifest wins even when callers do not await an earlier replacement.
await Promise.all([streamer.setManifest({tiles:[tiles[1]]},{baseURL:'http://localhost/'}),streamer.setManifest({tiles:[tiles[2]]},{baseURL:'http://localhost/'})]);
assert.deepEqual(streamer.getRecords().map(r=>r.id),[tiles[2].id]);
streamer.update({lng:tiles[2].origin_longitude,lat:tiles[2].origin_latitude,zoom:18,mode:'walk'},true);await until(()=>streamer.getState().visible>0&&!streamer.getState().pendingStates);assert.ok(states.size>0);
const final=streamer.getState();streamer.destroy();assert.equal(invalidRemovals,0);assert.equal(scene.objects.size,0);assert.equal(states.size,0);
console.log('PASS',JSON.stringify({spatialTiles:1000,peakFetch,peakConcurrent:final.peakConcurrent,peakCache:final.peakCache,evicted:final.evicted,cancelled:final.cancelled,discarded:final.discarded,disposed}));

// Advance only the real production network timer; parser completion is an
// explicit promise, so these fixtures do not shorten the 35000ms threshold.
const turn=()=>new Promise(resolve=>setImmediate(resolve));
async function settleUntil(predicate){for(let i=0;i<1000&&!predicate();i++)await turn();assert(predicate(),'Deadline fixture did not settle');}
function pendingValue(){let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};}
async function deadlineFar(t,{read,parse,sidecar=false}={}){
 const calls=[],objects=new Set(),removed=[],errors=[],owners=new Set();
 const model=fakeObject(),parser=parse||(()=>Promise.resolve(model));let parseCalls=0;
 const stream=new LocalModelStreamer({scene:{add:o=>objects.add(o)},
  loader:{async parseAsync(){parseCalls++;return {scene:await parser()};}},
  suppression:{setOwner:async owner=>{owners.add(owner);},removeOwner:async owner=>{owners.delete(owner);},getState:()=>({pendingStates:0}),clear:async()=>{},destroy:()=>owners.clear()},
  fetchFunction:async(url,{signal})=>{calls.push({url,signal});return {ok:true,arrayBuffer:()=>read?read(url,signal):Promise.resolve(new Uint8Array([1,2,3]).buffer)};},
  prepareObject(){},disposeObject:o=>{removed.push(o);objects.delete(o);},onError:e=>errors.push(e),maxVisible:1,maxCache:1,concurrency:1});
 t.after(()=>stream.destroy());
 await stream.setManifest({tiles:[{id:'deadline',file:'model.glb',origin_longitude:121,origin_latitude:31,geographic_bbox:[121,31,121.001,31.001],triangles:1,size_bytes:100,
  ...(sidecar?{feature_ids_file:'ids.json'}:{featureIds:['building-a']})}]},{baseURL:'https://example.test/'});
 return {stream,calls,objects,removed,errors,owners,model,get parseCalls(){return parseCalls;},start(){stream.update({lng:121,lat:31,zoom:18,mode:'walk'},true);}};
}

test('far CPU parse beyond the network deadline completes once without discard/reload',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});const delayed=pendingValue(),h=await deadlineFar(t,{parse:()=>delayed.promise});h.start();await settleUntil(()=>h.parseCalls===1);
 t.mock.timers.tick(35001);assert.equal(h.calls[0].signal.aborted,false);
 delayed.resolve(h.model);await settleUntil(()=>h.stream.getState().loading===0);h.start();await turn();
 assert.equal(h.stream.getState().visible,1);assert.equal(h.stream.stats.requests,1);assert.equal(h.stream.stats.discarded,0);assert.equal(h.stream.stats.failed,0);assert.equal(h.removed.length,0);assert.equal(h.owners.size,1);
});

for(const pendingPart of ['model','ids'])test(`far pending ${pendingPart} body still reaches the unchanged network timeout`,async t=>{
 t.mock.timers.enable({apis:['setTimeout']});let blockedSignal;
 const h=await deadlineFar(t,{sidecar:pendingPart==='ids',read:(url,signal)=>{
  if(url.endsWith(pendingPart==='ids'?'ids.json':'model.glb')){blockedSignal=signal;return new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')),{once:true}));}
  return Promise.resolve(new Uint8Array([1,2,3]).buffer);
 }});h.start();await settleUntil(()=>blockedSignal);t.mock.timers.tick(34999);assert.equal(blockedSignal.aborted,false);t.mock.timers.tick(1);await settleUntil(()=>h.stream.getState().loading===0);
 assert.equal(blockedSignal.reason,'timeout');assert.equal(h.parseCalls,0);assert.equal(h.stream.stats.failed,1);assert.equal(h.stream.stats.requests,1);assert.equal(h.stream.getState().visible,0);assert.equal(h.owners.size,0);assert.equal(h.errors.length,1);assert(h.stream.records.get('deadline').retryAt>performance.now());
});

test('far view change still disposes a late parse after its network timer was cleared',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});const delayed=pendingValue(),h=await deadlineFar(t,{parse:()=>delayed.promise});h.start();await settleUntil(()=>h.parseCalls===1);t.mock.timers.tick(35001);
 h.stream.update({lng:123,lat:31,zoom:18,mode:'walk'},true);assert.equal(h.calls[0].signal.reason,'view-changed');delayed.resolve(h.model);await settleUntil(()=>h.stream.getState().loading===0);
 assert.deepEqual(h.removed,[h.model]);assert.equal(h.stream.stats.discarded,1);assert.equal(h.stream.getState().loaded,0);assert.equal(h.objects.size,0);assert.equal(h.owners.size,0);
});
