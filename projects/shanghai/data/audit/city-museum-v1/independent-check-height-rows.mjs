// Independent replay of the exact pre-height clipper/catalogue metadata only.
// No original or authored model asset is decoded.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';
const [project,snapshot,payload,out]=process.argv.slice(2);assert(project&&snapshot&&payload&&out);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const bind=p=>{p=p instanceof URL?fileURLToPath(p):p;const b=fs.readFileSync(p);return {file:p,bytes:b.length,sha256:sha(b)}};
const read=p=>fs.readFileSync(p,'utf8');
const THREE=await import(pathToFileURL(project+'/vendor/three.module.js'));
const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};context.exports=context.module.exports;context.self=context;context.globalThis=context;
vm.runInNewContext(read(project+'/vendor/maplibre-gl.js'),context);
const before=snapshot+'/projects/shanghai/';
const source=read(before+'src/map-scene.js');
const block=source.slice(source.indexOf('  const mercatorOrigin ='),source.indexOf('  const scene = new THREE.Scene();'));
assert(block.includes('function geographicPosition'));
const geographicPosition=new Function('THREE','maplibregl',`const ORIGIN=[121.4737,31.2304];${block};return geographicPosition;`)(THREE,context.module.exports);
const {CandidateCityClipper}=await import('data:text/javascript;base64,'+Buffer.from(read(before+'src/candidate-city-clipping.js')).toString('base64'));
const catalog=JSON.parse(read(before+'data/candidate-city-integrations.json'));
assert.equal(catalog.models.length,41);assert(catalog.models.every(r=>!r.display_height_clips));
const clips=new Map();
for(const r of catalog.models){
 if(r.replacement_geometry)clips.set(r.id,{id:r.id,geometry:r.replacement_geometry,owner:r.owner,owners:r.owners,source_feature_ids:r.source_feature_ids||{}});
 if(r.site_replacement)clips.set(r.site_replacement.id,{...r.site_replacement,source_feature_ids:r.site_replacement.source_feature_ids||{}});
}
const old=new CandidateCityClipper({THREE,geographicPosition});old.update([...clips.values()]);assert.equal(old.triangleCount,258);
const actual=fs.readFileSync(payload);assert.equal(actual.length,262*16*4);
const regenerated=Buffer.from(old.data.buffer,0,258*16*4);assert(regenerated.equals(actual.subarray(0,258*16*4)));
const baselineDigest='f2400a2fbfec5d114227c0a7e6bab4afdeef3a9cfde09015a401b5383e805dcb';
assert.equal(sha(actual.subarray(0,218*16*4)),baselineDigest);
const earlier=JSON.parse(read(project+'/data/audit/city-museum-v1/clipping-budget-preflight.json'));
assert.equal(earlier.baseline,'93e3cb2d0ddeba1a7db7d435bf66c2f61492326e');assert.equal(earlier.historical_payload.old_sha256,baselineDigest);assert(earlier.historical_payload.identical);
const result={schema:'city-museum-independent-height-row-preservation-v1',passed:true,scope:'Re-execute exact frozen pre-height clipper and41-record catalogue using shipped Three/MapLibre metadata mathematics; no model GLB assets, native tools or browser.',old218_rows_identical:true,old218_bytes:218*64,old218_sha256:baselineDigest,all258_pre_height_rows_identical:true,all258_bytes:258*64,all258_sha256:sha(regenerated),new262_payload:bind(payload),bindings:[bind(before+'src/candidate-city-clipping.js'),bind(before+'src/map-scene.js'),bind(before+'data/candidate-city-integrations.json'),bind(project+'/vendor/three.module.js'),bind(project+'/vendor/maplibre-gl.js'),bind(project+'/data/audit/city-museum-v1/clipping-budget-preflight.json')],script:bind(new URL(import.meta.url))};
old.dispose();fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:true,old218:true,all258:true,addedRows:4}));
