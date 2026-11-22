/** Check the actual clipping texture at the retained northern base. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const audit = path.dirname(fileURLToPath(import.meta.url));
const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(audit, '../../..');
const THREE = await import(pathToFileURL(path.join(project, 'vendor/three.module.js')));
const renderer = path.join(project, 'src/candidate-city-clipping.js');
const {CandidateCityClipper} = await import(pathToFileURL(renderer));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const contractBytes = fs.readFileSync(path.join(audit, 'final-placement-contract.json'));
const contract = JSON.parse(contractBytes);
const catalogFile = process.env.CANDIDATE_CITY_CATALOG;
const catalog = catalogFile ? JSON.parse(fs.readFileSync(catalogFile)) : {models:[contract]};
const matched = catalog.models.find(row => row.id === contract.id);
assert.deepEqual(matched.display_height_clips, contract.display_height_clips);
assert.deepEqual(matched.replacement_geometry, contract.replacement_geometry);
const clip = contract.display_height_clips[0];
const {lng, lat, heading} = contract;
const rad = Math.PI/180;
const earth = 6371008.8;
const scale = earth*Math.cos(lat*rad);
const mercator = latitude => Math.asinh(Math.tan(latitude*rad));
function world(longitude, latitude, elevation=0) {
  return new THREE.Vector3((longitude-lng)*rad*scale, elevation*scale/(earth*Math.cos(latitude*rad)), (mercator(lat)-mercator(latitude))*scale);
}
function horizontally(x, y) {
  const t = heading*rad;
  const east=x*Math.cos(t)+y*Math.sin(t), north=-x*Math.sin(t)+y*Math.cos(t);
  return [lng+east/(scale*rad), Math.atan(Math.sinh(mercator(lat)+north/scale))/rad];
}
const clipper = new CandidateCityClipper({THREE, geographicPosition:world});
const primary = catalog.models.filter(m => m.replacement_geometry).map(m => ({owner:m.owner,owners:m.owners,geometry:m.replacement_geometry}));
clipper.update([...primary, ...catalog.models.flatMap(m => m.site_replacement?[m.site_replacement]:[]), ...catalog.models.flatMap(m => m.display_height_clips || [])]);
// Resolve the native macro identity with the renderer itself. A local owner number
// can repeat in another macro in the complete city.
const reference = new CandidateCityClipper({THREE, geographicPosition:world});
reference.update([clip]);
assert.equal(reference.triangleOwners.length,2);
const targetMacro=reference.triangleOwners[0].macro;
assert.ok(reference.triangleOwners.every(row=>row.localId===460 && row.macro===targetMacro));
const table=clipper.tableFor(targetMacro);
reference.dispose();
const records=[];
for(let i=0;i<table.triangles;i++){
  const row=Array.from(table.data.subarray(16*i,16*i+16));
  if(row[12]===460 && row[13]===targetMacro) records.push(row);
}
assert.equal(records.length,4);
const threshold=world(...clip.height_reference,8.3).y;
assert.equal(records.filter(r=>Math.abs(r[6]-threshold)<1e-5).length,2);
function removed(x, y, height, owner=460) {
  const w = world(...horizontally(x,y));
  w.y=world(...clip.height_reference,height).y;
  const side=(ax,ay,bx,by)=>(bx-ax)*(w.z-ay)-(by-ay)*(w.x-ax);
  return records.some(([ax,ay,bx,by,cx,cy,bottom,top,minX,minZ,maxX,maxZ,id])=>{
    if(id!==owner || w.y<bottom || w.y>top || w.x<minX || w.x>maxX || w.z<minZ || w.z>maxZ) return false;
    const sides=[side(ax,ay,bx,by),side(bx,by,cx,cy),side(cx,cy,ax,ay)];
    return sides.every(v=>v>=-.001) || sides.every(v=>v<=.001);
  });
}
const samples=[];
for(const [label,x,y,height,expected] of [
  ['north pavement',-17,.65,.04,false],['north wall head below joint',-17,.65,8.29,false],
  ['north wall head above joint',-17,.65,8.31,true],['north original roof',-17,3.2,25.6,true],
  ['north original rear',-17,6.15,22,false],['southern replacement base',3.5,1.2,.1,true],
  ['southern replacement roof',3.5,1.2,25.6,true],['southern original rear',3.5,6.15,25.6,false],
  ['street ahead of north end',-17,-2,11,false],['air above source range',-17,.65,41,false]
]) {
  const targetRemoved=removed(x,y,height);
  assert.equal(targetRemoved,expected,label);
  const negativeOwnerRemoved=removed(x,y,height,623);
  assert.equal(negativeOwnerRemoved,false);
  samples.push({label,local_xy:[x,y],source_elevation_m:height,owner_460_removed:targetRemoved,owner_623_removed:negativeOwnerRemoved});
}
const result={model:contract.id,passed:true,scope:catalogFile?'signed-city-texture':'contract-only-texture',catalog_sha256:catalogFile?sha(fs.readFileSync(catalogFile)):null,contract_sha256:sha(contractBytes),renderer_sha256:sha(fs.readFileSync(renderer)),total_texture_rows:clipper.triangleCount,rows_for_460:records,samples};
fs.writeFileSync(process.argv[2],JSON.stringify(result,null,2)+'\n');
clipper.dispose();
