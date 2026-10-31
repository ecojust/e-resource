/* Resume only phone/beacon QA in the original Chrome. MIT. No Playwright attach. */
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{createHash}=require('node:crypto');
const PROJECT=path.resolve(__dirname,'../../..'),ID='huangpu-xinxin-company',FROM='huangpu-new-wing-on-company';
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const sameIds=(a,b)=>assert.deepEqual([...a].sort(),[...b].sort());
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function connect(url){
 const ws=new WebSocket(url);await new Promise((ok,no)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',no,{once:true});});let serial=0;const pending=new Map(),listeners=[];
 ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(m.error)p?.reject(Error(JSON.stringify(m.error)));else p?.resolve(m.result);}else for(const f of listeners)f(m);});
 return {ws,on:f=>listeners.push(f),call:(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));})};
}
async function main(){
 assert(process.argv.includes('--run'),'Pass --run only to resume the retained original Chrome.');
 const initialFile=path.join(__dirname,'browser-initial-run.json'),initial=read(initialFile),report=structuredClone(initial);
 assert.equal(initial.completed,false);assert.equal(initial.captures.length,5);assert(initial.failure?.includes('assertFraming'));
 for(const binding of [initial.catalog,initial.manifest,initial.footprint,initial.qaScript])assert.equal(sha(fs.readFileSync(path.join(PROJECT,binding.file))),binding.sha256,binding.file);
 const catalog=read(path.join(PROJECT,initial.catalog.file)),row=catalog.models.find(r=>r.id===ID);assert(row);
 const pages=await fetch('http://127.0.0.1:9223/json/list').then(r=>r.json()),target=pages.find(p=>p.type==='page'&&p.url.includes('/index.html'));
 assert(target,'Original main-map page must still exist; this script does not create a new browser.');
 const cdp=await connect(target.webSocketDebuggerUrl),newEvents={errors:[],warnings:[],http:[]};let phase='resize-recovery';
 cdp.on(m=>{
  if(m.method==='Runtime.exceptionThrown')newEvents.errors.push({phase,source:'Runtime.exceptionThrown',message:m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text});
  if(m.method==='Runtime.consoleAPICalled'){
   const t=m.params.type,args=m.params.args.map(a=>a.value??a.description??'').join(' ');if(t==='error')newEvents.errors.push({phase,source:'console',message:args});if(t==='warning'||t==='warn')newEvents.warnings.push({phase,source:'console',message:args});
  }
  if(m.method==='Log.entryAdded'){
   const e=m.params.entry;if(e.level==='error')newEvents.errors.push({phase,source:e.source,message:e.text});if(e.level==='warning')newEvents.warnings.push({phase,source:e.source,message:e.text});
  }
  if(m.method==='Network.responseReceived'&&m.params.response.status>=400)newEvents.http.push({phase,status:m.params.response.status,url:m.params.response.url});
 });
 const evaluate=async expression=>{const r=await cdp.call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});assert(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result?.value;};
 const invoke=(fn,arg)=>evaluate(`(${fn.toString()})(${JSON.stringify(arg)})`);
 await cdp.call('Runtime.enable');await cdp.call('Log.enable');await cdp.call('Network.enable');
 report.recoveredFailures=[{phase:'initial mobile resize',error:initial.failure,observedViewport:initial.global.defaultMobile.viewport,observedPadding:initial.global.defaultMobile.map.padding,reason:'The DOM had resized to 390px before the MapLibre canvas width changed from 960px. The overview fit combined those two layouts. Wait for canvas/transform/UI geometry to converge across rendered frames, then call the unchanged production selectPlace again.',productionCodeChanged:false}];
 delete report.failure;delete report.global.defaultMobile;
 report.executionSegments=[{kind:'initial-run',script:initial.qaScript,report:{file:'data/audit/xinxin-company-v1/browser-initial-run.json',sha256:sha(fs.readFileSync(initialFile))},captures:initial.captures.map(x=>x.file),acceptedScope:'Auxiliary 3 views, real assets/directory and stable desktop/northern-body captures; mobile size assertion retained as recovered failure.'}];
 const resumeBinding={file:path.relative(PROJECT,__filename),sha256:sha(fs.readFileSync(__filename))};
 report.executionSegments.push({kind:'same-browser-resume',script:resumeBinding,method:'Raw CDP to the same page. No second browser, no Playwright connect, no source hiding or production-code edits.',captures:[],events:newEvents});
 for(const c of report.captures)c.captureScript=initial.qaScript;
 const save=()=>fs.writeFileSync(path.join(__dirname,'browser.json'),JSON.stringify(report,null,2)+'\n');
 const viewportReady=async(width,height)=>invoke(async([width,height])=>{
  const a=window.__SHANGHAI_APP__,m=a.scene.map;
  const state=()=>{const rect=s=>document.querySelector(s)?.getBoundingClientRect().toJSON();return {inner:[innerWidth,innerHeight],canvas:[m.getCanvas().clientWidth,m.getCanvas().clientHeight],transform:[m.transform.width,m.transform.height],tools:rect('.map-tools'),card:rect('#location-card'),legend:rect('#building-beacon-legend')};};
  const dimensions=s=>[s.inner,s.canvas,s.transform].every(v=>v[0]===width&&v[1]===height);
  const fingerprint=s=>JSON.stringify([s.inner,s.canvas,s.transform,...[s.tools,s.card,s.legend].map(r=>r&&[r.left,r.top,r.right,r.bottom].map(v=>Math.round(v*100)/100))]);
  const deadline=performance.now()+180000;let previous=null,consecutive=0;
  while(performance.now()<deadline){await new Promise(r=>{m.once('render',r);m.triggerRepaint();});const s=state();const same=dimensions(s)&&fingerprint(s)===previous;consecutive=same?consecutive+1:0;previous=fingerprint(s);if(consecutive>=2)return s;}
  throw Error('Responsive canvas/transform/UI layout failed to stabilize');
 },[width,height]);
 const select=async id=>invoke(async id=>{const a=window.__SHANGHAI_APP__;await a.selectPlace(a.landmarks.find(p=>p.id===id),{mode:'overview'});return true;},id);
 const settle=async(requireReplacement)=>invoke(async({requireReplacement,macro,id})=>{
  const a=window.__SHANGHAI_APP__,m=a.scene.map;
  const read=()=>{const s=a.scene.getStreamingState(),b=a.scene.getBuildingBeaconState(),c=a.scene.getCandidateIntegrationState(),v=c.vector.filter(r=>r.active);const owner=m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id});const city={loading:s.loading,queued:s.queued,pendingStates:s.pendingStates,detailLoading:s.detail.loading,ownerMacroVisible:s.active.some(r=>r.id===macro&&r.visible),active:s.active.map(r=>[r.id,r.visible]),detailActive:s.detail.active.map(r=>[r.id,r.triangles])};return {ready:!m.isMoving()&&m.areTilesLoaded()&&city.loading===0&&city.queued===0&&city.pendingStates===0&&city.detailLoading===0&&b.sourceIds.every(id=>m.isSourceLoaded(id))&&(!requireReplacement||(city.ownerMacroVisible&&(owner.localModel===true||owner.candidateModel===true)&&v.every(x=>!x.pending&&!x.residualLayer?.busy&&(!x.partialIDs||x.residualLayer?.ready)))),city,owner,fingerprint:JSON.stringify({city,beacons:b.revision,shader:requireReplacement?c.shader:null,vector:requireReplacement?v.map(x=>[x.source,x.coveredIDs,x.partialIDs,x.pending,x.residualLayer?.generation]):null})};};
  const deadline=performance.now()+240000;let previous=null,n=0;
  while(performance.now()<deadline){await new Promise(r=>{m.once('render',r);m.triggerRepaint();});const s=read();n=s.ready&&s.fingerprint===previous?n+1:0;previous=s.fingerprint;if(n>=2)return s;}
  throw Error('City/beacon state did not reach rendered stability');
 },{requireReplacement,macro:row.owner.macro_id,id:row.source_feature_ids.building[0]});
 const capture=async(label,state,size)=>{
  const view=await evaluate('[innerWidth,innerHeight]');assert.deepEqual(view,size);
  const suffix=sha(fs.readFileSync(__filename)+report.catalog.sha256+report.manifest.sha256).slice(0,8),file=`browser-${label}-29494443-resume-${suffix}.png`;
  const data=Buffer.from((await cdp.call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false})).data,'base64');assert.deepEqual([data.readUInt32BE(16),data.readUInt32BE(20)],size);fs.writeFileSync(path.join(__dirname,file),data);
  const item={file,bytes:data.length,sha256:sha(data),viewport:size,state,sourceBindings:structuredClone(report.sourceBindings),captureScript:resumeBinding,visualAcceptance:'pending actual image review'};report.captures.push(item);report.executionSegments[1].captures.push(file);save();console.log('SAVED',file);
 };
 try{
  report.global.mobileResizeRecovery=await viewportReady(390,844);await select(ID);report.global.mobileSteady=await settle(true);
  const phone=await invoke(({row})=>{
   const a=window.__SHANGHAI_APP__,m=a.scene.map,anchor=maplibregl.MercatorCoordinate.fromLngLat([row.lng,row.lat],row.altitude||0),u=anchor.meterInMercatorCoordinateUnits(),t=row.heading*Math.PI/180;const worldCorners=[];
   for(const x of [row.bounds_glb.min[0],row.bounds_glb.max[0]])for(const y of [row.bounds_glb.min[1],row.bounds_glb.max[1]])for(const z of [row.bounds_glb.min[2],row.bounds_glb.max[2]]){const q=new maplibregl.MercatorCoordinate(anchor.x+(Math.cos(t)*x-Math.sin(t)*z)*row.scale*u,anchor.y+(Math.sin(t)*x+Math.cos(t)*z)*row.scale*u,anchor.z+y*row.scale*u),p=m.transform.coordinatePoint(q,q.toAltitude(),m.transform._pixelMatrix3D);worldCorners.push({x:p.x,y:p.y});}
   return {hash:location.hash,title:document.querySelector('#location-name').textContent,mode:a.mode,viewport:[innerWidth,innerHeight],canvas:[m.getCanvas().clientWidth,m.getCanvas().clientHeight],map:{center:m.getCenter(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),padding:m.getPadding(),elevation:m.transform.elevation,centerClampedToGround:m.getCenterClampedToGround()},asset:a.scene.getLandmarkAssetState(row.id),worldCorners,walkDisabled:document.querySelector('#walk-mode').disabled&&document.querySelector('#start-walk').disabled,streaming:a.scene.getStreamingState(),candidate:a.scene.getCandidateIntegrationState(),beacons:a.scene.getBuildingBeaconState()};
  },{row});
  assert.deepEqual(phone.canvas,[390,844]);assert.equal(phone.asset.status,'loaded');assert(phone.asset.visible);assert.equal(phone.mode,'overview');assert(phone.walkDisabled);assert.equal(phone.map.centerClampedToGround,false);assert.equal(phone.map.pitch,35);assert(Math.abs(phone.map.bearing-row.overviewBearing)<1e-8);
  assert.equal(phone.asset.verifiedAsset.sha256,row.assets[phone.asset.variant==='full'?'web':'lod'].sha256);
  const p=phone.map.padding;assert(p.right<100);for(const q of phone.worldCorners)assert(q.x>=p.left-.5&&q.x<=390-p.right+.5&&q.y>=p.top-.5&&q.y<=844-p.bottom+.5,JSON.stringify({q,p}));
  report.global.defaultMobile=phone;await capture('global-default-mobile',phone,[390,844]);
  phase='beacons';await cdp.call('Emulation.setDeviceMetricsOverride',{width:320,height:568,screenWidth:320,screenHeight:568,deviceScaleFactor:1,mobile:false});report.beaconsResizeRecovery=await viewportReady(320,568);await select(FROM);
  await evaluate("(()=>{const a=window.__SHANGHAI_APP__,m=a.scene.map;window.__qaResumeBounds=m.getMaxBounds()?.toArray()||null;a.scene.setVisualQuality({shadows:false,surfaceNormals:true});m.setMaxBounds(null);m.setCenterClampedToGround(true);m.jumpTo({center:[121.45,31.20],zoom:8,pitch:0,bearing:0,elevation:0,padding:{top:0,right:0,bottom:0,left:0}});a.scene.refreshBuildingBeacons();return true})()");
  const beaconSteady=await settle(false);
  const b=await evaluate("(()=>{const a=window.__SHANGHAI_APP__,m=a.scene.map,s=a.scene.getBuildingBeaconState(),rect=q=>document.querySelector(q)?.getBoundingClientRect().toJSON();return {viewport:[innerWidth,innerHeight],canvas:[m.getCanvas().clientWidth,m.getCanvas().clientHeight],state:s,map:{center:m.getCenter(),zoom:m.getZoom(),padding:m.getPadding()},sources:s.sourceIds.map(id=>({id,ids:m.getSource(id).serialize().data.features.map(f=>f.properties.id)})),picks:s.labelPositions.map(p=>({id:p.id,hit:a.scene.pickBuildingBeacon({x:p.x,y:p.y})})),ui:{card:rect('#location-card'),tools:rect('.map-tools'),legend:rect('#building-beacon-legend')},allSpritesPresent:s.spriteIds.every(id=>m.hasImage(id))}})()");
  assert.deepEqual(b.viewport,[320,568]);assert.deepEqual(b.canvas,b.viewport);assert.equal(b.map.zoom,8);assert.equal(b.state.count,72);assert.equal(b.state.districtCount,16);assert.equal(b.state.viewportLabelCount,72);assert.equal(b.state.overlapFallbackCount,0);assert.equal(b.state.labelMode,'numbers');assert.equal(b.state.labelPixelSize,12);assert(b.allSpritesPresent);
  sameIds(b.state.ids,report.directory.cards.map(r=>r.id));for(const s of b.sources)sameIds(s.ids,b.state.ids);for(const p of b.picks)assert.equal(p.hit,p.id);
  const labels=b.state.labelPositions;sameIds(labels.map(p=>p.id),b.state.ids);
  for(let i=0;i<labels.length;i++){const p=labels[i];assert([22,24].includes(p.width)&&p.height===20);assert(p.x-p.width/2>=0&&p.x+p.width/2<=320&&p.y-p.height/2>=0&&p.y+p.height/2<=568);for(const r of Object.values(b.ui))if(r)assert(p.x+p.width/2<=r.left+.1||p.x-p.width/2>=r.right-.1||p.y+p.height/2<=r.top+.1||p.y-p.height/2>=r.bottom-.1);for(const q of labels.slice(i+1))assert(Math.abs(p.x-q.x)>=(p.width+q.width)/2-.1||Math.abs(p.y-q.y)>=(p.height+q.height)/2-.1);}
  report.beacons={...b,steady:beaconSteady,quality:'Shadows disabled only for the dense marker view. Buildings remain enabled. Bounds temporarily removed for exact zoom8 and restored after touch.',compactWidths:[...new Set(labels.map(p=>p.width))]};await capture('beacons-320-city-72',report.beacons,[320,568]);
  const route=()=>evaluate("(()=>({hash:location.hash,title:document.querySelector('#location-name').textContent,center:window.__SHANGHAI_APP__.scene.map.getCenter(),asset:window.__SHANGHAI_APP__.scene.getLandmarkAssetState('huangpu-xinxin-company')}))()");
  const before=await route();assert.equal(new URLSearchParams(before.hash.slice(1)).get('landmark'),FROM);const point=labels.find(p=>p.id===ID);assert(point);
  await cdp.call('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1});await cdp.call('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{id:1,x:point.x,y:point.y}]});await cdp.call('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await invoke(async id=>{const limit=performance.now()+60000;while(performance.now()<limit){const a=window.__SHANGHAI_APP__,s=a.scene.getLandmarkAssetState(id);if(new URLSearchParams(location.hash.slice(1)).get('landmark')===id&&document.querySelector('#location-name').textContent===a.landmarks.find(r=>r.id===id).name&&s.visible&&s.status==='loaded')return true;await new Promise(r=>setTimeout(r,100));}throw Error('Touch did not select and show target');},ID);
  const after=await route();assert.notEqual(before.hash,after.hash);assert.notEqual(before.title,after.title);assert.notDeepEqual(before.center,after.center);report.beacons.touch={method:'native CDP touchStart/touchEnd',id:ID,point:[point.x,point.y],before,after,changedDestination:true,targetAssetVisibleAfterTouch:true};
  await evaluate("(()=>{window.__SHANGHAI_APP__.scene.map.setMaxBounds(window.__qaResumeBounds);return true})()");
  // The initial runner is idle in its retained-failure catch. Let its event
  // listeners drain before freezing the merged report; it never replays steps.
  const pidFile=process.env.QA_INITIAL_PID_FILE||'/workspace/xinxin-qa-paused-pid',pid=Number(fs.readFileSync(pidFile,'utf8'));process.kill(pid,'SIGCONT');await delay(1200);
  await evaluate('true');await delay(300);
  const drained=read(path.join(__dirname,'browser.json'));report.originalRunnerDrain={pid,resumed:true,savedErrors:drained.errors,savedWarnings:drained.warnings,savedHTTP:drained.http,note:'Raw Runtime/Log domains also replayed buffered console entries and monitored continuation; no Playwright reconnect was used.'};
  for(const key of ['errors','warnings','http']){report[key]=[...initial[key],...drained[key],...newEvents[key]];assert.deepEqual(report[key],[],key);}
  report.completed=true;report.visualAcceptance='Seven actual captures complete in the same browser: five from the frozen initial script and two from this explicit continuation. Pixel review is separate.';save();console.log('COMPLETE same-browser phone and 72-beacon continuation');
  const browser=await fetch('http://127.0.0.1:9223/json/version').then(r=>r.json()),control=await connect(browser.webSocketDebuggerUrl);await control.call('Browser.close').catch(()=>{});control.ws.close();cdp.ws.close();process.kill(pid,'SIGTERM');
 }catch(error){report.continuationFailure=error.stack;report.completed=false;save();console.error(error);cdp.ws.close();process.exitCode=1;console.error('Original Chrome retained for diagnosis; do not attach Playwright.');}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
