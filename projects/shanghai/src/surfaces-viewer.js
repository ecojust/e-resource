import * as THREE from '../vendor/three.module.js';
import {GLTFLoader} from '../vendor/GLTFLoader.js';
import {OrbitControls} from '../vendor/OrbitControls.js';
import {disposeModelResources} from './model-resources.js';

const $ = id => document.getElementById(id);
const viewport = () => ({width:$('surface-view').clientWidth, height:Math.max(1,$('surface-view').clientHeight)});
const scene = new THREE.Scene();
scene.background = new THREE.Color('#10242d');
const camera = new THREE.PerspectiveCamera(42, viewport().width / viewport().height, 1, 2000000);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(viewport().width, viewport().height);
renderer.outputColorSpace = THREE.SRGBColorSpace;
$('surface-view').append(renderer.domElement);
renderer.domElement.setAttribute('aria-label', '地面与水系模型，使用上方范围选择与视角按钮浏览');
const controls = new OrbitControls(camera, renderer.domElement);
controls.maxPolarAngle = Math.PI / 2 - .015;
controls.minDistance = 5;
controls.maxDistance = 1000000;
scene.add(new THREE.HemisphereLight(0xffffff, 0x96a6a0, 2.2));
const sunlight = new THREE.DirectionalLight(0xffffff, 1.6);
sunlight.position.set(-1, 4, 2);
scene.add(sunlight);
const loader = new GLTFLoader();
const R = 6378137, RAD = Math.PI / 180, origin = [121.4737, 31.2304];
const mercY = latitude => Math.log(Math.tan(Math.PI / 4 + latitude * RAD / 2)) * R;
const scale = Math.cos(origin[1] * RAD);
let manifest, current = null, bounds = null, generation = 0, controller = null;
const state = {status:'initializing', selection:null, visibleDistricts:[], loadedBytes:0, error:null};
// Read-only diagnostics used by browser acceptance checks.
window.surfaceViewer = {getState:()=>({...state, visibleDistricts:[...state.visibleDistricts],
  geometries:renderer.info.memory.geometries, triangles:renderer.info.render.triangles})};
