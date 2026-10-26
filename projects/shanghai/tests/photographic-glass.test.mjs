import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../vendor/three.module.js';
import {isPhotographicGlass, preparePhotographicGlass} from '../src/photographic-glass.js';
import {correctPhotographicTexture} from '../src/photographic-texture.js';
import {disposeModelResources} from '../src/model-resources.js';
import {createRealisticLighting, isArchitecturalGlazing} from '../src/realistic-lighting.js';

function photo(name='PhotoFacade_Bund05_RegisteredGlass', image={width:5184,height:3456}) {
  const material=new THREE.MeshStandardMaterial({map:new THREE.Texture(image), color:0xb8c1ca,
    side:THREE.DoubleSide, opacity:.79, transparent:true, alphaTest:.1, depthWrite:false});
  material.name=name;material.toneMapped=true;material.polygonOffset=true;material.polygonOffsetFactor=-1;
  material.userData={source_id:'retained',photographicSource:{rawSize:[5184,3456],exifOrientation:6,uvConvention:'stored-pixels'}};
  return material;
}
function watch(resource) {let count=0;resource.addEventListener('dispose',()=>count++);return ()=>count;}

test('one group shares one converted material, preserves visual/texture state, and is idempotent',()=>{
  const source=photo(), group=new THREE.Group(), geometry=new THREE.PlaneGeometry();
  const first=new THREE.Mesh(geometry,source), second=new THREE.Mesh(geometry,[source,source]);group.add(first,second);
  const oldMap=source.map, disposed=watch(source), mapDisposed=watch(oldMap), uv=geometry.attributes.uv.array.slice();
  const result=preparePhotographicGlass(THREE,group), material=first.material;
  assert.deepEqual(result,{convertedMaterials:1,convertedMeshes:2});
  assert.ok(material.isMeshBasicMaterial);assert.equal(second.material[0],material);assert.equal(second.material[1],material);
  assert.equal(material.map,oldMap);assert.deepEqual(material.color.toArray(),source.color.toArray());
  assert.notEqual(material.color,source.color);
  for(const property of ['name','opacity','transparent','side','alphaTest','depthWrite','toneMapped','polygonOffset','polygonOffsetFactor'])
    assert.equal(material[property],source[property],property);
  assert.equal(material.userData.photographicSource,source.userData.photographicSource);
  assert.equal(material.userData.source_id,'retained');assert.equal(material.envMap,null);
  assert.equal(material.userData.photographicRendering.kind,'captured-radiance');
  assert.equal(disposed(),1);assert.equal(mapDisposed(),0,'no texture disposal while loaded');
  assert.deepEqual(geometry.attributes.uv.array,uv);
  assert.equal(first.castShadow,false);assert.equal(first.receiveShadow,false);
  assert.deepEqual(preparePhotographicGlass(THREE,group),{convertedMaterials:0,convertedMeshes:0});
  assert.equal(first.material,material);assert.equal(disposed(),1);
  disposeModelResources(group);assert.equal(mapDisposed(),1);assert.equal(disposed(),1,'old PBR source not retained as a live material');
});

test('only mapped explicit photo glass/glazing converts; photo stone and ordinary glazing retain materials',()=>{
  const group=new THREE.Group(), names=['PhotoFacade_Bund12_Glazing_OriginalPhoto','PhotoFacade_Bund17_Glazing',
    'PhotoFacade_Limestone_0','Ordinary glass','PhotoFacade_Bund12_Glass_Edge'];
  const materials=names.map(n=>photo(n));materials.at(-1).map=null;
  materials.forEach(m=>group.add(new THREE.Mesh(new THREE.PlaneGeometry(),m)));
  const result=preparePhotographicGlass(THREE,group);assert.equal(result.convertedMaterials,2);
  assert.equal(isPhotographicGlass(group.children[0].material),true);
  assert.equal(isArchitecturalGlazing(group.children[0].material),true);
  for(let i=2;i<materials.length;i++)assert.equal(group.children[i].material,materials[i],names[i]);
  const untagged=new THREE.MeshBasicMaterial({map:new THREE.Texture()});untagged.name='Ordinary glass';
  assert.equal(isArchitecturalGlazing(untagged),false,'do not treat all Basic materials as procedural glazing');
  disposeModelResources(group);untagged.map.dispose();untagged.dispose();
});

