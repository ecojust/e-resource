import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';import {createHash}from'node:crypto';
import path from 'node:path'; import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),p=path.resolve(here,'../../../..','..');
const sha=b=>createHash('sha256').update(b).digest('hex'),read=x=>JSON.parse(fs.readFileSync(x));const columns=read(path.join(here,'windows.json')).windows;
const env={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};env.exports=env.module.exports;env.self=env;env.globalThis=env;vm.runInNewContext(fs.readFileSync(p+'/vendor/maplibre-gl.js','utf8'),env);const lib=env.module.exports;
const dataset=read(path.join(here,'../original-default-layout-fixture.json'));const model=dataset.location;
function project(dims,camera,padding){const [w,h]=dims;const style=Object.create(lib.Style.prototype);let t;style.map={migrateProjection(next){t=next}};style.tileManagers={};style._setProjectionInternal('mercator');
 t.resize(w,h);t.setFov(36.87);t.setZoom(camera.zoom);t.setCenter(lib.LngLat.convert(camera.center));t.setElevation(camera.elevation);t.setPadding(padding);t.setPitch(camera.pitch);t.setBearing(camera.bearing);
 const r=Math.PI/180,an=r*model.heading,co=Math.cos(an),si=Math.sin(an),k=6371008.8*Math.cos(model.lat*r),lat0=Math.asinh(Math.tan(model.lat*r));
 return Object.fromEntries(Object.entries(columns).map(([key,c])=>[key,c.vertices.map(([x,y,z])=>{const e=x*co+y*si,n=-x*si+y*co,hi=()=>z;const o=t.locationToScreenPoint({lng:model.lng+e/k/r,lat:Math.atan(Math.sinh(lat0+n/k))/r},{getElevationForLngLat:hi,getElevationForLngLatZoom:hi});return [o.x,o.y];})]));}
const res={};
for (const [name,v] of Object.entries(dataset.screens)){
 const m=name.endsWith('mobile');const padding=m?{left:16,top:182,right:65,bottom:228}:{left:316,top:154,right:88,bottom:241};
 res[name]=project(v.size,v.camera,padding);
}
fs.writeFileSync(path.join(here,'screen-windows.json'),JSON.stringify(res));
