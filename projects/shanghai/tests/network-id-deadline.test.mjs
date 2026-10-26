import test from 'node:test';
import assert from 'node:assert/strict';
import {gzipSync} from 'node:zlib';
const {LocalModelStreamer}=await import(process.env.STREAMER_MODULE || '../src/local-model-streamer.js');

const turn=()=>new Promise(resolve=>setImmediate(resolve));
async function until(predicate){for(let i=0;i<2000&&!predicate();i++)await turn();assert(predicate(),'fixture did not settle');}
function pending(){let resolve;return {promise:new Promise(r=>resolve=r),resolve:value=>resolve(value)};}
const toBuffer=b=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);
const validIDs={building:['building-a','building-a','',null],building_part:['part-a',null]};
const rawIDs=toBuffer(new TextEncoder().encode(JSON.stringify(validIDs)));
const zippedIDs=toBuffer(gzipSync(Buffer.from(rawIDs)));
function delayedGzip(t){
 const Native=globalThis.DecompressionStream,gate=pending();let entered=false;
 globalThis.DecompressionStream=class{
  constructor(format){const native=new Native(format);return {writable:native.writable,
   readable:native.readable.pipeThrough(new TransformStream({async transform(chunk,controller){entered=true;await gate.promise;controller.enqueue(chunk);}}))};}
 };
 t.after(()=>{globalThis.DecompressionStream=Native;gate.resolve();});return {gate,get entered(){return entered;}};
}
async function fixture(t,{ids=zippedIDs,read,parse,missingIndex=false,inline=false}={}){
 const calls=[],errors=[],disposed=[],owners=new Map(),objects=new Set();let parses=0;
 const object={visible:true,traverse(callback){callback(this);}},scene={add:o=>objects.add(o)};
 const streamer=new LocalModelStreamer({scene,
  loader:{async parseAsync(){parses++;return {scene:parse?await parse():object};}},
  suppression:{async setOwner(owner,values){owners.set(owner,values);},async removeOwner(owner){owners.delete(owner);},getState:()=>({pendingStates:0}),async clear(){owners.clear();},destroy(){owners.clear();}},
  fetchFunction:async(url,{signal})=>{calls.push({url,signal});return {ok:true,arrayBuffer:()=>read?read(url,signal):Promise.resolve(url.endsWith('ids.gz')?ids:new ArrayBuffer(4))};},
  prepareObject(){},disposeObject(o){disposed.push(o);objects.delete(o);},onError:error=>errors.push(error),maxVisible:1,maxCache:1,concurrency:1});
 t.after(()=>streamer.destroy());
 await streamer.setManifest({tiles:[{id:'a',file:'far.glb',origin_longitude:121,origin_latitude:31,geographic_bbox:[121,31,121.001,31.001],size_bytes:4,triangles:1,
  ...(missingIndex?{}:inline?{featureIds:['inline-a']}:{feature_ids_file:'ids.gz'})}]},{baseURL:'https://test.invalid/'});
 return {streamer,calls,errors,disposed,owners,objects,object,get parses(){return parses;},start(){streamer.update({lng:121,lat:31,zoom:18,mode:'walk'},true);}};
}

for(const part of ['model','ids'])test(`pending raw ${part} body still aborts at exactly 35000ms`,async t=>{
 t.mock.timers.enable({apis:['setTimeout']});let blocked;
 const f=await fixture(t,{read:(url,signal)=>{
  if(url.endsWith(part==='model'?'far.glb':'ids.gz')){blocked=signal;return new Promise((_r,reject)=>signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')),{once:true}));}
  return Promise.resolve(url.endsWith('ids.gz')?zippedIDs:new ArrayBuffer(4));
 }});f.start();await until(()=>blocked);t.mock.timers.tick(34999);assert.equal(blocked.aborted,false);
 t.mock.timers.tick(1);await until(()=>f.streamer.inflight.size===0);
 assert.equal(blocked.reason,'timeout');assert.equal(f.streamer.stats.failed,1);assert.equal(f.parses,0);assert.equal(f.owners.size,0);assert.equal(f.errors.length,1);
});

test('received raw bytes survive slow actual gzip and subsequent JSON processing beyond network deadline',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});const delay=delayedGzip(t),f=await fixture(t);f.start();await until(()=>delay.entered);
 t.mock.timers.tick(35001);assert.ok(f.calls.every(c=>!c.signal.aborted));assert.equal(f.parses,0);
 delay.gate.resolve();await until(()=>f.streamer.inflight.size===0);
 assert.equal(f.streamer.stats.failed,0);assert.equal(f.streamer.stats.completed,1);assert.equal(f.parses,1);
 assert.deepEqual([...f.owners.values()][0],{building:['building-a'],building_part:['part-a']},'normalisation and invalid/duplicate ID filtering remain unchanged');
 assert.equal(f.errors.length,0);assert.equal(f.disposed.length,0);assert.equal(f.streamer.getState().visible,1);
});