const render = () => renderer.render(scene, camera);
controls.addEventListener('change', render);
function applyVisibility(group = current) {
  group?.traverse(object => {
    if (object.isMesh) object.visible = object.name === 'ground-proxy' ? $('show-ground').checked : $('show-water').checked;
  });
  render();
}
function fit(top = false) {
  if (!bounds) return;
  const center = bounds.getCenter(new THREE.Vector3());
  const size = bounds.getSize(new THREE.Vector3());
  const span = Math.max(size.x / camera.aspect, size.z, 100);
  const distance = span / (2 * Math.tan(camera.fov * RAD / 2)) * 1.35;
  controls.target.copy(center);
  camera.position.copy(center).add(top ? new THREE.Vector3(0, distance, .001 * distance) : new THREE.Vector3(.12 * distance, .85 * distance, .65 * distance));
  camera.near = Math.max(.1, distance / 10000);
  camera.far = Math.max(20000, distance * 30);
  camera.updateProjectionMatrix();
  controls.update();
  render();
}
async function verifiedModel(record, signal) {
  const response = await fetch(new URL(`../assets/surfaces/${record.file}`, import.meta.url), {signal});
  if (!response.ok) throw Error(`${record.name}读取失败（${response.status}）`);
  const bytes = await response.arrayBuffer();
  if (bytes.byteLength !== record.bytes || bytes.byteLength >= 100000000) throw Error(`${record.name}文件大小不匹配`);
  const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
  if (hash !== record.sha256) throw Error(`${record.name}文件校验失败`);
  const {scene:group} = await loader.parseAsync(bytes, '');
  const [lng,lat] = record.origin_wgs84;
  group.scale.setScalar(scale / Math.cos(lat * RAD));
  group.position.set((lng-origin[0])*RAD*R*scale, 0, -(mercY(lat)-mercY(origin[1]))*scale);
  group.userData.districtId = record.id;
  return group;
}
function links(records) {
  $('downloads').replaceChildren();
  if (records.length !== 1) {
    const link = document.createElement('a');
    link.href = 'assets/surfaces/manifest.json'; link.textContent = '16区文件清单 ↗';
    $('downloads').append(link); return;
  }
  const record = records[0];
  for (const [file,label] of [[record.file,'GLB 模型'],[record.native_file,'Blender 模型'],[record.partition_file,'GIS 边界']]) {
    if (!file) continue;
    const link = document.createElement('a');
    link.href = `assets/surfaces/${file}`; link.textContent = label; link.download = '';
    $('downloads').append(link);
  }
}
async function select(id) {
  if (!manifest) return;
  const records = id === 'all' ? manifest.districts : manifest.districts.filter(r=>r.id===id);
  if (!records.length) { $('status').textContent = '未找到这个行政区，请从列表选择。'; return; }
  const version = ++generation;
  controller?.abort();
  controller = new AbortController();
  const requestController = controller;
  const signal = requestController.signal;
  const deadline = setTimeout(()=>requestController.abort(), 90000);
  const candidate = new THREE.Group();
  $('district').value = id;
  state.status='loading'; state.error=null;
  $('retry').hidden=true;
  try {
    for (let index=0; index<records.length; index++) {
      $('status').textContent = `正在加载${records[index].name}（${index+1}/${records.length}）…`;
      const group = await verifiedModel(records[index], signal);
      candidate.add(group);
      if (version !== generation || signal.aborted) throw new DOMException('Cancelled', 'AbortError');
    }
    applyVisibility(candidate);
    scene.add(candidate);
    if (current) { scene.remove(current); disposeModelResources(current); }
    current=candidate;
    bounds=new THREE.Box3().setFromObject(current);
    state.status='ready'; state.selection=id; state.visibleDistricts=records.map(r=>r.id);
    state.loadedBytes=records.reduce((n,r)=>n+r.bytes,0);
    $('status').textContent = `${id==='all'?'16区':records[0].name}模型已加载`;
    $('details').textContent = `${records.reduce((n,r)=>n+r.triangles,0).toLocaleString()} 个三角面 · ${(state.loadedBytes/1000000).toFixed(2)} MB · 水陆使用同一零高程展示平面`;
    links(records); fit();
  } catch (error) {
    disposeModelResources(candidate);
    if (version !== generation) return;
    state.status='error'; state.error=error.message;
    $('status').textContent = `${error.name==='AbortError'?'加载超时':error.message}。${current?'保留上一个模型。':''}`;
    $('retry').hidden=false;
  } finally { clearTimeout(deadline); }
}
function hashSelection() { return new URLSearchParams(location.hash.slice(1)).get('district') || '310101'; }
$('district').addEventListener('change',()=>{
  const id=$('district').value;
  if (hashSelection()===id) select(id); else location.hash=`district=${id}`;
});
addEventListener('hashchange',()=>select(hashSelection()));
$('retry').addEventListener('click',()=>select($('district').value));
$('show-ground').addEventListener('change',()=>applyVisibility());
$('show-water').addEventListener('change',()=>applyVisibility());
$('fit').addEventListener('click',()=>fit());
$('top').addEventListener('click',()=>fit(true));
addEventListener('resize',()=>{
  const {width,height}=viewport();
  renderer.setSize(width,height); camera.aspect=width/height;
  camera.updateProjectionMatrix(); fit();
});
try {
  const response = await fetch('assets/surfaces/manifest.json');
  if (!response.ok) throw Error(`模型目录读取失败（${response.status}）`);
  manifest = await response.json();
  $('district').replaceChildren(...[{id:'all',name:'全市16区'},...manifest.districts].map(r=>{
    const option=document.createElement('option'); option.value=r.id; option.textContent=r.name; return option;
  }));
  $('district').disabled=false;
  await select(hashSelection());
} catch(error) {
  state.status='error'; state.error=error.message;
  $('status').textContent=`${error.message}，请刷新重试。`;
}
