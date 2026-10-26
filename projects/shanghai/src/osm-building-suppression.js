// MapLibre `within` supports points/lines, not polygon features. OSM fallback
// replacement therefore uses real source feature IDs and conservative geometry
// containment, independently of the GERS identifiers in the local GLB sidecars.
const EPS = 1e-10;
const emptyCoverage = () => ({cells: [], landmarks: [], reserved: []});
const cross = (a, b) => a[0] * b[1] - a[1] * b[0];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
const inBounds = (a, b) => a[0] >= b[0] - EPS && a[1] >= b[1] - EPS && a[2] <= b[2] + EPS && a[3] <= b[3] + EPS;
const overlap = (a, b) => a[0] <= b[2] + EPS && a[2] >= b[0] - EPS && a[1] <= b[3] + EPS && a[3] >= b[1] - EPS;

function onSegment(p, a, b) {
  const d = sub(b, a), v = sub(p, a), length = Math.hypot(...d);
  return Math.abs(cross(d, v)) <= EPS * Math.max(length, EPS)
    && p[0] >= Math.min(a[0], b[0]) - EPS && p[0] <= Math.max(a[0], b[0]) + EPS
    && p[1] >= Math.min(a[1], b[1]) - EPS && p[1] <= Math.max(a[1], b[1]) + EPS;
}

// -1 outside, 0 on the ring, 1 inside.
function pointInRing(p, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const a = ring[j], b = ring[i];
    if (onSegment(p, a, b)) return 0;
    if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside;
  }
  return inside ? 1 : -1;
}
function pointInPolygon(p, polygon) {
  const outer = pointInRing(p, polygon[0]);
  if (outer <= 0) return outer;
  for (const hole of polygon.slice(1)) {
    const hit = pointInRing(p, hole);
    if (hit === 1) return -1;
    if (hit === 0) return 0;
  }
  return 1;
}
function pointInShape(p, shape) {
  let boundary = false;
  for (const polygon of shape.polygons) {
    const value = pointInPolygon(p, polygon);
    if (value === 1) return 1;
    if (value === 0) boundary = true;
  }
  return boundary ? 0 : -1;
}
function prepareGeometry(geometry) {
  const polygons = geometry?.type === 'Polygon' ? [geometry.coordinates]
    : geometry?.type === 'MultiPolygon' ? geometry.coordinates : null;
  if (!polygons?.length) return null;
  const bounds = [Infinity, Infinity, -Infinity, -Infinity], edges = [];
  for (const polygon of polygons) {
    if (!polygon?.length) return null;
    for (const ring of polygon) {
      if (!Array.isArray(ring) || ring.length < 4) return null;
      for (const point of ring) {
        if (!Array.isArray(point) || !Number.isFinite(point[0]) || !Number.isFinite(point[1])) return null;
        bounds[0] = Math.min(bounds[0], point[0]); bounds[1] = Math.min(bounds[1], point[1]);
        bounds[2] = Math.max(bounds[2], point[0]); bounds[3] = Math.max(bounds[3], point[1]);
      }
      if (Math.hypot(...sub(ring[0], ring[ring.length - 1])) > EPS) return null;
      for (let i = 1; i < ring.length; i++) if (Math.hypot(...sub(ring[i], ring[i - 1])) > EPS) edges.push([ring[i - 1], ring[i]]);
    }
  }
  return edges.length ? {polygons, bounds, edges} : null;
}
function rectangle(bounds) {
  if (!Array.isArray(bounds) || bounds.length !== 4 || !bounds.every(Number.isFinite) || bounds[0] >= bounds[2] || bounds[1] >= bounds[3]) return null;
  const [w, s, e, n] = bounds;
  return prepareGeometry({type: 'Polygon', coordinates: [[[w, s], [e, s], [e, n], [w, n], [w, s]]]});
}
function prepareCoverage(coverage = {}) {
  const namedGeometry = item => {
    const prepared = prepareGeometry(item.geometry);
    return prepared ? {...prepared, id: item.id ?? null} : null;
  };
  return {
    cells: (coverage.cells || []).map(item => {
      const prepared = rectangle(item.bounds);
      return prepared ? {...prepared, id: item.id ?? null} : null;
    }).filter(Boolean),
    landmarks: (coverage.landmarks || []).map(namedGeometry).filter(Boolean),
    reserved: (coverage.reserved || []).map(namedGeometry).filter(Boolean),
  };
}

