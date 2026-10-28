import * as THREE from '../vendor/three.module.js';
import {GLTFLoader} from '../vendor/GLTFLoader.js';
import {MeshoptDecoder} from '../vendor/meshopt_decoder.module.js';
import {OrbitControls} from '../vendor/OrbitControls.js';
import {disposeModelResources} from './model-resources.js';
const $=id=>document.getElementById(id);
const viewport=()=>({width:$('model-view').clientWidth,height:Math.max(1,$('model-view').clientHeight)});
const scene=new THREE.Scene();scene.background=new THREE.Color('#172a30');
const camera=new THREE.PerspectiveCamera(42,viewport().width/viewport().height,.1,1000);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(viewport().width,viewport().height);
renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;$('model-view').append(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=3;controls.maxDistance=180;controls.maxPolarAngle=Math.PI/2-.01;
controls.target.set(0,.3,0);
scene.add(new THREE.HemisphereLight(0xffffff,0x94a398,2.0));
const sun=new THREE.DirectionalLight(0xfff8e9,2.4);sun.position.set(-15,24,22);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);
Object.assign(sun.shadow.camera,{left:-17,right:17,top:17,bottom:-17,near:1,far:80});sun.shadow.bias=-.0001;sun.shadow.normalBias=.025;scene.add(sun);
const stage=new THREE.Mesh(new THREE.PlaneGeometry(100,100),new THREE.MeshStandardMaterial({color:0x60746c,roughness:1}));stage.rotation.x=-Math.PI/2;stage.position.y=-2.2;stage.receiveShadow=true;scene.add(stage);
const loader=new GLTFLoader();loader.setMeshoptDecoder(MeshoptDecoder);
let manifest,current=null,generation=0,pending=null,pendingVariant=null,currentVariant=null,autoTimer=null,requestedVariant='full';
const state={status:'initializing',variant:null,error:null,triangles:0};
window.panPoolViewer={getState:()=>({...state,geometries:renderer.info.memory.geometries,renderedTriangles:renderer.info.render.triangles,distance:camera.position.distanceTo(controls.target)})};
const render=()=>renderer.render(scene,camera);
const setView=kind=>{
 const distance=kind==='fit'?Math.max(21,14/camera.aspect):21;
 const direction=kind==='front'?new THREE.Vector3(0,.22,1):kind==='rear'?new THREE.Vector3(-.6,.34,-1):new THREE.Vector3(.60,.36,1);
 camera.position.copy(controls.target).addScaledVector(direction.normalize(),distance);controls.update();render();
};
function chooseAuto(){
 if($('detail').value!=='auto'||!manifest)return;
 const distance=camera.position.distanceTo(controls.target);
 const desired=distance>65?'lod':distance<45?'full':currentVariant||'full';
 if(desired!==(pendingVariant||currentVariant))loadVariant(desired);
}
controls.addEventListener('change',()=>{render();clearTimeout(autoTimer);autoTimer=setTimeout(chooseAuto,180);});
function downloads(){
 for(const [role,label] of [['raw','原始 GLB'],['full','网页 GLB'],['lod','远景 GLB'],['native','Blender']]){
  const link=document.createElement('a');link.href='assets/models/candidates/chongming-pan-pool-bridge/'+manifest.assets[role].file;link.textContent=label;link.download='';$('downloads').append(link);
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
  const record=manifest.assets[variant];const url='assets/models/candidates/chongming-pan-pool-bridge/'+record.file;
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
  $('metrics').textContent=`${record.triangles.toLocaleString()} 个三角面 · ${(record.bytes/1000000).toFixed(2)} MB · 池深2.1米（文献记载）；水位与拱线为推定`;
  render();
 }catch(error){
  if(candidate)disposeModelResources(candidate);
  if(version!==generation)return;
  state.status='error';state.error=error.message;
  $('status').textContent=(error.name==='AbortError'?'模型加载超时':error.message)+(current?'，保留上一模型。':'。');$('retry').hidden=false;
 }finally{clearTimeout(deadline);if(version===generation){pending=null;pendingVariant=null;}}
}
for(const name of ['front','oblique','rear','fit'])$(name).addEventListener('click',()=>setView(name));
$('detail').addEventListener('change',()=>{$('detail').value==='auto'?chooseAuto():loadVariant($('detail').value);});
$('retry').addEventListener('click',()=>loadVariant(requestedVariant));
addEventListener('resize',()=>{const {width,height}=viewport();renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();setView('fit');});
setView('fit');
try{
 const response=await fetch('assets/models/candidates/chongming-pan-pool-bridge/manifest.json');if(!response.ok)throw Error('模型目录无法读取');
 manifest=await response.json();downloads();await loadVariant('full');
}catch(error){state.status='error';state.error=error.message;$('status').textContent=error.message+'，请刷新重试。';}
