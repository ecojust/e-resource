import {CityFeatureMask} from './city-feature-mask.js';
import {distanceToBounds} from './local-model-streamer.js';
import {countExpandedTriangles} from './model-resources.js';
import {estimateDetailResources} from './detail-model-cache.js';
import {cityModelCodecMetadata,decodeCityModelResponse} from './city-model-codec.js';

/** Bounded physical facade models. A visible far parent owns every replacement. */
export class CityDetailStreamer {
  constructor({THREE,scene,loader,prepareObject,disposeObject,onChange=()=>{},onError=()=>{},fetchFunction=(...args)=>fetch(...args),
    maxVisible=6,maxCache=8,triangleBudget=1100000,memoryBudget=64*1024*1024,radius=160,
    indexTimeoutMs=25000,modelTimeoutMs=35000,retryDelayMs=60000}) {
    Object.assign(this,{THREE,scene,loader,prepareObject,disposeObject,onChange,onError,maxVisible,maxCache,triangleBudget,memoryBudget,radius,indexTimeoutMs,modelTimeoutMs,retryDelayMs});
    this.fetch=fetchFunction;this.parents=new Map();this.records=new Set();this.wanted=new Set();this.inflight=null;this.view=null;this.destroyed=false;
    this.stats={requests:0,completed:0,failed:0,cancelled:0,evicted:0,discarded:0,metadataMismatches:0};
  }
  syncParents(records) {
    if(this.destroyed)return;
    const visible=new Map(records.filter(record=>record.object?.visible&&record.detailURL).map(record=>[record.object,record]));
    for(const parent of this.parents.values()) {
      const far=visible.get(parent.object);
      if(far&&far.detailURL!==parent.url){this.detach(parent.object);continue;}
      parent.active=Boolean(far);
      if(!parent.active) {
        if(parent.status==='loading')this.cancelIndex(parent,'parent-hidden');
        for(const record of parent.records)this.hide(record);
      }
    }
    for(const far of visible.values()) {
      let parent=this.parents.get(far.object);
      if(!parent) {
        parent={id:far.id,object:far.object,url:far.detailURL,active:true,records:[],status:'idle',retryAt:0};
        this.parents.set(far.object,parent);
      }
      parent.active=true;
      if(parent.status==='idle' && performance.now()>=parent.retryAt)this.loadIndex(parent);
    }
    this.select();
  }
  cancelIndex(parent,reason) {
    const controller=parent.controller;parent.controller=null;
    controller?.abort(reason);
    if(parent.status==='loading'){parent.status='idle';parent.retryAt=0;}
  }
  async loadIndex(parent) {
    if(this.destroyed||!parent.active||parent.status==='loading'||this.parents.get(parent.object)!==parent)return;
    parent.status='loading';const controller=parent.controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort('timeout'),this.indexTimeoutMs);
    let mask;
    try {
      const response=await this.fetch(parent.url,{signal:controller.signal});
      if(!response.ok)throw Error(`City detail index: ${response.status}`);
      const metadata=await response.json(), entries=metadata.near??metadata.tiles;
      const count=Number(metadata.feature_count??metadata.featureCount);
      if(!Array.isArray(entries)||!Number.isInteger(count)||count<1||count>16777215)throw Error('Invalid city detail index');
      const ownership=new Set(),recordIds=new Set();
      const prepared=entries.map(item=>{
        const ids=item.featureLocalIds??item.feature_local_ids;
        const bounds=item.geometry_bbox??item.geographic_bbox;
        if(!Array.isArray(ids)||!ids.length||!Array.isArray(bounds)||bounds.length!==4||!bounds.every(Number.isFinite)
          ||bounds[0]>bounds[2]||bounds[1]>bounds[3])throw Error('Invalid near building ownership');
        for(const id of ids) {
          if(!Number.isInteger(id)||id<1||id>count||ownership.has(id))throw Error('Duplicate or invalid near building ID');
          ownership.add(id);
        }
        const triangles=Number(item.expandedTriangles??item.triangles??item.expanded_triangles);
        const codec=cityModelCodecMetadata(item);
        const fileBytes=Number(item.size_bytes),geometryBytes=Number(item.geometryBytes??item.geometry_bytes??(codec.decodedBytes??fileBytes)*5);
        if(!Number.isInteger(triangles)||triangles<1||!Number.isInteger(fileBytes)||fileBytes<1||fileBytes>=100000000
          ||!Number.isFinite(geometryBytes)||geometryBytes<1)throw Error('Invalid near building resource budget');
        const file=item.file||item.url,id=String(item.id||file||'');
        if(typeof file!=='string'||!file||!id||recordIds.has(id))throw Error('Invalid or duplicate near building resource ID');
        recordIds.add(id);
        return {id:`${parent.id}/${id}`,owner:Symbol(id),parent,ids,bounds,url:new URL(file,parent.url).href,
          triangles,declaredTriangles:triangles,fileBytes,codec,geometryBytes,memoryBytes:geometryBytes,object:null,lastUsed:0,retryAt:0,status:'idle'};
      });
      if(ownership.size!==count)throw Error('Incomplete near building ownership');
      if(this.destroyed||this.parents.get(parent.object)!==parent||parent.controller!==controller||!parent.active||controller.signal.aborted)return;
      mask=new CityFeatureMask(this.THREE,count);
      if(this.maskBytes()+mask.data.byteLength>=this.memoryBudget)throw Error('City feature masks exceed the memory budget');
      mask.bindObject(parent.object);
      parent.mask=mask;parent.records=prepared;parent.status='ready';
      for(const record of prepared)this.records.add(record);
      this.select();this.notify();
    } catch(error) {
      mask?.dispose();
      if(!this.destroyed&&this.parents.get(parent.object)===parent&&parent.controller===controller) {
        parent.status='idle';
        if(!controller.signal.aborted||controller.signal.reason==='timeout') {
          parent.retryAt=performance.now()+this.retryDelayMs;
          this.onError(controller.signal.reason==='timeout'?Error('City detail index timed out'):error);
        } else parent.retryAt=0;
      }
    } finally {
      clearTimeout(timeout);
      if(parent.controller===controller){parent.controller=null;if(parent.status==='loading')parent.status='idle';}
    }
  }
  update(view) {this.view={...view};this.select();}
  select() {
    if(this.destroyed)return;
    const view=this.view, enabled=view && (view.mode==='walk'||view.zoom>=17.3), candidates=[];
    if(enabled)for(const parent of this.parents.values())if(parent.active && parent.status==='ready')for(const record of parent.records) {
      const distance=distanceToBounds(view.lng,view.lat,record.bounds);
      if(distance<=this.radius) {record.priority=distance-(record.object?.visible?12:0);candidates.push(record);}
    }
    candidates.sort((a,b)=>a.priority-b.priority||a.id.localeCompare(b.id));
    const wanted=new Set();let triangles=0,bytes=0;const availableMemory=Math.max(0,this.memoryBudget-this.maskBytes());
    for(const record of candidates) {
      if(wanted.size>=this.maxVisible)break;
      // A single indivisible large building may exceed the target. It gets the
      // whole near budget rather than being clipped at a microtile boundary.
      if(wanted.size&&(triangles+record.triangles>this.triangleBudget||bytes+record.memoryBytes>availableMemory*.85))continue;
      if(record.memoryBytes>availableMemory)continue;
      wanted.add(record);triangles+=record.triangles;bytes+=record.memoryBytes;
    }
    this.wanted=wanted;
    if(this.inflight&&!wanted.has(this.inflight.record))this.inflight.controller.abort('view-changed');
    for(const record of this.records) {
      if(!wanted.has(record))this.hide(record);
      else {record.lastUsed=performance.now();if(record.object)this.show(record);}
    }
    this.trim();this.pump();this.notify();
  }
  pump() {
    if(this.destroyed||this.inflight)return;
    const record=[...this.wanted].find(record=>!record.object&&performance.now()>=record.retryAt);
    if(record){this.trim(record.memoryBytes,1);this.load(record);}
  }
  async load(record) {
    const controller=new AbortController(),request={record,controller};this.inflight=request;
    record.status='loading';this.stats.requests++;const timeout=setTimeout(()=>controller.abort('timeout'),this.modelTimeoutMs);let object;
    try {
      const response=await this.fetch(record.url,{signal:controller.signal});
      if(!response.ok)throw Error(`City facade model: ${response.status}`);
      const buffer=await decodeCityModelResponse(response,record.codec,{signal:controller.signal});
      // Transport, decompression and integrity checks are complete. A slow
      // parser must not be discarded as a network timeout; view aborts remain.
      clearTimeout(timeout);
      if(controller.signal.aborted)throw Error('cancelled');
      object=(await this.loader.parseAsync(buffer,new URL('.',record.url).href)).scene;
      if(controller.signal.aborted&&controller.signal.reason==='timeout'&&!this.destroyed
        &&this.parents.get(record.parent.object)===record.parent)throw Error('City facade model timed out');
      if(this.destroyed||controller.signal.aborted||!this.wanted.has(record)||!record.parent.active||this.parents.get(record.parent.object)!==record.parent) {
        this.disposeObject(object);object=null;this.stats.discarded++;record.status='idle';return;
      }
      this.prepareObject(object,record.parent.object,record);
      const resources=estimateDetailResources(object),triangles=countExpandedTriangles(object);
      if(!Number.isFinite(triangles)||triangles<1)throw Error('City facade model has no valid triangles');
      record.geometryBytes=resources.geometryBytes+resources.instanceBytes+resources.skeletonBytes;
      record.memoryBytes=resources.totalBytes;record.resourceEstimate=resources;record.triangles=triangles;
      if(triangles!==record.declaredTriangles){record.metadataTriangleMismatch=true;this.stats.metadataMismatches++;}
      if(resources.unknownTextures||record.memoryBytes+this.maskBytes()>this.memoryBudget)throw Error('City facade model exceeds the memory budget or has unknown texture size');
      object.visible=false;record.object=object;this.scene.add(object);record.status='loaded';this.stats.completed++;
      // Re-select with decoded expanded triangles and owned resources before
      // any activation. Underestimated indexes cannot leave every model wanted
      // and therefore immune to the hidden-cache eviction rule.
      this.select();
    } catch(error) {
      if(object&&record.object!==object)this.disposeObject(object);
      if(this.destroyed||this.parents.get(record.parent.object)!==record.parent
        ||controller.signal.aborted&&controller.signal.reason!=='timeout'){this.stats.cancelled++;record.status='idle';}
      else {this.stats.failed++;record.status='error';record.retryAt=performance.now()+this.retryDelayMs;this.onError(error);}
    } finally {
      clearTimeout(timeout);if(this.inflight===request)this.inflight=null;
      this.pump();this.notify();
    }
  }
  show(record) {
    if(!record.object||record.object.visible||!record.parent.active||!this.wanted.has(record))return;
    // Both operations are synchronous. No frame can contain a near facade and
    // its old solid wall, nor a hidden far feature without a ready replacement.
    record.parent.mask.setOwner(record.owner,record.ids);record.object.visible=true;
  }
  hide(record) {
    if(!record.object?.visible)return;
    record.parent.mask?.removeOwner(record.owner);record.object.visible=false;
  }
  maskBytes(){return [...this.parents.values()].reduce((sum,parent)=>sum+(parent.mask?.data.byteLength||0),0);}
  trim(reserveBytes=0,reserveCount=0) {
    const loaded=[...this.records].filter(record=>record.object), hidden=loaded.filter(record=>!this.wanted.has(record)).sort((a,b)=>a.lastUsed-b.lastUsed);
    let count=loaded.length+reserveCount,bytes=loaded.reduce((sum,r)=>sum+r.memoryBytes,0)+this.maskBytes()+reserveBytes;
    while(hidden.length&&(count>this.maxCache||bytes>this.memoryBudget)) {
      const record=hidden.shift();this.hide(record);this.disposeObject(record.object);record.object=null;record.status='idle';
      count--;bytes-=record.memoryBytes;this.stats.evicted++;
    }
  }
  detach(object) {
    const parent=this.parents.get(object);if(!parent)return;
    parent.active=false;this.cancelIndex(parent,'parent-disposed');
    for(const record of parent.records) {
      if(this.inflight?.record===record)this.inflight.controller.abort('parent-disposed');
      this.hide(record);if(record.object)this.disposeObject(record.object);
      record.object=null;this.wanted.delete(record);this.records.delete(record);
    }
    parent.mask?.dispose();this.parents.delete(object);this.select();
  }
  getState() {
    const loaded=[...this.records].filter(record=>record.object),visible=loaded.filter(record=>record.object.visible);
    return {...this.stats,parents:this.parents.size,available:this.records.size,visible:visible.length,loaded:loaded.length,loading:this.inflight?1:0,
      geometryBytes:loaded.reduce((sum,r)=>sum+r.geometryBytes,0),memoryBytes:loaded.reduce((sum,r)=>sum+r.memoryBytes,0)+this.maskBytes(),maskBytes:this.maskBytes(),triangles:visible.reduce((sum,r)=>sum+r.triangles,0),
      features:visible.reduce((sum,r)=>sum+r.ids.length,0),active:visible.map(r=>({id:r.id,features:r.ids.length,triangles:r.triangles}))};
  }
  notify(){if(!this.destroyed)this.onChange(this.getState());}
  destroy(){this.destroyed=true;this.inflight?.controller.abort('destroyed');for(const object of [...this.parents.keys()])this.detach(object);}
}
