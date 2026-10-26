import {CityFeatureMask} from './city-feature-mask.js';
import {distanceToBounds} from './local-model-streamer.js';
import {countExpandedTriangles} from './model-resources.js';
import {estimateDetailResources} from './detail-model-cache.js';
import {cityModelCodecMetadata,decodeCityModelResponse} from './city-model-codec.js';

const SHA256=/^[a-f0-9]{64}$/;
const sameIDs=(a,b)=>a.length===b.length&&a.every((id,index)=>id===b[index]);
function replacementRegistry(manifest,baseURL) {
  if(manifest?.schema!=='city-precise-overrides-v1'||manifest.complete!==true||!Array.isArray(manifest.macros))throw Error('Invalid precise building registry');
  const macros=new Map(),landmarks=new Set();
  for(const source of manifest.macros) {
    if(typeof source.id!=='string'||!source.id||macros.has(source.id)||!Number.isInteger(source.feature_count)||source.feature_count<1
      ||source.feature_count>16777215||!SHA256.test(source.baseline_configuration_sha256)||!SHA256.test(source.baseline_far_sha256)
      ||!Array.isArray(source.near)||!source.near.length)throw Error('Invalid precise building macro');
    const near=new Map(),claimed=new Set(),owners=new Map();
    for(const item of source.near) {
      const ids=item.featureLocalIds;
      if(typeof item.id!=='string'||!item.id||near.has(item.id)||typeof item.baseline_file!=='string'||!item.baseline_file
        ||!SHA256.test(item.baseline_sha256)||!SHA256.test(item.baseline_decoded_sha256)||!Array.isArray(ids)||!ids.length
        ||!Array.isArray(item.groups)||!item.groups.length)throw Error('Invalid precise near replacement');
      for(const id of ids) {
        if(!Number.isInteger(id)||id<1||id>source.feature_count||claimed.has(id))throw Error('Duplicate precise near ownership');
        claimed.add(id);
      }
      const model=item.model,codec=cityModelCodecMetadata(model||{});
      if(!model||typeof model.file!=='string'||!model.file||!Number.isInteger(model.expandedTriangles)||model.expandedTriangles<1
        ||!Number.isFinite(model.geometryBytes)||model.geometryBytes<1||!SHA256.test(model.sha256)
        ||!Number.isInteger(model.size_bytes)||model.size_bytes<1||model.size_bytes>=100000000)throw Error('Invalid precise near model');
      const names=new Set();
      for(const group of item.groups) {
        if(typeof group.name!=='string'||!group.name||names.has(group.name)||typeof group.landmark_id!=='string'||!group.landmark_id
          ||!Array.isArray(group.local_ids)||!group.local_ids.length||new Set(group.local_ids).size!==group.local_ids.length
          ||!Array.isArray(group.feature_keys)||group.feature_keys.length!==group.local_ids.length
          ||group.feature_keys.some(key=>typeof key!=='string'||!/^building(?:_part)?:[a-f0-9-]{36}$/.test(key))
          ||!Number.isInteger(group.expandedTriangles)||group.expandedTriangles<1)throw Error('Invalid precise node group');
        names.add(group.name);landmarks.add(group.landmark_id);
        for(const id of group.local_ids) {
          if(!ids.includes(id)||owners.has(id))throw Error('Precise feature has multiple landmark owners');
          owners.set(id,group.landmark_id);
        }
      }
      near.set(item.id,{...item,codec,url:new URL(model.file,baseURL).href});
    }
    macros.set(source.id,{...source,near,owners});
  }
  return {macros,landmarks};
}

