/**
 * Buffer payload estimate shared by city and detailed-model budgets. Count GPU
 * buffer owners, not meshes or ArrayBuffers: Three uploads each BufferAttribute
 * separately, while interleaved attributes share their InterleavedBuffer.
 * Material images and renderer-generated morph packing/padding are not included.
 */
export function estimateModelBufferResources(object) {
  const geometries = new Set(), instances = new Set(), skeletons = new Set();
  const buffers = new Set(), dataTextures = new Set();
  let geometryBytes = 0, instanceBytes = 0, skeletonBytes = 0;
  object?.traverse(child => {
    if (child.geometry) geometries.add(child.geometry);
    if (child.isInstancedMesh) instances.add(child);
    if (child.isSkinnedMesh && child.skeleton) skeletons.add(child.skeleton);
  });
  const attributeBytes = attribute => {
    const buffer = attribute?.isInterleavedBufferAttribute ? attribute.data : attribute;
    if (!buffer) return 0;
    const key = buffer.isGLBufferAttribute ? buffer.buffer : buffer;
    if (!key || buffers.has(key)) return 0;
    buffers.add(key);
    const bytes = buffer.array?.byteLength ??
      (buffer.isGLBufferAttribute ? buffer.count * buffer.itemSize * buffer.elementSize : 0);
    return Number.isFinite(bytes) && bytes > 0 ? bytes : 0;
  };
  const dataTextureBytes = texture => {
    if (!texture || texture.userData?.shared || dataTextures.has(texture)) return 0;
    dataTextures.add(texture);
    // Bone matrices are RGBA Float32, instance morph weights Red Float32.
    // Their typed payload gives the actual channel width without assuming RGBA8.
    const bytes = (texture.source?.data || texture.image)?.data?.byteLength;
    return Number.isFinite(bytes) && bytes > 0 ? bytes : 0;
  };
  for (const geometry of geometries) {
    for (const attribute of Object.values(geometry.attributes || {})) geometryBytes += attributeBytes(attribute);
    geometryBytes += attributeBytes(geometry.index);
    for (const attributes of Object.values(geometry.morphAttributes || {})) {
      for (const attribute of attributes) geometryBytes += attributeBytes(attribute);
    }
  }
  for (const mesh of instances) {
    // Allocated capacity is resident even when mesh.count currently draws zero.
    instanceBytes += attributeBytes(mesh.instanceMatrix) + attributeBytes(mesh.instanceColor);
    instanceBytes += dataTextureBytes(mesh.morphTexture);
  }
  for (const skeleton of skeletons) {
    if (skeleton.boneTexture) skeletonBytes += dataTextureBytes(skeleton.boneTexture);
    else if (skeleton.boneMatrices) {
      // r180 allocates this padded RGBA32F texture on first draw. Include that
      // pending allocation without mutating the skeleton during estimation.
      const bones = skeleton.bones?.length ?? skeleton.boneMatrices.length / 16;
      const side = Math.max(4, Math.ceil(Math.sqrt(bones * 4) / 4) * 4);
      if (Number.isFinite(side)) skeletonBytes += side * side * 16;
    }
  }
  return {geometryBytes, instanceBytes, skeletonBytes, dataTextures,
    totalBytes: geometryBytes + instanceBytes + skeletonBytes};
}

/** Mesh triangles submitted once per instance, independent of shared storage. */
export function countExpandedTriangles(object) {
  let triangles = 0;
  object?.traverse(mesh => {
    if (!mesh.isMesh || !mesh.geometry) return;
    const geometry = mesh.geometry;
    const available = geometry.index?.count ?? geometry.attributes?.position?.count ?? 0;
    const start = Math.max(0, geometry.drawRange?.start || 0);
    const count = Math.max(0, Math.min(available - start, geometry.drawRange?.count ?? Infinity));
    let instances = 1;
    if (mesh.isInstancedMesh) instances = mesh.count;
    else if (geometry.isInstancedBufferGeometry) {
      instances = geometry.instanceCount;
      // Infinity is Three's default; finite attribute capacity bounds the draw.
      const capacities = Object.values(geometry.attributes || {}).flatMap(attribute => {
        const buffer = attribute.isInterleavedBufferAttribute ? attribute.data : attribute;
        return buffer?.isInstancedBufferAttribute || buffer?.isInstancedInterleavedBuffer
          ? [buffer.count * buffer.meshPerAttribute] : [];
      });
      if (capacities.length) instances = Math.min(instances, ...capacities);
    }
    if (Number.isFinite(instances) && Number.isFinite(count)) {
      triangles += Math.floor(count / 3) * Math.max(0, Math.floor(instances));
    }
  });
  return triangles;
}

/** Release resources owned by a glTF scene; shared viewer maps stay alive. */
export function disposeModelResources(object) {
  if (!object) return;
  const geometries = new Set(), materials = new Set(), textures = new Set(), images = new Set();
  object.traverse(child => {
    // InstancedMesh owns GPU buffers independently of its shared geometry.
    if (child.isInstancedMesh) child.dispose();
    if (child.geometry) geometries.add(child.geometry);
    for (const material of child.material ? (Array.isArray(child.material) ? child.material : [child.material]) : []) {
      materials.add(material);
      for (const value of Object.values(material)) {
        if (value?.isTexture && !value.userData.shared) textures.add(value);
      }
    }
  });
  for (const geometry of geometries) geometry.dispose();
  for (const material of materials) material.dispose();
  for (const texture of textures) {
    texture.dispose();
    const image = texture.source?.data;
    if (image?.close) images.add(image);
  }
  // glTF can use one ImageBitmap in multiple material texture slots.
  for (const image of images) image.close();
}
