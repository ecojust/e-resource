import {assetURL, readVerifiedBytes} from './ordinary-building-catalog.js';
import {sameJSON as equal} from './ordinary-contracts.js';
import {markVerifiedOrdinaryAsset} from './ordinary-asset-verification.js';
const assert = (condition, message) => { if (!condition) throw Error(message); };

// Explicit ordinary records always use the declared byte/SHA contract, even
// when curated statically. Dynamic ownership and asset verification are separate.
export const isOrdinaryLandmarkRecord = record => record.kind === 'building';

/** Called by the existing loadLandmark branch, before its normal material setup. */
export async function loadOrdinaryLandmarkAsset({record, variant, loader, fetchFunction = fetch, request = new AbortController()}) {
  assert(record.assets?.web && record.assets?.lod, 'Ordinary model lacks explicit web/LOD assets');
  const asset = record.assets[variant === 'distant' ? 'lod' : 'web'];
  const controller = request; record.catalogController = controller;
  const baseURL = record.catalogBaseURL || record.ordinaryBaseURL;
  try {
    const buffer = await readVerifiedBytes(asset, baseURL, {fetchFunction, signal: controller.signal});
    const view = new DataView(buffer);
    assert(buffer.byteLength >= 20 && view.getUint32(0, true) === 0x46546c67
      && view.getUint32(4, true) === 2 && view.getUint32(8, true) === buffer.byteLength
      && view.getUint32(16, true) === 0x4e4f534a && 20 + view.getUint32(12, true) <= buffer.byteLength, 'Invalid ordinary GLB container');
    const doc = JSON.parse(new TextDecoder().decode(new Uint8Array(buffer, 20, view.getUint32(12, true))));
    assert((doc.images || []).every(image => image.bufferView !== undefined && !('uri' in image))
      && (doc.buffers || []).every(item => !('uri' in item)), 'Ordinary GLB has external resource references');
    assert(!controller.signal.aborted && !record.catalogDisposed, 'Obsolete ordinary model');
    // The caller retains/disposes late parsed results using the existing
    // request signal and detailWanted checks; no source or feature owner is acquired by this loader.
    const parsed = await loader.parseAsync(buffer, new URL('.', assetURL(asset.file, baseURL)).href);
    if (!controller.signal.aborted && !record.catalogDisposed) {
      markVerifiedOrdinaryAsset(parsed.scene, {modelId: record.id, variant: variant === 'distant' ? 'lod' : 'web', asset});
    }
    return parsed;
  } finally {
    if (record.catalogController === controller) record.catalogController = null;
  }
}

