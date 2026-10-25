/** Render complete uncovered OSM components before suppressing their original ID. */
const emptyCollection = () => ({type: 'FeatureCollection', features: []});
const copy = value => typeof structuredClone === 'function'
  ? structuredClone(value) : JSON.parse(JSON.stringify(value));

export class OSMResidualLayer {
  constructor({map, sourceId = 'shanghai-osm-building-residuals',
    layerId = 'shanghai-osm-building-residuals-3d', templateLayerId, beforeId, timeoutMs = 30000, onInvalidated}) {
    if (!map || !templateLayerId) throw new TypeError('A map and extrusion template layer are required.');
    this.map = map; this.sourceId = sourceId; this.layerId = layerId;
    this.templateLayerId = templateLayerId; this.beforeId = beforeId;
    // Original geometry stays visible during this transaction. Allow several
    // rendered frames even on slow GPUs; readiness still requires source
    // content, source-loaded acknowledgment and a subsequent rendered frame.
    this.timeoutMs = Math.max(1, Number(timeoutMs) || 30000);
    this.destroyed = false; this.source = null; this.layer = null; this.ownsSource = false; this.ownsLayer = false;
    this.tail = Promise.resolve(); this.current = null; this.sequence = 0; this.queued = 0;
    this.stats = {ready: false, busy: false, featureCount: 0, replacements: 0, failures: 0, lastError: null};
    this.onInvalidated = typeof onInvalidated === 'function' ? onInvalidated : null;
    this.persistentListeners = [];
    for (const name of ['styledata', 'sourcedata', 'error']) {
      const listener = event => {
        if (this.destroyed || !this.stats.ready || this.stats.busy) return;
        if (name === 'error') {
          if (event?.sourceId !== this.sourceId) return;
          this._invalidate(event.error || new Error('Residual source failed after rendering.'));
        } else this.isReady();
      };
      this.map.on?.(name, listener); this.persistentListeners.push([name, listener]);
    }
  }

  setInvalidationHandler(handler) {
    this.onInvalidated = typeof handler === 'function' ? handler : null;
    return this;
  }

  _resourceError() {
    if (this.source && this.map.getSource(this.sourceId) !== this.source) {
      return new Error('OSM residual source was removed or replaced.');
    }
    if (this.ownsLayer && this.layer) {
      const layer = this.map.getLayer(this.layerId);
      if (layer !== this.layer) return new Error('OSM residual layer was removed or replaced.');
      if (layer.source !== this.sourceId) return new Error('OSM residual layer points to a different source.');
      const visibility = this.map.getLayoutProperty?.(this.layerId, 'visibility')
        ?? layer.serialize?.()?.layout?.visibility ?? layer.layout?.visibility;
      if (visibility === 'none') return new Error('OSM residual layer is hidden.');
    }
    return null;
  }

  _invalidate(error) {
    if (!this.stats.ready || this.destroyed) return;
    this.stats.ready = false; this.stats.lastError = String(error?.message || error);
    // Change state before the synchronous callback: restoring original feature
    // state may itself emit style events, which must not recursively invalidate.
    try { this.onInvalidated?.(this.getState()); }
    catch (failure) { this.stats.lastError += `; invalidation handler: ${failure?.message || failure}`; }
  }

  isReady() {
    if (this.destroyed || !this.stats.ready || this.stats.busy) return false;
    let error;
    try { error = this._resourceError(); } catch (failure) { error = failure; }
    if (error) this._invalidate(error);
    return this.stats.ready;
  }

  _snapshot(data) {
    if (data?.type !== 'FeatureCollection' || !Array.isArray(data.features)) {
      throw new TypeError('Residual data must be a FeatureCollection.');
    }
    const snapshot = copy(data), reserved = new Set(), used = new Set();
    const validId = id => typeof id === 'string' || (typeof id === 'number' && Number.isFinite(id));
    for (const feature of snapshot.features) {
      if (feature?.type !== 'Feature' || !['Polygon', 'MultiPolygon'].includes(feature.geometry?.type)) {
        throw new TypeError('Residual features must have Polygon or MultiPolygon geometry.');
      }
      if (validId(feature.id)) reserved.add(String(feature.id));
    }
    for (let index = 0; index < snapshot.features.length; index++) {
      const feature = snapshot.features[index];
      if (!validId(feature.id) || used.has(String(feature.id))) {
        let suffix = 0, id = `${this.sourceId}:component:${index}`;
        while (reserved.has(id) || used.has(id)) id = `${this.sourceId}:component:${index}:${++suffix}`;
        feature.id = id;
      }
      used.add(String(feature.id));
    }
    return snapshot;
  }