// Intersection positions along AB, including collinear contact endpoints.
function intersectionParameters(a, b, c, d) {
  const r = sub(b, a), s = sub(d, c), q = sub(c, a), determinant = cross(r, s);
  const length = Math.hypot(...r), otherLength = Math.hypot(...s);
  if (length <= EPS) return [];
  if (Math.abs(determinant) > EPS * Math.max(length, otherLength, EPS)) {
    const t = cross(q, s) / determinant, u = cross(q, r) / determinant;
    return t >= -EPS / length && t <= 1 + EPS / length && u >= -EPS / Math.max(otherLength, EPS) && u <= 1 + EPS / Math.max(otherLength, EPS)
      ? [Math.max(0, Math.min(1, t))] : [];
  }
  if (Math.abs(cross(q, r)) > EPS * length) return [];
  const length2 = length * length;
  return [c, d].map(p => ((p[0] - a[0]) * r[0] + (p[1] - a[1]) * r[1]) / length2)
    .filter(t => t >= -EPS / length && t <= 1 + EPS / length).map(t => Math.max(0, Math.min(1, t)));
}
function segmentsIntersect(a, b, c, d) {
  return intersectionParameters(a, b, c, d).length > 0 || onSegment(a, c, d) || onSegment(b, c, d);
}
function shapesIntersect(a, b) {
  if (!overlap(a.bounds, b.bounds)) return false;
  for (const polygon of a.polygons) if (pointInShape(polygon[0][0], b) >= 0) return true;
  for (const polygon of b.polygons) if (pointInShape(polygon[0][0], a) >= 0) return true;
  for (const [p, q] of a.edges) for (const [r, s] of b.edges) if (segmentsIntersect(p, q, r, s)) return true;
  return false;
}
function parameters(a, b, edges) {
  const values = [0, 1];
  for (const [c, d] of edges) values.push(...intersectionParameters(a, b, c, d));
  return [...new Set(values)].sort((x, y) => x - y);
}
function containedInUnion(feature, regions) {
  regions = regions.filter(region => overlap(feature.bounds, region.bounds));
  if (!regions.length) return false;
  const edges = regions.flatMap(region => region.edges);
  const covered = point => regions.some(region => pointInShape(point, region) >= 0);
  // Split every building edge at coverage boundaries. Vertex-only checks miss
  // an edge that crosses the gap in a concave confirmed landmark footprint.
  for (const [a, b] of feature.edges) {
    if (!covered(a) || !covered(b)) return false;
    const ts = parameters(a, b, edges);
    for (let i = 1; i < ts.length; i++) if (!covered(lerp(a, b, (ts[i - 1] + ts[i]) / 2))) return false;
  }
  // A building can enclose an uncovered hole without any edge crossing it.
  // Probe both sides of coverage boundary segments inside the building. This
  // also catches holes formed by the union of several otherwise solid cells.
  const splitEdges = [...edges, ...feature.edges];
  for (const [a, b] of edges) {
    const dx = b[0] - a[0], dy = b[1] - a[1], length = Math.hypot(dx, dy);
    const ts = parameters(a, b, splitEdges), offset = Math.max(EPS * 16, length * 1e-7);
    for (let i = 1; i < ts.length; i++) {
      if (ts[i] - ts[i - 1] <= EPS / Math.max(length, EPS)) continue;
      const middle = lerp(a, b, (ts[i - 1] + ts[i]) / 2);
      for (const sign of [-1, 1]) {
        const probe = [middle[0] - sign * dy / length * offset, middle[1] + sign * dx / length * offset];
        if (pointInShape(probe, feature) === 1 && !covered(probe)) return false;
      }
    }
  }
  return true;
}
function coveredPrepared(feature, coverage) {
  if (!feature) return false;
  // Generic GLBs intentionally omit detailed-building IDs. A failed/unloaded
  // detailed model must therefore never inherit the generic cell's coverage.
  // Once every intersected detailed owner is visible, the generic remainder
  // and detailed model jointly cover the owner cell. The OSM footprint need not
  // exactly equal the detailed footprint: tile quantization and compound OSM
  // buildings can extend into the surrounding, already loaded generic model.
  for (const region of coverage.reserved) {
    if (!shapesIntersect(feature, region)) continue;
    const knownOwner = region.id !== null && region.id !== '';
    const ready = knownOwner
      ? coverage.landmarks.some(active => active.id !== null && String(active.id) === String(region.id))
      : containedInUnion(region, coverage.landmarks);
    if (!ready) return false;
  }
  if (coverage.cells.some(cell => inBounds(feature.bounds, cell.bounds))) return true;
  return containedInUnion(feature, [...coverage.cells, ...coverage.landmarks]);
}
export function geometryFullyCovered(geometry, coverage = {}) {
  return coveredPrepared(prepareGeometry(geometry), prepareCoverage(coverage));
}

