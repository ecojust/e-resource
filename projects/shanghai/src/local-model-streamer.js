/** Spatially bounded, abortable streaming of georeferenced local city GLBs. */
import {estimateModelBufferResources} from './model-resources.js';

const EARTH = 6378137;
const DEG = Math.PI / 180;
const INDEX_LATITUDE = 31.2304 * DEG;
const METRES_X = EARTH * DEG * Math.cos(INDEX_LATITUDE);
const METRES_Y = EARTH * DEG;
const now = () => performance.now();
const nextFrame = callback => typeof requestAnimationFrame === 'function'
  ? requestAnimationFrame(callback) : setTimeout(callback, 0);
const cancelFrame = handle => typeof cancelAnimationFrame === 'function'
  ? cancelAnimationFrame(handle) : clearTimeout(handle);
const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

export function distanceToBounds(lng, lat, bounds) {
  const dx = (lng - clamp(lng, bounds[0], bounds[2])) * METRES_X;
  const dy = (lat - clamp(lat, bounds[1], bounds[3])) * METRES_Y;
  return Math.hypot(dx, dy);
}

/** The manifest is indexed once; view changes inspect nearby grid cells only. */
export class SpatialTileIndex {
  constructor(records = [], cellSize = 2000) {
    this.cellSize = Math.max(250, cellSize);
    this.cells = new Map();
    this.large = [];
    for (const record of records) this.insert(record);
  }
  insert(record) {
    const b = record.geometryBounds || record.bounds;
    const minX = Math.floor(b[0] * METRES_X / this.cellSize), maxX = Math.floor(b[2] * METRES_X / this.cellSize);
    const minY = Math.floor(b[1] * METRES_Y / this.cellSize), maxY = Math.floor(b[3] * METRES_Y / this.cellSize);
    if ((maxX-minX+1)*(maxY-minY+1) > 100) {this.large.push(record); return;}
    for (let x = minX; x <= maxX; x++) for (let y = minY; y <= maxY; y++) {
      const key = `${x}:${y}`;
      if (!this.cells.has(key)) this.cells.set(key, []);
      this.cells.get(key).push(record);
    }
  }
  query(lng, lat, radius) {
    const x = lng * METRES_X, y = lat * METRES_Y, found = new Set(this.large);
    for (let gx = Math.floor((x-radius)/this.cellSize); gx <= Math.floor((x+radius)/this.cellSize); gx++) {
      for (let gy = Math.floor((y-radius)/this.cellSize); gy <= Math.floor((y+radius)/this.cellSize); gy++) {
        for (const record of this.cells.get(`${gx}:${gy}`) || []) found.add(record);
      }
    }
    return [...found].filter(record => distanceToBounds(lng, lat, record.geometryBounds || record.bounds) <= radius);
  }
}

export function normaliseFeatureIds(value) {
  if (Array.isArray(value)) {
    const ids = [...new Set(value.filter(id => typeof id === 'string' || typeof id === 'number'))];
    return {building: ids, building_part: ids};
  }
  if (value?.ids && !value.building) return normaliseFeatureIds(value.ids);
  const result = {};
  for (const layer of ['building', 'building_part']) result[layer] = [...new Set((value?.[layer] || []).filter(id => id !== null && id !== undefined && id !== ''))];
  return result;
}