  replace(data) {
    if (this.destroyed) return Promise.reject(new Error('OSM residual layer is destroyed.'));
    let snapshot;
    try { snapshot = this._snapshot(data); } catch (error) { return Promise.reject(error); }
    this.queued++;
    const operation = this.tail.then(() => {
      this.queued--;
      if (this.destroyed) throw new Error('OSM residual layer is destroyed.');
      return this._replace(snapshot);
    });
    this.tail = operation.catch(() => {});
    return operation;
  }

  clear() { return this.replace(emptyCollection()); }

  _context() {
    const context = {id: ++this.sequence, deadline: Date.now() + this.timeoutMs,
      source: this.source, error: null, render: 0, lastEvent: null,
      awaitingContent: false, contentSeen: false, listeners: [], checks: new Set()};
    context.notify = kind => {
      context.lastEvent = kind;
      if (kind === 'render') context.render++;
      for (const check of [...context.checks]) check();
    };
    const listen = (target, name, fn) => {
      if (typeof target?.on !== 'function') return;
      target.on(name, fn); context.listeners.push(() => target.off?.(name, fn));
    };
    context.listen = listen;
    context.sourceEvent = (event, direct = false) => {
      if (!direct && event?.sourceId !== this.sourceId) return;
      if (event?.sourceDataType === 'content' && context.awaitingContent) context.contentSeen = true;
      context.notify('data');
    };
    context.sourceError = (event, direct = false) => {
      if (!direct && event?.sourceId !== this.sourceId) return;
      context.error = event?.error instanceof Error ? event.error
        : new Error(`Residual source failed: ${event?.error?.message || event?.message || 'source error'}`);
      context.notify('error');
    };
    listen(this.map, 'render', () => context.notify('render'));
    listen(this.map, 'sourcedata', event => context.sourceEvent(event));
    listen(this.map, 'styledata', () => context.notify('style'));
    listen(this.map, 'error', event => context.sourceError(event));
    listen(this.map, 'sourcedataabort', event => context.sourceError(event));
    return context;
  }

  _guard(context) {
    if (this.destroyed) throw new Error('OSM residual layer is destroyed.');
    if (context.error) throw context.error;
    if (context.source && this.map.getSource(this.sourceId) !== context.source) {
      throw new Error('OSM residual source was removed or replaced during an update.');
    }
    if (this.ownsLayer && this.layer && this.map.getLayer(this.layerId) !== this.layer) {
      throw new Error('OSM residual layer was removed or replaced during an update.');
    }
    const resourceError = this._resourceError();
    if (resourceError) throw resourceError;
    if (Date.now() >= context.deadline) throw new Error('OSM residual render readiness timed out.');
  }

  _wait(context, predicate) {
    return new Promise((resolve, reject) => {
      let timer, settled = false;
      const finish = error => {
        if (settled) return;
        settled = true; clearTimeout(timer); context.checks.delete(check);
        error ? reject(error) : resolve();
      };
      const check = () => {
        try { this._guard(context); if (predicate()) finish(); }
        catch (error) { finish(error); }
      };
      context.checks.add(check);
      timer = setTimeout(() => finish(new Error('OSM residual render readiness timed out.')),
        Math.max(1, context.deadline - Date.now()));
      check();
      if (!settled) this.map.triggerRepaint?.();
    });
  }

  _renderAfterReady(context, ready) {
    let readyAt = null;
    return this._wait(context, () => {
      if (!ready()) { readyAt = null; return false; }
      if (readyAt === null) {
        readyAt = context.render;
        this.map.triggerRepaint?.();
        return false;
      }
      return context.lastEvent === 'render' && context.render > readyAt;
    });
  }

  _loaded(context) {
    this._guard(context);
    return (typeof context.source?.loaded !== 'function' || context.source.loaded())
      && this.map.isSourceLoaded(this.sourceId) === true;
  }

