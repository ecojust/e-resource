import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const work=path.dirname(path.resolve(process.argv[1]));
const [contractFile,catalogFile,output,project]=process.argv.slice(2);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=name=>{const raw=fs.readFileSync(path.join(work,name));return JSON.parse(name.endsWith('.gz')?gunzipSync(raw):raw);};
const evidence=read('target-and-neighbors.json');
const approved=JSON.parse(fs.readFileSync(contractFile));
assert.equal(approved.id,'jingan-gordon-road-station-south-front');
const signed=read('signed-inputs.json');
const bytes=gunzipSync(fs.readFileSync(catalogFile));
assert.equal(sha(bytes),signed.orders['313'].catalog_sha256);
const catalog=JSON.parse(bytes);
assert(!catalog.models.some(r=>r.id===approved.id));
for(const name of ['src/candidate-vector-clipping.js','src/candidate-vector-geometry.js','vendor/polygon-clipping.umd.min.js']){
 assert.equal(sha(fs.readFileSync(path.join(project,name))),signed.renderer_modules[name].sha256);
}
await import(pathToFileURL(path.join(project,'vendor/polygon-clipping.umd.min.js')));
const {planCandidateVectorClipping}=await import(pathToFileURL(path.join(project,'src/candidate-vector-clipping.js')));
const poly=globalThis.polygonClipping;
const polys=g=>g.type==='Polygon'?[g.coordinates]:g.type==='MultiPolygon'?g.coordinates:[];
const area=parts=>parts.reduce((sum,rings)=>sum+rings.reduce((s,ring,i)=>{let a=0;
 for(let j=1;j<ring.length;j++)a+=(ring[j-1][0]-ring[0][0])*(ring[j][1]-ring[0][1])-(ring[j][0]-ring[0][0])*(ring[j-1][1]-ring[0][1]);
 return s+(i?-1:1)*Math.abs(a)/2;
},0),0)*((Math.PI/180)*6371008.8)**2*Math.cos(approved.lat*Math.PI/180);
const makeRule=row=>({...row,geometry:row.replacement_geometry});
const prior=catalog.models.filter(r=>r.replacement_geometry).map(makeRule);
const records=[];
const originalOwners=new Map(evidence.near_group_matches.map(row=>[row.local_owner,row]));
assert(evidence.groups[0].featureLocalIds.every(id=>originalOwners.has(id)));
assert.deepEqual(approved.owner,{macro_id:evidence.macro,feature_local_id:1295});
const east=originalOwners.get(1295);
const independent=[451,2722,2862].map(id=>originalOwners.get(id));
const phaseEvidence=[];

