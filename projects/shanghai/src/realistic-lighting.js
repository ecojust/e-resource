/**
 * Local, cached daylight for the geographic Three.js scene.
 *
 * Coordinates are scene metres: X east, Y up, Z south. This module never sets
 * scene.background or scene.environment. Only registered glazing receives the
 * photographic environment (or the small procedural fallback). Generic city
 * blocks are not shadow casters. The reflection photograph is a lighting asset,
 * not a geometric panorama of the model's current location.
 *
 * createRealisticLighting({THREE, scene, renderer}) must be called after the
 * shared WebGL renderer exists. Remove the old hemi/sun/fill lights, or supply
 * their references in `lights`, to avoid lighting the scene twice.
 */

import {HDRLoader} from '../vendor/HDRLoader.js';
import {isPhotographicGlass} from './photographic-glass.js';

const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));
const smoothstep = (minimum, maximum, value) => {
  const t = clamp((value - minimum) / (maximum - minimum), 0, 1);
  return t * t * (3 - 2 * t);
};
const clock = () => globalThis.performance?.now?.() ?? Date.now();

/** The known model names distinguish real glazing from bronze window frames. */
export function isArchitecturalGlazing(material) {
  const name = String(material?.name || '');
  if (material?.isMeshBasicMaterial && isPhotographicGlass(material)) return true;
  return /glass|glaz/i.test(name)
    && !/clock|opal|lamp|frame|mullion|muntin|division|grille|gate|bronze|stone/i.test(name)
    && Boolean(material?.isMeshStandardMaterial || material?.isMeshPhysicalMaterial);
}

/**
 * PMREM temporarily renders to its own FBO. Preserve the actual shared-context
 * framebuffer and viewport, not merely Three's idea of its render target.
 */
function preserveSharedFramebuffer(renderer, task) {
  const gl = renderer.getContext();
  const drawFramebuffer = gl.getParameter(gl.DRAW_FRAMEBUFFER_BINDING);
  const readFramebuffer = gl.getParameter(gl.READ_FRAMEBUFFER_BINDING);
  const viewport = gl.getParameter(gl.VIEWPORT);
  const scissor = gl.getParameter(gl.SCISSOR_BOX);
  const scissorTest = gl.isEnabled(gl.SCISSOR_TEST);
  try {
    return task();
  } finally {
    renderer.resetState();
    gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, drawFramebuffer);
    gl.bindFramebuffer(gl.READ_FRAMEBUFFER, readFramebuffer);
    gl.viewport(...viewport);
    gl.scissor(...scissor);
    if (scissorTest) gl.enable(gl.SCISSOR_TEST);
    else gl.disable(gl.SCISSOR_TEST);
  }
}

function makeSkyReflection(THREE, renderer, sunDirection) {
  const size = 64;
  const directions = [
    (u, v) => [1, -v, -u], (u, v) => [-1, -v, u],
    (u, v) => [u, 1, v], (u, v) => [u, -1, -v],
    (u, v) => [u, -v, 1], (u, v) => [-u, -v, -1],
  ];
  const faces = directions.map(direction => {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = size;
    const context = canvas.getContext('2d');
    const pixels = context.createImageData(size, size);
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      const d = new THREE.Vector3(...direction(2 * (x + .5) / size - 1, 2 * (y + .5) / size - 1)).normalize();
      const top = smoothstep(-.05, .08, d.y);
      const elevation = Math.pow(Math.abs(d.y), .56);
      const horizon = [177, 190, 194];
      const skyPole = [92, 130, 158];
      const groundPole = [57, 63, 61];
      const qx = d.x / (Math.max(.06, d.y) + .22);
      const qz = d.z / (Math.max(.06, d.y) + .22);
      const cloudNoise = Math.sin(qx * 1.7 + .3) * .36 + Math.sin(qz * 2.3) * .32
        + Math.sin(qx * .9 + qz * 1.2) * .22 + Math.sin(qx * 4.7 - qz * 3.1) * .10;
      const cloud = smoothstep(.23, .69, cloudNoise) * smoothstep(.03, .25, d.y) * .55;
      const sunGlow = Math.exp((d.dot(sunDirection) - 1) / .0035) * 95;
      const index = (y * size + x) * 4;
      for (let channel = 0; channel < 3; channel++) {
        const pole = groundPole[channel] * (1 - top) + skyPole[channel] * top;
        let value = horizon[channel] * (1 - elevation) + pole * elevation;
        value = value * (1 - cloud) + [225, 228, 221][channel] * cloud;
        pixels.data[index + channel] = clamp(value + sunGlow, 0, 255);
      }
      pixels.data[index + 3] = 255;
    }
    context.putImageData(pixels, 0, 0);
    return canvas;
  });
  const cube = new THREE.CubeTexture(faces);
  cube.colorSpace = THREE.SRGBColorSpace;
  cube.needsUpdate = true;
  const generator = new THREE.PMREMGenerator(renderer);
  try {
    return preserveSharedFramebuffer(renderer, () => generator.fromCubemap(cube));
  } finally {
    generator.dispose();
    cube.dispose();
  }
}

