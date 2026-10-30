import test from 'node:test';
import assert from 'node:assert/strict';
import {CityDetailStreamer} from '../src/city-detail-streamer.js';
import {CandidateCityClipper} from '../src/candidate-city-clipping.js';
import {disposeModelResources} from '../src/model-resources.js';
import {THREE,FAR,fixture,farObject} from './ordinary-fixtures.mjs';

function harness(t,{memoryBudget=1024*1024,registerParent=true}={}){
  const data=fixture(),scene=new THREE.Scene(),container=new THREE.Group(),object=farObject();
  scene.add(container);container.add(object);
  const clips=new CandidateCityClipper({THREE,geographicPosition:(x,y)=>new THREE.Vector3(x,0,y)});
  clips.update([{geometry:{type:'Polygon',coordinates:[[[0,0],[2,0],[2,2],[0,2],[0,0]]]},owner:{macro_id:data.macro,feature_local_id:1}}]);
  const events=[],errors=[],textures=[];
  const observedTHREE={...THREE,DataTexture:class extends THREE.DataTexture{
    constructor(...args){super(...args);const record={texture:this,disposed:0};textures.push(record);this.addEventListener('dispose',()=>record.disposed++);}
  }};
  const streamer=new CityDetailStreamer({THREE:observedTHREE,scene,memoryBudget,retryDelayMs:0,
    loader:{parseAsync(){assert.fail('index recovery must not start a near model without a view');}},
    prepareObject(){},disposeObject(model){clips.releaseObject(model);scene.remove(model);disposeModelResources(model);},
    beforeFarRebind(far){events.push(['before',far]);clips.releaseObject(far);},
    afterFarRebind(far,record){events.push(['after',far]);clips.bindObject(far,record);},
    fetchFunction:async()=>new Response(JSON.stringify(data.index)),onError:error=>errors.push(error),
  });
  const record={id:data.macro,object,detailURL:'https://example.test/READY.json',sha256:FAR,buildingCount:2};
  const parent={id:record.id,object,url:record.detailURL,active:true,records:[],status:'idle',retryAt:0};
  if(registerParent)streamer.parents.set(object,parent);
  clips.bindObject(object,record);
  t.after(()=>{streamer.destroy();clips.dispose();disposeModelResources(object);});
  return {data,scene,container,object,clips,streamer,parent,record,events,errors,textures};
}

