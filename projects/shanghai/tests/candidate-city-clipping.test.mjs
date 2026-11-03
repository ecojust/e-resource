import test from 'node:test';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
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

// Municipal Council needs additional rows beyond the original128-row allocation.
const triangleClip=(id,macro=MACRO)=>({geometry:{type:'Polygon',coordinates:[[[id*3,0],[id*3+2,0],[id*3,2],[id*3,0]]]},owner:{macro_id:macro,feature_local_id:id}});

const rowContains=(texture,row,x,z)=>{const d=texture.image.data,o=row*16;return new THREE.Triangle(new THREE.Vector3(d[o],0,d[o+1]),new THREE.Vector3(d[o+2],0,d[o+3]),new THREE.Vector3(d[o+4],0,d[o+5])).containsPoint(new THREE.Vector3(x,0,z));};

test('clipping rows beyond128 remain addressable in global and owner-filtered material passes',t=>{
  const {clipper,group,mesh,record}=harness(t,{ids:[139],initial:Array.from({length:139},(_,i)=>triangleClip(i+1))});
  assert.equal(clipper.getState().triangles,139);
  assert.equal(clipper.texture.image.width,4);assert.equal(clipper.texture.image.height,320);
  assert.equal(clipper.data.byteLength,20480);
  assert.equal(clipper.texture.minFilter,THREE.NearestFilter);assert.equal(clipper.texture.magFilter,THREE.NearestFilter);
  assert.equal(clipper.texture.generateMipmaps,false);
  assert.equal(clipper.texture.wrapS,THREE.ClampToEdgeWrapping);assert.equal(clipper.texture.wrapT,THREE.ClampToEdgeWrapping);
  assert.equal(clipper.data[138*16+12],139);
  assert(rowContains(clipper.texture,128,129*3+.25,.25));assert.equal(clipper.data[128*16+12],129);
  assert(!rowContains(clipper.texture,128,139*3+.25,.25));
  for(const shader of shaders(mesh)){
    assert.equal(shader.uniforms.candidateClipCount.value,1);
    assert.deepEqual(ownerIds(shader),[139]);
    assert.equal(shader.uniforms.candidateClipTexture.value.image.height,320);
    assert(rowContains(shader.uniforms.candidateClipTexture.value,0,139*3+.25,.25));
    assert.equal(shader.uniforms.candidateClipTexture.value.image.data[13],shader.uniforms.candidateMacro.value);
    assert.match(shader.fragmentShader,/for\(int i=0;i<320;i\+\+\)/);
    assert.match(shader.fragmentShader,/float row=\(float\(i\)\+0\.5\)\/320\.0/);
    assert(shader.fragmentShader.indexOf('if(float(i)>=candidateClipCount)break;')<shader.fragmentShader.indexOf('vec4 box=texture2D(candidateClipTexture'));
  }
  clipper.releaseObject(group);clipper.bindObject(group,{...record,ids:[140]});
  assert(shaders(mesh).every(shader=>shader.uniforms.candidateClipCount.value===0));
});

test('rows225,288 and320 stay addressable and321 rejects without corrupting live clipping state',t=>{
  const {clipper,mesh}=harness(t,{ids:[225,288,320],initial:Array.from({length:320},(_,i)=>triangleClip(i+1))}),compiled=shaders(mesh);
  assert.equal(clipper.getState().triangles,320);assert.equal(clipper.getState().triangleLimit,320);
  assert.equal(clipper.data[224*16+12],225);assert.equal(clipper.data[287*16+12],288);assert.equal(clipper.data[319*16+12],320);
  assert(compiled.every(shader=>shader.uniforms.candidateClipCount.value===3));
  assert(rowContains(clipper.texture,224,225*3+.25,.25));assert(!rowContains(clipper.texture,224,224*3+.25,.25));
  assert(rowContains(clipper.texture,287,288*3+.25,.25));assert(!rowContains(clipper.texture,287,287*3+.25,.25));
  assert(rowContains(clipper.texture,319,320*3+.25,.25));assert(!rowContains(clipper.texture,319,319*3+.25,.25));
  const texture=clipper.texture,scopedTexture=compiled[0].uniforms.candidateClipTexture.value;
  const scopedBefore=new Float32Array(scopedTexture.image.data),before=new Float32Array(clipper.data),revision=clipper.getState().revision;
  assert.throws(()=>clipper.update(Array.from({length:321},(_,i)=>triangleClip(i+1))),/候选模型局部边界过于复杂/);
  assert.equal(clipper.getState().triangles,320);assert.equal(clipper.getState().revision,revision);assert.deepEqual(clipper.data,before);
  assert.equal(clipper.texture,texture);assert.equal(compiled[0].uniforms.candidateClipTexture.value,scopedTexture);assert.deepEqual(scopedTexture.image.data,scopedBefore);
  assert(rowContains(scopedTexture,0,225*3+.25,.25));assert(rowContains(scopedTexture,1,288*3+.25,.25));assert(rowContains(scopedTexture,2,320*3+.25,.25));
  assert.equal(scopedTexture.image.data[13],compiled[0].uniforms.candidateMacro.value);
  assert(compiled.every(shader=>JSON.stringify(ownerIds(shader))==='[225,288,320]'));
});


