/** Replay the actual OSM fallback tile and verify that all other building parts survive the short Huangpu Road gray-building facade section. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const audit=path.dirname(fileURLToPath(import.meta.url)),project=process.env.SHANGHAI_PROJECT_ROOT||path.resolve(audit,'../../..');
const read=f=>JSON.parse(fs.readFileSync(f)),sha=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const module=path.join(project,'src/candidate-vector-clipping.js');
const {planCandidateVectorClipping}=await import(pathToFileURL(module));
const clip=globalThis.polygonClipping,contract=read(path.join(process.env.QA_CONTRACT_DIRECTORY||audit,'final-placement-contract.json'));
const placement=read(path.join(process.env.QA_CONTRACT_DIRECTORY||audit,'placement-geometry.json')),catalog=read(process.argv[3]),tile=read(process.argv[2]);
assert.equal(contract.id,'hongkou-unrra-gray-building-north-front');assert.equal(tile.sha256,'4fb028ba24738a5b5d34cd7c65859a7370fa48036e588f75c165167f8351406b');
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
    if(input.id!==84778190||input.component!==230){assert.deepEqual(before,after);unchanged.push([input.id,input.component]);continue;}
    const r0=before.residualData.features[0],r1=after.residualData.features[0];
    assert(r1);assert.deepEqual(r1.properties,input.properties);
    const previous=r0?parts(r0.geometry):clip.union(...parts(feature.geometry));const now=parts(r1.geometry);
    const cut=parts(contract.replacement_geometry);
    const delta=area(clip.intersection(previous,cut));
    const expected=placement.osm_fallback.intersecting_component.intersection_m2;
    assert(Math.abs(delta-expected)<.02,[delta,expected]);
    const difference=area(clip.xor(now,clip.difference(previous,cut)));
    assert(difference<.004,difference);
    affected.push({id:input.id,component:input.component,original_m2:area(previous),remaining_m2:area(now),cut_m2:delta,unintended_difference_m2:difference});
}
assert.equal(affected.length,1);assert.equal(unchanged.length,13);
fs.writeFileSync(process.argv[4],JSON.stringify({id:contract.id,passed:true,catalog_sha256:sha(process.argv[3]),
    data_sha256:tile.sha256,module_sha256:sha(module),script_sha256:sha(fileURLToPath(import.meta.url)),affected,unchanged},null,2)+'\n');
