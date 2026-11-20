/* Confirm the real, visible selected map in an existing Chromium session. */
const fs=require('node:fs'),{execFileSync}=require('node:child_process'),{createHash}=require('node:crypto');
const [port,id,file]=process.argv.slice(2);
const pages=JSON.parse(execFileSync('curl',['-sf','http://127.0.0.1:'+port+'/json/list']));
const page=pages.find(p=>p.url.includes(id));if(!page)throw Error('Target not selected');
const w=new WebSocket(page.webSocketDebuggerUrl),timeout=setTimeout(()=>{w.close();process.exitCode=1},90000);
const probe=async id=>{
  const s=window.__SHANGHAI_APP__.scene,m=s.map,frames=[];
  for(let i=0;i<4;i++){await new Promise(r=>requestAnimationFrame(r));const css=getComputedStyle(document.querySelector('#loading')),a=s.getLandmarkAssetState(id);
    frames.push({overlay:[css.visibility,css.opacity,css.pointerEvents],moving:m.isMoving(),size:[innerWidth,innerHeight],center:m.getCenter().toArray(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),asset:a.verifiedAsset?.sha256,variant:a.variant,section:s.getCandidateIntegrationState().sourceSections.filter(x=>x.id===id),route:location.hash});}
  return frames;
};
w.onopen=()=>w.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression:'('+probe.toString()+')('+JSON.stringify(id)+')',awaitPromise:true,returnByValue:true}}));
w.onmessage=ev=>{clearTimeout(timeout);const ret=JSON.parse(ev.data);try{
 if(ret.result.exceptionDetails)throw Error(ret.result.exceptionDetails.text);
 const frames=ret.result.result.value;const first=JSON.stringify(frames[0]);if(!frames.every(f=>JSON.stringify(f)===first&&f.overlay.join(',')==='hidden,0,none'&&!f.moving&&f.asset&&f.route.includes(id)))throw Error('Pose or pixels not stable');
 fs.writeFileSync(file,JSON.stringify({checked:new Date().toISOString(),url:page.url,script_sha256:createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),frames},null,2)+'\n');console.log(frames[0].size,frames[0].bearing,frames[0].pitch,frames[0].section.length);
}catch(e){console.error(e.message);process.exitCode=1}finally{w.close()}};