/** Bounded physical facade models. A visible far parent owns every replacement. */
export class CityDetailStreamer {
  constructor({THREE,scene,loader,prepareObject,disposeObject,onChange=()=>{},onError=()=>{},fetchFunction=(...args)=>fetch(...args),
    maxVisible=6,maxCache=8,triangleBudget=1100000,memoryBudget=64*1024*1024,radius=160,
    indexTimeoutMs=25000,modelTimeoutMs=35000,retryDelayMs=60000}) {
    Object.assign(this,{THREE,scene,loader,prepareObject,disposeObject,onChange,onError,maxVisible,maxCache,triangleBudget,memoryBudget,radius,indexTimeoutMs,modelTimeoutMs,retryDelayMs});
    this.fetch=fetchFunction;this.parents=new Map();this.records=new Set();this.wanted=new Set();this.inflight=null;this.view=null;this.destroyed=false;
    this.replacements={macros:new Map(),landmarks:new Set()};this.visibleLandmarks=new Set();this.replacementRegistryInstalled=false;
    this.stats={requests:0,completed:0,failed:0,cancelled:0,evicted:0,discarded:0,metadataMismatches:0};
  }
  /** Register audited variants before loading. baseURL is the project root URL. */
  setReplacementOverrides(manifest,baseURL) {
    if(this.destroyed||this.parents.size||this.replacementRegistryInstalled)throw Error('Precise registry must be installed before city loading');
    const prepared=replacementRegistry(manifest,baseURL);
    this.replacements=prepared;this.replacementRegistryInstalled=true;
  }
  /** Called before the far object becomes visible, including late far loads. */
  prepareFarObject(object,record) {
    const replacement=this.replacements.macros.get(record.id);
    if(!replacement)return;
    if(this.destroyed||this.parents.has(object)||record.sha256!==replacement.baseline_far_sha256
      ||record.buildingCount!==replacement.feature_count||!record.detailURL)throw Error('Precise replacement far baseline differs');
    const mask=new CityFeatureMask(this.THREE,replacement.feature_count);
    try {
      if(this.maskBytes()+mask.data.byteLength>=this.memoryBudget)throw Error('City feature masks exceed the memory budget');
      mask.bindObject(object);
      const parent={id:record.id,object,url:record.detailURL,active:false,records:[],status:'idle',retryAt:0,mask,replacement,preciseOwners:new Map()};
      this.parents.set(object,parent);this.applyVisibleLandmarks(parent);
    } catch(error) {mask.dispose();this.parents.delete(object);throw error;}
  }
  /** Exact loaded-and-visible landmark IDs only, independent of near owners. */
  setVisibleLandmarks(ids=[]) {
    if(this.destroyed)return;
    const next=new Set([...ids].filter(id=>this.replacements.landmarks.has(id)));
    if(next.size===this.visibleLandmarks.size&&[...next].every(id=>this.visibleLandmarks.has(id)))return;
    this.visibleLandmarks=next;
    for(const parent of this.parents.values())this.applyVisibleLandmarks(parent);
    this.notify();
  }
  applyVisibleLandmarks(parent) {
    if(!parent.replacement||!parent.mask)return;
    const wanted=new Map();
    for(const [id,landmark] of parent.replacement.owners)if(this.visibleLandmarks.has(landmark)) {
      if(!wanted.has(landmark))wanted.set(landmark,[]);wanted.get(landmark).push(id);
    }
    parent.preciseOwners ||= new Map();
    for(const [landmark,owner] of parent.preciseOwners)if(!wanted.has(landmark)){parent.mask.removeOwner(owner);parent.preciseOwners.delete(landmark);}
    for(const [landmark,ids] of wanted) {
      if(!parent.preciseOwners.has(landmark))parent.preciseOwners.set(landmark,Symbol(`landmark:${landmark}`));
      parent.mask.setOwner(parent.preciseOwners.get(landmark),ids);
    }
    for(const record of parent.records)for(const {object,landmark} of record.replacementGroups||[])object.visible=!this.visibleLandmarks.has(landmark);
  }
  bindReplacementGroups(object,record) {
    if(!record.replacement)return;
    const found=new Map(),expected=new Map(record.replacement.groups.map(group=>[group.name,group]));
    object.traverse(node=>{
      const tag=node.userData?.cityReplacement;
      if(!tag)return;
      const group=expected.get(node.name);
      if(!group||found.has(node.name)||tag.macro_id!==record.parent.id||tag.landmark_id!==group.landmark_id
        ||!Array.isArray(tag.local_ids)||!sameIDs(tag.local_ids,group.local_ids)
        ||!Array.isArray(tag.feature_keys)||!sameIDs(tag.feature_keys,group.feature_keys))throw Error('Precise near owner tag differs');
      if(countExpandedTriangles(node)!==group.expandedTriangles)throw Error('Precise near owner geometry is incomplete');
      for(let parent=node.parent;parent&&parent!==object;parent=parent.parent)if(parent.userData?.cityReplacement)throw Error('Nested precise near owners');
      found.set(node.name,{object:node,landmark:group.landmark_id});
    });
    if(found.size!==expected.size)throw Error('Precise near model is missing a complete owner group');
    if(countExpandedTriangles(object)!==record.declaredTriangles)throw Error('Precise near model triangle count differs');
    record.replacementGroups=[...found.values()];
    for(const {object:node,landmark} of record.replacementGroups)node.visible=!this.visibleLandmarks.has(landmark);
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
        if(this.replacements.macros.has(far.id))throw Error('Precise far model was not prepared before visibility');
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
      const replacement=parent.replacement,usedOverrides=new Set();
      if(replacement&&(count!==replacement.feature_count||metadata.configuration_sha256!==replacement.baseline_configuration_sha256
        ||metadata.far?.sha256!==replacement.baseline_far_sha256))throw Error('Precise near baseline index differs');
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
        const override=replacement?.near.get(id);
        if(override) {
          if(file!==override.baseline_file||item.sha256!==override.baseline_sha256||item.decoded_sha256!==override.baseline_decoded_sha256
            ||!sameIDs(ids,override.featureLocalIds)||triangles!==override.model.expandedTriangles)throw Error('Precise near source ownership or checksum differs');
          usedOverrides.add(id);
        }
        return {id:`${parent.id}/${id}`,owner:Symbol(id),parent,ids,bounds,url:override?.url||new URL(file,parent.url).href,
          triangles,declaredTriangles:triangles,fileBytes:override?.model.size_bytes??fileBytes,codec:override?.codec??codec,
          geometryBytes:override?.model.geometryBytes??geometryBytes,memoryBytes:override?.model.geometryBytes??geometryBytes,
          replacement:override,object:null,lastUsed:0,retryAt:0,status:'idle'};
      });
      if(ownership.size!==count)throw Error('Incomplete near building ownership');
      if(replacement&&usedOverrides.size!==replacement.near.size)throw Error('Precise near source tile is missing');
      if(this.destroyed||this.parents.get(parent.object)!==parent||parent.controller!==controller||!parent.active||controller.signal.aborted)return;
      if(!parent.mask) {
        mask=new CityFeatureMask(this.THREE,count);
        if(this.maskBytes()+mask.data.byteLength>=this.memoryBudget)throw Error('City feature masks exceed the memory budget');
        mask.bindObject(parent.object);parent.mask=mask;
      }
      parent.records=prepared;parent.status='ready';this.applyVisibleLandmarks(parent);
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
      this.bindReplacementGroups(object,record);
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
      if(object&&record.object!==object){this.disposeObject(object);record.replacementGroups=[];}
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
      record.replacementGroups=[];
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
      precise:{registered:this.replacements.landmarks.size,visible:[...this.visibleLandmarks],overrideTiles:loaded.filter(r=>r.replacement).length,
        hiddenGroups:loaded.reduce((sum,r)=>sum+(r.replacementGroups||[]).filter(group=>!group.object.visible).length,0)},
      geometryBytes:loaded.reduce((sum,r)=>sum+r.geometryBytes,0),memoryBytes:loaded.reduce((sum,r)=>sum+r.memoryBytes,0)+this.maskBytes(),maskBytes:this.maskBytes(),triangles:visible.reduce((sum,r)=>sum+r.triangles,0),
      features:visible.reduce((sum,r)=>sum+r.ids.length,0),active:visible.map(r=>({id:r.id,features:r.ids.length,triangles:r.triangles}))};
  }
  notify(){if(!this.destroyed)this.onChange(this.getState());}
  destroy(){this.destroyed=true;this.inflight?.controller.abort('destroyed');for(const object of [...this.parents.keys()])this.detach(object);}
}

// Staged public validator for incremental macro registries.
export {replacementRegistry as prepareReplacementRegistry};
