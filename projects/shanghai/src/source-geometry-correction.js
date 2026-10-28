import {getVerifiedOrdinaryAsset} from './ordinary-asset-verification.js';

const SHA = /^[a-f0-9]{64}$/;
const schema = 'source-geometry-correction-v1';
const finitePoint = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite)
  && Math.abs(p[0]) <= 180 && Math.abs(p[1]) <= 90;
const nativeID = id => (typeof id === 'string' && id.length > 0)
  || (typeof id === 'number' && Number.isSafeInteger(id));
const samePoint = (a, b) => finitePoint(a) && finitePoint(b) && a.every((v, i) => Math.abs(v - b[i]) <= 1e-10);
const components = g => g?.type === 'Polygon' ? [g.coordinates] : g?.type === 'MultiPolygon' ? g.coordinates : null;

function ringKey(ring) {
  if (!Array.isArray(ring) || ring.length < 4 || ring.length > 4096 || !ring.every(finitePoint)) return null;
  const points = ring.map(p => p.map(v => Math.round(v * 1e8)));
  if (points[0][0] !== points.at(-1)[0] || points[0][1] !== points.at(-1)[1]) return null;
  points.pop();
  if (new Set(points.map(p => p.join(','))).size !== points.length) return null;
  let twiceArea = 0;
  for (let i = 0; i < points.length; i++) {
    const a = points[i], b = points[(i + 1) % points.length];
    // Translate before cross products to avoid cancellation at WGS84 magnitudes.
    twiceArea += (a[0] - points[0][0]) * (b[1] - points[0][1]) - (b[0] - points[0][0]) * (a[1] - points[0][1]);
  }
  if (!twiceArea) return null;
  let best = null;
  for (const order of [points, [...points].reverse()]) for (let i = 0; i < order.length; i++) {
    const value = order.slice(i).concat(order.slice(0, i)).map(p => p.join(',')).join(';');
    if (best === null || value < best) best = value;
  }
  return best;
}

/** Ring start/winding and hole order do not matter; topology/vertex count do. */
export function canonicalComponentKey(coordinates) {
  if (!Array.isArray(coordinates) || !coordinates.length || coordinates.length > 32) return null;
  const rings = coordinates.map(ringKey);
  return rings.every(k => k !== null) ? JSON.stringify([rings[0], ...rings.slice(1).sort()]) : null;
}

function validMatch(m) {
  return m && typeof m.source === 'string' && m.source.length > 0 && m.source_layer === 'building'
    && nativeID(m.native_id) && (m.property_id === undefined || typeof m.property_id === 'string')
    && m.component?.type === 'Polygon' && canonicalComponentKey(m.component.coordinates) !== null;
}

export function correctionIdentityMatches(feature, context, match) {
  return match && context?.source === match.source && context.sourceLayer === match.source_layer
    && (feature.source === undefined || feature.source === match.source)
    && (feature.sourceLayer === undefined || feature.sourceLayer === match.source_layer)
    && feature.id === match.native_id
    && (match.property_id === undefined || feature.properties?.id === match.property_id) && validMatch(match);
}

export function componentMatches(feature, context, match) {
  return correctionIdentityMatches(feature, context, match) && feature.geometry?.type === 'Polygon'
    && canonicalComponentKey(feature.geometry.coordinates) === canonicalComponentKey(match.component.coordinates);
}

function commonConfiguration(boundary, id) {
  const c = boundary?.source_geometry_correction;
  if (!c || c.schema !== schema || c.model_id !== id || !finitePoint(c.anchor)
    || !Array.isArray(c.matches) || !c.matches.length || c.matches.length > 8 || !c.matches.every(validMatch)
    || typeof c.provenance?.source_record !== 'string' || !c.provenance.source_record
    || !SHA.test(c.provenance.evidence_sha256)) return null;
  return c;
}

function validCollisionGeometry(geometry, anchor) {
  const polygons = components(geometry);
  if (!polygons?.length || polygons.length > 32) return false;
  // This contract is a bounded replacement obstacle, not a district-sized
  // exception. The registry still requires independent geometry acceptance.
  const cos = Math.cos(anchor[1] * Math.PI / 180);
  return polygons.every(p => canonicalComponentKey(p) !== null && p.every(r => r.every(v =>
    Math.hypot((v[0] - anchor[0]) * 111320 * cos, (v[1] - anchor[1]) * 111320) <= 120)));
}