  _ensureLayer(context) {
    let source = this.map.getSource(this.sourceId);
    if (source && source !== this.source) throw new Error('Residual source ID is already owned by another source.');
    if (!source) {
      this.map.addSource(this.sourceId, {type: 'geojson', data: emptyCollection(), tolerance: 0});
      this.ownsSource = true; source = this.map.getSource(this.sourceId);
      if (!source) throw new Error('Residual GeoJSON source was not created.');
      this.source = source;
    }
    context.source = source;
    context.listen(source, 'data', event => context.sourceEvent(event, true));
    context.listen(source, 'error', event => context.sourceError(event, true));
    context.listen(source, 'dataabort', event => context.sourceError(event, true));
    const existingLayer = this.map.getLayer(this.layerId);
    if (existingLayer && !this.ownsLayer) throw new Error('Residual layer ID is already owned by another layer.');
    if (!existingLayer) {
      const original = this.map.getLayer(this.templateLayerId);
      const template = original?.serialize?.()
        || this.map.getStyle?.()?.layers?.find(layer => layer.id === this.templateLayerId) || original;
      if (!template || template.type !== 'fill-extrusion') throw new Error('Residual extrusion template layer is unavailable.');
      const layer = {id: this.layerId, type: 'fill-extrusion', source: this.sourceId,
        paint: copy(template.paint || {}), layout: {...copy(template.layout || {}), visibility: 'visible'}};
      for (const key of ['minzoom', 'maxzoom']) if (template[key] !== undefined) layer[key] = template[key];
      this.map.addLayer(layer, this.beforeId); this.ownsLayer = true;
      this.layer = this.map.getLayer(this.layerId);
    }
  }

  async _replace(data) {
    const context = this._context(); this.current = context;
    this.stats.busy = true; this.stats.ready = false; this.stats.lastError = null;
    try {
      // The caller restored original feature-state immediately before enqueueing.
      // Let that restoration render before touching the old residual geometry.
      await this._renderAfterReady(context, () => true);
      this._guard(context);
      if (!this.source && data.features.length === 0 && !this.map.getSource(this.sourceId)) {
        this.stats.featureCount = 0; this.stats.ready = true; this.stats.busy = false; this.stats.replacements++;
        return this.getState();
      }
      this._ensureLayer(context);
      // setData(..., true) can resolve immediately if the initial empty source
      // is still being indexed. Wait for it before issuing this transaction.
      await this._wait(context, () => this._loaded(context));
      context.awaitingContent = true; context.contentSeen = false;
      const completion = context.source.setData(data, true);
      if (completion && typeof completion.then === 'function') {
        Promise.resolve(completion).catch(error => {
          context.error = error instanceof Error ? error : new Error(String(error));
          context.notify('error');
        });
      }
      // The worker promise does not guarantee tile upload, and source errors can
      // be emitted instead of rejecting it. Observe scoped content and render.
      await this._renderAfterReady(context, () => context.contentSeen && this._loaded(context));
      this.stats.featureCount = data.features.length; this.stats.ready = true; this.stats.busy = false; this.stats.replacements++;
      return this.getState();
    } catch (error) {
      this.stats.failures++; this.stats.lastError = String(error?.message || error);
      throw error;
    } finally {
      context.awaitingContent = false;
      for (const remove of context.listeners.splice(0)) remove();
      if (this.current === context) this.current = null;
      this.stats.busy = false;
    }
  }

  getState() {
    return {sourceId: this.sourceId, layerId: this.layerId, destroyed: this.destroyed,
      queued: this.queued, generation: this.sequence, ...this.stats};
  }

  destroy() {
    if (this.destroyed) return;
    this.destroyed = true; this.stats.ready = false;
    for (const [name, listener] of this.persistentListeners.splice(0)) this.map.off?.(name, listener);
    this.current?.notify('destroy');
    // Never remove an unrelated source that replaced ours under the same ID.
    if (this.ownsLayer && this.map.getLayer(this.layerId) === this.layer) {
      try { this.map.removeLayer(this.layerId); } catch {}
    }
    if (this.ownsSource && this.map.getSource(this.sourceId) === this.source) {
      try { this.map.removeSource(this.sourceId); } catch {}
    }
    this.ownsLayer = false; this.ownsSource = false; this.source = null; this.layer = null;
  }
}
