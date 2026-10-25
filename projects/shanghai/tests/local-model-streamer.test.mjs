import assert from 'node:assert/strict';
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
