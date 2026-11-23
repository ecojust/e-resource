import * as THREE from '../../../../vendor/three.module.js';
import {GLTFLoader} from '../../../../vendor/GLTFLoader.js';
import {MeshoptDecoder} from '../../../../vendor/meshopt_decoder.module.js';
import {OrbitControls} from '../../../../vendor/OrbitControls.js';
import {disposeModelResources} from '../../../../src/model-resources.js';

const id = 'changning-mctyeire-richardson-hall';
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
  if (manifest.id !== id) throw new Error('模型目录与景莲堂页面不符。');
  const subject = document.querySelector('#subject');
  const sideDetails = document.querySelector('#side-material');
  let poses, buttons, currentSubject = 'hall', sidePose;
  const lastView = new Map();
  function makeButtons(cameras) {
    poses = new Map(cameras.map(pose => [pose.name, pose]));
    buttons = cameras.map(pose => {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.view = pose.name;
      button.textContent = pose.label;
      button.onclick = () => { showView(pose.name); update(); };
      return button;
    });
    buttonGroup.replaceChildren(...buttons);
  }
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
    lastView.set(currentSubject, name);
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
    const title = currentSubject === 'side' ? '侧门局部' : '五四楼主楼';
    let triangles = 0;
    shown?.traverse(node => {
      if (!node.isMesh) return;
      triangles += (node.geometry.index?.count || node.geometry.attributes.position.count) / 3;
    });
    return title + ' · ' + ({full:'完整近景', lod:'简化远景'})[role] + ' · ' +
      triangles.toLocaleString('zh-CN') + '个三角面';
  }
  async function update() {
    if (!view) return;
    const role = requestedRole();
    const subjectWhenRequested = currentSubject;
    const resource = currentSubject === 'side' ? 'side-entrance/' + role + '-side-entrance.glb' : manifest.assets[role].file;
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
    status.textContent = '正在载入景莲堂模型…';
    try {
      const model = (await loader.loadAsync(folder + resource)).scene;
      if (request !== generation) { disposeModelResources(model); return; }
      if (shown) { scene.remove(shown); disposeModelResources(shown); }
      shown = model;
      scene.add(shown);
      activeRole = role;
      stage.dataset.role = role;
      stage.dataset.subject = subjectWhenRequested;
      draw();
      retry.hidden = true;
      status.textContent = describe(role);
    } catch (error) {
      if (request === generation) { retry.hidden = false; status.textContent = error.message; }
    } finally {
      if (request === generation) pendingRole = undefined;
    }
  }
  async function sideCamera() {
    if (sidePose) return sidePose;
    const station = await getJSON(new URL('../measurements/side-entrance-photo.json', import.meta.url));
    const [width, height] = station.dimensions;
    const [x, y, z, , , , focal] = station.camera;
    const forward = station.projection[2].slice(0,3);
    const cy = height/2;
    const up = station.projection[1].slice(0,3).map((value,i) => -(value-cy*forward[i])/focal);
    const eye = [x,y,z];
    const length = -y/forward[1];
    sidePose = {name:'side-entrance-photo', label:'Ctny 2017 · 侧门', eye,
      target:eye.map((v,i) => v+length*forward[i]), world_up:up,
      width, height, width_m:length*width/focal,
      principal_point_edge_px:[width/2+.5, height/2+.5]};
    return sidePose;
  }
  let selection = 0;
  async function switchSubject(id, requestedView) {
    const token = ++selection;
    const cameras = id === 'side' ? [await sideCamera()] : views;
    if (token !== selection) return;
    ++generation;
    pendingRole = undefined;
    activeRole = undefined;
    currentSubject = id;
    subject.value = id;
    sideDetails.open = id === 'side';
    if (shown) { scene.remove(shown); disposeModelResources(shown); shown = undefined; }
    delete stage.dataset.role;
    delete stage.dataset.subject;
    makeButtons(cameras);
    const name = requestedView || lastView.get(id);
    showView(poses.has(name) ? name : cameras[0].name);
    await update();
  }
  subject.onchange = () => switchSubject(subject.value).catch(error => {
    status.textContent = error.message;
    retry.hidden = false;
    retry.onclick = () => location.reload();
  });
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
  const initialSubject = hash.get('subject') === 'side' || hash.get('view') === 'side-entrance-photo' ? 'side' : 'hall';
  await switchSubject(initialSubject, hash.get('view'));
}
start().catch(error => {
  status.textContent = error.message;
  retry.hidden = false;
  retry.onclick = () => location.reload();
});
