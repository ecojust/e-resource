/** Measure only the replaced corner inside the original 50-part fallback feature. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const audit=path.dirname(fileURLToPath(import.meta.url)),project=path.resolve(audit,'../../..');
const root=process.env.SHANGHAI_PROJECT_ROOT || project;
const read=f=>JSON.parse(fs.readFileSync(f));
const sha=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const file=process.env.MODEL_VERIFIED_CONTRACT || path.join(audit,'final-placement-contract.json');
const current=read(file),source=read(path.join(project,'source/precise',current.id,'footprint-review.json'));
const vector=read(process.argv[2]);
assert.equal(vector.sha256,source.fallback.tile_sha256);
const entries=vector.features, target=entries.find(f=>f.id===1657917650);
assert.equal(target.properties.render_height,4);
const {planCandidateVectorClipping}=await import(pathToFileURL(path.join(root,'src/candidate-vector-clipping.js')));
const clip=globalThis.polygonClipping;
const polygons=g=>g.type==='Polygon'?[g.coordinates]:g.coordinates;
const rad=Math.PI/180,k=6371008.8*Math.cos(current.lat*rad),yOrigin=Math.asinh(Math.tan(current.lat*rad));
const xy=([lon,lat])=>[(lon-current.lng)*rad*k,(Math.asinh(Math.tan(lat*rad))-yOrigin)*k];
function area(parts){
  return parts.reduce((sum,poly)=>sum+poly.reduce((a,r,j)=>{
    const pts=r.map(xy),v=pts.slice(1).reduce((n,[x,y],i)=>n+pts[i][0]*y-pts[i][1]*x,0);
    return a+(j?-1:1)*Math.abs(v)*.5;
  },0),0);
}
const rule=c=>({id:c.id,geometry:c.replacement_geometry,owner:c.owner,owners:c.owners,
    source_feature_ids:c.source_feature_ids,osm_replacement_geometry:c.osm_replacement_geometry});
const inputCatalog=read(process.argv[4]);
assert(!inputCatalog.models.some(r=>r.id===current.id));
const previous=inputCatalog.models.filter(r=>r.replacement_geometry).map(rule);
const plan=rules=>planCandidateVectorClipping(entries,{candidateClips:rules},{source:'openmaptiles',sourceLayer:'building'});
const before=plan(previous),after=plan([...previous,rule(current)]),solo=plan([rule(current)]);
assert.equal(before.stats.clippingErrors,0);assert.equal(after.stats.clippingErrors,0);assert.equal(solo.stats.clippingErrors,0);
function geometry(feature,plan){
  const key=typeof feature.id+':'+feature.id;
  if(!plan.desired.has(key))return feature.geometry;
  const id='candidate-residual:building:'+encodeURIComponent(key);
  return plan.residualData.features.find(f=>f.id===id)?.geometry || {type:'MultiPolygon',coordinates:[]};
}
const region=polygons(current.replacement_geometry);
const overlap=(g,r)=>area(clip.intersection(polygons(g),r));
const beforeTarget=geometry(target,before),afterTarget=geometry(target,after),soloTarget=geometry(target,solo);
assert.equal(polygons(target.geometry).length,50);
const normalizedComponents=polygons(soloTarget).length;
assert(normalizedComponents>0 && normalizedComponents<=50);
const delta=overlap(beforeTarget,region);
assert(delta>28 && delta<36);
assert(overlap(afterTarget,region)<.00001);
const expected=clip.difference(polygons(beforeTarget),region);
assert(area(clip.xor(polygons(afterTarget),expected))<.00002);
for(const other of entries.filter(f=>f.id!==target.id))assert.deepEqual(geometry(other,before),geometry(other,after));
const otherOwners=source.owners.map(o=>{
  const lot=polygons(o.geometry_wgs84);
  const a=entries.reduce((s,f)=>s+overlap(geometry(f,before),lot),0);
  const b=entries.reduce((s,f)=>s+overlap(geometry(f,after),lot),0);
  if(o.local_id===1173){assert(a>580 && b>550 && a-b>28 && a-b<36);}
  else {assert(Math.abs(a-b)<.00001);}
  return {owner:o.local_id,before_m2:a,after_m2:b};
});
const originals=polygons(target.geometry);
const bounds=ring=>ring.reduce(([minX,minY,maxX,maxY],[x,y])=>[
 Math.min(minX,x),Math.min(minY,y),Math.max(maxX,x),Math.max(maxY,y)],
 [Infinity,Infinity,-Infinity,-Infinity]);
const [west,south,east,north]=bounds(region[0][0]);
const partAreas=[];
for (const [index,part] of originals.entries()){
 const box=bounds(part[0]);
 if(box[0]>east||box[2]<west||box[1]>north||box[3]<south)continue;
 const before=overlap(beforeTarget,[part]),after=overlap(afterTarget,[part]);
 partAreas.push({component:index,before_m2:before,after_m2:after,change_m2:before-after});
}
assert.equal(partAreas.filter(r=>Math.abs(r.change_m2)>.00002).length,1);
const result={id:current.id,passed:true,input_catalog_sha256:sha(process.argv[4]),city_count:inputCatalog.resulting_city_count,
 tile_sha256:vector.sha256,contract_sha256:sha(file),module_sha256:sha(path.join(root,'src/candidate-vector-clipping.js')),
 source_id:target.id,original_parts:originals.length,other_components_unchanged:originals.length-partAreas.filter(r=>Math.abs(r.change_m2)>.00002).length,normalized_components:normalizedComponents,part_areas:partAreas,
 cut_m2:delta,other_aggregate_ids_equal:entries.filter(f=>f.id!==target.id).map(f=>f.id),owner_areas:otherOwners};
fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2)+'\n');
