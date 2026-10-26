import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from '../vendor/three.module.js';
import {CityFeatureMask} from '../src/city-feature-mask.js';
import {applyBuildingMaterial} from '../src/building-material.js';

// Execute the shipped Three r180 getProgram function, including its actual
// material/program/uniform cache-hit branch. GL compilation itself is stubbed;
// this is a cache/lifecycle regression, not a claim of a WebGL rendering test.
function rendererProgramCache(kind='standard') {
  const source=readFileSync(new URL('../vendor/three.module.js',import.meta.url),'utf8');
  const start=source.indexOf('\t\tfunction getProgram( material, scene, object ) {');
  const end=source.indexOf('\n\t\tfunction getUniformList(',start);
  assert(start>=0&&end>start,'Vendored getProgram boundary must be reviewed after a Three upgrade');
  const releaseStart=source.indexOf('\t\tfunction onMaterialDispose( event ) {');
  const releaseEnd=source.indexOf('\n\t\t// Buffer rendering',releaseStart);
  assert(releaseStart>=0&&releaseEnd>releaseStart,'Vendored material-release boundary must be reviewed after a Three upgrade');
  const objects=new WeakMap(),properties={
    get(material){if(!objects.has(material))objects.set(material,{});return objects.get(material);},
    remove(material){objects.delete(material);},
  };
  let acquired=0,released=0;
  const live=new Map(),keys=new Set();
  const programCache={
    getParameters(){const lib=THREE.ShaderLib[kind];return {vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader};},
    getProgramCacheKey(_parameters){return currentMaterial.customProgramCacheKey();},
    getUniforms(){return THREE.UniformsUtils.clone(THREE.ShaderLib[kind].uniforms);},
    acquireProgram(parameters,key){
      acquired++;keys.add(key);
      if(!live.has(key))live.set(key,{key,parameters,usedTimes:0});
      const program=live.get(key);program.usedTimes++;return program;
    },
    releaseProgram(program){released++;if(--program.usedTimes===0)live.delete(program.key);},
    releaseShaderCache(){},
  };
  const lights={state:{version:1}},currentRenderState={state:{lights,shadowsArray:[]}};
  const env={get(){return null;}};
  const getProgram=new Function('properties','currentRenderState','programCache','cubeuvmaps','cubemaps',
    'updateCommonMaterialProperties','materialNeedsLights','clipping','_emptyScene','_this',
    `${source.slice(releaseStart,releaseEnd)}\n${source.slice(start,end)}\nreturn getProgram;`)(properties,currentRenderState,programCache,env,env,
    ()=>{},()=>false,{uniform:{value:[]}},new THREE.Scene(),{});
  let currentMaterial;
  return {
    compile(material) {currentMaterial=material;const program=getProgram(material,new THREE.Scene(),{});return {program,uniforms:properties.get(material).uniforms};},
    stats(material){return {programs:properties.get(material).programs?.size||0,acquired,released,live:live.size,keys:keys.size};},
  };
}

for(const [kind,create] of [
  ['standard',()=>new THREE.MeshStandardMaterial()],
  ['depth',()=>new THREE.MeshDepthMaterial()],
  ['distanceRGBA',()=>new THREE.MeshDistanceMaterial()],
])test(`${kind}: cached compiled uniforms point to replacement mask after disposal and rebind`,()=>{
  const renderer=rendererProgramCache(kind),material=create();
  if(kind==='standard'){material.name='CityWalls';applyBuildingMaterial(material);}
  const originalHook=material.onBeforeCompile,originalKey=material.customProgramCacheKey();
  const a=new CityFeatureMask(THREE,4);a.bindMaterial(material);a.setOwner('near',[2]);
  const first=renderer.compile(material),textureHolder=first.uniforms.cityFeatureMask,widthHolder=first.uniforms.cityFeatureMaskWidth;
  assert.equal(textureHolder.value,a.texture);
  const cached=renderer.compile(material);
  assert.equal(cached.program,first.program);assert.equal(cached.uniforms,first.uniforms);
  assert.equal(renderer.stats(material).acquired,1,'The actual Three same-key cache branch was exercised');
  a.dispose();assert.equal(material.onBeforeCompile,originalHook);assert.equal(material.customProgramCacheKey(),originalKey);
  const b=new CityFeatureMask(THREE,256);b.bindMaterial(material);b.setOwner('precise',[128]);
  const second=renderer.compile(material);
  assert.equal(second.program.key,first.program.key,'Rebinding never creates a generation-dependent program key');
  assert.notEqual(second.uniforms,first.uniforms,'Disposal releases old renderer properties, so the restored hook can compile safely');
  assert.equal(second.uniforms.cityFeatureMask,textureHolder);
  assert.equal(second.uniforms.cityFeatureMaskWidth,widthHolder);
  assert.equal(textureHolder.value,b.texture,'Cached GPU uniforms must not sample the old cleared/disposed mask');
  assert.equal(widthHolder.value,b.width);assert.equal(textureHolder.value.image.data[128],255);
  a.dispose();assert.equal(textureHolder.value,b.texture,'Late idempotent old disposal cannot clear the new owner');
  assert.deepEqual(renderer.stats(material),{programs:1,acquired:2,released:1,live:1,keys:1});b.dispose();
  assert.deepEqual(renderer.stats(material),{programs:0,acquired:2,released:2,live:0,keys:1});
  assert.equal(textureHolder.value,null,'No live material holder retains a disposed texture');
});

