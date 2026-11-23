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
assert.equal(ID,'huangpu-puguang-ymca-east-entrance');
const PRIOR = spec.previous;
const control = process.argv.includes('--control');
const section = process.env.CITY_SECTION;
const desktopOnly = !['phone','touch'].includes(section);
const phase=section, mobile=!desktopOnly;
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
const {sourceGroups,assertGroupDraws}=require('./candidate-audit-groups.cjs');
const groupCases=sourceGroups(review,contract,spec);
const primaryCase=groupCases.find(g=>g.id===group.id);
const extraOwners=review.owners.filter(r=>r.local_id!==source.local_id&&addedOwners.includes(r.local_id));
const neighbors = review.owners.filter(r=>spec.neighbors.includes(r.local_id));
const point = (x,y) => {
  const h=contract.heading*Math.PI/180,k=6371008.8*Math.cos(contract.lat*Math.PI/180);
  const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
  return [contract.lng+east/k*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(contract.lat*Math.PI/180))+north/k))*180/Math.PI];
};
const camera = {center:point(...spec.front.center),elevation:spec.front.elevation,pitch:spec.front.pitch,bearing:contract.heading+spec.front.bearingOffset,zoom:spec.front.zoom,padding:{top:0,right:0,bottom:0,left:0}};
const detailCameras=JSON.parse(fs.readFileSync(path.join(__dirname,'geometry/formal-cameras.json')));
const measured=JSON.parse(fs.readFileSync(path.join(__dirname,'geometry/camera-and-preservation.json')));
const witnessPoints=Object.entries(measured.local_targets_enu).map(([name,[east,north,z]])=>{
  const metres=6371008.8*Math.cos(contract.lat*Math.PI/180);
  const lng=contract.lng+east/metres*180/Math.PI;
  const lat=Math.atan(Math.sinh(Math.asinh(Math.tan(contract.lat*Math.PI/180))+north/metres))*180/Math.PI;
  return {name,lng,lat,z};
});
assert.equal(witnessPoints.length,16);
const result = {id:ID,mode:control?'frozen-before':'delivered',started:new Date().toISOString(),completed:false,server:base,
  desktopOnly,section,caseSha256:sha(fs.readFileSync(caseFile)),scriptSha256:sha(fs.readFileSync(__filename)),sourceCommit:review.baseline_commit,camera,views:[],screenshots:[],files:[],errors:[],warnings:[],failed:[]};
