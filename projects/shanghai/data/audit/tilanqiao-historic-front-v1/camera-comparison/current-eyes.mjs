import fs from 'node:fs';
const p=process.argv[2],j=JSON.parse(fs.readFileSync('/tmp/tilan82/final-after/main-browser.json'));
let opts=j.cameraAlternatives;
if(!opts)throw Error('actual camera alternatives are not yet recorded');
const expression='('+String(async function(opts){
 const m=window.__SHANGHAI_APP__.scene.map,t=m.transform,LngLat=m.getCenter().constructor;
 const same={eye:t.getCameraLngLat().toArray(),alt:t.getCameraAltitude()};
 function eye(c,width,height){
   const q=t.clone();q.resize(width,height);q.setBearing(c.bearing);q.setPitch(c.pitch);q.setZoom(c.zoom);q.setPadding(c.padding);q.setCenter(new LngLat(...c.center));q.setElevation(c.elevation);
   return {eye_wgs84:q.getCameraLngLat().toArray(),eye_altitude_m:q.getCameraAltitude(),width,height,bearing:c.bearing,pitch:c.pitch,zoom:c.zoom,elevation:c.elevation,center:c.center};
 }
 const check=eye({bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),padding:m.getPadding(),center:m.getCenter().toArray(),elevation:m.getCenterElevation()},t.width,t.height);
 if(Math.abs(check.eye_wgs84[0]-same.eye[0])>1e-7||Math.abs(check.eye_wgs84[1]-same.eye[1])>1e-7||Math.abs(check.eye_altitude_m-same.alt)>1e-4)throw Error('Live eye mismatch '+JSON.stringify({check,same}));
 return {currentEye:same,cloneMatchedCurrentCamera:check,actualFrozenCameras:opts.flatMap(o=>[eye(o.registered,o.context.width,o.context.height),eye(o.candidate,o.context.width,o.context.height)])}
})+')('+JSON.stringify(opts)+')';
const list=await(await fetch('http://127.0.0.1:'+p+'/json/list')).json();const ws=new WebSocket(list.find(d=>d.type==='page').webSocketDebuggerUrl);ws.onopen=()=>ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression,returnByValue:true,awaitPromise:true}}));ws.onmessage=e=>{const r=JSON.parse(e.data);if(r.id!==1)return;if(r.result.exceptionDetails){console.error(r.result.result?.description||r.result.exceptionDetails);process.exitCode=1}else{fs.writeFileSync('/tmp/tilan82/actual-eyes.json',JSON.stringify(r.result.result.value,null,2)+'\n');console.log(r.result.result.value.actualFrozenCameras)}ws.close()};
