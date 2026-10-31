/* Actual 22x18 sprite pixels at 320x548, using the retained Cathay selection.
 * Temporarily pauses only the QA scheduler; Chrome and the scene keep running.
 * Restores 320x568 before the main script performs its native touch. MIT. */
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{createHash}=require('crypto');
const OUT=__dirname,PROJECT=path.resolve(OUT,'../../..'),sha=b=>createHash('sha256').update(b).digest('hex');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function run(){
 const driverPid=Number(process.argv[2]);assert.ok(Number.isInteger(driverPid)&&driverPid>1);
 const main=JSON.parse(fs.readFileSync(path.join(OUT,'browser.json')));assert.equal(main.completed,false);
 const report={generatedAt:new Date().toISOString(),completed:false,driverPid,script:{file:'data/audit/grosvenor-house-v1/qa-short-beacons.cjs',sha256:sha(fs.readFileSync(__filename))},catalog:main.catalog,manifest:main.manifest,sourceBindings:main.expectedSourceBindings,scope:'Actual 320x548 viewport keeps Cathay selected at zoom8. Its normal 143px card top becomes328px, matching the measured worst-title free region at320x568. This is not a claim that Beidajie222 was selected; no old model is selected or loaded for this check.',errors:[]};
 const save=()=>fs.writeFileSync(path.join(OUT,'short-beacons.json'),JSON.stringify(report,null,2)+'\n');save();
 const tab=(await (await fetch('http://127.0.0.1:9223/json/list')).json()).find(t=>t.type==='page');assert.ok(tab);
 const ws=new WebSocket(tab.webSocketDebuggerUrl),pending=new Map();let next=0,closedResolve;const closed=new Promise(resolve=>closedResolve=resolve);
 await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});ws.onclose=closedResolve;
 ws.onmessage=event=>{const r=JSON.parse(event.data);if(!r.id)return;const p=pending.get(r.id);if(!p)return;pending.delete(r.id);clearTimeout(p.timer);r.error?p.reject(Error(JSON.stringify(r.error))):p.resolve(r.result);};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++next,timer=setTimeout(()=>reject(Error('CDP timeout '+method)),1200000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));});
 const evaluate=async(fn,arg)=>{const r=await send('Runtime.evaluate',{expression:`(${fn.toString()})(${JSON.stringify(arg)??'undefined'})`,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result?.value;};
 const resize=height=>send('Emulation.setDeviceMetricsOverride',{width:320,height,deviceScaleFactor:1,mobile:false,screenWidth:320,screenHeight:height});
 const state=()=>evaluate(()=>{const a=window.__SHANGHAI_APP__,m=a.scene.map,b=a.scene.getBuildingBeaconState(),rect=q=>document.querySelector(q).getBoundingClientRect().toJSON();return {hash:location.hash,title:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],canvas:[m.getCanvas().clientWidth,m.getCanvas().clientHeight],transform:[m.transform.width,m.transform.height],map:{center:m.getCenter(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),padding:m.getPadding(),elevation:m.transform.elevation},beacons:b,ui:{card:rect('#location-card'),tools:rect('.map-tools'),legend:rect('#building-beacon-legend')},allSpritesPresent:b.spriteIds.every(id=>m.hasImage(id)),picks:b.labelPositions.map(p=>({id:p.id,hit:a.scene.pickBuildingBeacon({x:p.x,y:p.y})})),steady:window.__qaGrosvenorSteady()};});
 const stable=async height=>{const deadline=Date.now()+900000;let last=null,consecutive=0,logAt=Date.now();while(Date.now()<deadline){
  await evaluate(async()=>{const m=window.__SHANGHAI_APP__.scene.map;await new Promise(resolve=>{m.once('render',resolve);m.triggerRepaint();});});const s=await state(),fingerprint=JSON.stringify([s.viewport,s.canvas,s.transform,s.ui,s.steady.fingerprint]);
  const ready=s.viewport[0]===320&&s.viewport[1]===height&&JSON.stringify(s.canvas)===JSON.stringify(s.viewport)&&JSON.stringify(s.transform)===JSON.stringify(s.viewport)&&s.steady.ready;
  consecutive=ready&&fingerprint===last?consecutive+1:0;last=fingerprint;if(consecutive>=2)return s;
  if(Date.now()-logAt>30000){logAt=Date.now();console.log('WAIT_SHORT',JSON.stringify({viewport:s.viewport,ready:s.steady.ready,city:s.steady.city}));}await delay(100);
 }throw Error('Short sprite scene did not stabilize');};
 let resumed=false;
 try{
  report.before=await state();assert.deepEqual(report.before.viewport,[320,568]);assert.equal(new URLSearchParams(report.before.hash.slice(1)).get('landmark'),'huangpu-cathay-mansions');assert.equal(report.before.map.zoom,8);
  await resize(548);report.scene=await stable(548);const s=report.scene,b=s.beacons,labels=b.labelPositions;
  assert.equal(b.count,75);assert.equal(b.viewportLabelCount,75);assert.equal(b.overlapFallbackCount,0);assert.equal(b.labelMode,'numbers');assert.equal(b.labelPixelSize,12);assert.equal(b.anchorPixelSize,20);assert.ok(s.allSpritesPresent);assert.equal(b.spriteIds.length,9);assert.equal(s.ui.card.top,328);
  assert.equal(new Set(labels.map(p=>p.id)).size,75);for(const p of s.picks)assert.equal(p.hit,p.id);
  for(let i=0;i<labels.length;i++){const p=labels[i];assert.equal(p.width,22);assert.equal(p.height,18);assert.ok(p.x-11>=0&&p.x+11<=320&&p.y-9>=0&&p.y+9<=548);for(const r of Object.values(s.ui))assert.ok(p.x+11<=r.left+.1||p.x-11>=r.right-.1||p.y+9<=r.top+.1||p.y-9>=r.bottom-.1);for(const q of labels.slice(i+1))assert.ok(Math.abs(p.x-q.x)>=22-.1||Math.abs(p.y-q.y)>=18-.1);}
  const source=main.expectedSourceBindings.find(r=>r.file==='src/building-beacons.js'),version=source.sha256.slice(0,8)+'-'+sha(fs.readFileSync(__filename)+main.catalog.sha256+main.manifest.sha256).slice(0,8),file=`browser-beacons-320x548-short-${version}.png`;
  assert.ok(!fs.existsSync(path.join(OUT,file)));const screenshot=await send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false}),bytes=Buffer.from(screenshot.data,'base64');assert.deepEqual([bytes.readUInt32BE(16),bytes.readUInt32BE(20)],[320,548]);fs.writeFileSync(path.join(OUT,file),bytes);
  report.capture={file,bytes:bytes.length,sha256:sha(bytes),viewport:[320,548],captureScript:report.script,sourceBindings:report.sourceBindings,visualAcceptance:'pending actual image review'};save();console.log('SAVED',file);
  await resize(568);report.restored=await stable(568);assert.equal(report.restored.hash,report.before.hash);assert.deepEqual(report.restored.map,report.before.map);assert.equal(report.restored.ui.card.height,report.before.ui.card.height);
  for(const binding of [main.catalog,main.manifest,...main.expectedSourceBindings])assert.equal(sha(fs.readFileSync(path.join(PROJECT,binding.file))),binding.sha256);assert.equal(sha(fs.readFileSync(__filename)),report.script.sha256);
  report.completed=true;report.restoredMainViewport=true;report.completedAt=new Date().toISOString();save();process.kill(driverPid,'SIGCONT');resumed=true;console.log('RESTORED 320x568; resumed original QA driver');
  // Device emulation belongs to this CDP session, so keep it until the main
  // script closes Chrome; disconnecting earlier would clear the restored size.
  await closed;report.browserClosedWithMain=true;save();console.log('COMPLETE short-sprite visual supplement');
 }catch(error){report.failure=error.stack;save();console.error(error);try{await resize(568);await stable(568);}catch(restoreError){report.errors.push(restoreError.stack);save();}if(!resumed){process.kill(driverPid,'SIGCONT');resumed=true;}await closed;process.exitCode=1;}
}
run().catch(error=>{console.error(error);process.exitCode=1;});
