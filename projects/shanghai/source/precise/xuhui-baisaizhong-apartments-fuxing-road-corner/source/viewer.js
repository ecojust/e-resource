import * as THREE from '../../../../vendor/three.module.js';
import {GLTFLoader} from '../../../../vendor/GLTFLoader.js';
import {MeshoptDecoder} from '../../../../vendor/meshopt_decoder.module.js';
import {OrbitControls} from '../../../../vendor/OrbitControls.js';
import {disposeModelResources} from '../../../../src/model-resources.js';

const id = 'xuhui-baisaizhong-apartments-fuxing-road-corner';
const folder = 'assets/models/candidates/' + id + '/';
const stage = document.querySelector('#model-view');
const detail = document.querySelector('#detail');
const status = document.querySelector('#status');
const retry = document.querySelector('#retry');
const buttonGroup = document.querySelector('#model-cameras');

async function getJSON(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error('未能读取 ' + url.toString().split('/').pop());
  return response.json();
}

async function start() {
  const [manifest, views] = await Promise.all([
    getJSON(folder + 'manifest.json'),
    getJSON(new URL('./cameras.json', import.meta.url))
  ]);
  if (manifest.id !== id) throw new Error('模型目录与白赛仲公寓页面不符。');
  const poses = new Map(views.map(pose => [pose.name, pose]));
  const buttons = views.map(pose => {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.view = pose.name;
    button.textContent = pose.label;
    return button;
  });
  buttonGroup.replaceChildren(...buttons);
  const labels = {raw:'原始 GLB', full:'完整网页 GLB', lod:'远景 GLB', native:'Blender', garage1930s:'1930年代汽车间 GLB'};
  const garageAsset = manifest.variants?.garage1930s;
  if (!garageAsset?.file) throw new Error('模型目录缺少历史汽车间。');
  const downloads = document.querySelector('#downloads');
  for (const [role, label] of Object.entries(labels)) {
    const asset = role === 'garage1930s' ? garageAsset : manifest.assets[role];
    
    if (!asset?.file) throw new Error('模型目录缺少' + label + '。');
    const link = document.createElement('a');
    link.href = folder + asset.file;
    link.download = asset.file;
    link.textContent = label;
    link.dataset.role = role;
    downloads.append(link);
  }

  const renderer = new THREE.WebGLRenderer({antialias:true});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.65));
  renderer.setClearColor(0x263334);
  stage.replaceChildren(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(36, 1, .014, 1600);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.minDistance = .09;
  scene.add(new THREE.HemisphereLight(0xfff4e3, 0xa5a6a3, 2.25));
  const sun = new THREE.DirectionalLight(0xfff3db, 2.25);
  sun.position.set(-4, 8, 6);
  scene.add(sun);
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const toScene = ([x,y,z]) => new THREE.Vector3(x,z,-y);
  let view, distance, shown, activeRole, pendingRole, generation = 0, timer;
  const hash = new URLSearchParams(location.hash.slice(1));
  const period = document.querySelector('#garage-period');
  const periodStatus = document.querySelector('#period-status');
  let garageLoad;
  let garageModel;
  async function updateGarage(moveCamera = false) {
    const historical = period.value === '1930s';
    if (moveCamera) showView('garage');
    if (!historical) {
      if (garageModel) garageModel.visible = false;
      stage.dataset.garage = 'modern';
      periodStatus.textContent = '';
      draw();
      return;
    }
    periodStatus.textContent = '正在载入历史汽车间…';
    try {
      garageLoad ??= loader.loadAsync(folder + garageAsset.file);
      const gltf = await garageLoad;
      if (!garageModel) {
        garageModel = gltf.scene;
        scene.add(garageModel);
      }
      garageModel.visible = period.value === '1930s';
      stage.dataset.garage = garageModel.visible ? '1930s' : 'modern';
      periodStatus.textContent = garageModel.visible ? '已显示底片中可辨的三片门扇。' : '';
      draw();
    } catch (error) {
      garageLoad = undefined;
      if (period.value === '1930s') {
        period.value = 'modern';
        stage.dataset.garage = 'modern';
        periodStatus.textContent = '汽车间模型载入失败，可重新选择。';
      }
    }
  }
  function draw() { renderer.render(scene, camera); }
  function updateFOV() {
    const pose = poses.get(view);
    const frameWidth = pose.width_m;
    const registeredHeight = frameWidth * pose.height / pose.width;
    const frameHeight = Math.max(registeredHeight, frameWidth / camera.aspect);
    camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan(frameHeight / (2 * distance)));
    camera.updateProjectionMatrix();
  }
  function showView(name) {
    const pose = poses.get(name);
    view = name;
    const eye = toScene(pose.eye);
    const target = toScene(pose.target);
    distance = eye.distanceTo(target);
    controls.maxDistance = Math.max(24, distance*9);
    camera.position.copy(eye);
    controls.target.copy(target);
    updateFOV();
    controls.update();
    stage.dataset.view = name;
    for (const button of buttons) button.setAttribute('aria-pressed', String(button.dataset.view===name));
    draw();
  }
  function requestedRole() {
    if (detail.value !== 'auto') return detail.value;
    const ratio = camera.position.distanceTo(controls.target)/distance;
    if (ratio > 2.25) return 'lod';
    if (ratio < 1.85) return 'full';
    return activeRole === 'lod' ? 'lod' : 'full';
  }
  function describe(role) {
    return ({full:'完整近景', lod:'简化远景'})[role] +
      ' · ' + manifest.assets[role].triangles.toLocaleString('zh-CN') + '个三角面';
  }
  async function update() {
    const role = requestedRole();
    if (pendingRole === role) return;
    if (activeRole === role) {
      generation++;
      pendingRole = undefined;
      retry.hidden = true;
      status.textContent = describe(role);
      return;
    }
    const request = ++generation;
    pendingRole = role;
    status.textContent = '正在载入白赛仲公寓模型…';
    try {
      const model = (await loader.loadAsync(folder + manifest.assets[role].file)).scene;
      if (request !== generation) { disposeModelResources(model); return; }
      if (shown) { scene.remove(shown); disposeModelResources(shown); }
      shown = model;
      scene.add(shown);
      activeRole = role;
      stage.dataset.role = role;
      draw();
      retry.hidden = true;
      status.textContent = describe(role);
    } catch (error) {
      if (request === generation) { retry.hidden = false; status.textContent = error.message; }
    } finally {
      if (request === generation) pendingRole = undefined;
    }
  }
  for (const b of buttons) b.onclick = () => showView(b.dataset.view);
  detail.onchange = update;
  retry.onclick = update;
  controls.addEventListener('change', () => {
    draw();
    clearTimeout(timer);
    timer = setTimeout(update, 160);
  });
  function resize() {
    const width = Math.max(stage.clientWidth, 1);
    const height = Math.max(stage.clientHeight, 1);
    renderer.setSize(width, height);
    camera.aspect = width / height;
    if (view) { updateFOV(); draw(); }
  }
  new ResizeObserver(resize).observe(stage);
  resize();
  showView(poses.has(hash.get('view')) ? hash.get('view') : views[0].name);
  await update();
  period.onchange = () => updateGarage(true);
  if (hash.get('garage') === '1930s') period.value = '1930s';
  await updateGarage();
}
start().catch(error => {
  status.textContent = error.message;
  retry.hidden = false;
  retry.onclick = () => location.reload();
});
