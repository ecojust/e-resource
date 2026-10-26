import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../vendor/three.module.js';
import {CityFeatureMask} from '../src/city-feature-mask.js';
import {applyBuildingMaterial} from '../src/building-material.js';

function meshFor(ids=[1,1,1,2,2,2],material=new THREE.MeshStandardMaterial()) {
 const geometry=new THREE.BufferGeometry();
 geometry.setAttribute('position',new THREE.Float32BufferAttribute(ids.flatMap((_,i)=>[i%3,Math.floor(i/3),i%2]),3));
 geometry.setAttribute('normal',new THREE.Float32BufferAttribute(ids.flatMap(()=>[0,0,1]),3));
 geometry.setAttribute('_feature_id_0',new THREE.Float32BufferAttribute(ids,1));
 return new THREE.Mesh(geometry,material);
}
function compile(material,kind='standard') {
 const lib=THREE.ShaderLib[kind],shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:THREE.UniformsUtils.clone(lib.uniforms)};
 material.onBeforeCompile(shader,{});return shader;
}

test('actual Three texture lookup, reference ownership and invalid transaction rollback',()=>{
 const mask=new CityFeatureMask(THREE,4),version=mask.texture.version;
 assert(mask.texture.isDataTexture);assert.equal(mask.width,4);assert.equal(mask.texture.minFilter,THREE.NearestFilter);
 mask.setOwner('one',[1,2,2]);mask.setOwner('two',[2,4]);assert.deepEqual([...mask.data.slice(0,5)],[0,255,255,0,255]);
 mask.removeOwner('one');assert.deepEqual([...mask.data.slice(0,5)],[0,0,255,0,255]);
 assert.throws(()=>mask.setOwner('two',[3,NaN]),/Invalid/);assert.deepEqual([...mask.owners.get('two')],[2,4]);
 assert.throws(()=>mask.setOwner('two',[2.5]),/Invalid/);assert.equal(mask.references[2],1);
 mask.removeOwner('two');assert(mask.data.every(value=>value===0));assert(mask.texture.version>version);mask.dispose();
});

test('default Three cache key captures the previous hook before wrapping',()=>{
 const mesh=meshFor(),original=mesh.material.onBeforeCompile,oldKey=mesh.material.customProgramCacheKey();
 const mask=new CityFeatureMask(THREE,2);mask.bindObject(mesh);
 assert.equal(mesh.material.customProgramCacheKey(),oldKey+'|city-feature-mask-v2');
 mask.dispose();assert.equal(mesh.material.onBeforeCompile,original);assert.equal(mesh.material.customProgramCacheKey(),oldKey);
});

test('real standard/depth/distance ShaderLib chains mask and existing generic facade hook',()=>{
 const material=new THREE.MeshStandardMaterial();material.name='CityWalls';applyBuildingMaterial(material);
 const mesh=meshFor(undefined,material),mask=new CityFeatureMask(THREE,2);assert.equal(mesh.castShadow,false);mask.bindObject(mesh);
 const surface=compile(material);assert(surface.vertexShader.includes('vCityMetres'));assert(surface.fragmentShader.includes('facadeUV'));
 for(const [m,kind] of [[material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']]) {
  const shader=compile(m,kind);assert(shader.vertexShader.includes('vCityFeatureId = _feature_id_0'));
  assert(shader.fragmentShader.includes('if(texture2D(cityFeatureMask,maskUV).r>0.5) discard;'));
  assert.equal(shader.uniforms.cityFeatureMask.value,mask.texture);
 }
 mesh.castShadow=true;mask.setOwner('near',[2]);assert.equal(mask.data[2],255);mask.dispose();
});

test('late shadow activation keeps prior custom depth properties and restores originals',()=>{
 const mesh=meshFor(),depth=new THREE.MeshDepthMaterial({depthPacking:THREE.BasicDepthPacking,alphaTest:.4});
 const prior=function(shader){shader.uniforms.priorDepth={value:7}};depth.onBeforeCompile=prior;
 mesh.customDepthMaterial=depth;const mask=new CityFeatureMask(THREE,2);mask.bindObject(mesh);
 assert.notEqual(mesh.customDepthMaterial,depth);assert.equal(mesh.customDepthMaterial.alphaTest,.4);assert.equal(compile(mesh.customDepthMaterial,'depth').uniforms.priorDepth.value,7);
 let depthDisposed=0;mesh.customDepthMaterial.addEventListener('dispose',()=>depthDisposed++);mask.bindObject(mesh);
 assert.equal(mask.shadowBindings.length,1);mask.dispose();mask.dispose();assert.equal(mesh.customDepthMaterial,depth);assert.equal(depthDisposed,1);
});

test('cross-parent shared material rejects before attaching any shader, then can bind after release',()=>{
 const shared=new THREE.MeshStandardMaterial(),a=meshFor(undefined,shared),b=meshFor(undefined,shared);
 const one=new CityFeatureMask(THREE,2),two=new CityFeatureMask(THREE,2);one.bindObject(a);const hook=shared.onBeforeCompile;
 assert.throws(()=>two.bindObject(b),/shared across/);assert.equal(two.bindings.size,0);assert.equal(shared.onBeforeCompile,hook);
 one.dispose();two.bindObject(b);assert(two.bindings.has(shared));two.dispose();
});

for(const [name,ids] of [['nonfinite',[NaN,NaN,NaN]],['fractional',[1.5,1.5,1.5]],['mixed triangle',[1,1,2]],['outside namespace',[3,3,3]]])test(`reject ${name} IDs before modifying materials`,()=>{
 const mesh=meshFor(ids),original=mesh.material.onBeforeCompile,mask=new CityFeatureMask(THREE,2);
 assert.throws(()=>mask.bindObject(mesh),/feature ID|feature IDs/);assert.equal(mesh.material.onBeforeCompile,original);assert.equal(mask.bindings.size,0);mask.dispose();
});

test('invalid later mesh leaves earlier good mesh untouched',()=>{
 const group=new THREE.Group(),good=meshFor(),bad=meshFor([1,1,2]);group.add(good,bad);
 const original=good.material.onBeforeCompile,mask=new CityFeatureMask(THREE,2);assert.throws(()=>mask.bindObject(group));
 assert.equal(good.material.onBeforeCompile,original);assert.equal(good.customDepthMaterial,undefined);mask.dispose();
});

test('indexed triangles use actual index ownership, reject a mixed indexed face',()=>{
 const mesh=meshFor();mesh.geometry.setIndex([0,1,2,3,4,5]);const mask=new CityFeatureMask(THREE,2);mask.bindObject(mesh);mask.dispose();
 mesh.geometry.setIndex([0,1,3]);const invalid=new CityFeatureMask(THREE,2);assert.throws(()=>invalid.bindObject(mesh),/mixes feature IDs/);invalid.dispose();
});
