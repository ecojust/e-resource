import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from '../vendor/three.module.js';
import {CityFeatureMask} from '../src/city-feature-mask.js';
import {createRealisticLighting} from '../src/realistic-lighting.js';
import {createArchitecturalMaterials} from '../src/architectural-material.js';
import {disposeModelResources} from '../src/model-resources.js';
import {FeatureStateSuppressor,LocalModelStreamer} from '../src/local-model-streamer.js';
import {detailIsNearby} from '../src/detail-model-cache.js';

// Exercise the current production integration functions, with real Three objects
// and the real lighting owner. Only renderer/MapLibre services are absent.
const source=fs.readFileSync(new URL('../src/map-scene.js',import.meta.url),'utf8');
function functionBetween(start,next){const a=source.indexOf('  function '+start+'('),b=source.indexOf(next,a);assert(a>=0&&b>a);return source.slice(a,b);}
const prepareSource=functionBetween('prepareCityDetailObject','  async function setCityManifest');
const disposeSource=functionBetween('disposeModel','  function prepareCityObject');
// These legacy fixtures have no source_geometry_correction configuration.
// Execute the real production helpers with an explicitly empty correction
// manager; source-correction tests exercise verified asset activation separately.
const correctionStart=source.indexOf('  function syncSourceGeometryCorrections('),correctionEnd=source.indexOf('  let ordinaryCatalog=',correctionStart);
assert(correctionStart>=0&&correctionEnd>correctionStart);
const noSourceCorrectionHelpers=new Function('sourceGeometryCorrections',source.slice(correctionStart,correctionEnd)+
 '\nreturn {syncSourceGeometryCorrections,isLandmarkSourceActive};')({sync:()=>false,isConfigured:()=>false});

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
 const dispose=new Function('cityDetails','lighting','scene','disposeModelResources','syncSourceGeometryCorrections',disposeSource+'\nreturn disposeModel;')(details,lighting,scene,disposeModelResources,noSourceCorrectionHelpers.syncSourceGeometryCorrections);
 dispose(far);assert.deepEqual(order,['detach','lighting','geometry']);assert.equal(mask.disposed,true);
});

// Execute the production visibility/manifest functions against the real owner
// implementation. This checks effects and async restoration, not source strings.
function preciseMapFixture(t) {
 const states=new Map(),map={getCenter:()=>({lng:121,lat:31}),getZoom:()=>19,getSource:()=>({}),triggerRepaint(){},
  setFeatureState(target,value){states.set(target.sourceLayer+':'+target.id,value);},removeFeatureState(target){states.delete(target.sourceLayer+':'+target.id);}};
 const tileSuppression=new FeatureStateSuppressor(map,'overture'),landmarkSuppression=new FeatureStateSuppressor(map,'overture');
 const dynamic={id:'bund05',status:'loaded',activeVariant:'full',object:new THREE.Group(),distance:0,maxDistance:100};
 const staticRecord={id:'old-landmark',status:'loaded',activeVariant:'full',object:new THREE.Group(),distance:0,maxDistance:100};
 const records=new Map([[dynamic.id,dynamic],[staticRecord.id,staticRecord]]),visible=[];
 const env={...noSourceCorrectionHelpers,destroyed:false,map,walker:{group:{visible:true}},current:{lng:121,lat:31},landmarkRecords:records,
  distanceMetres:(_target,record)=>record.distance,detailIsNearby,desiredVariant:()=> 'full',streetInteraction:{},
  preciseLandmarkIds:new Set(['bund05']),landmarkBoundaries:new Map([['bund05',{building_ids:['new-source-id'],building_part_ids:[]}],['old-landmark',{building_ids:['old-source-id'],building_part_ids:[]}]]),
  tileSuppression,landmarkSuppression,cityDetails:{setVisibleLandmarks(ids){visible.push(ids);}},
  updateBuildingExclusions(){},selectHiddenDetailEvictions:()=>[],detailCacheLimits:{},releaseHiddenDetail(){},disposeModel(){},detailCacheStats:{},loadLandmark(){},updateStreetBasemap(){},updateLocalModels(){},
  moduleURL:'https://example.test/project/src/map-scene.js',localDataKind:'city',onLoadError(error){throw error;}};
 const visibilitySource=functionBetween('updateLandmarkVisibility','  function updateBuildingExclusions');
 const execute=body=>new Function('env',`with(env){${body.replaceAll('import.meta.url','moduleURL')}}`)(env);
 env.updateLandmarkVisibility=execute(visibilitySource+'\nreturn updateLandmarkVisibility;');
 const scene=new THREE.Scene();env.localStreamer=new LocalModelStreamer({scene,loader:{},suppression:tileSuppression,prepareObject(){},disposeObject(){}});
 t.after(()=>{env.localStreamer.destroy();landmarkSuppression.destroy({clearMap:true});});
 const asyncFunction=(name,next)=>{const begin=source.indexOf('  async function '+name+'('),end=source.indexOf(next,begin);assert(begin>=0&&end>begin);return execute(source.slice(begin,end)+`\nreturn ${name};`);};
 return {env,states,dynamic,staticRecord,visible,tileSuppression,landmarkSuppression,
  update:env.updateLandmarkVisibility,
  setCityManifest:asyncFunction('setCityManifest','  async function setNeighborhoods'),
  setNeighborhoods:asyncFunction('setNeighborhoods','  // Update exclusions only'),
  async settled(){await Promise.all([tileSuppression.setOwner('fixture-noop',null),landmarkSuppression.setOwner('fixture-noop',null)]);}};
}

