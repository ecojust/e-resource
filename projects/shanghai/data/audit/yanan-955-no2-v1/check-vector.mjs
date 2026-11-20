/** Exercise the existing and proposed clipping rules on every fallback footprint near Lane 955. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const audit=path.dirname(fileURLToPath(import.meta.url));
const project=process.env.SHANGHAI_PROJECT_ROOT||path.resolve(audit,'../../..');
const read=f=>JSON.parse(fs.readFileSync(f));
const sha=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const mod=path.join(project,'src/candidate-vector-clipping.js');
const {planCandidateVectorClipping}=await import(pathToFileURL(mod));
const tile=read(process.argv[2]);
const catalog=read(process.argv[3]);
const contract=read(path.join(audit,'final-placement-contract.json'));
assert.equal(contract.id,'jingan-yanan-955-no2');
assert.equal(tile.total_tile_buildings,26);
const before=catalog.models.filter(v=>v.replacement_geometry).map(rule);
function rule(v){return {id:v.id,owner:v.owner,owners:v.owners,geometry:v.replacement_geometry,
    source_feature_ids:v.source_feature_ids,...(v.osm_replacement_geometry && {osm_replacement_geometry:v.osm_replacement_geometry})};}
assert(!before.some(r=>r.id===contract.id));
const samples=[];
for(const feature of tile.nearby_features){
    const real={...feature,type:'Feature'};
    const states=[before,[...before,rule(contract)]].map(rules=>
        planCandidateVectorClipping([real],{candidateClips:rules},{source:'openmaptiles',sourceLayer:'building'}));
    for(const state of states)assert.equal(state.stats.clippingErrors,0);
    assert.deepEqual(states[0],states[1]);
    samples.push({id:feature.id,stats:states[1].stats,geometry_sha256:createHash('sha256').update(JSON.stringify(feature.geometry)).digest('hex')});
}
assert.deepEqual(samples.map(r=>r.id),[64634100]);
const placement=read(path.join(audit,'placement-geometry.json'));
const distance=placement.osm_fallback.nearby_distances_m['64634100'];
assert(distance>10);
fs.writeFileSync(process.argv[4],JSON.stringify({passed:true,id:contract.id,previous_count:catalog.resulting_city_count,
    previous_catalog_sha256:sha(process.argv[3]),clipper_sha256:sha(mod),tile_sha256:tile.sha256,
    tile_buildings:26,closest_distance_m:distance,nearest_features:tile.nearest_features,
    samples,script_sha256:sha(fileURLToPath(import.meta.url))},null,2)+'\n');