function stableValue(value) {
  if (Array.isArray(value)) return value.map(stableValue);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(key => [key, stableValue(value[key])]));
  return value;
}
function canonicalRing(ring) {
  const points = ring.slice(0, -1).map(point => JSON.stringify(point));
  let best = null;
  for (const sequence of [points, [...points].reverse()]) {
    for (let i = 0; i < sequence.length; i++) {
      const candidate = sequence.slice(i).concat(sequence.slice(0, i)).join(';');
      if (best === null || candidate < best) best = candidate;
    }
  }
  return best;
}
function componentKey(coordinates) {
  return JSON.stringify([canonicalRing(coordinates[0]), ...coordinates.slice(1).map(canonicalRing).sort()]);
}
function hashString(value) {
  let hash = 2166136261;
  for (let i = 0; i < value.length; i++) { hash ^= value.charCodeAt(i); hash = Math.imul(hash, 16777619); }
  return (hash >>> 0).toString(16);
}
function replacementPlan(features, coverage) {
  const groups = new Map(); let unknownIDs = 0, duplicateComponents = 0;
  for (const feature of features) {
    const id = feature.id;
    if ((typeof id !== 'number' && typeof id !== 'string') || (typeof id === 'number' && !Number.isSafeInteger(id)) || id === '') { unknownIDs++; continue; }
    const key = String(id), properties = feature.properties || {}, propertyKey = JSON.stringify(stableValue(properties));
    let group = groups.get(key);
    if (!group) { group = {id, key, properties, propertyKey, components: new Map(), multipart: false, invalid: false}; groups.set(key, group); }
    if (propertyKey !== group.propertyKey) group.invalid = true;
    const geometry = feature.geometry;
    const components = geometry?.type === 'MultiPolygon' ? geometry.coordinates : geometry?.type === 'Polygon' ? [geometry.coordinates] : null;
    if (!components?.length) { group.invalid = true; continue; }
    if (geometry.type === 'MultiPolygon') group.multipart = true;
    for (const coordinates of components) {
      const polygon = {type: 'Polygon', coordinates}, prepared = prepareGeometry(polygon);
      if (!prepared) { group.invalid = true; continue; }
      const componentID = componentKey(coordinates);
      if (group.components.has(componentID)) { duplicateComponents++; continue; }
      group.components.set(componentID, {key: componentID, geometry: polygon, prepared, covered: coveredPrepared(prepared, coverage)});
    }
  }
  const desired = new Map(), residualFeatures = []; let partialIDs = 0, removedComponents = 0, ambiguousFragments = 0;
  for (const [key, group] of groups) {
    if (group.invalid || !group.components.size) continue;
    const components = [...group.components.values()].sort((a, b) => a.key.localeCompare(b.key));
    const covered = components.filter(component => component.covered), uncovered = components.filter(component => !component.covered);
    if (!covered.length) continue;
    if (!uncovered.length) { desired.set(key, {...group, residual: false}); removedComponents += covered.length; continue; }
    // Polygon fragments can be a clipped part of one continuous building. Only
    // a source MultiPolygon authorizes independently replacing its components.
    if (!group.multipart) continue;
    // A source ID may aggregate thousands of otherwise independent buildings.
    // Keep intersecting/touching fragments together, but do not let an unrelated
    // unresolved fragment prevent replacing an independently covered component.
    const roots = components.map((_, i) => i);
    const root = i => { while (roots[i] !== i) { roots[i] = roots[roots[i]]; i = roots[i]; } return i; };
    let intersecting = false;
    for (let i = 0; i < components.length; i++) for (let j = 0; j < i; j++) {
      if (shapesIntersect(components[i].prepared, components[j].prepared)) {
        intersecting = true; roots[root(i)] = root(j);
      }
    }
    if (intersecting) ambiguousFragments++;
    const retainedRoots = new Set();
    components.forEach((component, i) => { if (!component.covered) retainedRoots.add(root(i)); });
    // Any uncovered member preserves its entire connected group, including
    // covered members. Every retained polygon/hole/property stays unchanged.
    const removable = [], retained = [];
    components.forEach((component, i) => (retainedRoots.has(root(i)) ? retained : removable).push(component));
    if (!removable.length) continue;
    desired.set(key, {...group, residual: true}); partialIDs++; removedComponents += removable.length;
    retained.forEach((component, index) => residualFeatures.push({
      type: 'Feature', id: `osm-residual:${encodeURIComponent(key)}:${index}:${hashString(component.key)}`,
      originalSourceId: group.id, properties: group.properties, geometry: component.geometry,
    }));
  }
  const residualData = {type: 'FeatureCollection', features: residualFeatures};
  const signature = JSON.stringify([...[...desired.keys()].sort(), residualFeatures.map(feature => [feature.id, feature.properties, feature.geometry])]);
  return {desired, residualData, signature, stats: {queriedFeatures: features.length, candidateIDs: groups.size,
    unknownIDs, partialIDs, residualComponents: residualFeatures.length, removedComponents, duplicateComponents,
    ambiguousFragments, retainedCrossingIDs: groups.size - desired.size}};
}
/** Pure, exact-component plan. Source Polygon crossing a boundary stays whole. */
export function planOSMBuildingReplacement(features, coverage = {}) {
  const plan = replacementPlan(features, prepareCoverage(coverage));
  return {hideIDs: [...plan.desired.values()].map(item => item.id), residualData: plan.residualData, ...plan.stats};
}

