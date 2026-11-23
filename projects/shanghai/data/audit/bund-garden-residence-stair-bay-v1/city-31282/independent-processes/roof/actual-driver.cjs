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
const PRIOR = 'huangpu-cathedral-school-jiujiang-front';
const phase=process.env.QA_PHASE;
const phases=['control','mobile-card','mobile-pin','desktop-card','desktop-pin','street','roof','lower-stair-windows','upper-stair-windows','distant'];
assert(phases.includes(phase));
const control=phase==='control',mobile=phase.startsWith('mobile-'),desktopOnly=!control&&!mobile;
const localExisting=JSON.parse(fs.readFileSync(path.join(__dirname,'nearby-registered-cards.json')))[0][1];
const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(audit,'../../..');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const out = process.env.QA_OUTPUT_DIR || audit;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const bindings=JSON.parse(fs.readFileSync(path.join(__dirname,'signed-comparison.json')));
const localBytes=f=>{
  if(fs.existsSync(f))return fs.readFileSync(f);
  if(fs.existsSync(f+'.gz'))return require('node:zlib').gunzipSync(fs.readFileSync(f+'.gz'));
  const stage=bindings.stages.find(v=>f===path.join(__dirname,'stage'+v.n,'data/candidate-city-integrations.json'));
  assert.ok(stage,'Unexpected unstaged input '+f);
  const got=execFileSync('curl',['-fsS','--max-time','30',stage.actual_reads['data/candidate-city-integrations.json'].url],{maxBuffer:16*1024*1024});
  assert.equal(sha(got),stage.catalog_sha256);
  return got;
};
const bytes=f=>localBytes(path.join(project,f));
const read = f => JSON.parse(bytes(f));
const review = JSON.parse(fs.readFileSync(path.join(__dirname,'source-proof.json')));
const contract = JSON.parse(fs.readFileSync(path.join(audit,'final-placement-contract.json')));
assert.equal(spec.added_source_clips,0);
assert.equal(contract.replacement_geometry,null);
assert.deepEqual(contract.source_feature_ids,{building:[],building_part:[]});
assert.ok(contract.collision_geometry);
const selected=control?localExisting:ID;
const source=review.owners.find(r=>r.local_id===1555);
const group=review.near_tiles.find(g=>g.feature_local_ids.includes(1555));
assert.deepEqual([...group.feature_local_ids].sort((a,b)=>a-b),[...spec.feature_group].sort((a,b)=>a-b));
const groupCases=[{id:group.id,tile:group,addedOwners:[],existingOwners:[]}],extraOwners=[];
const neighbors=review.owners.filter(r=>spec.neighbors.includes(r.local_id));
assert.equal(neighbors.length,4);
assert.equal(spec.existing_peers.length,0);
const roofNeighbors=spec.original_group_neighbors.map(q=>({name:'保留邻栋 '+q.owner,wgs84:q.ground,expected:'building',original_native:[q.owner]}));
assert.deepEqual(new Set(roofNeighbors.map(v=>v.original_native[0])),new Set(spec.neighbors));
spec.existingCandidateOwners=[];
spec.adjacentModel=null;
const point = (x,y) => {
  const h=contract.heading*Math.PI/180,k=6371008.8*Math.cos(contract.lat*Math.PI/180);
  const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
  return [contract.lng+east/k*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(contract.lat*Math.PI/180))+north/k))*180/Math.PI];
};
const camera = {center:point(...spec.front.center),elevation:spec.front.elevation,pitch:spec.front.pitch,bearing:spec.front.bearing,zoom:spec.front.zoom,padding:{top:0,right:0,bottom:0,left:0}};
const result = {id:ID,mode:control?'frozen-before':'delivered',started:new Date().toISOString(),completed:false,server:base,
  phase,desktopOnly,previousCatalogLastAddition:PRIOR,localExisting,caseSha256:sha(fs.readFileSync(caseFile)),scriptSha256:sha(fs.readFileSync(__filename)),sourceCommit:review.baseline_commit,camera,views:[],screenshots:[],files:[],errors:[],warnings:[],failed:[]};