test('deadline is already removed before JSON parsing starts',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});const f=await fixture(t,{ids:rawIDs}),original=JSON.parse;let inspected=false;
 t.mock.method(JSON,'parse',function(text,...rest){
  if(typeof text==='string'&&text.includes('building-a')){inspected=true;t.mock.timers.tick(35001);assert.ok(f.calls.every(c=>!c.signal.aborted));}
  return original(text,...rest);
 });
 f.start();await until(()=>f.streamer.inflight.size===0&&f.streamer.stats.completed===1);assert.equal(inspected,true);assert.equal(f.errors.length,0);
});

for(const reason of ['view','generation'])test(`${reason} change during slow ID decode does not publish an obsolete model or owner`,async t=>{
 t.mock.timers.enable({apis:['setTimeout']});const delay=delayedGzip(t),f=await fixture(t);f.start();await until(()=>delay.entered);
 if(reason==='view')f.streamer.update({lng:123,lat:31,zoom:18,mode:'walk'},true);else await f.streamer.reset();
 assert.ok(f.calls.every(c=>c.signal.aborted));delay.gate.resolve();await until(()=>f.streamer.inflight.size===0);
 assert.equal(f.parses,0);assert.equal(f.streamer.stats.cancelled,1);assert.equal(f.streamer.stats.failed,0);
 assert.equal(f.owners.size,0);assert.equal(f.objects.size,0);assert.equal(f.errors.length,0);
});

for(const [name,ids] of [['bad-gzip',zippedIDs.slice(0,12)],['bad-json',toBuffer(gzipSync(Buffer.from('{invalid-json')))]])test(`${name} remains a clear model failure after transport ends`,async t=>{
 t.mock.timers.enable({apis:['setTimeout']});const f=await fixture(t,{ids});f.start();await until(()=>f.streamer.inflight.size===0&&f.errors.length===1);
 assert.equal(f.streamer.stats.failed,1);assert.equal(f.parses,0);assert.equal(f.owners.size,0);assert.equal(f.objects.size,0);
 assert.match(f.errors[0].message,/分块暂不可用/);assert.doesNotMatch(f.errors[0].message,/Aborted/);
 assert.ok(f.calls.every(c=>c.signal.reason==='request-failed'));
});

test('late GLTF parse after a navigation change still disposes the stale object',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});const decode=pending();const f=await fixture(t,{parse:()=>decode.promise});f.start();await until(()=>f.parses===1);
 t.mock.timers.tick(35001);assert.ok(f.calls.every(c=>!c.signal.aborted));
 f.streamer.update({lng:123,lat:31,zoom:18,mode:'walk'},true);decode.resolve(f.object);await until(()=>f.streamer.inflight.size===0);
 assert.deepEqual(f.disposed,[f.object]);assert.equal(f.streamer.stats.discarded,1);assert.equal(f.owners.size,0);assert.equal(f.streamer.stats.failed,0);
});

test('missing feature index remains an explicit failure; inline IDs need no decoder',async t=>{
 const bad=await fixture(t,{missingIndex:true});bad.start();await until(()=>bad.errors.length===1&&bad.streamer.inflight.size===0);
 assert.match(bad.errors[0].message,/缺少建筑标识索引/);assert.equal(bad.parses,0);
 const good=await fixture(t,{inline:true});good.start();await until(()=>good.streamer.stats.completed===1&&good.streamer.inflight.size===0);
 assert.equal(good.calls.length,1);assert.deepEqual([...good.owners.values()][0],{building:['inline-a'],building_part:['inline-a']});
});
