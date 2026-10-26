/** Geographic third-person controls. Distances and speeds are in real metres.
 * No dependencies: MapLibre/Three are exposed through the scene adapter.
 */
const EARTH_RADIUS = 6378137;
const TO_RAD = Math.PI / 180;
const TO_DEG = 180 / Math.PI;
const WALK_SPEED = 4.2;
const RUN_SPEED = 8.5;
const BODY_RADIUS = 0.38;
const BODY_HEIGHT = 1.75;
// The procedural avatar's authored soles are .075 m above its group origin.
// Unknown streets retain this original datum and camera composition.
const DEFAULT_GROUND_HEIGHT = .075;
const MOVEMENT_KEYS = new Set([
  'KeyW', 'KeyA', 'KeyS', 'KeyD',
  'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
  'ShiftLeft', 'ShiftRight', 'KeyQ', 'KeyE', 'KeyR',
]);
const MAP_HANDLERS = [
  'dragPan', 'dragRotate', 'scrollZoom', 'doubleClickZoom',
  'touchZoomRotate', 'touchPitch', 'keyboard', 'boxZoom',
];

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const wrapAngle = value => ((value % 360) + 360) % 360;
const angleDelta = (from, to) => ((to - from + 540) % 360) - 180;
const isTyping = target => Boolean(target && (
  target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName)
));

/** Move a WGS84 point by local east/north metres. */
export function offsetPosition(point, east, north) {
  const cosLatitude = Math.max(0.01, Math.cos(point.lat * TO_RAD));
  return {
    lng: point.lng + east / (EARTH_RADIUS * cosLatitude) * TO_DEG,
    lat: point.lat + north / EARTH_RADIUS * TO_DEG,
  };
}

/** Local distance, sufficient for metre-scale movement anywhere in Shanghai. */
export function distanceMetres(a, b) {
  const latitude = (a.lat + b.lat) * 0.5 * TO_RAD;
  const east = (b.lng - a.lng) * TO_RAD * EARTH_RADIUS * Math.cos(latitude);
  const north = (b.lat - a.lat) * TO_RAD * EARTH_RADIUS;
  return Math.hypot(east, north);
}

function blockingType(value) {
  if (!value) return null;
  if (typeof value === 'string') return value;
  if (value === true) return 'building';
  return value.blocked ? (value.type || value.reason || 'building') : null;
}

export class WalkController {
  constructor(scene, options = {}) {
    if (!scene || typeof scene.setPlayer !== 'function') {
      throw new TypeError('WalkController needs a scene adapter with setPlayer().');
    }
    this.scene = scene;
    this.map = scene.map;
    this.container = options.container || this.map?.getCanvas?.() || this.map?.getContainer?.();
    this.onUpdate = options.onUpdate || (() => {});
    this.onNotice = options.onNotice || (() => {});
    this.position = { lng: 121.4869, lat: 31.2403 };
    this.heading = 45;
    this.bearing = 45;
    this.pitch = 82;
    this.zoom = 21.1 - Math.log2(14 / 12);
    this.cameraDistance = 14;
    this.speed = 0;
    this.groundHeight = DEFAULT_GROUND_HEIGHT;
    this.groundSurface = null;
    this._groundRevision = null;
    this.distance = 0;
    this.mode = 'walk';
    this.enabled = false;
    this.keys = new Set();
    this.moveVector = { x: 0, y: 0 };
    this.manualRun = false;
    this._follow = { ...this.position };
    this._pointer = null;
    this._previousTime = 0;
    this._lastUiUpdate = -Infinity;
    this._lastNotice = -Infinity;
    this._lastCamera = null;
    this._spawnGeneration = 0;
    this._destroyed = false;
    this._listeners = [];
    this._originalHandlers = new Map();
    this._raf = 0;
    this._spawnTimer = 0;
    this._requestFrame = options.requestAnimationFrame || window.requestAnimationFrame.bind(window);
    this._cancelFrame = options.cancelAnimationFrame || window.cancelAnimationFrame.bind(window);
    for (const name of MAP_HANDLERS) {
      const handler = this.map?.[name];
      if (handler?.isEnabled) this._originalHandlers.set(name, handler.isEnabled());
    }
    this._listen(window, 'keydown', event => this._keyDown(event));
    this._listen(window, 'keyup', event => this._keyUp(event));
    this._listen(window, 'blur', () => this._clearInput());
    this._listen(document, 'visibilitychange', () => {
      if (document.hidden) this._clearInput();
      this._previousTime = 0;
    });
    if (this.container) {
      this._listen(this.container, 'pointerdown', event => this._pointerDown(event));
      this._listen(this.container, 'pointermove', event => this._pointerMove(event));
      this._listen(this.container, 'pointerup', event => this._pointerUp(event));
      this._listen(this.container, 'pointercancel', event => this._pointerUp(event));
      this._listen(this.container, 'lostpointercapture', () => { this._pointer = null; });
      this._listen(this.container, 'wheel', event => this._wheel(event), { passive: false });
      this._listen(this.container, 'contextmenu', event => {
        if (this._walking()) event.preventDefault();
      });
    }
    this._tick = this._tick.bind(this);
    this._raf = this._requestFrame(this._tick);
  }