function makePhotographicReflection(THREE, renderer, texture) {
  texture.mapping = THREE.EquirectangularReflectionMapping;
  const generator = new THREE.PMREMGenerator(renderer);
  try {
    return preserveSharedFramebuffer(renderer, () => generator.fromEquirectangular(texture));
  } finally {
    generator.dispose();
  }
}

function materialsOf(mesh) {
  return (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).filter(Boolean);
}

function horizontalBoxDistance(box, point) {
  const dx = Math.max(box.min.x - point.x, 0, point.x - box.max.x);
  const dz = Math.max(box.min.z - point.z, 0, point.z - box.max.z);
  return Math.hypot(dx, dz);
}

export function createRealisticLighting({
  THREE, scene, renderer,
  lowMemory = false,
  // Close facade shadows need small light-space texels: the previous 8.2cm
  // sampling produced long serrated edges on grazing-angle window ledges.
  // Keep a local cached map; 4096 over 96m gives 2.34cm texels. Smaller-memory
  // devices retain a bounded 1024 map with the same local coverage.
  shadowSize = lowMemory ? 1024 : 4096,
  shadowHalfExtent = 48,
  casterRadius = 155,
  maxCasterHeight = 150,
  updateDistance = 12,
  minimumRefreshInterval = 240,
  shadowIntensity = .86,
  reflections = true,
  reflectionURL = new URL('../assets/materials/realism-v5/shanghai_riverside_1k.hdr', import.meta.url).href,
  onReflectionReady = () => {},
  lights = {},
} = {}) {
  if (!THREE || !scene || !renderer) throw new Error('Realistic daylight needs THREE, scene and an initialized renderer.');
  const deviceTextureLimit = renderer.capabilities?.maxTextureSize;
  if (Number.isFinite(deviceTextureLimit) && deviceTextureLimit > 0) {
    shadowSize = Math.min(shadowSize, 2 ** Math.floor(Math.log2(deviceTextureLimit)));
  }
  const previousShadowState = {
    enabled: renderer.shadowMap.enabled,
    autoUpdate: renderer.shadowMap.autoUpdate,
    type: renderer.shadowMap.type,
  };
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.autoUpdate = false;
  // PCFSoft ignores radius and samples up to two texels away. With a local
  // metre-scale map that produces self-shadow stripes on oblique facades.
  // A narrower PCF kernel keeps contact shadows without that large footprint.
  renderer.shadowMap.type = THREE.PCFShadowMap;
  // Create the first empty map too: all samplers have a valid cleared depth map.
  renderer.shadowMap.needsUpdate = true;

  const hemisphere = lights.hemisphere || new THREE.HemisphereLight();
  hemisphere.color.set('#c5d3dd'); hemisphere.groundColor.set('#4b514d'); hemisphere.intensity = .65;
  hemisphere.name = 'Bund diffuse sky';
  const sun = lights.sun || new THREE.DirectionalLight();
  sun.color.set('#fff5e5'); sun.intensity = 2.45; sun.name = 'Bund cached morning sun';
  const sunDirection = new THREE.Vector3(.76, .87, .50).normalize();
  sun.target.position.set(0, 22, 0);
  sun.position.copy(sun.target.position).addScaledVector(sunDirection, 310);
  sun.castShadow = true;
  sun.shadow.mapSize.set(shadowSize, shadowSize);
  sun.shadow.camera.left = sun.shadow.camera.bottom = -shadowHalfExtent;
  sun.shadow.camera.right = sun.shadow.camera.top = shadowHalfExtent;
  sun.shadow.camera.near = 5;
  sun.shadow.camera.far = 620;
  sun.shadow.camera.updateProjectionMatrix();
  const shadowTexelMetres = 2 * shadowHalfExtent / shadowSize;
  sun.shadow.bias = -shadowTexelMetres * 1.25 / (sun.shadow.camera.far - sun.shadow.camera.near);
  sun.shadow.normalBias = shadowTexelMetres * .70;
  sun.shadow.radius = .65;
  sun.shadow.intensity = shadowIntensity;
  sun.shadow.autoUpdate = false;
  sun.shadow.needsUpdate = true;
  const fill = lights.fill || new THREE.DirectionalLight();
  fill.color.set('#c5d7e3'); fill.intensity = .20; fill.position.set(-180, 130, -240);
  fill.name = 'Bund weak cool fill'; fill.castShadow = false;
  for (const light of [hemisphere, sun, fill]) if (!light.parent) scene.add(light);
  if (!sun.target.parent) scene.add(sun.target);

  const records = new Map();
  const reflectedMaterials = new Map();
  const backfaceCasterMaterials = new Map();
  const groundReceivers = [];
  let environment = null, reflectionAttempted = false, reflectionError = null;
  let pendingReflection = null, reflectionRequest = false, photographicReflectionError = null;
  let reflectionSource = null;
  let disposed = false, enabled = true, dirty = true, lastRefresh = -Infinity;
  let shadowRefreshRequests = 0, activeSignature = '', activeCasterModels = 0;
  const lastFocus = new THREE.Vector3(Infinity, 0, Infinity);
  const currentFocus = new THREE.Vector3();
  const shadowCenter = new THREE.Vector3();
  const lightRight = new THREE.Vector3(sunDirection.z, 0, -sunDirection.x).normalize();
  const lightUp = new THREE.Vector3().crossVectors(sunDirection, lightRight).normalize();
  const groundUniforms = {center: {value: new THREE.Vector2()}, radius: {value: shadowHalfExtent * .96}};

  function invalidate() { dirty = true; }

  function requestPhotographicReflection() {
    if (!reflectionURL || reflectionRequest || disposed) return;
    reflectionRequest = true;
    // Decode CPU data asynchronously. Do not issue GL calls inside this promise:
    // PMREM conversion belongs to update(), inside the custom map render pass.
    new HDRLoader().loadAsync(reflectionURL).then(texture => {
      if (disposed) { texture.dispose(); return; }
      pendingReflection = texture;
      onReflectionReady();
    }).catch(error => {
      if (!disposed) photographicReflectionError = String(error?.message || error);
    });
  }

  function installReflection(next, source) {
    next.texture.name = source === 'photographic' ? 'Shanghai Riverside photographic glazing reflection' : 'Shared Bund glazing sky';
    next.texture.userData.shared = true;
    next.texture.userData.owner = 'realistic-lighting';
    const previous = environment;
    environment = next;
    reflectionSource = source;
    for (const material of reflectedMaterials.keys()) {
      material.envMap = environment.texture; material.needsUpdate = true;
    }
    previous?.dispose();
  }

  function attachOpaqueCaster(material, group) {
    let entry = backfaceCasterMaterials.get(material);
    if (!entry) {
      // Blender exported the closed stonework as double-sided. Rendering both
      // faces into the depth map self-shadows its front surface. Keep the
      // visible material unchanged; only closed opaque caster depth uses backs.
      // Thin sheets and all glass retain their original depth-side behavior.
      if (!material || material.side !== THREE.DoubleSide || material.shadowSide != null
        || material.transparent || material.opacity < .99
        || /glass|glaz|flag|curtain|fabric|gate|grille|fence|wire|leaf|foliage/i.test(material.name || '')) return;
      entry = {users: new Set(), originalShadowSide: material.shadowSide};
      backfaceCasterMaterials.set(material, entry);
      material.shadowSide = THREE.BackSide;
    }
    entry.users.add(group);
  }

  function attachGlass(material, group) {
    if (!reflections || !isArchitecturalGlazing(material)) return;
    // Calibrated photo glazing already contains the captured reflections.
    // Keep its image colour instead of tinting it and adding a second sky.
    if (/^PhotoFacade_/i.test(material.name || '')) return;
    let entry = reflectedMaterials.get(material);
    if (!entry) {
      entry = {users: new Set(), original: {
        envMap: material.envMap, envMapIntensity: material.envMapIntensity,
        roughness: material.roughness, metalness: material.metalness,
        color: material.color.clone(),
      }};
      reflectedMaterials.set(material, entry);
      material.color.multiplyScalar(.78);
      material.roughness = clamp(material.roughness ?? .22, .16, .30);
      material.metalness = Math.min(material.metalness || 0, .12);
      material.envMapIntensity = 1.05;
      if (environment) material.envMap = environment.texture;
      material.needsUpdate = true;
    }
    entry.users.add(group);
  }

  /** Call after the group has its final geographic position/scale. */
  function configureModel(group, {detailed = false, ground = false, receiver = false, casterFilter = null} = {}) {
    if (!group || disposed) return;
    if (records.has(group)) releaseModel(group);
    group.updateWorldMatrix(true, true);
    const bounds = new THREE.Box3().setFromObject(group);
    const candidate = detailed && !bounds.isEmpty() && bounds.max.y - bounds.min.y <= maxCasterHeight;
    const meshes = [];
    group.traverse(mesh => {
      if (!mesh.isMesh) return;
      const materials = materialsOf(mesh);
      const allGlazing = materials.length > 0 && materials.every(isArchitecturalGlazing);
      // Inferred city windows are opaque facade panels. Omitting their depth
      // casts a false window-grid light pattern through neighboring buildings.
      const opaqueCityGlazing = allGlazing && materials.every(material =>
        material.name === 'Inferred dark glazing' && !material.transparent && material.opacity >= .99);
      meshes.push({mesh, previousCast: mesh.castShadow, previousReceive: mesh.receiveShadow,
        eligible: candidate && (!allGlazing || opaqueCityGlazing) && (!casterFilter || casterFilter(mesh))});
      mesh.castShadow = false;
      mesh.receiveShadow = Boolean(detailed || ground || receiver)
        && !(materials.length > 0 && materials.every(isPhotographicGlass));
      if (detailed) for (const material of materials) {
        attachGlass(material, group);
        if (candidate && !allGlazing) attachOpaqueCaster(material, group);
      }
    });
    records.set(group, {bounds, candidate: candidate && meshes.some(entry => entry.eligible), meshes, attached: Boolean(group.parent)});
    invalidate();
  }

  /** Release old LOD groups before disposing their geometries/materials. */
  function releaseModel(group) {
    const record = records.get(group);
    if (!record) return;
    for (const {mesh, previousCast, previousReceive} of record.meshes) {
      mesh.castShadow = previousCast; mesh.receiveShadow = previousReceive;
    }
    for (const [material, entry] of reflectedMaterials) {
      entry.users.delete(group);
      if (!entry.users.size) {
        Object.assign(material, entry.original, {color: material.color.copy(entry.original.color)});
        material.needsUpdate = true;
        reflectedMaterials.delete(material);
      }
    }
    for (const [material, entry] of backfaceCasterMaterials) {
      entry.users.delete(group);
      if (!entry.users.size) {
        material.shadowSide = entry.originalShadowSide;
        backfaceCasterMaterials.delete(material);
      }
    }
    records.delete(group); invalidate();
  }

  /**
   * Optional receiver for portions of the 2D basemap that have no 3D road mesh.
   * `polygons` = [ [outerRing, ...holeRings], ... ], points = [worldX, worldZ].
   * Supply actual land/road outlines, never a whole neighbourhood rectangle.
   * Existing 3D paving/asphalt should instead use configureModel({ground:true}).
   */
  function setGroundFootprints(polygons = [], {height = .006, opacity = .38} = {}) {
    for (const mesh of groundReceivers) {
      scene.remove(mesh); mesh.geometry.dispose(); mesh.material.dispose();
    }
    groundReceivers.length = 0;
    for (const rings of polygons) {
      if (!Array.isArray(rings) || !rings[0] || rings[0].length < 3) continue;
      const shape = new THREE.Shape(rings[0].map(([x, z]) => new THREE.Vector2(x, -z)));
      for (const ring of rings.slice(1)) {
        if (ring.length >= 3) shape.holes.push(new THREE.Path(ring.map(([x, z]) => new THREE.Vector2(x, -z))));
      }
      const geometry = new THREE.ShapeGeometry(shape);
      geometry.rotateX(-Math.PI / 2); geometry.translate(0, height, 0);
      const material = new THREE.ShadowMaterial({color: '#17232b', opacity, depthWrite: false});
      material.onBeforeCompile = shader => {
        shader.uniforms.uGroundShadowCenter = groundUniforms.center;
        shader.uniforms.uGroundShadowRadius = groundUniforms.radius;
        shader.vertexShader = shader.vertexShader
          .replace('#include <common>', '#include <common>\nvarying vec2 vGroundShadowXZ;')
          .replace('#include <begin_vertex>', '#include <begin_vertex>\nvGroundShadowXZ=(modelMatrix*vec4(position,1.0)).xz;');
        shader.fragmentShader = shader.fragmentShader
          .replace('#include <common>', '#include <common>\nvarying vec2 vGroundShadowXZ;\nuniform vec2 uGroundShadowCenter;\nuniform float uGroundShadowRadius;')
          .replace('opacity * ( 1.0 - getShadowMask() )', 'opacity * ( 1.0 - getShadowMask() ) * (1.0-smoothstep(uGroundShadowRadius*.72,uGroundShadowRadius,distance(vGroundShadowXZ,uGroundShadowCenter)))');
      };
      material.customProgramCacheKey = () => 'bund-local-ground-shadow-v4';
      const mesh = new THREE.Mesh(geometry, material);
      mesh.name = 'Mapped land-only shadow receiver';
      mesh.receiveShadow = true; mesh.castShadow = false;
      mesh.renderOrder = -10; mesh.visible = false;
      scene.add(mesh); groundReceivers.push(mesh);
    }
    invalidate();
  }

  /**
   * Call before renderer.render(), with the avatar or map-centre scene position.
   * There is no GL work on ordinary frames. The reflection is generated once;
   * the shadow map is refreshed only after geometry/visibility or focus changes.
   */
  function update({position, enabled: nextEnabled = true, now = clock()} = {}) {
    if (disposed) return false;
    if (position && Number.isFinite(position.x) && Number.isFinite(position.z)) {
      currentFocus.set(position.x, 0, position.z);
    }
    if (reflections && !reflectionAttempted && reflectedMaterials.size) {
      reflectionAttempted = true;
      try {
        installReflection(makeSkyReflection(THREE, renderer, sunDirection), 'procedural-fallback');
      } catch (error) {
        // A missing reflection must not stop geographic rendering or retry GL
        // creation every frame on a device with limited render-target support.
        reflectionError = String(error?.message || error);
      }
      requestPhotographicReflection();
    }
    if (pendingReflection) {
      const source = pendingReflection; pendingReflection = null;
      try {
        installReflection(makePhotographicReflection(THREE, renderer, source), 'photographic');
      } catch (error) {
        photographicReflectionError = String(error?.message || error);
      } finally {
        source.dispose();
      }
    }
    if (enabled !== Boolean(nextEnabled)) { enabled = Boolean(nextEnabled); invalidate(); }
    const active = [];
    for (const [group, record] of records) {
      if (!group.parent && record.attached) { releaseModel(group); continue; }
      record.attached ||= Boolean(group.parent);
      const nearby = enabled && group.visible && record.candidate
        && horizontalBoxDistance(record.bounds, currentFocus) < casterRadius;
      for (const {mesh, eligible} of record.meshes) mesh.castShadow = Boolean(nearby && eligible);
      if (nearby) active.push(group.uuid);
    }
    activeCasterModels = active.length;
    const signature = active.sort().join('|');
    if (signature !== activeSignature) { activeSignature = signature; invalidate(); }
    // Keep the same light/shader layout even outside the detail district.
    sun.shadow.intensity = enabled && activeCasterModels ? shadowIntensity : 0;
    for (const receiver of groundReceivers) receiver.visible = enabled && activeCasterModels > 0;
    // With no nearby detail the existing map stays cached and its intensity is
    // zero. Moving around the rest of Shanghai must not redraw empty shadows.
    // Keep dirty set so the first re-entering caster refreshes immediately.
    if (!enabled || activeCasterModels === 0) return false;
    const travelled = Math.hypot(currentFocus.x - lastFocus.x, currentFocus.z - lastFocus.z);
    if (travelled >= updateDistance) invalidate();
    if (!dirty || now - lastRefresh < minimumRefreshInterval) return false;

    shadowCenter.set(currentFocus.x, 22, currentFocus.z);
    // Stabilize projected texels as the shadow volume follows the walker.
    const texelSize = shadowTexelMetres;
    for (const axis of [lightRight, lightUp]) {
      const projection = shadowCenter.dot(axis);
      shadowCenter.addScaledVector(axis, Math.round(projection / texelSize) * texelSize - projection);
    }
    sun.target.position.copy(shadowCenter);
    sun.position.copy(shadowCenter).addScaledVector(sunDirection, 310);
    sun.target.updateMatrixWorld(); sun.updateMatrixWorld();
    groundUniforms.center.value.set(shadowCenter.x, shadowCenter.z);
    lastFocus.copy(currentFocus); lastRefresh = now; dirty = false;
    sun.shadow.needsUpdate = true;
    renderer.shadowMap.needsUpdate = true;
    shadowRefreshRequests++;
    return true;
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    for (const group of [...records.keys()]) releaseModel(group);
    setGroundFootprints([]);
    environment?.dispose(); environment = null;
    pendingReflection?.dispose(); pendingReflection = null;
    sun.shadow.map?.dispose(); sun.shadow.map = null;
    sun.shadow.mapPass?.dispose(); sun.shadow.mapPass = null;
    for (const [key, light] of [['hemisphere', hemisphere], ['sun', sun], ['fill', fill]]) {
      if (!lights[key]) scene.remove(light);
    }
    if (!lights.sun) scene.remove(sun.target);
    Object.assign(renderer.shadowMap, previousShadowState, {needsUpdate: true});
  }

  const getState = () => ({
    enabled, shadowSize, shadowHalfExtent, casterRadius,
    registeredModels: records.size, activeCasterModels, shadowRefreshRequests,
    backfaceCasterMaterials: backfaceCasterMaterials.size,
    shadowBias: sun.shadow.bias, shadowNormalBias: sun.shadow.normalBias, shadowRadius: sun.shadow.radius,
    glassMaterials: reflectedMaterials.size, reflectionReady: Boolean(environment), reflectionError,
    reflectionSource, photographicReflectionRequested: reflectionRequest,
    photographicReflectionError,
    groundReceiverPolygons: groundReceivers.length,
    defaultGroundPlaneCreated: false, sceneWideEnvironmentCreated: false,
  });

  return {
    configureModel, releaseModel, setGroundFootprints, update, invalidate, dispose,
    sun, hemisphere, fill,
    get reflectionTexture() { return environment?.texture || null; },
    getState,
    get stats() { return getState(); },
  };
}
