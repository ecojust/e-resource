import * as THREE from '../vendor/three.module.js';
import {makeWalker} from './walker-model.js';
import {moveOutside, blockedAt, cameraFraction} from './candidate-walk-motion.js';

/** A separate, explicitly unregistered outdoor inspection scene. The full
 * model's projected bounds stay closed: no implied interiors or bridge access.
 * A model is attached only after its viewer has verified its byte/SHA contract.
 */
export function installCandidateWalk({scene, camera, renderer, controls, stage, render, onEnter}) {
  const viewport = document.getElementById('model-view');
  const button = document.createElement('button');
  button.id = 'enter-model-walk'; button.type = 'button'; button.disabled = true;
  button.textContent = '进入模型室外漫游';
  const note = document.createElement('p'); note.className = 'scope';
  note.textContent = '独立模型场景，原址待配准。仅沿外围平地行走，不含室内、登楼或上桥。';
  document.querySelector('.panel').prepend(button, note);
  const ui = document.createElement('div'); ui.className = 'candidate-walk-ui'; ui.hidden = true;
  ui.innerHTML = '<div class="walk-heading"><strong>模型室外漫游 · 原址待配准</strong><button type="button" data-exit>返回模型查看</button><button type="button" data-home>回到起点</button></div><p>WASD / 方向键移动 · Shift 加速 · 拖动转向／仰视 · Esc 返回</p><div class="walk-pad" aria-label="触屏行走"><button type="button" data-key="w" aria-label="向前走">↑</button><button type="button" data-key="a" aria-label="向左走">←</button><button type="button" data-key="s" aria-label="向后走">↓</button><button type="button" data-key="d" aria-label="向右走">→</button></div>';
  viewport.append(ui);
  const keys = new Set(), heldPointers = new Map();
  let active = false, bounds = null, position = {x: 0, z: 0}, yaw = 0, pitch = .1;
  let visitor = null, saved = null, frame = null, previous = null, dragging = null;
  let ground = null, lastBlocked = false, distance = 0, desired = new URLSearchParams(location.hash.slice(1)).get('mode') === 'model-walk';
  const canvas = renderer.domElement; canvas.tabIndex = 0;
  const resetInput = () => { keys.clear(); heldPointers.clear(); dragging = null; previous = null; };
  function resize() {
    const width = viewport.clientWidth, height = Math.max(1, viewport.clientHeight);
    renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    if (active) updateView(); else render();
  }
  function home() {
    position = {x: (bounds.minX + bounds.maxX) / 2, z: bounds.maxZ + 6};
    yaw = 0; pitch = .1; distance = 0; lastBlocked = false; resetInput(); updateView();
  }
  function updateView() {
    visitor.group.position.set(position.x, -.095, position.z); visitor.group.rotation.y = yaw;
    const target = new THREE.Vector3(position.x, 1.35 + pitch * 8, position.z);
    const end = {x: position.x + Math.sin(yaw) * 6.5, z: position.z + Math.cos(yaw) * 6.5};
    const fraction = cameraFraction(position, end, bounds);
    camera.position.set(position.x + (end.x - position.x) * fraction, 1.7 + 1.6 * fraction, position.z + (end.z - position.z) * fraction);
    camera.lookAt(target); render();
  }
  function tick(time) {
    if (!active) return;
    const dt = previous === null ? 0 : Math.min(.05, (time - previous) / 1000); previous = time;
    let forward = Number(keys.has('w')) - Number(keys.has('s'));
    let right = Number(keys.has('d')) - Number(keys.has('a'));
    const length = Math.hypot(forward, right), speed = keys.has('shift') ? 4 : 2;
    if (length) { forward /= length; right /= length; }
    const dx = (right * Math.cos(yaw) - forward * Math.sin(yaw)) * speed * dt;
    const dz = (-forward * Math.cos(yaw) - right * Math.sin(yaw)) * speed * dt;
    const next = moveOutside(position, dx, dz, bounds), travel = Math.hypot(next.x - position.x, next.z - position.z);
    lastBlocked = !!length && travel + 1e-6 < Math.hypot(dx, dz);
    position = next; distance += travel; visitor.animate(dt ? travel / dt : 0, time / 1000);
    updateView(); frame = requestAnimationFrame(tick);
  }
  function enter() {
    if (!bounds || active) return;
    saved = {camera: camera.position.clone(), target: controls.target.clone()};
    if (!visitor) { visitor = makeWalker(); scene.add(visitor.group); }
    active = true; visitor.group.visible = true; controls.enabled = false;
    document.body.classList.add('candidate-walking'); ui.hidden = false;
    if (ground) ground.visible = true;
    history.replaceState(null, '', '#mode=model-walk'); home(); resize(); canvas.focus();
    frame = requestAnimationFrame(tick);
    // Walking requests full geometry. Keep an explicit quality choice in sync
    // when returning to the inspector; automatic mode remains automatic.
    const detail = document.getElementById('detail');
    if (detail.value === 'lod') detail.value = 'full';
    onEnter?.();
  }
  function leave() {
    desired = false;
    if (!active) return;
    active = false; cancelAnimationFrame(frame); resetInput(); visitor.group.visible = false;
    if (ground) ground.visible = false;
    document.body.classList.remove('candidate-walking'); ui.hidden = true; controls.enabled = true;
    history.replaceState(null, '', location.pathname + location.search);
    camera.position.copy(saved.camera); controls.target.copy(saved.target); controls.update(); resize(); button.focus();
  }
  button.addEventListener('click', enter); ui.querySelector('[data-exit]').addEventListener('click', leave);
  ui.querySelector('[data-home]').addEventListener('click', home);
  const keyName = key => ({ArrowUp: 'w', ArrowDown: 's', ArrowLeft: 'a', ArrowRight: 'd'}[key] || key.toLowerCase());
  addEventListener('keydown', event => {
    if (!active || /INPUT|SELECT|TEXTAREA/.test(event.target.tagName)) return;
    if (event.key === 'Escape') { event.preventDefault(); leave(); return; }
    const key = keyName(event.key);
    if (['w', 'a', 's', 'd', 'shift'].includes(key)) { event.preventDefault(); keys.add(key); }
  });
  addEventListener('keyup', event => keys.delete(keyName(event.key)));
  addEventListener('blur', resetInput);
  document.addEventListener('visibilitychange', () => { if (document.hidden) resetInput(); });
  canvas.addEventListener('pointerdown', event => {
    if (!active || event.button !== 0) return;
    canvas.focus(); canvas.setPointerCapture(event.pointerId); dragging = {id: event.pointerId, x: event.clientX, y: event.clientY};
  });
  canvas.addEventListener('pointermove', event => {
    if (!active || dragging?.id !== event.pointerId) return;
    yaw -= (event.clientX - dragging.x) * .005;
    pitch = Math.max(-.2, Math.min(.9, pitch - (event.clientY - dragging.y) * .003));
    dragging.x = event.clientX; dragging.y = event.clientY;
  });
  for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(name, () => { dragging = null; });
  for (const pad of ui.querySelectorAll('[data-key]')) {
    pad.addEventListener('pointerdown', event => {
      if (!active) return;
      event.preventDefault(); pad.setPointerCapture(event.pointerId);
      heldPointers.set(event.pointerId, pad.dataset.key); keys.add(pad.dataset.key);
    });
    for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) pad.addEventListener(name, event => {
      const key = heldPointers.get(event.pointerId); heldPointers.delete(event.pointerId);
      if (![...heldPointers.values()].includes(key)) keys.delete(key);
    });
  }
  function attachModel(model) {
    model.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(model);
    if (!Number.isFinite(box.min.x + box.max.z) || Math.max(Math.abs(box.min.x), Math.abs(box.max.x), Math.abs(box.min.z), Math.abs(box.max.z)) > 35) throw Error('模型超出室外漫游场地范围');
    const next = {minX: box.min.x - .05, maxX: box.max.x + .05, minZ: box.min.z - .05, maxZ: box.max.z + .05};
    bounds = bounds ? {minX: Math.min(bounds.minX, next.minX), maxX: Math.max(bounds.maxX, next.maxX), minZ: Math.min(bounds.minZ, next.minZ), maxZ: Math.max(bounds.maxZ, next.maxZ)} : next;
    // The pool viewer's original stage is below its basin. Add only surrounding
    // ground, leaving the basin visible; the entire pool/bridge stays closed.
    if (!ground && stage.position.y < -1) {
      ground = new THREE.Group();
      const {minX, maxX, minZ, maxZ} = bounds;
      for (const [x0, x1, z0, z1] of [[-50, minX, -50, 50], [maxX, 50, -50, 50], [minX, maxX, -50, minZ], [minX, maxX, maxZ, 50]]) {
        const mesh = new THREE.Mesh(new THREE.PlaneGeometry(x1 - x0, z1 - z0), stage.material);
        mesh.rotation.x = -Math.PI / 2; mesh.position.set((x0 + x1) / 2, -.02, (z0 + z1) / 2); mesh.receiveShadow = true; ground.add(mesh);
      }
      ground.visible = active; scene.add(ground);
    }
    button.disabled = false;
    if (active && blockedAt(position.x, position.z, bounds)) home();
    if (desired) { desired = false; enter(); }
  }
  const api = {enter, leave, resize, attachModel, get active() { return active; }, getState: () => ({active, position: {...position}, yaw, pitch, bounds: bounds && {...bounds}, distance, blocked: lastBlocked, keys: [...keys], scope: 'local-model-outdoor-only', geographicRegistration: false})};
  window.candidateWalk = api;
  return api;
}