  _listen(target, type, fn, options) {
    target.addEventListener(type, fn, options);
    this._listeners.push(() => target.removeEventListener(type, fn, options));
  }

  _walking() {
    return this.enabled && this.mode === 'walk' && !this._destroyed;
  }

  _clearInput() {
    this.keys.clear();
    this.moveVector = { x: 0, y: 0 };
    this.manualRun = false;
    this.speed = 0;
    this._pointer = null;
  }

  _keyDown(event) {
    if (!this._walking() || isTyping(event.target) || event.metaKey || event.ctrlKey || event.altKey) return;
    if (!MOVEMENT_KEYS.has(event.code)) return;
    event.preventDefault();
    if (event.code === 'KeyR') {
      if (!event.repeat) this.resetCamera();
      return;
    }
    this.keys.add(event.code);
  }

  _keyUp(event) {
    if (this.keys.has(event.code) && this._walking() && !isTyping(event.target)) event.preventDefault();
    this.keys.delete(event.code);
  }

  _pointerDown(event) {
    if (!this._walking() || this._pointer || event.button > 2) return;
    if (event.target?.closest?.('button,input,select,textarea,a,[data-no-camera]')) return;
    this._pointer = { id: event.pointerId, x: event.clientX, y: event.clientY };
    this.container.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  }

  _pointerMove(event) {
    if (!this._walking() || this._pointer?.id !== event.pointerId) return;
    const dx = event.clientX - this._pointer.x;
    const dy = event.clientY - this._pointer.y;
    this._pointer.x = event.clientX;
    this._pointer.y = event.clientY;
    this.setLookDelta(dx, dy);
    event.preventDefault();
  }

  _pointerUp(event) {
    if (this._pointer?.id !== event.pointerId) return;
    if (this.container.hasPointerCapture?.(event.pointerId)) {
      this.container.releasePointerCapture(event.pointerId);
    }
    this._pointer = null;
  }

  _wheel(event) {
    if (!this._walking()) return;
    event.preventDefault();
    const delta = clamp(event.deltaY, -160, 160);
    this.cameraDistance = clamp(this.cameraDistance * Math.exp(delta * 0.0016), 6, 30);
    this.zoom = 21.1 - Math.log2(this.cameraDistance / 12);
    this._lastCamera = null;
  }

  _applyMapInteraction() {
    const walking = this._walking();
    for (const [name, originallyEnabled] of this._originalHandlers) {
      const handler = this.map?.[name];
      if (walking) handler?.disable?.();
      else if (originallyEnabled) handler?.enable?.();
    }
  }