/** Actual OSM feature-state ownership for visible, successfully loaded models. */
export class OSMBuildingSuppressor {
  constructor({map, source, sourceLayer = 'building', getCoverage = null, residualLayer = null, onChange = () => {}}) {
    this.map = map; this.source = source; this.sourceLayer = sourceLayer;
    this.getCoverage = getCoverage; this.onChange = onChange;
    this.residualLayer = residualLayer; this.residualGeneration = 0; this.nextPlan = null;
    this.sourceEpoch = 0; this.inflightSignature = null;
    this.applying = null; this.lastSignature = ''; this.currentResidualCount = 0; this.residualReady = false;
    this.coverage = emptyCoverage(); this.active = false; this.destroyed = false;
    this.applied = new Map(); this.pendingRemovals = new Map(); this.sourceObject = null; this.timer = null;
    this.lastRefresh = 0;
    this.stats = {queriedFeatures: 0, candidateIDs: 0, coveredIDs: 0, retainedCrossingIDs: 0, unknownIDs: 0, failedWrites: 0, queryErrors: 0,
      partialIDs: 0, residualComponents: 0, removedComponents: 0, duplicateComponents: 0, ambiguousFragments: 0, residualErrors: 0};
  }
  setActive(active) {
    this.active = Boolean(active);
    if (!this.active) this.clear(); else this.schedule();
  }
  setCoverage(coverage) { this.coverage = coverage || emptyCoverage(); if (this.active) this.schedule(); }
  sourceChanged() {
    if (!this.active || this.destroyed) return;
    // A state ID also affects newly loaded vector-tile fragments. Restore it
    // immediately before those fragments can render outside an older residual
    // snapshot; only the subsequent source query can authorize hiding again.
    this.sourceEpoch++; this.lastSignature = '';
    for (const [key, item] of this.applied) this.remove(key, item);
    this.schedule();
  }
  residualInvalidated() {
    if (this.destroyed) return;
    this.residualReady = false; this.lastSignature = ''; this.sourceEpoch++;
    for (const [key, item] of this.applied) this.remove(key, item);
    this.schedule(); this.onChange(this.getState());
  }
  schedule() {
    if (this.destroyed || (!this.active && !this.pendingRemovals.size) || this.timer !== null) return;
    this.timer = setTimeout(() => { this.timer = null; this.refresh(); }, Math.max(0, 180 - (Date.now() - this.lastRefresh)));
  }
  remove(key, item) {
    try {
      if (this.map.getSource(this.source)) {
        const target = {source: this.source, sourceLayer: this.sourceLayer, id: item.id};
        if (!this.map.getFeatureState || this.map.getFeatureState(target)?.localModel === true) this.map.removeFeatureState(target, 'localModel');
      }
      this.applied.delete(key); this.pendingRemovals.delete(key);
    } catch {
      // Keep proof of the still-applied mask until restoration succeeds. A
      // later source/move event retries even after this controller is inactive.
      this.stats.failedWrites++; this.pendingRemovals.set(key, item);
    }
  }
  refresh() {
    if (this.destroyed) return this.getState();
    if (!this.active) { if (this.pendingRemovals.size) this.clear(); return this.getState(); }
    if (this.timer !== null) { clearTimeout(this.timer); this.timer = null; }
    this.lastRefresh = Date.now();
    const sourceObject = this.map.getSource(this.source);
    if (!sourceObject) { this.clear(); return this.getState(); }
    if (sourceObject !== this.sourceObject) {
      // A new source has no previous feature state. Keep no stale success cache.
      this.applied.clear(); this.pendingRemovals.clear(); this.sourceObject = sourceObject;
    }
    const coverage = prepareCoverage(this.getCoverage ? this.getCoverage() : this.coverage);
    if (!coverage.cells.length && !coverage.landmarks.length) { this.clear(); return this.getState(); }
    let features;
    try { features = this.map.querySourceFeatures(this.source, {sourceLayer: this.sourceLayer}); }
    catch { this.stats.queryErrors++; this.clear(); return this.getState(); }
    const plan = replacementPlan(features, coverage);
    plan.sourceEpoch = this.sourceEpoch;
    Object.assign(this.stats, plan.stats);
    if (!this.residualLayer) {
      // No residual renderer means no authorization to remove a partially
      // covered source ID. Whole covered features remain synchronous.
      for (const [key, group] of plan.desired) if (group.residual) plan.desired.delete(key);
      this.applyDesired(plan.desired); this.onChange(this.getState()); return this.getState();
    }
    const residualStillReady = !plan.residualData.features.length
      || (this.residualLayer.isReady ? this.residualLayer.isReady() : this.residualReady);
    if (plan.signature === this.lastSignature && !this.applying && residualStillReady) {
      this.applyDesired(plan.desired); this.onChange(this.getState()); return this.getState();
    }
    if (!plan.residualData.features.length && !this.currentResidualCount && !this.applying) {
      this.applyDesired(plan.desired); this.lastSignature = plan.signature;
      this.onChange(this.getState()); return this.getState();
    }
    this.queuePlan(plan);
    return this.applying ? this.applying.then(() => this.getState()) : this.getState();
  }
  applyDesired(desired) {
    for (const [key, item] of this.applied) if (!desired.has(key)) this.remove(key, item);
    for (const [key, item] of desired) {
      this.pendingRemovals.delete(key);
      const target = {source: this.source, sourceLayer: this.sourceLayer, id: item.id};
      // Recheck actual state, rather than reporting references as proof that a
      // prior write succeeded. Failed writes retry on the next source event.
      try {
        if (this.applied.has(key) && (!this.map.getFeatureState || this.map.getFeatureState(target)?.localModel === true)) continue;
        this.map.setFeatureState(target, {localModel: true}); this.applied.set(key, item);
      }
      catch { this.stats.failedWrites++; this.applied.delete(key); }
    }
  }
  queuePlan(plan) {
    if (this.nextPlan?.signature === plan.signature && this.nextPlan.sourceEpoch === plan.sourceEpoch) return;
    if (!this.nextPlan && this.inflightSignature === plan.signature && this.inflightSourceEpoch === plan.sourceEpoch) return;
    // Restore the entire original ID before replacing/dropping its residual
    // components. A transient duplicate is safer than a missing building.
    for (const [key, item] of this.applied) this.remove(key, item);
    if (this.pendingRemovals.size) { this.onChange(this.getState()); return; }
    this.residualGeneration++; this.nextPlan = plan;
    if (this.applying) return;
    this.applying = this.applyPlans().finally(() => { this.applying = null; this.onChange(this.getState()); });
  }
  async applyPlans() {
    while (this.nextPlan && !this.destroyed) {
      const plan = this.nextPlan, generation = this.residualGeneration; this.nextPlan = null;
      this.inflightSignature = plan.signature; this.inflightSourceEpoch = plan.sourceEpoch;
      try {
        await this.residualLayer.replace(plan.residualData);
        if (this.destroyed) return;
        if (this.residualLayer.isReady && !this.residualLayer.isReady()) throw new Error('Residual layer lost readiness before source suppression.');
        this.currentResidualCount = plan.residualData.features.length; this.residualReady = true;
        if (generation !== this.residualGeneration || plan.sourceEpoch !== this.sourceEpoch || !this.active) continue;
        this.applyDesired(plan.desired); this.lastSignature = plan.signature;
      } catch {
        if (this.destroyed) return;
        this.stats.residualErrors++; this.residualReady = false; this.lastSignature = '';
        for (const [key, item] of this.applied) this.remove(key, item);
        // Existing residuals may remain temporarily duplicated, but the
        // original source is visible. Never hide after an unconfirmed upload.
        if (!this.pendingRemovals.size) {
          try { await this.residualLayer.clear(); this.currentResidualCount = 0; } catch { this.stats.residualErrors++; }
        }
      }
      this.onChange(this.getState());
    }
    this.inflightSignature = null;
  }
  clear() {
    if (this.timer !== null) { clearTimeout(this.timer); this.timer = null; }
    for (const [key, item] of this.applied) this.remove(key, item);
    this.lastSignature = '';
    if (this.residualLayer && (this.currentResidualCount || this.applying || this.nextPlan)) {
      this.queuePlan({desired: new Map(), residualData: {type: 'FeatureCollection', features: []}, signature: 'clear', sourceEpoch:this.sourceEpoch});
    }
    this.stats.coveredIDs = 0; this.onChange(this.getState());
  }
  getState() { return {active: this.active, ...this.stats, coveredIDs: this.applied.size, pendingRemovals: this.pendingRemovals.size,
    residualReady: this.residualReady, renderedResidualComponents: this.currentResidualCount,
    residualLayer: this.residualLayer?.getState?.(), pending: this.timer !== null || Boolean(this.applying || this.nextPlan)}; }
  destroy({mapWillBeRemoved = false} = {}) {
    this.clear(); this.destroyed = true;
    // Standalone cleanup must retain the last visible residual if restoration
    // failed. The scene explicitly guarantees immediate map.remove() instead.
    if (!this.pendingRemovals.size || mapWillBeRemoved) this.residualLayer?.destroy();
  }
}
