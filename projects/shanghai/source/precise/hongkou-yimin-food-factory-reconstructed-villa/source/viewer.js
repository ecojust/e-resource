import * as THREE from '../../../../vendor/three.module.js';
import {GLTFLoader} from '../../../../vendor/GLTFLoader.js';
import {MeshoptDecoder} from '../../../../vendor/meshopt_decoder.module.js';
import {OrbitControls} from '../../../../vendor/OrbitControls.js';
import {disposeModelResources} from '../../../../src/model-resources.js';

const stage = document.querySelector('#model-view');
const status = document.querySelector('#status');
const select = document.querySelector('#detail');
const retry = document.querySelector('#retry');
const folder = 'assets/models/candidates/hongkou-yimin-food-factory-reconstructed-villa/';
// Front-facing cameras are in GLB coordinates. The author exports framing alongside the meshes.
let cameras;
async function start() {
  const response = await fetch(folder+'manifest.json');
  if (!response.ok) throw Error('三维文件目录尚未载入。');
  const manifest = await response.json();
  cameras=manifest.camera_views;
  const renderer = new THREE.WebGLRenderer({antialias:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.65));
  renderer.setClearColor(0x263334);
  stage.replaceChildren(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(36,1,0.008,120);
  const controls = new OrbitControls(camera,renderer.domElement);
  scene.add(new THREE.HemisphereLight(0xfff2dc,0xa3a7ad,2.2));
  const sun = new THREE.DirectionalLight(0xfff5df,2.5);
  sun.position.set(-3,6,5);
  scene.add(sun);
  const loader = new GLTFLoader();
  loader.setMeshoptDecoder(MeshoptDecoder);
  let shown, role, pending, token=0, distance=1, timer, view='oblique';
  function render() { renderer.render(scene,camera); }
  function frame(name) {
    view=name;
    const [target,angle,height,width]=cameras[name];
    distance=0.59*Math.max(height,width/camera.aspect)/Math.tan(THREE.MathUtils.degToRad(camera.fov/2));
    controls.target.set(...target);
    camera.position.copy(controls.target).addScaledVector(new THREE.Vector3(...angle).normalize(),distance);
    controls.minDistance=0.15; controls.maxDistance=distance*7;
    controls.update();
    render();
  }
  function preferred() {
    if (select.value!=='auto') return select.value;
    const relative=camera.position.distanceTo(controls.target)/distance;
    return relative>2.25?'lod':relative<1.85?'full':role||'full';
  }
  async function update() {
    const next=preferred();
    if (pending===next) return;
    if (role===next) {
      ++token; pending=undefined;
      status.textContent=(role==='lod'?'远景':'近景')+' · '+manifest.assets[role].triangles.toLocaleString('zh-CN')+'个三角面';
      retry.hidden=true;return;
    }
    const request=++token;
    pending=next;
    try {
      status.textContent='正在载入三维模型…';
      const asset=manifest.assets[next];
      const mesh=(await loader.loadAsync(folder+asset.file)).scene;
      if (request!==token) { disposeModelResources(mesh); return; }
      if (shown) { scene.remove(shown); disposeModelResources(shown); }
      shown=mesh; scene.add(mesh); role=next; render();
      status.textContent=(next==='lod'?'远景':'近景')+' · '+asset.triangles.toLocaleString('zh-CN')+'个三角面';
      retry.hidden=true;
    } catch (error) {
      if (request===token) { status.textContent=error.message; retry.hidden=false; }
    } finally {
      if (request===token) pending=undefined;
    }
  }
  for (const b of document.querySelectorAll('[data-view]')) b.onclick=()=>frame(b.dataset.view);
  select.onchange=update; retry.onclick=update;
  controls.addEventListener('change',()=>{render();clearTimeout(timer);timer=setTimeout(update,180);});
  const resize=()=>{
    const w=Math.max(stage.clientWidth,1), h=Math.max(stage.clientHeight,1);
    renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix(); frame(view);
  };
  new ResizeObserver(resize).observe(stage); resize(); await update();
}
start().catch(error=>{status.textContent=error.message;retry.hidden=false;retry.onclick=()=>location.reload();});
