import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const work=path.dirname(fileURLToPath(import.meta.url));
const [contractFile,base,output,signature]=process.argv.slice(2);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=name=>JSON.parse(name.endsWith('.geojson')?gunzipSync(fs.readFileSync(path.join(work,name+'.gz'))):fs.readFileSync(path.join(work,name)));
const evidence=read('initial-correspondence.json');
const approved=JSON.parse(fs.readFileSync(contractFile));
assert.equal(approved.id,'huangpu-nanshi-telephone-exchange');
const project='/workspace/e-resource/projects/shanghai';
const inputs={};
async function verified(name) {
 const url=new URL(name,base).href;
 const response=await fetch(url);assert.equal(response.status,200);
 const bytes=Buffer.from(await response.arrayBuffer());
 inputs[name]={url,sha256:sha(bytes),bytes:bytes.length};
 return bytes;
}
const catalogName='data/candidate-city-integrations.json';
const catalog=JSON.parse(await verified(catalogName));
assert.equal(signature,inputs[catalogName].sha256);
assert(!catalog.models.some(r=>r.id===approved.id));
for(const name of ['src/candidate-vector-clipping.js','src/candidate-vector-geometry.js','vendor/polygon-clipping.umd.min.js']){
 const real=await verified(name);assert.equal(sha(real),sha(fs.readFileSync(path.join(project,name))),name);
}
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
for(const [source,file,targetID]of [['openmaptiles','openmaptiles-matched.geojson',4943897300],['overture-buildings','overture-owners.geojson','9d26169a-5e70-47aa-9929-9c61c14ffd68']]){
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
 const oldArea=area(from),newArea=area(to),delta=oldArea-newArea;
 assert(delta>0&&newArea>0); assert(area(poly.xor(to,poly.difference(from,region)))<.0001);
 const parts=polys(target.geometry).map((p,i)=>{const old=area(poly.intersection(from,[p])),next=area(poly.intersection(to,[p]));return {part:i,before_m2:old,after_m2:next,change_m2:old-next};});
 const changed=parts.filter(p=>Math.abs(p.change_m2)>.0001);assert.equal(changed.length,1);if(source==='openmaptiles'){assert.equal(parts.length,14);assert.equal(changed[0].part,13);}
 for(const other of entries.filter(v=>v.id!==targetID))assert.deepEqual(effective(other,before),effective(other,after));
 records.push({source,targetID,parts:parts.length,changed_part:changed[0],other_parts_unchanged:parts.length-1,other_features_unchanged:entries.filter(x=>x.id!==targetID).map(x=>x.id),before_m2:oldArea,after_m2:newArea,removed_m2:delta,all_parts:parts});
}
fs.writeFileSync(output,JSON.stringify({passed:true,contract_sha256:sha(fs.readFileSync(contractFile)),original_sources:evidence,prior_city_count:catalog.resulting_city_count,actual_runtime_inputs:inputs,records},null,2)+'\n');
console.log(records.map(r=>[r.source,r.removed_m2,r.changed_part]));
