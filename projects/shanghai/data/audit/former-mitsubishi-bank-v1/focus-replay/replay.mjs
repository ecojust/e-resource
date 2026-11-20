import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
const w='/tmp/mitsubishi117/projection',p='/tmp/shanghai-consulate-focus/local-view117/projects/shanghai',audit='/workspace/e-resource/projects/shanghai/data/audit/former-mitsubishi-bank-v1';
const read=f=>JSON.parse(fs.readFileSync(f)),sha=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const env={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};env.exports=env.module.exports;env.self=env;env.globalThis=env;vm.runInNewContext(fs.readFileSync(p+'/vendor/maplibre-gl.js','utf8'),env);const lib=env.module.exports;
const data=read(audit+'/main-map-browser.json'),id=data.model_id;let details={};
for(const phase of ['before','after']){
 const base=w+'/'+phase, m=await import(base+'/src/building-beacons.js'), {labelSize}=await import(base+'/size.mjs'),{candidateOverviewCamera}=await import(base+'/src/candidate-overview-camera.js');
 const catalog=read(base+'/data/candidate-city-integrations.json'),places=[...read(base+'/data/landmarks.json'),...catalog.models];
 assert.equal(places.length,155);const focus={...places.at(-1),city_integration:true};
 details[phase]={};
 for(const v of data.views.slice(0,2)){
  const key=v.view,[width,height]=v.viewport,desktop=width>760;
  const lamp=desktop?[561.99,349.46]:[168.5,466.0];let best=null;
  for(const right of desktop?[88]:[64,65])for(let bottom=174;bottom<=268;bottom+=.5){
   const insets={left:desktop?316:16,right,top:desktop?154:182,bottom},cam=candidateOverviewCamera(focus,{width,height,insets});
   if(Math.abs(cam.zoom-v.camera.zoom)>.002)continue;
   const style=Object.create(lib.Style.prototype);let t;style.map={migrateProjection(next){t=next}};style.tileManagers={};style._setProjectionInternal('mercator');
   t.resize(width,height);t.setFov(36.87);t.setZoom(v.camera.zoom);t.setCenter(lib.LngLat.convert(v.camera.center));t.setElevation(cam.elevation);t.setPadding(cam.padding);t.setPitch(v.camera.pitch);t.setBearing(v.camera.bearing);
   const map={transform:t};const visible=places.map((r,i)=>{let xy=m.projectBeaconAnchor(map,[r.lng,r.lat]);return {id:r.id,number:i+1,x:xy.x,y:xy.y,perspectiveScale:m.beaconPerspectiveScale(map,[r.lng,r.lat]),...labelSize(r.name)};}).filter(o=>o.x>=0&&o.y>=0&&o.x<=width&&o.y<=height&&t.isPointOnMapSurface(o));
   const view={width,height,insets:{...insets,left:desktop?312:12},focusedId:id};
   const original=m.layoutBeaconLabels(visible,view),protectedArea=m.projectFocusedFacade(map,focus);
   const enabled=phase==='before'?width>760&&original.length>1:original.length>0;
   const layout=enabled?m.avoidFocusedFacade(original,protectedArea,view):original;
   const item=layout.find(q=>q.id===id),measured=v.selected_label,anchor=visible.find(q=>q.id===id);
   const err=Math.hypot(anchor.x-lamp[0],anchor.y-lamp[1])+Math.abs(cam.zoom-v.camera.zoom)*1000;
   if(!best||err<best.err){let projector=(x,y,z)=>{const deg=Math.PI/180,a=focus.heading*deg,e=x*Math.cos(a)+y*Math.sin(a),n=-x*Math.sin(a)+y*Math.cos(a),r=6371008.8*Math.cos(focus.lat*deg),lat0=Math.asinh(Math.tan(focus.lat*deg)),elev=()=>z;
    let px=t.locationToScreenPoint({lng:focus.lng+e/r/deg,lat:Math.atan(Math.sinh(lat0+n/r))/deg},{getElevationForLngLat:elev,getElevationForLngLatZoom:elev});return [px.x,px.y]};
    let parts={};const tri=read(w+'/mesh.json');for(const [k,mesh]of Object.entries(tri)){parts[k]=mesh.vertices.map(v=>projector(...v))}
    best={err,cam,padding:cam.padding,lamp,projected_lamp:[anchor.x,anchor.y],protectedArea,observed:v.selected_label,original_label_delta_px:Math.hypot(measured.x-item.labelX,measured.y-item.labelY),labels:layout.map(q=>({id:q.id,number:q.number,x:q.labelX,y:q.labelY,width:q.width,height:q.height})),parts};
   }
  }
  assert(best,key);details[phase][key]=best;console.log(phase,key,best.err,best.original_label_delta_px,best.labels.map(q=>[q.id,q.x,q.y]),best.padding);
 }
}
for(const [key,a]of Object.entries(details.before)){assert(a.original_label_delta_px<1.2);assert(a.err<1.4);const b=details.after[key];assert(b.err<1.4);console.log('label-delta',key,JSON.stringify(a.labels)===JSON.stringify(b.labels));}
fs.writeFileSync(w+'/layouts.json',JSON.stringify(details));
