// CC0 surface grain on metre-sized, UV-less architecture. Source masonry joints
// are deliberately excluded: the GLBs already model their own stone courses.
const SURFACES = {
  stone: {
    id: 'sandstone_blocks_08',
    region: [360 / 1024, 644 / 1024, 260 / 1024, 155 / 1024],
    metres: [260 / 1024 * 3, 155 / 1024 * 3],
    luminance: 0.293948519,
    normalBias: [-0.05697465, -0.06456965],
  },
  granite: {
    id: 'granite_tile_03',
    region: [24 / 1024, 538 / 1024, 292 / 1024, 462 / 1024],
    metres: [292 / 1024 * 1.802, 462 / 1024 * 1.802],
    luminance: 0.112906753,
    normalBias: [-0.004499641, 0.000815976],
  },
  asphalt: {
    id: 'clean_asphalt', region: [0, 0, 1, 1],
    metres: [2.1, 2.1], luminance: 0.061306991,
    normalBias: [-0.000124920, -0.001134648],
  },
  grass: {
    id: 'grass_ground', region: [0, 0, 1, 1],
    metres: [2.51, 2.51], luminance: 0.122335923,
    meanColor: [0.158131379, 0.119077053, 0.049214460],
    normalBias: [-0.000326568, 0.000164488],
  },
};

const PROFILES = {
  stone: { surface: 'stone', contrast: 0.36, normal: 0.08, roughness: 0.25, paving: 0 },
  granite: { surface: 'granite', contrast: 0.24, normal: 0.12, roughness: 0.32, paving: 0 },
  paving: { surface: 'granite', contrast: 0.18, normal: 0.08, roughness: 0.45, paving: 1 },
  curb: { surface: 'granite', contrast: 0.28, normal: 0.14, roughness: 0.40, paving: 0 },
  asphalt: { surface: 'asphalt', contrast: 0.65, normal: 0.25, roughness: 0.60, paving: 0 },
  grass: { surface: 'grass', contrast: 0.58, normal: 0.16, roughness: 0.65, paving: 0 },
  // A restrained grain sample for inferred near facades; it does not claim the
  // observed finish or weathering of an individual ordinary building.
  cityPlaster: { surface: 'stone', contrast: 0.12, normal: 0.035, roughness: 0.20, paving: 0 },
};

function profileFor(material, kind) {
  // A calibrated facade already carries its own source colour and grain.
  // Applying an unrelated quarry sample would erase the photographic detail.
  if (material.map) return null;
  const name = material.name || '';
  if (/^Bund(?:Stone|Frontage)Paving$/i.test(name)) return 'paving';
  if (/^BundGraniteCurb$/i.test(name)) return 'curb';
  if (/^BundRoadSurface$/i.test(name)) return 'asphalt';
  if (/^BundPlantingGrass$/i.test(name)) return 'grass';
  if (/^BundPlantingGranite$/i.test(name)) return 'curb';
  if (kind === 'city-detail' && /inferred.*(plaster|reveal|masonry|wall|base)/i.test(name)) return 'cityPlaster';
  // Large city proxies and distant landmarks keep their inexpensive materials.
  if (!/^(bund|street|streets|architecture)$/i.test(kind)) return null;
  if (/glass|glaz|metal|bronze|brass|iron|zinc|copper|gold|letter|flag|joint|shadow|interior|curtain|frame|paint|gravel/i.test(name)) return null;
  if (/granite/i.test(name)) return 'granite';
  if (/limestone|carved.*stone|pale.*stone|stone.*relief|art.*deco.*stone/i.test(name)) return 'stone';
  return null;
}

const VERTEX_POSITION = `
  // Match Three's position pipeline, including EXT_mesh_gpu_instancing and the
  // glTF node scale used to decode quantized meshopt positions.
  vec4 archPosition = vec4(transformed, 1.0);
  #ifdef USE_BATCHING
    archPosition = batchingMatrix * archPosition;
  #endif
  #ifdef USE_INSTANCING
    archPosition = instanceMatrix * archPosition;
  #endif
  vArchWorld = (modelMatrix * archPosition).xyz;
`;

