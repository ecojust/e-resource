// Verify proposal against production containment and all-city shader budget.
// Run with <Shanghai project directory> <placement contract> <macro folder>.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import { registerHooks } from 'node:module';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { gunzipSync } from 'node:zlib';

const [project, file, macroDir] = process.argv.slice(2).map(p => path.resolve(p));
const local = p => pathToFileURL(path.join(project,p)).href;
const sha = content => createHash('sha256').update(content).digest('hex');
registerHooks({resolve(s,c,next) {
  return s === 'three' ? {url:local('vendor/three.module.js'), shortCircuit:true} : next(s,c);
}});
const THREE = await import(local('vendor/three.module.js'));
const { GLTFLoader } = await import(local('vendor/GLTFLoader.js'));
const { MeshoptDecoder } = await import(local('vendor/meshopt_decoder.module.js'));
const { planCandidateVectorClipping } = await import(local('src/candidate-vector-clipping.js'));
const { CandidateSourceSections } = await import(local('src/candidate-source-sections.js'));
const { CandidateCityClipper } = await import(local('src/candidate-city-clipping.js'));
const { candidateGeometryContains } = await import(local('src/candidate-city-integrations.js'));
const bytes = fs.readFileSync(file);
const contract = JSON.parse(bytes);
const catalogBytes = fs.readFileSync(path.join(project,'data/candidate-city-integrations.json'));
const catalog = JSON.parse(catalogBytes);
const models = catalog.models;
const registered = models.filter(row => row.id === contract.id);
assert.equal(registered.length, 1, 'Final catalog must contain the garden facade');
for (const key of ['lng', 'lat', 'heading', 'scale', 'owner', 'source_feature_ids',
  'replacement_geometry', 'collision_geometry', 'source_section_caps', 'model_geometry_sha256']) {
  assert.deepEqual(registered[0][key], contract[key], 'Catalog differs from placement: ' + key);
}
// CandidateCityState collapses shared site clips by ID.
const baseClips = new Map();
for(const p of models){
  if(p.replacement_geometry) baseClips.set(p.id,{geometry:p.replacement_geometry,owner:p.owner,owners:p.owners});
  if(p.site_replacement) baseClips.set(p.site_replacement.id,p.site_replacement);
}
const clips = [...baseClips.values(), ...models.flatMap(p => p.display_height_clips || [])];
const rad = Math.PI/180, earth = 6371008.8;
const log = lat => Math.log(Math.tan(Math.PI/4+lat*rad/2));
const k = earth*Math.cos(contract.lat*rad);
const origin = [121.4737,31.2304], kMap = earth*Math.cos(origin[1]*rad);
function geographicPosition(lng, lat, h=0) {
  return new THREE.Vector3(kMap*(lng-origin[0])*rad, h*kMap/(earth*Math.cos(lat*rad)), -kMap*(log(lat)-log(origin[1])));
}
function lngLat(x,y) {
  const angle=-contract.heading*rad;
  const east=x*Math.cos(angle)-y*Math.sin(angle), north=x*Math.sin(angle)+y*Math.cos(angle);
  return [contract.lng+east/k/rad, (2*Math.atan(Math.exp(log(contract.lat)+north/k))-Math.PI/2)/rad];
}
const checks = [
  ['central plinth',0,.5,true,true], ['ground in front of recessed bays',15,1,false,true],
  ['infill upper-ground pier',15,3.4,true,true], ['end portico',33,.5,true,true],
  ['garden path',0,-6,false,false], ['rear coarse source',0,10,false,false],
  ['west source',-47,1,false,false], ['east source',45,1,false,false],
].map(([name,x,y,blocked,cut])=>{
  const point=lngLat(x,y);
  assert.equal(candidateGeometryContains(contract.collision_geometry,point),blocked,name);
  assert.equal(candidateGeometryContains(contract.replacement_geometry,point),cut,name);
  return {name, uv:[x,y], point, structuralCollision:blocked, sourceCut:cut};
});
const source = JSON.parse(fs.readFileSync(path.join(project,'source/precise',contract.id,'footprint-review.json')));
const sourceId = contract.source_feature_ids.building[0];
const original = {type:'Feature',id:1,properties:{id:sourceId},geometry:source.source_geometry_wgs84};
const vectorResults=[];
for(const name of ['overture-buildings','openmaptiles']){
  const plan=planCandidateVectorClipping([original],{
    candidateClips:[{geometry:contract.replacement_geometry,source_feature_ids:contract.source_feature_ids}],
  },{source:name,sourceLayer:'building'});
  assert.equal(plan.stats.clippingErrors,0);
  assert.equal(plan.residualData.features.length,1);
  const residual=plan.residualData.features[0].geometry;
  for(const [x,y,retained] of [[0,-2,false],[0,10,true],[-47,1,true],[45,1,true]]){
    assert.equal(candidateGeometryContains(residual,lngLat(x,y)),retained);
  }
  vectorResults.push({source:name,partialIDs:plan.stats.partialIDs,retainsBackAndSides:true});
}
const clipper = new CandidateCityClipper({THREE, geographicPosition});
clipper.update(clips);
const allCity = clipper.getState();
assert(allCity.triangles<=allCity.triangleLimit);
const owner=contract.owner;
const getHash=p=>sha(fs.readFileSync(p));
const ready=JSON.parse(fs.readFileSync(path.join(macroDir,'READY.json')));
const tile=ready.near.find(r=>r.featureLocalIds.includes(owner.feature_local_id));
const results=[];
let sectionCheck;
for(const [variant,name,record] of [
  ['near',tile.file,{id:tile.id,parent:{id:owner.macro_id},ids:tile.featureLocalIds}],
  ['far','far.glb',{id:owner.macro_id}],
]){
  const input=fs.readFileSync(path.join(macroDir,name));
  const data=variant==='near' ? gunzipSync(input) : input;
  const scene=(await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(
    data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength), '')).scene;
  clipper.bindObject(scene,record);
  let meshCount=0;
  scene.traverse(mesh=>{
    if(!mesh.isMesh) return;
    meshCount++;
    const passes=[['standard',mesh.material],['depth',mesh.customDepthMaterial],['distanceRGBA',mesh.customDistanceMaterial]];
    for(const [kind,mat] of passes){
      const lib=THREE.ShaderLib[kind];
      const shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:{}};
      mat.onBeforeCompile(shader,{});
      const uniforms=shader.uniforms;
      const tex=uniforms.candidateClipTexture.value.image.data, count=uniforms.candidateClipCount.value;
      assert.equal(uniforms.candidateHasFeatureIds.value, variant==='far'?1:0);
      const targetIndices=Array.from({length:count},(_,i)=>i).filter(i=>tex[16*i+12]===owner.feature_local_id && tex[16*i+13]===uniforms.candidateMacro.value);
      assert.equal(targetIndices.length,6);
      if(variant==='near') assert.equal(count,6);
    }
  });
  results.push({variant,file:name,sha256:sha(input),meshCount,targetClipTriangles:6,materialPasses:['standard','depth','distanceRGBA']});
  if (variant === 'far') {
    const world = new THREE.Scene();
    world.add(scene);
    const sections = new CandidateSourceSections(world, geographicPosition);
    const sourceMacro = {id: owner.macro_id, object: scene, sha256: sha(input)};
    assert.equal(sections.sync([registered[0]], [sourceMacro]), true);
    const [state] = sections.getState();
    assert.equal(state.segments, 7);
    assert.equal(state.feature_local_id, owner.feature_local_id);
    const capMesh = world.children.find(object => object !== scene);
    const position = capMesh.geometry.getAttribute('position');
    const heights = Array.from({length:position.count}, (_,i) => position.getY(i)+capMesh.position.y);
    const cap = contract.source_section_caps;
    assert(Math.abs(Math.max(...heights)-geographicPosition(...cap.height_reference,cap.roof_m).y) < .00001);
    sections.sync([], [sourceMacro]);
    assert.deepEqual(sections.getState(), []);
    sections.sync([registered[0]], [{...sourceMacro, sha256: '0'.repeat(64)}]);
    assert.deepEqual(sections.getState(), []);
    sections.sync([registered[0]], [sourceMacro]);
    sections.sync([registered[0]], []);
    assert.deepEqual(sections.getState(), []);
    sectionCheck = {...state, minWorldY:Math.min(...heights), maxWorldY:Math.max(...heights),
      hiddenWithoutCandidate:true, hiddenWithoutSource:true, hiddenWithWrongHash:true};
    sections.dispose();
    scene.removeFromParent();
  }
  clipper.releaseObject(scene);
}
clipper.update([]);
assert.equal(clipper.triangleCount,0);
clipper.dispose();
console.log(JSON.stringify({scope:'Serialized mask/collision predicates and real source material bindings on CPU. Browser pixels recorded separately.',
  catalogSha256:sha(catalogBytes),contractSha256:sha(bytes), scriptSha256:getHash(new URL(import.meta.url)),
  allCityTriangles:allCity.triangles,limit:allCity.triangleLimit,checks,vectorResults,sectionCheck,results,
  runtimeModuleSha256:Object.fromEntries(['src/candidate-city-clipping.js','src/candidate-city-integrations.js',
    'src/candidate-source-sections.js','src/candidate-vector-clipping.js','src/map-scene.js'].map(p => [p,getHash(path.join(project,p))]))},null,2));
