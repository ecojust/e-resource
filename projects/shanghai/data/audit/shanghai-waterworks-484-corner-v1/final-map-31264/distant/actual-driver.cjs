/* Compare an audited, source-owned model with the frozen pre-delivery city view.
 * Run with its map-case.json path, and --control for the prior state. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright-core');
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
const addedOwners=[];
const declaredOwners=(contract.owners??[contract.owner]).map(o=>o.feature_local_id);
assert.deepEqual(declaredOwners,[1766]);assert.equal(contract.replacement_geometry,null);assert.equal(contract.altitude,4.75);assert.equal(contract.collision_geometry.type,"Polygon");
assert.ok(addedOwners.every(id=>group.feature_local_ids.includes(id)),'Expected every added owner in the tested streamed group');
const extraOwners=review.owners.filter(r=>r.local_id!==source.local_id&&addedOwners.includes(r.local_id));
const neighbors = review.owners.filter(r=>spec.neighbors.includes(r.local_id));
const point = (x,y) => {
  const h=contract.heading*Math.PI/180,k=6371008.8*Math.cos(contract.lat*Math.PI/180);
  const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
  return [contract.lng+east/k*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(contract.lat*Math.PI/180))+north/k))*180/Math.PI];
};
const camera = {center:point(...spec.front.center),elevation:spec.front.elevation,pitch:spec.front.pitch,bearing:spec.front.bearing,zoom:spec.front.zoom,padding:{top:0,right:0,bottom:0,left:0}};
const result = {id:ID,mode:control?'frozen-before':'delivered',started:new Date().toISOString(),completed:false,server:base,
  desktopOnly,caseSha256:sha(fs.readFileSync(caseFile)),scriptSha256:sha(fs.readFileSync(__filename)),sourceCommit:review.baseline_commit,camera,views:[],screenshots:[],files:[],errors:[],warnings:[],failed:[]};
result.servedRuntime={};
const reportPath=path.join(out,control?'control-browser.json':'main-browser.json');
// Keep the full X11 image, its exact crop and the raw WebGL framebuffer on volumes with room.
function storeCapture(file,data){
  const dirs=[process.env.QA_EVIDENCE_VOLUME,'/run/codex-docker/user','/dev/shm','/tmp'].filter(Boolean).map(base=>{
    const stats=fs.statfsSync(base);
    return {base,free:stats.bavail*stats.bsize};
  }).sort((a,b)=>b.free-a.free);
  const digest=sha(data);
  for(const {base,free} of dirs){
    if(free<data.length+65536)continue;
    const folder=path.join(base,'waterworks-264-screens',phase,String(process.pid));
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
  storeCapture(file,execFileSync(process.env.QA_X11_SCANNER,[],{env,timeout,maxBuffer:16*1024*1024}));
}
function crop(source,rect,file,env) {
  storeCapture(file,execFileSync(process.env.QA_X11_SCANNER,[source,...rect.match(/^(\d+)x(\d+)\+(\d+)\+(\d+)$/).slice(1).map(Number).map((_,i,a)=>String(a[(i+2)%4]))],{env,timeout:10000,maxBuffer:16*1024*1024}));
}
// Reserve the running report before the browser allocates its cache. Each interim
// document is valid JSON, followed by whitespace until Chromium closes.
fs.mkdirSync(out,{recursive:true});assert.ok(!fs.existsSync(reportPath),'Use a fresh output directory');
const reserve=128*1024;
const candidates=[process.env.QA_EVIDENCE_VOLUME,'/run/codex-docker/user','/tmp','/dev/shm'].filter(Boolean);
let reportFd;
for(const volume of candidates){
  const file=path.join(volume,'qa264-'+process.pid+'.json');
  try{
    fs.writeFileSync(file,Buffer.alloc(reserve,32),{flag:'wx'});
    fs.symlinkSync(file,reportPath);
    reportFd=fs.openSync(file,'r+');
    break;
  }catch(error){
    fs.rmSync(file,{force:true});
    if(!['ENOSPC','EDQUOT'].includes(error.code))throw error;
  }
}
assert.notEqual(reportFd,undefined,'Space for the live technical report');
let previousReportLength=0;
const save=()=>{
  const body=Buffer.from(JSON.stringify(result,null,2)+'\n');
  assert.ok(body.length<=reserve,'Reserved report size');
  let pos=0;
  while(pos<body.length)pos+=fs.writeSync(reportFd,body,pos,body.length-pos,pos);
  if(body.length<previousReportLength)fs.writeSync(reportFd,Buffer.alloc(previousReportLength-body.length,32),0,previousReportLength-body.length,body.length);
  previousReportLength=body.length;
  if(result.finished)fs.ftruncateSync(reportFd,body.length);
};
async function run() {

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
  if(row) for(const key of ['owner','source_feature_ids','replacement_geometry','collision_geometry','model_geometry_sha256'])
    assert.deepEqual(row[key],contract[key],key);
  result.bindings=Object.fromEntries(['src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','index.html','landmarks.html']
    .map(f=>[f,sha(frozenControl?fs.readFileSync(path.join(controlRoot,f)):bytes(f))]));
  const received=new Set();
  const browser=await chromium.launch({headless:false,env:{...process.env,DISPLAY:':53'},executablePath:'/usr/bin/chromium',args:['--disable-translate','--disable-features=Translate,TranslateUI','--lang=zh-CN','--ozone-platform=x11','--disable-gpu-program-cache','--no-zygote','--single-process','--in-process-gpu','--window-position=0,0','--no-sandbox',...(process.env.QA_ANGLE_BACKEND?.startsWith('gl')?['--use-gl=angle','--ignore-gpu-blocklist','--disable-gpu-watchdog']:[]),'--use-angle='+(process.env.QA_ANGLE_BACKEND||'swiftshader'),'--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disable-background-networking','--disable-component-update','--disable-sync','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--expose-gc --optimize-for-size --max-old-space-size=212 --max-semi-space-size=1','--disk-cache-size=1048576','--disable-gpu-shader-disk-cache','--force-gpu-mem-available-mb=96',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const viewport=phone?{width:390,height:540}:phase==='mouse'?{width:620,height:460}:phase==='distant'?{width:470,height:400}:control?{width:420,height:380}:phase==='desktop'?{width:740,height:410}:phase==='architecture'?{width:825,height:490}:{width:650,height:445};
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
             super({...options,pixelRatio:0.5,maxTileCacheSize:4,antialias:false,canvasContextAttributes:{...options.canvasContextAttributes,antialias:false}});
             const gl=this.getCanvas().getContext('webgl2');const ext=gl&&gl.getExtension('WEBGL_debug_renderer_info');
             window.initialMapRendering={antialias:gl?.getContextAttributes().antialias,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):null,pixelRatio:this.getPixelRatio(),width:this.getCanvas().width,height:this.getCanvas().height};
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
  let finishInitial;
  const firstMapFrame=new Promise(r=>finishInitial=r);
  const afterInitial=async()=>{
    if(!control&&!['desktop','architecture'].includes(phase))return;
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
      if((control||phase==='desktop') && pos>0) await afterInitial();
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
    if(target>=0&&!claimed.has(target)&&(control||phase==='architecture'||phase==='desktop')){
      await targetTransfer(route,request,trace,target);return;
    }
    if(priority){
      if(!shuttingDown){
        trace.continued=Date.now();
        if(phase==='desktop'){
          const done=new Promise(resolve=>completions.set(request,resolve));
          if(!(await continueReal(route)))complete(request,'continuation-canceled');
          trace.completion=await done;trace.completed=Date.now();
          if(trace.completion==='requestfinished'){
            const reply=await request.response();trace.status=reply.status();trace.responseBytes=Number(await reply.headerValue('content-length'));trace.sizes=await request.sizes();
            assert.equal(trace.sizes.responseBodySize,trace.responseBytes);
          }
          save();
        }else await continueReal(route);
      }
      return;
    }
    const lane=macro?lanes.tiles:lanes.models;
    const firstDelay=macro?(far?14000:28000):42000,spacing=macro?(far?5000:8500):12000;
    const deliver=async()=>{
      await afterInitial();
      const earliest=Math.max(queued+firstDelay,phase==='architecture'&&result.transferTiming.firstMapFrame?result.transferTiming.firstMapFrame+(macro?2500:26000):0,lane.lastEnd?lane.lastEnd+spacing:0);
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
  const readyPath='assets/city-detail/macros/'+review.frozen_macro+'/READY.json';
  const readyResponse=await page.request.get(new URL(readyPath,base).href);
  assert.equal(readyResponse.status(),200);
  const readyBytes=await readyResponse.body(), readyBook=JSON.parse(readyBytes);
  assert.equal(readyBook.id,review.frozen_macro);
  const candidates=readyBook.near.filter(g=>g.file===group.file);
  assert.equal(candidates.length,1);assert.equal(candidates[0].sha256,group.sha256);
  const streamed=candidates[0];
  result.streamedSourceRegistry={path:readyPath,sha256:sha(readyBytes),groups:[{author:group.id,stream:streamed.id,file:group.file,sha256:group.sha256}]};
  const context={id:ID,clipID:ID,selected,control,macro:review.frozen_macro,group:streamed.id,owner:source,extraOwners,neighbors,adjacentID:spec.adjacentModel};
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
      const ownerState=s.map.getSource('overture-buildings') ? s.map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:owner.key.slice(9)}) : {};
      if(!t.active.some(tile=>tile.id===macro&&tile.visible)||!t.detail.active.some(tile=>tile.id===macro+'/'+group))return false;
      return !!active && active.feature_local_ids.includes(owner.local_id) && !active.clip_feature_local_ids.includes(owner.local_id)
        && vectors.every(v=>!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer?.ready));
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
      const label=beacons.labelPositions.find(z=>z.id===selected);
      const containingGroup=beacons.labelPositions.find(z=>z.memberIds?.includes(selected));
      const gl=m.painter.context.gl;
      const canvas=m.getCanvas(),rect=canvas.getBoundingClientRect();
      const frame={png:canvas.toDataURL('image/png'),canvas:{x:rect.x,y:rect.y,w:rect.width,h:rect.height,width:canvas.width,height:canvas.height,pixelRatio:m.getPixelRatio()},bounds:{left:screenX,top:screenY,outerWidth,outerHeight,width:innerWidth,height:innerHeight,dpr:devicePixelRatio,focus:document.hasFocus(),href:location.href}};
      const state={route:location.hash,name:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],mode:app.mode,
        walkDisabled:document.querySelector('#start-walk').disabled,asset:s.getLandmarkAssetState(selected),source:sourceState(owner),
        ...(extraOwners.length?{extraOwnerStates:extraOwners.map(o=>({local_id:o.local_id,state:sourceState(o)}))}:{}),
        adjacentAsset:adjacentID?s.getLandmarkAssetState(adjacentID):undefined,neighbors:neighbors.map(o=>({local_id:o.local_id,state:sourceState(o)})),sections:ci.sourceSections?.filter(x=>x.id===id)??[],clip:ci.clips.find(c=>c.id===id)||null,
        group:ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group)||null,shader:{triangles:ci.shader.triangles,limit:ci.shader.triangleLimit,macroTextures:ci.shader.macroTextures??null,denseMacroTables:ci.shader.denseMacroTables??[]},
        labels:beacons.count,pick:label?s.pickBuildingBeacon(label):null,
        beaconLabelMode:beacons.labelMode,selectedLabelGroup:containingGroup?{...containingGroup,actualHit:s.pickBuildingBeacon(containingGroup)}:null,camera:{center:m.getCenter(),elevation:m.getCenterElevation(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom(),padding:m.getPadding(),viewport:[m.getCanvas().clientWidth,m.getCanvas().clientHeight]},
        glError:gl.getError(),contextLost:gl.isContextLost()};
      resolve({state,frame});
      });map.triggerRepaint();
    }),context);
    result.views.push({view:name,...state});save();
    assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.equal(state.labels,catalog.resulting_city_count);
    if(!control && phase==='distant' && state.beaconLabelMode==='groups'){
      const group=state.selectedLabelGroup;
      assert.ok(group?.memberIds.includes(selected),'Focused building must be in its real aggregated beacon');
      assert.equal(group.actualHit,group.id,'The rendered group must be selectable at its actual screen position');
    } else if(!control && (phase!=='architecture' || state.pick!==null))assert.equal(state.pick,selected);
    assert.equal(new URLSearchParams(state.route.slice(1)).get('landmark'),selected);
    for(const n of state.neighbors){if(!spec.existing_group_sources.some(existing=>existing.sources.includes(n.local_id)))assert.notEqual(n.state.candidateModel,true);}
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
    if(control){assert.deepEqual(state.sections,[]);assert.equal(state.clip,null);assert.notEqual(state.source.candidateModel,true);assert.ok(!state.group.clip_feature_local_ids.includes(source.local_id));}
    else{
      for(const t of state.shader.denseMacroTables) assert.ok(t.pages>=2 && t.maxFeatureSpan<=state.shader.limit,'Active dense macro exceeds a draw page');
      assert.equal(state.name,row.name);assert.equal(state.mode,'overview');assert.equal(state.walkDisabled,true);
      const variant=state.asset.variant==='full'?'web':'lod';
      assert.equal(state.asset.verifiedAsset.sha256,row.assets[variant].sha256);assert.equal(state.asset.triangles,row.assets[variant].triangles);
      assert.deepEqual(state.asset.anchor,[row.lng,row.lat]);assert.equal(state.asset.heading,row.heading);
      assert.equal(state.clip,null);assert.deepEqual(state.sections,[]);
      if(detail){assert.ok(!state.group.clip_feature_local_ids.includes(1766));assert.deepEqual([...state.group.clip_feature_local_ids].sort((a,b)=>a-b),[]);assert.equal(state.group.triangles,0);}
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
      x11(source,commandEnv,12500);
      let root=fs.readFileSync(source);
      assert.ok(x+bounds.width<=root.readUInt32BE(16)&&y+bounds.height<=root.readUInt32BE(20),'Viewport outside recorded X display '+JSON.stringify(bounds));
      const target=path.join(out,name+'.png');
      crop(source,rect,target,commandEnv);
      let image=fs.readFileSync(target);
      if(phase==='architecture'&&result.screenshots.length){
        const last=path.join(out,result.screenshots.at(-1).file);
        const pixelDigest=f=>sha(execFileSync('convert',[f,'-strip','-depth','8','rgb:-'],{maxBuffer:8*1024*1024}));
        const previous=pixelDigest(last);
        for(let n=0;pixelDigest(target)===previous&&n<18;n++){
          await new Promise(r=>setTimeout(r,200));
          x11(source,commandEnv,12500);
          crop(source,rect,target,commandEnv);
        }
        root=fs.readFileSync(source);image=fs.readFileSync(target);
        assert.notEqual(pixelDigest(target),previous,'Two camera presentations retained the same viewport');
      }
      assert.ok(image.length>1000&&image.readUInt32BE(16)===bounds.width&&image.readUInt32BE(20)===bounds.height);
      result.screenshots.push({file:name+'.png',bytes:image.length,sha256:sha(image)});
      const webgl=Buffer.from(frame.png.split(',')[1],'base64'),filename=name+'-webgl.png';
      assert.equal(webgl.readUInt32BE(16),frame.canvas.width);
      assert.equal(webgl.readUInt32BE(20),frame.canvas.height);assert.ok(webgl.length>1000);
      storeCapture(path.join(out,filename),webgl);
      (result.webglCaptures??=[]).push({file:filename,sha256:sha(webgl),bytes:webgl.length,...frame.canvas});
      (result.displayCaptures??=[]).push({display:':53',bounds,rectangle:rect,displayImage:path.basename(source),displayImageSha256:sha(root)});
      if((phase==='desktop' && name==='map-desktop')||(phase==='architecture'&&name==='map-street-facade')){result.transferTiming.firstMapFrame=Date.now();finishInitial();}
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
    const placements=[{left:0,right:0,top:0,bottom:0}];
    for(const padding of placements){
      await jump({...camera,...shot,padding});
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
      attempts.push({padding,targets:clearPoints});
      if(attempts.length===1 && !clearPoints.every(p=>p.clear)){
        const alternatives=await page.evaluate(points=>{
          const canvas=window.__SHANGHAI_APP__.scene.map.getCanvas();
          const {width,height}=canvas.getBoundingClientRect();
          const candidates=[];
          for(let dy=-200;dy<=200;dy+=10){
            for(let dx=-300;dx<=300;dx+=12){
              if(!dx&&!dy)continue;
              if(!points.every(p=>p.x+dx>12&&p.x+dx<width-12&&p.y+dy>12&&p.y+dy<height-12))continue;
              if(!points.every(p=>document.elementFromPoint(p.x+dx,p.y+dy)===canvas))continue;
              let margin=0;
              for(const r of [5,12,24,36]){
                if(!points.every(p=>[[r,0],[-r,0],[0,r],[0,-r]].every(([x,y])=>document.elementFromPoint(p.x+dx+x,p.y+dy+y)===canvas)))break;
                margin=r;
              }
              candidates.push({dx,dy,score:Math.hypot(dx,dy)-margin*2});
            }
          }
          candidates.sort((a,b)=>a.score-b.score);
          const chosen=[];
          for(const c of candidates){
            if(chosen.every(d=>Math.hypot(c.dx-d.dx,c.dy-d.dy)>40))chosen.push(c);
            if(chosen.length===10)break;
          }
          return chosen.map(({dx,dy})=>({left:Math.max(0,2*dx),right:Math.max(0,-2*dx),top:Math.max(0,2*dy),bottom:Math.max(0,-2*dy)}));
        },clearPoints);
        placements.push(...alternatives);
      }
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
    const answer=await page.waitForFunction(getHit,ID,{polling:254,timeout:240000});
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
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));await closePanel();await jump(camera);
      await page.evaluate(()=>new Promise(r=>{const map=window.__SHANGHAI_APP__.scene.map;map.once('render',()=>r());map.triggerRepaint();}));
      result.transferTiming.firstMapFrame=Date.now();finishInitial();save();await view('map-before',null,true);
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
      await jump({...camera,center:point(...spec.roof.center),bearing:spec.roof.bearing,elevation:spec.roof.elevation,pitch:spec.roof.pitch,zoom:spec.roof.zoom});await view('map-roof','full',true);
      await architecturalView('map-window-cartouche-stone-garland',{center:point(0,-.35),bearing:21,pitch:56,elevation:10.25,zoom:21.55},[["left corner ruled pier", -2.2, -0.42, 10.97], ["hollow centre of garland", 0.0, -0.42, 10.67], ["stone crown flower", 0.0, -0.686, 11.6894], ["right horn binding", 1.1, -0.6295, 10.7697], ["lower stone knot", 0.0, -0.63, 9.64]]);
      await architecturalView('map-square-window-and-red-hipped-roof',{center:point(0,-.10),bearing:26,pitch:48,elevation:15.05,zoom:21.5},[["rectangular window glass", 0.26, -0.145, 13.54], ["projecting upper flashing", -1.28, -0.77, 16.0], ["red hipped roof", 0.4697, -0.29, 16.6334]]);
      result.ground=await page.evaluate(async probes=>{const scene=window.__SHANGHAI_APP__.scene;await scene.waitForData(10000);
        return probes.map(p=>({...p,found:scene.collisionAt(...p.position)}));},[...spec.ground.map(w=>({name:w.name,position:w.wgs84,expected:w.expected})),...spec.original_group_neighbors.map(n=>({name:'retained neighbor '+n.owner,position:n.ground,expected:'building'}))]);
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);
        }else {
                const targetDistance=row.lod_switch_out_m+80;
      result.distantApproach={switchOutM:row.lod_switch_out_m,requiredEyeDistanceM:targetDistance,positions:[]};
      for(const zoom of [15.55,15.20,14.90]){
        await jump({...camera,zoom,pitch:20,elevation:0,padding:{top:0,right:0,bottom:0,left:0}});
        const observation=await page.evaluate(({lng,lat,height})=>{
          const map=window.__SHANGHAI_APP__.scene.map,t=map.transform;
          const eye=t.getCameraLngLat(), altitude=t.getCameraAltitude();
          const east=(eye.lng-lng)*111319.49*Math.cos(lat*Math.PI/180),north=(eye.lat-lat)*111319.49;
          return {zoom:map.getZoom(),eye:[eye.lng,eye.lat,altitude],rangeM:Math.hypot(east,north,altitude-height*.5)};
        },{lng:row.lng,lat:row.lat,height:row.height_m});
        result.distantApproach.positions.push(observation);save();
        if(observation.rangeM>=targetDistance)break;
      }
      assert.ok(result.distantApproach.positions.at(-1).rangeM>=targetDistance,'Camera has physically crossed the catalog LOD threshold');
      await view('map-distant','distant');

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
