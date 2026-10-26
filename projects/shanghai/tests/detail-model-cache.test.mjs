import test from 'node:test';
import assert from 'node:assert/strict';
import {MIB, detailIsNearby, estimateDetailResources, selectHiddenDetailEvictions,
  releaseHiddenDetail, retainDetailResult, detailCacheState} from '../src/detail-model-cache.js';

const object = children => ({visible:false,traverse(fn){for(const child of children)fn(child);}});
const texture = (width,height,extra={}) => ({isTexture:true,userData:{},source:{data:{width,height}},generateMipmaps:true,...extra});
const record = (id,bytes,{visible=false,wanted=false,photo=0,variant='full',used=1,unknown=0}={}) =>
  ({id,object:{visible},detailWanted:wanted,activeVariant:variant,lastDetailUsed:used,status:'loaded',
    resourceEstimate:{totalBytes:bytes,textureBytes:photo,unknownTextures:unknown}});

test('decoded photograph dimensions and mipmaps, not JPEG bytes, dominate the estimate',()=>{
  const map=texture(6000,4000), shared=texture(8192,8192,{userData:{shared:true}});
  const estimate=estimateDetailResources(object([{material:{map,roughnessMap:map,envMap:shared}}]));
  assert.equal(estimate.textureBytes,128000000);
  assert.equal(estimate.ownedTextures,1);
  assert.equal(estimate.unknownTextures,0);
  const rotated=estimateDetailResources(object([{material:{map:texture(4000,6000)}}]));
  assert.equal(rotated.textureBytes,estimate.textureBytes,'EXIF width/height swap preserves memory estimate');
});

test('shared/interleaved geometry, instance buffers, morphs and texture references count once',()=>{
  const positions=new Float32Array(18), indices=new Uint16Array(6), instances=new Float32Array(32), morph=new Float32Array(18);
  const interleaved={isInterleavedBufferAttribute:true,data:{array:positions}};
  const geometry={attributes:{position:interleaved,normal:interleaved},index:{array:indices},morphAttributes:{position:[{array:morph}]}};
  const owned=texture(8,8,{generateMipmaps:false});
  const e=estimateDetailResources(object([{geometry,isInstancedMesh:true,instanceMatrix:{array:instances},material:{map:owned}},{geometry,material:{map:owned}}]));
  assert.equal(e.geometryBytes,positions.byteLength+indices.byteLength+morph.byteLength);
  assert.equal(e.instanceBytes,instances.byteLength);
  assert.equal(e.textureBytes,256);
});

test('compressed mip chains and typed float images have explicit estimates',()=>{
  const compressed={isTexture:true,userData:{},isCompressedTexture:true,mipmaps:[{data:new Uint8Array(64)},{data:new Uint8Array(16)}]};
  const half=texture(8,8,{generateMipmaps:false,source:{data:{width:8,height:8,data:new Uint16Array(256)}}});
  const e=estimateDetailResources(object([{material:{map:compressed,normalMap:half}}]));
  assert.equal(e.textureBytes,80+512);
});

test('hidden photo/full is evicted before small cached LOD; visible full is protected',()=>{
  const visible=record('visible',200*MIB,{visible:true,wanted:true,photo:190*MIB});
  const photo=record('photo',100*MIB,{photo:96*MIB,used:30});
  const lod=record('lod',4*MIB,{variant:'distant',used:1});
  assert.deepEqual(selectHiddenDetailEvictions([visible,photo,lod],{maxCount:2,maxBytes:32*MIB}),[photo]);
});

test('count budget evicts the oldest ordinary hidden model and keeps recent entries',()=>{
  const a=record('a',MIB,{used:1}),b=record('b',MIB,{used:2}),c=record('c',MIB,{used:3});
  assert.deepEqual(selectHiddenDetailEvictions([c,b,a],{maxCount:2,maxBytes:32*MIB}),[a]);
});

test('two photographs exceeding hidden budget are both evicted, no large first-object exception',()=>{
  const a=record('a',100*MIB,{photo:96*MIB}),b=record('b',100*MIB,{photo:96*MIB});
  assert.deepEqual(selectHiddenDetailEvictions([a,b]).map(x=>x.id),['a','b']);
});

test('unknown-size hidden texture is not retained under a false zero-byte estimate',()=>{
  const unknown=estimateDetailResources(object([{material:{map:{isTexture:true,userData:{}}}}]));
  assert.equal(unknown.unknownTextures,1);
  const a=record('unknown',0,{unknown:1});
  assert.deepEqual(selectHiddenDetailEvictions([a]),[a]);
});

test('visibility fringe retains only already-visible models; it never preloads outside the enter range',()=>{
  assert.equal(detailIsNearby(101,100,false,300),false);
  assert.equal(detailIsNearby(399,100,true,300),true);
  assert.equal(detailIsNearby(400,100,true,300),false);
  assert.equal(detailIsNearby(NaN,100,true),false);
});

test('release resets to reloadable idle and does not unlock an in-flight upgrade',()=>{
  const r=record('one',100*MIB,{photo:90*MIB});r.loadingModel=true;const old=r.object;const released=[];
  assert.equal(releaseHiddenDetail(r,o=>released.push(o)),true);
  assert.deepEqual(released,[old]);assert.equal(r.object,null);assert.equal(r.status,'idle');
  assert.equal(r.loadingModel,true);assert.equal(r.activeVariant,null);assert.equal(r.resourceEstimate,null);
  assert.equal(releaseHiddenDetail(r,()=>assert.fail('double disposal')),false);
});

test('visible or wanted objects cannot be released even if a stale eviction list contains them',()=>{
  for(const r of [record('visible',MIB,{visible:true}),record('wanted',MIB,{wanted:true})]){
    assert.equal(releaseHiddenDetail(r,()=>assert.fail('visible disposal')),false);
  }
});

test('late unwanted result is disposed, does not replace an old object or unlock its request',()=>{
  const r=record('one',MIB);r.loadingModel=true;const old=r.object,newObject={};const disposed=[];
  assert.equal(retainDetailResult(r,newObject,{disposeObject:o=>disposed.push(o)}),false);
  assert.equal(r.object,old);assert.equal(r.status,'loaded');assert.equal(r.loadingModel,true);
  assert.deepEqual(disposed,[newObject]);
  r.detailWanted=true;
  assert.equal(retainDetailResult(r,{}, {disposeObject:()=>assert.fail()}),true);
  assert.equal(retainDetailResult(r,{}, {destroyed:true,disposeObject:()=>{}}),false);
});

test('diagnostics distinguish hidden budget from visible memory',()=>{
  const records=[record('visible',100*MIB,{visible:true,wanted:true,photo:96*MIB}),record('cached',MIB)];
  const state=detailCacheState(records,{maxCount:2,maxBytes:32*MIB},{evicted:3});
  assert.equal(state.hiddenEstimatedBytes,MIB);assert.equal(state.residentEstimatedBytes,101*MIB);
  assert.equal(state.visible,1);assert.equal(state.hidden,1);assert.equal(state.evicted,3);
});