  setEnabled(enabled) {
    this.enabled = Boolean(enabled);
    this._clearInput();
    this._previousTime = 0;
    this._lastCamera = null;
    this._applyMapInteraction();
    if (this.enabled) this._sendPlayer(0, 0);
    this._emitUpdate(performance.now(), true);
  }

  setMode(mode) {
    if (mode !== 'walk' && mode !== 'overview') throw new RangeError('Mode must be walk or overview.');
    if (mode === this.mode) return;
    this.mode = mode;
    this._clearInput();
    this._follow = { ...this.position };
    this._lastCamera = null;
    this._applyMapInteraction();
    this.scene.setAvatarVisible?.(mode === 'walk');
    if (mode === 'walk' && this.enabled) { this._sendPlayer(0, 0); this._updateCamera(1, true); }
    this._emitUpdate(performance.now(), true);
  }

  teleport({ lng, lat, bearing = this.bearing }) {
    if (!Number.isFinite(lng) || !Number.isFinite(lat) || Math.abs(lat) > 85) {
      throw new TypeError('teleport() requires finite WGS84 longitude and latitude.');
    }
    this.position = { lng, lat };
    this._follow = { lng, lat };
    this.bearing = wrapAngle(bearing);
    this.heading = this.bearing;
    this._clearInput();
    this._lastCamera = null;
    this._sendPlayer(0, 0);
    if (this._walking()) this._updateCamera(1, true);
    this._emitUpdate(performance.now(), true);
    // Building/water tiles may arrive shortly after a district teleport.
    // Recheck once loaded and shift to the nearest visible walkable location.
    const generation = ++this._spawnGeneration;
    clearTimeout(this._spawnTimer);
    if (typeof this.scene.findSafePosition === 'function') {
      Promise.resolve(this.scene.findSafePosition({ lng, lat, timeout: 8000 }))
        .then(result => {
          if (this._destroyed || generation !== this._spawnGeneration ||
              distanceMetres(this.position, { lng, lat }) > 1 || !result?.verified) return;
          if (result.adjusted && Number.isFinite(result.lng) && Number.isFinite(result.lat)) {
            this.position = { lng: result.lng, lat: result.lat };
            this._follow = { ...this.position };
            this._lastCamera = null;
            this._sendPlayer(0, 0);
            if (this._walking()) this._updateCamera(1, true);
            this._emitUpdate(performance.now(), true);
            this.onNotice('已将起点放到附近可行走的道路上。');
          }
          if (this._localCollision(this.position, this.position)) this._scheduleSpawnCheck(generation, 0);
        })
        .catch(() => {
          if (generation === this._spawnGeneration) this._scheduleSpawnCheck(generation, 0);
        });
    } else {
      this._scheduleSpawnCheck(generation, 0);
    }
    return { ...this.position };
  }

  _scheduleSpawnCheck(generation, attempt) {
    this._spawnTimer = setTimeout(() => {
      if (this._destroyed || generation !== this._spawnGeneration) return;
      if (this.map?.areTilesLoaded && !this.map.areTilesLoaded()) {
        if (attempt < 16) this._scheduleSpawnCheck(generation, attempt + 1);
        return;
      }
      if (!this._walking() || !(this._collision(this.position) || this._localCollision(this.position, this.position))) return;
      for (const radius of [3, 6, 10, 16, 25, 40, 65]) {
        for (let i = 0; i < 16; i++) {
          const angle = i * Math.PI / 8;
          const candidate = offsetPosition(this.position, Math.sin(angle) * radius, Math.cos(angle) * radius);
          if (!this._collision(candidate) && !this._localCollision(candidate, candidate)) {
            this.position = candidate;
            this._follow = { ...candidate };
            this._lastCamera = null;
            this._sendPlayer(0, 0);
            this._updateCamera(1, true);
            this._emitUpdate(performance.now(), true);
            this.onNotice('已将起点放到附近可行走的位置。');
            return;
          }
        }
      }
      this.onNotice('当前位置周围是建筑或水面，可以从地点列表换一个起点。');
    }, attempt === 0 ? 700 : 450);
  }