result.phase=phase;result.servedRuntime={};
const reportPath=path.join(out,control?'control-browser.json':'main-browser.json');
// Keep the full X11 image, its exact crop and the raw WebGL framebuffer on volumes with room.
function storeCapture(file,data){
  const dirs=[out].map(base=>{
    const stats=fs.statfsSync(base);
    return {base,free:stats.bavail*stats.bsize};
  }).sort((a,b)=>b.free-a.free);
  const digest=sha(data);
  for(const {base,free} of dirs){
    if(free<data.length+65536)continue;
    const folder=path.join(base,'puguang-263-screens',phase,String(process.pid));
    let partial;
    try{
      fs.mkdirSync(folder,{recursive:true});
      const physical=path.join(folder,digest+'-'+path.basename(file));
      if(!fs.existsSync(physical)){
        partial=physical+'.writing';fs.writeFileSync(partial,data);
        assert.equal(sha(fs.readFileSync(partial)),digest);
        fs.renameSync(partial,physical);
      }
      const link=file+'.new';
      fs.rmSync(link,{force:true});fs.symlinkSync(physical,link);fs.renameSync(link,file);
      assert.equal(sha(fs.readFileSync(file)),digest);
      return;
    }catch(error){
      if(partial)fs.rmSync(partial,{force:true});
      if(!['ENOSPC','EDQUOT'].includes(error.code))throw error;
    }
  }
  throw Error('No writable volume can retain the '+data.length+' bytes of '+file);
}
function x11(file,env,timeout) {
  storeCapture(file,execFileSync('import',['-silent','-display',':53','-window','root','png:-'],{env,timeout,maxBuffer:16*1024*1024}));
}
function crop(source,rect,file,env) {
  storeCapture(file,execFileSync('convert',[source,'-crop',rect,'+repage','PNG24:-'],{env,timeout:10000,maxBuffer:16*1024*1024}));
}
const save=()=>{
  const data=Buffer.from(JSON.stringify(result,null,2)+'\n');
  const volumes=[out].sort((a,b)=>{
    const available=dir=>{const st=fs.statfsSync(dir);return st.bsize*st.bavail};return available(b)-available(a);
  });
  for(const volume of volumes){
    const physical=path.join(volume,'puguang-263-report-'+process.pid+'.json');
    const partial=physical+'.new';
    try{
      fs.writeFileSync(partial,data);fs.renameSync(partial,physical);
      const prior=fs.existsSync(reportPath)?fs.realpathSync(reportPath):null;
      const link=reportPath+'.link';fs.rmSync(link,{force:true});fs.symlinkSync(physical,link);fs.renameSync(link,reportPath);
      if(prior&&prior!==physical&&path.basename(prior)===path.basename(physical))fs.rmSync(prior,{force:true});
      return;
    }catch(error){fs.rmSync(partial,{force:true});if(!['ENOSPC','EDQUOT'].includes(error.code))throw error;}
  }
  throw Error('No local volume can store the complete technical report');
};
async function run() {
  fs.mkdirSync(out,{recursive:true});assert.ok(!fs.existsSync(reportPath),'Use a fresh output directory');
  const catalogFile='data/candidate-city-integrations.json';
  const frozenControl=control && process.env.QA_CONTROL_CATALOG;
  const controlRoot=frozenControl && path.dirname(path.dirname(path.resolve(frozenControl)));
  const data=frozenControl?fs.readFileSync(frozenControl):control?execFileSync('git',['show',review.baseline_commit+':projects/shanghai/'+catalogFile],{cwd:path.resolve(project,'../..')}):bytes(catalogFile);
  const catalog=JSON.parse(data),row=catalog.models.find(r=>r.id===ID);
  result.catalog={sha256:sha(data),count:catalog.resulting_city_count};
  if(frozenControl){
    assert.equal(result.catalog.sha256,process.env.QA_CONTROL_CATALOG_SHA256,'Frozen predecessor catalog SHA-256');
    assert.equal(result.catalog.count,Number(process.env.QA_CONTROL_CITY_COUNT),'Frozen predecessor catalog size');
  }
  assert.equal(Boolean(row),!control);
  if(row) for(const key of ['owner','source_feature_ids','replacement_geometry','collision_geometry','display_height_clips','model_geometry_sha256'])
    assert.deepEqual(row[key],contract[key],key);
  result.bindings=Object.fromEntries(['src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','index.html','landmarks.html']
    .map(f=>[f,sha(frozenControl?fs.readFileSync(path.join(controlRoot,f)):bytes(f))]));
  const received=new Set();
  const browser=await chromium.launch({headless:false,env:{...process.env,DISPLAY:':53'},executablePath:'/usr/bin/chromium',args:['--test-type','--noerrdialogs','--disable-infobars','--lang=zh-CN','--disable-translate','--disable-features=Translate,TranslateUI','--lang=zh-CN','--ozone-platform=x11','--disable-gpu-program-cache','--no-zygote','--single-process','--in-process-gpu','--window-position=0,0','--no-sandbox',...(process.env.QA_ANGLE_BACKEND?.startsWith('gl')?['--use-gl=angle','--ignore-gpu-blocklist','--disable-gpu-watchdog']:[]),'--use-angle='+(process.env.QA_ANGLE_BACKEND||'swiftshader'),'--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disable-background-networking','--disable-component-update','--disable-sync','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--optimize-for-size --max-old-space-size=212 --max-semi-space-size=1','--disk-cache-size=1048576','--disable-gpu-shader-disk-cache','--force-gpu-mem-available-mb=96',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const viewport=mobile?{width:390,height:540}:phase==='distant'?{width:440,height:380}:control?{width:510,height:405}:phase==='closeups'?{width:720,height:600}:phase==='architecture'?{width:790,height:529}:{width:850,height:620};
  const page=await browser.newPage({viewport,locale:'zh-CN',deviceScaleFactor:1,ignoreHTTPSErrors:true,hasTouch:mobile});
  let calibrated=null; const calibrationView=page.viewportSize();
  try {
  const sizing=await page.context().newCDPSession(page);
  const nativeWindow=await sizing.send('Browser.getWindowForTarget');
  await sizing.send('Browser.setWindowBounds',{windowId:nativeWindow.windowId,bounds:{left:0,top:0,width:Math.max(520,calibrationView.width+30),height:Math.min(970,calibrationView.height+210)}});
  await sizing.detach();
  await page.setContent('<style>body{margin:0;background:rgb(22,17,43)}i,b{position:fixed;display:block;width:9px;height:9px}i{left:0;top:0;background:rgb(207,43,171)}b{right:0;bottom:0;background:rgb(31,211,93)}</style><i></i><b></b>');
  await page.bringToFront();
  const probe=path.join(out,'viewport-calibration-x11-root.png');
  const locate="from PIL import Image; import sys,json; im=Image.open(sys.argv[1]).convert('RGB'); a=im.load(); w,h=map(int,sys.argv[2:4]); print(json.dumps(next(([x,y] for y in range(im.height-h+1) for x in range(im.width-w+1) if a[x,y]==(207,43,171) and a[x+8,y+8]==(207,43,171) and a[x+w-1,y+h-1]==(31,211,93) and a[x+w-9,y+h-9]==(31,211,93)),None)))";
  for(let n=0;!calibrated&&n<15;n++){
    await new Promise(resolve=>setTimeout(resolve,120));
    x11(probe,{...process.env,DISPLAY:':53',MAGICK_THREAD_LIMIT:'1'},12000);
    calibrated=JSON.parse(execFileSync('python',['-c',locate,probe,String(calibrationView.width),String(calibrationView.height)],{encoding:'utf8'}));
  }
  assert.ok(calibrated,'Both opposite corners of the browser viewport must be visible');
  result.viewportCalibration={x:calibrated[0],y:calibrated[1],...calibrationView,display:':53',image:path.basename(probe),sha256:sha(fs.readFileSync(probe))};
  } catch(error){result.failure=error.stack;result.finished=new Date().toISOString();try{save();}finally{await browser.close();}throw error;}
  await page.addInitScript(()=>{
     let api;
     Object.defineProperty(window,'maplibregl',{configurable:true,get(){return api},set(v){
       api=v;
       if(typeof v?.setWorkerCount==='function')v.setWorkerCount(1);
       if(typeof v?.Map==='function'){
         const OriginalMap=v.Map;
         v.Map=class extends OriginalMap {
           constructor(options){
             super({...options,pixelRatio:0.5,maxTileCacheSize:8,antialias:false,canvasContextAttributes:{...options.canvasContextAttributes,antialias:false}});
             const gl=this.getCanvas().getContext('webgl2');const info=gl?.getExtension('WEBGL_debug_renderer_info');
             window.initialMapRendering={webgl2:!!gl,renderer:info?gl.getParameter(info.UNMASKED_RENDERER_WEBGL):null,pixelRatio:this.getPixelRatio(),width:this.getCanvas().width,height:this.getCanvas().height};
           }
         };
       }
     }});
  });
  await page.addInitScript(() => {
    document.addEventListener('pointerdown', event => {
      const card=event.target.closest?.('.landmark-card');
      if(card) sessionStorage.setItem('qa263DirectoryPointer', JSON.stringify({id:card.dataset.landmark, type:event.pointerType, trusted:event.isTrusted}));
      if(event.target.closest?.('.maplibregl-canvas-container')) window.qa263MapPointer={type:event.pointerType,trusted:event.isTrusted,x:event.clientX,y:event.clientY};
    },true);
  });
  const physicalMemory=await page.evaluate(()=>navigator.deviceMemory??null);
  await page.addInitScript(()=>Object.defineProperty(navigator,'deviceMemory',{value:4,configurable:true}));
  result.browserProfile={physicalMemory,deviceMemoryProfileGiB:4,shadowQuality:'off',normalMaps:true};

  result.browser=browser.version();
  page.setDefaultTimeout(180000);
  if(control)assert.ok(frozenControl,'The control is served from the real predecessor origin');
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
  const frozenFile=rec=>'/'+rec.repository_path.replace('projects/shanghai/','');
  const priorityNear=groupCases.map(g=>frozenFile(review.frozen_bindings.find(r=>r.repository_path.endsWith('/'+g.tile.file))));
  const priorityFar=[frozenFile(review.frozen_bindings.find(r=>r.repository_path.endsWith('/far.glb')))];
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
  let finishInitial;
  const firstMapFrame=new Promise(r=>finishInitial=r);
  const afterInitial=async()=>{
    if(!control)return;
    await Promise.race([firstMapFrame,delay(60000)]);
  };
  result.transferTiming.initialViewport=viewport;
  result.transferTiming.nonfocalAfter='First rendered calibrated map frame; 60 second fall-back';

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
      if(control && pos>0) await afterInitial();
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
    if(target>=0&&!claimed.has(target)){
      await targetTransfer(route,request,trace,target);return;
    }
    if(priority){if(!shuttingDown){trace.continued=Date.now();await continueReal(route);}return;}
    const lane=macro?lanes.tiles:lanes.models;
    const firstDelay=macro?(far?14000:28000):42000,spacing=macro?(far?5000:8500):12000;
    const deliver=async()=>{
      if(shuttingDown)return;
      await afterInitial();
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
  const context={id:ID,selected,control,witnessPoints,macro:review.frozen_macro,group:group.id,groupCases,owner:source,extraOwners,neighbors,adjacentID:spec.adjacentModel};
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
      const activeGroups=groupCases.every(g=>{
        const key=macro+'/'+g.id, draw=c.shader.ownerScopedSources.find(v=>v.id===key);
        return t.detail.active.some(v=>v.id===key) && draw && (control || g.addedOwners.every(id=>draw.clip_feature_local_ids.includes(id)));
      });
      return t.active.some(t=>t.id===macro&&t.visible)&&t.detail.active.some(t=>t.id===macro+'/'+group)
        && activeGroups
        &&c.vector.filter(v=>v.active).every(v=>!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer?.ready));
    },{...context,variant,detail},{polling:400,timeout:240000});
    await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>resolve());m.triggerRepaint();}));
  }
  async function view(name,variant,detail=false){
    await configureBacking();
    await settle(variant,detail);
    if(!control && !detail && spec.sourceSectionCount && name!=='map-distant'){
      await page.waitForFunction(({id,adjacentID,expected})=>{
        const scene=window.__SHANGHAI_APP__.scene;
        const section=scene.getCandidateIntegrationState().sourceSections.find(item=>item.id===id);
        const adjacentReady=!adjacentID||scene.getLandmarkAssetState(adjacentID)?.visible;
        return adjacentReady && section?.segments===expected;
      },{...context,expected:spec.sourceSectionCount},{polling:400,timeout:240000});
    }
    console.log('[map]',name);
    await page.waitForFunction(()=>{
      const cover=document.getElementById('loading');const scene=window.__SHANGHAI_APP__?.scene;
      return cover&&cover.classList.contains('loaded')&&getComputedStyle(cover).visibility==='hidden'&&scene&&!scene.map.isMoving();
    },null,{polling:300,timeout:240000});
    const {state,frame}=await page.evaluate(({id,selected,macro,group,groupCases,owner,extraOwners,neighbors,adjacentID,witnessPoints})=>new Promise(resolve=>{
      const map=window.__SHANGHAI_APP__.scene.map;
      map.once('render',()=>{
      const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,beacons=s.getBuildingBeaconState(),ci=s.getCandidateIntegrationState();
      const sourceState=o=>m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o.key.slice(9)});
      const label=beacons.labelPositions.find(z=>z.id===selected),gl=m.painter.context.gl;
      const canvas=m.getCanvas(),rect=canvas.getBoundingClientRect();
      const frame={png:canvas.toDataURL('image/png'),canvas:{x:rect.x,y:rect.y,w:rect.width,h:rect.height,width:canvas.width,height:canvas.height,pixelRatio:m.getPixelRatio()},bounds:{left:screenX,top:screenY,outerWidth,outerHeight,width:innerWidth,height:innerHeight,dpr:devicePixelRatio,focus:document.hasFocus(),href:location.href}};
      const projections=witnessPoints.map(p=>{
        const elevation=()=>p.z;
        const xy=m.transform.locationToScreenPoint({lng:p.lng,lat:p.lat},{getElevationForLngLat:elevation,getElevationForLngLatZoom:elevation});
        const x=xy.x+rect.left,y=xy.y+rect.top,hit=document.elementFromPoint(x,y),beacon=s.pickBuildingBeacon(xy);
        return {...p,x,y,inside:x>=0&&x<innerWidth&&y>=0&&y<innerHeight,element:hit?.tagName??null,clear:hit===canvas&&!beacon,beacon};
      });
      const state={projections,route:location.hash,name:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],mode:app.mode,
        walkDisabled:document.querySelector('#start-walk').disabled,asset:s.getLandmarkAssetState(selected),source:sourceState(owner),
        ...(extraOwners.length?{extraOwnerStates:extraOwners.map(o=>({local_id:o.local_id,state:sourceState(o)}))}:{}),
        adjacentAsset:adjacentID?s.getLandmarkAssetState(adjacentID):undefined,neighbors:neighbors.map(o=>({local_id:o.local_id,state:sourceState(o)})),sections:ci.sourceSections?.filter(x=>x.id===id)??[],clip:ci.clips.find(c=>c.id===id)||null,bands:ci.displayClips.filter(c=>c.id.startsWith(id+'-')),
        group:ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group)||null,
        ...(groupCases.length>1?{streamedGroups:groupCases.map(g=>ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+g.id)||null)}:{}),shader:{triangles:ci.shader.triangles,limit:ci.shader.triangleLimit,macroTextures:ci.shader.macroTextures??null},
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
    for(const n of state.neighbors){if(!spec.existingCandidateOwners?.includes(n.local_id))assert.notEqual(n.state.candidateModel,true);}
    if(detail){
      assert.deepEqual(state.group.feature_local_ids,group.feature_local_ids);
      if(spec.groups)assertGroupDraws(groupCases,state.streamedGroups||[state.group],control);
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
    if(control){assert.deepEqual(state.sections,[]);assert.deepEqual(state.bands,[]);assert.equal(state.clip,null);assert.ok(!state.group.clip_feature_local_ids.includes(source.local_id));}
    else{
      assert.equal(state.name,row.name);assert.equal(state.mode,'overview');assert.equal(state.walkDisabled,true);
      const variant=state.asset.variant==='full'?'web':'lod';
      assert.equal(state.asset.verifiedAsset.sha256,row.assets[variant].sha256);assert.equal(state.asset.triangles,row.assets[variant].triangles);
      assert.deepEqual(state.asset.anchor,[row.lng,row.lat]);assert.equal(state.asset.heading,row.heading);
      assert.equal(state.clip,null);
      assert.deepEqual(state.sections,[]);
      assert.deepEqual(state.bands.map(c=>({id:c.id,owner:c.owner,geometry:c.geometry,min_height:c.min_height,max_height:c.max_height,height_reference:c.height_reference})),contract.display_height_clips);
      if(detail){assert.notEqual(state.source.candidateModel,true);assert.deepEqual([...state.group.clip_feature_local_ids].sort((a,b)=>a-b),[...primaryCase.existingOwners,...primaryCase.addedOwners].sort((a,b)=>a-b));assert.equal(state.group.triangles,primaryCase.groupTriangles);if(spec.sourceSectionCount){
        assert.equal(state.sections.length,1);
        const section=state.sections[0];
        assert.equal(section.feature_local_id,source.local_id);
        assert.equal(section.macro_id,review.frozen_macro);
        assert.equal(section.segments,spec.sourceSectionCount);
        assert.equal(section.roof_m,row.source_section_caps.roof_m);
      }}
    }
    await page.waitForFunction(()=>{const app=window.__SHANGHAI_APP__,loader=document.querySelector('#loading');if(!app?.scene||!loader)return false;const css=getComputedStyle(loader);return !app.scene.map.isMoving()&&loader.classList.contains('loaded')&&css.opacity==='0'&&css.visibility==='hidden'&&css.pointerEvents==='none';},null,{timeout:240000,polling:300});
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
      x11(source,commandEnv,12500);
      let root=fs.readFileSync(source);
      assert.ok(x+bounds.width<=root.readUInt32BE(16)&&y+bounds.height<=root.readUInt32BE(20),'Viewport outside recorded X display '+JSON.stringify(bounds));
      const target=path.join(out,name+'.png');
      crop(source,rect,target,commandEnv);
      let image=fs.readFileSync(target);
      assert.ok(image.length>1000&&image.readUInt32BE(16)===bounds.width&&image.readUInt32BE(20)===bounds.height);
      result.screenshots.push({file:name+'.png',bytes:image.length,sha256:sha(image)});
      const webgl=Buffer.from(frame.png.split(',')[1],'base64'),filename=name+'-webgl.png';
      assert.equal(webgl.readUInt32BE(16),frame.canvas.width);
      assert.equal(webgl.readUInt32BE(20),frame.canvas.height);assert.ok(webgl.length>1000);
      storeCapture(path.join(out,filename),webgl);
      (result.webglCaptures??=[]).push({file:filename,sha256:sha(webgl),bytes:webgl.length,...frame.canvas});
      (result.displayCaptures??=[]).push({display:':53',bounds,rectangle:rect,displayImage:path.basename(source),displayImageSha256:sha(root)});
      save();
    }
  }

  async function clickBeacon(id,prev,center,report) {
    await page.goto(new URL('index.html#landmark='+prev+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()),null,{timeout:180000});
    await closePanel();
    const dimensions=page.viewportSize();
    await jump({center,zoom:19.65,pitch:0,bearing:0,elevation:0,padding:{left:0,right:0,top:0,bottom:Math.round(dimensions.height*.22)}});
    await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene;const p=s.getBuildingBeaconState().labelPositions.find(x=>x.id===id||x.memberIds?.includes(id));if(!p||s.pickBuildingBeacon(p)!==p.id)return false;const b=s.map.getCanvas().getBoundingClientRect(),el=document.elementFromPoint(b.x+p.x,b.y+p.y);return el===s.map.getCanvas()||el?.closest('.maplibregl-canvas-container');},id,{polling:300,timeout:180000});
    const action=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,p=s.getBuildingBeaconState().labelPositions.find(x=>x.id===id||x.memberIds?.includes(id)),b=s.map.getCanvas().getBoundingClientRect();return {x:b.x+p.x,y:b.y+p.y,id:p.id,group:p.memberIds?.length>0,previous:location.hash,viewport:[innerWidth,innerHeight]};},id);
    assert.equal(new URLSearchParams(action.previous.slice(1)).get('landmark'),prev);
    const touch=section==='touch';
    if(touch)await page.touchscreen.tap(action.x,action.y);else await page.mouse.click(action.x,action.y);
    if(action.group){const choice=page.locator('dialog.beacon-group-picker[open] [data-landmark="'+id+'"]');if(touch)await choice.tap();else await choice.click();}
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id,{timeout:180000});
    const pointer=await page.evaluate(()=>window.qa263MapPointer);assert.ok(pointer?.trusted);assert.equal(pointer.type,touch?'touch':'mouse');
    report.realBeacon={...action,pointer,landed:id,action:touch?'physical canvas touch':'physical canvas mouse click'};save();
  }
  async function jump(camera){
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
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));await closePanel();await jump(camera);
      await page.evaluate(()=>new Promise(done=>{const map=window.__SHANGHAI_APP__.scene.map;map.once('render',()=>done());map.triggerRepaint();}));
      result.transferTiming.firstMapFrame=Date.now();finishInitial();save();
      await view('map-before',null,true);
      const positions=spec.ground.map(w=>({name:w.name,position:point(...w.xy),postDelivery:w.expected})).concat(neighbors.map(n=>({name:'retained neighbor '+n.local_id,position:spec.neighborGround[n.local_id],postDelivery:'building'})));
      result.beforeGround=await page.evaluate(async positions=>{const scene=window.__SHANGHAI_APP__.scene;await scene.waitForData(10000);return positions.map(w=>({...w,found:scene.collisionAt(...w.position)}));},positions);
      assert.equal(result.beforeGround.length,59);
    }else{
      if(section==='desktop'||section==='phone'){
        const mobile=section==='phone';
        assert.deepEqual(page.viewportSize(),viewport);
        await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
        assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
        const card=page.locator('#district-'+row.districtId+' [data-landmark="'+ID+'"] .card-foot a[href="index.html#landmark='+ID+'&mode=overview"]');
        if(mobile) await card.tap(); else await card.click();
        await view(mobile?'map-mobile':'map-desktop','full',true);
        result.directoryPointer=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('qa263DirectoryPointer')));assert.ok(result.directoryPointer?.trusted);assert.equal(result.directoryPointer.id,ID);assert.equal(result.directoryPointer.type,mobile?'touch':'mouse');
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
        ...neighbors.map(n=>({name:'retained neighbor '+n.local_id,position:spec.neighborGround[n.local_id],expected:'building'}))]);
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);
      }
      if(section==='closeups'){
        assert.deepEqual(page.viewportSize(),viewport);
        await page.goto(base+'index.html#landmark='+ID+'&mode=overview',{waitUntil:'domcontentloaded'});
        await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));
        await closePanel();
        await jump(detailCameras.entrance);
        await view('map-stone-entrance-and-clock','full',true);
        await jump(detailCameras.upper);
        await view('map-upper-windows-and-pediment','full',true);
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
    for(const rec of review.frozen_bindings.filter(r=>r.repository_path.endsWith('/far.glb')||groupCases.some(g=>r.repository_path.endsWith('/'+g.tile.file))))
      await receipt(rec.repository_path.replace('projects/shanghai/',''),rec,control||section==='architecture'||(section==='distant'&&rec.repository_path.endsWith('/far.glb')));
    await Promise.all(runtimeChecks);
    for(const name of ['src/app.js','src/map-scene.js','src/building-beacons.js'])assert.equal(result.servedRuntime[name]?.sha256,result.bindings[name],name);
    assert.deepEqual(result.errors,[]);assert.deepEqual(result.failed,[]);result.completed=true;
   }catch(e){result.failure=e.stack;result.failureState=await page.evaluate(({id,selected,group,macro})=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return {body:document.body.innerText.slice(0,1000)};
      return {route:location.hash,moving:s.map.isMoving(),stream:s.getStreamingState(),camera:{center:s.map.getCenter(),zoom:s.map.getZoom()},active:s.getLandmarkAssetState(selected),selectedTarget:s.getLandmarkAssetState(id),group:s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.id===macro+'/'+group),labels:s.getBuildingBeaconState().viewportLabelCount};
    },context).catch(err=>({error:String(err)}));throw e;}
  finally{await browser.close();result.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