test('100 rebind cycles keep one holder pair and one program key, with current ownership only',()=>{
  const renderer=rendererProgramCache(),material=new THREE.MeshStandardMaterial();
  let textureHolder,widthHolder,program;
  for(let i=0;i<100;i++) {
    const mask=new CityFeatureMask(THREE,i%2?512:4);mask.bindMaterial(material);mask.setOwner(`owner-${i}`,[1]);
    const compiled=renderer.compile(material);
    if(!textureHolder){textureHolder=compiled.uniforms.cityFeatureMask;widthHolder=compiled.uniforms.cityFeatureMaskWidth;program=compiled.program;}
    assert.equal(compiled.program.key,program.key);assert.equal(compiled.uniforms.cityFeatureMask,textureHolder);
    assert.equal(compiled.uniforms.cityFeatureMaskWidth,widthHolder);
    assert.equal(textureHolder.value,mask.texture);assert.equal(widthHolder.value,mask.width);
    assert.equal(renderer.stats(material).live,1);mask.dispose();assert.equal(textureHolder.value,null);assert.equal(renderer.stats(material).live,0);
  }
  assert.deepEqual(renderer.stats(material),{programs:0,acquired:100,released:100,live:0,keys:1});
});

test('distinct materials never share mask uniform holders even with the same shader key',()=>{
  const renderer=rendererProgramCache(),a=new THREE.MeshStandardMaterial(),b=new THREE.MeshStandardMaterial();
  const one=new CityFeatureMask(THREE,2),two=new CityFeatureMask(THREE,2);
  one.bindMaterial(a);two.bindMaterial(b);assert.equal(a.customProgramCacheKey(),b.customProgramCacheKey());
  const ua=renderer.compile(a).uniforms,ub=renderer.compile(b).uniforms;
  assert.notEqual(ua.cityFeatureMask,ub.cityFeatureMask);assert.equal(ua.cityFeatureMask.value,one.texture);assert.equal(ub.cityFeatureMask.value,two.texture);
  assert.equal(renderer.stats(a).live,1,'Identical shader keys share one actual program with two references');
  one.dispose();assert.equal(ub.cityFeatureMask.value,two.texture);assert.equal(renderer.stats(b).live,1);
  assert.equal(renderer.compile(b).uniforms,ub,'Disposing another material cannot evict this material uniforms');
  two.dispose();assert.equal(renderer.stats(b).live,0);
});

// This is possible while an asynchronously reloaded near index is pending.
// The material can render its original generic facade between two masks.
test('rebind after an intervening unmasked compile still exposes current mask uniforms',()=>{
  const renderer=rendererProgramCache(),material=new THREE.MeshStandardMaterial();
  material.name='CityWalls';applyBuildingMaterial(material);
  const a=new CityFeatureMask(THREE,2);a.bindMaterial(material);renderer.compile(material);a.dispose();
  renderer.compile(material);
  const b=new CityFeatureMask(THREE,2);b.bindMaterial(material);b.setOwner('near',[2]);
  const returned=renderer.compile(material);
  assert.equal(returned.uniforms.cityFeatureMask?.value,b.texture);
  assert.equal(returned.uniforms.cityFeatureMaskWidth?.value,b.width);
  assert.equal(renderer.stats(material).programs,2);b.dispose();assert.equal(renderer.stats(material).live,0);
  assert.equal(renderer.stats(material).acquired,renderer.stats(material).released);
});


test('mask release invalidates programs without disposing source maps, geometry or prior shadow materials',()=>{
  const map=new THREE.Texture(),normalMap=new THREE.Texture(),geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,1,0,0,0,1,0],3));
  geometry.setAttribute('_feature_id_0',new THREE.Float32BufferAttribute([1,1,1],1));
  const material=new THREE.MeshStandardMaterial({map,normalMap}),mesh=new THREE.Mesh(geometry,material);
  const originalDepth=new THREE.MeshDepthMaterial(),originalDistance=new THREE.MeshDistanceMaterial();
  mesh.customDepthMaterial=originalDepth;mesh.customDistanceMaterial=originalDistance;
  let sourceDisposals=0,surfaceDisposals=0,depthDisposals=0,distanceDisposals=0;
  for(const item of [map,normalMap,geometry,originalDepth,originalDistance])item.addEventListener('dispose',()=>sourceDisposals++);
  material.addEventListener('dispose',()=>surfaceDisposals++);
  const mask=new CityFeatureMask(THREE,1);mask.bindObject(mesh);
  mesh.customDepthMaterial.addEventListener('dispose',()=>depthDisposals++);
  mesh.customDistanceMaterial.addEventListener('dispose',()=>distanceDisposals++);
  const renderer=rendererProgramCache();renderer.compile(material);mask.dispose();mask.dispose();
  assert.equal(sourceDisposals,0);assert.equal(surfaceDisposals,1);assert.equal(depthDisposals,1);assert.equal(distanceDisposals,1);
  assert.equal(material.map,map);assert.equal(material.normalMap,normalMap);assert.equal(mesh.geometry,geometry);
  assert.equal(mesh.customDepthMaterial,originalDepth);assert.equal(mesh.customDistanceMaterial,originalDistance);
  assert.equal(renderer.stats(material).live,0);
});
