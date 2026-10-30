import {CityDetailStreamer, prepareReplacementRegistry} from './city-detail-streamer.js';
import {sameJSON as equal} from './ordinary-contracts.js';

/** Incremental, audited macro variants. Uses the existing masks and near loader. */
export class OrdinaryCityDetailStreamer extends CityDetailStreamer {
  constructor(options) {
    super(options);
    this.staticReplacements = this.replacements;
    this.macroRegistrations = new Map();
    this.sourceFarRecords = new WeakMap();
    this.registryTransition = false;
  }
  setReplacementOverrides(manifest, baseURL) {
    if (this.macroRegistrations.size) throw Error('Install curated registry before ordinary macro loading');
    super.setReplacementOverrides(manifest, baseURL);
    this.staticReplacements = this.replacements;
  }
  prepareFarObject(object, record) {
    this.sourceFarRecords.set(object, record);
    super.prepareFarObject(object, record);
  }
  syncParents(records) {
    for (const record of records) if (record.object) this.sourceFarRecords.set(record.object, record);
    super.syncParents(records);
  }
  select() { if (!this.registryTransition) super.select(); }
  notify() { if (!this.registryTransition) super.notify(); }

  installMacroReplacements(owner, manifest, baseURL) {
    if (this.destroyed || typeof owner !== 'string' || !owner || this.macroRegistrations.has(owner)) {
      throw Error('Invalid or duplicate ordinary registry owner');
    }
    const prepared = prepareReplacementRegistry(manifest, baseURL);
    if (prepared.macros.size !== 1) throw Error('An ordinary registry must describe exactly one complete macro');
    const [macroId, replacement] = [...prepared.macros][0];
    if ([...this.macroRegistrations.values()].some(item => item.macroId === macroId)) {
      throw Error('Macro already has an ordinary registry owner');
    }
    // A revised macro must retain every existing curated target and its exact
    // baseline ownership. A new opaque near file cannot erase an older target.
    const original = this.staticReplacements.macros.get(macroId);
    if (original) {
      for (const key of ['feature_count', 'baseline_configuration_sha256', 'baseline_far_sha256']) {
        if (replacement[key] !== original[key]) throw Error('Ordinary registry changes curated baseline');
      }
      for (const [id, near] of original.near) {
        const next = replacement.near.get(id);
        if (!next || !equal(near.featureLocalIds, next.featureLocalIds)
          || near.baseline_sha256 !== next.baseline_sha256 || near.baseline_decoded_sha256 !== next.baseline_decoded_sha256
          || near.baseline_file !== next.baseline_file) throw Error('Ordinary registry drops curated near ownership');
        for (const group of near.groups) {
          if (!next.groups.some(other => equal(other, group))) throw Error('Ordinary registry changes a curated target group');
        }
      }
    }
    for (const [id, macro] of this.replacements.macros) if (id !== macroId) {
      for (const landmark of macro.owners.values()) {
        if (prepared.landmarks.has(landmark)) throw Error('Ordinary target ID already belongs to another macro');
      }
    }
    const parents = [...this.parents.values()].filter(parent => parent.id === macroId);
    for (const parent of parents) {
      const far = this.sourceFarRecords.get(parent.object);
      if (!far || far.sha256 !== replacement.baseline_far_sha256 || far.buildingCount !== replacement.feature_count || !far.detailURL) {
        throw Error('Loaded far source does not match ordinary registry');
      }
    }
    // Full validation precedes any detachment. No ordinary model is visible at
    // this stage. Affected near cells may briefly fall back to their far parent.
    const prior = this.replacements;
    const next = {macros: new Map(prior.macros), landmarks: new Set(prior.landmarks)};
    next.macros.set(macroId, replacement);
    for (const id of prepared.landmarks) next.landmarks.add(id);
    this.rebindMacro(macroId, next, prior);
    this.macroRegistrations.set(owner, {macroId, prepared});
    return {macroId, targetIds: [...prepared.landmarks]};
  }

  removeMacroReplacements(owner) {
    const registration = this.macroRegistrations.get(owner);
    if (!registration) return;
    const {macroId, prepared} = registration;
    const ordinaryIds = [...prepared.landmarks].filter(id => !this.staticReplacements.landmarks.has(id));
    if (ordinaryIds.some(id => this.visibleLandmarks.has(id))) {
      throw Error('Hide ordinary models and release their visible owners before removing the macro');
    }
    const prior = this.replacements, next = {macros: new Map(prior.macros), landmarks: new Set(prior.landmarks)};
    const original = this.staticReplacements.macros.get(macroId);
    if (original) next.macros.set(macroId, original); else next.macros.delete(macroId);
    for (const id of ordinaryIds) next.landmarks.delete(id);
    this.rebindMacro(macroId, next, prior);
    this.macroRegistrations.delete(owner);
  }

  rebindMacro(macroId, next, prior) {
    const saved = [...this.parents.values()].filter(parent => parent.id === macroId).map(parent => ({
      object: parent.object, record: this.sourceFarRecords.get(parent.object), active: parent.active,
    }));
    this.registryTransition = true;
    const bind = replacements => {
      this.replacements = replacements;
      for (const item of saved) {
        if (replacements.macros.has(macroId)) super.prepareFarObject(item.object, item.record);
        else this.parents.set(item.object, {id: item.record.id, object: item.object, url: item.record.detailURL,
          active: false, records: [], status: 'idle', retryAt: 0});
        const parent = this.parents.get(item.object);
        parent.active = item.active;
        this.afterFarRebind(item.object,item.record);
      }
    };
    try {
      for (const item of saved) {this.beforeFarRebind(item.object);super.detach(item.object);}
      bind(next);
    } catch (error) {
      for (const item of saved) {this.beforeFarRebind(item.object);super.detach(item.object);}
      bind(prior); // Restore the audited previous registry; no new model owner exists.
      throw error;
    } finally {
      this.registryTransition = false;
      for (const item of saved) {
        const parent = this.parents.get(item.object);
        if (parent?.active && parent.status === 'idle') this.loadIndex(parent);
      }
      this.select(); this.notify();
    }
  }
  getState() {
    return {...super.getState(), ordinaryRegistries: this.macroRegistrations?.size || 0};
  }
  destroy() {
    this.macroRegistrations.clear();
    super.destroy();
  }
}
