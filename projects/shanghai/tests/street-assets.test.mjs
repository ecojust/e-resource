import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import * as THREE from '../vendor/three.module.js';
import {loadStreetAssets} from '../src/street-assets.js';
import {StreetInteraction} from '../src/street-interaction.js';

const project=new URL('../',import.meta.url);
const records=JSON.parse(readFileSync(new URL('data/scene-props.json',project)));
const published=records.find(record=>record.id==='bund-streets');
assert.ok(published,'the published street owner is part of this integration fixture');
const modelBytes=readFileSync(new URL(published.model,project));
const interactionBytes=readFileSync(new URL(published.interaction_file,project));
const greeneryBytes=readFileSync(new URL('data/bund/greenery-v4.5.json',project));
const sourceInteraction=JSON.parse(interactionBytes);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const jsonBytes=value=>Buffer.from(JSON.stringify(value));
const documentBase='https://shanghai.test/project/index.html';

function setup(t,{model=modelBytes,interaction=interactionBytes,greenery=greeneryBytes,record={},deferBodies=[]}={}) {
  const descriptor=Object.getOwnPropertyDescriptor(globalThis,'document');
  Object.defineProperty(globalThis,'document',{configurable:true,value:{baseURI:documentBase}});
  t.after(()=>{
    if(descriptor)Object.defineProperty(globalThis,'document',descriptor);
    else delete globalThis.document;
  });
  const current={...published,url:published.model,...record};
  const modelURL=new URL(current.url,documentBase).href;
  const interactionURL=new URL(current.interaction_file,documentBase).href;
  const greeneryURL=new URL('../data/bund/greenery-v4.5.json',import.meta.url).href;
  const assets=new Map([[modelURL,model],[interactionURL,interaction],[greeneryURL,greenery]]);
  const requested=[],pendingBodies=new Map();
  const assetURLs={model:modelURL,interaction:interactionURL,greenery:greeneryURL};
  const deferredURLs=new Set(deferBodies.map(name=>assetURLs[name]));
  t.mock.method(globalThis,'fetch',async(url,options)=>{
    const href=String(url);requested.push(href);
    assert.ok(options?.signal instanceof AbortSignal,'all street requests have an abort deadline');
    assert.ok(assets.has(href),`unexpected asset request: ${href}`);
    const value=assets.get(href);
    if(value instanceof Error)throw value;
    if(value===null)return new Response('unavailable',{status:503});
    if(deferredURLs.has(href))return {ok:true,status:200,arrayBuffer:()=>new Promise((resolve,reject)=>{
      const signal=options.signal,abort=()=>reject(signal.reason);
      if(signal.aborted){abort();return;}
      signal.addEventListener('abort',abort,{once:true});
      pendingBodies.set(href,()=>{
        signal.removeEventListener('abort',abort);
        resolve(value.buffer.slice(value.byteOffset,value.byteOffset+value.byteLength));
      });
    })};
    return new Response(value,{status:200});
  });
  const scene=new THREE.Group(),ground=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());
  ground.name='verified street GLB placeholder';scene.add(ground);
  const parsed=[];
  const loader={async parseAsync(bytes,base){
    parsed.push({bytes,base});
    assert.deepEqual(Buffer.from(bytes),modelBytes,'only the exact verified model reaches the decoder');
    assert.equal(base,new URL('.',modelURL).href);
    return {scene};
  }};
  t.after(()=>{
    scene.userData.streetAssembly?.greenery?.dispose();
    ground.geometry.dispose();ground.material.dispose();
  });
  const warnings=[];
  return {scene,ground,parsed,requested,warnings,current,pendingBodies,
    finishBody:name=>{const finish=pendingBodies.get(assetURLs[name]);assert.ok(finish,`body is pending: ${name}`);finish();},
    load:()=>loadStreetAssets({THREE,loader,record:current,onWarning:error=>warnings.push(error.message)})};
}