test('paired native heights use the actual city anchor transform in all three shader passes',t=>{
  const source=readFileSync(new URL('../src/map-scene.js',import.meta.url),'utf8');
  const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};
  context.exports=context.module.exports;context.self=context;context.globalThis=context;
  vm.runInNewContext(readFileSync(new URL('../vendor/maplibre-gl.js',import.meta.url),'utf8'),context);
  const coordinates=source.slice(source.indexOf('  const mercatorOrigin ='),source.indexOf('  const scene = new THREE.Scene();'));
  const prepare=source.slice(source.indexOf('  function prepareCityObject('),source.indexOf('  function handleStreamingChange('));
  const env=new Function('THREE','maplibregl',`
    const ORIGIN=[121.4737,31.2304],EARTH=6378137,DEG=Math.PI/180;
    const cityDetails={prepareFarObject(){}},candidateClipper={bindObject(){}};
    function applyBuildingMaterial(){}
    ${coordinates}\n${prepare}
    return {geographicPosition,prepareCityObject};
  `)(THREE,context.module.exports);
  const reference=[121.519775390625,31.306714687449947],group=new THREE.Group();
  env.prepareCityObject(group,{id:MACRO,name:'source-height fixture',lng:reference[0],lat:reference[1]});
  group.updateMatrixWorld(true);
  const clipper=new CandidateCityClipper({THREE,geographicPosition:env.geographicPosition});
  const heightClip={...clip(),min_height:28.705,max_height:30.11,height_reference:reference};
  clipper.update([clip(),heightClip]);
  const mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());group.add(mesh);
  clipper.bindObject(group,{id:'height-near-fixture',parent:{id:MACRO},ids:CATHAY});
  t.after(()=>{clipper.dispose();mesh.geometry.dispose();mesh.material.dispose();});
  const low=Math.fround(env.geographicPosition(...reference,heightClip.min_height).y);
  const high=Math.fround(env.geographicPosition(...reference,heightClip.max_height).y);
  assert.notEqual(low,Math.fround(heightClip.min_height),'raw metres are not scene world Y');
  const neighborRoof=new THREE.Vector3(0,28.700000762939453,0).applyMatrix4(group.matrixWorld).y;
  const sourceRoof=new THREE.Vector3(0,30.100000381469727,0).applyMatrix4(group.matrixWorld).y;
  assert(low-neighborRoof>.0048,'the retained28.7m neighbor stays below the Float32 threshold');
  assert(sourceRoof>low&&sourceRoof<high,'the30.1m original roof is removed only in the extra polygon');
  for(const shader of shaders(mesh)){
    const data=shader.uniforms.candidateClipTexture.value.image.data;
    assert.equal(shader.uniforms.candidateClipCount.value,4);
    assert.deepEqual([data[6],data[7]],[-100,1000]);
    for(const row of [2,3])assert.deepEqual([data[row*16+6],data[row*16+7]],[low,high]);
    assert.match(shader.vertexShader,/vCandidatePosition=mat3\(modelMatrix\)\*candidatePosition\.xyz/);
    assert.match(shader.fragmentShader,/if\(candidateWorldPosition\.y<cy\.z\|\|candidateWorldPosition\.y>cy\.w\)continue;/);
    assert.match(shader.fragmentShader,/if\(candidateInside\(vCandidatePosition\+modelMatrix\[3\]\.xyz\)\)discard;/);
    assert.match(shader.fragmentShader,/#ifndef USE_TRANSMISSION\nuniform mat4 modelMatrix;\n#endif/);
  }
});

