import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';import {createHash}from'node:crypto';
import path from 'node:path';import {fileURLToPath}from'node:url';
const p=path.resolve(process.argv[2]),f=path.dirname(fileURLToPath(import.meta.url)),out=path.resolve(process.argv[3]);fs.mkdirSync(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex'),read=x=>JSON.parse(fs.readFileSync(x));const columns=read(f+'/columns.json').columns;
const env={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};env.exports=env.module.exports;env.self=env;env.globalThis=env;vm.runInNewContext(fs.readFileSync(p+'/vendor/maplibre-gl.js','utf8'),env);const lib=env.module.exports;
const model=read(p+'/data/candidate-city-integrations.json').models.find(x=>x.id==='huangpu-bank-of-taiwan-building');const current=read(f+'/c-actual/browser.json');const original=read(path.join(f,'../original153/main-browser.json'));
function project(dims,camera,padding){const [w,h]=dims;const style=Object.create(lib.Style.prototype);let t;style.map={migrateProjection(next){t=next}};style.tileManagers={};style._setProjectionInternal('mercator');
 t.resize(w,h);t.setFov(36.87);t.setZoom(camera.zoom);t.setCenter(lib.LngLat.convert(camera.center));t.setElevation(camera.elevation);t.setPadding(padding);t.setPitch(camera.pitch);t.setBearing(camera.bearing);
 const r=Math.PI/180,an=r*model.heading,co=Math.cos(an),si=Math.sin(an),k=6371008.8*Math.cos(model.lat*r),lat0=Math.asinh(Math.tan(model.lat*r));
 return Object.fromEntries(Object.entries(columns).map(([key,c])=>[key,c.vertices.map(([x,y,z])=>{const e=x*co+y*si,n=-x*si+y*co,hi=()=>z;const o=t.locationToScreenPoint({lng:model.lng+e/k/r,lat:Math.atan(Math.sinh(lat0+n/k))/r},{getElevationForLngLat:hi,getElevationForLngLatZoom:hi});return [o.x,o.y];})]));}
const res={};
for(const key of ['mobile','desktop']){
 const v=current.views[key+'-default'],old=original.views.find(x=>x.view==='map-'+key);
 const cal=project(v.viewport,v.camera,v.camera.padding),actual=read(f+'/c-actual/'+key+'-default-projection.json');
 let error=0;for(const i in cal)for(let j=0;j<cal[i].length;j++)for(const d of [0,1])error=Math.max(error,Math.abs(cal[i][j][d]-actual[i][j][d]));
 assert(error<.015,'MapLibre projection replay '+error);
 const xy=project(old.viewport,old.camera,v.camera.padding);
 const outputFile=out+'/original-'+key+'-xy.json',blob=JSON.stringify(xy);fs.writeFileSync(outputFile,blob);
 res[key]={real_calibration_max_deviation_px:error,padding_used:v.camera.padding,original_recorded_camera:old.camera,original_viewport:old.viewport,projected_sha256:sha(blob),after_actual_coordinate_sha256:v.projection_sha256};
}
fs.writeFileSync(out+'/baseline-calibration.json',JSON.stringify(res,null,2)+'\n');console.log(res);
