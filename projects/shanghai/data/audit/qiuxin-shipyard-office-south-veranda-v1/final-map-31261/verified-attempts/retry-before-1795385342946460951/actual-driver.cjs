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
const audit = path.dirname(caseFile);
const ID = spec.id;
const PRIOR = spec.previous;
const control = process.argv.includes('--control');
const phase=process.argv[3];
const phone=['phone','touch'].includes(phase);
const desktopOnly=!phone;
assert.ok(['before','phone','desktop','architecture','mouse','touch','distant'].includes(phase));

const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(audit,'../../..');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const out = process.env.QA_OUTPUT_DIR || audit;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const bytes = f => fs.readFileSync(path.join(project,f));
const read = f => JSON.parse(bytes(f));
const review = read('source/precise/'+ID+'/footprint-review.json');
const contract = JSON.parse(fs.readFileSync(path.join(audit,'final-placement-contract.json')));
const selected = control ? PRIOR : ID;
const group = review.near_tiles.find(g=>g.feature_local_ids.includes(contract.owner.feature_local_id));
const source = review.owners.find(r => r.local_id===contract.owner.feature_local_id);
const addedOwners=spec.addedOwners??[source.local_id];
const declaredOwners=(contract.owners??[contract.owner]).map(o=>o.feature_local_id);
assert.deepEqual([...addedOwners].sort((a,b)=>a-b),[...declaredOwners].sort((a,b)=>a-b));
assert.ok(addedOwners.every(id=>group.feature_local_ids.includes(id)),'Expected every added owner in the tested streamed group');
const extraOwners=review.owners.filter(r=>r.local_id!==source.local_id&&addedOwners.includes(r.local_id));
const neighbors = review.owners.filter(r=>spec.neighbors.includes(r.local_id));
const point = (x,y) => {
  const h=contract.heading*Math.PI/180,k=6371008.8*Math.cos(contract.lat*Math.PI/180);
  const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
  return [contract.lng+east/k*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(contract.lat*Math.PI/180))+north/k))*180/Math.PI];
};
const camera = {center:point(...spec.front.center),elevation:spec.front.elevation,pitch:spec.front.pitch,bearing:contract.heading+spec.front.bearingOffset,zoom:spec.front.zoom,padding:{top:0,right:0,bottom:0,left:0}};
const result = {id:ID,mode:control?'frozen-before':'delivered',started:new Date().toISOString(),completed:false,server:base,
  desktopOnly,caseSha256:sha(fs.readFileSync(caseFile)),scriptSha256:sha(fs.readFileSync(__filename)),sourceCommit:review.baseline_commit,camera,views:[],screenshots:[],files:[],errors:[],warnings:[],failed:[]};