for(const [source,file,targetID]of [['openmaptiles','affected-fallback.geojson.gz',east.match.feature_id],['overture-buildings','overture-group.geojson.gz',east.overture_key.slice(9)]]){
 const entries=read(file).features;
 const run=rules=>planCandidateVectorClipping(entries,{candidateClips:rules},{source,sourceLayer:'building'});
 const before=run(prior),after=run([...prior,makeRule(approved)]),solo=run([makeRule(approved)]);
 for(const run of [before,after,solo])assert.equal(run.stats.clippingErrors,0);
 assert.deepEqual([...solo.desired.values()].map(x=>x.id),[targetID]);
 const effective=(row,result)=>{
  const k=typeof row.id+':'+row.id;
  if(!result.desired.has(k))return polys(row.geometry);
  return polys(result.residualData.features.find(x=>x.id==='candidate-residual:building:'+encodeURIComponent(k))?.geometry??{type:'MultiPolygon',coordinates:[]});
 };
 const target=entries.find(x=>x.id===targetID),from=effective(target,before),to=effective(target,after);
 const region=polys(source==='openmaptiles'?approved.osm_replacement_geometry??approved.replacement_geometry:approved.replacement_geometry);
 // Original aggregated buildings can overlap. Measure the occupied union in both states.
 const oldArea=area(poly.union(from)),newArea=area(poly.union(to)),delta=area(poly.difference(from,to));
 assert(Math.abs(oldArea-newArea-delta)<.0001);
 assert(area(poly.difference(to,from))<.0001);
 assert(delta>0&&newArea>0); assert(area(poly.xor(to,poly.difference(from,region)))<.0001);
 const envelope=p=>p.flat().reduce((a,q)=>[Math.min(a[0],q[0]),Math.min(a[1],q[1]),Math.max(a[2],q[0]),Math.max(a[3],q[1])],[Infinity,Infinity,-Infinity,-Infinity]);
 const overlaps=(a,b)=>a[0]<=b[2]&&b[0]<=a[2]&&a[1]<=b[3]&&b[1]<=a[3];
 const oldIndex=from.map(p=>[envelope(p),p]),newIndex=to.map(p=>[envelope(p),p]);
 const localIntersection=(p,index)=>{
   const box=envelope(p),local=index.filter(([b])=>overlaps(box,b)).map(([,q])=>q);
   return local.length ? area(poly.intersection(local,[p])) : 0;
 };
 const parts=polys(target.geometry).map((p,i)=>{
   const old=localIntersection(p,oldIndex),next=localIntersection(p,newIndex);
   return {part:i,before_m2:old,after_m2:next,change_m2:old-next};
 });
 const changed=parts.filter(p=>Math.abs(p.change_m2)>.0001);assert.equal(changed.length,1);assert(Math.abs(delta-changed[0].change_m2)<.0001);if(source==='openmaptiles'){assert.equal(parts.length,east.match.component_count);assert.equal(changed[0].part,east.match.component);}
 const unchangedOthers=[];
 for(const other of entries.filter(v=>v.id!==targetID)){
   const oldShape=effective(other,before),newShape=effective(other,after);
   const sameCoordinates=JSON.stringify(oldShape)===JSON.stringify(newShape);
   const changedArea=sameCoordinates?0:area(poly.xor(oldShape,newShape));
   assert(changedArea<.0001,'Neighbor '+other.id+' changed '+changedArea+' square meters');
   unchangedOthers.push({id:other.id,original_part_count:polys(other.geometry).length,identical_coordinates:sameCoordinates,symmetric_difference_m2:changedArea,area_before_m2:area(oldShape),area_after_m2:area(newShape)});
 }
 // The three independently identified neighboring buildings have distinct geometry. Preserve each detected component.
 for(const owner of independent){
   if(source==='openmaptiles'&&!owner.match)continue;
   if(source==='openmaptiles'&&owner.match.feature_id===targetID){
     const component=polys(target.geometry)[owner.match.component];
     const oldShape=poly.intersection(from,[component]);
     const newShape=poly.intersection(to,[component]);
     assert(oldShape.length>0&&newShape.length>0);
     assert(area(poly.xor(oldShape,newShape))<.0001);
   }else{
     const id=source==='openmaptiles'?owner.match.feature_id:owner.overture_key.slice(9);
     assert(unchangedOthers.some(x=>x.id===id&&x.symmetric_difference_m2===0));
   }
 }
 const phases=[];
 for(const [step,active] of [['before',false],['full',true],['hidden',false],['restored',true],['distant',true],['unloaded',false]]){
   const now=run(active?[...prior,makeRule(approved)]:prior), expected=active?after:before;
   for(const feat of entries)assert.deepEqual(effective(feat,now),effective(feat,expected),step);
   phases.push({step,active,effective_feature_count:entries.length});
 }
 phaseEvidence.push({source,phases});
 records.push({source,targetID,parts:parts.length,changed_part:changed[0],other_parts_unchanged:parts.length-1,other_features_unchanged:unchangedOthers,before_m2:oldArea,after_m2:newArea,removed_m2:delta,all_parts:parts});
}
fs.writeFileSync(output,JSON.stringify({passed:true,contract_sha256:sha(fs.readFileSync(contractFile)),prior_city_count:catalog.resulting_city_count,records,visibility_plans:phaseEvidence},null,2)+'\n');
