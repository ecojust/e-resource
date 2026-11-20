/* Evaluate all-candidate shader capacity and the historical footprint, retained
   source, and open courtyards using the actual renderer's containment logic. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import * as THREE from '../../../vendor/three.module.js';
import {CandidateCityClipper} from '../../../src/candidate-city-clipping.js';
import {candidateGeometryContains} from '../../../src/candidate-city-integrations.js';
import {planCandidateVectorClipping} from '../../../src/candidate-vector-clipping.js';

const audit=path.dirname(fileURLToPath(import.meta.url)), project=path.resolve(audit,'../../..');
const sha=b=>createHash('sha256').update(b).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(path.join(project,p)));
const contract=JSON.parse(fs.readFileSync(path.join(audit,'final-placement-contract.json')));
const catalogBytes=fs.readFileSync(path.join(project,'data/candidate-city-integrations.json'));
const catalog=JSON.parse(catalogBytes);
const mapSource=read('source/precise/'+contract.id+'/footprint-review.json');
const row=catalog.models.find(r=>r.id===contract.id);
for(const key of ['owner','source_feature_ids','source_section_caps','site_replacement','replacement_geometry','collision_geometry','model_geometry_sha256']){
  assert.deepEqual(row[key],contract[key],key+' differs');
}
const k=6371008.8*Math.cos(row.lat*Math.PI/180);
const log=lat=>Math.asinh(Math.tan(lat*Math.PI/180));
const cs=Math.cos(Math.PI/12),sn=Math.sin(Math.PI/12);
function lngLat(x,y){
  const east=-cs*x+sn*y,north=-sn*x-cs*y;
  return [row.lng+east/k*180/Math.PI,Math.atan(Math.sinh(log(row.lat)+north/k))*180/Math.PI];
}
const projectWorld=(lng,lat,h=0)=>new THREE.Vector3((lng-row.lng)*Math.PI/180*k,h,(log(row.lat)-log(lat))*k);
function cityBudget(models){
  const unique=new Map();
  for(const m of models){
    if(m.replacement_geometry) unique.set(m.id,{id:m.id,geometry:m.replacement_geometry,owner:m.owner,owners:m.owners});
    if(m.site_replacement) unique.set(m.site_replacement.id,m.site_replacement);
  }
  const all=[...unique.values(),...models.flatMap(m=>m.display_height_clips||[])];
  const clipper=new CandidateCityClipper({THREE,geographicPosition:projectWorld});clipper.update(all);
  const {triangleLimit,triangles}=clipper.getState();clipper.dispose();return {triangleLimit,triangles};
}
const city=cityBudget(catalog.models),without=cityBudget(catalog.models.filter(r=>r.id!==contract.id));
assert.equal(city.triangles-without.triangles,4);assert.ok(city.triangles<=city.triangleLimit);
const north={...row,geometry:row.replacement_geometry}, stem=row.site_replacement;
const oldGarden=catalog.models.find(m=>m.id==='jingan-country-hospital');
const garden={...oldGarden,geometry:oldGarden.replacement_geometry};
const cuts=[north,stem,garden];
const residuals=[];
for(const source of ['overture-buildings','openmaptiles']){
  for(const id of [848,2764,3292,1805]){
    const owner=mapSource.owners.find(o=>o.local_id===id);
    const original={type:'Feature',id:1,properties:{id:owner.key.slice('building:'.length)},geometry:owner.geometry_wgs84};
    const plan=planCandidateVectorClipping([original],{candidateClips:cuts},{source,sourceLayer:'building'});
    assert.equal(plan.stats.clippingErrors,0);
    if(id===848||id===2764){
      assert.equal(plan.residualData.features.length,1);
      const residual=plan.residualData.features[0].geometry;
      const [cutAt,keepAt]=id===848?[[0,3],[-24,9]]:[[-1,29],[-8,39]];
      assert.equal(candidateGeometryContains(residual,lngLat(...cutAt)),false);
      assert.equal(candidateGeometryContains(residual,lngLat(...keepAt)),true);
    }else assert.equal(plan.residualData.features.length,0);
    residuals.push({source,owner:id,partial:plan.stats.partialIDs,residualFeatures:plan.residualData.features.length});
  }
}
const probes=[
  ['north block floor',0,3,true,'building'],['clinic stem outside both coarse blocks',0,22,true,'building'],
  ['stem joins southern source',-1,29,true,'building'],['north entrance forecourt',0,-8,false,null],
  ['eastern courtyard',-12,23,false,null],['western courtyard',9,24,false,null],
  ['preserved east end of 848',-24,9,false,'building'],['preserved south source 2764',-8,39,false,'building'],
  ['unrelated west neighbor 3292',21,8,false,'building'],['unrelated east neighbor 1805',-42,-4,false,'building'],
].map(([name,x,y,expected,sceneExpected])=>{
  const position=lngLat(x,y);
  assert.equal(candidateGeometryContains(row.collision_geometry,position),expected);
  return {name,position,modelObstacle:expected,sceneExpected};
});
const report={model:contract.id,registrySha256:sha(catalogBytes),scriptSha256:sha(fs.readFileSync(fileURLToPath(import.meta.url))),
  withoutThisModel:without,allCity:city,rows:catalog.resulting_city_count,vectorResiduals:residuals,groundProbes:probes};
fs.writeFileSync(path.join(audit,'runtime-placement.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(city));
