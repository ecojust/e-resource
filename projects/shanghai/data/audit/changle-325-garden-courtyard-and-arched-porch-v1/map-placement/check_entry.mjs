import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const [repo,modelDir,projectSite,out]=process.argv.slice(2);
const api=await import(pathToFileURL(path.join(repo,'src/candidate-city-integrations.js')));
const read=p=>JSON.parse(fs.readFileSync(p));
const town=read(path.join(repo,'data/candidate-city-integrations.json')),row=read(path.join(modelDir,'proof/candidate-row.json'));
const baseline=town.models.map(m=>m.id);const entryIndex=town.models.findIndex(m=>m.id===row.id);
if(entryIndex!==-1)throw Error('A pre-existing town entry requires explicit revision');
const result=api.mergeCandidateCityModels([],{...town,models:[...town.models,row]});
const records=result.filter(m=>m.id===row.id);
if(records.length!==1||result.length!==baseline.length+1||!baseline.every((k,i)=>result[i].id===k))throw Error('Existing city rows changed');
if(!api.validCandidateGeometry(row.collision_geometry,{collision:true}))throw Error('Invalid garden collision');
const assets={};for(const name of ['web','lod']) {
 const r=row.assets[name];const b=fs.readFileSync(path.join(modelDir,'assets',path.basename(r.file)));
 const hash=createHash('sha256').update(b).digest('hex');if(hash!==r.sha256||b.length!==r.bytes)throw Error('Asset integrity mismatch');
 assets[name]={path:r.file,sha256:hash,triangles:r.triangles,bytes:b.length}
}
const linked=fs.readFileSync(path.join(projectSite,row.individual_page),'utf8');
if(!linked.includes(row.id))throw Error('Individual link does not open this garden');
const report={baseline_city_rows:baseline.length,total_city_rows_in_prototype:result.length,same_existing_order:true,ordinary_entry_count:records.length,individual_page:row.individual_page,page_sha256:createHash('sha256').update(linked).digest('hex'),map_assets:assets,source_owners_removed:row.source_feature_ids,source_replacement_geometry:row.replacement_geometry,collision_shape_valid:true,merge_module_sha256:createHash('sha256').update(fs.readFileSync(path.join(repo,'src/candidate-city-integrations.js'))).digest('hex')};
fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report).slice(0,175));