const FRAGMENT_COMMON = `
  varying vec3 vArchWorld;
  uniform sampler2D archColorMap;
  uniform sampler2D archNormalMap;
  uniform sampler2D archRoughnessMap;
  uniform vec4 archRegion;
  uniform vec2 archMetres;
  uniform vec2 archNormalBias;
  uniform vec4 archSurface; // source luminance, contrast, normal, roughness mix
  uniform float archPaving;
  uniform float archGrass;
  uniform float archFullAsphalt;
  uniform vec3 archMeanColor;
  uniform float archGrainStrength;
  uniform float archNormalStrength;
  uniform float archRoughnessStrength;

  // One dominant plane, three total map samples; no full-scene triplanar or IBL.
  vec2 archPlane(vec3 position, vec3 geometricNormal) {
    vec3 n = abs(geometricNormal);
    if (n.y >= n.x && n.y >= n.z) return position.xz;
    if (n.x >= n.z) return position.zy;
    return position.xy;
  }

  // Reflect the interior sample at its edges, keeping source grout outside the
  // sampled rectangle. Original images remain unchanged for provenance.
  vec2 archSampleUV(vec2 metrePosition) {
    vec2 mirrored = 1.0 - abs(mod(metrePosition / archMetres, 2.0) - 1.0);
    return archRegion.xy + mirrored * archRegion.zw;
  }

  mat3 archCotangentFrame(vec3 n, vec3 viewPosition, vec2 uv) {
    vec3 dp1 = dFdx(viewPosition);
    vec3 dp2 = dFdy(viewPosition);
    vec2 duv1 = dFdx(uv);
    vec2 duv2 = dFdy(uv);
    vec3 dp2perp = cross(dp2, n);
    vec3 dp1perp = cross(n, dp1);
    vec3 t = dp2perp * duv1.x + dp1perp * duv2.x;
    vec3 b = dp2perp * duv1.y + dp1perp * duv2.y;
    float length2 = max(dot(t, t), dot(b, b));
    float scale = inversesqrt(max(length2, 1e-16));
    return mat3(t * scale, b * scale, n);
  }
`;

const FRAGMENT_COLOR = `
  vec3 archGeometricNormal = normalize(cross(dFdx(vArchWorld), dFdy(vArchWorld)));
  vec2 archPlanePosition = archPlane(vArchWorld, archGeometricNormal);
  vec2 archUV = archSampleUV(archPlanePosition);
  vec2 archWorldPixel = max(abs(dFdx(archPlanePosition)), abs(dFdy(archPlanePosition)));
  // Stop sampling a cropped source once the mip footprint can include its grout.
  float archPixelMetres = max(archWorldPixel.x, archWorldPixel.y);
  // Complete grass/asphalt scans have no cropped masonry grout to exclude.
  // Retain mip-filtered asphalt colour into the middle distance; micro normals
  // still use the original much closer cutoff below. Thresholds are render
  // sampling estimates, not additional site-scale surface or survey claims.
  float archCoverage = archGrass > 0.5
    ? 1.0 - smoothstep(0.5, 2.0, archPixelMetres)
    : archFullAsphalt > 0.5
      ? 1.0 - smoothstep(0.20, 0.90, archPixelMetres)
      : 1.0 - smoothstep(0.025, 0.14, archPixelMetres);
  float archNormalCoverage = 1.0 - smoothstep(0.008, 0.055, max(archWorldPixel.x, archWorldPixel.y));
  if (archCoverage > 0.001) {
    vec3 archSample = texture2D(archColorMap, archUV).rgb;
    float archLuminance = dot(archSample, vec3(0.2126, 0.7152, 0.0722));
    float archGrain = pow(max(archLuminance / archSurface.x, 0.01), archSurface.y);
    // Retain each building's established colour rather than recolouring every
    // facade with the colour of an unrelated source quarry.
    if (archGrass > 0.5) {
      // Preserve small brown/green differences in the scanned grass/soil while
      // keeping the model's chosen mean tint. This does not assert a grass species.
      vec3 archChromatic = pow(max(archSample / archMeanColor, vec3(0.01)), vec3(archSurface.y));
      diffuseColor.rgb *= mix(vec3(1.0), clamp(archChromatic, vec3(0.62), vec3(1.45)), archCoverage * archGrainStrength);
    } else {
      diffuseColor.rgb *= mix(1.0, clamp(archGrain, 0.80, 1.18), archCoverage * archGrainStrength);
    }
  }
  if (archPaving > 0.5 && abs(archGeometricNormal.y) > 0.85) {
    // Broad granite slabs suggested by the promenade reference photograph.
    // 1.20 x 0.60m slabs / 4mm joints are reconstruction estimates, not a survey.
    // Retain the existing metre-space mapping; no unlocated transverse bands.
    vec2 archPavingMetres = vArchWorld.xz;
    vec2 archTile = archPavingMetres / vec2(1.20, 0.60);
    archTile.x += mod(floor(archTile.y), 2.0) * 0.5;
    vec2 archEdgeMetres = min(fract(archTile), 1.0 - fract(archTile)) * vec2(1.20, 0.60);
    vec2 archAA = max(fwidth(archPavingMetres) * 0.65, vec2(0.0008));
    vec2 archJoint = 1.0 - smoothstep(vec2(0.002) - archAA, vec2(0.002) + archAA, archEdgeMetres);
    float archJointCoverage = 1.0 - smoothstep(0.025, 0.14, max(archAA.x, archAA.y));
    diffuseColor.rgb *= 1.0 - max(archJoint.x, archJoint.y) * 0.14 * archJointCoverage;
  }
`;