function assertRetainedStreetWithoutTrees(context,data) {
  assert.equal(data.scene,context.scene);
  assert.equal(context.parsed.length,1);
  assert.equal(context.ground.parent,data.scene,'the verified base GLB remains attached');
  const assembly=data.scene.userData.streetAssembly;
  assert.equal(assembly.greenery,null);
  assert.ok(assembly.interaction,'a greenery-only failure must not remove verified terrain');
  assert.deepEqual(assembly.interaction.features,sourceInteraction.features);
  const expected=sourceInteraction.local_obstacles.filter(obstacle=>obstacle.kind!=='tree');
  assert.equal(sourceInteraction.local_obstacles.length-expected.length,7,'fixture includes seven invisible-tree failure cases');
  assert.deepEqual(assembly.interaction.local_obstacles,expected,'remove only tree proxies, retaining all actual street furniture');
  assert.equal(data.scene.children.length,1,'failed greenery is not attached as an empty alternate owner');
  const interaction=new StreetInteraction();
  assert.equal(interaction.setOwner(published.id,assembly.interaction,{modelSha256:assembly.modelSha256,active:true}),true);
  assert.equal(interaction.getState().activeOwners,1,'the verified street terrain can still activate');
  interaction.clear();
}

test('a model byte/SHA mismatch is rejected before any GLB parse or attachment',async t=>{
  const altered=Buffer.from(modelBytes);altered[altered.length-1]^=1;
  const context=setup(t,{model:altered});
  await assert.rejects(context.load(),/街景模型校验值不符/);
  assert.equal(context.parsed.length,0);
  assert.equal(context.scene.userData.streetAssembly,undefined);
});

test('sidecar JSON must match original bytes, not merely the same parsed object',async t=>{
  const rewritten=jsonBytes(sourceInteraction);
  assert.deepEqual(JSON.parse(rewritten),sourceInteraction);
  assert.notEqual(sha(rewritten),published.interaction_sha256,'serialization changes the integrity-bound bytes');
  const context=setup(t,{interaction:rewritten,greenery:null});
  const data=await context.load();
  assert.equal(context.parsed.length,1);
  assert.equal(data.scene.userData.streetAssembly.interaction,null,'unverified ground is never exposed for activation');
  assert.ok(context.warnings.some(message=>message.includes('街景地面数据校验值不符')));
});

test('a correctly hashed sidecar bound to a different model cannot activate ground',async t=>{
  const changed={...sourceInteraction,web_model_sha256:'0'.repeat(64)};
  const bytes=jsonBytes(changed);
  const context=setup(t,{interaction:bytes,record:{interaction_sha256:sha(bytes)},greenery:null});
  const data=await context.load();
  assert.equal(data.scene.userData.streetAssembly.interaction,null);
  assert.ok(context.warnings.some(message=>message.includes('街景地面与模型版本不一致')));
  assert.equal(context.ground.parent,data.scene,'the independently verified base model still displays');
});

test('a failed sidecar request leaves the base model usable without unverified ground',async t=>{
  const context=setup(t,{interaction:new Error('sidecar network unavailable'),greenery:null});
  const data=await context.load();
  assert.equal(context.parsed.length,1);
  assert.equal(data.scene.userData.streetAssembly.interaction,null);
  assert.ok(context.warnings.includes('sidecar network unavailable'));
});

test('greenery network failure retains street and terrain but removes exactly seven tree proxies',async t=>{
  const context=setup(t,{greenery:new Error('greenery network unavailable')});
  assertRetainedStreetWithoutTrees(context,await context.load());
  assert.deepEqual(context.warnings,['greenery network unavailable']);
});

test('greenery JSON byte/SHA mismatch retains terrain without invisible tree collision',async t=>{
  const rewritten=jsonBytes(JSON.parse(greeneryBytes));
  assert.notEqual(sha(rewritten),sourceInteraction.greenery_data_sha256);
  const context=setup(t,{greenery:rewritten});
  assertRetainedStreetWithoutTrees(context,await context.load());
  assert.ok(context.warnings.some(message=>message.includes('绿化位置校验值不符')));
});

