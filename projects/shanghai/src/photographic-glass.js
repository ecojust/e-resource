/**
 * Explicit photographic glazing contains lighting and reflected scenery already.
 * Display that captured radiance without adding scene lighting or another HDR.
 * The application's original tone mapping, colour factor, alpha and fog remain.
 * Photographic masonry and ordinary procedural glazing are not converted.
 */
import {retainModelTextureOwnership} from './model-resources.js';

export function isPhotographicGlass(material) {
  // Existing Bund12/17 use "Glazing"; the later registrations use "Glass".
  return Boolean(material?.map?.isTexture
    && /^PhotoFacade_.*(?:glass|glazing)/i.test(material.name || ''));
}

/** Call once on an owned imported glTF group, before surfaces/lighting attach. */
export function preparePhotographicGlass(THREE, group) {
  if (!group?.traverse) return {convertedMaterials:0, convertedMeshes:0};
  const replacements = new Map(), plans = [];
  try {
    group.traverse(mesh => {
      if (!mesh.isMesh) return;
      const original = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      const materials = original.map(source => {
        if (!isPhotographicGlass(source) || source.isMeshBasicMaterial) return source;
        if (!replacements.has(source)) {
          const material = new THREE.MeshBasicMaterial();
          // Copy Material's common depth/alpha/blending/clipping state, not the
          // incompatible Standard/Physical shader or its reflection bindings.
          THREE.Material.prototype.copy.call(material, source);
          material.color.copy(source.color);
          material.map = source.map;
          material.alphaMap = source.alphaMap || null;
          material.fog = source.fog;
          material.wireframe = source.wireframe;
          material.wireframeLinewidth = source.wireframeLinewidth;
          material.userData = {...source.userData, photographicRendering: {
            kind:'captured-radiance', sourceMaterialType:source.type,
            sceneLighting:false, supplementalReflection:false,
            toneMapped:source.toneMapped,
          }};
          replacements.set(source, material);
        }
        return replacements.get(source);
      });
      plans.push({mesh, original, materials, array:Array.isArray(mesh.material)});
    });
  } catch (error) {
    // No mesh ownership has changed yet. Original materials retain all maps.
    for (const material of replacements.values()) material.dispose();
    throw error;
  }
  let convertedMeshes = 0;
  for (const {mesh, original, materials, array} of plans) {
    if (materials.some((material, i) => material !== original[i])) {
      mesh.material = array ? materials : materials[0];
      convertedMeshes++;
    }
    if (materials.length && materials.every(isPhotographicGlass)) {
      mesh.castShadow = false;
      mesh.receiveShadow = false;
    }
  }
  for (const source of replacements.keys()) {
    // dispose() releases only the obsolete material program. Shared base maps
    // and auxiliary source textures remain owned by the group until unloading.
    retainModelTextureOwnership(group, Object.values(source).filter(value => value?.isTexture));
    source.dispose();
  }
  return {convertedMaterials:replacements.size, convertedMeshes};
}
