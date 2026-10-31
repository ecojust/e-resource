/* Continue the two unfinished Cathay captures in the retained Chrome.
 * Raw CDP only; never attaches another Playwright controller. MIT. */
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const {createHash}=require('crypto');
const PROJECT=path.resolve(__dirname,'../../..'),REPO=path.resolve(PROJECT,'../..');
const OUT=__dirname,BASE=process.env.MODEL_BASE_URL||'http://127.0.0.1:8782/';
const ID='huangpu-cathay-mansions',TOUCH_FROM='huangpu-daxin-company',COUNT=74;
const EXPECTED_SOURCE='f6e4b883-ed86-4c90-aa96-2c717ff043c5';
const ZERO_PADDING={top:0,right:0,bottom:0,left:0};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=rel=>JSON.parse(fs.readFileSync(path.join(PROJECT,rel),'utf8'));
const sameIds=(a,b)=>assert.deepEqual([...a].sort(),[...b].sort());
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));

async function connect(){
 const tabs=await (await fetch('http://127.0.0.1:9223/json/list')).json();
 assert.equal(tabs.filter(t=>t.type==='page').length,1,'Retain exactly one page');
 const tab=tabs.find(t=>t.type==='page');assert.ok(tab.url.includes('index.html#landmark='+ID));
 const ws=new WebSocket(tab.webSocketDebuggerUrl),pending=new Map(),listeners=new Map();let next=0;
 await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
 ws.onmessage=event=>{const message=JSON.parse(event.data);if(message.id){const p=pending.get(message.id);if(!p)return;pending.delete(message.id);clearTimeout(p.timer);message.error?p.reject(Error(JSON.stringify(message.error))):p.resolve(message.result);}else for(const listener of listeners.get(message.method)||[])listener(message.params);};
 return {send(method,params={}){return new Promise((resolve,reject)=>{const id=++next,timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP timeout: '+method));},300000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));});},on(method,listener){listeners.set(method,[...(listeners.get(method)||[]),listener]);},close(){ws.close();}};
}

async function run(){
 assert.ok(process.argv.includes('--run'),'Use --run only for the retained failed browser');
 const originalPath=path.join(OUT,'qa-browser.cjs'),original=fs.readFileSync(originalPath,'utf8');
 const report=read('data/audit/cathay-mansions-v1/browser.json');
 assert.equal(report.completed,false);assert.equal(report.captures.length,5);assert.ok(report.failure.includes('at panel'));
 assert.equal(sha(original),report.qaScript.sha256);assert.equal(report.qaScript.sha256,'b640413bddb463bdde23fb9ce8c6f0a68056a71e083bd538906df3c587ce4b32');
 for(const capture of report.captures)assert.equal(sha(fs.readFileSync(path.join(OUT,capture.file))),capture.sha256);
 const catalog=read(report.catalog.file),row=catalog.models.find(r=>r.id===ID),footprint=read(report.footprint.file),manifest=read(report.manifest.file);
 const neighbors=[...new Map([...footprint.exclusions.all_macro_neighbors_within_65m,...footprint.exclusions.required_context_sources].map(n=>[n.source_id,n])).values()];
 const contextIds=Object.values(footprint.identity.excluded_context_sources),cards=report.directory.cards,staticDirectories=report.directory.readmes;
 for(const binding of [report.catalog,report.manifest,report.footprint,report.qaScript,report.viewerRegistry,...report.expectedSourceBindings])assert.equal(sha(fs.readFileSync(path.join(PROJECT,binding.file))),binding.sha256);
 for(const binding of staticDirectories)assert.equal(sha(fs.readFileSync(path.join(REPO,binding.file))),binding.sha256);
 report.resumeScript={file:path.relative(PROJECT,__filename),sha256:sha(fs.readFileSync(__filename))};
 report.recovery={startedAt:new Date().toISOString(),completed:false,method:'Raw CDP continuation in the original Chrome/page; no second Playwright connection.',initialFailure:report.failure,initialScript:report.qaScript,preservedCaptures:report.captures.map(c=>({file:c.file,sha256:c.sha256})),cause:'The QA panel() timeout was 30 seconds. During the 390px resize the panel already had closed/aria-expanded=false but its CSS transform had not advanced under software GPU load. A later read in the same page confirmed transform -335px, opacity 0, no active animation, and DOM/canvas/MapLibre dimensions 390x844. No production code or assets changed.',scope:'Continue only global mobile, 320px 74-beacon native touch, and final bindings/ownership assertions. Do not repeat accepted auxiliary assets, desktop/default, north-recess view, downloads, directory or full/LOD checks.',panelTimeoutMs:180000};
 delete report.failure;const save=()=>fs.writeFileSync(path.join(OUT,'browser.json'),JSON.stringify(report,null,2)+'\n');save();
 const cdp=await connect();let phase='global-resume';const responses=[];
 const page={
  async evaluate(fn,arg){const result=await cdp.send('Runtime.evaluate',{expression:`(${fn.toString()})(${JSON.stringify(arg)??'undefined'})`,awaitPromise:true,returnByValue:true});if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result?.value;},
  async waitForFunction(fn,arg,options={}){const deadline=Date.now()+(options.timeout||30000);while(Date.now()<deadline){if(await this.evaluate(fn,arg))return;await delay(options.polling||500);}throw Error('Recovered waitForFunction timed out: '+fn.toString());},
  async setViewportSize({width,height}){await cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false,screenWidth:width,screenHeight:height});},
  locator(selector){return {getAttribute:name=>page.evaluate(({selector,name})=>document.querySelector(selector).getAttribute(name),{selector,name}),click:()=>page.evaluate(selector=>document.querySelector(selector).click(),selector)};},
  async screenshot({path:file}){const {data}=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});fs.writeFileSync(file,Buffer.from(data,'base64'));},
  context(){return {newCDPSession:async()=>({send:(...args)=>cdp.send(...args),detach:async()=>{}})};}
 };
 cdp.on('Runtime.exceptionThrown',({exceptionDetails})=>{report.errors.push({phase,message:JSON.stringify(exceptionDetails)});save();});
 cdp.on('Runtime.consoleAPICalled',event=>{if(['error','warning'].includes(event.type)){report[event.type==='error'?'errors':'warnings'].push({phase,message:event.args.map(a=>a.value??a.description).join(' ')});save();}});
 cdp.on('Network.responseReceived',({response})=>{const u=new URL(response.url),h=Object.fromEntries(Object.entries(response.headers).map(([k,v])=>[k.toLowerCase(),v]));if(response.status>=400)report.http.push({phase,status:response.status,url:response.url});if(u.origin===new URL(BASE).origin&&u.pathname.startsWith('/assets/city-detail/macros/')&&[row.owner.macro_id,...footprint.exclusions.required_context_sources.map(n=>n.macro_id)].some(id=>u.pathname.includes('/'+id+'/')))report.citySourceHTTP.push({url:response.url,path:u.pathname.slice(1),status:response.status,sha256:h['x-audit-sha256'],origin:h['x-audit-origin'],bytes:Number(h['content-length']),phase});});
 await cdp.send('Runtime.enable');await cdp.send('Network.enable');
 const slice=(start,end)=>{const a=original.indexOf(start),b=original.indexOf(end,a+start.length);assert.ok(a>=0&&b>a);return original.slice(a,b);};
 // Reuse the frozen, reviewed assertions verbatim. Only panel's transition
 // budget and the capture-script binding change for this recovery segment.
 const layout=slice(' const layoutReady=async',' try{').replace('captureScript:report.qaScript','captureScript:report.resumeScript');
 const helpers=slice('  const panel=async open=>','  await panel(true);report.global.desktopLayout').replace('{timeout:30000}','{timeout:180000}');
 const remaining=slice('  await page.setViewportSize({width:390,height:844});await panel(false);report.global.mobileLayout',' }catch(error)');
 const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
 const names=['fs','path','assert','PROJECT','REPO','OUT','BASE','ID','TOUCH_FROM','COUNT','EXPECTED_SOURCE','ZERO_PADDING','sha','sameIds','report','save','page','responses','catalog','row','footprint','manifest','neighbors','contextIds','cards','staticDirectories','__filename'];
 const values=[fs,path,assert,PROJECT,REPO,OUT,BASE,ID,TOUCH_FROM,COUNT,EXPECTED_SOURCE,ZERO_PADDING,sha,sameIds,report,save,page,responses,catalog,row,footprint,manifest,neighbors,contextIds,cards,staticDirectories,__filename];
 try{
  await new AsyncFunction(...names,`let phase='global-resume';\n${layout}\n${helpers}\n${remaining}`)(...values);
  assert.equal(sha(fs.readFileSync(__filename)),report.resumeScript.sha256);assert.equal(report.captures.length,7);
  report.recovery.completed=true;report.recovery.completedAt=new Date().toISOString();report.recovery.remainingCaptures=report.captures.slice(5).map(c=>({file:c.file,sha256:c.sha256,captureScript:c.captureScript}));save();
  await cdp.send('Browser.close');cdp.close();
  let closed=false;for(let n=0;n<20;n++){closed=await fetch('http://127.0.0.1:9223/json/version',{signal:AbortSignal.timeout(500)}).then(()=>false).catch(()=>true);if(closed)break;await delay(500);}assert.ok(closed,'Browser must close after successful recovery');report.recovery.browserClosed=true;save();console.log('COMPLETE retained-browser recovery; 7 unique captures, no production changes.');
 }catch(error){report.completed=false;report.recovery.failure=error.stack;save();console.error(error);console.error('Original Chrome retained; do not attach Playwright.');cdp.close();process.exitCode=1;}
}
run().catch(error=>{console.error(error);process.exitCode=1;});
