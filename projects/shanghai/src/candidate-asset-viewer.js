import * as THREE from '../vendor/three.module.js';
import {GLTFLoader} from '../vendor/GLTFLoader.js';
import {MeshoptDecoder} from '../vendor/meshopt_decoder.module.js';
import {OrbitControls} from '../vendor/OrbitControls.js';
import {disposeModelResources} from './model-resources.js';

function getDetailSelector(status) {
  const existing = document.getElementById('detail');
  if (existing) return existing;

  const label = document.createElement('label');
  label.htmlFor = 'detail';
  label.textContent = '模型细节';
  const select = document.createElement('select');
  select.id = 'detail';
  for (const [value, title] of [['auto', '随距离切换'], ['full', '完整近景'], ['lod', '简化远景']]) {
    select.add(new Option(title, value));
  }
  const buttons = status.closest('.panel')?.querySelector('.buttons');
  (buttons ?? status).before(label, select);
  return select;
}

export function showCandidateAssetViewer(modelId, detailViews = {}) {
  const folder = 'assets/models/candidates/' + modelId + '/';
  const screen = document.getElementById('model-view');
  const frontSign = screen.dataset.front === 'negative-z' ? -1 : 1;
  const status = document.getElementById('status');
  const detail = getDetailSelector(status);
  const retry = document.getElementById('retry');
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#172a30');
  scene.add(new THREE.HemisphereLight(0xfff9ea, 0x9a9b91, 1.25));
  const sun = new THREE.DirectionalLight(0xfff3da, 2.1);
  sun.position.set(-52, 72, 48 * frontSign);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, {left: -55, right: 55, bottom: -36, top: 36, near: 1, far: 170});
  sun.shadow.normalBias = 0.025;
  sun.shadow.bias = -0.0001;
  scene.add(sun);
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 3000);
  const renderer = new THREE.WebGLRenderer({antialias: true});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  screen.append(renderer.domElement);
  const controls = new OrbitControls(camera, renderer.domElement);
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const sideSign = screen.dataset.oblique === 'negative-x' ? -1 : 1;
  const obliqueX = Number(screen.dataset.obliqueX);
  const directions = {
    front: [0, 0.06, frontSign],
    oblique: [Number.isFinite(obliqueX) ? obliqueX : sideSign * 0.38, 0.17, frontSign],
    above: [sideSign * 0.16, 1, frontSign * 0.65],
  };
  let bounds, manifest, current, variant, pending, controller, delay;
  let fitDistance = 1;
  let activeDetailView;
  const render = () => renderer.render(scene, camera);

  function frame(view) {
    if (!bounds) return;
    const detailView = detailViews[view];
    activeDetailView = detailView ? view : undefined;
    const center = detailView ? new THREE.Vector3(...detailView.center) : bounds.getCenter(new THREE.Vector3());
    const size = detailView ? new THREE.Vector3(...detailView.size) : bounds.getSize(new THREE.Vector3());
    const direction = new THREE.Vector3(...(detailView?.direction ?? directions[view])).normalize();
    const halfAngle = THREE.MathUtils.degToRad(camera.fov / 2);
    camera.position.copy(center).add(direction);
    camera.lookAt(center);
    const inverse = camera.quaternion.clone().invert();
    // A photographed detail can span less than one metre, including its orbit radius.
    const minimumDistance = detailView ? Math.max(camera.near * 1.5, size.length() * 0.12) : 1;
    fitDistance = minimumDistance;
    for (const x of [-1, 1]) for (const y of [-1, 1]) for (const z of [-1, 1]) {
      const corner = new THREE.Vector3(x, y, z).multiply(size).multiplyScalar(0.5).applyQuaternion(inverse);
      const projected = Math.max(Math.abs(corner.y), Math.abs(corner.x) / camera.aspect);
      fitDistance = Math.max(fitDistance, corner.z + 1.14 * projected / Math.tan(halfAngle));
    }
    controls.target.copy(center);
    controls.minDistance = minimumDistance;
    controls.maxDistance = fitDistance * 6;
    camera.far = Math.max(3000, controls.maxDistance * 2);
    camera.updateProjectionMatrix();
    camera.position.copy(center).addScaledVector(direction, fitDistance);
    controls.update();
    render();
  }
  function desiredVariant() {
    if (detail.value !== 'auto') return detail.value;
    const relative = camera.position.distanceTo(controls.target) / fitDistance;
    if (relative > 2.3) return 'lod';
    if (relative < 1.8) return 'full';
    return pending || variant || 'full';
  }
  async function show(next) {
    if (!manifest || pending === next) return;
    controller?.abort();
    if (next === variant) {
      pending = null;
      retry.hidden = true;
      status.textContent = summary(next);
      return;
    }
    const request = new AbortController();
    controller = request;
    pending = next;
    retry.hidden = true;
    status.textContent = '正在加载模型…';
    let loaded;
    try {
      const asset = manifest.assets[next];
      const response = await fetch(folder + asset.file, {signal: request.signal});
      if (!response.ok) throw Error(`模型读取失败（${response.status}）`);
      const data = await response.arrayBuffer();
      const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', data));
      const hex = Array.from(digest, b => b.toString(16).padStart(2, '0')).join('');
      if (data.byteLength !== asset.bytes || hex !== asset.sha256) throw Error('模型文件校验失败');
      loaded = (await loader.parseAsync(data, '')).scene;
      if (request.signal.aborted) return;
      if (current) {
        scene.remove(current);
        disposeModelResources(current);
      }
      current = loaded;
      loaded = null;
      current.traverse(object => {
        if (object.isMesh) {
          object.castShadow = true;
          object.receiveShadow = true;
        }
      });
      scene.add(current);
      variant = next;
      if (!bounds) {
        bounds = new THREE.Box3().setFromObject(current);
        frame('oblique');
      }
      render();
      status.textContent = summary(next);
    } catch (error) {
      if (!request.signal.aborted) {
        status.textContent = error.message;
        retry.hidden = false;
      }
    } finally {
      if (loaded) disposeModelResources(loaded);
      if (controller === request) pending = null;
    }
  }
  function summary(role) {
    const asset = manifest.assets[role];
    return `${role === 'full' ? '近景' : '远景'} · ${asset.triangles.toLocaleString()} 个三角面 · ${(asset.bytes / 1000000).toFixed(2)} MB`;
  }
  controls.addEventListener('change', () => {
    render();
    clearTimeout(delay);
    delay = setTimeout(() => {
      const next = desiredVariant();
      if (next !== (pending || variant)) show(next);
    }, 180);
  });
  detail.addEventListener('change', () => show(desiredVariant()));
  for (const button of document.querySelectorAll('[data-view]')) {
    button.onclick = () => frame(button.dataset.view);
  }
  new ResizeObserver(() => {
    const {width, height} = screen.getBoundingClientRect();
    renderer.setSize(width, height);
    camera.aspect = width / Math.max(1, height);
    camera.updateProjectionMatrix();
    frame(activeDetailView ?? 'oblique');
  }).observe(screen);

  async function initialize() {
    try {
      const response = await fetch(folder + 'manifest.json');
      if (!response.ok) throw Error(`清单读取失败（${response.status}）`);
      const catalog = await response.json();
      if (catalog.id !== modelId) throw Error('模型身份不符');
      manifest = catalog;
      for (const [role, title] of Object.entries({raw: '原始 GLB', full: '网页 GLB', lod: '远景 GLB', native: 'Blender'})) {
        const link = document.createElement('a');
        link.href = folder + catalog.assets[role].file;
        link.textContent = title;
        link.download = '';
        document.getElementById('downloads').append(link);
      }
      await show('full');
    } catch (error) {
      status.textContent = error.message;
      retry.hidden = false;
    }
  }
  retry.onclick = () => manifest ? show(desiredVariant()) : initialize();
  initialize();
}
