/* Municipal Council: one original Chrome, six preserved captures, actual near
 * context plus remaining beacon/touch checks. No second Playwright connection. MIT. */
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
 assert.equal(report.completed,false);assert.equal(report.captures.length,6);assert.match(report.failure,/Need actual visible own and independent courtyard1754/);
 assert.equal(sha(original),report.qaScript.sha256);assert.equal(report.qaScript.sha256,'7c246f1438357f337f8bfd5e39624e871f509ac819b3fd0963591050f35963b5');
 const failedPath='data/audit/municipal-council-v1/browser-before-near-context-recovery.json';assert.equal(sha(fs.readFileSync(path.join(PROJECT,failedPath))),sha(JSON.stringify(report,null,2)+'\n'));
 for(const capture of report.captures)assert.equal(sha(fs.readFileSync(path.join(OUT,capture.file))),capture.sha256);
 for(const binding of [report.catalog,report.manifest,report.footprint,report.qaScript,report.viewerRegistry,report.placementBinding,report.preflightAdjustment,report.httpRecovery,...report.expectedSourceBindings,...report.documentBindings])assert.equal(sha(fs.readFileSync(path.join(PROJECT,binding.file))),binding.sha256,binding.file);
 const catalog=read(report.catalog.file),row=catalog.models.find(r=>r.id===ID),footprint=read(report.footprint.file),manifest=read(report.manifest.file),cards=report.directory.cards;
 const neighbors=[...new Map([...footprint.exclusions.context_sources_within_80m,...footprint.exclusions.required_context_sources].map(n=>[n.source_id,n])).values()];
 const contextIds=[...new Set([...Object.values(footprint.identity.excluded_context_sources),...footprint.exclusions.required_context_sources.map(n=>n.source_id)])];
 const staticDirectories=report.directory.readmes;for(const binding of staticDirectories)assert.equal(sha(fs.readFileSync(path.join(REPO,binding.file))),binding.sha256,binding.file);
 report.resumeScript={file:path.relative(PROJECT,__filename),sha256:sha(fs.readFileSync(__filename))};
 report.recovery={startedAt:new Date().toISOString(),completed:false,browserClosed:false,initialFailure:report.failure,failedReport:{file:failedPath,sha256:sha(fs.readFileSync(path.join(PROJECT,failedPath)))},originalScript:report.qaScript,preservedCaptures:report.captures.map(c=>({file:c.file,sha256:c.sha256})),method:'Raw CDP continuation in the original sole Chrome and main-map document; no second Playwright controller.',cause:'The large 124 m compound fits default desktop/courtyard/mobile at zoom16.84/16.74/16.64, below the production near-detail activation threshold17.3. Those six screenshots remain valid auxiliary/default/far-source evidence. The full/LOD checks already loaded own1554=24 and foreign1754=0 together; a dedicated saved near-context view is still required.',scope:'Add one 1200x900 near courtyard view at actual zoom17.5, retain queue-zero/two-render stability and simultaneous own/foreign active assertions, then only finish the 320px dense/worst-title/native-touch checks. Production inputs remain frozen.'};delete report.failure;
 const save=()=>fs.writeFileSync(path.join(OUT,'browser.json'),JSON.stringify(report,null,2)+'\n');save();
 const cdp=await connect(),phaseState={current:'near-context-recovery'},responses=[],bodyRequests=new Map();
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
  const layout=slice(' const layoutReady=async',' try{').replace('captureScript:report.qaScript','captureScript:report.resumeScript');
  const helpers=slice('  const panel=async open=>','  await page.setViewportSize({width:320,height:568});await panel(false);await layoutReady(320,568,true);');
  let ownership=slice('  const isolation=footprint.near_group_owner_isolation_requirement',"  phase='beacons';");
  assert.ok(ownership.includes('mobile:report.global.defaultMobile}'));
  ownership=ownership.replace('mobile:report.global.defaultMobile}','mobile:report.global.defaultMobile,nearCourtyard:report.global.nearCourtyardRetainedContext}').replace("['desktop','courtyard','mobile'].includes(r.label)","['desktop','courtyard','mobile','nearCourtyard'].includes(r.label)");
  const near=`
  await page.setViewportSize({width:1200,height:900});await panel(false);report.global.nearCourtyardLayout=await layoutReady(1200,900,true);
  await select(ID);
  await page.evaluate(({row,pose,padding})=>{const s=window.__SHANGHAI_APP__.scene;s.setVisualQuality({shadows:false,surfaceNormals:true});s.map.setCenterClampedToGround(false);s.map.jumpTo({center:[row.lng,row.lat],zoom:17.5,pitch:pose.pitch,bearing:pose.bearing,padding,elevation:0});s.loadLandmarks();},{row,pose:footprint.camera_obstruction_review.scope_view_suggestion,padding:ZERO_PADDING});
  await settle(true);report.global.nearCourtyardRetainedContext=await globalState();assertAsset(report.global.nearCourtyardRetainedContext,report.global.nearCourtyardRetainedContext.asset.variant);assertFraming(report.global.nearCourtyardRetainedContext);assert.equal(report.global.nearCourtyardRetainedContext.map.zoom,17.5);
  report.global.nearCourtyardRetainedContext.note='Dedicated actual near-layer view above the production17.3 activation threshold. Shadows disabled for legibility; all authored and preserved source geometry remains in the production scene.';
  const nearSources=report.global.nearCourtyardRetainedContext.candidate.shader.ownerScopedSources,nearActive=new Set(report.global.nearCourtyardRetainedContext.streaming.detail.active.map(r=>r.id));
  const ownNear=nearSources.find(r=>r.macro_id===row.owner.macro_id&&r.feature_local_ids.includes(1554)),courtNear=nearSources.find(r=>r.macro_id===row.owner.macro_id&&r.feature_local_ids.includes(1754));
  assert.ok(ownNear&&courtNear&&nearActive.has(ownNear.id)&&nearActive.has(courtNear.id));assert.equal(ownNear.triangles,24);assert.equal(courtNear.triangles,0);sameIds(ownNear.clip_feature_local_ids,[1554]);sameIds(courtNear.clip_feature_local_ids,[]);
  await capture('global-near-courtyard-retained-context',report.global.nearCourtyardRetainedContext,[1200,900]);
  report.global.webglAfterNearCapture=await page.evaluate(()=>{const a=window.__SHANGHAI_APP__,gl=a.scene.map.painter.context.gl;return {glError:gl.getError(),contextLost:gl.isContextLost(),clipping:a.scene.getCandidateIntegrationState().shader};});assert.equal(report.global.webglAfterNearCapture.glError,0);assert.equal(report.global.webglAfterNearCapture.contextLost,false);assertClipCapacity(report.global.webglAfterNearCapture.clipping);save();
  `;
  const remaining=slice("  phase='beacons';",' }catch(error)').replace("phase='beacons'","phaseState.current='beacons-recovery'");
  const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
  const names=['fs','path','assert','PROJECT','REPO','OUT','BASE','ID','TOUCH_FROM','COUNT','EXPECTED_CLIP_TRIANGLES','EXPECTED_SOURCE','ZERO_PADDING','sha','sameIds','assertClipCapacity','report','save','page','responses','catalog','row','footprint','manifest','neighbors','contextIds','cards','staticDirectories','phaseState','__filename'];
  const values=[fs,path,assert,PROJECT,REPO,OUT,BASE,ID,TOUCH_FROM,COUNT,EXPECTED_CLIP_TRIANGLES,EXPECTED_SOURCE,ZERO_PADDING,sha,sameIds,assertClipCapacity,report,save,page,responses,catalog,row,footprint,manifest,neighbors,contextIds,cards,staticDirectories,phaseState,__filename];
  await new AsyncFunction(...names,layout+'\n'+helpers+'\n'+near+'\n'+ownership+'\n'+remaining)(...values);
  assert.equal(sha(fs.readFileSync(__filename)),report.resumeScript.sha256);assert.equal(report.captures.length,9);for(const capture of report.captures)assert.equal(sha(fs.readFileSync(path.join(OUT,capture.file))),capture.sha256);
  report.recovery.completed=true;report.recovery.completedAt=new Date().toISOString();report.recovery.remainingCaptures=report.captures.slice(6).map(c=>({file:c.file,sha256:c.sha256,captureScript:c.captureScript}));save();
  try{await cdp.send('Browser.close');}catch(error){report.recovery.browserCloseTransport=error.message;}cdp.close();let closed=false;for(let n=0;n<20;n++){closed=await fetch('http://127.0.0.1:9223/json/version',{signal:AbortSignal.timeout(500)}).then(()=>false).catch(()=>true);if(closed)break;await delay(500);}assert.ok(closed);report.recovery.browserClosed=true;report.browserClosed=true;report.browserClosedAt=new Date().toISOString();save();console.log('COMPLETE Municipal Council near-context recovery; all frozen inputs unchanged.');
 }catch(error){report.completed=false;report.recovery.failure=error.stack;save();console.error(error);console.error('Original Chrome retained; do not attach another Playwright controller.');process.exitCode=1;await new Promise(()=>{});}
}
run().catch(error=>{console.error(error);process.exitCode=1;});
