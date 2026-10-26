import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import * as THREE from '../vendor/three.module.js';
import {OrdinaryCityDetailStreamer as CityDetailStreamer} from '../src/ordinary-city-detail-streamer.js';
import {LocalModelStreamer} from '../src/local-model-streamer.js';
import {disposeModelResources} from '../src/model-resources.js';

const HASH='a'.repeat(64),CONFIG='b'.repeat(64),BASE='c'.repeat(64),DECODED='d'.repeat(64);
const UUID='building:480cfef1-55ad-4830-9cfc-b41459f0c76b';
const bytes=new TextEncoder().encode('independently checked override fixture');
const sha=createHash('sha256').update(bytes).digest('hex');
const bounds=[121,31,121.0001,31.0001],view={lng:121,lat:31,zoom:18,mode:'walk'};
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(test){const deadline=performance.now()+2000;while(!test()){if(performance.now()>deadline)throw Error('precise fixture timed out');await delay(2);}}
function deferred(){let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};}
function far(){const group=new THREE.Group(),g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,1,0,0,0,1,0,2,0,0,3,0,0,2,1,0],3));g.setAttribute('_feature_id_0',new THREE.Float32BufferAttribute([1,1,1,2,2,2],1));group.add(new THREE.Mesh(g,new THREE.MeshStandardMaterial()));return group;}
function near(){const root=new THREE.Group(),target=new THREE.Group();target.name='target-05';target.userData.cityReplacement={macro_id:'macro',landmark_id:'bund05',local_ids:[1],feature_keys:[UUID]};target.add(new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial()));root.add(target,new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial()));return root;}
function registry(){return {schema:'city-precise-overrides-v1',complete:true,macros:[{id:'macro',feature_count:2,baseline_configuration_sha256:CONFIG,baseline_far_sha256:HASH,near:[{id:'n',baseline_file:'near.glb.gz',baseline_sha256:BASE,baseline_decoded_sha256:DECODED,featureLocalIds:[1,2],model:{file:'assets/city-detail/overrides-v6/n.glb',sha256:sha,size_bytes:bytes.length,expandedTriangles:24,geometryBytes:10000},groups:[{name:'target-05',landmark_id:'bund05',local_ids:[1],feature_keys:[UUID],expandedTriangles:12}]}]}]};}
function index(){return {configuration_sha256:CONFIG,feature_count:2,far:{sha256:HASH},near:[{id:'n',file:'near.glb.gz',sha256:BASE,decoded_sha256:DECODED,decoded_size_bytes:1000,content_encoding:'gzip',size_bytes:100,featureLocalIds:[1,2],geographic_bbox:bounds,expandedTriangles:24,geometryBytes:10000}]};}
function harness(t,{metadata=index(),fetchModel,parse=()=>near()}={}){
 const scene=new THREE.Scene(),object=far(),errors=[],disposed=[],calls=[];
 const record={id:'macro',object,detailURL:'https://example.test/assets/city-detail/macros/macro/READY.json',sha256:HASH,buildingCount:2};
 const streamer=new CityDetailStreamer({THREE,scene,loader:{async parseAsync(){return {scene:await parse()};}},prepareObject:()=>{},disposeObject(o){disposed.push(o);scene.remove(o);disposeModelResources(o);},onError:e=>errors.push(e.message),retryDelayMs:60000,
  fetchFunction:async(url,{signal})=>{calls.push(url);return url.endsWith('READY.json')?new Response(JSON.stringify(metadata)):fetchModel?fetchModel(url,signal):new Response(bytes);}});
 streamer.setReplacementOverrides(registry(),'https://example.test/');streamer.prepareFarObject(object,record);
 t.after(()=>streamer.destroy());
 return {streamer,record,object,errors,disposed,calls,get parent(){return streamer.parents.get(object);},activate(){streamer.update(view);streamer.syncParents([record]);}};
}