const FRAGMENT_ROUGHNESS = `
  if (archCoverage > 0.001) {
    float archRough = texture2D(archRoughnessMap, archUV).g;
    roughnessFactor = mix(roughnessFactor, clamp(archRough, 0.58, 0.98),
      archSurface.w * archCoverage * archRoughnessStrength);
  }
`;

const FRAGMENT_NORMAL = `
  if (archNormalCoverage * archNormalStrength > 0.001) {
    vec3 archN = texture2D(archNormalMap, archUV).xyz * 2.0 - 1.0;
    // A cropped slab can contain a low-frequency tilt from the photographed
    // block. Remove that mean slope so mirrored repeats do not alternate tilt.
    archN.xy -= archNormalBias;
    archN.xy *= archSurface.z * archNormalCoverage * archNormalStrength;
    normal = normalize(archCotangentFrame(normal, -vViewPosition, archUV) * normalize(archN));
  }
`;

/**
 * @param {object} THREE The same Three.js namespace used by the viewer.
 * @param {object} options baseURL is a directory URL; default resolves next to src/.
 * @returns apply(mesh, kind), configure({grainStrength, normalStrength,
 * roughnessStrength}), dispose(), stats. Call dispose only at viewer shutdown.
 */
export async function createArchitecturalMaterials(THREE, options = {}) {
  const baseURL = String(options.baseURL || new URL('../assets/materials/realism-v4/', import.meta.url));
  const directory = baseURL.endsWith('/') ? baseURL : `${baseURL}/`;
  const loader = new THREE.TextureLoader(options.manager);
  const textures = [];
  // These shared detail maps are optional; a stalled image must not prevent
  // createShanghaiScene from returning and starting the building streamers.
  const timeoutMs = options.timeoutMs ?? 10000;
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) throw new TypeError('Invalid surface texture timeout');
  let abandoned = false, timer;
  const mapped = new WeakSet();
  const controls = {
    archGrainStrength: { value: 1 },
    archNormalStrength: { value: 1 },
    archRoughnessStrength: { value: 1 },
  };
  const stats = { textures: 0, sourceBytes: 7413517, appliedMaterials: 0, byProfile: {}, disposed: false };
  const loaded = {};

  const requests = Object.entries(SURFACES).map(async ([key, surface]) => {
    const mapResults = await Promise.allSettled(['diff', 'nor_gl', 'rough'].map(async (role) => {
      const texture = await loader.loadAsync(`${directory}${surface.id}_${role}_1k.jpg`);
      if (abandoned) {
        texture.dispose();
        throw new Error('Surface texture arrived after loading was abandoned');
      }
      texture.colorSpace = role === 'diff' ? THREE.SRGBColorSpace : THREE.NoColorSpace;
      texture.wrapS = texture.wrapT = THREE.ClampToEdgeWrapping;
      texture.minFilter = THREE.LinearMipmapLinearFilter;
      texture.magFilter = THREE.LinearFilter;
      texture.anisotropy = Math.max(1, Math.min(options.anisotropy || 4, 8));
      texture.userData.shared = true;
      texture.userData.source = `https://polyhaven.com/a/${surface.id}`;
      texture.userData.license = 'CC0-1.0';
      textures.push(texture);
      return texture;
    }));
    const failedMap = mapResults.find(result => result.status === 'rejected');
    if (failedMap) throw failedMap.reason;
    const maps = mapResults.map(result => result.value);
    loaded[key] = { surface, maps };
  });
  // Apply only a complete set. On timeout, release completed maps immediately;
  // callbacks above dispose later arrivals without mutating the live scene.
  try {
    const results = await Promise.race([
      Promise.allSettled(requests),
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error('Optional surface textures timed out; retaining base materials')), timeoutMs);
      }),
    ]);
    const failed = results.find(result => result.status === 'rejected');
    if (failed) throw new Error(`Architectural surface textures failed to load: ${failed.reason?.message || failed.reason}`);
  } catch (error) {
    abandoned = true;
    textures.splice(0).forEach(texture => texture.dispose());
    throw error;
  } finally {
    clearTimeout(timer);
  }
  stats.textures = textures.length;

  function configure(values = {}) {
    for (const [name, key] of [['grainStrength', 'archGrainStrength'], ['normalStrength', 'archNormalStrength'], ['roughnessStrength', 'archRoughnessStrength']]) {
      if (Number.isFinite(values[name])) controls[key].value = Math.max(0, Math.min(values[name], 1));
    }
  }
  configure(options);

  function apply(mesh, kind = 'bund') {
    if (stats.disposed || !mesh?.isMesh) return 0;
    let count = 0;
    for (const material of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
      if (!material?.isMeshStandardMaterial || mapped.has(material)) continue;
      const profileName = profileFor(material, kind);
      if (!profileName) continue;
      const profile = PROFILES[profileName];
      const { surface, maps } = loaded[profile.surface];
      const previousHook = material.onBeforeCompile;
      const previousKey = material.customProgramCacheKey();
      const uniforms = {
        archColorMap: { value: maps[0] },
        archNormalMap: { value: maps[1] },
        archRoughnessMap: { value: maps[2] },
        archRegion: { value: new THREE.Vector4(...surface.region) },
        archMetres: { value: new THREE.Vector2(...surface.metres) },
        archNormalBias: { value: new THREE.Vector2(...surface.normalBias) },
        archSurface: { value: new THREE.Vector4(surface.luminance, profile.contrast, profile.normal, profile.roughness) },
        archPaving: { value: profile.paving },
        archGrass: { value: profileName === 'grass' ? 1 : 0 },
        archFullAsphalt: { value: profileName === 'asphalt' ? 1 : 0 },
        archMeanColor: { value: new THREE.Vector3(...(surface.meanColor || [1, 1, 1])) },
        ...controls,
      };
      material.onBeforeCompile = function (shader, renderer) {
        previousHook.call(this, shader, renderer);
        Object.assign(shader.uniforms, uniforms);
        shader.vertexShader = shader.vertexShader
          .replace('#include <common>', '#include <common>\nvarying vec3 vArchWorld;')
          .replace('#include <worldpos_vertex>', `#include <worldpos_vertex>\n${VERTEX_POSITION}`);
        shader.fragmentShader = shader.fragmentShader
          .replace('#include <common>', `#include <common>\n${FRAGMENT_COMMON}`)
          .replace('#include <color_fragment>', `#include <color_fragment>\n${FRAGMENT_COLOR}`)
          .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>\n${FRAGMENT_ROUGHNESS}`)
          .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>\n${FRAGMENT_NORMAL}`);
      };
      material.customProgramCacheKey = () => `${previousKey}|bund-architectural-v5-street-asphalt2`;
      material.userData.architecturalSurface = profileName;
      material.needsUpdate = true;
      mapped.add(material);
      stats.appliedMaterials++;
      stats.byProfile[profileName] = (stats.byProfile[profileName] || 0) + 1;
      count++;
    }
    return count;
  }

  function dispose() {
    if (stats.disposed) return;
    textures.forEach(texture => texture.dispose());
    textures.length = 0;
    stats.disposed = true;
  }

  return { apply, configure, dispose, stats };
}
