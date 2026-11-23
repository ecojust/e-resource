import * as THREE from '../../../../vendor/three.module.js';
import {GLTFLoader} from '../../../../vendor/GLTFLoader.js';
import {MeshoptDecoder} from '../../../../vendor/meshopt_decoder.module.js';
import {OrbitControls} from '../../../../vendor/OrbitControls.js';
import {disposeModelResources} from '../../../../src/model-resources.js';

const id = 'xuhui-hunan-280-lane-house-2';
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
  if (manifest.id !== id) throw new Error('模型目录与湖南路280弄2号页面不符。');
  const poses = new Map(views.map(pose => [pose.name, pose]));
  const buttons = views.map(pose => {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.view = pose.name;
    button.textContent = pose.label;
    return button;
  });
  buttonGroup.replaceChildren(...buttons);
  const labels = {raw:'原始 GLB', full:'完整网页 GLB', lod:'远景 GLB', native:'Blender'};
  const downloads = document.querySelector('#downloads');
  for (const [role, label] of Object.entries(labels)) {
    const asset = manifest.assets[role];

    if (!asset?.file) throw new Error('模型目录缺少' + label + '。');
    const link = document.createElement('a');
    link.href = folder + asset.file;
    link.download = asset.file;
    link.textContent = label;
    link.dataset.role = role;
    downloads.append(link);
  }

  for (const [role, label] of Object.entries({fbx:'FBX',obj:'OBJ 与 MTL（ZIP）',stl:'STL（米）'})) {
    const file = manifest.interchange?.[role]?.file;
    if (!file) throw new Error('缺少' + label + '下载记录。');
    const link = document.createElement('a');
    link.href = folder + file;
    link.download = file;
    link.dataset.role = role;
    link.textContent = label;
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
  function draw() { renderer.render(scene, camera); }
  function updateFOV() {
    const pose = poses.get(view);
    const frameWidth = pose.width_m;
    const width = stage.clientWidth;
    const height = stage.clientHeight;
    if (!width || !height) return;
    const fit = Math.min(width / pose.width, height / pose.height);
    const pixelAspectY = pose.pixel_aspect_y || 1;
    const fy = distance * pose.width / (frameWidth * pixelAspectY);
    camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan(height / (2 * fit * fy)));
    camera.updateProjectionMatrix();
    const matrix = camera.projectionMatrix;
    const principal = pose.principal_point_edge_px || pose.principal_point_px || [pose.width / 2, pose.height / 2];
    matrix.elements[0] *= pixelAspectY;
    matrix.elements[4] = -2*(pose.skew_px || 0)*fit/width;
    matrix.elements[8] = (pose.width - 2 * principal[0]) * fit / width;
    matrix.elements[9] = (2 * principal[1] - pose.height) * fit / height;
    camera.projectionMatrixInverse.copy(matrix).invert();
  }
  function showView(name) {
    const pose = poses.get(name);
    view = name;
    const eye = toScene(pose.eye);
    const target = toScene(pose.target);
    distance = eye.distanceTo(target);
    controls.maxDistance = Math.max(24, distance*9);
    camera.up.copy(toScene(pose.world_up || [0,0,1]));
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
    status.textContent = '正在载入湖南路280弄2号模型…';
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
}
start().catch(error => {
  status.textContent = error.message;
  retry.hidden = false;
  retry.onclick = () => location.reload();
});
