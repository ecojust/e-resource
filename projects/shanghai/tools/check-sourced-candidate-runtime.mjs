/* Exercise the complete production catalog, a real owner clip, both vector
 * sources and nearby ground witnesses with the renderer's own implementations. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const caseFile=path.resolve(process.argv[2]), audit=path.dirname(caseFile);
const spec=JSON.parse(fs.readFileSync(caseFile));
const project=process.env.SHANGHAI_PROJECT_ROOT||path.resolve(audit,'../../..');
const local=f=>path.join(project,f);
const read=f=>JSON.parse(fs.readFileSync(local(f)));
const hash=b=>createHash('sha256').update(b).digest('hex');
const THREE=await import(pathToFileURL(local('vendor/three.module.js')));
const {CandidateCityClipper}=await import(pathToFileURL(local('src/candidate-city-clipping.js')));
const {planCandidateVectorClipping}=await import(pathToFileURL(local('src/candidate-vector-clipping.js')));
const {candidateGeometryContains}=await import(pathToFileURL(local('src/candidate-city-integrations.js')));
const contract=JSON.parse(fs.readFileSync(path.join(audit,'final-placement-contract.json')));
const ownerID=contract.owner.feature_local_id;
const addedOwners=spec.addedOwners??[ownerID];
const declaredOwners=(contract.owners??[contract.owner]).map(o=>o.feature_local_id);
assert.deepEqual([...addedOwners].sort((a,b)=>a-b),[...declaredOwners].sort((a,b)=>a-b));
const review=read('source/precise/'+contract.id+'/footprint-review.json');
const catalog=read('data/candidate-city-integrations.json'),model=catalog.models.find(r=>r.id===contract.id);
for(const key of ['owner','source_feature_ids','replacement_geometry','collision_geometry','model_geometry_sha256'])
  assert.deepEqual(model[key],contract[key],key);
const rad=Math.PI/180,k=6371008.8*Math.cos(model.lat*rad);
const log=lat=>Math.asinh(Math.tan(lat*rad));
function geographicPosition(lng,lat,height=0){
  return new THREE.Vector3((lng-model.lng)*rad*k,height*k/(6371008.8*Math.cos(lat*rad)),(log(model.lat)-log(lat))*k);
}
function point(x,y){
  const h=model.heading*rad;
  const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
  return [model.lng+east/k/rad,Math.atan(Math.sinh(log(model.lat)+north/k))/rad];
}
function evaluate(models){
  const base=new Map();
  for(const r of models){
    if(r.replacement_geometry)base.set(r.id,{id:r.id,owner:r.owner,owners:r.owners,geometry:r.replacement_geometry});
    if(r.site_replacement)base.set(r.site_replacement.id,r.site_replacement);
  }
  const clipper=new CandidateCityClipper({THREE,geographicPosition});
  const source=review.near_tiles.find(g=>g.feature_local_ids.includes(ownerID));
  assert.ok(addedOwners.every(id=>source.feature_local_ids.includes(id)),'Expected every added owner in the tested streamed group');
  const cube=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());
  clipper.bindObject(cube,{id:source.id,parent:{id:review.frozen_macro},ids:source.feature_local_ids});
  const adjacentGroup=review.near_tiles.find(g=>!g.feature_local_ids.includes(ownerID));
  const second=adjacentGroup&&new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());
  if(second)clipper.bindObject(second,{id:adjacentGroup.id,parent:{id:review.frozen_macro},ids:adjacentGroup.feature_local_ids});
  clipper.update([...base.values(),...models.flatMap(r=>r.display_height_clips||[])]);
  const state=clipper.getState();
  const counts=[...clipper.macroTables.values()].map(t=>t.triangles);
  const result={triangles:state.triangles,perDrawLimit:state.triangleLimit,macroTextures:state.macroTextures,
    largestFeatureScan:Math.max(clipper.defaultTable.maxFeatureSpan,...[...clipper.macroTables.values()].map(t=>t.maxFeatureSpan)),
    denseMacroTables:state.denseMacroTables,macroTriangleCounts:counts.sort((a,b)=>b-a),largestShaderTable:Math.max(clipper.defaultTable.triangles,...counts),
    scopedTargetDraw:state.ownerScopedSources[0],adjacentDraw:state.ownerScopedSources[1]??null};
  clipper.dispose();cube.geometry.dispose();cube.material.dispose();if(second){second.geometry.dispose();second.material.dispose();}return result;
}
const before=evaluate(catalog.models.filter(r=>r.id!==contract.id)),after=evaluate(catalog.models);
assert.equal(after.triangles-before.triangles,spec.addedTriangles??spec.groupTriangles);assert.ok(after.triangles>after.perDrawLimit);
assert.ok(after.macroTextures>1&&after.largestFeatureScan<=after.perDrawLimit);
const oldOwners=spec.existingGroupOwners||[];
assert.deepEqual([...after.scopedTargetDraw.clip_feature_local_ids].sort((a,b)=>a-b),[...oldOwners,...addedOwners].sort((a,b)=>a-b));assert.equal(after.scopedTargetDraw.triangles,spec.groupTriangles);
assert.deepEqual(before.scopedTargetDraw.clip_feature_local_ids,oldOwners);
if(after.adjacentDraw)assert.deepEqual(after.adjacentDraw,before.adjacentDraw);
const clip={...model,geometry:model.replacement_geometry};
const targets=new Set(addedOwners);
const vector=[];
for(const source of ['overture-buildings','openmaptiles']){
  for(const owner of review.owners.filter(r=>[...addedOwners,...spec.neighbors].includes(r.local_id))){
    const geometry=owner.geometry_wgs84??owner.geometry;
    assert.ok(geometry?.type==='Polygon'||geometry?.type==='MultiPolygon','Missing source footprint for '+owner.local_id);
    const feature={type:'Feature',id:1,properties:{id:owner.key.slice(9)},geometry};
    const plan=planCandidateVectorClipping([feature],{candidateClips:[clip]},{source,sourceLayer:'building'});
    assert.equal(plan.stats.clippingErrors,0);
    const retainedProbes=spec.ground.filter(p=>p.modelObstacle===false&&p.expected==='building'&&(p.ownerLocalId??ownerID)===owner.local_id);
    const partial=targets.has(owner.local_id)&&retainedProbes.length>0;
    assert.equal(plan.residualData.features.length,partial?1:0);
    if(partial){
      const retained=plan.residualData.features[0].geometry;
      for(const p of retainedProbes)assert.equal(candidateGeometryContains(retained,point(...p.xy)),true,p.name);
      const cutProbe=spec.residualCutProbe===undefined?[0,0]:spec.residualCutProbe;
      if(spec.residualCutProbe!==undefined){
        assert.ok(Array.isArray(cutProbe)&&cutProbe.length===2&&cutProbe.every(Number.isFinite),'Expected finite residualCutProbe in local metres');
        const removedPoint=point(...cutProbe);
        assert.ok(candidateGeometryContains(geometry,removedPoint),'Removed probe outside original owner');
        assert.ok(candidateGeometryContains(clip.geometry,removedPoint),'Removed probe outside replacement cut');
      }
      assert.equal(candidateGeometryContains(retained,point(...cutProbe)),false,'Removed probe still inside residual');
    }
    assert.equal(plan.desired.size,targets.has(owner.local_id)?1:0);
    vector.push({source,owner:owner.local_id,hidden:plan.desired.size===1,residuals:plan.residualData.features.length});
  }
}
const points=spec.ground.map(p=>[p.name,point(...p.xy),p.modelObstacle??(p.expected==='building'),p.cut??(p.expected==='building')]);
for(const [key,value]of Object.entries(spec.neighborGround))points.push(['neighbor '+key,value,false,false]);
const ground=points.map(([name,position,expected,expectedCut])=>{
  const candidate=candidateGeometryContains(contract.collision_geometry,position),cut=candidateGeometryContains(contract.replacement_geometry,position);
  assert.equal(candidate,expected,name);assert.equal(cut,expectedCut,name);return {name,position,candidate,cut};
});
const report={id:contract.id,caseSha256:hash(fs.readFileSync(caseFile)),catalogRows:catalog.resulting_city_count,before,after,vector,ground,
  sha256:{catalog:hash(fs.readFileSync(local('data/candidate-city-integrations.json'))),clipper:hash(fs.readFileSync(local('src/candidate-city-clipping.js'))),checker:hash(fs.readFileSync(fileURLToPath(import.meta.url)))}};
const out=process.env.QA_OUTPUT_DIR||audit;fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'runtime-placement.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({triangles:after.triangles,macroTextures:after.macroTextures,largest:after.largestShaderTable}));