function containsPoint(polygon, point) {
  const ringContains = ring => {
    let inside=false;
    for(let i=0,j=ring.length-1;i<ring.length;j=i++){
      const a=ring[j],b=ring[i];
      if((a[1]>point[1])!==(b[1]>point[1])
        && point[0]<(b[0]-a[0])*(point[1]-a[1])/(b[1]-a[1])+a[0])inside=!inside;
    }
    return inside;
  };
  return ringContains(polygon[0]) && !polygon.slice(1).some(ringContains);
}

function pendingVariant(record,config,getDesiredVariant) {
  if(config.enabled!==true || !record || record.kind!=='building' || !record.detailWanted || record.catalogDisposed
    || !samePoint(config.anchor,record.anchor||[record.lng,record.lat])
    || !validCollisionGeometry(config.collision_geometry,config.anchor))return null;
  const requested=getDesiredVariant(record),variant=requested==='full'?'web':requested==='distant'?'lod':null;
  const asset=record.assets?.[variant],binding=config.variants?.[variant];
  if(!variant || !SHA.test(binding?.asset_sha256) || binding.asset_sha256!==asset?.sha256
    || typeof asset.file!=='string' || !asset.file || !Number.isInteger(asset.bytes) || asset.bytes<=0 || asset.bytes>=100000000
    || record.failedVariants?.has(requested) || record.status==='error'
    || record.catalogController?.signal.aborted)return null;
  return record.loadingModel || record.status==='loading' || record.status==='idle'
    || (record.status==='loaded' && record.activeVariant!==requested) ? variant : null;
}

function inScene(object, scene) {
  if (!scene || !object) return false;
  for (let node=object; node; node=node.parent) {
    if(node.visible===false)return false;
    if(node===scene)return true;
  }
  return false;
}

function verifiedVariant(record, config, scene) {
  if (!record || record.kind !== 'building' || !samePoint(config.anchor, record.anchor || [record.lng,record.lat])) return null;
  const variant = record.activeVariant === 'full' ? 'web' : record.activeVariant === 'distant' ? 'lod' : null;
  const receipt = getVerifiedOrdinaryAsset(record.object), contract = config.variants?.[variant];
  if (config.enabled !== true || !variant || !SHA.test(contract?.asset_sha256)
    || !validCollisionGeometry(config.collision_geometry, config.anchor)
    || record.status !== 'loaded' || !record.object?.visible || !inScene(record.object,scene) || record.catalogDisposed
    || !receipt || receipt.modelId !== record.id || receipt.variant !== variant
    || receipt.sha256 !== contract.asset_sha256 || receipt.sha256 !== record.assets?.[variant]?.sha256
    || receipt.file !== record.assets?.[variant]?.file || receipt.bytes !== record.assets?.[variant]?.bytes) return null;
  return {variant, receipt};
}

