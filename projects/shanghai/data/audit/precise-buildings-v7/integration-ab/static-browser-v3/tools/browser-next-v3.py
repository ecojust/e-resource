#!/usr/bin/env python3
"""Single-browser candidate-building acceptance, generalized from frozen v6.
Explicit targets and exact navigation cardinality use actual candidate metadata.
The existing full/oblique/LOD/return, owner release/reset, source/near/far and
neighbor checks remain. Zero-photo geometry is supported without inventing
PhotoFacade or EXIF assertions. Preparation does not mark a model accepted;
actual browser failures can never be replaced by metadata claims.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlsplit, unquote

from playwright.sync_api import sync_playwright

os.environ['PW_TEST_SCREENSHOT_NO_FONTS_READY'] = '1'
import browser_expectations as expectations
TARGET_PROFILES = {}
_progress_callback = lambda label, **detail: None

def progress(label, **detail):
    _progress_callback(label, **detail)

CONFIG = 'bc00ae98308d26661b45dd7dab7b5098cab3ca4c7c7f9c1490122212af5e9956'

# Capture the existing instances through one restored getState wrapper. This is
# the same read-only instrumentation used by v5 acceptance; never calls owners.
INSTALL_PROBE = r"""async registry=>{
 const app=__SHANGHAI_APP__;
 const [{CityDetailStreamer},{LocalModelStreamer},{countExpandedTriangles},THREE]=await Promise.all([
   import(new URL('src/city-detail-streamer.js',document.baseURI).href),
   import(new URL('src/local-model-streamer.js',document.baseURI).href),
   import(new URL('src/model-resources.js',document.baseURI).href),
   import(new URL('vendor/three.module.js',document.baseURI).href)]);
 function capture(Class){let instance;const original=Class.prototype.getState;
   try{Class.prototype.getState=function(...args){instance=this;return original.apply(this,args)};app.scene.getStreamingState()}
   finally{Class.prototype.getState=original}if(!instance)throw Error('Cannot inspect '+Class.name);return instance}
 const detail=capture(CityDetailStreamer),local=capture(LocalModelStreamer);
 const probe=window.__V6_CAPTURE__={detail,local,registry,heldMasks:[],farLoadFailures:[]};
 // Preserve the real callback and scheduling; retain unthrottled diagnostics
 // before map-scene's notice throttle discards repeated transient failures.
 const notifyFarError=local.onError;
 local.onError=function(error,record){
   const request=local.inflight.get(record.id);
   probe.farLoadFailures.push({at:performance.now(),id:record.id,message:String(error?.message||error),
     status:record.status,aborted:request?.controller.signal.aborted??false,
     abortReason:request?.controller.signal.reason??null,wanted:local.wanted.has(record.id),
     hasObject:Boolean(record.object),visible:Boolean(record.object?.visible)});
   return notifyFarError.call(this,error,record);
 };
 // Synchronous, restored interception: the first traversal is the real
 // imported root used by countExpandedTriangles inside the public asset API.
 probe.assetState=id=>{
   const original=THREE.Object3D.prototype.traverse;let group=null,state;
   try{
     THREE.Object3D.prototype.traverse=function(...args){if(!group)group=this;return original.apply(this,args)};
     state=app.scene.getLandmarkAssetState(id);
   }finally{THREE.Object3D.prototype.traverse=original;}
   const glass=[],otherPhoto=[];
   if(group){
     let root=group;while(root.parent)root=root.parent;probe.sceneRoot=root;
     original.call(group,mesh=>{
       if(!mesh.isMesh)return;
       for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]){
         if(!material?.map||!/^PhotoFacade_/i.test(material.name||''))continue;
         const row={mesh:mesh.name,meshUUID:mesh.uuid,material:material.name,type:material.type,
           isMeshBasicMaterial:material.isMeshBasicMaterial===true,
           actualMeshBasicInstance:material instanceof THREE.MeshBasicMaterial,
           receiveShadow:mesh.receiveShadow,castShadow:mesh.castShadow,
           envMap:material.envMap?{name:material.envMap.name,uuid:material.envMap.uuid}:null,
           envMapIsNull:material.envMap===null,
           photographicRendering:material.userData?.photographicRendering||null};
         (/^PhotoFacade_.*(?:glass|glazing)/i.test(material.name)?glass:otherPhoto).push(row);
       }
     });
   }
   return {...state,actualPhotographicMaterials:{rootFound:Boolean(group),
     traverseRestored:THREE.Object3D.prototype.traverse===original,glass,otherPhoto}};
 };
 probe.shadowState=()=>{
   const sun=probe.sceneRoot?.children.find(o=>o.isDirectionalLight&&o.name==='Bund cached morning sun');
   const gl=app.scene.map.painter?.context?.gl;
   const maxTextureSize=gl?.getParameter(gl.MAX_TEXTURE_SIZE)??null;
   const lowMemory=Boolean(navigator.deviceMemory&&navigator.deviceMemory<=4),requestedSize=lowMemory?1024:4096;
   const expectedSize=Number.isFinite(maxTextureSize)&&maxTextureSize>0
     ?Math.min(requestedSize,2**Math.floor(Math.log2(maxTextureSize))):requestedSize;
   const camera=sun?.shadow.camera;
   return {found:Boolean(sun),deviceMemory:navigator.deviceMemory??null,lowMemory,maxTextureSize,requestedSize,expectedSize,
     mapSize:sun?[sun.shadow.mapSize.x,sun.shadow.mapSize.y]:null,
     camera:camera?{left:camera.left,right:camera.right,top:camera.top,bottom:camera.bottom,near:camera.near,far:camera.far}:null};
 };
 const exact=()=>new Set(registry.landmarks.filter(r=>{
   const a=app.scene.getLandmarkAssetState(r.id);return a.status==='loaded'&&a.visible;
 }).map(r=>r.id));
 const same=(a,b)=>a.length===b.length&&[...a].sort().every((x,i)=>x===[...b].sort()[i]);
 probe.holdMasks=()=>{probe.heldMasks=[...detail.parents.values()].filter(p=>p.mask).map(p=>({id:p.id,mask:p.mask}));
   return probe.heldMasks.map(p=>({id:p.id,owners:p.mask.owners.size}))};
 probe.audit=()=>{
   const active=exact(),errors=[],parents=[],neighborIDs=new Set();
   if(!same([...active],[...detail.visibleLandmarks]))errors.push('Precise visible IDs differ from actual loaded-visible landmarks');
   for(const p of detail.parents.values()){
     if(!p.mask)continue;
     const visible=p.records.filter(r=>r.object?.visible),expected=new Map();
     for(const r of visible)for(const id of r.ids)expected.set(id,(expected.get(id)||0)+1);
     const expectedPrecise=new Map();
     for(const [id,landmark] of p.replacement?.owners||[])if(active.has(landmark)){
       expected.set(id,(expected.get(id)||0)+1);
       if(!expectedPrecise.has(landmark))expectedPrecise.set(landmark,[]);expectedPrecise.get(landmark).push(id);
     }
     let badReferences=0,badBits=0;
     for(let id=0;id<p.mask.references.length;id++){
       if(p.mask.references[id] !== (expected.get(id)||0))badReferences++;
       if(Boolean(p.mask.data[id]) !== expected.has(id))badBits++;
     }
     const missingOwners=visible.some(r=>!p.mask.owners.has(r.owner))||
       [...expectedPrecise].some(([id])=>!p.preciseOwners?.has(id)||!p.mask.owners.has(p.preciseOwners.get(id)));
     const ownerCountWrong=p.mask.owners.size!==visible.length+expectedPrecise.size||
       (p.preciseOwners?.size||0)!==expectedPrecise.size;
     const invalidVisible=visible.some(r=>r.status!=='loaded'||!p.active||!p.object.visible);
     const near=[];
     for(const r of p.records){
       if(!r.object||!r.replacement)continue;
       const groups=(r.replacementGroups||[]).map(({object,landmark})=>({name:object.name,landmark,
         visible:object.visible,triangles:countExpandedTriangles(object),tag:object.userData.cityReplacement}));
       const expectedIDs=r.replacement.featureLocalIds.filter(id=>!r.replacement.groups.some(g=>g.local_ids.includes(id)));
       const kept=[];r.object.traverse(o=>{if(Array.isArray(o.userData?.cityPreservedLocalIds))kept.push(o)});
       const expectedTriangles=r.declaredTriangles-r.replacement.groups.reduce((n,g)=>n+g.expandedTriangles,0);
       const keptIDs=kept.flatMap(o=>o.userData.cityPreservedLocalIds),keptTriangles=kept.reduce((n,o)=>n+countExpandedTriangles(o),0);
       const passed=groups.length===r.replacement.groups.length&&groups.every(g=>{
         const e=r.replacement.groups.find(x=>x.name===g.name);
         return e&&g.landmark===e.landmark_id&&g.triangles===e.expandedTriangles&&g.visible===!active.has(g.landmark)&&
           same(g.tag.local_ids,e.local_ids)&&same(g.tag.feature_keys,e.feature_keys);
       })&&same(keptIDs,expectedIDs)&&kept.every(o=>o.visible)&&keptTriangles===expectedTriangles&&
         countExpandedTriangles(r.object)===r.declaredTriangles;
       if(!passed)errors.push('Complete target or neighbor group differs: '+r.id);
       if(r.object.visible)for(const id of keptIDs)neighborIDs.add(p.id+':'+id);
       near.push({id:r.id,visible:r.object.visible,status:r.status,url:r.url,ids:[...r.ids],groups,
         triangles:countExpandedTriangles(r.object),declaredTriangles:r.declaredTriangles,
         preservedNeighborIDs:keptIDs,preservedNeighborTriangles:keptTriangles,passed});
     }
     if(badReferences||badBits||missingOwners||ownerCountWrong||invalidVisible||p.mask.disposed)errors.push('Far mask ownership differs: '+p.id);
     parents.push({id:p.id,active:p.active,farVisible:p.object.visible,preciseOwners:[...expectedPrecise],
       visibleNear:visible.map(r=>r.id),badReferences,badBits,missingOwners,ownerCountWrong,invalidVisible,
       maskedCount:expected.size,owners:p.mask.owners.size,near});
   }
   const suppression=local.suppression,online=[];
   for(const entry of registry.landmarks){
     const owner='precise:'+entry.id,owned=suppression.owners.get(owner)||new Map();
     const keys=[...(entry.building_ids||[]).map(id=>'building\0'+id),...(entry.building_part_ids||[]).map(id=>'building_part\0'+id)];
     if(!same([...owned.keys()],active.has(entry.id)?keys:[]))errors.push('Dynamic online owner differs: '+entry.id);
     const sources=keys.map(key=>{
       const reference=suppression.references.get(key),[layer,id]=key.split('\0');
       let expected=0;for(const values of suppression.owners.values())if(values.has(key))expected++;
       const actual=reference?.count||0;if(actual!==expected)errors.push('Shared online refcount differs: '+key);
       let state=null;if(suppression.map.getSource(suppression.source))state=suppression.map.getFeatureState({source:suppression.source,sourceLayer:layer,id});
       return {layer,id,expectedReferences:expected,actualReferences:actual,state};
     });
     online.push({id:entry.id,active:active.has(entry.id),owner,keys:[...owned.keys()],sources});
   }
   const held=probe.heldMasks.map(({id,mask})=>({id,disposed:mask.disposed,owners:mask.owners.size,
     remainingReferences:mask.references.reduce((n,v)=>n+(v!==0),0),remainingBits:mask.data.reduce((n,v)=>n+(v!==0),0)}));
   return {passed:errors.length===0,errors,activePrecise:[...active],parents,online,
     onlinePending:suppression.pending.size,visibleNeighborIDs:[...neighborIDs],held,
     heldReleased:held.every(p=>p.disposed&&!p.owners&&!p.remainingReferences&&!p.remainingBits)};
 };
 probe.snapshot=()=>{
   const m=app.scene.map,t=m.transform,eye=t?.getCameraLngLat?.();
   return {mode:app.mode,districts:app.districts.length,controller:app.controller.getState?.()||{position:app.controller.position},
     camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),
       fov:m.getVerticalFieldOfView?.(),eye:eye?{lng:eye.lng,lat:eye.lat,alt:t.getCameraAltitude?.()}:null},
     landmarks:app.scene.getLandmarkState(),assets:Object.fromEntries(registry.landmarks.map(r=>[r.id,probe.assetState(r.id)])),
     actualShadow:probe.shadowState(),
     streaming:app.scene.getStreamingState(),cache:app.scene.getLandmarkCacheState(),
     source:app.scene.getCollisionState(),realism:app.scene.getRealismState(),audit:probe.audit(),
     farDiagnostics:{events:probe.farLoadFailures.slice(),currentErrors:[...local.records.values()].filter(r=>['error','missing'].includes(r.status)).map(r=>({id:r.id,status:r.status,wanted:local.wanted.has(r.id),visible:Boolean(r.object?.visible),retryAt:r.retryAt})),inflight:[...local.inflight].map(([id,r])=>({id,aborted:r.controller.signal.aborted,abortReason:r.controller.signal.reason??null}))}};
 };
 return {read_only_probe:true,restored_prototypes:true,monitored_far_error_callback:true,registered:detail.replacements.landmarks.size};
}"""

FETCH_JSON = r"""async files=>{
 const out={};for(const [key,file]of Object.entries(files)){
   const url=new URL(file,document.baseURI).href,r=await fetch(url);if(!r.ok)throw Error(url+': HTTP '+r.status);
   const b=await r.arrayBuffer(),sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('');
   out[key]={url,bytes:b.byteLength,sha256,data:JSON.parse(new TextDecoder().decode(b))};
 }return out;
}"""

AUDIT_ASSET = r"""async ({record,variant})=>{
 const hash=async b=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('');
 const file=variant==='full'?record.model:record.lod_model,url=new URL(file,document.baseURI).href;
 const response=await fetch(url);if(!response.ok)throw Error('GLB '+response.status+': '+url);
 const buffer=await response.arrayBuffer(),v=new DataView(buffer);
 if(buffer.byteLength<28||v.getUint32(0,true)!==0x46546c67||v.getUint32(4,true)!==2||v.getUint32(8,true)!==buffer.byteLength)throw Error('Invalid GLB header');
 const length=v.getUint32(12,true),doc=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,20,length))),bin=28+length;
 const images=await Promise.all((doc.images||[]).map(async image=>{
   if(image.uri||!Number.isInteger(image.bufferView))throw Error('Expected embedded image');
   const view=doc.bufferViews[image.bufferView],start=bin+(view.byteOffset||0);
   return {bytes:view.byteLength,mimeType:image.mimeType,sha256:await hash(buffer.slice(start,start+view.byteLength))};
 }));
 const photo=(doc.materials||[]).filter(m=>/^PhotoFacade_/i.test(m.name||'')&&m.pbrMetallicRoughness?.baseColorTexture);
 return {file,url,bytes:buffer.byteLength,sha256:await hash(buffer),images,mappedPhotoMaterials:photo.map(m=>m.name),
   triangles:(doc.meshes||[]).reduce((n,m)=>n+m.primitives.reduce((n,p)=>n+(doc.accessors[p.indices]?.count||0)/3,0),0),
   copyright:doc.asset.copyright||'',externalResources:(doc.buffers||[]).some(b=>b.uri&&!b.uri.startsWith('data:'))};
}"""


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_report(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def metres(a, b):
    return math.hypot(math.radians(a['lng']-b['lng'])*6378137*math.cos(math.radians(b['lat'])),
                      math.radians(a['lat']-b['lat'])*6378137)


def photo_check(record, state, variant):
    profile=TARGET_PROFILES.get(record['id']);require(profile is not None,'No frozen target profile')
    expectations.validate_record(record,profile)
    variant_profile=profile['variants']['web' if variant=='full' else 'lod']
    require(state.get('status') == 'loaded' and state.get('visible') is True and state.get('variant') == variant,
            f"{record['id']}: model is not actually visible loaded {variant}")
    triangles = record['triangles' if variant == 'full' else 'lod_triangles']
    require(state.get('triangles') == triangles, f"{record['id']}: actual triangles differ from manifest")
    photo = expectations.photo_policy(record)
    expected = (photo or {}).get('expected_images', {}).get('web' if variant == 'full' else 'lod', 0)
    require(expected in (0, 1), 'This QA requires explicit review of a new multi-photo schema')
    require(len(state.get('images', [])) == expected, f"{record['id']}: decoded photo count differs")
    require(expected==variant_profile['images'],'Decoded image policy differs from pinned final expectations')
    actual=state.get('actualPhotographicMaterials') or {}
    require(actual.get('rootFound') and actual.get('traverseRestored'), 'Actual loaded model not inspected or traverse not restored')
    glass=actual.get('glass',[]);other=actual.get('otherPhoto',[])
    require(len(glass)==variant_profile['glass_materials'],'Actual mapped photo-glass count differs from target role')
    require(len(other)==variant_profile['other_materials'],'Actual non-glass photo count differs from target role')
    require(sorted(m['material'] for m in glass+other)==sorted(variant_profile['material_names']),
            'Actual photographic material identity differs')
    if not expected:
        return {'passed': True, 'expected_photo_images': 0, 'decoded_images': [],
                'actual_glass_materials_checked':0,'other_photo_materials_not_subject_to_glass_assertion':0}
    require(state.get('photoMeshes', 0) > 0, 'No photographic mesh rendered')
    for material in glass:
        require(material.get('type')=='MeshBasicMaterial' and material.get('isMeshBasicMaterial') is True
                and material.get('actualMeshBasicInstance') is True,
                'Mapped photo glass still uses scene-lit material: '+material.get('material','?'))
        require(material.get('castShadow') is False and material.get('receiveShadow') is False,
                'Mapped photo glass casts/receives a scene shadow: '+material.get('material','?'))
        require(material.get('envMap') is None and material.get('envMapIsNull') is True,
                'Mapped photo glass still has a second environment reflection')
    # Other-photo rows, such as physical signs or stone walls, are deliberately not
    # subjected to glass-only unlit/shadow policy. Role/count/name still checked.

    spec = photo.get('orientation', {})
    raw = spec.get('rawSize')
    require(spec.get('uvConvention') == 'stored-pixels' and isinstance(raw, list) and len(raw) == 2,
            'Photographic orientation metadata missing')
    for image in state['images']:
        dims = [image['width'], image['height']]
        evidence = image.get('orientation') or {}
        require(evidence.get('rawSize') == raw and evidence.get('decodedSize') == dims and
                evidence.get('exifOrientation') == spec.get('exifOrientation'), 'Runtime photo orientation evidence differs')
        exif = spec.get('exifOrientation')
        if exif == 1:
            require(dims == raw and evidence.get('status') == 'identity' and evidence.get('corrected') is False,
                    'Ordinary photograph has incorrect decoded dimensions or UV correction')
        elif exif == 6:
            rotated = dims == raw[::-1]
            require(dims in (raw, raw[::-1]) and evidence.get('corrected') is rotated and evidence.get('status') ==
                    ('decoder-rotation-compensated' if rotated else 'decoder-kept-stored-pixels'), 'EXIF-6 compensation differs')
        else:
            raise AssertionError(f'Unsupported photo EXIF orientation requires explicit QA: {exif}')
    return {'passed': True, 'expected_photo_images': expected, 'decoded_images': state['images'],
            'actual_glass_materials_checked':len(glass),'other_photo_materials_not_subject_to_glass_assertion':len(actual.get('otherPhoto',[]))}


def wait_ready(page, identity, variant, timeout, require_near=False):
    progress('wait-model BEGIN', id=identity, variant=variant, require_near=require_near)
    page.wait_for_function(r"""({id,variant,near})=>{
      const a=__SHANGHAI_APP__,p=__V6_CAPTURE__,r=a.scene.getLandmarkState().find(x=>x.id===id),
        s=a.scene.getLandmarkAssetState(id),stream=a.scene.getStreamingState();
      if(!r||r.status!=='loaded'||r.loadingModel||r.activeVariant!==variant||!s.visible||stream.pendingStates||p.local.suppression.pending.size)return false;
      const parents=[...p.detail.parents.values()].filter(x=>x.replacement&&[...x.replacement.owners.values()].includes(id));
      if(!parents.some(x=>x.object.visible&&x.preciseOwners?.has(id)))return false;
      if(near&&!parents.some(x=>x.records.some(r=>r.object?.visible&&r.replacementGroups?.some(g=>g.landmark===id&&!g.object.visible))))return false;
      return p.audit().passed;
    }""", arg={'id': identity, 'variant': variant, 'near': require_near}, timeout=timeout, polling=250)
    progress('wait-model READY', id=identity, variant=variant)


def frame(page, timeout):
    progress('render-frame BEGIN')
    page.evaluate(r"""timeout=>new Promise((resolve,reject)=>{
      const m=__SHANGHAI_APP__.scene.map;
      const done=()=>{clearTimeout(timer);m.off('render',done);resolve()};
      const timer=setTimeout(()=>{m.off('render',done);reject(Error('Required actual render timed out'))},timeout);
      m.on('render',done);m.triggerRepaint();
    })""", min(timeout, 90000))
    progress('render-frame READY')


def near_view(page, identity):
    progress('navigate-near BEGIN', id=identity)
    page.evaluate(r"""async id=>{
      const a=__SHANGHAI_APP__,r=a.landmarks.find(r=>r.id===id);if(!r)throw Error('Unknown landmark '+id);
      a.syncMode('walk',false);a.controller.resetCamera();await a.selectPlace(r);a.scene.map.stop();a.scene.loadLandmarks();
    }""", identity)
    progress('navigate-near READY', id=identity)


def reviewed_oblique(profile):
    view=profile.get('reviewed_oblique')
    if view is None:return None
    require(view.get('scope')=='root-reviewed-actual-camera-v1','Unreviewed camera override')
    for key in ('diagnostic_sha256','visual_review_sha256','image_sha256'):
        require(bool(re.fullmatch(r'[0-9a-f]{64}',str(view.get('evidence',{}).get(key,'')))), 'Reviewed camera evidence binding missing: '+key)
    request=view.get('request',{})
    for key in ('from','to'):
        point=request.get(key,{})
        require(set(point)=={'lng','lat','alt'} and all(type(v) in (int,float) and math.isfinite(v) for v in point.values()),'Invalid reviewed camera point')
        require(abs(point['lng'])<=180 and abs(point['lat'])<=85,'Invalid reviewed camera geography')
    require(type(request.get('fov')) in (int,float) and math.isfinite(request['fov']) and 10<=request['fov']<=80,'Invalid reviewed actual FOV')
    return json.loads(json.dumps(request))


def check_reviewed_camera_state(camera,request):
    eye=camera.get('eye');require(eye is not None,'Actual reviewed camera eye missing')
    require(type(camera.get('fov')) in (int,float) and abs(camera['fov']-request['fov'])<1e-6,'Actual vertical FOV differs from reviewed request')
    horizontal=metres(eye,request['from']);vertical=abs(eye['alt']-request['from']['alt'])
    require(horizontal<.01 and vertical<.01,'Actual camera was clamped or moved from the reviewed normalized eye')
    return {'passed':True,'actual_fov':camera['fov'],'horizontal_error_m':horizontal,'vertical_error_m':vertical,'tolerance_m':.01}


def camera_view(page, record, distant=False):
    reviewed=None if distant else reviewed_oblique(TARGET_PROFILES.get(record['id'],{}))
    if reviewed is not None:
        page.evaluate(r"""v=>{const a=__SHANGHAI_APP__;a.syncMode('overview',false);a.scene.map.stop();
          a.scene.map.setVerticalFieldOfView(v.fov);a.scene.setCameraFromTo({from:v.from,to:v.to});a.scene.loadLandmarks();}""",reviewed)
        progress('reviewed-camera READY',id=record['id'],distant=False)
        return reviewed
    progress('camera BEGIN', id=record['id'], distant=distant)
    start,bearing = expectations.walk_pose(record)
    b = math.radians(bearing)
    outward, along = (-math.sin(b), -math.cos(b)), (math.cos(b), -math.sin(b))
    radius = max(600, record.get('lod_switch_out_m', 400)+180) if distant else 8
    anchor = [record['lng'], record['lat']] if distant else start
    lateral = 0 if distant else 12
    east, north = outward[0]*radius+along[0]*lateral, outward[1]*radius+along[1]*lateral
    target_height = min(15, record['height_m']*.36)
    request = {'from': {'lng': anchor[0]+math.degrees(east/(6378137*math.cos(math.radians(anchor[1])))),
                        'lat': anchor[1]+math.degrees(north/6378137), 'alt': target_height+(110 if distant else 5)},
               'to': {'lng': record['lng'], 'lat': record['lat'], 'alt': target_height}, 'fov': 36.87 if distant else 50}
    page.evaluate(r"""v=>{const a=__SHANGHAI_APP__;a.syncMode('overview',false);a.scene.map.stop();
      a.scene.map.setVerticalFieldOfView?.(v.fov);a.scene.setCameraFromTo({from:v.from,to:v.to});a.scene.loadLandmarks();}""", request)
    progress('camera READY', id=record['id'], distant=distant)
    return request


def environment_proxy(environ=None):
 # Test-environment transport only. BrowserContext.request and route.fetch use
 # this same explicit context proxy; the launcher bytes/URLs stay unchanged.
 env=os.environ if environ is None else environ
 name=next((name for name in ('HTTPS_PROXY','HTTP_PROXY') if env.get(name)),None)
 require(name is not None,'Proxy QA requires HTTPS_PROXY or HTTP_PROXY')
 value=urlsplit(env[name])
 require(value.scheme in ('http','https') and value.hostname and value.path in ('','/')
   and not value.query and not value.fragment,'Unsupported environment proxy URL')
 try:port=value.port
 except ValueError:raise RuntimeError('Invalid environment proxy port') from None
 host=value.hostname
 require(not any(c.isspace() or ord(c)<32 for c in host),'Invalid environment proxy host')
 server=value.scheme+'://'+('['+host+']' if ':' in host else host)+((':'+str(port)) if port else '')
 bypass='localhost,127.0.0.1'
 proxy={'server':server,'bypass':bypass}
 if value.username is not None:proxy['username']=unquote(value.username)
 if value.password is not None:proxy['password']=unquote(value.password)
 safe={'enabled':True,'source_environment':name,'scheme':value.scheme,'host':host,'port':port,
  'bypass':bypass,'credentials_supplied':value.username is not None or value.password is not None,
  'scope':'Explicit Playwright BrowserContext proxy shared by browser requests, context.request and route.fetch; localhost remains direct.',
  'remote_urls_or_bytes_rewritten':False}
 return proxy,safe


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', '--base-url', dest='url', required=True, help='Project root HTTP(S) URL; index.html also accepted')
    parser.add_argument('--output', '--out', dest='output', type=Path, required=True)
    parser.add_argument('--targets', nargs='+', required=True, help='Actual selected candidate navigation IDs; no implicit target list')
    parser.add_argument('--expected-record-count',type=int,required=True,help='Exact candidate navigation cardinality, e.g. 21 for existing20 plus129')
    parser.add_argument('--use-env-proxy',action='store_true',help='Explicitly use HTTPS_PROXY/HTTP_PROXY for this test context; local hosts bypass')
    parser.add_argument('--expectations',type=Path,required=True,help='Pinned final metadata and locally verified raw/web/LOD expectations')
    parser.add_argument('--registry-path',default='data/precise-buildings-v6.json')
    parser.add_argument('--landmarks-path',default='data/landmarks.json')
    parser.add_argument('--timeout-ms', type=int, default=240000)
    parser.add_argument('--chromium', default='/usr/bin/chromium')
    parser.add_argument('--width', type=int, default=1040)
    parser.add_argument('--height', type=int, default=760)
    parser.add_argument('--dpr', type=float, default=1)
    parser.add_argument('--reset-only', action='store_true', help='Exercise selected near model, manifest reset and owner replay only; full/LOD/release cycle is not claimed')
    parser.add_argument('--force-osm', action='store_true', help='Deliberately abort Overture PMTiles/STAC; record these expected aborts separately')
    return parser.parse_args()


def main():
    args = parse_args()
    pinned=expectations.load_profile(args.expectations,args.targets)
    for profile in pinned['targets'].values():reviewed_oblique(profile)
    require(args.expected_record_count==pinned['expected_record_count'],'CLI count differs from frozen actual candidate count')
    global TARGET_PROFILES
    TARGET_PROFILES=pinned['targets']
    require(urlsplit(args.url).scheme in ('http', 'https'), '--url must be HTTP(S)')
    require(len(set(args.targets)) == len(args.targets), 'Duplicate targets')
    require(not args.reset_only or len(args.targets)==1, '--reset-only requires exactly one --targets value')
    require(args.timeout_ms > 0 and args.width > 0 and args.height > 0 and args.dpr > 0, 'Invalid dimensions or timeout')
    args.output.mkdir(parents=True, exist_ok=True)
    require(not (args.output/'browser.json').exists(), 'Use a new output directory; existing browser.json will not be overwritten')
    report = {'schema':'precise-building-browser-v7-candidate','started_at':utc(),'passed':False,'technical_passed':False,
              'targets':args.targets,'expected_record_count':args.expected_record_count,'expectations_sha256':hashlib.sha256(args.expectations.read_bytes()).hexdigest(),'expectations':pinned,'static_candidate_navigation':True,'catalog_workflow_tested':False,'reset_only':args.reset_only,'url':args.url,'single_browser':True,'force_osm':args.force_osm,
              'viewport':{'width':args.width,'height':args.height,'dpr':args.dpr},'timeout_ms':args.timeout_ms,
              'progress':[],'console_warnings':[],'captures':[],'asset_audits':[],'checks':[],'page_errors':[],'shader_errors':[],
              'asset_errors':[],'request_failures':[],'expected_aborts':[],'console_errors':[],
              'external_http_errors':[],'forced_outage_requests':[],'hardware_performance_test':False,
              'visual_review':{'status':'pending','required':True,'checks':['No doubled building/wall surfaces',
                'Window panes are not opaque black','Photograph features have correct upright direction',
                'Neighbor buildings retain detail','Architecture resembles source photographs']}}
    write = lambda: write_report(args.output/'browser.json', report)
    write()
    started=time.monotonic()
    def checkpoint(label, **detail):
        row={'stage':label,'utc':utc(),'elapsed_seconds':round(time.monotonic()-started,3),**detail}
        report['progress'].append(row);report['current_stage']=row
        print('PROGRESS '+json.dumps(row,ensure_ascii=False),flush=True);write()
    global _progress_callback
    _progress_callback=checkpoint
    progress('script-ready')
    browser = page = None
    cumulative_neighbors = set()
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['script_sha256'] = script_hash
    proxy_options,network = environment_proxy() if args.use_env_proxy else (None,{'enabled':False,'source':'Playwright default transport'})
    report['network']=network
    base = args.url.split('#',1)[0].split('?',1)[0]
    if not base.endswith('/'): base = base.rsplit('/',1)[0]+'/' if base.endswith('.html') else base+'/'

    def critical(url):
        path = urlsplit(url).path.lower()
        return path.endswith(('.glb','.glb.gz','/ready.json')) or ('/shanghai/' in path and path.endswith(('.js','.json','.jpg','.png','.webp')))

    def response_seen(response):
        if response.status >= 400:
            row = {'url':response.url,'status':response.status}
            report['asset_errors' if critical(response.url) or response.url.startswith(base) else 'external_http_errors'].append(row)
            print('HTTP_ERROR '+json.dumps(row),flush=True);write()

    def request_failed(request):
        row = {'url':request.url,'error':request.failure}
        if 'ERR_ABORTED' in str(request.failure) or request.url in report['forced_outage_requests']:
            report['expected_aborts'].append(row)
        else:
            report['request_failures'].append(row)
            if critical(request.url) or request.url.startswith(base): report['asset_errors'].append(row)
        print('REQUEST_FAILED '+json.dumps(row),flush=True);write()

    def console_seen(message):
        if message.type not in ('error','warning'): return
        row = {'type':message.type,'text':message.text,'location':message.location}
        terms = ('webglprogram','validate_status','gl_invalid','context lost','linkprogram','invalid_operation','invalid_value','invalid_enum','shader error','shader failed')
        if any(s in message.text.lower() for s in terms): report['shader_errors'].append(row)
        elif message.type == 'error': report['console_errors'].append(row)
        else:report['console_warnings'].append(row)
        print('CONSOLE '+json.dumps(row,ensure_ascii=False),flush=True);write()

    def page_error(error):
        report['page_errors'].append(str(error));print('PAGE_ERROR '+str(error),flush=True);write()

    def capture(name, record=None, variant=None, request=None, near=False):
        frame(page, args.timeout_ms)
        progress('state-snapshot BEGIN', name=name)
        # A render can finish a different generic macro after wait_ready returned.
        # Keep the zero-pending assertion, but wait for a fresh coherent state
        # instead of failing on that legitimate in-flight owner batch.
        handle = page.wait_for_function(r"""({id,variant,near})=>{
          const s=__V6_CAPTURE__.snapshot();
          const a=id?s.assets[id]:null;
          const ready=s.audit.passed&&s.audit.onlinePending===0&&
            s.streaming.pendingStates===0&&s.streaming.detail.metadataMismatches===0&&
            (!id||(a?.status==='loaded'&&a.visible&&a.variant===variant))&&
            (!near||s.audit.parents.some(p=>p.near.some(r=>r.visible&&r.groups.some(g=>g.landmark===id&&!g.visible))));
          window.__V6_LAST_CAPTURE_WAIT__={pending:s.audit.onlinePending,
            streamingPending:s.streaming.pendingStates,errors:s.audit.errors,ready};
          return ready?s:false;
        }""",arg={'id':record['id'] if record else None,'variant':variant,'near':near},
          timeout=args.timeout_ms,polling=250)
        try:state=handle.json_value()
        finally:handle.dispose()
        progress('state-snapshot READY', name=name)
        require(state['districts'] == 16, 'District navigation no longer includes 16 districts')
        require(state['audit']['passed'], 'Live ownership audit failed: '+str(state['audit']['errors']))
        require(state['audit']['onlinePending'] == 0, 'Source owner updates remain pending')
        require(state['streaming']['detail']['metadataMismatches'] == 0, 'Near metadata mismatch')
        shadow=state.get('actualShadow') or {};declared=(state.get('realism') or {}).get('lighting') or {}
        require(shadow.get('found'), 'Actual directional shadow camera not found')
        require(shadow.get('mapSize')==[shadow['expectedSize']]*2, 'Actual shadow map size differs from device-clamped 4096/1024 policy')
        camera=shadow.get('camera') or {}
        require([camera.get(k) for k in ('left','right','top','bottom')]==[-48,48,48,-48], 'Actual shadow camera half extent is not 48 m')
        require(declared.get('shadowSize')==shadow['expectedSize'] and declared.get('shadowHalfExtent')==48, 'Lighting diagnostic differs from actual shadow camera')
        state['shadow_check']={'passed':True,'expectedSize':shadow['expectedSize'],'halfExtent':48}

        if record and request and variant=='full' and TARGET_PROFILES[record['id']].get('reviewed_oblique'):
            state['reviewed_camera_check']=check_reviewed_camera_state(state['camera'],request)

        if record:
            state['photo_check'] = photo_check(record, state['assets'][record['id']], variant)
            if variant == 'distant':
                eye = state['camera']['eye'];require(eye is not None, 'No actual distant camera position')
                state['distance_from_building_m'] = metres(eye, record)
                require(state['distance_from_building_m'] > record.get('lod_switch_out_m',400), 'Actual camera did not cross LOD outer threshold')
            if near:
                matches=[r for p in state['audit']['parents'] for r in p['near'] if r['visible'] and any(g['landmark']==record['id'] for g in r['groups'])]
                require(matches, 'Target near override is not visible; far fallback cannot pass the near test')
        for item in state['audit']['online']:
            if state['source']['buildingSource']=='overture':
                for src in item['sources']:
                    require(bool((src['state'] or {}).get('localModel')) == (src['expectedReferences']>0), 'Actual online GERS state differs from shared owner references')
        cumulative_neighbors.update(state['audit']['visibleNeighborIDs'])
        progress('screenshot BEGIN', name=name)
        path=args.output/(name+'.png');page.screenshot(path=str(path),timeout=min(args.timeout_ms,90000))
        progress('screenshot READY', name=name)
        report['captures'].append({'name':name,'image':path.name,'requested_camera':request,**state})
        print('CAPTURE', name, flush=True);write();return state

    def audit_asset(record, variant):
        progress('asset-audit BEGIN', id=record['id'], variant=variant)
        profile=TARGET_PROFILES[record['id']];expectations.validate_record(record,profile)
        value=page.evaluate(AUDIT_ASSET,{'record':record,'variant':variant})
        prefix='web' if variant=='full' else 'lod'
        require(value['bytes']==record[prefix+'_bytes'] and value['sha256']==record[prefix+'_sha256'], 'Actual GLB bytes/SHA differ: '+record['id']+' '+variant)
        require(value['bytes']<100000000 and not value['externalResources'], 'Runtime GLB is oversized or requires external geometry')
        require(value['triangles']==record['triangles' if variant=='full' else 'lod_triangles'], 'Actual GLB triangle count differs')
        photo=expectations.photo_policy(record) or {};expected=photo.get('expected_images',{}).get('web' if variant=='full' else 'lod',0)
        require(len(value['images'])==expected, 'Embedded image count differs from metadata')
        variant_profile=profile['variants'][prefix]
        require(expected==variant_profile['images'],'Actual image count differs from pinned final policy')
        require(sorted(value['mappedPhotoMaterials'])==sorted(variant_profile['material_names']),'Actual mapped material identity differs')
        if expected:
            require(expected==1 and value['mappedPhotoMaterials'] and value['images'][0]['sha256']==photo['sha256']==profile['source_photo']['sha256'] and value['images'][0]['bytes']==photo['bytes']==profile['source_photo']['bytes'], 'Embedded photograph differs from declared source')
            normal=lambda s:re.sub(r'[^a-z0-9]','',str(s).lower())
            require(bool(photo.get('author')) and photo['author'] in value['copyright'] and
                    bool(photo.get('license')) and normal(photo['license']) in normal(value['copyright']), 'Photo attribution/license missing from GLB')
        report['asset_audits'].append({'id':record['id'],'variant':variant,'passed':True,**value});write()
        progress('asset-audit READY', id=record['id'], variant=variant)

    with sync_playwright() as playwright:
        try:
            progress('browser-launch BEGIN')
            browser=playwright.chromium.launch(executable_path=args.chromium,headless=True,
                args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'])
            progress('browser-launch READY')
            context_options={'viewport':{'width':args.width,'height':args.height},'device_scale_factor':args.dpr}
            if proxy_options:context_options['proxy']=proxy_options
            context=browser.new_context(**context_options)
            page=context.new_page();page.set_default_timeout(args.timeout_ms)
            page.on('pageerror',page_error)
            page.on('console',console_seen);page.on('response',response_seen);page.on('requestfailed',request_failed)
            page.add_init_script("window.__V6_CONTEXT_LOSSES__=0;document.addEventListener('webglcontextlost',()=>window.__V6_CONTEXT_LOSSES__++,true)")
            if args.force_osm:
                def route_request(route):
                    u=route.request.url
                    if '.pmtiles' in u or ('overture' in u.lower() and ('stac' in u.lower() or u.endswith('catalog.json'))):
                        report['forced_outage_requests'].append(u);route.abort()
                    else:route.continue_()
                page.route('**/*',route_request)
            progress('page-navigation BEGIN')
            page.goto(urljoin(base,'index.html')+'#mode=walk',wait_until='domcontentloaded',timeout=args.timeout_ms)
            progress('page-navigation DOM_READY')
            link=page.get_by_role('link',name='Open the page')
            if link.count():link.click()
            progress('app-controller BEGIN')
            page.wait_for_function('()=>Boolean(window.__SHANGHAI_APP__?.controller)',timeout=args.timeout_ms,polling=250)
            progress('app-controller READY')
            report['final_url']=page.url
            progress('metadata-fetch BEGIN')
            fetched=page.evaluate(FETCH_JSON,{'registry':args.registry_path,'landmarks':args.landmarks_path,
                'city':'assets/city-detail/manifest.json'})
            progress('metadata-fetch READY')
            registry=fetched['registry']['data'];city=fetched['city']['data'];landmarks=fetched['landmarks']['data']
            require(registry.get('complete') is True and registry.get('schema')=='city-precise-overrides-v1','Incomplete precise registry')
            require(city.get('complete') is True and city.get('model_count')==1708 and city.get('feature_count')==1796419 and city.get('configuration_sha256')==CONFIG,'Immutable complete v5 city manifest differs')
            require(len({r['id'] for r in landmarks})==len(landmarks)==args.expected_record_count,'Actual candidate navigation cardinality differs')
            require(fetched['landmarks']['sha256']==pinned['metadata_source']['landmarks_sha256'],'Candidate navigation bytes changed after expectation freeze')
            records={r['id']:r for r in landmarks if r['id'] in args.targets}
            require(set(records)==set(args.targets),'Requested buildings have not been registered')
            expected_neighbors,neighbor_details=expectations.validate_registry(registry,fetched['registry']['sha256'],pinned,[args.targets[-1]] if args.reset_only else args.targets)
            for record in records.values():expectations.validate_record(record,TARGET_PROFILES[record['id']])
            report['derived_neighbor_expectations']={'ids':sorted(expected_neighbors),'near':neighbor_details}
            report['records']=records
            report['metadata']={k:{a:b for a,b in v.items() if a!='data'} for k,v in fetched.items()}
            report['registry']=registry
            progress('readonly-probe BEGIN')
            report['probe']=page.evaluate(INSTALL_PROBE,registry);write()
            progress('readonly-probe READY')
            if not args.reset_only:
                for identity in args.targets:
                    record=records[identity]
                    near_view(page,identity);wait_ready(page,identity,'full',args.timeout_ms,True)
                    capture(identity+'-walk-full',record,'full',near=True);audit_asset(record,'full')
                    requested=camera_view(page,record);wait_ready(page,identity,'full',args.timeout_ms,True)
                    capture(identity+'-windows-oblique',record,'full',requested,near=True)
                    requested=camera_view(page,record,True);wait_ready(page,identity,'distant',args.timeout_ms)
                    capture(identity+'-distant-lod',record,'distant',requested);audit_asset(record,'distant')
                    near_view(page,identity);wait_ready(page,identity,'full',args.timeout_ms,True)
                    capture(identity+'-returned-full',record,'full',near=True)
                # Actual visibility release through navigation, not direct mutation.
                page.evaluate(r"""()=>{const a=__SHANGHAI_APP__;a.syncMode('overview',false);a.scene.map.stop();
                  a.scene.setCameraFromTo({from:{lng:121.1,lat:31.1,alt:900},to:{lng:121.1,lat:31.1,alt:0}});a.scene.loadLandmarks()}""")
                progress('release-owner-wait BEGIN')
                page.wait_for_function("()=>{const p=__V6_CAPTURE__,a=p.audit();return a.passed&&!a.activePrecise.length&&!a.onlinePending}",timeout=args.timeout_ms,polling=250)
                progress('release-owner-wait READY')
                released=capture('precise-owners-released')
                require(all(not p['preciseOwners'] for p in released['audit']['parents']),'Hidden landmarks retained far owners')
                last=records[args.targets[-1]];near_view(page,last['id']);wait_ready(page,last['id'],'full',args.timeout_ms,True)
                capture('precise-owners-returned',last,'full',near=True)
            else:
                last=records[args.targets[-1]]
                near_view(page,last['id']);wait_ready(page,last['id'],'full',args.timeout_ms,True)
                capture('before-city-manifest-reset',last,'full',near=True)
            report['held_before_reset']=page.evaluate('()=>__V6_CAPTURE__.holdMasks()')
            require(report['held_before_reset'],'No live far mask to exercise reset')
            progress('manifest-reset BEGIN')
            page.evaluate("async()=>{const a=__SHANGHAI_APP__;await a.scene.setCityManifest(new URL('assets/city-detail/manifest.json',document.baseURI).href);a.scene.loadLandmarks()}")
            progress('manifest-reset READY')
            wait_ready(page,last['id'],'full',args.timeout_ms,True)
            state=capture('after-city-manifest-reset',last,'full',near=True)
            require(state['audit']['heldReleased'],'Old far masks survived manifest reset')
            require(expected_neighbors.issubset(cumulative_neighbors),'Not all preserved neighbor features were actually visible in near models')
            report['neighbors']={'expected':sorted(expected_neighbors),'observed':sorted(cumulative_neighbors),'passed':True}
            losses=page.evaluate('window.__V6_CONTEXT_LOSSES__');report['webgl_context_losses']=losses
            require(not losses and not report['page_errors'] and not report['shader_errors'] and not report['asset_errors'],'Page, WebGL or required-asset errors occurred; see report')
            if args.force_osm:
                require(report['forced_outage_requests'],'Forced outage did not intercept an Overture request')
                require(any(c['source']['buildingSource']=='osm' for c in report['captures']),'Forced OSM fallback was not observed')
            report['technical_passed']=True;report['passed']=True
            report['pass_scope']=('Technical selected near-model loading, owner release/replay on manifest reset and selected neighbors. LOD/release navigation cycle not run.' if args.reset_only else 'Technical loading, ownership, neighbor conservation, photo metadata, LOD and reset.')+' Visual review remains explicitly pending.'
        except Exception as error:
            report['error']={'type':type(error).__name__,'message':str(error)}
            write();print('FAIL '+json.dumps(report['error']),flush=True)
            progress('failure-diagnostics BEGIN')
            if page:
                try:report['failure_state']=page.evaluate('()=>window.__V6_CAPTURE__?.snapshot()||null')
                except Exception as failure:report['failure_state_error']=str(failure)
                try:page.screenshot(path=str(args.output/'failure.png'),timeout=30000)
                except Exception as failure:report['failure_screenshot_error']=str(failure)
            raise
        finally:
            report['finished_at']=utc();write()
            if browser:browser.close()
    print(json.dumps({'passed':report['passed'],'report':str(args.output/'browser.json'),
                      'visual_review':'pending','captures':len(report['captures'])}),flush=True)


if __name__=='__main__':
    main()
