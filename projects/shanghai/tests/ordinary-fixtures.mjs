import {createHash} from 'node:crypto';
import * as THREE from '../vendor/three.module.js';
export {THREE};
export const sha = bytes => createHash('sha256').update(bytes).digest('hex');
export const bytes = text => new TextEncoder().encode(text);
export const json = object => bytes(JSON.stringify(object));
export const BASE = bytes('SYNTHETIC baseline near, parser fixture only');
export const OVERRIDE = bytes('SYNTHETIC complete target plus preserved neighbor');
export const FAR = 'a'.repeat(64), CONFIG = 'b'.repeat(64), DECODED = 'c'.repeat(64);
export const KEY = 'building:e73638a1-a217-47f7-a17b-151902f0fece';
export const view = {lng: 121, lat: 31, zoom: 18, mode: 'walk'};
export const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
export async function until(check) { const limit=performance.now()+3000; while(!check()) { if(performance.now()>limit)throw Error('Fixture timeout');await delay(2); } }
export function deferred() {let resolve;return {promise:new Promise(r=>resolve=r),resolve:value=>resolve(value)};}
export function farObject() {
  const root = new THREE.Group(), geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute([0,0,0,1,0,0,0,1,0,2,0,0,3,0,0,2,1,0],3));
  geometry.setAttribute('_feature_id_0',new THREE.Float32BufferAttribute([1,1,1,2,2,2],1));
  root.add(new THREE.Mesh(geometry,new THREE.MeshStandardMaterial())); return root;
}
export function nearObject({macro='14-13718-6695',id='ordinary-test',override=true}={}) {
  const root=new THREE.Group(), target=new THREE.Group(); target.name='complete-target';
  if(override)target.userData.cityReplacement={macro_id:macro,landmark_id:id,local_ids:[1],feature_keys:[KEY]};
  target.add(new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial()));
  const neighbor=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());neighbor.position.x=3;neighbor.name='preserved-neighbor';
  root.add(target,neighbor);return root;
}
export function fixture({macro='14-13718-6695',id='ordinary-test',lng=121}={}) {
  const box=[lng,31,lng+.0001,31.0001];
  const boundary={type:'Polygon',coordinates:[[[lng,31],[lng+.0001,31],[lng+.0001,31.0001],[lng,31.0001],[lng,31]]]};
  const near={id:'near-a',file:'near.glb',sha256:sha(BASE),decoded_sha256:DECODED,size_bytes:BASE.length,
    expandedTriangles:24,geometryBytes:10000,featureLocalIds:[1,2],geographic_bbox:box};
  const index={configuration_sha256:CONFIG,feature_count:2,far:{sha256:FAR},near:[near]};
  const registry={schema:'city-precise-overrides-v1',complete:true,
    landmarks:[{id,confirmed_boundary:boundary,building_ids:[KEY.slice(9)],building_part_ids:[]}],
    macros:[{id:macro,feature_count:2,baseline_configuration_sha256:CONFIG,baseline_far_sha256:FAR,near:[{
      id:near.id,baseline_file:near.file,baseline_sha256:near.sha256,baseline_decoded_sha256:DECODED,featureLocalIds:[1,2],
      model:{file:`assets/city-overrides-v6/${macro}/override.glb`,sha256:sha(OVERRIDE),size_bytes:OVERRIDE.length,expandedTriangles:24,geometryBytes:10000},
      groups:[{name:'complete-target',landmark_id:id,local_ids:[1],feature_keys:[KEY],expandedTriangles:12}]}]}]};
  const assets={web:{file:`assets/models/precise/${id}/web.glb`,bytes:4,sha256:'d'.repeat(64)},lod:{file:`assets/models/precise/${id}/lod.glb`,bytes:4,sha256:'e'.repeat(64)}};
  const record={id,kind:'building',detail_level:'architectural',name:'Synthetic ordinary building',source_provider:'Synthetic non-OSM provider',source_url:'https://example.test/source',
    source_license:[{id:'CC-BY-4.0'}],asset_license:[{id:'CC-BY-SA-4.0'}],district:{id:'test',name:'Explicit district'},districtId:'test',district_name:'Explicit district',
    anchor:[lng,31],lng,lat:31,bbox:box,height_m:10,height_estimated:true,confirmed_boundary:boundary,navigation:{listed:false},accepted:true,pending_stages:[],
    acceptance:Object.fromEntries(['source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','browser_proof','uncertainty'].map(k=>[k,{status:'passed'}])),
    assets,model:assets.web.file,web_sha256:assets.web.sha256,web_bytes:4,lod_model:assets.lod.file,lod_sha256:assets.lod.sha256,lod_bytes:4,
    owner:{macro_id:macro,feature_local_id:1,feature_key:KEY,baseline_configuration_sha256:CONFIG,near_owner_id:near.id,
      baseline_near_sha256:near.sha256,baseline_near_feature_local_ids:[1,2],replace_only_local_ids:[1],preserve_neighbor_local_ids:[2]}};
  const registryBytes=json(registry), registryMeta={file:`data/precise-buildings/macros/${macro}/replacement.json`,bytes:registryBytes.length,sha256:sha(registryBytes)};
  const shard={schema:'precise-building-macro-v1',macro_id:macro,record_count:1,url_base:'project-root',models:[record],replacement_registry:registryMeta};
  const shardBytes=json(shard),entry={id:macro,bbox:box,record_count:1,file:`data/precise-buildings/macros/${macro}/index.json`,bytes:shardBytes.length,sha256:sha(shardBytes)};
  const catalog={schema:'precise-building-catalog-v1',url_base:'project-root',macro_count:1,record_count:1,macros:[entry]};
  return {macro,id,record,index,registry,shard,entry,catalog,files:new Map([[entry.file,shardBytes],[registryMeta.file,registryBytes]])};
}
