/** Hidden detailed-model cache only; visible objects and city tiles are untouched. */
import {estimateModelBufferResources} from './model-resources.js';

export const MIB = 1024 * 1024;

export function detailIsNearby(distance, maxDistance, wasVisible = false, fringe = 300) {
  return Number.isFinite(distance) && distance < maxDistance + (wasVisible ? fringe : 0);
}

/** Conservative owned GPU estimate, not a measurement of total GPU/CPU memory. */
export function estimateDetailResources(object) {
  const buffers = estimateModelBufferResources(object), textures = new Set();
  object?.traverse(child => {
    for (const material of child.material ? (Array.isArray(child.material) ? child.material : [child.material]) : []) {
      for (const value of Object.values(material)) {
        if (value?.isTexture && !value.userData?.shared && !buffers.dataTextures.has(value)) textures.add(value);
      }
    }
  });
  const {geometryBytes, instanceBytes, skeletonBytes} = buffers;
  let textureBytes = 0, unknownTextures = 0;
  for (const texture of textures) {
    // Compressed uploads already provide their complete authored mip chain.
    if (texture.isCompressedTexture && texture.mipmaps?.length) {
      const bytes = texture.mipmaps.reduce((sum, mip) => sum + (mip.data?.byteLength || 0), 0);
      if (bytes) textureBytes += bytes; else unknownTextures++;
      continue;
    }
    const image = texture.source?.data || texture.image;
    const width = Number(image?.width || image?.naturalWidth || image?.videoWidth);
    const height = Number(image?.height || image?.naturalHeight || image?.videoHeight);
    if (!(width > 0 && height > 0 && Number.isFinite(width * height))) {unknownTextures++; continue;}
    // JPEG/PNG are decoded to RGBA8; their compressed file size is irrelevant.
    // Typed data sources retain their element width. Four channels deliberately
    // overestimate narrower formats; GLTF photographs use the default RGBA8.
    const bytesPerChannel = image?.data?.BYTES_PER_ELEMENT || 1;
    const explicitMips = texture.mipmaps?.length > 1;
    const mipFactor = texture.generateMipmaps !== false || explicitMips ? 4 / 3 : 1;
    textureBytes += Math.ceil(width * height * 4 * bytesPerChannel * mipFactor);
  }
  return {geometryBytes, instanceBytes, skeletonBytes, textureBytes, ownedTextures: textures.size,
    unknownTextures, totalBytes: buffers.totalBytes + textureBytes};
}

/** Pure choice: unknown-size textures cannot safely remain in a hidden cache. */
export function selectHiddenDetailEvictions(records, {maxCount = 2, maxBytes = 32 * MIB} = {}) {
  const hidden = [...records].filter(record => record.object && !record.object.visible && !record.detailWanted);
  const resource = record => record.resourceEstimate || {totalBytes: 0, textureBytes: 0, unknownTextures: 1};
  const photoFull = record => record.activeVariant === 'full' && resource(record).textureBytes > 0;
  const priority = (a, b) =>
    (resource(b).unknownTextures > 0) - (resource(a).unknownTextures > 0)
    || Number(photoFull(b)) - Number(photoFull(a))
    || (photoFull(a) ? resource(b).textureBytes - resource(a).textureBytes : 0)
    || (a.lastDetailUsed || 0) - (b.lastDetailUsed || 0)
    || resource(b).totalBytes - resource(a).totalBytes
    || String(a.id).localeCompare(String(b.id));
  const candidates = hidden.slice().sort(priority);
  let count = hidden.length, bytes = hidden.reduce((sum, record) => sum + resource(record).totalBytes, 0);
  const evict = [];
  for (const record of candidates) {
    if (resource(record).unknownTextures || count > Math.max(0, maxCount) || bytes > Math.max(0, maxBytes)) {
      evict.push(record); count--; bytes -= resource(record).totalBytes;
    }
  }
  return evict;
}

/** Called only after the existing visibility/source-owner update has run. */
export function releaseHiddenDetail(record, disposeObject) {
  if (!record.object || record.object.visible || record.detailWanted) return false;
  disposeObject(record.object);
  record.object = null;
  record.resourceEstimate = null;
  record.activeVariant = null;
  record.status = 'idle';
  // A pending upgrade keeps loadingModel=true until its own finally block.
  return true;
}

/** Decoded late results never enter the scene or acquire source-hide ownership. */
export function retainDetailResult(record, object, {destroyed = false, disposeObject} = {}) {
  if (!destroyed && record.detailWanted) return true;
  disposeObject(object);
  record.status = record.object ? 'loaded' : 'idle';
  return false;
}

export function detailCacheState(records, limits, stats = {}) {
  const resident = [...records].filter(record => record.object);
  const hidden = resident.filter(record => !record.object.visible && !record.detailWanted);
  const sum = (list, key) => list.reduce((n, r) => n + (r.resourceEstimate?.[key] || 0), 0);
  return {resident: resident.length, visible: resident.filter(r => r.object.visible).length,
    hidden: hidden.length, hiddenEstimatedBytes: sum(hidden, 'totalBytes'),
    residentEstimatedBytes: sum(resident, 'totalBytes'), ownedTextureBytes: sum(resident, 'textureBytes'),
    unknownTextures: sum(resident, 'unknownTextures'), maxHiddenCount: limits.maxCount,
    maxHiddenEstimatedBytes: limits.maxBytes, ...stats};
}