/** Reference-counted GERS visibility. No city-wide ID arrays enter style filters. */
export class FeatureStateSuppressor {
  constructor(map, source, {budgetMs = 4, batchSize = 600} = {}) {
    this.map = map; this.source = source; this.budgetMs = budgetMs; this.batchSize = batchSize;
    this.owners = new Map(); this.references = new Map(); this.pending = new Map();
    this.applied = new Map(); this.waiters = []; this.frame = null; this.destroyed = false;
  }
  setOwner(owner, input = null) {
    if (this.destroyed) return Promise.resolve();
    const ids = normaliseFeatureIds(input), next = new Map();
    for (const [layer, values] of Object.entries(ids)) for (const id of values) next.set(`${layer}\0${id}`, {layer, id});
    const previous = this.owners.get(owner) || new Map();
    for (const [key, item] of previous) {
      if (next.has(key)) continue;
      const reference = this.references.get(key);
      if (reference && --reference.count === 0) {
        this.references.delete(key); this.pending.set(key, {...item, hidden: false});
      }
    }
    for (const [key, item] of next) {
      if (previous.has(key)) continue;
      const reference = this.references.get(key);
      if (reference) reference.count++;
      else {this.references.set(key, {...item, count: 1}); this.pending.set(key, {...item, hidden: true});}
    }
    if (next.size) this.owners.set(owner, next); else this.owners.delete(owner);
    if (!this.pending.size) return Promise.resolve();
    this.schedule();
    return new Promise(resolve => this.waiters.push(resolve));
  }
  removeOwner(owner) {return this.setOwner(owner, null);}
  schedule() {
    if (this.frame === null && !this.destroyed) this.frame = nextFrame(() => this.flushBatch());
  }
  flushBatch() {
    this.frame = null;
    const started = now(); let count = 0;
    while (this.pending.size && count++ < this.batchSize && now()-started < this.budgetMs) {
      const [key, item] = this.pending.entries().next().value;
      this.pending.delete(key);
      try {
        if (this.map.getSource(this.source)) {
          const target = {source: this.source, sourceLayer: item.layer, id: item.id};
          if (item.hidden) {
            this.map.setFeatureState(target, {localModel: true});
            this.applied.set(key, item);
          } else if (this.applied.has(key)) {
            // MapLibre cannot remove a key on a never-created feature state.
            // A quick teleport can cancel a pending hide before its first flush.
            this.map.removeFeatureState(target, 'localModel');
            this.applied.delete(key);
          }
        }
      } catch { /* A removed/replaced source has no geometry left to suppress. */ }
    }
    if (this.pending.size) this.schedule();
    else {for (const resolve of this.waiters.splice(0)) resolve();}
  }
  getState() {return {owners: this.owners.size, hiddenFeatures: this.references.size, pendingStates: this.pending.size};}
  async clear() {
    await Promise.all([...this.owners.keys()].map(owner => this.removeOwner(owner)));
    // A caller may already have removed every owner while removals are still
    // waiting for the next animation frame. Reset must wait for those too.
    if(this.pending.size)await new Promise(resolve=>{this.waiters.push(resolve);this.schedule();});
  }
  destroy({clearMap = false} = {}) {
    this.destroyed = true;
    if (this.frame !== null) cancelFrame(this.frame);
    if (clearMap) for (const item of this.applied.values()) {
      try {this.map.removeFeatureState({source:this.source,sourceLayer:item.layer,id:item.id}, 'localModel');} catch {}
    }
    this.owners.clear(); this.references.clear(); this.pending.clear(); this.applied.clear();
    for (const resolve of this.waiters.splice(0)) resolve();
  }
}