  setMoveVector(x, y) {
    x = Number.isFinite(x) ? x : 0;
    y = Number.isFinite(y) ? y : 0;
    const length = Math.hypot(x, y);
    this.moveVector = length > 1 ? { x: x / length, y: y / length } : { x, y };
  }

  setLookDelta(dx, dy) {
    if (!this._walking()) return;
    this.bearing = wrapAngle(this.bearing + dx * 0.22);
    this.pitch = clamp(this.pitch - dy * 0.13, 48, 82);
    this._lastCamera = null;
  }

  setRun(running) {
    this.manualRun = Boolean(running);
  }

  resetCamera() {
    this.bearing = this.heading;
    this.pitch = 82;
    this.cameraDistance = 14;
    this.zoom = 21.1 - Math.log2(14 / 12);
    this._lastCamera = null;
  }

  _collision(position) {
    return blockingType(this.scene.collisionAt?.(position.lng, position.lat));
  }

  _groundAt(position) {
    const surface = this.scene.groundAt?.(position.lng, position.lat);
    return surface && Number.isFinite(surface.height) ? surface : null;
  }

  _syncGround() {
    const previousRevision = this._groundRevision;
    this.groundSurface = this._groundAt(this.position);
    this.groundHeight = this.groundSurface?.height ?? DEFAULT_GROUND_HEIGHT;
    this._groundRevision = this.scene.streetInteractionRevision?.() ?? 0;
    // A model can finish loading around an already stationary visitor. Recover
    // from a newly activated bed/pole instead of trapping the body inside it.
    if (previousRevision !== null && previousRevision !== this._groundRevision &&
        this._walking() && this._localCollision(this.position, this.position)) {
      clearTimeout(this._spawnTimer);
      this._scheduleSpawnCheck(this._spawnGeneration, 0);
    }
  }

  _sendPlayer(speed, dt) {
    this._syncGround();
    this.scene.setPlayer(this.position.lng, this.position.lat, this.heading, speed, dt, this.groundHeight);
  }

  _localCollision(from, to) {
    return blockingType(this.scene.sweepLocalCollision?.(from, to, {
      radius: BODY_RADIUS,
      groundHeight: this._groundAt(from)?.height ?? DEFAULT_GROUND_HEIGHT,
      height: BODY_HEIGHT,
      maxStepHeight: .2,
    }));
  }

  _canOccupy(position, east, north) {
    // A continuous local sweep catches thin poles/rails even at sprint speed;
    // the existing online building/water probes still cover the rest of Shanghai.
    const local = this._localCollision(this.position, position);
    if (local) return local;
    const center = this._collision(position);
    if (center) return center;
    const length = Math.hypot(east, north);
    if (!length) return null;
    const forwardEast = east / length;
    const forwardNorth = north / length;
    const front = offsetPosition(position, forwardEast * BODY_RADIUS, forwardNorth * BODY_RADIUS);
    const frontHit = this._collision(front);
    if (frontHit) return frontHit;
    // One shoulder on each side keeps the avatar from grazing wall corners.
    for (const side of [-1, 1]) {
      const shoulder = offsetPosition(position,
        forwardNorth * BODY_RADIUS * side,
        -forwardEast * BODY_RADIUS * side);
      const hit = this._collision(shoulder);
      if (hit) return hit;
    }
    return null;
  }