/** Parameters are existing map-scene closures. This module owns no global scene. */
export function createOrdinaryMacroRegistrar({cityDetails, landmarkRecords, landmarkBoundaries, preciseLandmarkIds,
  tileSuppression, disposeModel, updateLandmarkVisibility, updateBuildingExclusions, reportLandmarks = () => {},
  onError = () => {}, onNearbyRecords = () => {},
  isSourceVisible = record => record.status === 'loaded' && Boolean(record.object?.visible)}) {
  const nearbyByOwner = new Map();
  const publishNearby = () => onNearbyRecords([...nearbyByOwner.values()].flat());
  return ({owner, macroId, models, registry, baseURL}) => {
    const planned = [], adopted = [], borrowedBoundaries = new Set(), allIds = new Set(models.map(row => row.id));
    for (const row of models) {
      const existing = landmarkRecords.get(row.id);
      if (existing) {
        // A curated ordinary navigation item may already own this one model.
        // Reuse it only with full evidence; never overwrite a Bund/other owner.
        assert(existing.kind === 'building' && !existing.catalogOwner && equal(existing.owner, row.owner)
          && existing.web_sha256 === row.web_sha256 && existing.lod_sha256 === row.lod_sha256
          && cityDetails.staticReplacements.landmarks.has(row.id), 'Conflicting existing precise building record');
        adopted.push(existing); continue;
      }
      if (landmarkBoundaries.has(row.id) || preciseLandmarkIds.has(row.id)) {
        assert(preciseLandmarkIds.has(row.id) && cityDetails.staticReplacements.landmarks.has(row.id)
          && equal(landmarkBoundaries.get(row.id), registry.landmarks.find(item=>item.id===row.id)), 'Ordinary boundary ID already exists with different evidence');
        borrowedBoundaries.add(row.id);
      }
      planned.push({...row, url: assetURL(row.assets.web.file, baseURL), lodUrl: assetURL(row.assets.lod.file, baseURL),
        reference: row.reference ? {...row.reference, image: assetURL(row.reference.image, baseURL)} : undefined,
        // EXIF compensation, when required, must be explicitly supplied by the
        // reviewed asset metadata. It is never guessed from a reference photo.
        photo_texture: row.rendering?.photo_texture ?? row.photo_texture,
        catalogOwner: owner, catalogBaseURL: baseURL, catalogWanted: false, catalogDisposed: false,
        maxDistance: 650, status: 'idle', detailWanted: false});
    }
    cityDetails.installMacroReplacements(owner, registry, baseURL);
    let disposed = false, wantedSignature = null;
    const releaseSource = id => {
      try { Promise.resolve(tileSuppression.setOwner(`precise:${id}`, null)).catch(onError); }
      catch (error) { onError(error); throw error; }
    };
    try {
      for (const record of planned) {
        landmarkRecords.set(record.id, record);
        landmarkBoundaries.set(record.id, registry.landmarks.find(item => item.id === record.id));
        preciseLandmarkIds.add(record.id);
      }
      updateLandmarkVisibility(); reportLandmarks();
    } catch (error) {
      for (const record of planned) {
        record.catalogWanted = false; record.detailWanted = false; record.catalogDisposed = true;
        record.catalogController?.abort('registration-failed');
        if (record.object) record.object.visible = false;
        landmarkRecords.delete(record.id);
        if (!borrowedBoundaries.has(record.id)) { landmarkBoundaries.delete(record.id); preciseLandmarkIds.delete(record.id); }
        releaseSource(record.id);
      }
      cityDetails.setVisibleLandmarks([...landmarkRecords.values()].filter(isSourceVisible).map(r=>r.id));
      cityDetails.removeMacroReplacements(owner);
      for (const record of planned) if (record.object) disposeModel(record.object);
      throw error;
    }
    return {
      adoptedIds: adopted.map(record => record.id),
      setWanted(ids) {
        if (disposed) return;
        assert([...ids].every(id => allIds.has(id)), 'Ordinary session received a foreign model ID');
        const signature = [...ids].sort().join('|');
        if (signature === wantedSignature) return;
        wantedSignature = signature;
        for (const record of planned) {
          record.catalogWanted = ids.has(record.id);
          if (!record.catalogWanted) record.catalogController?.abort('ordinary-view-changed');
        }
        updateLandmarkVisibility();
        nearbyByOwner.set(owner, models.map(record => ({...record, modelRequested: ids.has(record.id), macro_id: macroId})));
        publishNearby();
      },
      dispose() {
        if (disposed) return;
        for (const record of planned) {
          record.catalogWanted = false; record.detailWanted = false; record.catalogDisposed = true;
          record.catalogController?.abort('ordinary-macro-unloaded');
          if (record.object) record.object.visible = false;
          releaseSource(record.id);
        }
        // Existing static/curated and other macro models remain in the full set.
        cityDetails.setVisibleLandmarks([...landmarkRecords.values()].filter(isSourceVisible).map(record=>record.id));
        cityDetails.removeMacroReplacements(owner);
        for (const record of planned) {
          landmarkRecords.delete(record.id);
          if (!borrowedBoundaries.has(record.id)) { landmarkBoundaries.delete(record.id); preciseLandmarkIds.delete(record.id); }
          if (record.object) { disposeModel(record.object); record.object = null; }
        }
        disposed = true;
        updateBuildingExclusions(); updateLandmarkVisibility(); reportLandmarks();
        nearbyByOwner.delete(owner); publishNearby();
      },
    };
  };
}