async function decodeIds(data) {
  const bytes = new Uint8Array(data);
  if (bytes[0] === 0x1f && bytes[1] === 0x8b) {
    if (typeof DecompressionStream === 'undefined') throw new Error('浏览器不支持压缩建筑索引');
    data = await new Response(new Blob([data]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  }
  return normaliseFeatureIds(JSON.parse(new TextDecoder().decode(data)));
}

export function estimateGeometryBytes(object) {
  return estimateModelBufferResources(object).totalBytes;
}

/**
 * The renderer-specific functions are injected; this scheduler owns only nearby
 * model requests, resource lifetimes and the geographic manifest index.
 */
export class LocalModelStreamer {
  constructor({scene, loader, suppression, prepareObject, disposeObject, prepareFeatureIds = ids => ids, onChange = () => {}, onError = () => {},
    fetchFunction = (...args) => fetch(...args), maxVisible = 6, maxCache = 8, concurrency = 2,
    memoryBudget = 128 * 1024 * 1024, triangleBudget = 1200000, minZoom = 14}) {
    this.scene=scene; this.loader=loader; this.suppression=suppression; this.prepareObject=prepareObject;
    this.disposeObject=disposeObject; this.prepareFeatureIds=prepareFeatureIds;
    this.onChange=onChange; this.onError=onError; this.fetch=fetchFunction;
    this.maxVisible=clamp(maxVisible,1,8); this.maxCache=clamp(maxCache,this.maxVisible,8);
    this.concurrency=clamp(concurrency,1,2); this.memoryBudget=memoryBudget; this.triangleBudget=triangleBudget; this.minZoom=minZoom;
    this.records=new Map(); this.index=new SpatialTileIndex(); this.loaded=new Set(); this.inflight=new Map();
    this.wanted=new Set(); this.queue=[]; this.generation=0; this.manifestRequest=0; this.view=null; this.lastUpdate=0; this.destroyed=false;
    this.stats={requests:0,completed:0,cancelled:0,discarded:0,failed:0,evicted:0,candidates:0,selectionMs:0,peakConcurrent:0,peakCache:0};
  }
  async setManifest(manifest, {baseURL, replace = true} = {}) {
    const request=++this.manifestRequest;
    if (replace) await this.reset();
    if (request!==this.manifestRequest || this.destroyed) return;
    const generation=this.generation;
    const entries=Array.isArray(manifest)?manifest:manifest?.tiles || manifest?.models || [];
    const base=new URL(baseURL || './', globalThis.document?.baseURI || 'http://localhost/').href;
    for (const item of entries) {
      const id=String(item.id ?? item.tile_id ?? item.district_id ?? '');
      const bounds=item.geographic_bbox || item.bounds;
      const lng=Number(item.origin_longitude ?? item.lng), lat=Number(item.origin_latitude ?? item.lat);
      if (!id || this.records.has(id) || !Array.isArray(bounds) || bounds.length!==4 || !bounds.every(Number.isFinite)
        || bounds[0]>bounds[2] || bounds[1]>bounds[3] || !Number.isFinite(lng) || !Number.isFinite(lat)) continue;
      const file=item.url || item.file;
      if (!file) continue;
      const inlineIds=item.featureIds || item.feature_ids || null;
      this.records.set(id,{id,name:item.name || item.district_name || id,lng,lat,bounds,
        geometryBounds:item.geometry_bbox || bounds,url:new URL(file,base).href,
        detailURL:item.near_manifest_file?new URL(item.near_manifest_file,base).href:null,
        idsURL:item.feature_ids_file?new URL(item.feature_ids_file,base).href:null,
        inlineIds:inlineIds?normaliseFeatureIds(inlineIds):null,
        triangles:Number(item.triangles || 0),fileBytes:Number(item.size_bytes || 0),sha256:item.sha256,buildingCount:Number(item.building_count || item.represented_features || 0),
        status:'idle',object:null,gpuBytes:0,lastUsed:0,retryAt:0,owner:`${generation}:${id}`,visibilityVersion:0});
    }
    this.index=new SpatialTileIndex(this.records.values(), Number(manifest?.tile_size_m || 2000));
    if (this.view) this.update(this.view,true);
    this.notify();
  }
  update(view, force=false) {
    if (this.destroyed) return;
    const time=now();
    if (!force && this.view && time-this.lastUpdate<180
      && Math.abs(view.zoom-this.view.zoom)<.15
      && Math.hypot((view.lng-this.view.lng)*METRES_X,(view.lat-this.view.lat)*METRES_Y)<55
      && view.mode===this.view.mode) return;
    this.view={...view}; this.lastUpdate=time;
    const start=now();
    const radius=view.mode==='walk'?1800:clamp(1200*2**(16-view.zoom),850,3500);
    const candidates=view.zoom>=this.minZoom?this.index.query(view.lng,view.lat,radius):[];
    const bearing=(view.bearing || 0)*DEG;
    for (const record of candidates) {
      const distance=distanceToBounds(view.lng,view.lat,record.geometryBounds);
      const dx=(record.lng-view.lng)*METRES_X, north=(record.lat-view.lat)*METRES_Y;
      const facing=(dx*Math.sin(bearing)+north*Math.cos(bearing))/Math.max(1,Math.hypot(dx,north));
      record.priority=distance + Math.max(0,-facing)*distance*.25 - (record.object?.visible?90:0);
    }
    candidates.sort((a,b)=>a.priority-b.priority);
    const selected=[]; let triangles=0, estimatedBytes=0;
    for (const record of candidates) {
      if (selected.length>=this.maxVisible) break;
      const bytes=record.gpuBytes || record.fileBytes*5;
      if (selected.length && (triangles+record.triangles>this.triangleBudget || estimatedBytes+bytes>this.memoryBudget*.9)) continue;
      selected.push(record); triangles+=record.triangles; estimatedBytes+=bytes;
    }
    const previous=this.wanted; this.wanted=new Set(selected.map(r=>r.id));
    for (const id of previous) {
      if (this.wanted.has(id)) continue;
      const record=this.records.get(id);
      if (!record) continue;
      if (record.object) this.hide(record);
      if (record.status==='queued') record.status='idle';
    }
    for (const [id,request] of this.inflight) if (!this.wanted.has(id)) request.controller.abort('view-changed');
    this.queue=[];
    for (const record of selected) {
      record.lastUsed=time;
      if (record.object) this.show(record);
      else if (!this.inflight.has(record.id) && time>=record.retryAt) {
        record.status='queued'; this.queue.push(record);
      }
    }
    this.stats.candidates=candidates.length; this.stats.selectionMs=now()-start;
    this.radius=radius; this.trimCache(this.inflight.size); this.pump(); this.notify();
  }
  pump() {
    if (this.destroyed) return;
    while (this.inflight.size<this.concurrency && this.queue.length) {
      const record=this.queue.shift();
      if (!this.wanted.has(record.id) || record.object || this.inflight.has(record.id)) continue;
      this.trimCache(this.inflight.size+1);
      this.load(record);
    }
  }
  async load(record) {
    const controller=new AbortController(), generation=this.generation;
    const request={controller}; this.inflight.set(record.id,request); record.status='loading';
    this.stats.requests++; this.stats.peakConcurrent=Math.max(this.stats.peakConcurrent,this.inflight.size);
    const timeout=setTimeout(()=>controller.abort('timeout'),35000);
    let object=null;
    try {
      const modelRequest=this.fetch(record.url,{signal:controller.signal}).then(async response=>{
        if (!response.ok) throw Object.assign(new Error(`模型读取失败 (${response.status})`),{status:response.status});
        return response.arrayBuffer();
      });
      const idsRequest=record.inlineIds?Promise.resolve(record.inlineIds):record.idsURL
        ?this.fetch(record.idsURL,{signal:controller.signal}).then(async response=>{
          if (!response.ok) throw Object.assign(new Error(`建筑索引读取失败 (${response.status})`),{status:response.status});
          return response.arrayBuffer();
        })
        :Promise.reject(new Error('分块缺少建筑标识索引，继续显示在线建筑'));
      const [buffer,idsData]=await Promise.all([modelRequest,idsRequest]);
      // The network deadline ends after BOTH raw response bodies arrive.
      // Gzip/JSON work can wait behind rendering even after HTTP completed;
      // do not charge that processing to transport. View aborts remain active.
      clearTimeout(timeout);
      if (controller.signal.aborted) throw new DOMException('Aborted','AbortError');
      const ids=record.inlineIds ? idsData : await decodeIds(idsData);
      if (controller.signal.aborted) throw new DOMException('Aborted','AbortError');
      const data=await this.loader.parseAsync(buffer,new URL('.',record.url).href); object=data.scene;
      if (this.destroyed || generation!==this.generation || controller.signal.aborted || !this.wanted.has(record.id)) {
        this.disposeObject(object); object=null; this.stats.discarded++; record.status='idle'; return;
      }
      record.ids=this.prepareFeatureIds(ids);
      this.prepareObject(object,record); object.visible=false;
      record.object=object; record.gpuBytes=estimateGeometryBytes(object); record.lastUsed=now(); record.status='loaded';
      this.scene.add(object); this.loaded.add(record); this.stats.completed++;
      this.trimCache(); this.stats.peakCache=Math.max(this.stats.peakCache,this.loaded.size);
      await this.show(record); this.notify();
    } catch (error) {
      if (object && record.object!==object) this.disposeObject(object);
      const cancelled=controller.signal.aborted && controller.signal.reason!=='timeout';
      // A failed sidecar or GLB must also stop its paired network request.
      if(!controller.signal.aborted)controller.abort('request-failed');
      if (cancelled) {
        this.stats.cancelled++; record.status=record.object?'loaded':'idle';
      } else {
        this.stats.failed++; record.status=error.status===404?'missing':'error';
        record.retryAt=now()+(error.status===404?120000:20000);
        this.onError(new Error(`${record.name} 分块暂不可用，保留在线建筑：${error.message}`),record);
      }
    } finally {
      clearTimeout(timeout);
      if (this.inflight.get(record.id)===request) this.inflight.delete(record.id);
      this.pump(); this.notify();
    }
  }
  async show(record) {
    if (!record.object || record.object.visible || record.showing || !this.wanted.has(record.id)) return;
    const version=++record.visibilityVersion; record.showing=true;
    await this.suppression.setOwner(record.owner,record.ids);
    // A newer activation may already own the same IDs after a fast turn.
    // Never let a stale completion remove that newer activation's state.
    if (version!==record.visibilityVersion) return;
    record.showing=false;
    if (this.destroyed || !record.object || !this.wanted.has(record.id)) {
      await this.suppression.removeOwner(record.owner); return;
    }
    record.object.visible=true; this.notify();
  }
  hide(record) {
    record.visibilityVersion++; record.showing=false;
    if (record.object) record.object.visible=false;
    this.suppression.removeOwner(record.owner);
  }
  trimCache(reserve=0) {
    const candidates=[...this.loaded].filter(record=>!this.wanted.has(record.id)).sort((a,b)=>a.lastUsed-b.lastUsed);
    let bytes=[...this.loaded].reduce((sum,record)=>sum+record.gpuBytes,0);
    const limit=Math.max(this.maxVisible,this.maxCache-reserve);
    while (candidates.length && (this.loaded.size>limit || bytes>this.memoryBudget)) {
      const record=candidates.shift(); this.hide(record);
      bytes-=record.gpuBytes; this.disposeObject(record.object);
      record.object=null; record.ids=null; record.gpuBytes=0; record.status='idle';
      this.loaded.delete(record); this.stats.evicted++;
    }
  }
  getVisible() {return [...this.loaded].filter(record=>record.object?.visible);}
  getState() {
    return {total:this.records.size,visible:this.getVisible().length,loaded:this.loaded.size,
      loading:this.inflight.size,queued:this.queue.length,wanted:this.wanted.size,radius:this.radius || 0,
      geometryBytes:[...this.loaded].reduce((sum,r)=>sum+r.gpuBytes,0),maxVisible:this.maxVisible,maxCache:this.maxCache,
      concurrency:this.concurrency,...this.stats,...this.suppression.getState(),
      active:[...this.loaded].map(r=>({id:r.id,name:r.name,visible:Boolean(r.object?.visible),triangles:r.triangles,sizeBytes:r.fileBytes}))};
  }
  getRecords() {return [...this.records.values()].map(r=>({id:r.id,name:r.name,status:r.status,visible:Boolean(r.object?.visible)}));}
  notify() {if(!this.destroyed)this.onChange(this.getState());}
  async reset() {
    this.generation++; this.wanted.clear(); this.queue=[];
    for (const request of this.inflight.values()) request.controller.abort('manifest-replaced');
    for (const record of this.loaded) {this.hide(record); this.disposeObject(record.object); record.object=null;}
    this.loaded.clear(); this.records.clear(); this.index=new SpatialTileIndex();
    await this.suppression.clear();
  }
  destroy() {
    this.destroyed=true; this.wanted.clear(); this.queue=[];
    for (const request of this.inflight.values()) request.controller.abort('destroyed');
    for (const record of this.loaded) {this.hide(record);this.disposeObject(record.object);record.object=null;}
    this.loaded.clear(); this.records.clear(); this.suppression.destroy({clearMap:true});
  }
}