  _move(dt, now) {
    this._syncGround();
    let right = this.moveVector.x;
    let forward = this.moveVector.y;
    if (this.keys.has('KeyW') || this.keys.has('ArrowUp')) forward += 1;
    if (this.keys.has('KeyS') || this.keys.has('ArrowDown')) forward -= 1;
    if (this.keys.has('KeyD') || this.keys.has('ArrowRight')) right += 1;
    if (this.keys.has('KeyA') || this.keys.has('ArrowLeft')) right -= 1;
    const magnitude = Math.hypot(right, forward);
    const turning = Number(this.keys.has('KeyE')) - Number(this.keys.has('KeyQ'));
    if (turning) this.bearing = wrapAngle(this.bearing + turning * dt * 75);
    if (magnitude < 0.05) {
      this.speed = 0;
      return;
    }
    if (magnitude > 1) { right /= magnitude; forward /= magnitude; }
    const running = this.manualRun || this.keys.has('ShiftLeft') || this.keys.has('ShiftRight');
    const requestedSpeed = running ? RUN_SPEED : WALK_SPEED;
    const angle = this.bearing * TO_RAD;
    const east = (Math.sin(angle) * forward + Math.cos(angle) * right) * requestedSpeed * dt;
    const north = (Math.cos(angle) * forward - Math.sin(angle) * right) * requestedSpeed * dt;
    const before = this.position;
    const target = offsetPosition(before, east, north);
    const obstruction = this._canOccupy(target, east, north);
    if (!obstruction) {
      this.position = target;
    } else {
      // Axis sliding keeps movement useful alongside long building facades.
      if (Math.abs(east) > 0.0001) {
        const alongEast = offsetPosition(this.position, east, 0);
        if (!this._canOccupy(alongEast, east, 0)) this.position = alongEast;
      }
      if (Math.abs(north) > 0.0001) {
        const alongNorth = offsetPosition(this.position, 0, north);
        if (!this._canOccupy(alongNorth, 0, north)) this.position = alongNorth;
      }
      if (now - this._lastNotice > 4500 && distanceMetres(before, this.position) < 0.002) {
        this._lastNotice = now;
        this.onNotice(obstruction === 'water' ? '前方是水面，请沿岸边或桥梁通行。'
          : obstruction === 'street-step' ? '前方高差较大，请沿平缓的通道绕行。'
          : obstruction === 'street-obstacle' ? '前方有设施或种植区，请沿步道绕行。'
          : '前方有建筑，请沿道路绕行。');
      }
    }
    const travelled = distanceMetres(before, this.position);
    this.distance += travelled;
    this.speed = dt > 0 ? travelled / dt : 0;
    this._syncGround();
    if (travelled > 0.0001) {
      const desiredHeading = wrapAngle(Math.atan2(east, north) * TO_DEG);
      this.heading = wrapAngle(this.heading + angleDelta(this.heading, desiredHeading) * (1 - Math.exp(-dt * 14)));
    }
  }

