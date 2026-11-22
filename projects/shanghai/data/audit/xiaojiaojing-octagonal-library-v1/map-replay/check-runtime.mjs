/** Re-run on a signed predecessor (private model) or the real successor (published catalog). */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import http from 'node:http';
import crypto from 'node:crypto';
import vm from 'node:vm';
import {registerHooks,createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
import os from 'node:os';
import {gunzipSync} from 'node:zlib';

const work = path.dirname(fileURLToPath(import.meta.url));
const audit = path.dirname(work);
const proj = path.resolve(work, '../../../..');
const read = p => JSON.parse(fs.readFileSync(p));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const stage = process.argv[2];
assert(['310', '311'].includes(stage), 'Pass the historical stage 310 or 311.');
const result = process.argv[3] || path.resolve('library-map-' + stage + '.json');
const argPlacement = path.join(audit, 'final-placement-contract.json');
const placement = read(argPlacement);
const pilot = path.join(proj, 'assets/models/candidates', placement.id);
const manifest = read(path.join(pilot, 'manifest.json'));
const review = read(path.join(work, 'footprints.json'));
const original = {original_bindings: review.frozen_bindings};
const ground = read(path.join(audit,'placement-geometry.json')).ground.map(row => ({
  ...row, original_owners: [], blocked_by_pavilion: row.modelObstacle
}));
const signed = read(path.join(work, 'signed-inputs.json'))[stage];
const httpInputs = {};
async function get(name) {
  const input = signed.files[name];
  assert(input, name);
  let bytes;
  if (input.archive) {
    bytes = gunzipSync(fs.readFileSync(path.join(work, input.archive)));
  } else {
    for (const root of [proj, process.env.SHANGHAI_MAP_SOURCE_ROOT].filter(Boolean)) {
      const local = path.join(root, name);
      if (!fs.existsSync(local)) continue;
      const candidate = fs.readFileSync(local);
      if (sha(candidate) === input.sha256) { bytes = candidate; break; }
    }
    if (!bytes) {
      const response = await fetch(input.url);
      assert.equal(response.status, 200, input.url);
      bytes = Buffer.from(await response.arrayBuffer());
    }
  }
  assert.equal(bytes.length, input.bytes, name);
  assert.equal(sha(bytes), input.sha256, name);
  httpInputs[name] = {source: input.archive || input.url, bytes: bytes.length, sha256: sha(bytes)};
  return bytes;
}
const catalog=JSON.parse(await get('data/candidate-city-integrations.json'));assert.equal(httpInputs['data/candidate-city-integrations.json'].sha256,signed.catalog_sha256);
for(const binding of original.original_bindings){const name=binding.repository_path.replace('projects/shanghai/','');assert.equal(sha(await get(name)),binding.sha256,name);}
const modules=['src/candidate-bridge-walk.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/candidate-vector-clipping.js','src/candidate-vector-geometry.js','src/candidate-source-sections.js','src/historical-view.js','src/ordinary-scene-adapter.js','src/ordinary-building-catalog.js','src/ordinary-contracts.js','src/model-resources.js','src/local-model-streamer.js','src/ordinary-asset-verification.js','vendor/polygon-clipping.umd.min.js','vendor/three.module.js','vendor/three.core.js','vendor/GLTFLoader.js','vendor/BufferGeometryUtils.js','vendor/meshopt_decoder.module.js'];
const frozen = fs.mkdtempSync(path.join(os.tmpdir(), 'library-map-'));
process.on('exit', () => fs.rmSync(frozen, {recursive:true, force:true}));
fs.writeFileSync(path.join(frozen, 'package.json'), JSON.stringify({type:'module'}));
for (const name of modules) {
  const bytes = await get(name);
  const dest = path.join(frozen, name);
  fs.mkdirSync(path.dirname(dest), {recursive:true});
  const local = path.join(proj, name);
  try {
    if (!fs.existsSync(local) || sha(fs.readFileSync(local)) !== sha(bytes)) throw Error('source differs');
    fs.linkSync(local, dest);
  } catch {
    fs.writeFileSync(dest, bytes, {flag:'wx'});
  }
  assert.equal(sha(fs.readFileSync(dest)), signed.files[name].sha256, name);
}
const moduleURL=p=>pathToFileURL(path.join(frozen,p)).href,load=p=>import(moduleURL(p));
registerHooks({resolve(specifier,ctx,next){return specifier==='three'?{url:moduleURL('vendor/three.module.js'),shortCircuit:true}:next(specifier,ctx)}});
const THREE=await load('vendor/three.module.js'),{CandidateCityClipper}=await load('src/candidate-city-clipping.js'),{CandidateCityState,candidateGeometryContains:inside,mergeCandidateCityModels,validCandidateGeometry}=await load('src/candidate-city-integrations.js'),{planCandidateVectorClipping:planVectors}=await load('src/candidate-vector-clipping.js'),{loadOrdinaryLandmarkAsset}=await load('src/ordinary-scene-adapter.js');
const {GLTFLoader}=await load('vendor/GLTFLoader.js'),{MeshoptDecoder}=await load('vendor/meshopt_decoder.module.js');
const h=placement.heading*Math.PI/180,deg=Math.PI/180,k=6371008.8*Math.cos(placement.lat*deg),log=lat=>Math.asinh(Math.tan(lat*deg));
function wgs([x,y]){return [placement.lng+(x*Math.cos(h)+y*Math.sin(h))/k/deg,Math.atan(Math.sinh(log(placement.lat)+(-x*Math.sin(h)+y*Math.cos(h))/k))/deg];}
const published=catalog.models.some(m=>m.id===placement.id),actual=catalog.models.find(m=>m.id===placement.id);
if(Number(stage)>=311)assert(published);else assert(!published);
if(actual){assert(!actual.owner && !actual.replacement_geometry && !actual.display_height_clips?.length);for(const key of ['lng','lat','heading','source_feature_ids','collision_geometry','model_geometry_sha256'])assert.deepEqual(actual[key],placement[key],key);}
const assets = actual?.assets || {};
const transfers = new Map();
for (const [key, role] of [['web', 'full'], ['lod', 'lod']]) {
  const m = manifest.assets[role];
  const local = path.join(pilot, m.file);
  const bytes = fs.readFileSync(local);
  assert.equal(sha(bytes), placement.model_geometry_sha256[key]);
  if (!actual) assets[key] = {file:m.file, sha256:sha(bytes), bytes:bytes.length};
  assert.equal(assets[key].sha256, sha(bytes));
  transfers.set('/' + assets[key].file, local);
}
const server = http.createServer((request, response) => {
  const source = transfers.get(request.url);
  if (!source) { response.writeHead(404).end(); return; }
  response.writeHead(200, {'Content-Length':fs.statSync(source).size, 'Content-Type':'model/gltf-binary'});
  fs.createReadStream(source).pipe(response);
});
await new Promise((resolve, reject) => {
  server.once('error', reject);
  server.listen(0, '::1', resolve);
});
const address = 'http://[::1]:' + server.address().port + '/';

const records=new Map(),scene=new THREE.Scene(),record={...placement,...(actual||{}),assets,id:placement.id,kind:'building',height_m:11.42,city_integration:true,catalogBaseURL:address};
const assetReceipts={},results=[];
const checkRow={...record,assets:Object.fromEntries(Object.entries(assets).map(([key,a])=>[key,{...a,file:a.file.startsWith('assets/')?a.file:'assets/'+a.file}]))};
assert(validCandidateGeometry(record.collision_geometry,{collision:true}));assert.equal(mergeCandidateCityModels([],{schema:'candidate-city-integrations-v1',models:[checkRow]})[0].id,record.id);assert.equal(record.replacement_geometry,null);assert(!record.owner);
records.set(record.id,record);const st=new CandidateCityState({getRecords:()=>records,getScene:()=>scene});
function capture(step){
 st.sync();const state=st.getState(),active=['full','restored','distant'].includes(step);assert.equal(state.active.length,active?1:0);assert.deepEqual(state.clips,[]);assert.deepEqual(state.displayClips,[]);
 const cols=st.collisions();assert.equal(cols.length,active?1:0);
 const samples=ground.map(row=>{const q=wgs(row.xy);
    const isOriginal=row.original_owners.length>0;const added=cols.some(c=>inside(c.geometry,q));
    assert.equal(added,active&&row.blocked_by_pavilion);
    for(const layer of ['building','building_part'])for(const name of ['overture-buildings','openmaptiles'])for(const id of review.neighbors)assert.equal(st.clipsPoint(q[0],q[1],{name,layer,id,propertyId:id}),false);
    return {xy:row.xy,originalOwners:row.original_owners,blockedByPavilion:added,combinedBlocked:isOriginal||added};});
 results.push({step,active:state.active,cuts:state.clips.length,renderCuts:state.displayClips.length,collisionRecords:cols.length,samples});
}
const png=createRequire(import.meta.url)('pngjs').PNG;
const decodedTextures=[];globalThis.self=globalThis;globalThis.createImageBitmap=async function(blob){
 const bytes=Buffer.from(await blob.arrayBuffer()),image=png.sync.read(bytes);
 const rec={width:image.width,height:image.height,encoded_sha256:sha(bytes),rgba_sha256:sha(image.data)};
 assert(rec.width>0&&rec.height>0);decodedTextures.push(rec);
 return {width:image.width,height:image.height,data:image.data,close(){}};
};
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
async function install(variant){if(record.object)scene.remove(record.object);const response=await loadOrdinaryLandmarkAsset({record,variant,loader}),o=response.scene;scene.add(o);record.object=o;record.status='loaded';record.activeVariant=variant;let meshes=0,tris=0;o.traverse(n=>{if(n.isMesh){meshes++;tris+=(n.geometry.index?.count??n.geometry.attributes.position.count)/3;}});assert.equal(tris,manifest.assets[variant==='full'?'full':'lod'].triangles);assetReceipts[variant]={...o.userData.__ordinaryVerifiedAsset,meshes,triangles:tris,transfer:actual?'frozen-model-http':'private-signed-geometry-http'};}
try{capture('before');await install('full');capture('full');record.object.visible=false;capture('hidden');record.object.visible=true;capture('restored');await install('distant');capture('distant');scene.remove(record.object);capture('unloaded');}finally{if(server){server.closeAllConnections();await new Promise(r=>server.close(r));}}
assert(decodedTextures.length>0);fs.writeFileSync(result,JSON.stringify({passed:true,stage:Number(stage),published,model:record.id,predecessor_signature:signed.production_receipt_sha256,placement_sha256:sha(fs.readFileSync(argPlacement)),source_inputs:httpInputs,ground_samples_per_state:ground.length,model_transfer:assetReceipts,textures:decodedTextures,results},null,1)+'\n');console.log(result,results.map(s=>[s.step,s.cuts,s.samples.filter(q=>q.blockedByPavilion).length]));