result.servedRuntime={};
const reportPath=path.join(out,control?'control-browser.json':'main-browser.json');
const save=()=>fs.writeFileSync(reportPath,JSON.stringify(result,null,2)+'\n');
function storeCapture(file,data){fs.writeFileSync(file,data);}
function x11(file,env,timeout) {
  storeCapture(file,execFileSync(process.env.QA_X11_SCANNER,[],{env,timeout,maxBuffer:16*1024*1024}));
}
function crop(source,rect,file,env) {
  storeCapture(file,execFileSync(process.env.QA_X11_SCANNER,[source,...rect.match(/^(\d+)x(\d+)\+(\d+)\+(\d+)$/).slice(1).map(Number).map((_,i,a)=>String(a[(i+2)%4]))],{env,timeout:10000,maxBuffer:16*1024*1024}));
}

async function run() {
  fs.mkdirSync(out,{recursive:true});assert.ok(!fs.existsSync(reportPath),'Use a fresh output directory');
  const catalogFile='data/candidate-city-integrations.json';
  const frozenControl=control && process.env.QA_CONTROL_CATALOG;
  const controlRoot=frozenControl && path.dirname(path.dirname(path.resolve(frozenControl)));
  const data=frozenControl?localBytes(frozenControl):control?execFileSync('git',['show',review.baseline_commit+':projects/shanghai/'+catalogFile],{cwd:path.resolve(project,'../..')}):bytes(catalogFile);
  const catalog=JSON.parse(data); spec.existingCandidateOwners=catalog.models.filter(m=>m.id!==ID&&m.owner?.macro_id===review.frozen_macro&&m.replacement_geometry&&m.source_feature_ids?.building?.length).map(m=>m.owner.feature_local_id); const row=catalog.models.find(r=>r.id===ID);
  result.catalog={sha256:sha(data),count:catalog.resulting_city_count,lastVisibleCatalogRow:catalog.models.at(-1).id};
  assert.equal(catalog.models.at(-1).id,control?PRIOR:ID);
  if(frozenControl){
    assert.equal(result.catalog.sha256,process.env.QA_CONTROL_CATALOG_SHA256,'Frozen predecessor catalog SHA-256');
    assert.equal(result.catalog.count,Number(process.env.QA_CONTROL_CITY_COUNT),'Frozen predecessor catalog size');
  }
  assert.equal(Boolean(row),!control);
  if(row) for(const key of ['owner','source_feature_ids','replacement_geometry','collision_geometry','model_geometry_sha256','display_height_clips'])
    assert.deepEqual(row[key],contract[key],key);
  result.bindings=Object.fromEntries(['src/app.js','src/map-scene.js','src/candidate-overview-camera.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','index.html','landmarks.html']
    .map(f=>[f,sha(frozenControl?fs.readFileSync(path.join(controlRoot,f)):bytes(f))]));
  const independentGets=new Map();
  const captureGet=file=>{
    const data=execFileSync('curl',['--fail','--silent','--show-error','--max-time','45',new URL(file,base).href],{maxBuffer:12*1024*1024});
    independentGets.set(file,{bytes:data.length,sha256:sha(data),at:new Date().toISOString()});
  };
  if(frozenControl)for(const file of [catalogFile,...Object.keys(result.bindings)])captureGet(file);
  if(control||phase==='street')for(const item of review.frozen_bindings){
    if(item.repository_path.endsWith('/far.glb')||groupCases.some(g=>item.repository_path.endsWith('/'+g.tile.file)))captureGet(item.repository_path.replace('projects/shanghai/',''));
  }
  if(phase==='street'||phase==='distant'){
    const sourceManifest=read(row.candidate_manifest);
    for(const [role,asset] of Object.entries(sourceManifest.assets)){
      if(phase==='street'?role==='full':role!=='full')captureGet(path.posix.join(path.posix.dirname(row.candidate_manifest),asset.file));
    }
  }
  const received=new Set();
  const browser=await chromium.launch({headless:false,env:{...process.env,DISPLAY:':53'},executablePath:'/usr/bin/chromium',args:['--disable-translate','--disable-features=Translate,TranslateUI','--lang=zh-CN','--ozone-platform=x11','--disable-gpu-program-cache','--no-zygote','--single-process','--in-process-gpu','--window-position=0,0','--no-sandbox',...(process.env.QA_ANGLE_BACKEND?.startsWith('gl')?['--use-gl=angle','--ignore-gpu-blocklist','--disable-gpu-watchdog']:[]),'--use-angle='+(process.env.QA_ANGLE_BACKEND||'swiftshader'),'--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disable-background-networking','--disable-component-update','--disable-sync','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--expose-gc --optimize-for-size --max-old-space-size=212 --max-semi-space-size=1','--disk-cache-size=1048576','--disable-gpu-shader-disk-cache','--force-gpu-mem-available-mb=96',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const activationOnly=phase==='desktop-pin';
  const viewport=mobile?{width:390,height:650}:['roof','lower-stair-windows','upper-stair-windows','street'].includes(phase)?{width:820,height:580}:phase==='distant'?{width:460,height:345}:control?{width:470,height:390}:phase==='desktop-pin'?{width:470,height:390}:{width:540,height:465};
  const page=await browser.newPage({viewport,locale:'zh-CN',deviceScaleFactor:1,ignoreHTTPSErrors:true,hasTouch:mobile});
  let calibrated=null; let sizing; const calibrationView=page.viewportSize();
  try {
  sizing=await page.context().newCDPSession(page);
  await sizing.send('Network.enable');
  await sizing.send('Network.emulateNetworkConditions',{offline:false,latency:12,downloadThroughput:1250000,uploadThroughput:1500000});
  result.networkProfile={latencyMs:12,downloadBytesPerSecond:1250000};
  const nativeWindow=await sizing.send('Browser.getWindowForTarget');
  await sizing.send('Browser.setWindowBounds',{windowId:nativeWindow.windowId,bounds:{left:0,top:0,width:Math.max(520,calibrationView.width+30),height:calibrationView.height+120}});
  
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
  await page.addInitScript(pixelRatio=>{
     let api;
     Object.defineProperty(window,'maplibregl',{configurable:true,get(){return api},set(v){
       api=v;
       if(typeof v?.setWorkerCount==='function')v.setWorkerCount(1);
       if(typeof v?.Map==='function'){
         const OriginalMap=v.Map;
         v.Map=class extends OriginalMap {
           constructor(options){
             super({...options,pixelRatio,maxTileCacheSize:2,antialias:false,canvasContextAttributes:{...options.canvasContextAttributes,antialias:false}});
             const gl=this.getCanvas().getContext('webgl2');const ext=gl&&gl.getExtension('WEBGL_debug_renderer_info');
             window.initialMapRendering={antialias:gl?.getContextAttributes().antialias,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):null,pixelRatio:this.getPixelRatio(),width:this.getCanvas().width,height:this.getCanvas().height};
           }
         };
       }
     }});
  },activationOnly?0.25:0.375);
  const heapController=await page.context().newCDPSession(page);
  let collecting=false;
  const collect=setInterval(async()=>{if(collecting)return;collecting=true;try{await heapController.send('Memory.simulatePressureNotification',{level:'moderate'});await heapController.send('HeapProfiler.collectGarbage');}catch{}finally{collecting=false;}},4000);collect.unref();
  await page.addInitScript(()=>Object.defineProperty(navigator,'hardwareConcurrency',{value:1,configurable:true}));
  const physicalMemory=await page.evaluate(()=>navigator.deviceMemory??null);
  await page.addInitScript(()=>Object.defineProperty(navigator,'deviceMemory',{value:2,configurable:true}));
  result.browserProfile={physicalMemory,deviceMemoryProfileGiB:2,shadowQuality:'disabled with scene.setVisualQuality',normalMaps:true};

  result.browser=browser.version();
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
  const delayed=[];
  let beginFarRequests;
  const farRequests=new Promise(resolve=>{beginFarRequests=resolve;});
  let admittedAt=null,queueAt=0;
  const release=()=>{if(admittedAt===null){admittedAt=Date.now();beginFarRequests();}};
  const maximumGate=setTimeout(release,46000);maximumGate.unref();
  await page.route(/(?:\.(?:glb|gltf)(?:\.gz)?|\/macros\/[^/]+\/READY\.json)(?:\?|$)/i,async route=>{
    const url=new URL(route.request().url());
    if(!url.pathname.includes('/'+ID+'/')||!url.pathname.includes('-lod.glb')){
      const queued=Date.now();
      await farRequests;
      if(control||desktopOnly){
        const mainMacro=url.pathname.includes('/'+review.frozen_macro+'/');
        const selectedAsset=url.pathname.includes('/'+selected+'/');
        const foreignAsset=url.pathname.includes('/assets/models/candidates/')&&!selectedAsset;
        const otherMacro=url.pathname.includes('/macros/')&&!mainMacro;
        const readyAfter=admittedAt+(foreignAsset?17000:otherMacro?13000:0);
        await new Promise(resolve=>setTimeout(resolve,Math.max(0,readyAfter-Date.now())).unref());
      }
      const when=Math.max(Date.now(),queueAt);queueAt=Math.min(when+1700,Date.now()+10000);
      await new Promise(resolve=>setTimeout(resolve,Math.max(0,when-Date.now())).unref());
      delayed.push({path:url.pathname,waitMs:Date.now()-queued,admittedAt});
    }
    try{await route.continue();}catch(error){if(!page.isClosed())throw error;}
  });
  result.backgroundModelRequestSchedule=delayed;
  page.on('requestfinished',async req=>{
    if(req.url().startsWith(base)&&/\.(pbf|glb|bin|json|gz)(?:\?|$)/.test(req.url())){
      try{const sizes=await req.sizes();if(sizes.responseBodySize>500000)fs.appendFileSync(path.join(out,'large-responses.jsonl'),JSON.stringify({file:req.url(),bytes:sizes.responseBodySize,at:Date.now()})+'\n');}catch{}
    }
  });
  page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')result.failed.push({url:r.url(),failure:r.failure()});});
  page.on('response',r=>{const u=new URL(r.url());if(r.status()>=400)result.failed.push({url:r.url(),status:r.status()});
    if(u.origin===new URL(base).origin&&r.status()===200)received.add(decodeURIComponent(u.pathname.slice(1)));});
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
      const ownerSource=s.map.getSource('overture-buildings');
      const ownerState=ownerSource?s.map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:owner.key.slice(9)}):{};
      const key=macro+'/'+group,draw=c.shader.ownerScopedSources.find(v=>v.id===key);
      return t.active.some(v=>v.id===macro&&v.visible)&&t.detail.active.some(v=>v.id===key)
        &&(!draw||draw.clip_feature_local_ids.length===0)
        &&c.vector.filter(v=>v.active).every(v=>!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer?.ready));
    },{...context,variant,detail},{polling:400,timeout:240000});
    return await page.evaluate(()=>new Promise(resolve=>{
      const map=window.__SHANGHAI_APP__.scene.map;
      map.once('render',()=>{
        const canvas=map.getCanvas(),rect=canvas.getBoundingClientRect();
        resolve({png:canvas.toDataURL('image/png'),
          canvas:{x:rect.x,y:rect.y,w:rect.width,h:rect.height,width:canvas.width,height:canvas.height,pixelRatio:map.getPixelRatio()},
          bounds:{left:screenX,top:screenY,outerWidth,outerHeight,width:innerWidth,height:innerHeight,dpr:devicePixelRatio,focus:document.hasFocus(),href:location.href},
          profile:window.initialMapRendering});
      });
      map.triggerRepaint();
    }));

  }
  async function view(name,variant,detail=false){
    if(phase.endsWith('-card')||phase.endsWith('-pin')){
      const original=await page.evaluate(id=>{
        const s=window.__SHANGHAI_APP__.scene,m=s.map;
        const marker=s.getBuildingBeaconState().labelPositions.find(v=>v.id===id||v.memberIds?.includes(id));
        return {zoom:m.getZoom(),center:m.getCenter(),marker:marker?.id??null};
      },selected);
      if(!original.marker){
        await page.evaluate(point=>{
          const s=window.__SHANGHAI_APP__.scene,m=s.map,c=m.getCenter();
          m.jumpTo({zoom:m.getZoom()-.8,center:[(c.lng+point[0])/2,(c.lat+point[1])/2],padding:{left:0,top:0,right:0,bottom:0}});
          s.refreshBuildingBeacons();s.loadLandmarks();
        },[contract.lng,contract.lat]);
        await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene;return !s.map.isMoving()&&s.getBuildingBeaconState().labelPositions.some(v=>v.id===id||v.memberIds?.includes(id));},selected,{timeout:95000,polling:350});
        result.directoryReframing={initial:original,reason:'The selected model was visible but its geographic marker was outside this viewport.'};
      }
    }
    const frame=await settle(variant,detail);

    if(!control && detail && spec.sourceSectionCount){
      await page.waitForFunction(({id,adjacentID,expected})=>{
        const scene=window.__SHANGHAI_APP__.scene;
        const section=scene.getCandidateIntegrationState().sourceSections.find(item=>item.id===id);
        const adjacentReady=!adjacentID||scene.getLandmarkAssetState(adjacentID)?.visible;
        return adjacentReady && section?.segments===expected;
      },{...context,expected:spec.sourceSectionCount},{polling:400,timeout:240000});
    }
    console.log('[map]',name);
    const state=await page.evaluate(({id,selected,macro,group,groupCases,owner,extraOwners,neighbors,adjacentID})=>{
      const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,beacons=s.getBuildingBeaconState(),ci=s.getCandidateIntegrationState();
      const sourceState=o=>m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o.key.slice(9)});
      const label=beacons.labelPositions.find(z=>z.id===selected)||beacons.labelPositions.find(z=>z.memberIds?.includes(selected)),gl=m.painter.context.gl;
      return {route:location.hash,name:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],mode:app.mode,
        walkDisabled:document.querySelector('#start-walk').disabled,asset:s.getLandmarkAssetState(selected),source:sourceState(owner),
        ...(extraOwners.length?{extraOwnerStates:extraOwners.map(o=>({local_id:o.local_id,state:sourceState(o)}))}:{}),
        adjacentAsset:adjacentID?s.getLandmarkAssetState(adjacentID):undefined,neighbors:neighbors.map(o=>({local_id:o.local_id,state:sourceState(o)})),sections:ci.sourceSections?.filter(x=>x.id===id)??[],clip:ci.clips.find(c=>c.id===id)||null,
        group:ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group)||null,
        ...(groupCases.length>1?{streamedGroups:groupCases.map(g=>ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+g.id)||null)}:{}),shader:{triangles:ci.shader.triangles,limit:ci.shader.triangleLimit,macroTextures:ci.shader.macroTextures??null},
        labels:beacons.count,projectedGroundLabel:label?{id:label.id,members:label.memberIds||[],x:label.x,y:label.y}:null,pick:label?s.pickBuildingBeacon(label):null,camera:{center:m.getCenter(),elevation:m.getCenterElevation(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom()},
        glError:gl.getError(),contextLost:gl.isContextLost()};
    },context);
    result.views.push({view:name,...state});save();
    assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.equal(state.labels,catalog.resulting_city_count);
    if(!control && (phase.endsWith('-pin') || phase.endsWith('-card'))){const label=state.projectedGroundLabel;assert.ok(label&&(label.id===selected||label.members.includes(selected)));assert.equal(state.pick,label.id);}assert.equal(new URLSearchParams(state.route.slice(1)).get('landmark'),selected);
    for(const n of state.neighbors){if(!spec.existingCandidateOwners?.includes(n.local_id))assert.notEqual(n.state.candidateModel,true);}
    if(phase==='street') {
      const frozen=JSON.parse(fs.readFileSync(path.join(__dirname,'isolated-evidence/control/control-browser.json')));
      assert.ok(frozen.completed && frozen.mode==='frozen-before');
      const flags=rows=>rows.map(o=>[o.local_id,Boolean(o.state.candidateModel)]).sort((a,b)=>a[0]-b[0]);
      assert.deepEqual(flags(state.neighbors),flags(frozen.views[0].neighbors),'all 17 neighbors retain the original vector display state');
    }
    assert.equal(state.clip,null);
    assert.deepEqual(state.sections,[]);
    assert.ok(!state.group?.clip_feature_local_ids.includes(1555));
    if(state.group)assert.ok(state.group.clip_feature_local_ids.length===0);
    assert.notEqual(state.source.candidateModel,true);
    if(detail){
      if(state.group)assert.deepEqual([...state.group.feature_local_ids].sort((a,b)=>a-b),[...group.feature_local_ids].sort((a,b)=>a-b));
    }
    if(!control){
      assert.equal(state.name,row.name);assert.equal(state.mode,'overview');assert.equal(state.walkDisabled,true);
      const variant=state.asset.variant==='full'?'web':'lod';
      assert.equal(state.asset.verifiedAsset.sha256,row.assets[variant].sha256);
      assert.equal(state.asset.triangles,row.assets[variant].triangles);
      assert.deepEqual(state.asset.anchor,[row.lng,row.lat]);assert.equal(state.asset.heading,row.heading);
    }
    await page.waitForFunction(()=>{const el=document.getElementById('loading');if(!el)return false;const css=getComputedStyle(el);return el.classList.contains('loaded')&&css.visibility==='hidden'&&css.opacity==='0'&&css.pointerEvents==='none'&&!window.__SHANGHAI_APP__.scene.map.isMoving();},null,{polling:300,timeout:240000});
    assert.equal(frame.profile.pixelRatio,activationOnly?.25:.375);assert.ok(frame.profile.renderer);
    result.browserProfile.map=frame.profile;
      const bounds=frame.bounds;
      assert.equal(bounds.dpr,1);
      assert.ok(bounds.focus&&bounds.href.startsWith(base));
      const displaySource=path.join(out,name+'-x11-root.png');
      assert.deepEqual([bounds.width,bounds.height],[calibrationView.width,calibrationView.height]);
      const x=calibrated[0];
      const y=calibrated[1];
      const rect=bounds.width+'x'+bounds.height+'+'+x+'+'+y;
      const commandEnv={...process.env,DISPLAY:':53',MAGICK_THREAD_LIMIT:'1',OMP_NUM_THREADS:'1'};
      x11(displaySource,commandEnv,12500);
      let root=fs.readFileSync(displaySource);
      assert.ok(x+bounds.width<=root.readUInt32BE(16)&&y+bounds.height<=root.readUInt32BE(20),'Viewport outside recorded X display '+JSON.stringify(bounds));
      const target=path.join(out,name+'.png');
      crop(displaySource,rect,target,commandEnv);
      let image=fs.readFileSync(target);
      assert.ok(image.length>1000&&image.readUInt32BE(16)===bounds.width&&image.readUInt32BE(20)===bounds.height);
      result.screenshots.push({file:name+'.png',bytes:image.length,sha256:sha(image)});
      const webgl=Buffer.from(frame.png.split(',')[1],'base64'),filename=name+'-webgl.png';
      assert.equal(webgl.readUInt32BE(16),frame.canvas.width);
      assert.equal(webgl.readUInt32BE(20),frame.canvas.height);assert.ok(webgl.length>1000);
      storeCapture(path.join(out,filename),webgl);
      (result.webglCaptures??=[]).push({file:filename,sha256:sha(webgl),bytes:webgl.length,...frame.canvas});
      (result.displayCaptures??=[]).push({display:':53',bounds,rectangle:rect,displayImage:path.basename(displaySource),displayImageSha256:sha(root)});
      save();

  }
  async function enterMapLabel(id, previous, position, pointer, report) {
    assert.equal(previous,localExisting);
    assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('landmark'),previous);
    await page.waitForFunction(previous=>{const s=window.__SHANGHAI_APP__?.scene;const cover=document.getElementById('loading');return s && !s.map.isMoving() && cover?.classList.contains('loaded') && getComputedStyle(cover).visibility==='hidden' && new URLSearchParams(location.hash.slice(1)).get('landmark')===previous;},previous,{polling:350,timeout:240000});
    const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
    let hit;
    for(const zoom of [18.65,17.55,16.55]) {
      await jump({center:position,zoom,pitch:0,bearing:0,elevation:0,padding:{top:0,right:0,bottom:0,left:0}});
      const handle=await page.waitForFunction(id=>{
        const s=window.__SHANGHAI_APP__.scene;if(s.map.isMoving())return false;
        const c=s.map.getCanvas(),r=c.getBoundingClientRect();const b=s.getBuildingBeaconState().labelPositions.find(b=>b.id===id||b.memberIds?.includes(id));if(!b)return false;
        for(const dx of [0,-.22,.22])for(const dy of [0,-.18,.18]){
          const px=b.x+dx*(b.width||0),py=b.y+dy*(b.height||0);if(document.elementFromPoint(r.x+px,r.y+py)===c && s.pickBuildingBeacon({x:px,y:py})===b.id)return {x:r.x+px,y:r.y+py,id:b.id,member:b.id!==id,previous:location.hash,viewport:[innerWidth,innerHeight]};
        }return false;
      },id,{polling:250,timeout:24000}).catch(()=>null);
      if(handle){hit=await handle.jsonValue();break;}
    }
    assert.ok(hit,'Target must be reachable by a visible map label');
    await page.evaluate(()=>{window.__verifiedPointer=null;window.addEventListener('pointerup',e=>{const s=window.__SHANGHAI_APP__.scene,c=s.map.getCanvas(),r=c.getBoundingClientRect();window.__verifiedPointer={trusted:e.isTrusted,on_canvas:e.target===c,type:e.pointerType,x:e.clientX,y:e.clientY,picked:s.pickBuildingBeacon({x:e.clientX-r.left,y:e.clientY-r.top})};},{capture:true,once:true});});
    if(pointer==='touch')await page.touchscreen.tap(hit.x,hit.y);else await page.mouse.click(hit.x,hit.y);
    await page.waitForFunction(()=>window.__verifiedPointer!==null,null,{timeout:24000});const event=await page.evaluate(()=>window.__verifiedPointer);
    assert.ok(event.trusted&&event.on_canvas);assert.equal(event.type,pointer);assert.equal(event.picked,hit.id);
    if(hit.member){const choice=page.locator('dialog.beacon-group-picker[open] [data-landmark="'+id+'"]');if(pointer==='touch')await choice.tap();else await choice.click();}
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id,{timeout:120000});
    (result.realBeaconInputs??=[]).push({hit,pointer:event,landed:id});save();
  }

  async function jump(camera){
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
  }
  async function closePanel(){const p=page.locator('#panel-toggle');if(await p.getAttribute('aria-expanded')==='true')await p.click();}
  async function receipt(file,rec,seen){
    if(seen)assert.ok(received.has(file),'Scene never downloaded '+file);
    const got=independentGets.get(file);assert.ok(got,file);
    assert.equal(got.bytes,rec.bytes);assert.equal(got.sha256,rec.sha256);
    result.files.push({file,...got,loadedByScene:received.has(file)});
  }
  try {
    const pin=phase.endsWith('-pin'),entry=control?localExisting:ID;
    assert(catalog.models.find(r=>r.id===PRIOR));
    assert(catalog.models.find(r=>r.id===localExisting));assert(localExisting!==ID);
    await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
    const cards=page.locator('.landmark-card[data-landmark]');
    await cards.first().waitFor({timeout:120000});assert.equal(await cards.count(),catalog.resulting_city_count);
    assert.equal(await page.locator('.landmark-card[data-landmark="'+ID+'"]').count(),control?0:1);
    const card=page.locator('.landmark-card[data-landmark="'+entry+'"] .card-foot a[href="index.html#landmark='+entry+'&mode=overview"]');
    assert.equal(await card.count(),1);
    await page.evaluate(()=>document.addEventListener('pointerup',event=>{
      const card=event.target.closest('[data-landmark]');if(card)sessionStorage.setItem('hankouStairDirectory',JSON.stringify({id:card.dataset.landmark,type:event.pointerType,trusted:event.isTrusted}));
    },{capture:true,once:true}));
    if(mobile)await card.tap();else await card.click();
    await page.waitForFunction(()=>!!window.__SHANGHAI_APP__?.scene?.setVisualQuality);
    await page.evaluate(()=>window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:false,surfaceNormals:true}));
    if(control){await closePanel();await jump(camera);}
    if(phase==='distant'){await closePanel();await jump({...camera,zoom:16.1,pitch:40,elevation:9,padding:{top:0,right:245,bottom:35,left:0}});}
    release();
    await page.waitForFunction(entry=>{
      const scene=window.__SHANGHAI_APP__?.scene,cover=document.getElementById('loading');
      if(!scene||!cover||!cover.classList.contains('loaded')||scene.map.isMoving())return false;
      const st=getComputedStyle(cover);
      return st.visibility==='hidden'&&st.opacity==='0'&&st.pointerEvents==='none'&&new URLSearchParams(location.hash.slice(1)).get('landmark')===entry;
    },entry,{polling:300,timeout:240000});
    const directoryInput=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('hankouStairDirectory')));
    assert.equal(directoryInput.id,entry);assert.equal(directoryInput.type,mobile?'touch':'mouse');assert.equal(directoryInput.trusted,true);
    result.realDirectoryEntry={pointer:directoryInput,id:entry,route:await page.evaluate(()=>location.hash),normalStartupFinished:true};
    if(control){await view('map-before',null,true);}
    else if(phase==='mobile-card'){await view('map-mobile',null);}
    else if(phase==='desktop-card'){await view('map-desktop','full');}
    else if(pin){
      const toggle=page.locator('#panel-toggle');
      if(await toggle.getAttribute('aria-expanded')!=='true')await toggle.click();
      const previousButton=page.locator('button[data-place="'+localExisting+'"]');
      if(!await previousButton.count())await page.locator('#landmark-tab').click();
      await previousButton.scrollIntoViewIfNeeded();
      await page.evaluate(()=>window.addEventListener('pointerup',event=>{
        const b=event.target.closest('button[data-place]');window.__priorPlacePointer={id:b?.dataset.place,trusted:event.isTrusted,type:event.pointerType};
      },{once:true,capture:true}));
      if(mobile)await previousButton.tap();else await previousButton.click();
      await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,localExisting);
      result.startingLandmark=await page.evaluate(()=>({route:location.hash,action:window.__priorPlacePointer}));
      assert.equal(result.startingLandmark.action.id,localExisting);assert.equal(result.startingLandmark.action.trusted,true);
      save();
      await closePanel();
      await jump({center:[contract.lng,contract.lat],zoom:18.65,pitch:0,bearing:0,elevation:0,padding:{top:0,right:0,bottom:0,left:0}});
      await enterMapLabel(ID,localExisting,[contract.lng,contract.lat],mobile?'touch':'mouse',result);
      await view(mobile?'map-mobile-label':'map-desktop-label','full');
    }else{
     await closePanel();
     if(phase==='street'){
      await jump({...camera,center:point(...spec.front.center),bearing:spec.front.bearing,elevation:spec.front.elevation,pitch:spec.front.pitch,zoom:spec.front.zoom});await view('map-hankou-street-bay','full',true);
      result.ground=await page.evaluate(async probes=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(10000);
        return probes.map(p=>({...p,found:s.collisionAt(...p.position)}));},[
        ...[...spec.ground,...roofNeighbors].map(w=>({name:w.name,position:w.wgs84,expected:w.expected}))]);
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);

     }else if(phase==='roof'){
      await jump({...camera,center:point(...spec.roof.center),bearing:spec.roof.bearing,elevation:spec.roof.elevation,pitch:spec.roof.pitch,zoom:spec.roof.zoom});await view('map-stair-bay-roofline','full',true);
     }else if(phase==='lower-stair-windows'){
      await jump({...camera,center:point(0,.09),bearing:347,elevation:5.65,pitch:66,zoom:21.67});await view('map-lower-stair-windows','full',true);
     }else if(phase==='upper-stair-windows'){
      await jump({...camera,center:point(0,.12),bearing:349,elevation:8.10,pitch:57,zoom:21.64});await view('map-upper-stair-windows','full',true);
     }else if(phase==='distant'){
      await jump({...camera,zoom:16.1,pitch:40,elevation:9,padding:{top:0,right:245,bottom:35,left:0}});await view('map-distant','distant');
     }
     if(phase==='street'||phase==='distant'){
       for(const [role,item] of Object.entries(manifest.assets)){
        if(phase==='street'&&role!=='full'||phase==='distant'&&role==='full')continue;
        await receipt(path.posix.join(path.posix.dirname(row.candidate_manifest),item.file),item,role==='full'||role==='lod');
       }
     }
    }
    if(!control){assert.equal(sha(bytes(catalogFile)),result.catalog.sha256);for(const [f,sum] of Object.entries(result.bindings))assert.equal(sha(bytes(f)),sum,'Changed input '+f);}
    if(frozenControl){
      await receipt(catalogFile,{bytes:data.length,sha256:result.catalog.sha256},true);
      for(const [f,digest] of Object.entries(result.bindings)){
        const size=fs.statSync(path.join(controlRoot,f)).size;
        await receipt(f,{bytes:size,sha256:digest},false);
      }
    }
    if(control||phase==='street')for(const rec of review.frozen_bindings.filter(r=>r.repository_path.endsWith('/far.glb')||groupCases.some(g=>r.repository_path.endsWith('/'+g.tile.file))))
      await receipt(rec.repository_path.replace('projects/shanghai/',''),rec,true);
    result.inputDevice=await page.evaluate(()=>({touchPoints:navigator.maxTouchPoints,viewport:[innerWidth,innerHeight]}));
    assert.equal(result.inputDevice.touchPoints===0,control||desktopOnly);
    await Promise.all(runtimeChecks);
    for(const key of ['src/app.js','src/map-scene.js','src/candidate-overview-camera.js','src/building-beacons.js','src/building-beacon-groups.js'])assert.ok(result.servedRuntime[key],key);
    assert.deepEqual(result.errors,[]);assert.deepEqual(result.warnings,[]);assert.deepEqual(result.failed,[]);result.completed=true;
   }catch(e){result.failure=e.stack;result.failureState=await page.evaluate(({id,selected,group,macro})=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return {body:document.body.innerText.slice(0,1000)};
      return {route:location.hash,moving:s.map.isMoving(),stream:s.getStreamingState(),camera:{center:s.map.getCenter(),zoom:s.map.getZoom()},active:s.getLandmarkAssetState(selected),selectedTarget:s.getLandmarkAssetState(id),group:s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.id===macro+'/'+group),labels:s.getBuildingBeaconState().viewportLabelCount};
    },context).catch(err=>({error:String(err)}));throw e;}
  finally{await browser.close();result.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