test('existing EXIF correction and asset-image inspection still use the same single texture',()=>{
  const source=photo('PhotoFacade_Bund17_Glazing',{width:3456,height:5184});
  source.map.offset.set(.1,.2);source.map.repeat.set(.5,.75);
  const group=new THREE.Group();group.add(new THREE.Mesh(new THREE.PlaneGeometry(),source),new THREE.Mesh(new THREE.PlaneGeometry(),source));
  preparePhotographicGlass(THREE,group);
  const maps=new Set();
  group.traverse(mesh=>{if(!mesh.isMesh)return;const m=mesh.material;correctPhotographicTexture(THREE,m);if(/^PhotoFacade_/i.test(m.name)&&m.map)maps.add(m.map);});
  assert.equal(maps.size,1);const texture=[...maps][0];assert.equal(texture,source.map);
  assert.equal(texture.userData.photographicOrientation.corrected,true);
  assert.deepEqual(texture.userData.photographicOrientation.decodedSize,[3456,5184]);
  const uv=new THREE.Vector2(.15,.70).applyMatrix3(texture.matrix);
  assert.ok(uv.distanceTo(new THREE.Vector2(1-(.70*.75+.2),.15*.5+.1))<1e-12);
  disposeModelResources(group);
});

test('conversion retains auxiliary texture ownership until unload, with map and Bitmap deduplication',()=>{
  let closed=0,sharedClosed=0;const bitmap={width:4,height:4,close(){closed++;}};
  const source=photo(undefined,bitmap),aux=new THREE.Texture(bitmap),shared=new THREE.Texture({close(){sharedClosed++;}});
  shared.userData.shared=true;source.normalMap=aux;source.envMap=shared;
  const counts={map:watch(source.map),aux:watch(aux),shared:watch(shared),source:watch(source)};
  const other=new THREE.MeshStandardMaterial({map:source.map});const group=new THREE.Group();
  group.add(new THREE.Mesh(new THREE.PlaneGeometry(),source),new THREE.Mesh(new THREE.PlaneGeometry(),other));
  preparePhotographicGlass(THREE,group);const basic=group.children[0].material,basicDisposed=watch(basic);
  assert.equal(basic.normalMap,undefined);assert.equal(basic.envMap,null);
  assert.equal(counts.source(),1);assert.equal(closed,0);assert.equal(counts.map(),0);assert.equal(counts.aux(),0);
  disposeModelResources(group);
  assert.equal(counts.map(),1);assert.equal(counts.aux(),1);assert.equal(closed,1);
  assert.equal(basicDisposed(),1);assert.equal(counts.source(),1);
  assert.equal(counts.shared(),0);assert.equal(sharedClosed,0,'shared viewer reflection is not owned by this model');
});

test('lighting keeps photographic Basic glass out of shadow casting/receiving while stone still participates',()=>{
  const renderer={shadowMap:{enabled:false,autoUpdate:true,type:THREE.BasicShadowMap}},scene=new THREE.Scene();
  const lighting=createRealisticLighting({THREE,scene,renderer,reflections:false});
  const group=new THREE.Group(),glass=new THREE.Mesh(new THREE.PlaneGeometry(4,5),photo()),
    stone=new THREE.Mesh(new THREE.BoxGeometry(6,8,1),photo('PhotoFacade_Limestone_0'));
  group.add(glass,stone);scene.add(group);preparePhotographicGlass(THREE,group);
  lighting.configureModel(group,{detailed:true});lighting.update({position:new THREE.Vector3(),now:0});
  assert.equal(glass.castShadow,false);assert.equal(glass.receiveShadow,false);
  assert.equal(stone.castShadow,true);assert.equal(stone.receiveShadow,true);assert.ok(stone.material.isMeshStandardMaterial);
  lighting.releaseModel(group);assert.equal(glass.receiveShadow,false,'release returns converted pre-lighting state');
  lighting.dispose();disposeModelResources(group);
});

test('an owned texture does not close a Bitmap still owned by a shared viewer texture',()=>{
  let closed=0;const bitmap={width:4,height:4,close(){closed++;}};
  const source=photo(undefined,bitmap),shared=new THREE.Texture(bitmap);
  shared.userData.shared=true;source.envMap=shared;
  const group=new THREE.Group();group.add(new THREE.Mesh(new THREE.PlaneGeometry(),source));
  const ownedDispose=watch(source.map),sharedDispose=watch(shared);
  preparePhotographicGlass(THREE,group);disposeModelResources(group);
  assert.equal(ownedDispose(),1);assert.equal(sharedDispose(),0);assert.equal(closed,0);
});

test('separate import groups create independent materials and do not share a global conversion cache',()=>{
  const groups=[new THREE.Group(),new THREE.Group()];
  for(const g of groups)g.add(new THREE.Mesh(new THREE.PlaneGeometry(),photo()));
  groups.forEach(g=>preparePhotographicGlass(THREE,g));
  assert.notEqual(groups[0].children[0].material,groups[1].children[0].material);
  assert.notEqual(groups[0].children[0].material.map,groups[1].children[0].material.map);
  groups.forEach(disposeModelResources);
});
