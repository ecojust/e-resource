import assert from 'node:assert/strict';
import * as THREE from '../vendor/three.module.js';
import {correctPhotographicTexture} from '../src/photographic-texture.js';
const metadata={exifOrientation:6,rawSize:[5184,3456],uvConvention:'stored-pixels'};
function material(width,height) {
  const result=new THREE.MeshStandardMaterial({map:new THREE.Texture({width,height})});
  result.name='PhotoFacade_test';result.userData.photographicSource=metadata;return result;
}
const rotated=material(3456,5184),originalUV=[.15,.70];
const result=correctPhotographicTexture(THREE,rotated);
assert.equal(result.corrected,true);
const transformed=new THREE.Vector2(...originalUV).applyMatrix3(rotated.map.matrix);
assert.ok(transformed.distanceTo(new THREE.Vector2(.30,.15))<1e-12);
const first=rotated.map.matrix.clone();correctPhotographicTexture(THREE,rotated);
assert.deepEqual(rotated.map.matrix.elements,first.elements,'a shared texture is corrected only once');
const raw=material(5184,3456);assert.equal(correctPhotographicTexture(THREE,raw).corrected,false);
assert.equal(raw.map.matrixAutoUpdate,true);
const transformedMap=material(3456,5184);transformedMap.map.offset.set(.1,.2);transformedMap.map.repeat.set(.5,.75);
correctPhotographicTexture(THREE,transformedMap);
const actual=new THREE.Vector2(...originalUV).applyMatrix3(transformedMap.map.matrix);
assert.ok(actual.distanceTo(new THREE.Vector2(1-(.70*.75+.2),.15*.5+.1))<1e-12,'preserve an existing texture transform');
const unknown=material(1024,1024);assert.equal(correctPhotographicTexture(THREE,unknown).status,'unexpected-decoded-size');
assert.equal(unknown.map.matrixAutoUpdate,true,'do not guess when decoder dimensions are ambiguous');
const ordinary=material(3456,5184);ordinary.name='Ordinary glass';assert.equal(correctPhotographicTexture(THREE,ordinary),null);
const noMetadata=material(3456,5184);delete noMetadata.userData.photographicSource;
assert.equal(correctPhotographicTexture(THREE,noMetadata),null);
console.log('PASS: raw/oriented JPEG detection, shared-map idempotence, existing UV transform, and conservative unknown sizes');
