/** Count the original-world draw group's actual triangulated masks with production map coordinates. */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath, pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';

const audit=path.dirname(fileURLToPath(import.meta.url));
const project=process.env.SHANGHAI_PROJECT_ROOT||path.resolve(audit,'../../..');
const [catalogPath,contractPath,footprintPath,output]=process.argv.slice(2);
const read=p=>JSON.parse(fs.readFileSync(p));
const sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const city=read(catalogPath),contract=read(contractPath),source=read(footprintPath);
assert(!city.models.some(r=>r.id===contract.id));assert.equal(contract.owner.feature_local_id,2100);
const THREE=await import(pathToFileURL(path.join(project,'vendor/three.module.js')));
const {CandidateCityClipper}=await import(pathToFileURL(path.join(project,'src/candidate-city-clipping.js')));
const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};
context.exports=context.module.exports;context.self=context;context.globalThis=context;
vm.runInNewContext(fs.readFileSync(path.join(project,'vendor/maplibre-gl.js'),'utf8'),context);
const map=fs.readFileSync(path.join(project,'src/map-scene.js'),'utf8');
const origin=map.match(/^const ORIGIN = (\[[^\]]+\]);/m);
assert(origin);
const coords=map.slice(map.indexOf('  const mercatorOrigin ='),map.indexOf('  const scene = new THREE.Scene();'));
const geographicPosition=new Function('THREE','maplibregl','ORIGIN',coords+'\nreturn geographicPosition;')(THREE,context.module.exports,JSON.parse(origin[1]));
const clipper=new CandidateCityClipper({THREE,geographicPosition});
const group=new Set(source.near_tiles[0].feature_local_ids);
function count(models){
  const masks=models.filter(r=>r.replacement_geometry).map(r=>({geometry:r.replacement_geometry,owner:r.owner,owners:r.owners}));
  clipper.update(masks);
  // A local ID can recur in another macro; measure the signed macro numerically as well.
  const macroHash=[...source.frozen_macro].reduce((v,c)=>Math.imul(v^c.charCodeAt(0),16777619),2166136261)>>>0;
  return clipper.triangleOwners.filter(r=>group.has(r.localId) && r.macro===macroHash%16777215).length;
}
const previous=count(city.models),after=count([...city.models,contract]),solo=count([contract]);
assert(solo>0);assert.equal(after-previous,solo);
fs.writeFileSync(output,JSON.stringify({id:contract.id,passed:true,macro:source.frozen_macro,group_ids:[...group],previous_group_triangles:previous,added_triangles:solo,current_group_triangles:after,contract_sha256:sha(contractPath),catalog_sha256:sha(catalogPath),map_scene_sha256:sha(path.join(project,'src/map-scene.js')),clipper_sha256:sha(path.join(project,'src/candidate-city-clipping.js'))},null,2)+'\n');