test('invalid or unrepresentable paired heights reject atomically before live texture changes',t=>{
  const {clipper,mesh}=harness(t),compiled=shaders(mesh),reference=[121.5,31.3];
  // This harness intentionally maps y to0. A real-world range that collapses
  // under a bad coordinate callback must not clear its existing correction.
  const good={...clip(),min_height:28,max_height:31,height_reference:reference};
  const invalid=[
    {...good,min_height:undefined},{...good,max_height:undefined},{...good,height_reference:undefined},
    {...good,min_height:null},{...good,min_height:true},{...good,min_height:'28'},
    {...good,min_height:NaN},{...good,max_height:Infinity},{...good,min_height:31},
    {...good,min_height:32},{...good,height_reference:[181,31]},
    {...good,height_reference:[121,86]},{...good,height_reference:[121]},
    {...good,height_reference:[121,31,0]},{...good,height_reference:[NaN,31]},
    {geometry,height_reference:reference},good,
  ];
  const before=new Float32Array(clipper.data),revision=clipper.revision,owners=structuredClone(clipper.triangleOwners);
  const texture=clipper.texture,version=texture.version,scoped=compiled[0].uniforms.candidateClipTexture.value;
  const scopedData=new Float32Array(scoped.image.data),scopedVersion=scoped.version;
  for(const bad of invalid){
    assert.throws(()=>clipper.update([clip(),bad]),/高度裁剪范围无效/);
    assert.deepEqual(clipper.data,before);assert.deepEqual(clipper.triangleOwners,owners);
    assert.equal(clipper.revision,revision);assert.equal(clipper.texture,texture);assert.equal(texture.version,version);
    assert.equal(clipper.triangleCount,2);assert.equal(scoped.version,scopedVersion);assert.deepEqual(scoped.image.data,scopedData);
    for(const shader of compiled){assert.equal(shader.uniforms.candidateClipTexture.value,scoped);assert.equal(shader.uniforms.candidateClipCount.value,2);}
  }
});

test('Float32 height overflow and collapsed endpoints reject without changing prior valid rows',t=>{
  const clipper=new CandidateCityClipper({THREE,geographicPosition:(x,z,y=0)=>new THREE.Vector3(x,y,z)});
  t.after(()=>clipper.dispose());clipper.update([clip()]);
  const before=new Float32Array(clipper.data),revision=clipper.revision;
  for(const [min_height,max_height] of [[28,Number.MAX_VALUE],[30,30+1e-10]]){
    assert.throws(()=>clipper.update([{...clip(),min_height,max_height,height_reference:[121,31]}]),/高度裁剪范围无效/);
    assert.deepEqual(clipper.data,before);assert.equal(clipper.revision,revision);
  }
});


test('translation-free clipping preserves batching and instancing and does not forward-reference transmission modelMatrix',t=>{
  const {clipper,mesh}=harness(t);
  for(const shader of shaders(mesh)){
    const batch=shader.vertexShader.indexOf('candidatePosition=batchingMatrix*candidatePosition;');
    const instance=shader.vertexShader.indexOf('candidatePosition=instanceMatrix*candidatePosition;');
    const varying=shader.vertexShader.indexOf('vCandidatePosition=mat3(modelMatrix)*candidatePosition.xyz;');
    assert(batch>=0&&instance>batch&&varying>instance);
    assert.match(shader.fragmentShader,/bool candidateInside\(vec3 candidateWorldPosition\)/);
    assert.match(shader.fragmentShader,/if\(candidateInside\(vCandidatePosition\+modelMatrix\[3\]\.xyz\)\)discard;/);
  }
  const material=new THREE.MeshPhysicalMaterial({transmission:.5}),library=THREE.ShaderLib.physical;
  clipper.bindMaterial(material,{featureIds:false,macroId:MACRO});
  const shader={vertexShader:library.vertexShader,fragmentShader:library.fragmentShader,uniforms:{}};
  material.onBeforeCompile(shader,{});
  const helper=shader.fragmentShader.slice(shader.fragmentShader.indexOf('bool candidateInside('),shader.fragmentShader.indexOf('return false;')+'return false;'.length);
  assert(!helper.includes('modelMatrix'),'the common helper must use its parameter, before transmission declares its modelMatrix');
  const transmission=shader.fragmentShader.indexOf('#include <transmission_pars_fragment>'),main=shader.fragmentShader.indexOf('void main(){');
  assert(transmission>=0&&transmission<main);
  assert.match(THREE.ShaderChunk.transmission_pars_fragment,/#ifdef USE_TRANSMISSION[\s\S]*uniform mat4 modelMatrix;/);
  assert.match(shader.fragmentShader,/#ifndef USE_TRANSMISSION\nuniform mat4 modelMatrix;\n#endif/);
  assert.match(material.customProgramCacheKey(),/candidate-city-clip-v3/);
  t.after(()=>material.dispose());
});
