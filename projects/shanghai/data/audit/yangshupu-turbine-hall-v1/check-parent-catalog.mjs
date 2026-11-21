import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const [project,predecessor,output]=process.argv.slice(2);
const filename='data/candidate-city-integrations.json';
const catalog=fs.readFileSync(path.join(predecessor,filename));
const rows=JSON.parse(catalog).models.filter(r=>r.kind==='historical-site');
async function load(root,file){return import(pathToFileURL(path.join(root,'src',file)));}
async function summarize(root){
  const {validHistoricalSite,historicalSiteCaption}=await load(root,'historical-view.js');
  const {placeDescription,walkingPose}=await load(root,'precise-registration-ui.js');
  const {mergeCandidateCityModels}=await load(root,'candidate-city-integrations.js');
  return rows.map(row=>{
    assert.ok(validHistoricalSite(row),row.id);
    const [place]=mergeCandidateCityModels([],{schema:'candidate-city-integrations-v1',models:[row]});
    assert.equal(walkingPose(place),null);
    assert.equal(place.model,undefined);
    return {id:row.id,name:row.name,page:row.individual_page,period:row.historical_view,
      marker_caption:historicalSiteCaption(row.historical_view),drawer_description:placeDescription(place)};
  });
}
const original=await summarize(predecessor),updated=await summarize(project);
assert.ok(original.some(r=>r.period.evidence_kind==='published-drawing'));
assert.ok(original.some(r=>r.period.evidence_kind==='reprinted-photograph'));
assert.ok(original.some(r=>r.period.building_year));
assert.deepEqual(original,updated);
fs.writeFileSync(output,JSON.stringify({all_prior_markers_unchanged:true,previous_catalog_sha256:createHash('sha256').update(catalog).digest('hex'),preserved_records:original},null,2)+'\n');
console.log(original.length,'historical sites and their original captions verified unchanged');
