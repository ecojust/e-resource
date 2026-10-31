import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../vendor/three.module.js';
import {CandidateCityClipper} from '../src/candidate-city-clipping.js';

const MACRO='14-13719-6694',CATHAY=[2101,3146,3170],EAST=[2122,895,848,2805];
const geometry={type:'Polygon',coordinates:[[[0,0],[2,0],[2,2],[0,2],[0,0]]]};
const clip=(localId=3146,macro=MACRO)=>({geometry,owner:{macro_id:macro,feature_local_id:localId}});
function harness(t,{ids=CATHAY,featureIds=false,initial=[clip()]}={}){
  const clipper=new CandidateCityClipper({THREE,geographicPosition:(x,y)=>new THREE.Vector3(x,0,y)});
  const group=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());
  if(featureIds)mesh.geometry.setAttribute('_feature_id_0',new THREE.Float32BufferAttribute(new Float32Array(mesh.geometry.getAttribute('position').count).fill(3146),1));
  group.add(mesh);clipper.update(initial);
  const record={id:`${MACRO}/near-fixture`,parent:{id:MACRO}};if(ids!==null)record.ids=ids;
  clipper.bindObject(group,record);
  t.after(()=>{clipper.dispose();mesh.geometry.dispose();mesh.material.dispose();});
  return {clipper,group,mesh,record};
}
function shaders(mesh){
  return [[mesh.material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']].map(([material,kind])=>{
    const library=THREE.ShaderLib[kind],shader={vertexShader:library.vertexShader,fragmentShader:library.fragmentShader,uniforms:{}};
    material.onBeforeCompile(shader,{});return shader;
  });
}
function ownerIds(shader){
  const count=shader.uniforms.candidateClipCount.value,data=shader.uniforms.candidateClipTexture.value.image.data;
  return Array.from({length:count},(_,i)=>data[i*16+12]);
}

test('an untagged eastern near group excludes Cathay clipping in visible and shadow passes',t=>{
  const {clipper,mesh}=harness(t,{ids:EAST});
  for(const shader of shaders(mesh)){
    assert.equal(shader.uniforms.candidateHasFeatureIds.value,0);
    assert.notEqual(shader.uniforms.candidateClipTexture.value,clipper.texture);
    assert.equal(shader.uniforms.candidateClipCount.value,0);
    assert.deepEqual(ownerIds(shader),[]);
  }
  assert.deepEqual(clipper.getState().ownerScopedSources[0].feature_local_ids,EAST);
  assert.equal(clipper.getState().ownerScopedSources[0].triangles,0);
});

test('the shared Cathay near group receives its whole clip while excluding other groups and macros',t=>{
  const {clipper,mesh}=harness(t,{initial:[clip(),clip(2122),clip(3146,'another-macro')]});
  assert.equal(clipper.getState().triangles,6);
  for(const shader of shaders(mesh)){
    assert.equal(shader.uniforms.candidateClipCount.value,2);
    assert.deepEqual(ownerIds(shader),[3146,3146]);
  }
  assert.deepEqual(clipper.getState().ownerScopedSources[0].clip_feature_local_ids,[3146]);
});

test('ownerless wildcard clips retain prior spatial behavior while still respecting macro ownership',t=>{
  const {mesh}=harness(t,{ids:EAST,initial:[{geometry},clip(0),clip(0,'another-macro')]});
  for(const shader of shaders(mesh)){
    assert.equal(shader.uniforms.candidateClipCount.value,4);
    assert.deepEqual(ownerIds(shader),[0,0,0,0]);
  }
});

test('late candidate activation and removal update already compiled near material uniforms',t=>{
  const {clipper,mesh}=harness(t,{initial:[]}),compiled=shaders(mesh);
  assert(compiled.every(shader=>shader.uniforms.candidateClipCount.value===0));
  clipper.update([clip()]);
  assert(compiled.every(shader=>shader.uniforms.candidateClipCount.value===2));
  assert(compiled.every(shader=>ownerIds(shader).every(id=>id===3146)));
  clipper.update([clip(2122)]);
  assert(compiled.every(shader=>shader.uniforms.candidateClipCount.value===0));
  clipper.update([]);
  assert(compiled.every(shader=>shader.uniforms.candidateClipTexture.value.image.data.every(value=>value===0)));
});

test('per-vertex feature IDs retain the original global texture and shader owner comparison',t=>{
  const {clipper,mesh}=harness(t,{ids:EAST,featureIds:true});
  for(const shader of shaders(mesh)){
    assert.equal(shader.uniforms.candidateHasFeatureIds.value,1);
    assert.equal(shader.uniforms.candidateClipTexture.value,clipper.texture);
    assert.match(shader.vertexShader,/vCandidateFeatureId=_feature_id_0/);
    assert.match(shader.fragmentShader,/abs\(owner\.x-vCandidateFeatureId\)>0\.5/);
  }
  assert.deepEqual(clipper.getState().ownerScopedSources,[]);
});

for(const ids of [null,[]])test(`near objects with ${ids===null?'missing':'empty'} owner metadata retain prior spatial clipping`,t=>{
  const {clipper,mesh}=harness(t,{ids});
  for(const shader of shaders(mesh)){
    assert.equal(shader.uniforms.candidateClipTexture.value,clipper.texture);
    assert.equal(shader.uniforms.candidateClipCount.value,2);
    assert.equal(shader.uniforms.candidateHasFeatureIds.value,0);
  }
  assert.deepEqual(clipper.getState().ownerScopedSources,[]);
});

test('release disposes the scoped texture and rebind updates cached shader holders without recompilation',t=>{
  const {clipper,group,mesh,record}=harness(t),compiled=shaders(mesh),oldTexture=compiled[0].uniforms.candidateClipTexture.value;
  let disposed=0;oldTexture.addEventListener('dispose',()=>disposed++);
  clipper.releaseObject(group);assert.equal(disposed,1);
  assert(compiled.every(shader=>shader.uniforms.candidateClipTexture.value===null));
  clipper.bindObject(group,{...record,ids:EAST});
  // Three may reuse the standard material's cached program without rerunning its hook.
  assert.notEqual(compiled[0].uniforms.candidateClipTexture.value,oldTexture);
  assert.equal(compiled[0].uniforms.candidateClipCount.value,0);
  assert.deepEqual(shaders(mesh).map(shader=>shader.uniforms.candidateClipCount.value),[0,0,0]);
  clipper.releaseObject(group);clipper.releaseObject(group);assert.equal(disposed,1);
  assert.deepEqual(clipper.getState().ownerScopedSources,[]);
});
