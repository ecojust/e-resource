/** Verify by clipping the actual aggregated OSM vector feature, the separately keyed
 * Overture polygons, and binding the actual city clipper to both near ownership groups. */
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';

const audit=path.dirname(fileURLToPath(import.meta.url)),project=path.resolve(audit,'../../..');
const runtime=process.argv[3]||project;
const read=p=>JSON.parse(fs.readFileSync(p));
const sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const moduleAt=(p)=>import(pathToFileURL(path.join(runtime,p)));
const {planCandidateVectorClipping}=await moduleAt('src/candidate-vector-clipping.js');
const {candidateGeometryContains,CandidateCityState}=await moduleAt('src/candidate-city-integrations.js');
const {CandidateCityClipper}=await moduleAt('src/candidate-city-clipping.js');
const THREE=await moduleAt('vendor/three.module.js');
const manifest=read(path.join(audit,'final-placement-contract.json'));
const source=read(path.join(project,'source/precise',manifest.id,'footprint-review.json'));
const actual=read(process.argv[2]);
assert.equal(actual.tile_sha256,source.fallback_vector.sha256);
const pc=globalThis.polygonClipping;
const polys=g=>g.type==='Polygon'?[g.coordinates]:g.coordinates;
const radians=Math.PI/180,k=6371008.8*Math.cos(manifest.lat*radians);
const log=lat=>Math.asinh(Math.tan(lat*radians));
const local=(lon,lat)=>[(lon-manifest.lng)*radians*k,(log(lat)-log(manifest.lat))*k];
function area(polygons){
  return polygons.reduce((s,poly)=>s+poly.reduce((a,r,i)=>{
    const points=r.map(p=>local(...p));
    return a+(i?-1:1)*Math.abs(points.slice(1).reduce((sum,[x,y],j)=>sum+points[j][0]*y-x*points[j][1],0))*.5;
  },0),0);
}
const full=manifest.replacement_geometry, osm=manifest.osm_replacement_geometry;
assert.ok(osm);
const clip={id:manifest.id,geometry:full,osm_replacement_geometry:osm,owner:manifest.owner,source_feature_ids:manifest.source_feature_ids};
const merged=actual.features[0],neighbor=source.adjacent_near_group.geometry;
const primary={type:'Feature',id:manifest.source_feature_ids.building[0],properties:{},geometry:source.source_outline};
const neighborId=source.adjacent_near_group.key.slice('building:'.length);
const nearFeature={type:'Feature',id:neighborId,properties:{},geometry:neighbor};
const vector=(features,from,rule)=>planCandidateVectorClipping(features,{candidateClips:[rule]},{source:from,sourceLayer:'building'});
const overture=vector([primary,nearFeature],'overture-buildings',clip);
assert.equal(overture.stats.clippingErrors,0);assert.equal(overture.desired.size,1);
assert.deepEqual([...overture.desired.values()],[{id:primary.id,residual:false}]);
const report={};
for(const [name,rule] of [['original',({...clip,osm_replacement_geometry:undefined})],['scoped',clip]]){
  const plan=vector([merged],'openmaptiles',rule);
  assert.equal(plan.stats.clippingErrors,0);assert.equal(plan.residualData.features.length,1);
  const before=pc.intersection(polys(merged.geometry),polys(neighbor));
  const after=pc.intersection(polys(plan.residualData.features[0].geometry),polys(neighbor));
  report[name]={source_feature_id:merged.id,before_m2:area(before),after_m2:area(after),lost_m2:area(before)-area(after),stats:plan.stats};
}
assert.ok(report.original.lost_m2>1);assert.ok(Math.abs(report.scoped.lost_m2)<.001);
const projected=(lon,lat,height=0)=>{const [e,n]=local(lon,lat);return new THREE.Vector3(e,height,-n);};
const clipper=new CandidateCityClipper({THREE,geographicPosition:projected});
clipper.update([clip]);
const ownerScope={};
for(const [name,group] of [['theatre',source.near],['adjacent',source.adjacent_near_group]]){
  const object=new THREE.Group();object.add(new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial()));
  clipper.bindObject(object,{id:name,parent:{id:manifest.owner.macro_id},ids:group.local_ids});
  const n=clipper.objects.get(object).scope.triangles;
  assert.equal(name==='theatre',n>0);
  ownerScope[name]={triangles:n,ids:group.local_ids};
  clipper.releaseObject(object);
}
const tri=clipper.getState().triangles;clipper.dispose();
const state=new CandidateCityState({getRecords:()=>new Map(),getScene:()=>null});state.clips=[clip];
const disputed=pc.intersection(polys(full),polys(neighbor));
const ring=disputed[0][0].slice(0,-1);
const point=ring.reduce((sum,[lon,lat])=>[sum[0]+lon/ring.length,sum[1]+lat/ring.length],[0,0]);
assert.ok(candidateGeometryContains(full,point));assert.ok(candidateGeometryContains(neighbor,point));assert.ok(!candidateGeometryContains(osm,point));
assert.equal(state.clipsPoint(...point,{name:'openmaptiles',id:merged.id,layer:'building'}),false);
assert.equal(state.clipsPoint(...point,{name:'overture-buildings',id:primary.id,layer:'building'}),true);
assert.equal(state.clipsPoint(...point,{name:'overture-buildings',id:neighborId,layer:'building'}),false);
const modules=['src/candidate-vector-geometry.js','src/candidate-vector-clipping.js','src/candidate-city-integrations.js','src/candidate-city-clipping.js'];
const result={model:manifest.id,contract_sha256:sha(path.join(audit,'final-placement-contract.json')),source_sha256:sha(path.join(project,'source/precise',manifest.id,'footprint-review.json')),
  tile_sha256:actual.tile_sha256,geojson_sha256:sha(process.argv[2]),script_sha256:sha(fileURLToPath(import.meta.url)),runtime_sha256:Object.fromEntries(modules.map(f=>[f,sha(path.join(runtime,f))])),
  vector:report,overture:overture.stats,shared_party_wall_probe:point,city_owner_scopes:ownerScope,active_shader_triangles:tri};
fs.writeFileSync(process.argv[4]||path.join(audit,'vector-source-checks.json'),JSON.stringify(result,null,2)+'\n');
console.log(report,ownerScope);