test('verified actual fixture attaches real Three instances beneath one street owner',async t=>{
  assert.equal(sha(modelBytes),published.web_sha256);
  assert.equal(sha(interactionBytes),published.interaction_sha256);
  assert.equal(sourceInteraction.web_model_sha256,published.web_sha256);
  assert.equal(sha(greeneryBytes),sourceInteraction.greenery_data_sha256);
  const context=setup(t);
  const data=await context.load();
  assert.deepEqual(context.warnings,[]);
  assert.equal(context.parsed.length,1);
  assert.equal(context.requested.length,3,'no second owner, texture fetch, or extra asynchronous asset loader');
  const assembly=data.scene.userData.streetAssembly;
  assert.equal(assembly.modelSha256,published.web_sha256);
  assert.equal(assembly.interaction.owner,published.id);
  assert.deepEqual(assembly.interaction,sourceInteraction);
  assert.equal(assembly.greenery.group.parent,data.scene,'instances inherit the verified street owner transform and lifetime');
  assert.equal(data.scene.children.length,2);
  assert.equal(assembly.greenery.stats.trees,7);
  assert.ok(assembly.greenery.group.children.length>0);
  assert.ok(assembly.greenery.group.children.every(mesh=>mesh instanceof THREE.InstancedMesh));
  assert.equal(assembly.greenery.stats.externalTextures,0);
  assert.deepEqual(assembly.greenery.locations,JSON.parse(greeneryBytes).trees.map(({lng,lat})=>({lng,lat})));
  const interaction=new StreetInteraction();
  assert.equal(interaction.setOwner(published.id,assembly.interaction,{modelSha256:assembly.modelSha256,active:false}),true);
  assert.equal(interaction.getState().activeOwners,0);
  interaction.setOwnerActive(published.id,true);
  assert.equal(interaction.getState().activeOwners,1);
  interaction.removeOwner(published.id);
  assert.equal(interaction.getState().activeOwners,0,'one owner removal disables all loaded street proxies');
});


// Controlled AbortSignal deadlines exercise real fetch/body abort behavior
// without making the regression suite wait 35 seconds of wall-clock time.
function deadlineClock(t) {
  let current=0;
  const timers=[];
  t.mock.method(AbortSignal,'timeout',duration=>{
    const controller=new AbortController();
    timers.push({at:current+duration,controller});
    return controller.signal;
  });
  return {advanceTo(time){
    assert.ok(time>=current);current=time;
    for(const timer of timers)if(timer.at<=current&&!timer.controller.signal.aborted)
      timer.controller.abort(new DOMException('signal timed out','TimeoutError'));
  }};
}
const flushAsync=()=>new Promise(resolve=>setImmediate(resolve));

test('successful optional bodies arriving after 12 seconds still build one complete street assembly',async t=>{
  const clock=deadlineClock(t);
  const context=setup(t,{deferBodies:['interaction','greenery']});
  const loading=context.load();
  await flushAsync();
  assert.equal(context.pendingBodies.size,2,'both optional responses reached HTTP 200 while their bodies are pending');
  clock.advanceTo(20000);
  context.finishBody('interaction');context.finishBody('greenery');
  const data=await loading,assembly=data.scene.userData.streetAssembly;
  assert.deepEqual(context.warnings,[]);
  assert.equal(context.requested.length,3,'no resource is retried or downloaded twice');
  assert.equal(context.parsed.length,1,'the verified base is parsed once');
  assert.equal(assembly.interaction.owner,published.id);
  assert.equal(assembly.greenery.stats.trees,7);
  assert.equal(assembly.greenery.group.parent,data.scene);
  assert.equal(data.scene.children.length,2,'one base and one attached greenery group');
  const interaction=new StreetInteraction();
  assert.equal(interaction.setOwner(published.id,assembly.interaction,{modelSha256:assembly.modelSha256,active:true}),true);
  assert.equal(interaction.getState().owners,1);
  assert.equal(interaction.getState().activeOwners,1);
  interaction.clear();
});

test('a greenery body still hanging at 35 seconds falls back without invisible tree collision or retries',async t=>{
  const clock=deadlineClock(t);
  const context=setup(t,{deferBodies:['greenery']});
  let settled=false;
  const loading=context.load().then(value=>{settled=true;return value;});
  await flushAsync();
  assert.equal(context.pendingBodies.size,1,'HTTP 200 alone does not complete a pending body');
  clock.advanceTo(34999);await flushAsync();
  assert.equal(settled,false,'the bounded network budget has not expired yet');
  clock.advanceTo(35000);
  assertRetainedStreetWithoutTrees(context,await loading);
  assert.deepEqual(context.warnings,['signal timed out']);
  assert.equal(context.requested.length,3,'a network hang does not restart any owner or request');
});
