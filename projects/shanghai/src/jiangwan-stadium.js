import * as THREE from '../vendor/three.module.js';
import {GLTFLoader} from '../vendor/GLTFLoader.js';
import {MeshoptDecoder} from '../vendor/meshopt_decoder.module.js';
import {OrbitControls} from '../vendor/OrbitControls.js';
import {disposeModelResources} from './model-resources.js';
// Auxiliary asset inspector; public building links open the main city map.
const VIEW_CONFIG={target:[0,8,0],fitDistance:700,fitWidthDistance:630,stageSize:800,autoLodDistance:1050,autoFullDistance:800};
const $=id=>document.getElementById(id);
const viewport=()=>({width:$('model-view').clientWidth,height:Math.max(1,$('model-view').clientHeight)});
const scene=new THREE.Scene();scene.background=new THREE.Color('#172a30');
const camera=new THREE.PerspectiveCamera(42,viewport().width/viewport().height,.1,2500);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(viewport().width,viewport().height);
renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;$('model-view').append(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=3;controls.maxDistance=1800;controls.maxPolarAngle=Math.PI/2-.01;
controls.target.set(...VIEW_CONFIG.target);
scene.add(new THREE.HemisphereLight(0xffffff,0x94a398,2.0));
const sun=new THREE.DirectionalLight(0xfff8e9,2.4);sun.position.set(-200,350,240);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);
Object.assign(sun.shadow.camera,{left:-270,right:270,top:270,bottom:-270,near:1,far:1000});sun.shadow.bias=-.0004;sun.shadow.normalBias=.025;scene.add(sun);
const stage=new THREE.Mesh(new THREE.PlaneGeometry(VIEW_CONFIG.stageSize,VIEW_CONFIG.stageSize),new THREE.MeshStandardMaterial({color:0x60746c,roughness:1}));stage.rotation.x=-Math.PI/2;stage.position.y=-.10;stage.receiveShadow=true;scene.add(stage);
const loader=new GLTFLoader();loader.setMeshoptDecoder(MeshoptDecoder);
let manifest,current=null,generation=0,pending=null,pendingVariant=null,currentVariant=null,autoTimer=null,requestedVariant='full';
const state={status:'initializing',variant:null,error:null,triangles:0};
function framing(){
 if(!current)return null;
 camera.updateMatrixWorld(true);
 const box=new THREE.Box3().setFromObject(current),points=[];
 for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z])points.push(new THREE.Vector3(x,y,z).project(camera));
 return {modelBounds:{min:box.min.toArray(),max:box.max.toArray()},screenBounds:{minX:Math.min(...points.map(p=>p.x)),maxX:Math.max(...points.map(p=>p.x)),minY:Math.min(...points.map(p=>p.y)),maxY:Math.max(...points.map(p=>p.y)),minZ:Math.min(...points.map(p=>p.z)),maxZ:Math.max(...points.map(p=>p.z))}};
}
window.jiangwanStadiumViewer={getState:()=>({...state,modelId:manifest?.id||null,geometries:renderer.info.memory.geometries,renderedTriangles:renderer.info.render.triangles,distance:camera.position.distanceTo(controls.target),framing:framing()})};
const render=()=>renderer.render(scene,camera);
const setView=kind=>{
 const distance=Math.max(VIEW_CONFIG.fitDistance,VIEW_CONFIG.fitWidthDistance/camera.aspect);
 const direction=kind==='field'?new THREE.Vector3(0,1,.2):kind==='front'?new THREE.Vector3(0,.65,1):kind==='rear'?new THREE.Vector3(1,.65,-1):new THREE.Vector3(-1,.70,1);
 camera.position.copy(controls.target).addScaledVector(direction.normalize(),distance);controls.update();render();
};
function chooseAuto(){
 if($('detail').value!=='auto'||!manifest)return;
 const distance=camera.position.distanceTo(controls.target);
 const desired=distance>VIEW_CONFIG.autoLodDistance?'lod':distance<VIEW_CONFIG.autoFullDistance?'full':currentVariant||'full';
 if(desired!==(pendingVariant||currentVariant))loadVariant(desired);
}
controls.addEventListener('change',()=>{render();clearTimeout(autoTimer);autoTimer=setTimeout(chooseAuto,180);});
function downloads(){
 for(const [role,label] of [['raw','原始 GLB'],['full','网页 GLB'],['lod','远景 GLB'],['native','Blender']]){
  const link=document.createElement('a');link.href='assets/models/candidates/yangpu-jiangwan-stadium/'+manifest.assets[role].file;link.textContent=label;link.download='';link.dataset.role=role;$('downloads').append(link);
 }
}
async function loadVariant(variant){
 if(!manifest)return;
 requestedVariant=variant;
 if(variant===pendingVariant||variant===currentVariant&&state.status==='ready')return;
 const version=++generation;pending?.abort();const controller=new AbortController();pending=controller;pendingVariant=variant;
 const deadline=setTimeout(()=>controller.abort(),60000);
 state.status='loading';state.error=null;$('retry').hidden=true;$('status').textContent='正在加载'+(variant==='full'?'完整近景':'简化远景')+'…';
 let candidate=null;
 try{
  const record=manifest.assets[variant];const url='assets/models/candidates/yangpu-jiangwan-stadium/'+record.file;
  const response=await fetch(url,{signal:controller.signal});if(!response.ok)throw Error(`读取失败（${response.status}）`);
  const bytes=await response.arrayBuffer();if(bytes.byteLength!==record.bytes||bytes.byteLength>=100000000)throw Error('模型文件大小不匹配');
  const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
  if(digest!==record.sha256)throw Error('模型校验失败');
  candidate=(await loader.parseAsync(bytes,'')).scene;
  if(version!==generation||controller.signal.aborted)throw new DOMException('Cancelled','AbortError');
  candidate.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
  scene.add(candidate);if(current){scene.remove(current);disposeModelResources(current);}current=candidate;candidate=null;currentVariant=variant;
  state.status='ready';state.variant=variant;state.triangles=record.triangles;
  $('status').textContent=(variant==='full'?'完整近景':'简化远景')+'已加载';
  $('metrics').textContent=`${record.triangles.toLocaleString()} 个三角面 · ${(record.bytes/1000000).toFixed(2)} MB · 江湾体育场看台与入口 · 尺度含估计`;
  render();
 }catch(error){
  if(candidate)disposeModelResources(candidate);
  if(version!==generation)return;
  state.status='error';state.error=error.message;
  $('status').textContent=(error.name==='AbortError'?'模型加载超时':error.message)+(current?'，保留上一模型。':'。');$('retry').hidden=false;
 }finally{clearTimeout(deadline);if(version===generation){pending=null;pendingVariant=null;}}
}
for(const name of ['front','oblique','rear','field','fit'])$(name).addEventListener('click',()=>setView(name));
$('detail').addEventListener('change',()=>{$('detail').value==='auto'?chooseAuto():loadVariant($('detail').value);});
$('retry').addEventListener('click',()=>loadVariant(requestedVariant));
addEventListener('resize',()=>{const {width,height}=viewport();renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();setView('fit');});
setView('fit');
try{
 const response=await fetch('assets/models/candidates/yangpu-jiangwan-stadium/manifest.json');if(!response.ok)throw Error('模型目录无法读取');
 manifest=await response.json();if(manifest.id!=='yangpu-jiangwan-stadium')throw Error('模型身份不匹配');downloads();await loadVariant('full');
}catch(error){state.status='error';state.error=error.message;$('status').textContent=error.message+'，请刷新重试。';}
