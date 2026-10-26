import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from '../vendor/three.module.js';
import {CityFeatureMask} from '../src/city-feature-mask.js';
import {createRealisticLighting} from '../src/realistic-lighting.js';
import {createArchitecturalMaterials} from '../src/architectural-material.js';
import {disposeModelResources} from '../src/model-resources.js';

// Exercise the current production integration functions, with real Three objects
// and the real lighting owner. Only renderer/MapLibre services are absent.
const source=fs.readFileSync(new URL('../src/map-scene.js',import.meta.url),'utf8');
function functionBetween(start,next){const a=source.indexOf('  function '+start+'('),b=source.indexOf(next,a);assert(a>=0&&b>a);return source.slice(a,b);}
const prepareSource=functionBetween('prepareCityDetailObject','  async function setCityManifest');
const disposeSource=functionBetween('disposeModel','  function prepareCityObject');

test('map integration copies far transform, adds grain without painted windows, and updates near shadow casters',async()=>{
 const scene=new THREE.Scene(),renderer={shadowMap:{enabled:false,autoUpdate:true,type:THREE.BasicShadowMap,needsUpdate:false}};
 const lighting=createRealisticLighting({THREE,scene,renderer,reflections:false,minimumRefreshInterval:0});
 const surfaces=await createArchitecturalMaterials({...THREE,TextureLoader:class {async loadAsync(){return new THREE.Texture({width:1024,height:1024});}}},{baseURL:'https://fixture.invalid/'});
 const prepare=new Function('THREE','lighting','surfaces',prepareSource+'\nreturn prepareCityDetailObject;')(THREE,lighting,surfaces);
 const far=new THREE.Group();far.position.set(20,3,30);far.scale.setScalar(1.001);far.quaternion.setFromAxisAngle(new THREE.Vector3(0,1,0),.3);
 const near=new THREE.Group(),stone=new THREE.MeshStandardMaterial({color:'#999999'});stone.name='InferredPlaster';
 const instance=new THREE.InstancedMesh(new THREE.BoxGeometry(3,8,3),stone,2);instance.setMatrixAt(0,new THREE.Matrix4());instance.setMatrixAt(1,new THREE.Matrix4().makeTranslation(5,0,0));near.add(instance);
 prepare(near,far,{id:'fixture/near'});scene.add(near);
 assert(near.position.equals(far.position));assert(near.scale.equals(far.scale));assert(near.quaternion.equals(far.quaternion));assert(instance.boundingSphere);
 assert.equal(stone.userData.architecturalSurface,'cityPlaster','surface dispatcher must receive each mesh, not the Group');
 assert.equal(stone.userData.cityFacade,undefined,'physical windows never get the old painted-window shader');
 lighting.update({position:new THREE.Vector3(20,0,30),now:1000});assert.equal(instance.castShadow,true);assert.equal(instance.receiveShadow,true);
 near.visible=false;lighting.update({position:new THREE.Vector3(20,0,30),now:2000});assert.equal(instance.castShadow,false);
 near.visible=true;lighting.update({position:new THREE.Vector3(20,0,30),now:3000});assert.equal(instance.castShadow,true);
 lighting.releaseModel(near);assert.equal(instance.castShadow,false);assert.equal(instance.receiveShadow,false);lighting.dispose();surfaces.dispose();disposeModelResources(near);
});

test('map disposal detaches feature ownership before releasing lighting, scene nodes and GPU buffers',()=>{
 const scene=new THREE.Scene(),far=new THREE.Group(),geometry=new THREE.BufferGeometry();
 geometry.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,1,0,0,0,1,0],3));geometry.setAttribute('_feature_id_0',new THREE.Float32BufferAttribute([1,1,1],1));
 const material=new THREE.MeshStandardMaterial(),mesh=new THREE.Mesh(geometry,material);far.add(mesh);scene.add(far);
 const original=material.onBeforeCompile,mask=new CityFeatureMask(THREE,1);mask.bindObject(far);mask.setOwner('ready-near',[1]);
 const order=[],details={detach(object){assert.equal(object,far);mask.removeOwner('ready-near');mask.dispose();order.push('detach');}};
 const lighting={releaseModel(object){assert.equal(object,far);assert.equal(mask.data[1],0);assert.equal(material.onBeforeCompile,original);order.push('lighting');}};
 geometry.addEventListener('dispose',()=>{assert.equal(far.parent,null);order.push('geometry');});
 const dispose=new Function('cityDetails','lighting','scene','disposeModelResources',disposeSource+'\nreturn disposeModel;')(details,lighting,scene,disposeModelResources);
 dispose(far);assert.deepEqual(order,['detach','lighting','geometry']);assert.equal(mask.disposed,true);
});