test('precise map visibility shares online source ownership and uses only loaded visible models',async t=>{
 const h=preciseMapFixture(t);await h.tileSuppression.setOwner('ordinary-tile',{building:['new-source-id'],building_part:[]});
 h.update();await h.settled();assert(h.states.has('building:new-source-id'));assert(h.states.has('building:old-source-id'));
 assert(h.tileSuppression.owners.has('precise:bund05'));assert(!h.landmarkSuppression.owners.has('bund05'));
 assert.deepEqual(h.visible.at(-1),['bund05','old-landmark']);
 h.dynamic.distance=10000;h.update();await h.settled();assert.equal(h.dynamic.object.visible,false);assert(!h.tileSuppression.owners.has('precise:bund05'));
 assert(h.states.has('building:new-source-id'),'ordinary tile retains the source mask after the landmark leaves');
 assert.deepEqual(h.visible.at(-1),['old-landmark']);
 await h.tileSuppression.removeOwner('ordinary-tile');assert(!h.states.has('building:new-source-id'));
 h.dynamic.distance=0;h.dynamic.status='loading';h.dynamic.object=null;h.update();await h.settled();assert(!h.states.has('building:new-source-id'));assert.deepEqual(h.visible.at(-1),['old-landmark']);
 h.dynamic.status='error';h.update();await h.settled();assert(!h.states.has('building:new-source-id'));
 h.dynamic.status='loaded';h.dynamic.object=new THREE.Group();h.update();await h.settled();assert(h.states.has('building:new-source-id'));
});

test('precise map city-manifest reset replays live landmark owner after the generic cache is cleared',async t=>{
 const h=preciseMapFixture(t);h.update();await h.settled();await h.tileSuppression.setOwner('old-city-tile',{building:['new-source-id','neighbor'],building_part:[]});
 await h.setCityManifest({tiles:[]},{baseURL:'https://example.test/project/assets/city-detail/'});await h.settled();
 assert(h.tileSuppression.owners.has('precise:bund05'));assert(!h.tileSuppression.owners.has('old-city-tile'));assert(h.states.has('building:new-source-id'));
 assert(!h.states.has('building:neighbor'));assert(h.states.has('building:old-source-id'));assert.deepEqual(h.visible.at(-1),['bund05','old-landmark']);
});
