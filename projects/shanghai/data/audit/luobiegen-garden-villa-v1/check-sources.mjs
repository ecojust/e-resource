/** Verify the actual production clipping implementation against both providers and the villa connector. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const audit=path.dirname(fileURLToPath(import.meta.url));
const project=path.resolve(audit,'../../..');
const runtime=process.env.SHANGHAI_PROJECT_ROOT||project;
const mod=f=>import(pathToFileURL(path.join(runtime,f)));
const hash=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const read=f=>JSON.parse(fs.readFileSync(f));
const {planCandidateVectorClipping}=await mod('src/candidate-vector-clipping.js');
const {candidateGeometryContains}=await mod('src/candidate-city-integrations.js');
const {CandidateCityClipper}=await mod('src/candidate-city-clipping.js');
const THREE=await mod('vendor/three.module.js');
const cf=path.join(audit,'final-placement-contract.json'),contract=read(cf);
const sf=path.join(project,'source/precise',contract.id,'footprint-review.json'),source=read(sf);
const geometry=read(path.join(audit,'placement-geometry.json'));
const osm=read(process.argv[2]);
const expected=read(path.join(audit,'fallback-vector.json'));
assert.equal(osm.tile_sha256,expected.tile_sha256);
const features=source.owners.map(o=>({type:'Feature',id:o.key.slice(9),geometry:o.geometry_wgs84,properties:{}}));
const clip={...contract,geometry:contract.replacement_geometry};
const kept=geometry.ground_probes.find(w=>w.name==='western connecting strip').wgs84;
const cleared=geometry.ground_probes.find(w=>w.name==='central hall').wgs84;
const vectors=[];
for(const [name,providerFeatures,owner] of [['overture-buildings',features,features[0].id],['openmaptiles',osm.features,13160566110]]){
  const plan=planCandidateVectorClipping(providerFeatures,{candidateClips:[clip]},{source:name,sourceLayer:'building'});
  assert.equal(plan.stats.clippingErrors,0);assert.equal(plan.desired.size,1);
  assert.equal([...plan.desired.values()][0].id,owner);assert.equal(plan.residualData.features.length,1);
  const residual=plan.residualData.features[0].geometry;
  assert(candidateGeometryContains(residual,kept));assert(!candidateGeometryContains(residual,cleared));
  vectors.push({source:name,original_feature_count:providerFeatures.length,replaced_only:owner,retained_western_connector:true,model_removed_from_original:true,stats:plan.stats});
}
const clipper=new CandidateCityClipper({THREE,geographicPosition:(lng,lat)=>new THREE.Vector3((lng-contract.lng)*95000,0,-(lat-contract.lat)*111195)});
for(const group of source.near_tiles){
  const object=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());
  clipper.bindObject(object,{id:group.id,parent:{id:source.frozen_macro},ids:group.feature_local_ids});
}
clipper.update([clip]);
const state=clipper.getState();
for(const g of state.ownerScopedSources){const own=g.feature_local_ids.includes(1431);assert.deepEqual(g.clip_feature_local_ids,own?[1431]:[]);assert.equal(Boolean(g.triangles),own);}
const bindingFiles=['src/candidate-vector-clipping.js','src/candidate-vector-geometry.js','src/candidate-city-integrations.js','src/candidate-city-clipping.js'];
const out=process.env.QA_OUTPUT_DIR||audit;fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'runtime-source-checks.json'),JSON.stringify({id:contract.id,contract_sha256:hash(cf),reference_sha256:hash(sf),script_sha256:hash(fileURLToPath(import.meta.url)),input_geojson_sha256:hash(process.argv[2]),tile_sha256:osm.tile_sha256,
  runtime_sha256:Object.fromEntries(bindingFiles.map(f=>[f,hash(path.join(runtime,f))])),vectors,source_draws:state.ownerScopedSources,per_draw_limit:state.triangleLimit},null,2)+'\n');
console.log('Verified partial villa replacement on both true providers and',state.ownerScopedSources.length,'draw groups.');
