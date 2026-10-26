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