function assertLiveClipping(h,{mask=null}={}){
  assert.equal(h.clips.objects.has(h.object),true,'the live far object must retain its clipping owner');
  const mesh=h.object.children[0];
  for(const [material,kind] of [[mesh.material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']]){
    assert(material,`${kind} material remains available`);
    const lib=THREE.ShaderLib[kind],shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:{}};
    material.onBeforeCompile(shader,{});
    assert.equal(shader.uniforms.candidateClipTexture?.value,h.clips.texture,`${kind}: current clipping texture`);
    assert.equal(shader.uniforms.candidateClipCount?.value,2);
    assert.equal(shader.uniforms.candidateHasFeatureIds?.value,1);
    assert.equal(shader.vertexShader.split('varying vec3 vCandidatePosition;').length-1,1,'never duplicate clipping hooks');
    if(mask)assert.equal(shader.uniforms.cityFeatureMask?.value,mask.texture,`${kind}: retry uses the new live mask`);
    else assert.equal(shader.uniforms.cityFeatureMask,undefined,`${kind}: disposed mask is not retained in the restored shader`);
  }
}

test('mask budget failure before binding preserves candidate clipping on the live far object',async t=>{
  const h=harness(t,{memoryBudget:4});assertLiveClipping(h);
  const mesh=h.object.children[0],hook=mesh.material.onBeforeCompile,depth=mesh.customDepthMaterial,distance=mesh.customDistanceMaterial;
  await h.streamer.loadIndex(h.parent);
  assert.equal(h.errors.length,1);assert.match(h.errors[0].message,/memory budget/);
  assert.equal(h.parent.status,'idle');assert.equal(h.parent.mask??null,null);
  assert.equal(h.textures.length,1);assert.equal(h.textures[0].disposed,1);
  assert.deepEqual(h.events,[],'failure before binding must not disturb the existing candidate hooks');
  assert.equal(mesh.material.onBeforeCompile,hook);assert.equal(mesh.customDepthMaterial,depth);assert.equal(mesh.customDistanceMaterial,distance);
  assertLiveClipping(h);
});

test('post-assignment failure clears the disposed mask, restores clipping and retries with a fresh mask',async t=>{
  const h=harness(t),original=h.streamer.applyVisibleLandmarks;let failedMask,fail=true;
  h.streamer.applyVisibleLandmarks=function(parent){
    if(fail){fail=false;failedMask=parent.mask;assert(failedMask);throw Error('injected visibility failure');}
    return original.call(this,parent);
  };
  await h.streamer.loadIndex(h.parent);
  assert.equal(h.errors.length,1);assert.match(h.errors[0].message,/injected visibility failure/);
  assert.equal(failedMask.disposed,true);assert.equal(h.parent.mask,null);assert.equal(h.parent.status,'idle');
  assert.equal(h.textures[0].disposed,1);assert.equal(h.streamer.records.size,0);assert.equal(h.parent.records.length,0);
  assert.deepEqual(h.events.map(([name])=>name),['before','after','before','after']);
  assertLiveClipping(h);
  await h.streamer.loadIndex(h.parent);
  assert.equal(h.parent.status,'ready');assert(h.parent.mask);assert.notEqual(h.parent.mask,failedMask);
  assert.equal(h.parent.mask.disposed,false);assert.equal(h.textures.length,2);assert.equal(h.textures[1].disposed,0);
  assert.equal(h.streamer.records.size,1);assert.equal(h.errors.length,1);
  assertLiveClipping(h,{mask:h.parent.mask});
});

test('selection failure rolls back newly registered records and wanted requests before a clean retry',async t=>{
  const h=harness(t),original=h.streamer.select;let failedMask,abortedController,failedRecord,fail=true;
  h.streamer.select=function(){
    if(fail){
      fail=false;failedMask=h.parent.mask;
      failedRecord=[...this.records][0];assert(failedRecord,'selection starts after index records are registered');
      this.wanted.add(failedRecord);abortedController=new AbortController();
      this.inflight={record:failedRecord,controller:abortedController};
      throw Error('injected partial selection failure');
    }
    return original.call(this);
  };
  await h.streamer.loadIndex(h.parent);
  assert.equal(h.errors.length,1);assert.match(h.errors[0].message,/partial selection failure/);
  assert.equal(abortedController.signal.aborted,true,'the partially started near request must be cancelled');
  assert.equal(failedMask.disposed,true);assert.equal(h.parent.mask,null);assert.equal(h.parent.records.length,0);
  assert.equal(h.streamer.records.size,0);assert.equal(h.streamer.wanted.size,0);
  assertLiveClipping(h);
  // The request completion would clear its own slot after observing the abort.
  h.streamer.inflight=null;
  await h.streamer.loadIndex(h.parent);
  assert.equal(h.parent.status,'ready');assert.notEqual(h.parent.mask,failedMask);
  assert.equal(h.streamer.records.size,1);assert.equal(h.parent.records.length,1);
  assert.notEqual(h.parent.records[0],failedRecord);assert.equal(h.errors.length,1);
  assertLiveClipping(h,{mask:h.parent.mask});
});

for(const action of ['removed from scene','detached parent','destroyed streamer'])
  test(`post-assignment failure does not rebind an object after it is ${action}`,async t=>{
    const h=harness(t);let failedMask;
    h.streamer.applyVisibleLandmarks=function(parent){
      failedMask=parent.mask;assert(failedMask);
      if(action==='removed from scene')h.object.removeFromParent();
      else if(action==='detached parent')this.detach(h.object);
      else this.destroy();
      throw Error(`injected failure: ${action}`);
    };
    await h.streamer.loadIndex(h.parent);
    assert.equal(failedMask.disposed,true);
    assert.equal(h.parent.mask,null,'the failed mask must not survive cleanup even on detached parent records');
    assert.equal(h.clips.objects.has(h.object),false);
    assert.equal(h.clips.bindings.size,0);
    assert.equal(h.events.filter(([name])=>name==='after').length,1,'only the initial successful bind occurred, never a cleanup resurrection');
    assert.equal(h.textures[0].disposed,1);
  });

test('prepareFarObject failure cleans up and propagates without rebinding a model the loader will discard',t=>{
  const h=harness(t,{registerParent:false});
  h.streamer.setReplacementOverrides(h.data.registry,'https://example.test/');
  let failedMask;
  h.streamer.applyVisibleLandmarks=function(parent){failedMask=parent.mask;throw Error('injected prepare failure');};
  assert.throws(()=>h.streamer.prepareFarObject(h.object,h.record),/injected prepare failure/);
  assert(failedMask);assert.equal(failedMask.disposed,true);
  assert.equal(h.streamer.parents.has(h.object),false);assert.equal(h.clips.objects.has(h.object),false);
  assert.equal(h.clips.bindings.size,0);assert.equal(h.textures[0].disposed,1);
  assert.equal(h.events.filter(([name])=>name==='after').length,0);
});