test('precise far owner is acquired before the first far visibility and survives delayed index',async t=>{
 const h=harness(t);h.streamer.setVisibleLandmarks(['bund05','legacy-landmark']);assert.equal(h.parent.mask.data[1],255);assert.equal(h.parent.mask.data[2],0);
 h.activate();await until(()=>h.streamer.getState().visible===1);
 const record=[...h.streamer.records][0];assert.equal(record.replacementGroups[0].object.visible,false);assert.equal(record.object.children[1].visible,true);
 assert.deepEqual(h.streamer.getState().precise.visible,['bund05']);assert.match(h.calls[1],/^https:\/\/example.test\/assets\/city-detail\/overrides-v6\//);
 h.streamer.setVisibleLandmarks([]);assert.equal(record.replacementGroups[0].object.visible,true);
 assert.equal(h.parent.mask.data[1],255,'near owner still masks the far target');assert.equal(h.parent.mask.data[2],255);
 h.streamer.syncParents([]);assert.equal(h.parent.mask.data[1],0);assert.equal(h.parent.mask.data[2],0);
});

test('near unload releases only near ownership; visible landmark still hides only its far feature',async t=>{
 const h=harness(t);h.activate();await until(()=>h.streamer.getState().visible===1);h.streamer.setVisibleLandmarks(['bund05']);h.streamer.syncParents([]);
 assert.equal(h.parent.mask.data[1],255);assert.equal(h.parent.mask.data[2],0);h.streamer.setVisibleLandmarks([]);assert.equal(h.parent.mask.data[1],0);
 h.streamer.syncParents([h.record]);assert.equal(h.streamer.getState().visible,1);assert.equal([...h.streamer.records][0].replacementGroups[0].object.visible,true);
});

test('override fetch failure preserves every far neighbor and can later retry without base opaque near',async t=>{
 let fail=true;const h=harness(t,{fetchModel:()=>fail?new Response('',{status:503}):new Response(bytes)});h.activate();await until(()=>h.errors.length===1);
 assert.equal(h.streamer.getState().visible,0);assert.equal(h.parent.mask.data[1],0);assert.equal(h.parent.mask.data[2],0);assert(!h.calls.some(url=>url.endsWith('/near.glb.gz')));
 h.streamer.setVisibleLandmarks(['bund05']);assert.equal(h.parent.mask.data[1],255);assert.equal(h.parent.mask.data[2],0);
 fail=false;[...h.streamer.records][0].retryAt=0;h.streamer.update(view);await until(()=>h.streamer.getState().visible===1);
 assert.equal([...h.streamer.records][0].replacementGroups[0].object.visible,false);
});

for(const defect of ['missing owner','wrong keys','partial target','unknown owner','nested owner'])test(`reject ${defect} without acquiring a near mask`,async t=>{
 const model=near(),target=model.children[0];
 if(defect==='missing owner')delete target.userData.cityReplacement;
 if(defect==='wrong keys')target.userData.cityReplacement.feature_keys=['building:ffffffff-ffff-ffff-ffff-ffffffffffff'];
 if(defect==='partial target')target.children[0].geometry.setDrawRange(0,3);
 if(defect==='unknown owner')target.name='unexpected';
 if(defect==='nested owner'){const extra=target.clone();extra.name='nested';target.add(extra);}
 const h=harness(t,{parse:()=>model});h.activate();await until(()=>h.errors.length===1);assert(h.disposed.includes(model));assert.equal(h.parent.mask.data[1],0);assert.equal(h.parent.mask.data[2],0);assert.equal(h.streamer.getState().visible,0);
});

test('late parse reflects current landmark state and cannot revive a detached parent',async t=>{
 const p=deferred(),h=harness(t,{parse:()=>p.promise});h.activate();await until(()=>h.calls.length===2);h.streamer.setVisibleLandmarks(['bund05']);h.streamer.setVisibleLandmarks([]);
 p.resolve(near());await until(()=>h.streamer.getState().visible===1);assert.equal([...h.streamer.records][0].replacementGroups[0].object.visible,true);
 const mask=h.parent.mask;h.streamer.detach(h.object);assert.equal(mask.disposed,true);h.streamer.setVisibleLandmarks(['bund05']);assert.equal(h.streamer.parents.size,0);
});

test('baseline SHA and complete local ownership are checked before replacing near',async t=>{
 const metadata=index();metadata.near[0].sha256='e'.repeat(64);const h=harness(t,{metadata});h.activate();await until(()=>h.errors.length===1);assert.match(h.errors[0],/source ownership or checksum/);assert.equal(h.calls.length,1);assert.equal(h.parent.mask.data[1],0);
});

test('registry rejects duplicate ownership atomically and far preparation rejects absent/wrong hash',t=>{
 const h=harness(t),other=new CityDetailStreamer({THREE,scene:new THREE.Scene(),loader:{},prepareObject:()=>{},disposeObject:()=>{}});t.after(()=>other.destroy());
 const bad=registry();bad.macros[0].near[0].groups.push({...bad.macros[0].near[0].groups[0],name:'duplicate'});
 assert.throws(()=>other.setReplacementOverrides(bad,'https://example.test/'),/multiple landmark owners/);assert.equal(other.replacementRegistryInstalled,false);
 other.setReplacementOverrides(registry(),'https://example.test/');assert.throws(()=>other.prepareFarObject(far(),{...h.record,sha256:undefined}),/baseline differs/);assert.equal(other.parents.size,0);
 assert.throws(()=>h.streamer.setReplacementOverrides(registry(),'https://example.test/'),/before city loading/);
});

test('local city record retains the manifest SHA for precise namespace binding',async t=>{
 const streamer=new LocalModelStreamer({scene:new THREE.Scene(),loader:{},suppression:{async clear(){},destroy(){},getState(){return {pending:0};}},prepareObject:()=>{},disposeObject:()=>{}});t.after(()=>streamer.destroy());
 await streamer.setManifest({tiles:[{id:'macro',file:'far.glb',sha256:HASH,origin_longitude:121,origin_latitude:31,geographic_bbox:bounds,building_count:2}]},'https://example.test/');
 assert.equal(streamer.records.get('macro').sha256,HASH);
});
