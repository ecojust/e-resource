/* Resume after the directory's legitimate two-result keyword search.
 * Keep the original Chrome and three accepted auxiliary captures. MIT. */
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const {createHash}=require('crypto');
const PROJECT=path.resolve(__dirname,'../../..'),REPO=path.resolve(PROJECT,'../..');
const OUT=__dirname,BASE=process.env.MODEL_BASE_URL||'http://127.0.0.1:8782/';
const ID='huangpu-grosvenor-house',TOUCH_FROM='huangpu-cathay-mansions',COUNT=75,EXPECTED_CLIP_TRIANGLES=26;
const EXPECTED_SOURCE='6fa0e0aa-bfd0-4d9e-a4bb-16e9088d530e';
const ZERO_PADDING={top:0,right:0,bottom:0,left:0};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=rel=>JSON.parse(fs.readFileSync(path.join(PROJECT,rel),'utf8'));
const sameIds=(a,b)=>assert.deepEqual([...a].sort(),[...b].sort());
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));

async function connect(expectedPath){
 const tabs=await (await fetch('http://127.0.0.1:9223/json/list')).json();
 assert.equal(tabs.filter(t=>t.type==='page').length,1);
 const tab=tabs.find(t=>t.type==='page');assert.equal(new URL(tab.url).pathname,expectedPath);
 const ws=new WebSocket(tab.webSocketDebuggerUrl),pending=new Map(),listeners=new Map();let next=0;
 await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
 ws.onmessage=event=>{const message=JSON.parse(event.data);if(message.id){const p=pending.get(message.id);if(!p)return;pending.delete(message.id);clearTimeout(p.timer);message.error?p.reject(Error(JSON.stringify(message.error))):p.resolve(message.result);}else for(const listener of listeners.get(message.method)||[])listener(message.params);};
 return {send(method,params={}){return new Promise((resolve,reject)=>{const id=++next,timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP timeout: '+method));},1200000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));});},on(method,listener){listeners.set(method,[...(listeners.get(method)||[]),listener]);},close(){ws.close();}};
}

async function run(){
 assert.ok(process.argv.includes('--run'),'Use --run only with the retained directory page');
 const originalPath=path.join(OUT,'qa-browser.cjs'),original=fs.readFileSync(originalPath,'utf8');
 const report=read('data/audit/grosvenor-house-v1/browser.json');
 assert.equal(report.completed,false);assert.equal(report.captures.length,3);const continuingMain=Boolean(report.directory.cards&&report.recovery?.failure?.includes('Object reference chain is too long'));
 const currentFailure=continuingMain?report.recovery.failure:report.failure;assert.ok(continuingMain||currentFailure.includes('sameIds'));
 if(continuingMain){const prior=structuredClone(report.recovery);prior.script={...report.resumeScript,file:'data/audit/grosvenor-house-v1/qa-browser-resume-before-boolean.cjs'};assert.equal(sha(fs.readFileSync(path.join(PROJECT,prior.script.file))),prior.script.sha256);report.recoveryAttempts=[...(report.recoveryAttempts||[]),prior];}
 assert.equal(sha(original),report.qaScript.sha256);assert.equal(report.qaScript.sha256,'0ac13676e68ded2d7ff9ac457d7b081189e9e547e5f981a734f7e18c49b6d178');
 for(const capture of report.captures)assert.equal(sha(fs.readFileSync(path.join(OUT,capture.file))),capture.sha256);
 const catalog=read(report.catalog.file),row=catalog.models.find(r=>r.id===ID),footprint=read(report.footprint.file),manifest=read(report.manifest.file);
 const neighbors=[...new Map([...footprint.exclusions.all_macro_neighbors_within_65m,...footprint.exclusions.required_context_sources].map(n=>[n.source_id,n])).values()];
 const contextIds=Object.values(footprint.identity.excluded_context_sources),readDirectory=require('./qa-browser.cjs').readDirectory;
 const staticDirectories=[readDirectory(path.join(REPO,'README.md')),readDirectory(path.join(PROJECT,'README.md'))];
 for(const binding of [report.catalog,report.manifest,report.footprint,report.qaScript,report.viewerRegistry,...report.expectedSourceBindings])assert.equal(sha(fs.readFileSync(path.join(PROJECT,binding.file))),binding.sha256);
 for(const binding of report.preflight.directories)assert.equal(sha(fs.readFileSync(path.join(REPO,binding.file))),binding.sha256);
 report.resumeScript={file:path.relative(PROJECT,__filename),sha256:sha(fs.readFileSync(__filename))};
 report.recovery={startedAt:new Date().toISOString(),completed:false,method:'Raw CDP continuation in the original Chrome/page; no second Playwright controller.',initialFailure:currentFailure,initialScript:report.qaScript,booleanWaitAdapterFixed:true,preservedCaptures:report.captures.map(c=>({file:c.file,sha256:c.sha256})),cause:'The raw-CDP wait adapter now returns Boolean(predicate) instead of serializing the large app object; the failed adapter version is retained. The original QA wrongly required the short keyword 峻岭 to yield exactly one card. The Cathay scope description legitimately mentions neighboring 峻岭公寓, so two matches are correct. Verify both keyword matches, then the complete current title must resolve to the unique Grosvenor card. No production source or input changed.',scope:'Continue directory search semantics and the main-map/forecourt/mobile/beacon checks; preserve the accepted three auxiliary views and four verified downloads. Add an offscreen same-CSS measurement of all 75 current card titles without selecting or loading other models.'};
 delete report.failure;const save=()=>fs.writeFileSync(path.join(OUT,'browser.json'),JSON.stringify(report,null,2)+'\n');save();
 const cdp=await connect(continuingMain?'/index.html':'/landmarks.html'),phaseState={current:'directory-resume'},responses=[],catalogBodies=new Map();
 const page={
  async evaluate(fn,arg){const result=await cdp.send('Runtime.evaluate',{expression:`(${fn.toString()})(${JSON.stringify(arg)??'undefined'})`,awaitPromise:true,returnByValue:true});if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result?.value;},
  async waitForFunction(fn,arg,options={}){const deadline=Date.now()+(options.timeout||30000);while(Date.now()<deadline){const value=await cdp.send('Runtime.evaluate',{expression:`Boolean((${fn.toString()})(${JSON.stringify(arg)??'undefined'}))`,awaitPromise:true,returnByValue:true});if(value.exceptionDetails)throw Error(JSON.stringify(value.exceptionDetails));if(value.result?.value)return;await delay(options.polling||500);}throw Error('Recovered waitForFunction timed out: '+fn.toString());},
  async setViewportSize({width,height}){await cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false,screenWidth:width,screenHeight:height});},
  locator(selector){return {getAttribute:name=>page.evaluate(({selector,name})=>document.querySelector(selector).getAttribute(name),{selector,name}),click:()=>page.evaluate(selector=>document.querySelector(selector).click(),selector)};},
  async goto(url,{timeout=90000}={}){await cdp.send('Page.navigate',{url});const deadline=Date.now()+timeout;while(Date.now()<deadline){try{if(await this.evaluate(url=>location.href===url&&document.readyState!=='loading',url))return;}catch(error){if(!/context|navigat|destroy/i.test(error.message))throw error;}await delay(100);}throw Error('Navigation did not reach DOMContentLoaded');},
  async screenshot({path:file}){const {data}=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});fs.writeFileSync(file,Buffer.from(data,'base64'));},
  context(){return {newCDPSession:async()=>({send:(...args)=>cdp.send(...args),detach:async()=>{}})};}
 };
 cdp.on('Runtime.exceptionThrown',({exceptionDetails})=>{report.errors.push({phase:phaseState.current,message:JSON.stringify(exceptionDetails)});save();});
 cdp.on('Runtime.consoleAPICalled',event=>{if(['error','warning'].includes(event.type)){report[event.type==='error'?'errors':'warnings'].push({phase:phaseState.current,message:event.args.map(a=>a.value??a.description).join(' ')});save();}});
 cdp.on('Network.responseReceived',({requestId,response})=>{
  const u=new URL(response.url),h=Object.fromEntries(Object.entries(response.headers).map(([k,v])=>[k.toLowerCase(),v]));
  if(response.status>=400)report.http.push({phase:phaseState.current,status:response.status,url:response.url});
  if(u.origin!==new URL(BASE).origin)return;
  if(u.pathname.startsWith('/src/'))report.sourceBindings[u.pathname.slice(5)]={sha256:h['x-audit-sha256'],origin:h['x-audit-origin'],status:response.status};
  if(u.pathname==='/data/candidate-city-integrations.json')responses.push(new Promise((resolve,reject)=>catalogBodies.set(requestId,{resolve,reject,url:response.url,status:response.status,origin:h['x-audit-origin']})));
  if(u.pathname.startsWith('/assets/city-detail/macros/')&&[row.owner.macro_id,...footprint.exclusions.required_context_sources.map(n=>n.macro_id)].some(id=>u.pathname.includes('/'+id+'/')))report.citySourceHTTP.push({url:response.url,path:u.pathname.slice(1),status:response.status,sha256:h['x-audit-sha256'],origin:h['x-audit-origin'],bytes:Number(h['content-length']),phase:phaseState.current});
 });
 cdp.on('Network.loadingFinished',({requestId})=>{const binding=catalogBodies.get(requestId);if(!binding)return;catalogBodies.delete(requestId);cdp.send('Network.getResponseBody',{requestId}).then(({body,base64Encoded})=>{const bytes=Buffer.from(body,base64Encoded?'base64':'utf8');report.catalog.http={url:binding.url,status:binding.status,sha256:sha(bytes),origin:binding.origin};assert.equal(report.catalog.http.sha256,report.catalog.sha256);binding.resolve();}).catch(binding.reject);});
 await cdp.send('Runtime.enable');await cdp.send('Network.enable');await cdp.send('Page.enable');
 try{
  let cards;if(!continuingMain){cards=await page.evaluate(()=>[...document.querySelectorAll('.landmark-card[data-landmark]')].map(n=>({id:n.dataset.landmark,district:n.closest('.landmark-group').id,search:n.dataset.search,links:[...n.querySelectorAll('a')].map(a=>a.getAttribute('href'))})));
  assert.equal(cards.length,COUNT);assert.equal(new Set(cards.map(c=>c.id)).size,COUNT);assert.equal(new Set(cards.map(c=>c.district)).size,16);
  const newCard=cards.find(c=>c.id===ID);assert.equal(newCard.district,'district-310101');assert.ok(newCard.links.includes(`index.html#landmark=${ID}&mode=overview`));assert.ok(newCard.links.includes('grosvenor-house.html'));assert.ok(!newCard.links.some(l=>l.includes('mode=walk')));
  for(const directory of staticDirectories)sameIds(directory.rows.map(r=>r.id),cards.map(c=>c.id));
  const search=async text=>page.evaluate(text=>{const input=document.querySelector('#landmark-search');input.value=text;input.dispatchEvent(new Event('input',{bubbles:true}));return [...document.querySelectorAll('.landmark-card[data-landmark]:not([hidden])')].map(n=>({id:n.dataset.landmark,search:n.dataset.search}));},text);
  const keyword=await search('峻岭');sameIds(keyword.map(c=>c.id),[ID,TOUCH_FROM]);assert.ok(keyword.every(c=>c.search.includes('峻岭')));
  const exact=await search(row.name);sameIds(exact.map(c=>c.id),[ID]);
  const mainResponse=await fetch(new URL('index.html',BASE)),mainBytes=Buffer.from(await mainResponse.arrayBuffer());assert.equal(mainResponse.status,200);
  const readmeResponse=await fetch(new URL('README.md',BASE)),readmeBytes=Buffer.from(await readmeResponse.arrayBuffer());assert.equal(readmeResponse.status,200);assert.equal(sha(readmeBytes),staticDirectories[1].sha256);
  report.directory={cards,readmes:staticDirectories,grosvenorSearch:{keyword:'峻岭',matches:keyword,exactTitle:row.name,exactMatches:exact},mainDocumentHTTP:{status:mainResponse.status,sha256:sha(mainBytes)},projectReadmeHTTP:{status:readmeResponse.status,sha256:sha(readmeBytes)},note:'The short keyword correctly matches the Grosvenor name and Cathay neighboring-scope text. The full current title uniquely locates Grosvenor. All 75 card and README routes still target the shared main map.'};save();
  }else cards=report.directory.cards;
  const slice=(start,end)=>{const a=original.indexOf(start),b=original.indexOf(end,a+start.length);assert.ok(a>=0&&b>a);return original.slice(a,b);};
  const layout=slice(' const layoutReady=async',' try{').replace('captureScript:report.qaScript','captureScript:report.resumeScript');
  let remaining=slice("  phase='global';await page.setViewportSize",' }catch(error)').replace("phase='global'","phaseState.current='global-resume'").replace("phase='beacons'","phaseState.current='beacons-resume'");
  if(continuingMain)remaining=remaining.split('\n').filter(line=>!line.trim().startsWith('await page.goto(')).join('\n');
  const marker='  await panel(true);report.global.desktopLayout=await layoutReady(960,720,true);';
  const measurement=`
  await page.setViewportSize({width:320,height:568});await panel(false);await layoutReady(320,568,true);
  report.cardTitleCapacity=await page.evaluate(async()=>{
   const a=window.__SHANGHAI_APP__,m=a.scene.map,{walkingPose}=await import('./src/precise-registration-ui.js'),{layoutBeaconLabels}=await import('./src/building-beacons.js');
   const originalCard=document.querySelector('#location-card'),before=originalCard.outerHTML,currentRect=originalCard.getBoundingClientRect().toJSON(),clone=originalCard.cloneNode(true);
   clone.id='qa-card-measurement';clone.removeAttribute('aria-live');clone.inert=true;clone.style.transform='translateX(-10000px)';clone.style.visibility='hidden';clone.style.pointerEvents='none';
   for(const node of clone.querySelectorAll('[id]')){node.dataset.qaRole=node.id;node.removeAttribute('id');}
   const part=id=>clone.querySelector('[data-qa-role="'+id+'"]');document.body.append(clone);const rows=[];
   try{for(const place of a.landmarks){const district=a.districts.find(d=>d.id===(place.districtId||place.id)),overviewOnly=place.kind==='building'&&!walkingPose(place);
    part('location-name').textContent=place.name;part('location-district').textContent=(district?.name||'上海市')+(place.city_integration?' · 近似定位 · 外观模型':place.kind==='building'?' · 逐栋复原':place.height_m?' · 城市地标':' · 城市探索');
    part('start-walk').disabled=overviewOnly;part('start-walk').innerHTML=overviewOnly?'当前建筑仅支持俯瞰':'进入漫游 <span>↗</span>';
    part('reference-button').hidden=!place.reference&&!place.city_integration;part('reference-button').textContent=place.city_integration?'查看模型范围说明 ↗':'查看实景参考 ↗';
    const r=clone.getBoundingClientRect();rows.push({id:place.id,name:place.name,top:r.top,height:r.height,width:r.width,overviewOnly});
   }}finally{clone.remove();}
   if(originalCard.outerHTML!==before)throw Error('Main location card changed during offscreen measurement');
   const currentId=new URLSearchParams(location.hash.slice(1)).get('landmark'),currentCopy=rows.find(r=>r.id===currentId);if(!currentCopy||Math.abs(currentCopy.height-currentRect.height)>.5||Math.abs(currentCopy.width-currentRect.width)>.5)throw Error('Offscreen copy does not reproduce current card dimensions');
   const minTop=Math.min(...rows.map(r=>r.top)),maximumCards=rows.filter(r=>Math.abs(r.top-minTop)<.1),tools=document.querySelector('.map-tools').getBoundingClientRect(),legend=document.querySelector('#building-beacon-legend').getBoundingClientRect();
   const insets={left:12,right:Math.max(64,innerWidth-tools.left+8),top:Math.max(182,legend.bottom+8),bottom:Math.max(174,innerHeight-minTop+8)};
   const items=a.landmarks.map(r=>{const p=m.project([r.lng,r.lat]);return {id:r.id,x:p.x,y:p.y,width:176,height:62};}),positions=layoutBeaconLabels(items,{width:320,height:568,insets});
   return {viewport:[innerWidth,innerHeight],count:rows.length,currentId,currentCard:currentRect,currentCopy,rows,minimumCardTop:minTop,maximumCards,insets,positions,overlapFallbackCount:positions.filter(p=>p.overlapFallback).length,distinctSlots:new Set(positions.map(p=>p.labelX+','+p.labelY)).size,mainCardUnchanged:true,method:'Offscreen cloned card uses current production CSS, real title, district, walkingPose/button and reference visibility for all 75 records. No other model is selected or loaded. Capacity calls the shipped layout function with all real IDs/locations and maximal name-cell dimensions to enter the same compact branch.'};
  });
  assert.equal(report.cardTitleCapacity.count,COUNT);assert.equal(report.cardTitleCapacity.overlapFallbackCount,0);assert.equal(report.cardTitleCapacity.distinctSlots,COUNT);
  for(let i=0;i<report.cardTitleCapacity.positions.length;i++){const p=report.cardTitleCapacity.positions[i],n=report.cardTitleCapacity.insets;assert.ok(p.labelX-p.width/2>=n.left-.1&&p.labelX+p.width/2<=320-n.right+.1&&p.labelY-p.height/2>=n.top-.1&&p.labelY+p.height/2<=568-n.bottom+.1);for(const q of report.cardTitleCapacity.positions.slice(i+1))assert.ok(Math.abs(p.labelX-q.labelX)>=(p.width+q.width)/2-.1||Math.abs(p.labelY-q.labelY)>=(p.height+q.height)/2-.1);}
  console.log('MAX_CARD_LAYOUT',JSON.stringify({minimumTop:report.cardTitleCapacity.minimumCardTop,maximumCards:report.cardTitleCapacity.maximumCards,slots:report.cardTitleCapacity.distinctSlots,overlapFallback:report.cardTitleCapacity.overlapFallbackCount}));save();
  await page.setViewportSize({width:960,height:720});
`;
  assert.ok(remaining.includes(marker));remaining=remaining.replace(marker,measurement+marker);
  const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
  const names=['fs','path','assert','PROJECT','REPO','OUT','BASE','ID','TOUCH_FROM','COUNT','EXPECTED_CLIP_TRIANGLES','EXPECTED_SOURCE','ZERO_PADDING','sha','sameIds','report','save','page','responses','catalog','row','footprint','manifest','neighbors','contextIds','cards','staticDirectories','phaseState','__filename'];
  const values=[fs,path,assert,PROJECT,REPO,OUT,BASE,ID,TOUCH_FROM,COUNT,EXPECTED_CLIP_TRIANGLES,EXPECTED_SOURCE,ZERO_PADDING,sha,sameIds,report,save,page,responses,catalog,row,footprint,manifest,neighbors,contextIds,cards,staticDirectories,phaseState,__filename];
  await new AsyncFunction(...names,layout+'\n'+remaining)(...values);
  assert.equal(sha(fs.readFileSync(__filename)),report.resumeScript.sha256);assert.ok([7,8].includes(report.captures.length));
  report.recovery.completed=true;report.recovery.completedAt=new Date().toISOString();report.recovery.remainingCaptures=report.captures.slice(3).map(c=>({file:c.file,sha256:c.sha256,captureScript:c.captureScript}));save();
  await cdp.send('Browser.close');cdp.close();let closed=false;for(let n=0;n<20;n++){closed=await fetch('http://127.0.0.1:9223/json/version',{signal:AbortSignal.timeout(500)}).then(()=>false).catch(()=>true);if(closed)break;await delay(500);}assert.ok(closed);report.recovery.browserClosed=true;save();console.log('COMPLETE original-browser Grosvenor recovery; all frozen inputs unchanged.');
 }catch(error){report.completed=false;report.recovery.failure=error.stack;save();console.error(error);console.error('Original Chrome and raw-CDP session retained; do not attach Playwright.');process.exitCode=1;await new Promise(()=>{});}
}
run().catch(error=>{console.error(error);process.exitCode=1;});
