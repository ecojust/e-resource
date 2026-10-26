import {distanceToBounds} from './local-model-streamer.js';
import {sameJSON as same} from './ordinary-contracts.js';

const SHA = /^[a-f0-9]{64}$/;
const IDENT = /^[a-z0-9][a-z0-9-]{0,95}$/;
const MACRO = /^\d+-\d+-\d+$/;
const KEY = /^building:[a-f0-9-]{36}$/;
const ACCEPTANCE = ['source_photos', 'identity_footprint', 'height_evidence', 'visible_facade_opening_grid',
  'roof', 'texture_mapping_qa', 'geometry_proof', 'size_proof', 'browser_proof', 'uncertainty'];
const ok = (value, message) => { if (!value) throw Error(message); };
const bounds = value => Array.isArray(value) && value.length === 4 && value.every(Number.isFinite)
  && value[0] <= value[2] && value[1] <= value[3] && value[0] >= -180 && value[2] <= 180 && value[1] >= -90 && value[3] <= 90;
const text = value => typeof value === 'string' && value.trim().length > 0;
export function assetURL(path, baseURL) {
  ok(text(path), 'Missing asset URL');
  if (!/^https?:\/\//.test(path)) {
    ok(!path.startsWith('/') && !/[\\:%?#\u0000-\u001f]/.test(path)
      && path.split('/').every(part => part && part !== '.' && part !== '..'), 'Unsafe project-relative asset path');
  }
  const url = new URL(path, baseURL);
  ok(['http:', 'https:'].includes(url.protocol) && !url.username && !url.password && !url.hash, 'Invalid asset URL');
  return url.href;
}
function fileMetadata(meta, limit) {
  ok(meta && text(meta.file) && SHA.test(meta.sha256) && Number.isInteger(meta.bytes)
    && meta.bytes > 0 && meta.bytes < limit, 'Missing or invalid file byte/SHA contract');
}

/** Exact original response bytes; bounded even if Content-Length is dishonest. */
export async function readVerifiedBytes(meta, baseURL, {fetchFunction = fetch, signal, timeoutMs = 35000,
  limit = 100000000, digest = bytes => crypto.subtle.digest('SHA-256', bytes)} = {}) {
  fileMetadata(meta, limit);
  const controller = new AbortController(), abort = () => controller.abort(signal?.reason || 'cancelled');
  if (signal?.aborted) abort(); else signal?.addEventListener('abort', abort, {once: true});
  const timer = setTimeout(() => controller.abort('timeout'), timeoutMs);
  let reader;
  const cancelReader = () => { reader?.cancel(controller.signal.reason).catch(() => {}); };
  controller.signal.addEventListener('abort', cancelReader, {once: true});
  try {
    if (controller.signal.aborted) throw Error('Asset request cancelled');
    const response = await fetchFunction(assetURL(meta.file, baseURL), {signal: controller.signal});
    ok(response.ok, `Asset request failed (${response.status})`);
    const chunks = []; let length = 0;
    if (response.body?.getReader) {
      reader = response.body.getReader();
      for (;;) {
        const {done, value} = await reader.read(); if (done) break;
        length += value.byteLength;
        ok(length <= meta.bytes && length < limit, 'Asset response exceeds declared size');
        chunks.push(value);
      }
    } else {
      const data = new Uint8Array(await response.arrayBuffer());
      length = data.byteLength; chunks.push(data);
    }
    // No network deadline during hash/JSON/GLTF CPU work. External cancellation remains active.
    clearTimeout(timer);
    ok(length === meta.bytes && length < limit, 'Asset byte length differs');
    const bytes = new Uint8Array(length); let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    const hash = [...new Uint8Array(await digest(bytes))].map(v => v.toString(16).padStart(2, '0')).join('');
    ok(hash === meta.sha256, 'Asset SHA256 differs');
    ok(!controller.signal.aborted, 'Asset request cancelled');
    return bytes.buffer;
  } catch (error) {
    await reader?.cancel().catch(() => {});
    if (controller.signal.reason === 'timeout') throw Error('Asset network timed out');
    if (!controller.signal.aborted) controller.abort('request-failed');
    throw error;
  } finally {
    clearTimeout(timer); signal?.removeEventListener('abort', abort);
    controller.signal.removeEventListener('abort', cancelReader); reader?.releaseLock();
  }
}

export function validateMacroIndex(index, entry, registry, districts) {
  ok(index?.schema === 'precise-building-macro-v1' && index.macro_id === entry.id
    && index.url_base === 'project-root' && Array.isArray(index.models)
    && index.record_count === entry.record_count && index.models.length === entry.record_count, 'Macro index declaration differs');
  ok(registry?.schema === 'city-precise-overrides-v1' && registry.complete === true
    && registry.macros?.length === 1 && registry.macros[0].id === entry.id, 'Expected audited complete single-macro replacement registry');
  const macro = registry.macros[0], ids = new Set(), owners = new Set();
  for (const row of index.models) {
    const owner = row.owner, web = row.assets?.web, lod = row.assets?.lod;
    ok(IDENT.test(row.id) && !ids.has(row.id), 'Duplicate or invalid ordinary building ID'); ids.add(row.id);
    ok(row.accepted === true && row.pending_stages?.length === 0
      && ACCEPTANCE.every(key => row.acceptance?.[key]?.status === 'passed'), 'Ordinary building acceptance is incomplete');
    ok(row.kind === 'building' && row.detail_level === 'architectural' && text(row.name)
      && text(row.source_provider) && text(row.source_url) && Array.isArray(row.source_license) && row.source_license.length
      && Array.isArray(row.asset_license) && row.asset_license.length, 'Missing explicit ordinary building provenance');
    ok(row.district && districts.get(String(row.district.id)) === row.district.name
      && row.districtId === row.district.id && row.district_name === row.district.name, 'District metadata differs');
    ok(Array.isArray(row.anchor) && row.anchor.length === 2 && row.anchor.every(Number.isFinite)
      && row.lng === row.anchor[0] && row.lat === row.anchor[1] && bounds(row.bbox)
      && Number.isFinite(row.height_m) && row.height_m > 0 && typeof row.height_estimated === 'boolean', 'Invalid anchor/height metadata');
    ok(typeof row.navigation?.listed === 'boolean', 'Navigation inclusion must be explicit');
    if (row.navigation.listed) ok(Array.isArray(row.navigation.walkStart) && row.navigation.walkStart.length === 2
      && row.navigation.walkStart.every(Number.isFinite) && Number.isFinite(row.navigation.bearing), 'Curated navigation lacks a reviewed pose');
    fileMetadata(web, 100000000); fileMetadata(lod, 100000000);
    ok(row.model === web.file && row.lod_model === lod.file && row.web_sha256 === web.sha256
      && row.lod_sha256 === lod.sha256 && row.web_bytes === web.bytes && row.lod_bytes === lod.bytes, 'Model aliases disagree with verified asset records');
    ok(owner?.macro_id === entry.id && Number.isInteger(owner.feature_local_id) && owner.feature_local_id > 0
      && !owners.has(owner.feature_local_id) && KEY.test(owner.feature_key)
      && owner.baseline_configuration_sha256 === macro.baseline_configuration_sha256, 'Invalid or duplicate exact ordinary owner');
    owners.add(owner.feature_local_id);
    const near = macro.near.find(item => item.id === owner.near_owner_id);
    const groups = near?.groups.filter(group => group.landmark_id === row.id);
    ok(near && near.baseline_sha256 === owner.baseline_near_sha256
      && same(near.featureLocalIds, owner.baseline_near_feature_local_ids)
      && groups.length === 1 && same(groups[0].local_ids, [owner.feature_local_id])
      && same(groups[0].feature_keys, [owner.feature_key])
      && same(owner.replace_only_local_ids, [owner.feature_local_id])
      && same([...owner.preserve_neighbor_local_ids].sort((a,b)=>a-b), near.featureLocalIds.filter(id=>id!==owner.feature_local_id).sort((a,b)=>a-b)), 'Audited variant does not preserve the exact target and all neighbors');
    const boundary = registry.landmarks?.find(item => item.id === row.id);
    ok(boundary && same(boundary.confirmed_boundary, row.confirmed_boundary)
      && same(boundary.building_ids, [owner.feature_key.slice('building:'.length)])
      && same(boundary.building_part_ids, []), 'Replacement boundary/source UUID differs');
  }
  return index.models;
}

/** Small metadata only; model loading/disposal is delegated to the existing scene. */
export class OrdinaryBuildingCatalog {
  constructor({baseURL, districts, registerMacro, fetchFunction = fetch, onChange = () => {}, onError = () => {},
    maxMacros = 4, maxRecords = 256, maxModels = 2, radius = 700, fringe = 180, modelRadius = 550,
    concurrency = 2, retryDelayMs = 60000, metadataLimit = 8 * 1024 * 1024}) {
    ok(typeof registerMacro === 'function', 'A reversible scene registration adapter is required');
    Object.assign(this, {baseURL, registerMacro, fetchFunction, onChange, onError, maxMacros, maxRecords, maxModels,
      radius, fringe, modelRadius, concurrency, retryDelayMs, metadataLimit});
    this.districts = new Map(districts.map(row => [String(row.id), row.name]));
    this.entries = new Map(); this.wanted = new Set(); this.inflight = new Map();
    this.generation = 0; this.destroyed = false; this.view = null;
    this.stats = {requests: 0, completed: 0, failed: 0, discarded: 0, unloaded: 0};
  }
  setCatalog(catalog) {
    ok(!this.destroyed && catalog?.schema === 'precise-building-catalog-v1'
      && catalog.url_base === 'project-root' && Array.isArray(catalog.macros)
      && catalog.macro_count === catalog.macros.length, 'Invalid ordinary building catalog');
    const prepared = new Map(); let count = 0;
    for (const row of catalog.macros) {
      fileMetadata(row, this.metadataLimit);
      ok(MACRO.test(row.id) && !prepared.has(row.id) && bounds(row.bbox)
        && Number.isInteger(row.record_count) && row.record_count > 0 && row.record_count <= this.maxRecords, 'Macro summary requires subdivision or is invalid');
      assetURL(row.file, this.baseURL);
      prepared.set(row.id, {...row, status: 'idle', retryAt: 0, models: [], session: null}); count += row.record_count;
    }
    ok(count === catalog.record_count, 'Catalog record count differs');
    this.reset(); this.entries = prepared; this.update(this.view);
  }
  update(view) {
    if (this.destroyed || this.resetting || this.updating) return;
    this.updating = true;
    try { this.updateView(view); } finally { this.updating = false; }
  }
  updateView(view) {
    this.view = view && {...view};
    const candidates = [];
    if (view && Number.isFinite(view.lng) && Number.isFinite(view.lat) && (view.mode === 'walk' || view.zoom >= 17.3)) {
      for (const entry of this.entries.values()) {
        const distance = distanceToBounds(view.lng, view.lat, entry.bbox);
        if (distance <= this.radius + (entry.session ? this.fringe : 0)) candidates.push({entry, distance});
      }
    }
    candidates.sort((a,b)=>a.distance-b.distance || a.entry.id.localeCompare(b.entry.id));
    const wanted = new Set(); let records = 0;
    for (const {entry} of candidates) {
      if (wanted.size >= this.maxMacros) break;
      if (records + entry.record_count > this.maxRecords) continue;
      records += entry.record_count; wanted.add(entry.id);
    }
    this.wanted = wanted;
    for (const entry of this.entries.values()) if (!wanted.has(entry.id)) {
      this.inflight.get(entry.id)?.controller.abort('view-changed');
      if (entry.session) this.unload(entry);
    }
    this.refreshWantedModels(); this.pump(); this.notify();
  }
  pump() {
    if (this.destroyed || this.resetting) return;
    for (const id of this.wanted) {
      if (this.inflight.size >= this.concurrency) break;
      const entry = this.entries.get(id);
      if (!entry.session && !this.inflight.has(id) && performance.now() >= entry.retryAt) this.load(entry);
    }
  }
  async load(entry) {
    const generation = this.generation, controller = new AbortController();
    const request = {controller}; this.inflight.set(entry.id, request); entry.status = 'loading'; this.stats.requests++;
    let session;
    const current = () => !this.destroyed && generation === this.generation && this.entries.get(entry.id) === entry
      && this.inflight.get(entry.id) === request && this.wanted.has(entry.id) && !controller.signal.aborted;
    const json = async meta => JSON.parse(new TextDecoder().decode(await readVerifiedBytes(meta, this.baseURL,
      {fetchFunction: this.fetchFunction, signal: controller.signal, limit: this.metadataLimit})));
    try {
      const index = await json(entry);
      ok(current(), 'Obsolete ordinary macro index');
      // Exact-owner-bindings alone is deliberately not sufficient to render.
      fileMetadata(index.replacement_registry, this.metadataLimit);
      const registry = await json(index.replacement_registry);
      ok(current(), 'Obsolete ordinary replacement registry');
      const models = validateMacroIndex(index, entry, registry, this.districts);
      const otherIds = new Set([...this.entries.values()].flatMap(item => item.models.map(model => model.id)));
      ok(models.every(model => !otherIds.has(model.id)), 'Building ID is already registered in another active macro');
      session = this.registerMacro({owner: `ordinary:${entry.id}`, macroId: entry.id, models, registry, baseURL: this.baseURL});
      ok(session && typeof session.setWanted === 'function' && typeof session.dispose === 'function'
        && typeof session.then !== 'function', 'Scene adapter must return a synchronous reversible macro session');
      if (!current()) { session.dispose(); session = null; this.stats.discarded++; return; }
      entry.models = models; entry.session = session; entry.status = 'ready'; this.stats.completed++;
      this.refreshWantedModels();
    } catch (error) {
      if (session) {
        session.dispose();
        if (entry.session === session) { entry.session = null; entry.models = []; }
      }
      if (current()) { entry.status = 'error'; entry.retryAt = performance.now() + this.retryDelayMs; this.stats.failed++; this.onError(error); }
      else { entry.status = 'idle'; this.stats.discarded++; }
    } finally {
      if (this.inflight.get(entry.id) === request) this.inflight.delete(entry.id);
      this.pump(); this.notify();
    }
  }
  refreshWantedModels() {
    const candidates = [];
    if (this.view) for (const entry of this.entries.values()) if (entry.session && this.wanted.has(entry.id)) {
      for (const model of entry.models) {
        const distance = distanceToBounds(this.view.lng, this.view.lat, model.bbox);
        if (distance <= this.modelRadius) candidates.push({id: model.id, distance});
      }
    }
    candidates.sort((a,b)=>a.distance-b.distance || a.id.localeCompare(b.id));
    const ids = new Set(candidates.slice(0, this.maxModels).map(item => item.id));
    this.requestedModelIds = [...ids];
    for (const entry of this.entries.values()) if (entry.session) entry.session.setWanted(new Set(entry.models.filter(model=>ids.has(model.id)).map(model=>model.id)));
  }
  unload(entry) {
    // The adapter restores near/far/source ownership before disposing geometry.
    const session = entry.session, models = entry.models;
    if (!session) return;
    // Visibility callbacks may synchronously refresh the catalog. Detach the
    // metadata handle first so a nested update cannot dispose the same session.
    entry.session = null; entry.models = []; entry.status = 'idle';
    try { session.setWanted(new Set()); session.dispose(); this.stats.unloaded++; }
    catch (error) { entry.session = session; entry.models = models; entry.status = 'error'; throw error; }
  }
  reset() {
    this.resetting = true;
    try {
      this.generation++; this.wanted.clear();
      this.requestedModelIds = [];
      for (const request of this.inflight.values()) request.controller.abort('generation-changed');
      for (const entry of this.entries.values()) if (entry.session) this.unload(entry);
      this.entries.clear();
    } finally { this.resetting = false; }
  }
  getState() {
    return {...this.stats, catalogMacros: this.entries.size, loading: this.inflight.size,
      activeMacros: [...this.entries.values()].filter(entry=>entry.session).map(entry=>entry.id),
      requestedModelIds: this.requestedModelIds || [],
      residentRecords: [...this.entries.values()].reduce((sum,entry)=>sum+entry.models.length,0),
      maxMacros: this.maxMacros, maxRecords: this.maxRecords, maxModels: this.maxModels};
  }
  notify() { if (!this.destroyed) this.onChange(this.getState()); }
  destroy() { if (!this.destroyed) { this.destroyed = true; this.reset(); } }
}