  _updateCamera(dt, instant = false) {
    this._syncGround();
    const groundOffset = this.groundHeight - DEFAULT_GROUND_HEIGHT;
    const blend = instant ? 1 : 1 - Math.exp(-dt * 14);
    this._follow.lng += (this.position.lng - this._follow.lng) * blend;
    this._follow.lat += (this.position.lat - this._follow.lat) * blend;
    const previous = this._lastCamera;
    if (!instant && previous &&
        distanceMetres(previous, this._follow) < 0.005 &&
        Math.abs(angleDelta(previous.bearing, this.bearing)) < 0.01 &&
        Math.abs(previous.pitch - this.pitch) < 0.01 &&
        Math.abs(previous.groundHeight - this.groundHeight) < 0.0001 &&
        previous.groundRevision === this._groundRevision &&
        Math.abs(previous.distance - this.cameraDistance) < 0.001) return;
    const angle = this.bearing * TO_RAD;
    const targetForDistance = distance => {
      // A close camera follows the actual player to avoid backward movement
      // clipping the shoes while the ordinary follow anchor catches up.
      const lag = clamp((distance - 3.5) / 4.5, 0, 1);
      const anchor = {
        lng: this.position.lng + (this._follow.lng - this.position.lng) * lag,
        lat: this.position.lat + (this._follow.lat - this.position.lat) * lag,
      };
      const ahead = Math.min(3, distance * .20);
      return offsetPosition(anchor, Math.sin(angle) * ahead, Math.cos(angle) * ahead);
    };
    let target = targetForDistance(this.cameraDistance);
    if (typeof this.scene.setCameraFromTo === 'function') {
      let effectiveDistance = this.cameraDistance;
      // Shorten the boom when a wall would cover the avatar. Water does not
      // obstruct the camera, and only nearby loaded building footprints count.
      for (let attempt = 0; attempt < 3; attempt++) {
        target = targetForDistance(effectiveDistance);
        const horizontal = Math.sin(this.pitch * TO_RAD) * effectiveDistance;
        const candidate = offsetPosition(target, -Math.sin(angle) * horizontal, -Math.cos(angle) * horizontal);
        const midpoint = offsetPosition(target, -Math.sin(angle) * horizontal * .6, -Math.cos(angle) * horizontal * .6);
        const targetHeight = groundOffset + .90 + 2.10 * clamp((effectiveDistance - 3.5) / 10.5, 0, 1);
        const fixtureHit = blockingType(this.scene.localCameraCollision?.(
          {...target, alt:targetHeight},
          {...candidate, alt:targetHeight + Math.cos(this.pitch * TO_RAD) * effectiveDistance},
          {radius:.12}));
        if (this._collision(candidate) !== 'building' && this._collision(midpoint) !== 'building' && !fixtureHit) break;
        effectiveDistance = Math.max(3.5, effectiveDistance * .6);
      }
      target = targetForDistance(effectiveDistance);
      const horizontal = Math.sin(this.pitch * TO_RAD) * effectiveDistance;
      const from = offsetPosition(target, -Math.sin(angle) * horizontal, -Math.cos(angle) * horizontal);
      // Default composition places the visitor's centre near 70% screen height
      // and gives the street architecture more room. Lower the target for a
      // shortened boom so the same framing does not crop the feet by a wall.
      const targetHeight = groundOffset + .90 + 2.10 * clamp((effectiveDistance - 3.5) / 10.5, 0, 1);
      this.scene.setCameraFromTo({
        from: { ...from, alt: targetHeight + Math.cos(this.pitch * TO_RAD) * effectiveDistance },
        to: { ...target, alt: targetHeight },
      });
    } else {
      this.scene.setCamera({ ...target, bearing: this.bearing, pitch: this.pitch, zoom: this.zoom, altitude: groundOffset });
    }
    this._lastCamera = { ...this._follow, bearing: this.bearing, pitch: this.pitch, distance: this.cameraDistance,
      groundHeight:this.groundHeight,groundRevision:this._groundRevision };
  }

  _emitUpdate(now, force = false) {
    if (!force && now - this._lastUiUpdate < 100) return;
    this._lastUiUpdate = now;
    this.onUpdate({
      ...this.position,
      heading: this.heading,
      bearing: this.bearing,
      speed: this.speed,
      distance: this.distance,
      mode: this.mode,
      running: this.manualRun || this.keys.has('ShiftLeft') || this.keys.has('ShiftRight'),
      cameraDistance: this.cameraDistance,
      pitch: this.pitch,
      zoom: this.zoom,
      groundHeight: this.groundHeight,
      groundSurfaceId: this.groundSurface?.id ?? null,
    });
  }

  _tick(now) {
    if (this._destroyed) return;
    const dt = this._previousTime ? clamp((now - this._previousTime) / 1000, 0, 0.05) : 0;
    this._previousTime = now;
    if (this._walking() && !document.hidden) {
      this._move(dt, now);
      this._sendPlayer(this.speed, dt);
      this._updateCamera(dt);
      this._emitUpdate(now);
    }
    this._raf = this._requestFrame(this._tick);
  }

  destroy() {
    if (this._destroyed) return;
    this.enabled = false;
    this._applyMapInteraction();
    this._destroyed = true;
    this._spawnGeneration++;
    clearTimeout(this._spawnTimer);
    this._cancelFrame(this._raf);
    this._clearInput();
    for (const remove of this._listeners) remove();
    this._listeners.length = 0;
  }
}
