/* Compare an audited, source-owned model with the frozen pre-delivery city view.
 * Run with its map-case.json path, and --control for the prior state. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');
const caseFile = path.resolve(process.argv[2]);
const spec = JSON.parse(fs.readFileSync(caseFile));
const audit = process.env.MODEL_AUDIT_DIR || path.dirname(caseFile);
const ID = spec.id;
assert.equal(ID,'huangpu-longmen-village-gatehouse');
const PRIOR = spec.previous;
const control = process.argv.includes('--control');
const section = process.env.CITY_SECTION;
const desktopOnly = !['phone','touch'].includes(section);
const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(audit,'../../..');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const out = process.env.QA_OUTPUT_DIR || audit;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const bytes = f => fs.readFileSync(path.join(project,f));
const read = f => JSON.parse(bytes(f));
const review = read('source/precise/'+ID+'/footprint-review.json');
const contract = JSON.parse(fs.readFileSync(path.join(audit,'final-placement-contract.json')));
const selected = control ? PRIOR : ID;
const group = review.near_tiles[0];
const groupCases=[{id:group.id,tile:group,macro:review.frozen_macro},...review.adjacent_macro.near_tiles.map(tile=>({id:tile.id,tile,macro:review.adjacent_macro.frozen_macro}))];
const source=review.owners.find(r=>r.local_id===353);
const extraOwners=[];
const neighbors=review.owners.filter(r=>spec.neighbors.includes(r.local_id)).concat(review.adjacent_macro.owners.filter(r=>r.local_id===1726));
assert.deepEqual(neighbors.map(r=>r.local_id).sort((a,b)=>a-b),[353,1608,1726]);
assert.equal(contract.replacement_geometry,null);
assert.equal(contract.owner,undefined);
const point = (x,y) => {
  const h=contract.heading*Math.PI/180,k=6371008.8*Math.cos(contract.lat*Math.PI/180);
  const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
  return [contract.lng+east/k*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(contract.lat*Math.PI/180))+north/k))*180/Math.PI];
};
const camera = {center:point(...spec.front.center),elevation:spec.front.elevation,pitch:spec.front.pitch,bearing:contract.heading+spec.front.bearingOffset,zoom:spec.front.zoom,padding:{top:0,right:0,bottom:0,left:0}};
const result = {id:ID,mode:control?'frozen-before':'delivered',started:new Date().toISOString(),completed:false,server:base,
  desktopOnly,section,caseSha256:sha(fs.readFileSync(caseFile)),scriptSha256:sha(fs.readFileSync(__filename)),sourceCommit:review.baseline_commit,camera,views:[],screenshots:[],files:[],errors:[],warnings:[],failed:[]};
const reportPath=path.join(out,control?'control-browser.json':'main-browser.json');
const save=()=>fs.writeFileSync(reportPath,JSON.stringify(result,null,2)+'\n');
async function run() {
  fs.mkdirSync(out,{recursive:true});assert.ok(!fs.existsSync(reportPath),'Use a fresh output directory');
  const catalogFile='data/candidate-city-integrations.json';
  const frozenControl=control && process.env.QA_CONTROL_CATALOG;
  const controlRoot=frozenControl && path.dirname(path.dirname(path.resolve(frozenControl)));
  const data=frozenControl?fs.readFileSync(frozenControl):control?execFileSync('git',['show',review.baseline_commit+':projects/shanghai/'+catalogFile],{cwd:path.resolve(project,'../..')}):bytes(catalogFile);
  const catalog=JSON.parse(data),row=catalog.models.find(r=>r.id===ID);
  result.catalog={sha256:sha(data),count:catalog.resulting_city_count};
  if(frozenControl){
    assert.equal(result.catalog.sha256,process.env.QA_CONTROL_CATALOG_SHA256,'Frozen predecessor catalog SHA-260');
    assert.equal(result.catalog.count,Number(process.env.QA_CONTROL_CITY_COUNT),'Frozen predecessor catalog size');
  }
  assert.equal(Boolean(row),!control);
  if(row) for(const key of ['owner','source_feature_ids','replacement_geometry','collision_geometry','model_geometry_sha256'])
    assert.deepEqual(row[key],contract[key],key);
  result.bindings=Object.fromEntries(['src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','index.html','landmarks.html']
    .map(f=>[f,sha(frozenControl?fs.readFileSync(path.join(controlRoot,f)):bytes(f))]));
  const received=new Set();
  const browser=await chromium.launch({headless:false,env:{...process.env,DISPLAY:':53'},executablePath:'/usr/bin/chromium',args:['--disable-translate','--disable-features=Translate,TranslateUI','--lang=zh-CN','--ozone-platform=x11','--no-zygote','--single-process','--in-process-gpu','--window-position=0,0','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disable-background-networking','--disable-component-update','--disable-sync','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--max-old-space-size=300 --max-semi-space-size=4','--disk-cache-size=1048576','--disable-gpu-shader-disk-cache','--force-gpu-mem-available-mb=96',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const viewport=section==='details'?{width:510,height:460}:['desktop','architecture'].includes(section)?{width:850,height:620}:section==='closeups'?{width:720,height:600}:['before','distant'].includes(section)?{width:440,height:380}:{width:390,height:540};
  const page=await browser.newPage({viewport,locale:'zh-CN',deviceScaleFactor:1,ignoreHTTPSErrors:true,hasTouch:!desktopOnly});
  let calibrated=null; const calibrationView=page.viewportSize();
  try {
  const sizing=await page.context().newCDPSession(page);
  const nativeWindow=await sizing.send('Browser.getWindowForTarget');
  await sizing.send('Browser.setWindowBounds',{windowId:nativeWindow.windowId,bounds:{left:0,top:0,width:Math.max(520,calibrationView.width+30),height:calibrationView.height+120}});
  await sizing.detach();
  await page.setContent('<style>body{margin:0;background:rgb(22,17,43)}i,b{position:fixed;display:block;width:9px;height:9px}i{left:0;top:0;background:rgb(207,43,171)}b{right:0;bottom:0;background:rgb(31,211,93)}</style><i></i><b></b>');
  await page.bringToFront();
  const probe=path.join(out,'viewport-calibration-x11-root.png');
  const locate="from PIL import Image; import sys,json; im=Image.open(sys.argv[1]).convert('RGB'); a=im.load(); w,h=map(int,sys.argv[2:4]); print(json.dumps(next(([x,y] for y in range(im.height-h+1) for x in range(im.width-w+1) if a[x,y]==(207,43,171) and a[x+8,y+8]==(207,43,171) and a[x+w-1,y+h-1]==(31,211,93) and a[x+w-9,y+h-9]==(31,211,93)),None)))";
  for(let n=0;!calibrated&&n<15;n++){
    await new Promise(resolve=>setTimeout(resolve,120));
    execFileSync('import',['-silent','-display',':53','-window','root',probe],{env:{...process.env,DISPLAY:':53',MAGICK_THREAD_LIMIT:'1'},timeout:12000});
    calibrated=JSON.parse(execFileSync('python',['-c',locate,probe,String(calibrationView.width),String(calibrationView.height)],{encoding:'utf8'}));
  }
  assert.ok(calibrated,'Both opposite corners of the browser viewport must be visible');
  result.viewportCalibration={x:calibrated[0],y:calibrated[1],...calibrationView,display:':53',image:path.basename(probe),sha256:sha(fs.readFileSync(probe))};
  } catch(error){result.failure=error.stack;result.finished=new Date().toISOString();save();await browser.close();throw error;}
  await page.addInitScript(()=>{
     let api;
     Object.defineProperty(window,'maplibregl',{configurable:true,get(){return api},set(v){
       api=v;
       if(typeof v?.setWorkerCount==='function')v.setWorkerCount(1);
       if(typeof v?.Map==='function'){
         const OriginalMap=v.Map;
         v.Map=class extends OriginalMap {
           constructor(options){
             super({...options,pixelRatio:0.5,maxTileCacheSize:16});
             window.initialMapRendering={pixelRatio:this.getPixelRatio(),width:this.getCanvas().width,height:this.getCanvas().height};
           }
         };
       }
     }});
  });
  const physicalMemory=await page.evaluate(()=>navigator.deviceMemory??null);
  await page.addInitScript(()=>Object.defineProperty(navigator,'deviceMemory',{value:4,configurable:true}));
  result.browserProfile={physicalMemory,deviceMemoryProfileGiB:4,shadowQuality:'off',normalMaps:true};

  await page.addInitScript(() => {
    document.addEventListener('pointerdown', event => {
      const card=event.target.closest?.('.landmark-card');
      if(card) sessionStorage.setItem('qa260DirectoryPointer', JSON.stringify({id:card.dataset.landmark, type:event.pointerType, trusted:event.isTrusted}));
      if(event.target.closest?.('.maplibregl-canvas-container')) window.qa260MapPointer={type:event.pointerType,trusted:event.isTrusted,x:event.clientX,y:event.clientY};
    },true);
  });
  result.browser=browser.version();
  page.setDefaultTimeout(180000);
  if(control&&!frozenControl)await page.route('**/data/candidate-city-integrations.json*',r=>r.fulfill({contentType:'application/json',body:data}));
  page.on('pageerror',e=>result.errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')result.errors.push({url:m.location().url,message:m.text()});if(m.type()==='warning'&&m.text().includes('[Shanghai map]'))result.warnings.push(m.text());});
  page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')result.failed.push({url:r.url(),failure:r.failure()});});
  page.on('response',r=>{const u=new URL(r.url());if(r.status()>=400)result.failed.push({url:r.url(),status:r.status()});
    if(u.origin===new URL(base).origin&&r.status()===200)received.add(decodeURIComponent(u.pathname.slice(1)));});
  const priorityNear=groupCases.map(group=>'/'+group.macro+'/near/'+path.posix.basename(group.tile.file));
  const priorityFar=groupCases.map(group=>'/'+group.macro+'/far.glb');
  const lanes={tiles:{lastEnd:0,tail:Promise.resolve()},models:{lastEnd:0,tail:Promise.resolve()}};
  const completions=new Map();
  const timers=new Set();
  let shuttingDown=false;
  const delay=ms=>new Promise(done=>{
    if(shuttingDown){done();return;}
    const wake=()=>{clearTimeout(timer);timers.delete(wake);done();};
    const timer=setTimeout(wake,ms);timers.add(wake);
  });
  function complete(req,kind){
    const release=completions.get(req);if(release){completions.delete(req);release(kind);}
  }
  page.on('requestfinished',request=>complete(request,'requestfinished'));
  page.on('requestfailed',request=>complete(request,'requestfailed'));
  function shutDown(){
    shuttingDown=true;
    for(const wake of timers)wake();
    for(const request of [...completions.keys()])complete(request,'browser-closed');
  }
  page.once('close',shutDown);browser.once('disconnected',shutDown);
  result.transferTiming={priorityNear,priorityFar,pacing:'actual preceding transfer completion',
    otherFarFirstDelay:14000,otherFarSpacing:5000,otherNearFirstDelay:28000,
    otherNearSpacing:8500,otherModelFirstDelay:42000,otherModelSpacing:12000,requests:[]};
  async function continueReal(route){
    try{await route.continue();return true;}
    catch(e){if(!shuttingDown&&browser.isConnected()&&!page.isClosed()&&!String(e).includes('Invalid InterceptionId'))throw e;return false;}
  }
  const targetOrder=[...priorityFar.slice().reverse(),...priorityNear.slice().reverse()];
  const outcome=targetOrder.map(()=>{let release; const promise=new Promise(done=>release=done);return {promise,release};});
  const claimed=new Set();
  result.transferTiming.targetOrder=targetOrder;
  async function getProgress(){
    return page.evaluate(()=>{
      const scene=window.__SHANGHAI_APP__?.scene;
      if(!scene)return {scene:false};
      const s=scene.getStreamingState();
      return {scene:true,zoom:scene.map.getZoom(),moving:scene.map.isMoving(),
        macros:(s.active||[]).map(item=>({id:item.id,visible:item.visible})),
        detail:(s.detail?.active||[]).map(item=>item.id)};
    }).catch(error=>({error:String(error)}));
  }
  async function readSmall(url,method,range){
    return new Promise((resolve,reject)=>{
      const probe=require('node:http').request(url,{method,headers:range?{Range:'bytes=0-0'}:{}},reply=>{
        let count=0,first=null;
        reply.on('data',chunk=>{count+=chunk.length;if(first===null&&chunk.length)first=chunk[0];});
        reply.on('error',reject);
        reply.on('end',()=>resolve({status:reply.statusCode,length:Number(reply.headers['content-length']),
          contentRange:reply.headers['content-range']||null,bodyBytes:count,firstByte:first}));
      });
      probe.on('error',reject);probe.setTimeout(15000,()=>probe.destroy(new Error('Asset preflight timed out')));probe.end();
    });
  }
  async function targetTransfer(route,request,trace,pos){
    claimed.add(pos);
    try{
      if(pos>0){
        const prior=await Promise.race([outcome[pos-1].promise,new Promise(done=>{if(shuttingDown)done(false);else page.once('close',()=>done(false));})]);
        if(!prior || shuttingDown)return;
        await delay(2200);
      }
      if(shuttingDown || !browser.isConnected() || page.isClosed())return;
      trace.head=await readSmall(request.url(),'HEAD',false);
      assert.equal(trace.head.status,200);assert.ok(trace.head.length>0);
      trace.range=await readSmall(request.url(),'GET',true);
      assert.equal(trace.range.status,206);assert.equal(trace.range.contentRange,'bytes 0-0/'+trace.head.length);
      assert.equal(trace.range.bodyBytes,1);assert.equal(trace.range.firstByte,trace.pathname.endsWith('.gz')?31:103);
      trace.streamingBefore=await getProgress();
      if(shuttingDown || !browser.isConnected() || page.isClosed())return;
      const done=new Promise(resolve=>completions.set(request,resolve));
      trace.continued=Date.now();save();
      if(!(await continueReal(route)))complete(request,'continuation-canceled');
      trace.completion=await done;trace.completed=Date.now();
      if(trace.completion!=='requestfinished')return;
      const reply=await request.response();assert.ok(reply);trace.status=reply.status();trace.sizes=await request.sizes();
      trace.responseBytes=Number(await reply.headerValue('content-length'));trace.streamingAfter=await getProgress();
      assert.equal(trace.status,200);assert.equal(trace.responseBytes,trace.head.length);
      assert.equal(trace.sizes.responseBodySize,trace.head.length);
      trace.passed=true;
    }catch(error){trace.error=String(error);if(!shuttingDown&&browser.isConnected()&&!page.isClosed())throw error;}
    finally{completions.delete(request);outcome[pos].release(Boolean(trace.passed));save();}
  }
  async function routeModel(route){
    const request=route.request(),pathname=new URL(request.url()).pathname;
    const queued=Date.now(),macro=pathname.includes('/assets/city-detail/');
    const far=macro&&/\/far\.glb(?:\.gz)?$/i.test(pathname);
    const priority=macro?(far?priorityFar:priorityNear).some(tile=>pathname.endsWith(tile)||pathname.endsWith(tile+'.gz')):
      [ID,PRIOR,spec.adjacentModel].some(id=>id&&pathname.includes('/'+id+'/'));
    const trace={pathname,priority,queued};result.transferTiming.requests.push(trace);
    const target=targetOrder.findIndex(tile=>pathname.endsWith(tile)||pathname.endsWith(tile+'.gz'));
    if(control&&section==='before'&&target>=0&&!claimed.has(target)){
      await targetTransfer(route,request,trace,target);return;
    }
    if(priority){if(!shuttingDown){trace.continued=Date.now();await continueReal(route);}return;}
    const lane=macro?lanes.tiles:lanes.models;
    const firstDelay=macro?(far?14000:28000):42000,spacing=macro?(far?5000:8500):12000;
    const deliver=async()=>{
      if(shuttingDown || page.isClosed() || !browser.isConnected())return;
      const earliest=Math.max(queued+firstDelay,lane.lastEnd?lane.lastEnd+spacing:0);
      if(earliest>Date.now())await delay(earliest-Date.now());
      if(shuttingDown || page.isClosed() || !browser.isConnected())return;
      if(request.failure()){trace.completed=Date.now();trace.completion='failed-while-queued';return;}
      const actualEnd=new Promise(resolve=>completions.set(request,resolve));
      trace.previousResponseEnd=lane.lastEnd;trace.continued=Date.now();
      try{
        if(!(await continueReal(route)))complete(request,'continuation-canceled');
        trace.completion=await actualEnd;trace.completed=Date.now();lane.lastEnd=trace.completed;
      }finally{completions.delete(request);}
    };
    const queuedJob=lane.tail.then(deliver);lane.tail=queuedJob.catch(()=>{});await queuedJob;
  }
  await page.route(/\/assets\/city-detail\/macros\/[^?#]+\/(?:near\/[^?#]+|far)\.glb(?:\.gz)?(?:[?#]|$)/i,routeModel);
  await page.route(/\/assets\/models\/[^?#]+\.glb(?:\.gz)?(?:[?#]|$)/i,routeModel);
  async function configureBacking(){
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.map));
    const allocation=await page.evaluate(()=>{
      const scene=window.__SHANGHAI_APP__.scene;
      scene.setVisualQuality({shadows:false,surfaceNormals:true});
      const canvas=scene.map.getCanvas();
      return {initial:window.initialMapRendering,active:{pixelRatio:scene.map.getPixelRatio(),width:canvas.width,height:canvas.height}};
    });
    assert.equal(allocation.initial?.pixelRatio,0.5,'MapLibre initial framebuffer pixel ratio');
    assert.equal(allocation.active.pixelRatio,0.5,'Active map framebuffer pixel ratio');
    assert.ok(allocation.initial.width>0&&allocation.initial.height>0,'Initial map backing dimensions');
    result.browserProfile.mapRendering=allocation;
  }
  const context={id:ID,selected,control,macro:review.frozen_macro,group:group.id,groupCases,owner:source,extraOwners,neighbors,adjacentID:spec.adjacentModel};
  const manifest = row && read(row.candidate_manifest);
  async function settle(variant,detail=false){
    await page.waitForFunction(({selected,variant,detail,macro,group,groupCases,owner,control,adjacentID})=>{
      const s=window.__SHANGHAI_APP__?.scene;
      if(!s||s.map.isMoving())return false;
      const a=s.getLandmarkAssetState(selected);
      if(!control&&(!a?.visible||a.status!=='loaded'||(variant&&a.variant!==variant)))return false;
      if(!detail)return true;
      if(adjacentID&&!s.getLandmarkAssetState(adjacentID)?.visible)return false;
      const c=s.getCandidateIntegrationState(),t=s.getStreamingState();
      const activeGroups=groupCases.every(g=>t.detail.active.some(v=>v.id===g.macro+'/'+g.id));
      return activeGroups && t.active.some(t=>t.id===macro&&t.visible)
        &&c.vector.filter(v=>v.active).every(v=>!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer?.ready));
    },{...context,variant,detail},{polling:400,timeout:240000});
    await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>resolve());m.triggerRepaint();}));
  }
  async function view(name,variant,detail=false){
    await configureBacking();await settle(variant,detail);
    if(!control && !detail && spec.sourceSectionCount && name!=='map-distant'){
      await page.waitForFunction(({id,adjacentID,expected})=>{
        const scene=window.__SHANGHAI_APP__.scene;
        const section=scene.getCandidateIntegrationState().sourceSections.find(item=>item.id===id);
        const adjacentReady=!adjacentID||scene.getLandmarkAssetState(adjacentID)?.visible;
        return adjacentReady && section?.segments===expected;
      },{...context,expected:spec.sourceSectionCount},{polling:400,timeout:240000});
    }
    console.log('[map]',name);
    await page.waitForFunction(()=>{const app=window.__SHANGHAI_APP__,loader=document.querySelector('#loading');if(!app?.scene||!loader)return false;const css=getComputedStyle(loader);return !app.scene.map.isMoving()&&loader.classList.contains('loaded')&&css.opacity==='0'&&css.visibility==='hidden'&&css.pointerEvents==='none';},null,{timeout:240000,polling:300});
    const {state,frame}=await page.evaluate(({id,selected,macro,group,groupCases,owner,extraOwners,neighbors,adjacentID})=>new Promise(resolve=>{
      const map=window.__SHANGHAI_APP__.scene.map;
      map.once('render',()=>{
      const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,beacons=s.getBuildingBeaconState(),ci=s.getCandidateIntegrationState();
      const sourceState=o=>m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o.key.slice(9)});
      const label=beacons.labelPositions.find(z=>z.id===selected),gl=m.painter.context.gl;
      const canvas=m.getCanvas(),rect=canvas.getBoundingClientRect();
      const frame={png:canvas.toDataURL('image/png'),canvas:{x:rect.x,y:rect.y,w:rect.width,h:rect.height,width:canvas.width,height:canvas.height,pixelRatio:m.getPixelRatio()},bounds:{left:screenX,top:screenY,outerWidth,outerHeight,width:innerWidth,height:innerHeight,dpr:devicePixelRatio,focus:document.hasFocus(),href:location.href}};
      const state={route:location.hash,name:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],mode:app.mode,
        walkDisabled:document.querySelector('#start-walk').disabled,asset:s.getLandmarkAssetState(selected),source:sourceState(owner),streaming:s.getStreamingState().detail.active.map(item=>item.id),
        ...(extraOwners.length?{extraOwnerStates:extraOwners.map(o=>({local_id:o.local_id,state:sourceState(o)}))}:{}),
        adjacentAsset:adjacentID?s.getLandmarkAssetState(adjacentID):undefined,neighbors:neighbors.map(o=>({local_id:o.local_id,state:sourceState(o)})),sections:ci.sourceSections?.filter(x=>x.id===id)??[],clip:ci.clips.find(c=>c.id===id)||null,
        group:ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group)||null,
        ...(groupCases.length>1?{streamedGroups:groupCases.map(g=>ci.shader.ownerScopedSources.find(v=>v.id===g.macro+'/'+g.id)||null)}:{}),shader:{triangles:ci.shader.triangles,limit:ci.shader.triangleLimit,macroTextures:ci.shader.macroTextures??null},
        labels:beacons.count,pick:label?s.pickBuildingBeacon(label):null,camera:{center:m.getCenter(),elevation:m.getCenterElevation(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom()},
        glError:gl.getError(),contextLost:gl.isContextLost()};
      resolve({state,frame});
      });map.triggerRepaint();
    }),context);
    result.views.push({view:name,...state});save();
    assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.equal(state.labels,catalog.resulting_city_count);
    const route=new URLSearchParams(state.route.slice(1));
    if(control){
      assert.equal(route.get('landmark'),null);
      assert.ok(Math.abs(Number(route.get('lng'))-contract.lng)<.000001 && Math.abs(Number(route.get('lat'))-contract.lat)<.000001);
    }else{
      assert.equal(route.get('landmark'),selected);
      assert.equal(state.asset.id,selected);
      if(!['architecture','closeups'].includes(section))assert.equal(state.pick,selected);
      else if(state.pick!==null)assert.equal(state.pick,selected);
    }

    assert.equal(state.clip,null);
    assert.deepEqual(state.sections,[]);
    for(const neighbor of state.neighbors){
      assert.notEqual(neighbor.state.candidateModel,true,'Ordinary source claimed by the candidate: '+neighbor.local_id);
      if(detail){
        const group=state.streamedGroups.find(item=>item?.feature_local_ids.includes(neighbor.local_id));
        assert.ok(group,'No loaded ordinary macro mesh for '+neighbor.local_id);
        const ownerMacro=neighbor.local_id===1726?review.adjacent_macro.frozen_macro:review.frozen_macro;
        assert.equal(group.macro_id,ownerMacro);
        assert.ok(state.streaming.includes(group.id));
        assert.ok(!group.clip_feature_local_ids.includes(neighbor.local_id),'Candidate clip overlaps '+neighbor.local_id);
        assert.equal(neighbor.state.localModel,true,'Vector shell suppressed for visible ordinary mesh '+neighbor.local_id);
      }
    }
    if(detail)for(const g of groupCases)assert.ok(state.streaming.includes(g.macro+'/'+g.id));
    if(!control){
      assert.equal(state.name,row.name);assert.equal(state.mode,'overview');
      const variant=state.asset.variant==='full'?'web':'lod';
      assert.equal(state.asset.verifiedAsset.sha256,row.assets[variant].sha256);
      assert.equal(state.asset.triangles,row.assets[variant].triangles);
      assert.deepEqual(state.asset.anchor,[row.lng,row.lat]);assert.equal(state.asset.heading,row.heading);
    }
      const bounds=frame.bounds;
      assert.equal(bounds.dpr,1);
      assert.ok(bounds.focus&&bounds.href.startsWith(base));
      const source=path.join(out,name+'-x11-root.png');
      assert.deepEqual([bounds.width,bounds.height],[calibrationView.width,calibrationView.height]);
      const x=calibrated[0];
      const y=calibrated[1];
      const rect=bounds.width+'x'+bounds.height+'+'+x+'+'+y;
      const commandEnv={...process.env,DISPLAY:':53',MAGICK_THREAD_LIMIT:'1',OMP_NUM_THREADS:'1'};
      execFileSync('import',['-silent','-display',':53','-window','root',source],{env:commandEnv,timeout:12500});
      let root=fs.readFileSync(source);
      assert.ok(x+bounds.width<=root.readUInt32BE(16)&&y+bounds.height<=root.readUInt32BE(20),'Viewport outside recorded X display '+JSON.stringify(bounds));
      const target=path.join(out,name+'.png');
      execFileSync('convert',[source,'-crop',rect,'+repage','PNG24:'+target],{env:commandEnv,timeout:10000});
      let image=fs.readFileSync(target);
      if(['architecture','closeups'].includes(section)&&result.screenshots.length){
        const last=path.join(out,result.screenshots.at(-1).file);
        const pixelDigest=f=>sha(execFileSync('convert',[f,'-strip','-depth','8','rgb:-'],{maxBuffer:8*1024*1024}));
        const previous=pixelDigest(last);
        for(let n=0;pixelDigest(target)===previous&&n<18;n++){
          await new Promise(r=>setTimeout(r,200));
          execFileSync('import',['-silent','-display',':53','-window','root',source],{env:commandEnv,timeout:12500});
          execFileSync('convert',[source,'-crop',rect,'+repage','PNG24:'+target],{env:commandEnv,timeout:10000});
        }
        root=fs.readFileSync(source);image=fs.readFileSync(target);
        assert.notEqual(pixelDigest(target),previous,'Two camera presentations retained the same viewport');
      }
      assert.ok(image.length>1000&&image.readUInt32BE(16)===bounds.width&&image.readUInt32BE(20)===bounds.height);
      result.screenshots.push({file:name+'.png',bytes:image.length,sha256:sha(image)});
      const webgl=Buffer.from(frame.png.split(',')[1],'base64'),filename=name+'-webgl.png';
      assert.equal(webgl.readUInt32BE(16),frame.canvas.width);
      assert.equal(webgl.readUInt32BE(20),frame.canvas.height);assert.ok(webgl.length>1000);
      fs.writeFileSync(path.join(out,filename),webgl);
      (result.webglCaptures??=[]).push({file:filename,sha256:sha(webgl),bytes:webgl.length,...frame.canvas});
      (result.displayCaptures??=[]).push({display:':53',bounds,rectangle:rect,displayImage:path.basename(source),displayImageSha256:sha(root)});
      save();

  }

  async function clickBeacon(id,prev,center,report) {
    await page.goto(new URL('index.html#landmark='+prev+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()),null,{timeout:180000});
    let visible=false;
    const trials=[];
    for(const [zoom,left,bottom] of [[19.65,0,0],[19.65,120,140],[18.4,160,100],[16.4,0,0],[19.3,100,170]]){
      await jump({center,zoom,pitch:0,bearing:0,elevation:0,padding:{left,right:0,top:0,bottom}});
      try {
        await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene;const p=s.getBuildingBeaconState().labelPositions.find(x=>x.id===id||x.memberIds?.includes(id));if(!p||s.pickBuildingBeacon(p)!==p.id)return false;const b=s.map.getCanvas().getBoundingClientRect(),el=document.elementFromPoint(b.x+p.x,b.y+p.y);return el===s.map.getCanvas()||el?.closest('.maplibregl-canvas-container');},id,{polling:200,timeout:6000});
        trials.push({zoom,left,bottom,visible:true}); visible=true;break;
      }catch(error){if(error.name!=='TimeoutError')throw error;trials.push({zoom,left,bottom,visible:false});}
    }
    report.beaconCameraTrials=trials;save();assert.ok(visible,'No visible trusted beacon target in the measured map');
    const action=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,p=s.getBuildingBeaconState().labelPositions.find(x=>x.id===id||x.memberIds?.includes(id)),b=s.map.getCanvas().getBoundingClientRect();return {x:b.x+p.x,y:b.y+p.y,id:p.id,group:p.memberIds?.length>0,previous:location.hash,viewport:[innerWidth,innerHeight]};},id);
    assert.equal(new URLSearchParams(action.previous.slice(1)).get('landmark'),prev);
    const touch=section==='touch';
    if(touch)await page.touchscreen.tap(action.x,action.y);else await page.mouse.click(action.x,action.y);
    if(action.group){const choice=page.locator('dialog.beacon-group-picker[open] [data-landmark="'+id+'"]');if(touch)await choice.tap();else await choice.click();}
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id,{timeout:180000});
    const pointer=await page.evaluate(()=>window.qa260MapPointer);assert.ok(pointer?.trusted);assert.equal(pointer.type,touch?'touch':'mouse');
    report.realBeacon={...action,pointer,landed:id,action:touch?'physical canvas touch':'physical canvas mouse click'};save();
  }
  async function jump(camera){
    await configureBacking();
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
  }
  async function closePanel(){const p=page.locator('#panel-toggle');if(await p.getAttribute('aria-expanded')==='true')await p.click();}
  async function receipt(file,rec,seen){
    if(seen)assert.ok(received.has(file),'Scene never downloaded '+file);
    const resp=await page.request.get(new URL(file,base).href),data=await resp.body();
    assert.equal(resp.status(),200);assert.equal(data.length,rec.bytes);assert.equal(sha(data),rec.sha256);
    result.files.push({file,bytes:data.length,sha256:sha(data),loadedByScene:received.has(file)});
  }
  try {
    if(control){
      await page.goto(base+'index.html#lng='+contract.lng+'&lat='+contract.lat+'&mode=overview',{waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));await closePanel();await jump(camera);await view('map-before',null,true);
      result.beforeGround=await page.evaluate(async probes=>{
        const scene=window.__SHANGHAI_APP__.scene;await scene.waitForData(10000);
        return {points:probes.map(p=>({...p,found:scene.collisionAt(...p.position)})),
          collision:scene.getCollisionState?.()??null,route:location.hash};
      },spec.ground.map(w=>({name:w.name,position:point(...w.xy)})));
      assert.equal(result.beforeGround.points.length,51);
      assert.ok(result.beforeGround.points.every(p=>p.found===null||typeof p.found==='string'));
      save();
    }else{
      if(section==='desktop'||section==='phone'){
        const mobile=section==='phone';
        assert.deepEqual(page.viewportSize(),viewport);
        await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
        assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
        const card=page.locator('#district-'+row.districtId+' [data-landmark="'+ID+'"] .card-foot a[href="index.html#landmark='+ID+'&mode=overview"]');
        if(mobile) await card.tap(); else await card.click();
        await view(mobile?'map-mobile':'map-desktop','full',true);
        result.directoryPointer=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('qa260DirectoryPointer')));assert.ok(result.directoryPointer?.trusted);assert.equal(result.directoryPointer.id,ID);assert.equal(result.directoryPointer.type,mobile?'touch':'mouse');
      }
      if(section==='details'||section==='touch'){
        await clickBeacon(ID,PRIOR,[contract.lng,contract.lat],result);
        await view(section==='touch'?'map-touch-beacon-return':'map-beacon-return','full',true);
      }
      if(section==='architecture'){
        await page.goto(base+'index.html#landmark='+ID+'&mode=overview',{waitUntil:'domcontentloaded'});
        await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));
        await closePanel();await jump(camera);await view('map-street-facade','full',true);
        await jump({...camera,center:point(...spec.roof.center),bearing:contract.heading+spec.roof.bearingOffset,elevation:spec.roof.elevation,pitch:spec.roof.pitch,zoom:spec.roof.zoom});
        await view('map-roof','full',true);
      result.ground=await page.evaluate(async probes=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(10000);
        return probes.map(p=>({...p,found:s.collisionAt(...p.position)}));},[
        ...spec.ground.map(w=>({name:w.name,position:point(...w.xy),expected:w.expected})),
        ...neighbors.filter(n=>spec.neighborGround[n.local_id]).map(n=>({name:'retained neighbor '+n.local_id,position:spec.neighborGround[n.local_id],expected:'building'}))]);
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);
      }
      if(section==='closeups'){
        assert.deepEqual(page.viewportSize(),viewport);
        await page.goto(base+'index.html#landmark='+ID+'&mode=overview',{waitUntil:'domcontentloaded'});
        await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));
        await closePanel();
        await jump({...camera,center:point(0,.0),elevation:4.9,pitch:66,zoom:21.35,bearing:contract.heading+2});
        await view('map-arched-passage-and-recessed-plaque','full',true);
        await jump({...camera,center:point(0,.4),elevation:10.9,pitch:59,zoom:21.12,bearing:contract.heading+5});
        await view('map-red-casements-year-and-tiled-eaves','full',true);
      }
      if(section==='distant'){
        assert.deepEqual(page.viewportSize(),viewport);
        await page.goto(base+'index.html#landmark='+ID+'&mode=overview',{waitUntil:'domcontentloaded'});
        await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));
        await jump({...camera,zoom:15.5,pitch:32,elevation:0});await view('map-distant','distant');
        for(const [role,item] of Object.entries(manifest.assets))
          await receipt(path.posix.join(path.posix.dirname(row.candidate_manifest),item.file),item,role==='lod');
      }
      if(section==='architecture')await receipt(path.posix.join(path.posix.dirname(row.candidate_manifest),manifest.assets.full.file),manifest.assets.full,true);
      assert.equal(sha(bytes(catalogFile)),result.catalog.sha256);
      for(const [f,sum] of Object.entries(result.bindings))assert.equal(sha(bytes(f)),sum,'Changed input '+f);
    }
    if(frozenControl){
      await receipt(catalogFile,{bytes:data.length,sha256:result.catalog.sha256},true);
      for(const [f,digest] of Object.entries(result.bindings)){
        const size=fs.statSync(path.join(controlRoot,f)).size;
        await receipt(f,{bytes:size,sha256:digest},false);
      }
    }
    for(const rec of [...review.frozen_bindings,...review.adjacent_macro.frozen_bindings].filter(r=>r.repository_path.endsWith('/far.glb')||groupCases.some(g=>r.repository_path.endsWith('/'+g.tile.file))))
      await receipt(rec.repository_path.replace('projects/shanghai/',''),rec,control||section==='architecture'||(section==='distant'&&rec.repository_path.endsWith('/far.glb')));
    assert.deepEqual(result.errors,[]);assert.deepEqual(result.failed,[]);result.completed=true;
   }catch(e){result.failure=e.stack;result.failureState=await page.evaluate(({id,selected,group,macro})=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return {body:document.body.innerText.slice(0,1000)};
      return {route:location.hash,moving:s.map.isMoving(),stream:s.getStreamingState(),camera:{center:s.map.getCenter(),zoom:s.map.getZoom()},active:s.getLandmarkAssetState(selected),selectedTarget:s.getLandmarkAssetState(id),group:s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.id===macro+'/'+group),labels:s.getBuildingBeaconState().viewportLabelCount};
    },context).catch(err=>({error:String(err)}));throw e;}
  finally{await browser.close();result.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