result.servedRuntime={};
const reportPath=path.join(out,control?'control-browser.json':'main-browser.json');
const save=()=>fs.writeFileSync(reportPath,JSON.stringify(result,null,2)+'\n');
async function run() {
  fs.mkdirSync(out,{recursive:true});assert.ok(!fs.existsSync(reportPath),'Use a fresh output directory');
  const catalogFile='data/candidate-city-integrations.json';
  const frozenControl=control && process.env.QA_CONTROL_CATALOG;
  if(control)assert.ok(frozenControl,'Audited predecessor origin required');
  const controlRoot=frozenControl && path.dirname(path.dirname(path.resolve(frozenControl)));
  const data=frozenControl?fs.readFileSync(frozenControl):control?execFileSync('git',['show',review.baseline_commit+':projects/shanghai/'+catalogFile],{cwd:path.resolve(project,'../..')}):bytes(catalogFile);
  const catalog=JSON.parse(data),row=catalog.models.find(r=>r.id===ID);
  result.catalog={sha256:sha(data),count:catalog.resulting_city_count};
  if(frozenControl){
    assert.equal(result.catalog.sha256,process.env.QA_CONTROL_CATALOG_SHA256,'Frozen predecessor catalog SHA-256');
    assert.equal(result.catalog.count,Number(process.env.QA_CONTROL_CITY_COUNT),'Frozen predecessor catalog size');
  }
  assert.equal(Boolean(row),!control);
  if(row) for(const key of ['owner','source_feature_ids','replacement_geometry','collision_geometry','model_geometry_sha256'])
    assert.deepEqual(row[key],contract[key],key);
  result.bindings=Object.fromEntries(['src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','index.html','landmarks.html']
    .map(f=>[f,sha(frozenControl?fs.readFileSync(path.join(controlRoot,f)):bytes(f))]));
  const received=new Set();
  const browser=await chromium.launch({headless:false,env:{...process.env,DISPLAY:':53'},executablePath:'/usr/bin/chromium',args:['--disable-translate','--disable-features=Translate,TranslateUI','--lang=zh-CN','--ozone-platform=x11','--no-zygote','--single-process','--in-process-gpu','--window-position=0,0','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disable-background-networking','--disable-component-update','--disable-sync','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--max-old-space-size=300 --max-semi-space-size=4','--disk-cache-size=1048576','--disable-gpu-shader-disk-cache','--force-gpu-mem-available-mb=96',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const viewport=phone?{width:390,height:540}:phase==='mouse'?{width:620,height:460}:phase==='distant'?{width:470,height:400}:control?{width:660,height:500}:{width:870,height:660};
  const page=await browser.newPage({viewport,locale:'zh-CN',deviceScaleFactor:1,ignoreHTTPSErrors:true,hasTouch:true});
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

  result.browser=browser.version();result.phase=phase;
  page.setDefaultTimeout(180000);
  if(control&&!frozenControl)await page.route('**/data/candidate-city-integrations.json*',r=>r.fulfill({contentType:'application/json',body:data}));
  page.on('pageerror',e=>result.errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')result.errors.push({url:m.location().url,message:m.text()});if(m.type()==='warning'&&m.text().includes('[Shanghai map]'))result.warnings.push(m.text());});
  const runtimeChecks=[];
  page.on('response',response=>{
    const u=new URL(response.url()), key=u.pathname.replace(/^\//,'');
    if (u.origin === new URL(base).origin && response.status()===200 && Object.hasOwn(result.bindings,key)) {
      runtimeChecks.push(response.body().then(body=>{
        const digest=sha(body);assert.equal(digest,result.bindings[key],key);
        result.servedRuntime[key]={sha256:digest,query:u.search,bytes:body.length};
      },()=>{}));
    }
  });
  page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')result.failed.push({url:r.url(),failure:r.failure()});});
  page.on('response',r=>{const u=new URL(r.url());if(r.status()>=400)result.failed.push({url:r.url(),status:r.status()});
    if(u.origin===new URL(base).origin&&r.status()===200)received.add(decodeURIComponent(u.pathname.slice(1)));});
  const ordinaryBook=controlRoot?JSON.parse(fs.readFileSync(path.join(controlRoot,'data/precise-buildings-v6.json'))):read('data/precise-buildings-v6.json');
  const currentGroup=ordinaryBook.macros.find(m=>m.id===review.frozen_macro)?.near.find(n=>n.id===group.id);
  const ordinaryPath=review.frozen_bindings.find(r=>r.repository_path.endsWith('/'+group.file)).repository_path.replace('projects/shanghai/','');
  const priorityNear=['/'+(currentGroup?.model.file||ordinaryPath)];
  const priorityFar=['/'+review.frozen_bindings.find(r=>r.repository_path.endsWith('/far.glb')).repository_path.replace('projects/shanghai/','')];
  const lanes={tiles:{lastEnd:0,tail:Promise.resolve()},models:{lastEnd:0,tail:Promise.resolve()}};
  const completions=new Map();
  const timers=new Set();
  let shuttingDown=false;
  const delay=ms=>new Promise(done=>{
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
    const queued=Date.now(),macro=pathname.includes('/assets/city-detail/')||priorityNear.includes(pathname);
    const far=macro&&/\/far\.glb(?:\.gz)?$/i.test(pathname);
    const priority=macro?(far?priorityFar:priorityNear).some(tile=>pathname.endsWith(tile)||pathname.endsWith(tile+'.gz')):
      [ID,PRIOR,spec.adjacentModel].some(id=>id&&pathname.includes('/'+id+'/'));
    const trace={pathname,priority,queued};result.transferTiming.requests.push(trace);
    const target=targetOrder.findIndex(tile=>pathname.endsWith(tile)||pathname.endsWith(tile+'.gz'));
    if(target>=0&&!claimed.has(target)&&(control||phase==='architecture')){
      await targetTransfer(route,request,trace,target);return;
    }
    if(priority){if(!shuttingDown){trace.continued=Date.now();await continueReal(route);}return;}
    const lane=macro?lanes.tiles:lanes.models;
    const firstDelay=macro?(far?14000:28000):42000,spacing=macro?(far?5000:8500):12000;
    const deliver=async()=>{
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
  await page.route(url=>(priorityNear.includes(url.pathname)||priorityFar.includes(url.pathname)||/^\/assets\/(?:city-detail|models)\/.+\.glb(?:\.gz)?$/.test(url.pathname)),routeModel);
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
  const context={id:ID,clipID:ID,selected,control,macro:review.frozen_macro,group:group.id,owner:source,extraOwners,neighbors,adjacentID:spec.adjacentModel};
  const manifest = row && read(row.candidate_manifest);
  async function settle(variant,detail=false){
    await page.waitForFunction(({selected,variant,detail,macro,group,owner,control,adjacentID})=>{
      const s=window.__SHANGHAI_APP__?.scene;
      if(!s?.getLandmarkAssetState||s.map.isMoving())return false;
      const a=s.getLandmarkAssetState(selected);
      if(!control&&(!a?.visible||a.status!=='loaded'||(variant&&a.variant!==variant)))return false;
      if(!detail)return true;
      if(adjacentID&&!s.getLandmarkAssetState(adjacentID)?.visible)return false;
      const c=s.getCandidateIntegrationState(),t=s.getStreamingState();
      const active=c.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group);
      const vectors=c.vector.filter(v=>v.active);

      return t.active.some(t=>t.id===macro&&t.visible)&&t.detail.active.some(t=>t.id===macro+'/'+group)
        && active && (control || (active.clip_feature_local_ids.includes(owner.local_id)
         ))
        && vectors.every(v=>!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer?.ready));
    },{...context,variant,detail},{polling:400,timeout:240000});
    await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>resolve());m.triggerRepaint();}));
  }
  async function view(name,variant,detail=false){
    await configureBacking();await settle(variant,detail);
    if(!control && !detail && spec.sourceSectionCount && name!=='map-distant'){
      await page.waitForFunction(({clipID,adjacentID,expected})=>{
        const scene=window.__SHANGHAI_APP__.scene;
        const section=scene.getCandidateIntegrationState().sourceSections.find(item=>item.id===clipID);
        const adjacentReady=!adjacentID||scene.getLandmarkAssetState(adjacentID)?.visible;
        return adjacentReady && section?.segments===expected;
      },{...context,expected:spec.sourceSectionCount},{polling:400,timeout:240000});
    }
    console.log('[map]',name);
    await page.waitForFunction(() => {
      const loading = document.getElementById('loading');
      if (!loading) return true;
      const style = getComputedStyle(loading);
      return style.visibility === 'hidden' || (Number(style.opacity) === 0 && style.pointerEvents === 'none');
    }, undefined, {polling: 250,timeout: 180000});
    await page.waitForFunction(()=>{
      const cover=document.querySelector('#loading');if(!cover)return false;
      const css=getComputedStyle(cover),scene=window.__SHANGHAI_APP__?.scene;
      return cover.classList.contains('loaded')&&css.visibility==='hidden'&&css.opacity==='0'&&css.pointerEvents==='none'&&scene&&!scene.map.isMoving();
    },null,{polling:300,timeout:300000});
    const {state,frame}=await page.evaluate(({id,clipID,selected,macro,group,owner,extraOwners,neighbors,adjacentID})=>new Promise(resolve=>{
      const map=window.__SHANGHAI_APP__.scene.map;
      map.once('render',()=>{
      const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,beacons=s.getBuildingBeaconState(),ci=s.getCandidateIntegrationState();
      const sourceState=o=>m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o.key.slice(9)});
      const label=beacons.labelPositions.find(z=>z.id===selected),gl=m.painter.context.gl;
      const canvas=m.getCanvas(),rect=canvas.getBoundingClientRect();
      const frame={png:canvas.toDataURL('image/png'),canvas:{x:rect.x,y:rect.y,w:rect.width,h:rect.height,width:canvas.width,height:canvas.height,pixelRatio:m.getPixelRatio()},bounds:{left:screenX,top:screenY,outerWidth,outerHeight,width:innerWidth,height:innerHeight,dpr:devicePixelRatio,focus:document.hasFocus(),href:location.href}};
      const state={route:location.hash,name:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],mode:app.mode,
        walkDisabled:document.querySelector('#start-walk').disabled,asset:s.getLandmarkAssetState(selected),source:sourceState(owner),
        ...(extraOwners.length?{extraOwnerStates:extraOwners.map(o=>({local_id:o.local_id,state:sourceState(o)}))}:{}),
        adjacentAsset:adjacentID?s.getLandmarkAssetState(adjacentID):undefined,neighbors:neighbors.map(o=>({local_id:o.local_id,state:sourceState(o)})),sections:ci.sourceSections?.filter(x=>x.id===clipID)??[],clip:ci.clips.find(c=>c.id===clipID)||null,
        group:ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group)||null,shader:{triangles:ci.shader.triangles,limit:ci.shader.triangleLimit,macroTextures:ci.shader.macroTextures??null,denseMacroTables:ci.shader.denseMacroTables??[]},
        labels:beacons.count,pick:label?s.pickBuildingBeacon(label):null,camera:{center:m.getCenter(),elevation:m.getCenterElevation(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom(),padding:m.getPadding(),viewport:[m.getCanvas().clientWidth,m.getCanvas().clientHeight]},
        glError:gl.getError(),contextLost:gl.isContextLost()};
      resolve({state,frame});
      });map.triggerRepaint();
    }),context);
    result.views.push({view:name,...state});save();
    assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.equal(state.labels,catalog.resulting_city_count);
    if(!control && (phase!=='architecture' || state.pick!==null))assert.equal(state.pick,selected);assert.equal(new URLSearchParams(state.route.slice(1)).get('landmark'),selected);
    for(const n of state.neighbors){if(!spec.existingCandidateOwners?.includes(n.local_id))assert.notEqual(n.state.candidateModel,true);}
    if(detail){
      assert.deepEqual(state.group.feature_local_ids,group.feature_local_ids);
      if(spec.adjacentModel){
        const adjacent=catalog.models.find(model=>model.id===spec.adjacentModel);
        const seen=state.adjacentAsset;
        assert.equal(seen.status,'loaded');assert.equal(seen.visible,true);
        assert.deepEqual(seen.anchor,[adjacent.lng,adjacent.lat]);
        assert.equal(seen.verifiedAsset.sha256,adjacent.assets[seen.variant==='full'?'web':'lod'].sha256);
        if(control){
          assert.deepEqual(state.group.clip_feature_local_ids,spec.existingGroupOwners);
          assert.equal(state.group.triangles,spec.groupTriangles-spec.addedTriangles);
        }
      }
    }
    if(detail&&extraOwners.length){
      for(const o of state.extraOwnerStates){
        if(control){assert.notEqual(o.state.candidateModel,true);assert.ok(!state.group.clip_feature_local_ids.includes(o.local_id));}
        else assert.ok(o.state.candidateModel||o.state.localModel,'Missing model state on source '+o.local_id);
      }
    }
    if(control&&detail){assert.deepEqual(state.group.clip_feature_local_ids,spec.existingGroupOwners);assert.equal(state.group.triangles,spec.groupTriangles-spec.addedTriangles);}
    if(control){assert.deepEqual(state.sections,[]);assert.equal(state.clip,null);assert.notEqual(state.source.candidateModel,true);assert.ok(!state.group.clip_feature_local_ids.includes(source.local_id));}
    else{
      for(const t of state.shader.denseMacroTables) assert.ok(t.pages>=2 && t.maxFeatureSpan<=state.shader.limit,'Active dense macro exceeds a draw page');
      assert.equal(state.name,row.name);assert.equal(state.mode,'overview');assert.equal(state.walkDisabled,true);
      const variant=state.asset.variant==='full'?'web':'lod';
      assert.equal(state.asset.verifiedAsset.sha256,row.assets[variant].sha256);assert.equal(state.asset.triangles,row.assets[variant].triangles);
      assert.deepEqual(state.asset.anchor,[row.lng,row.lat]);assert.equal(state.asset.heading,row.heading);
      assert.deepEqual(state.clip.owner,row.owner);assert.deepEqual(state.clip.geometry,row.replacement_geometry);
      if(detail){assert.ok(state.source.candidateModel||state.source.localModel);assert.deepEqual([...state.group.clip_feature_local_ids].sort((a,b)=>a-b),[...(spec.existingGroupOwners||[]),...addedOwners].sort((a,b)=>a-b));assert.equal(state.group.triangles,spec.groupTriangles);if(spec.sourceSectionCount){
        assert.equal(state.sections.length,1);
        const section=state.sections[0];
        assert.equal(section.feature_local_id,source.local_id);
        assert.equal(section.macro_id,review.frozen_macro);
        assert.equal(section.segments,spec.sourceSectionCount);
        assert.equal(section.roof_m,row.source_section_caps.roof_m);
      }}
    }
    {
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
      if(phase==='architecture'&&result.screenshots.length){
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
  }
  async function jump(camera){
    await configureBacking();
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
  }
  async function architecturalView(name,shot,coordinates){
    const targets=coordinates.map(([label,x,y,z])=>({name:label,lnglat:point(x,y),z}));
    const attempts=[];
    for(const [left,top,bottom] of [[0,0,0],[390,68,150],[260,60,130],[120,68,195]]){
      await jump({...camera,...shot,padding:{left,right:left?30:0,top,bottom}});
      await settle('full',true);
      let clearPoints;
      const points=targets;
      clearPoints=await page.evaluate(points=>{
          const scene=window.__SHANGHAI_APP__.scene,m=scene.map;
          const labels=scene.getBuildingBeaconState().labelPositions||[];
          return points.map(p=>{
            const elevation=()=>p.z;
            const xy=m.transform.locationToScreenPoint({lng:p.lnglat[0],lat:p.lnglat[1]},{getElevationForLngLat:elevation,getElevationForLngLatZoom:elevation});
            const canvas=m.getCanvas(),b=canvas.getBoundingClientRect(),x=xy.x+b.left,y=xy.y+b.top;
            const hit=document.elementFromPoint(x,y),label=scene.pickBuildingBeacon(xy);
            return {...p,x,y,hit:hit?.tagName,clear:hit===canvas&&!label,beacon:label};
          });
        },points);
      attempts.push({left,top,bottom,targets:clearPoints});
      if(clearPoints.every(p=>p.clear)){
        (result.architecturalPixels??=[]).push({name,attempts});
        save();
        await view(name,'full',true);
        return;
      }
    }
    (result.architecturalPixels??=[]).push({name,attempts});
    save();
    throw new Error('Map interface still covers the architectural samples for '+name);
  }
  async function selectPhysical(touch){
    const city=base+'index.html#landmark='+PRIOR+'&mode=overview';
    await page.goto('about:blank');
    await page.goto(city,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>!!window.__SHANGHAI_APP__?.scene?.map);
    await closePanel();
    await jump({...camera,center:[contract.lng,contract.lat],elevation:0,pitch:0,bearing:0,zoom:19.15});
    const getHit=id=>{const scene=window.__SHANGHAI_APP__?.scene,map=scene?.map,el=document.querySelector('#loading');
      if(!map||map.isMoving()||!el?.classList.contains('loaded')||getComputedStyle(el).visibility!=='hidden')return false;
      const b=scene.getBuildingBeaconState(),p=b.labelPositions.find(v=>v.id===id||v.memberIds?.includes(id));
      if(!p||scene.pickBuildingBeacon(p)!==p.id)return false;
      const box=map.getCanvas().getBoundingClientRect();
      return {x:box.x+p.x,y:box.y+p.y,label:p.id,group:Boolean(p.memberIds),members:p.memberIds||[],route:location.hash};};
    const answer=await page.waitForFunction(getHit,ID,{polling:250,timeout:240000});
    const p=await answer.jsonValue();assert.ok(!p.route.includes('landmark='+ID));
    if(touch)await page.touchscreen.tap(p.x,p.y);else await page.mouse.click(p.x,p.y);
    if(p.group){const option=page.locator('dialog.beacon-group-picker[open] [data-landmark="'+ID+'"]');if(touch)await option.tap();else await option.click();}
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,ID);
    (result.physicalSelections??=[]).push({...p,input:touch?'touch':'mouse',selected:ID});save();
    await view('map-after-physical-'+phase,'full',true);
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
      await page.goto(base+'index.html#landmark='+PRIOR+'&mode=overview',{waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));await closePanel();await jump(camera);await view('map-before',null,true);
      result.beforeGround=await page.evaluate(async probes=>{const scene=window.__SHANGHAI_APP__.scene;await scene.waitForData(10000);
        return {points:probes.map(p=>({...p,found:scene.collisionAt(...p.position)})),collision:scene.getCollisionState()};},
        spec.ground.map(w=>({name:w.name,position:point(...w.xy)})));
      assert.equal(result.beforeGround.points.length,spec.ground.length);save();
    }else{
      if (['phone','desktop'].includes(phase)) {
        await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
        assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
        const card=page.locator('#district-'+row.districtId+' [data-landmark="'+ID+'"] .card-foot a[href="index.html#landmark='+ID+'&mode=overview"]');
        if (phone) await card.tap(); else await card.click();
        await view(phone?'map-mobile':'map-desktop',null);
        await view(phone?'map-mobile-settled':'map-desktop-settled','full',true);
      } else if (['mouse','touch'].includes(phase)) {
        await selectPhysical(phone);
      } else {
        await page.goto(base+'index.html#landmark='+ID+'&mode=overview',{waitUntil:'domcontentloaded'});
        if(phase==='distant'){
          await page.waitForFunction(()=>!!window.__SHANGHAI_APP__?.scene?.map);
          await settle('full');
          await closePanel();
          await jump(camera);
        }
        await settle('full',true);await closePanel();
        if(phase==='architecture'){
      await jump(camera);await view('map-street-facade','full',true);
      await jump({...camera,center:point(...spec.roof.center),bearing:contract.heading+spec.roof.bearingOffset,elevation:spec.roof.elevation,pitch:spec.roof.pitch,zoom:spec.roof.zoom});await view('map-roof','full',true);
      await architecturalView('map-cast-posts-and-spandrels',{center:point(0,0.6),bearing:contract.heading+(4),pitch:53,elevation:4.3,zoom:20.6},[["middle paired post", 1.88, 0.074, 6.42], ["cast upper spandrel", -0.1, 0.08, 8.21], ["lower spandrel", 3.7, 0.08, 4.02], ["balustrade", -0.4, 0.079, 5.3]]);
      await architecturalView('map-recessed-windows-and-roof',{center:point(0,4.1),bearing:contract.heading+(7),pitch:45,elevation:8.3,zoom:20.5},[["west gallery window", -6.03, 2.54, 6.2], ["east gallery window", 5.99, 2.54, 6.2], ["south eave", 2.0, -0.11, 8.82], ["west chimney", -4.92, 5.2, 11.64], ["east chimney", 3.67, 5.2, 11.64]]);
      result.ground=await page.evaluate(async probes=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(10000);
        return probes.map(p=>({...p,found:s.collisionAt(...p.position)}));},[
        ...spec.ground.map(w=>({name:w.name,position:point(...w.xy),expected:w.expected})),
        ...neighbors.map(n=>({name:'retained neighbor '+n.local_id,position:spec.neighborGround[n.local_id],expected:'building'}))]);
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);
        }else {
          await jump({...camera,zoom:15.65,pitch:15,elevation:0});await view('map-distant','distant');
          for(const [role,item] of Object.entries(manifest.assets))await receipt(path.posix.join(path.posix.dirname(row.candidate_manifest),item.file),item,role==='full'||role==='lod');
        }
      }
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
    const ordinaryManifest='data/precise-buildings-v6.json';
    const ordinaryIndex=controlRoot?JSON.parse(fs.readFileSync(path.join(controlRoot,ordinaryManifest))):read(ordinaryManifest);
    const ordinaryMacro=ordinaryIndex.macros.find(r=>r.id===review.frozen_macro);
    const override=ordinaryMacro?.near.find(g=>g.id===group.id);
    for(const rec of review.frozen_bindings.filter(r=>r.repository_path.endsWith('/far.glb')||r.repository_path.endsWith('/'+group.file))){
      const isRepacked=Boolean(override)&&rec.repository_path.endsWith('/'+group.file);
      await receipt(rec.repository_path.replace('projects/shanghai/',''),rec,!isRepacked);
      if(isRepacked){
        assert.equal(rec.sha256,override.baseline_sha256);assert.deepEqual(override.featureLocalIds,group.feature_local_ids);
        await receipt(override.model.file,{bytes:override.model.size_bytes,sha256:override.model.sha256},true);
      }
    }
    await Promise.all(runtimeChecks);
    for(const key of ['src/app.js','src/map-scene.js','src/building-beacons.js','src/building-beacon-groups.js'])assert.ok(result.servedRuntime[key],key);
    assert.deepEqual(result.errors,[]);assert.deepEqual(result.failed,[]);result.completed=true;
   }catch(e){result.failure=e.stack;result.failureState=await page.evaluate(({id,selected,group,macro})=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return {body:document.body.innerText.slice(0,1000)};
      return {route:location.hash,moving:s.map.isMoving(),stream:s.getStreamingState(),camera:{center:s.map.getCenter(),zoom:s.map.getZoom()},active:s.getLandmarkAssetState(selected),selectedTarget:s.getLandmarkAssetState(id),group:s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.id===macro+'/'+group),labels:s.getBuildingBeaconState().viewportLabelCount};
    },context).catch(err=>({error:String(err)}));throw e;}
  finally{await browser.close();result.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
