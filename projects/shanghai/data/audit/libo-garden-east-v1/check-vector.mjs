/** Replay the actual OSM fallback tile and verify that the black roof survives the partial mask. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const audit=path.dirname(fileURLToPath(import.meta.url)),project=process.env.SHANGHAI_PROJECT_ROOT||path.resolve(audit,'../../..');
const read=f=>JSON.parse(fs.readFileSync(f)),sha=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const module=path.join(project,'src/candidate-vector-clipping.js');
const {planCandidateVectorClipping}=await import(pathToFileURL(module));
const clip=globalThis.polygonClipping,contract=read(path.join(audit,'final-placement-contract.json'));
const placement=read(path.join(audit,'placement-geometry.json')),catalog=read(process.argv[3]),tile=read(process.argv[2]);
assert.equal(contract.id,'xuhui-libo-garden-east-house');assert.equal(tile.total_tile_buildings,23);
const existing=catalog.models.filter(v=>v.replacement_geometry).map(rule);
function rule(v){return {id:v.id,owner:v.owner,owners:v.owners,geometry:v.replacement_geometry,
    source_feature_ids:v.source_feature_ids,...(v.osm_replacement_geometry&&{osm_replacement_geometry:v.osm_replacement_geometry})};}
assert(!existing.some(r=>r.id===contract.id));
const parts=g=>g.type==='Polygon'?[g.coordinates]:g.coordinates;
const rad=Math.PI/180,k=6371008.8*Math.cos(contract.lat*rad),log=Math.asinh(Math.tan(contract.lat*rad));
function area(polys){
    return polys.reduce((total,poly)=>total+poly.reduce((sum,ring,j)=>{
        const pts=ring.map(([a,b])=>[(a-contract.lng)*rad*k,(Math.asinh(Math.tan(b*rad))-log)*k]);
        let a=0;for(let i=1;i<pts.length-1;i++)a+=(pts[i][0]-pts[0][0])*(pts[i+1][1]-pts[0][1])-(pts[i+1][0]-pts[0][0])*(pts[i][1]-pts[0][1]);
        return sum+(j?-1:1)*Math.abs(a)/2;
    },0),0);
}
const unchanged=[],affected=[];
for(const input of tile.nearby_features){
    const feature={...input,type:'Feature'};
    const run=rules=>planCandidateVectorClipping([feature],{candidateClips:rules},{source:'openmaptiles',sourceLayer:'building'});
    const before=run(existing),after=run([...existing,rule(contract)]);
    assert.equal(before.stats.clippingErrors,0);assert.equal(after.stats.clippingErrors,0);
    if(input.id!==147898520){assert.deepEqual(before,after);unchanged.push(input.id);continue;}
    const r0=before.residualData.features[0],r1=after.residualData.features[0];
    assert(r1);assert.deepEqual(r1.properties,input.properties);
    const previous=r0?parts(r0.geometry):clip.union(...parts(feature.geometry));const now=parts(r1.geometry);
    const cut=parts(contract.replacement_geometry);
    const delta=area(clip.intersection(previous,cut));
    const expected=placement.fallback_affected[0].area_cut_m2;
    assert(Math.abs(delta-expected)<.15,[delta,expected]);
    const erroneous=area(clip.xor(now,clip.difference(previous,cut)));assert(erroneous<.008,erroneous);
    const remain=area(clip.intersection(now,cut));assert(remain<.00004);
    assert.equal(parts(feature.geometry).length,2426);
    affected.push({id:input.id,original_components:2426,properties:r1.properties,affected_components:placement.fallback_affected[0].affected_components,
        previous_m2:area(previous),remaining_m2:area(now),removed_m2:delta,unintended_m2:erroneous,remaining_under_mask_m2:remain,
        retained_native_eastern_roof_m2:placement.source_records.far.eastern_flat_roof_retained_m2});
}
assert.equal(affected.length,1);assert.equal(unchanged.length,22);
fs.writeFileSync(process.argv[4],JSON.stringify({id:contract.id,passed:true,catalog_sha256:sha(process.argv[3]),
    data_sha256:tile.sha256,module_sha256:sha(module),script_sha256:sha(fileURLToPath(import.meta.url)),affected,unchanged},null,2)+'\n');