/** Reads current Maps on every sync, including dynamic macro removal/re-add. */
export class SourceGeometryCorrectionState {
  constructor({getRecords, getBoundaries, getScene = () => null, getMode = () => '', onChange = () => {}}) {
    Object.assign(this, {getRecords, getBoundaries, getScene, getMode, onChange});
    this.plans = new Map(); this.configured = new Set(); this.signature = JSON.stringify(['',[],[]]); this.revision = 0;
    this.hits = new Map(); this.uniqueHits = new Map(); this.collisionPass = 0;
  }
  sync() {
    const records = this.getRecords(), boundaries = this.getBoundaries(), plans = new Map(), configured = new Set();
    for (const [id, boundary] of boundaries) {
      if (!Object.hasOwn(boundary, 'source_geometry_correction')) continue;
      configured.add(id);
      const record = records.get(id), config = commonConfiguration(boundary, id);
      if (config) plans.set(id, {id, config, verified: verifiedVariant(record, config, this.getScene())});
    }
    const signature = JSON.stringify([configured.size ? this.getMode() : '', [...configured].sort(), [...plans].map(([id, p]) =>
      [id, p.config, p.verified ? [p.verified.variant, p.verified.receipt.sha256, p.verified.receipt.serial] : null])]);
    this.configured = configured; this.plans = plans;
    if (signature === this.signature) return false;
    this.signature = signature; this.revision++; this.hits.clear(); this.uniqueHits.clear(); this.onChange(this.getState(false)); return true;
  }
  isConfigured(id) { return Object.hasOwn(this.getBoundaries().get(id) || {}, 'source_geometry_correction'); }
  isActive(id) { this.sync(); return Boolean(this.plans.get(id)?.verified); }
  getOSMCorrections(source, sourceLayer) {
    this.sync();
    return [...this.plans.values()].flatMap(p => p.config.matches
      .filter(m => m.source === source && m.source_layer === sourceLayer)
      .map(match => ({match, active: Boolean(p.verified)})));
  }
  beginCollisionPass() { this.hits.clear(); this.uniqueHits.clear(); this.collisionPass++; }
  /** Navigation may wait, never bypass collision, for a real pending correction.
   * Query source data lazily only after a valid pending asset/point candidate.
   */
  pendingAt({lng,lat}, {source,sourceLayer,getFeatures,getDesiredVariant=record=>record.activeVariant||'full'}) {
    this.sync();
    const point=[lng,lat];if(!finitePoint(point) || sourceLayer!=='building')return false;
    const records=this.getRecords();let features=null;
    for(const plan of this.plans.values()){
      if(plan.verified || !pendingVariant(records.get(plan.id),plan.config,getDesiredVariant))continue;
      for(const match of plan.config.matches){
        if(match.source!==source || match.source_layer!==sourceLayer || !containsPoint(match.component.coordinates,point))continue;
        if(features===null){try{features=getFeatures();}catch{return false;}}
        if(!Array.isArray(features))return false;
        if(features.some(feature=>components(feature.geometry)?.some(coordinates=>
          componentMatches({...feature,geometry:{type:'Polygon',coordinates}},{source,sourceLayer},match))))return true;
      }
    }
    return false;
  }
  filterFeature(feature, {source, sourceLayer, kind, snapshot = false}) {
    // A synchronous map cache rebuild already took one live-state snapshot.
    // Public standalone calls still recheck visibility, SHA and current Maps.
    if(!snapshot)this.sync();
    const original = feature.geometry;
    if (kind !== 'building' || sourceLayer !== 'building') return original;
    const polygonParts = components(original);
    if (!polygonParts) return original;
    const active = [...this.plans.values()].filter(p => p.verified);
    let removed = 0;
    const retained = polygonParts.filter(coordinates => {
      const component = {...feature, geometry: {type: 'Polygon', coordinates}};
      const hit = active.find(p => p.config.matches.some(m => componentMatches(component, {source, sourceLayer}, m)));
      if (!hit) return true;
      removed++;
      const key = `${hit.id}:${source}:${sourceLayer}:${typeof feature.id}:${feature.id}`;
      this.hits.set(key, (this.hits.get(key) || 0) + 1);
      if(!this.uniqueHits.has(key))this.uniqueHits.set(key,new Set());
      this.uniqueHits.get(key).add(canonicalComponentKey(coordinates)); return false;
    });
    if (!removed) return original;
    return retained.length ? {type: original.type, coordinates: original.type === 'Polygon' ? retained[0] : retained} : null;
  }
  getCollisionGeometries() {
    this.sync();
    return [...this.plans.values()].filter(p => p.verified).map(p => ({id: p.id, geometry: p.config.collision_geometry}));
  }
  getState(sync = true) {
    if (sync) this.sync();
    const records=this.getRecords();
    return {revision: this.revision, mode: this.getMode(), configured: [...this.configured],
      active: [...this.plans.values()].filter(p => p.verified).map(p => ({id: p.id, variant: p.verified.variant,
        assetSha256: p.verified.receipt.sha256})),
      bindings:[...this.configured].map(id=>{
        const record=records.get(id),plan=this.plans.get(id),receipt=getVerifiedOrdinaryAsset(record?.object);
        const variant=record?.activeVariant==='full'?'web':record?.activeVariant==='distant'?'lod':null;
        const configurationValid=Boolean(plan && validCollisionGeometry(plan.config.collision_geometry,plan.config.anchor)
          && ['web','lod'].some(key=>SHA.test(plan.config.variants?.[key]?.asset_sha256)));
        return {id,configurationValid,enabled:plan?.config.enabled===true,active:Boolean(plan?.verified),
          recordStatus:record?.status||null,objectVisible:Boolean(record?.object?.visible),
          inCurrentScene:inScene(record?.object,this.getScene()),activeVariant:record?.activeVariant||null,
          verifiedAsset:receipt||null,expectedAssetSha256:plan?.config.variants?.[variant]?.asset_sha256||null};
      }), collisionPass:this.collisionPass,matchedComponentCalls:Object.fromEntries(this.hits),
      uniqueMatchedComponents:Object.fromEntries([...this.uniqueHits].map(([key,values])=>[key,values.size]))};
  }
}
