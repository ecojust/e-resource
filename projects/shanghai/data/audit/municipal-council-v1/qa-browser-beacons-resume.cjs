/* Municipal Council: seven preserved captures; continue only320px beacons/touch
 * with measured real-frame layout readiness in the original Chrome. MIT. */
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const {createHash}=require('crypto');
const PROJECT=path.resolve(__dirname,'../../..'),REPO=path.resolve(PROJECT,'../..'),OUT=__dirname,BASE=process.env.MODEL_BASE_URL||'http://127.0.0.1:8782/';
const ID='huangpu-shanghai-municipal-council',TOUCH_FROM='huangpu-grosvenor-house',COUNT=76,EXPECTED_CLIP_TRIANGLES=24,EXPECTED_SOURCE='86e8b002-5e0e-4912-9807-086c2afeb27c';
const ZERO_PADDING={top:0,right:0,bottom:0,left:0};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex'),read=rel=>JSON.parse(fs.readFileSync(path.join(PROJECT,rel),'utf8'));
const sameIds=(a,b)=>assert.deepEqual([...a].sort(),[...b].sort()),delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const assertClipCapacity=shader=>{assert.equal(shader.triangleLimit,192);assert.ok(Number.isInteger(shader.triangles)&&shader.triangles>=0&&shader.triangles<=192);for(const [key,value] of Object.entries({width:4,height:192,bytes:12288,type:'FloatType',format:'RGBAFormat',minFilter:'NearestFilter',magFilter:'NearestFilter',generateMipmaps:false}))assert.equal(shader.clippingTexture[key],value);};
async function connect(){
 const tabs=await(await fetch('http://127.0.0.1:9223/json/list')).json();assert.equal(tabs.filter(t=>t.type==='page').length,1);const tab=tabs.find(t=>t.type==='page');assert.equal(new URL(tab.url).pathname,'/index.html');
 const ws=new WebSocket(tab.webSocketDebuggerUrl),pending=new Map(),listeners=new Map();let next=0;
 await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
 ws.onclose=()=>{for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error('CDP transport closed'));}pending.clear();};
 ws.onmessage=event=>{const message=JSON.parse(event.data);if(message.id){const p=pending.get(message.id);if(!p)return;pending.delete(message.id);clearTimeout(p.timer);message.error?p.reject(Error(JSON.stringify(message.error))):p.resolve(message.result);}else for(const listener of listeners.get(message.method)||[])listener(message.params);};
 return {send(method,params={}){return new Promise((resolve,reject)=>{const id=++next,timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP timeout: '+method));},1200000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));});},on(method,listener){listeners.set(method,[...(listeners.get(method)||[]),listener]);},close(){ws.close();}};
}
async function run(){
 assert.ok(process.argv.includes('--run'),'Use --run only with the retained sole main-map page');
 const original=fs.readFileSync(path.join(__dirname,'qa-browser.cjs'),'utf8'),report=read('data/audit/municipal-council-v1/browser.json');
 assert.equal(report.completed,false);assert.equal(report.captures.length,7);assert.match(report.recovery.failure,/No layout render for 60s/);
 assert.equal(sha(original),report.qaScript.sha256);assert.equal(report.qaScript.sha256,'7c246f1438357f337f8bfd5e39624e871f509ac819b3fd0963591050f35963b5');
 const failedPath='data/audit/municipal-council-v1/browser-before-layout-recovery.json';assert.equal(sha(fs.readFileSync(path.join(PROJECT,failedPath))),sha(JSON.stringify(report,null,2)+'\n'));
 for(const capture of report.captures)assert.equal(sha(fs.readFileSync(path.join(OUT,capture.file))),capture.sha256);
 for(const binding of [report.catalog,report.manifest,report.footprint,report.qaScript,report.viewerRegistry,report.placementBinding,report.preflightAdjustment,report.httpRecovery,...report.expectedSourceBindings,...report.documentBindings])assert.equal(sha(fs.readFileSync(path.join(PROJECT,binding.file))),binding.sha256,binding.file);
 const catalog=read(report.catalog.file),row=catalog.models.find(r=>r.id===ID),footprint=read(report.footprint.file),manifest=read(report.manifest.file),cards=report.directory.cards;
 const neighbors=[...new Map([...footprint.exclusions.context_sources_within_80m,...footprint.exclusions.required_context_sources].map(n=>[n.source_id,n])).values()];
 const contextIds=[...new Set([...Object.values(footprint.identity.excluded_context_sources),...footprint.exclusions.required_context_sources.map(n=>n.source_id)])];
 const staticDirectories=report.directory.readmes;for(const binding of staticDirectories)assert.equal(sha(fs.readFileSync(path.join(REPO,binding.file))),binding.sha256,binding.file);
 const priorResumeScript=report.resumeScript;assert.equal(sha(fs.readFileSync(path.join(PROJECT,priorResumeScript.file))),priorResumeScript.sha256);
 const previousRecovery={...structuredClone(report.recovery),script:priorResumeScript};report.recoveryAttempts=[...(report.recoveryAttempts||[]),previousRecovery];
 report.resumeScript={file:path.relative(PROJECT,__filename),sha256:sha(fs.readFileSync(__filename))};
 report.layoutDiagnosticBinding={file:'data/audit/municipal-council-v1/layout-runtime-inspection.json',sha256:sha(fs.readFileSync(path.join(__dirname,'layout-runtime-inspection.json')))};
 report.layoutRecoveryNote={file:'data/audit/municipal-council-v1/layout-recovery-note.json',sha256:sha(fs.readFileSync(path.join(__dirname,'layout-recovery-note.json')))};
 report.recovery={startedAt:new Date().toISOString(),completed:false,browserClosed:false,initialFailure:previousRecovery.failure,failedReport:{file:failedPath,sha256:sha(fs.readFileSync(path.join(PROJECT,failedPath)))},previousScript:priorResumeScript,preservedCaptures:report.captures.map(c=>({file:c.file,sha256:c.sha256})),method:'Sequential raw CDP continuation in the same sole Chrome and main-map document; previous hosts are idle after recorded failures, no second Playwright controller.',cause:'The old layout helper used a60s per-render guard. Live sampling confirms visible/focused page, correct320x568 DOM/canvas/transform, liveGL with error0, zeroqueues and actual advancing render/rAF events. Keep real-frame proof and use one900s total layout budget with30s progress.',scope:'Only remaining320px baseline/worst-title captures and nativeGrosvenor-to-Municipal touch. Preserve seven images, four asset downloads,76directory, full/LOD and actualnear/source/HTTP/GPU proofs. Private next-model Blender is paused to yield CPU; no production input changed.'};
 const save=()=>fs.writeFileSync(path.join(OUT,'browser.json'),JSON.stringify(report,null,2)+'\n');save();
 const originalHostPID=4947,originalHostPath='/proc/'+originalHostPID;assert.match(fs.readFileSync(originalHostPath+'/cmdline','utf8'),/municipal-council-v1\/qa-browser\.cjs/);assert.match(fs.readFileSync(originalHostPath+'/status','utf8'),/State:\s+T/);assert.ok(!fs.existsSync('/proc/6442'),'Old raw-CDP host must be disconnected before handoff');report.hostHandoff={originalHostPID,originalHostPaused:true,priorRawHostPID:6442,priorRawHostExited:true,chromeRetained:true};save();
 const cdp=await connect(),phaseState={current:'beacons-layout-recovery'},responses=[],bodyRequests=new Map();
 const page={
  async evaluate(fn,arg){const result=await cdp.send('Runtime.evaluate',{expression:`(${fn.toString()})(${JSON.stringify(arg)??'undefined'})`,awaitPromise:true,returnByValue:true});if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result?.value;},
  async waitForFunction(fn,arg,options={}){const deadline=Date.now()+(options.timeout||30000);while(Date.now()<deadline){const value=await cdp.send('Runtime.evaluate',{expression:`Boolean((${fn.toString()})(${JSON.stringify(arg)??'undefined'}))`,awaitPromise:true,returnByValue:true});if(value.exceptionDetails)throw Error(JSON.stringify(value.exceptionDetails));if(value.result?.value)return;await delay(options.polling||500);}throw Error('Recovered waitForFunction timed out: '+fn.toString());},
  async setViewportSize({width,height}){await cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false,screenWidth:width,screenHeight:height});},
  locator(selector){return {getAttribute:name=>page.evaluate(({selector,name})=>document.querySelector(selector).getAttribute(name),{selector,name}),click:()=>page.evaluate(selector=>document.querySelector(selector).click(),selector)};},
  async screenshot({path:file}){const {data}=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});fs.writeFileSync(file,Buffer.from(data,'base64'));},
  context(){return {newCDPSession:async()=>({send:(...args)=>cdp.send(...args),detach:async()=>{}})};}
 };
 cdp.on('Runtime.exceptionThrown',({exceptionDetails})=>{report.errors.push({phase:phaseState.current,message:JSON.stringify(exceptionDetails)});save();});
 cdp.on('Runtime.consoleAPICalled',event=>{if(['error','warning'].includes(event.type)){report[event.type==='error'?'errors':'warnings'].push({phase:phaseState.current,message:event.args.map(a=>a.value??a.description).join(' ')});save();}});
 cdp.on('Network.responseReceived',({requestId,response})=>{
  const u=new URL(response.url),h=Object.fromEntries(Object.entries(response.headers).map(([k,v])=>[k.toLowerCase(),v]));if(response.status>=400)report.http.push({phase:phaseState.current,status:response.status,url:response.url});
  if(u.origin!==new URL(BASE).origin)return;
  if(u.pathname.startsWith('/src/')||u.pathname.startsWith('/assets/city-detail/macros/'+row.owner.macro_id+'/'))responses.push(new Promise((resolve,reject)=>bodyRequests.set(requestId,{resolve,reject,url:response.url,path:u.pathname,headers:h,status:response.status,phase:phaseState.current})));
 });
 cdp.on('Network.loadingFinished',({requestId})=>{const binding=bodyRequests.get(requestId);if(!binding)return;bodyRequests.delete(requestId);cdp.send('Network.getResponseBody',{requestId}).then(({body,base64Encoded})=>{const bytes=Buffer.from(body,base64Encoded?'base64':'utf8'),digest=sha(bytes);if(binding.headers['x-audit-sha256'])assert.equal(digest,binding.headers['x-audit-sha256']);const receipt={url:binding.url,path:binding.path.slice(1),status:binding.status,sha256:digest,bytes:bytes.length,origin:binding.headers['x-audit-origin'],phase:binding.phase,verification:'Actual resumed browser HTTP response bytes'};if(binding.path.startsWith('/src/'))report.sourceBindings[binding.path.slice(5)]=receipt;else report.citySourceHTTP.push(receipt);binding.resolve();}).catch(binding.reject);});
 cdp.on('Network.loadingFailed',({requestId,errorText,canceled})=>{const binding=bodyRequests.get(requestId);if(!binding)return;bodyRequests.delete(requestId);if(canceled)binding.resolve();else binding.reject(Error('HTTP failed: '+binding.url+' '+errorText));});
 await cdp.send('Runtime.enable');await cdp.send('Network.enable');await cdp.send('Page.enable');
 try{
  const slice=(start,end)=>{const a=original.indexOf(start),b=original.indexOf(end,a+start.length);assert.ok(a>=0&&b>a);return original.slice(a,b);};
  const capture=slice(' const capture=async',' try{').replace('captureScript:report.qaScript','captureScript:report.resumeScript');
  const layout=`
 const layoutReady=async(width,height,main)=>{
  assert.equal(main,true,'This continuation only handles the existing main map');
  await page.evaluate(({width,height})=>{
   const m=window.__SHANGHAI_APP__.scene.map;if(window.__qaLayoutListener)m.off('render',window.__qaLayoutListener);
   const state=()=>{const canvas=m.getCanvas(),r=canvas.getBoundingClientRect(),rect=q=>document.querySelector(q)?.getBoundingClientRect().toJSON();return {inner:[innerWidth,innerHeight],canvas:[canvas.clientWidth,canvas.clientHeight],buffer:[canvas.width,canvas.height],rect:[r.width,r.height],transform:[m.transform.width,m.transform.height],ui:['#explore-panel','#location-card','.map-tools','#building-beacon-legend'].map(rect)};};
   const dimensions=s=>s.inner[0]===width&&s.inner[1]===height&&s.canvas[0]===width&&s.canvas[1]===height&&s.transform[0]===width&&s.transform[1]===height;
   const fingerprint=s=>JSON.stringify([s.inner,s.canvas,s.buffer,s.transform,...s.ui.map(r=>r&&[r.left,r.top,r.right,r.bottom].map(v=>Math.round(v*100)/100))]);
   let previous=null;window.__qaLayoutProgress={ready:false,frames:0,consecutiveStableComparisons:0,started:performance.now(),current:state(),renderTimes:[]};
   window.__qaLayoutListener=()=>{const p=window.__qaLayoutProgress,s=state(),next=fingerprint(s);p.frames++;p.consecutiveStableComparisons=dimensions(s)&&next===previous?p.consecutiveStableComparisons+1:0;previous=next;p.current=s;p.renderTimes.push(performance.now());p.ready=p.consecutiveStableComparisons>=2;if(p.ready)m.off('render',window.__qaLayoutListener);};
   m.on('render',window.__qaLayoutListener);m.triggerRepaint();
  },{width,height});
  const deadline=Date.now()+900000;let loggedAt=Date.now(),last;
  while(Date.now()<deadline){last=await page.evaluate(()=>{const p=window.__qaLayoutProgress;if(!p.ready)window.__SHANGHAI_APP__.scene.map.triggerRepaint();return p;});if(last.ready){assert.ok(last.frames>=3&&last.consecutiveStableComparisons>=2);return {...last.current,actualRenderFrames:last.frames,stableComparisons:last.consecutiveStableComparisons,renderTimes:last.renderTimes};}if(Date.now()-loggedAt>=30000){loggedAt=Date.now();console.log('WAIT_LAYOUT',JSON.stringify({width,height,frames:last.frames,stable:last.consecutiveStableComparisons,current:last.current}));}await new Promise(resolve=>setTimeout(resolve,500));}
  await page.evaluate(()=>window.__SHANGHAI_APP__.scene.map.off('render',window.__qaLayoutListener));throw Error('Actual layout render/fingerprint did not stabilize within900s: '+JSON.stringify(last));
 };
 `;
  const helpers=slice('  const panel=async open=>','  await page.setViewportSize({width:320,height:568});await panel(false);await layoutReady(320,568,true);');
  const witnessed=report.global.ownerGroupIsolation.observations.find(r=>r.label==='nearCourtyard');assert.ok(witnessed.ownVisible&&witnessed.foreign.some(f=>f.representativeOwner===1754&&f.visible));assert.equal(witnessed.own.triangles,24);assert.equal(witnessed.foreign.find(f=>f.representativeOwner===1754).actual.triangles,0);assert.equal(report.global.webglAfterNearCapture.glError,0);assert.equal(report.global.webglAfterNearCapture.contextLost,false);
  const remaining=slice("  phase='beacons';",' }catch(error)').replace("phase='beacons'","phaseState.current='beacons-recovery'");
  const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
  const names=['fs','path','assert','PROJECT','REPO','OUT','BASE','ID','TOUCH_FROM','COUNT','EXPECTED_CLIP_TRIANGLES','EXPECTED_SOURCE','ZERO_PADDING','sha','sameIds','assertClipCapacity','report','save','page','responses','catalog','row','footprint','manifest','neighbors','contextIds','cards','staticDirectories','phaseState','__filename'];
  const values=[fs,path,assert,PROJECT,REPO,OUT,BASE,ID,TOUCH_FROM,COUNT,EXPECTED_CLIP_TRIANGLES,EXPECTED_SOURCE,ZERO_PADDING,sha,sameIds,assertClipCapacity,report,save,page,responses,catalog,row,footprint,manifest,neighbors,contextIds,cards,staticDirectories,phaseState,__filename];
  await new AsyncFunction(...names,layout+'\n'+capture+'\n'+helpers+'\n'+remaining)(...values);
  for(const binding of [report.resumeScript,priorResumeScript,report.layoutDiagnosticBinding,report.layoutRecoveryNote])assert.equal(sha(fs.readFileSync(path.join(PROJECT,binding.file))),binding.sha256,binding.file);assert.equal(report.captures.length,9);for(const capture of report.captures)assert.equal(sha(fs.readFileSync(path.join(OUT,capture.file))),capture.sha256);
  report.recovery.completed=true;report.recovery.completedAt=new Date().toISOString();report.recovery.remainingCaptures=report.captures.slice(7).map(c=>({file:c.file,sha256:c.sha256,captureScript:c.captureScript}));save();
  try{await cdp.send('Browser.close');}catch(error){report.recovery.browserCloseTransport=error.message;}cdp.close();let closed=false;for(let n=0;n<20;n++){closed=await fetch('http://127.0.0.1:9223/json/version',{signal:AbortSignal.timeout(500)}).then(()=>false).catch(()=>true);if(closed)break;await delay(500);}assert.ok(closed);if(fs.existsSync(originalHostPath)){assert.match(fs.readFileSync(originalHostPath+'/cmdline','utf8'),/municipal-council-v1\/qa-browser\.cjs/);process.kill(originalHostPID,'SIGKILL');for(let n=0;n<20&&fs.existsSync(originalHostPath);n++)await delay(100);}assert.ok(!fs.existsSync(originalHostPath));report.hostHandoff.originalHostCleanedAfterChromeClose=true;report.hostHandoff.cleanupSignal='SIGKILL of paused idle QA host, after Browser.close confirmation';report.recovery.browserClosed=true;report.browserClosed=true;report.browserClosedAt=new Date().toISOString();save();console.log('COMPLETE Municipal Council beacon-only recovery; all frozen inputs unchanged.');
 }catch(error){report.completed=false;report.recovery.failure=error.stack;save();console.error(error);console.error('Original Chrome retained; do not attach another Playwright controller.');process.exitCode=1;await new Promise(()=>{});}
}
run().catch(error=>{console.error(error);process.exitCode=1;});
