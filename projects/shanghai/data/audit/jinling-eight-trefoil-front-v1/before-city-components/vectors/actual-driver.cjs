/* Compare an audited, source-owned model with the frozen pre-delivery city view.
 * Run with its map-case.json path, and --control for the prior state. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {createHash} = require('node:crypto');
const {chromium} = require('./system-chromium-cdp-285.cjs');
const caseFile = path.resolve(process.argv[2]);
const spec = JSON.parse(fs.readFileSync(caseFile));
const audit = path.dirname(caseFile);
const ID = spec.id;
const PRIOR = "huangpu-zhongxing-bank-curved-front";
const phase=process.env.QA_PHASE;
const phases=['control','mobile-card','mobile-pin','desktop-card','desktop-pin','street','roof','recessed-gates','trefoil-and-glass','distant'];
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
const review=JSON.parse(fs.readFileSync(path.join(__dirname,'source-proof.json')));
const contract = JSON.parse(fs.readFileSync(path.join(audit,'final-placement-contract.json')));
assert.equal(spec.sourceSectionCount,0);assert.equal(contract.source_section_caps,undefined);
const selected = control ? localExisting : ID;
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
const result = {id:ID,mode:control?'frozen-before':'delivered',started:new Date().toISOString(),completed:false,server:base,
  phase,desktopOnly,previousCatalogLastAddition:PRIOR,localExisting,caseSha256:sha(fs.readFileSync(caseFile)),scriptSha256:sha(fs.readFileSync(__filename)),sourceCommit:review.baseline_commit,camera,views:[],screenshots:[],files:[],errors:[],warnings:[],failed:[]};
result.servedRuntime={};
const reportPath=path.join(out,control?'control-browser.json':'main-browser.json');
const save=()=>fs.writeFileSync(reportPath,JSON.stringify(result,null,2)+'\n');
async function run() {
  fs.mkdirSync(out,{recursive:true});assert.ok(!fs.existsSync(reportPath),'Use a fresh output directory');
  const catalogFile='data/candidate-city-integrations.json';
  const frozenControl=control && process.env.QA_CONTROL_CATALOG;
  const controlRoot=frozenControl && path.dirname(path.dirname(path.resolve(frozenControl)));
  const data=frozenControl?localBytes(frozenControl):control?execFileSync('git',['show',review.baseline_commit+':projects/shanghai/'+catalogFile],{cwd:path.resolve(project,'../..')}):bytes(catalogFile);
  const catalog=JSON.parse(data),row=catalog.models.find(r=>r.id===ID);
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
  const received=new Set();
  const launch = () => chromium.launch({executablePath:'/usr/bin/chromium',env:{...process.env,DISPLAY:':53',LIBGL_ALWAYS_SOFTWARE:'1',GALLIUM_DRIVER:'llvmpipe',LP_NUM_THREADS:'1',MESA_SHADER_CACHE_DISABLE:'true'},args:['--headless=new','--disable-extensions','--disable-sync','--window-size=480,420','--disable-accelerated-2d-canvas','--disable-back-forward-cache','--disable-features=Translate,TranslateUI,BackForwardCache,PaintHolding','--lang=zh-CN','--no-sandbox','--single-process','--disable-gpu-program-cache','--enable-features=V8FlushBytecode','--ozone-platform=x11','--in-process-gpu','--force-gpu-mem-available-mb=32','--no-zygote','--disable-dev-shm-usage','--disable-background-networking','--disable-component-update','--disk-cache-size=262144','--disable-gpu-shader-disk-cache','--enable-low-end-device-mode','--num-raster-threads=1','--disable-gpu-rasterization','--js-flags=--expose-gc --no-opt --no-sparkplug --optimize-for-size --max-old-space-size=130 --max-semi-space-size=1','--use-angle=swiftshader','--ignore-gpu-blocklist','--disable-gpu-watchdog','--enable-unsafe-swiftshader',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const viewport=control?{width:385,height:360}:mobile?{width:390,height:844}:phase.startsWith('desktop')?{width:740,height:548}:phase==='distant'?{width:760,height:560}:['recessed-gates','trefoil-and-glass','roof'].includes(phase)?{width:740,height:580}:{width:640,height:480};
  let directoryHandoff;
  if(control){
    const directory=fs.readFileSync('/run/codex-docker/user/actual-285/control-entry-pure-html/directory.json');
    assert.equal(sha(directory),'120d245953fb1e6216a2c6a1c92680b73a0c6b25f38c658bbaa57941556a2331');
    directoryHandoff=JSON.parse(directory);
    assert.equal(directoryHandoff.driver,sha(fs.readFileSync('/run/codex-docker/user/actual-285/real-directory-only.cjs')));
    assert.equal(directoryHandoff.catalog_sha256,result.catalog.sha256);assert.equal(directoryHandoff.cards,catalog.resulting_city_count);
    assert.equal(directoryHandoff.first_browser_closed,true);assert.equal(directoryHandoff.pointer.trusted,true);assert.equal(directoryHandoff.pointer.type,'mouse');
    assert.equal(directoryHandoff.pointer.id,localExisting);assert.equal(directoryHandoff.href,base+'index.html#landmark='+localExisting+'&mode=overview');
    fs.writeFileSync(path.join(out,'actual-directory-before-map.json'),directory);
  }
  const browser=await launch();
  const opening=viewport;const page=await browser.newPage({viewport:opening,deviceScaleFactor:control?.75:1,ignoreHTTPSErrors:true,hasTouch:mobile});
  await page.addInitScript(initialCamera=>{
     const nativeRequest=window.requestAnimationFrame.bind(window),nativeCancel=window.cancelAnimationFrame.bind(window);
     const queued=new Map();let serial=0,timer=0;
     function flush(){
       timer=0;const frame=[...queued];queued.clear();
       nativeRequest(time=>{for(const [id,callback] of frame)callback(time);});
     }
     window.requestAnimationFrame=callback=>{const id=++serial;queued.set(id,callback);if(!timer)timer=setTimeout(flush,180);return id;};
     window.cancelAnimationFrame=id=>{queued.delete(id);};
     Object.defineProperty(navigator,'hardwareConcurrency',{value:1,configurable:true});
     let api;
     Object.defineProperty(window,'maplibregl',{configurable:true,get(){return api},set(v){
       api=v;
       if(typeof v?.setWorkerCount==='function')v.setWorkerCount(1);if(typeof v?.setMaxParallelImageRequests==='function')v.setMaxParallelImageRequests(1);
       if(typeof v?.Map==='function'){
         const OriginalMap=v.Map;
         v.Map=class extends OriginalMap {
           addLayer(layer,before){
             if(layer?.id==='shanghai-landmarks-and-walker' && !layer.__delayedCoveredFirstFrames){
               const render=layer.render;
               layer.__delayedCoveredFirstFrames=true;
               layer.render=function(...args){
                 const cover=document.querySelector('#loading');
                 if(cover && !cover.classList.contains('loaded')){window.coveredFramesSkipped=(window.coveredFramesSkipped||0)+1;return;}
                 const scene=window.__SHANGHAI_APP__?.scene;
                 if(scene && !window.appliedFirstFrameBudget){scene.setVisualQuality({shadows:false,surfaceNormals:true});window.appliedFirstFrameBudget=true;}
                 window.actualCustomFrames=(window.actualCustomFrames||0)+1;
                 return render.apply(this,args);
               };
             }
             return super.addLayer(layer,before);
           }
           constructor(options){
             super({...options,center:initialCamera.center,zoom:initialCamera.zoom,bearing:initialCamera.bearing,pitch:initialCamera.alignAtStartup?0:initialCamera.pitch,pixelRatio:0.25,maxTileCacheSize:1,antialias:false,canvasContextAttributes:{...options.canvasContextAttributes,antialias:false}});
             const liveMap=this;
             if(initialCamera.alignAtStartup) {
               let aligned=false;
               const apply=()=>{
                 if(!aligned && document.querySelector('#loading-message')?.textContent.includes('正在铺开道路')) {
                   aligned=true;liveMap.stop();liveMap.jumpTo(initialCamera);observer.disconnect();
                 }
               };
               const observer=new MutationObserver(apply);
               observer.observe(document,{subtree:true,childList:true,characterData:true});apply();
             }
             const gl=this.getCanvas().getContext('webgl2');const ext=gl&&gl.getExtension('WEBGL_debug_renderer_info');
             window.initialMapRendering={antialias:gl?.getContextAttributes().antialias,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):null,pixelRatio:this.getPixelRatio(),width:this.getCanvas().width,height:this.getCanvas().height};
           }
         };
       }
     }});
  },{...camera,alignAtStartup:control});
  await page.addInitScript(controls=>{
    const set=()=>{const scene=window.__SHANGHAI_APP__?.scene;if(!scene?.setVisualQuality)return;
      scene.setVisualQuality({shadows:false,surfaceNormals:true});clearInterval(interval);};
    const interval=setInterval(set,75);
  },control);
  await page.addInitScript(()=>Object.defineProperty(navigator,'deviceMemory',{value:2,configurable:true}));
  const devtools=await page.context().newCDPSession(page);
  let collecting=false;const collect=setInterval(async()=>{if(collecting)return;collecting=true;try{await devtools.send('Memory.simulatePressureNotification',{level:'moderate'});await devtools.send('HeapProfiler.collectGarbage');}catch{}finally{collecting=false;}},6100);collect.unref();
  let lastStatus='';const scenePoll=setInterval(async()=>{
    try{const status=await page.evaluate(()=>({
      message:document.querySelector('#loading-message')?.textContent,loaded:document.querySelector('#loading')?.className,
      available:Boolean(window.__SHANGHAI_APP__),url:location.href,gl:window.initialMapRendering?.renderer
    }));const key=JSON.stringify(status);if(key!==lastStatus){lastStatus=key;fs.appendFileSync(path.join(out,'real-scene-startup.jsonl'),JSON.stringify({at:Date.now(),...status})+'\n');}}catch{}
  },800);scenePoll.unref();
  result.browser=browser.version();result.capture_mode='headless-compositor';
  page.setDefaultTimeout(180000);const metrics=setInterval(()=>{try{const status=fs.readFileSync('/sys/fs/cgroup/memory.current','utf8').trim();fs.appendFileSync(path.join(out,'resource-pressure.jsonl'),JSON.stringify({time:Date.now(),bytes:Number(status),node:process.memoryUsage().rss})+'\n');}catch{}},500);metrics.unref();
  if(control&&!frozenControl)await page.route('**/data/candidate-city-integrations.json*',r=>r.fulfill({contentType:'application/json',body:data}));
  let openRegional;const streamingGate=control?new Promise(r=>{openRegional=r}):Promise.resolve();if(control){const timer=setTimeout(()=>openRegional(),125000);timer.unref();}
  const startNetwork=Date.now(); let nextVector=0;
  let nextRange=Date.now(),releaseVectors;
  const vectorGate=control?new Promise(r=>{releaseVectors=r}):Promise.resolve();
  if(control){const delayed=setTimeout(()=>releaseVectors(),160000);delayed.unref();}
  await page.route(/\.pmtiles(?:\?|$)/i,async route=>{
    await vectorGate;const now=Date.now(),serve=Math.max(now,nextRange);
    nextRange=serve+2300;
    fs.appendFileSync(path.join(out,'range-schedule.jsonl'),JSON.stringify({url:route.request().url(),time:now,serve})+'\n');
    await new Promise(r=>setTimeout(r,serve-now).unref());
    if(!page.isClosed())await route.continue();
  });
  await page.route(/\.(?:png|jpg|webp)(?:\?|$)/i,async route=>{
    const file=new URL(route.request().url()).pathname;
    if(file.includes('/materials/realism-')){
      if(!page.isClosed())await route.continue();return;
    }else{
      if(control)await streamingGate;
      // The panel is closed for the actual street-site comparison. Its offscreen
      // photographs stay in the original request queue until after local geometry.
      if(control&&!file.includes('/'+localExisting+'/')&&!file.includes('/'+ID+'/'))await new Promise(r=>setTimeout(r,Math.max(0,startNetwork+125000-Date.now())).unref());
      const waitMs=Math.max(0,startNetwork+21000-Date.now())+[...file].reduce((n,c)=>n+c.charCodeAt(0),0)%11*130;
      await new Promise(r=>setTimeout(r,waitMs).unref());
    }
    if(!page.isClosed())await route.continue();
  });
  await page.route(/\.pbf(?:\?|$)/i, async route=>{
    await vectorGate;if(control)await new Promise(resolve=>setTimeout(resolve,6500));const now=Date.now(),advance=Math.max(now,nextVector);nextVector=advance+2000;
    await new Promise(r=>setTimeout(r,advance-now).unref());if(!page.isClosed())await route.continue();
  });
  await page.route(/\/macros\/[^/]+\/(?:online-ids|feature-table)\.json(?:\.gz)?(?:\?|$)/i,async route=>{
    const file=new URL(route.request().url()).pathname;
    const wanted=file.includes('/'+review.frozen_macro+'/');
    if(control)await streamingGate;
    if(control && !wanted)await new Promise(resolve=>setTimeout(resolve,file.includes('/14-13720-6694/')?6500:55000));
    if(!page.isClosed())await route.continue();
  });
  await page.route(/(?:\.(?:glb|gltf)(?:\.gz)?|\/macros\/[^/]+\/READY\.json)(?:\?|$)|\/assets\/materials\/realism-v[45]\//i,async route=>{
    const file=new URL(route.request().url()).pathname;
    const must=file.includes('/'+review.frozen_macro+'/')&&(file.endsWith('/far.glb')||file.endsWith('/READY.json')||groupCases.some(g=>file.endsWith('/'+g.tile.file)));
    const subject=file.includes('/'+ID+'/')||file.includes('/'+selected+'/')||file.includes('/'+(spec.adjacentModel||'no-other')+'/');
    if(control&&!file.includes('/assets/materials/')&&!file.includes('/'+localExisting+'/')){
      await streamingGate;
      if(file.includes('/near/'))await new Promise(resolve=>setTimeout(resolve,must?3400:11000));
    }
    const cell=file.includes('/'+review.frozen_macro+'/near/'+group.file.split('/').pop().split('-s')[0]+'-');
    const regionalOverview=control && file.includes('/14-13720-6694/') && (file.endsWith('/READY.json')||file.endsWith('/far.glb'));
    const wait=file.includes('/assets/materials/realism-v4/')?0:must?1000:cell?1600:subject?0:regionalOverview?48000:file.includes('/assets/materials/')?150000:140000;
    await new Promise(r=>setTimeout(r,Math.max(0,startNetwork+wait-Date.now())).unref());
    if(!page.isClosed())await route.continue();
  });
  page.on('pageerror',e=>result.errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')result.errors.push({url:m.location().url,message:m.text()});if(m.type()==='warning'&&m.text().includes('[Shanghai map]'))result.warnings.push(m.text());});
  const runtimeChecks=[];
  page.on('response',response=>{
    const u=new URL(response.url());const headers=response.headers();const range=Object.entries(headers).find(([name])=>name.toLowerCase()==='content-range')?.[1];fs.appendFileSync(path.join(out,'requests-seen.jsonl'),JSON.stringify({at:Date.now(),file:u.pathname,status:response.status(),...(range?{range}:{})})+'\n');const key=u.pathname.replace(/^\//,'');
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
      if(control){
        const draw=c.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group);
        return Boolean(t.active.some(tile=>tile.id===macro&&tile.visible)
          && t.detail.active.some(tile=>tile.id===macro+'/'+group) && draw?.feature_local_ids.includes(owner.local_id)
          && !draw.clip_feature_local_ids.includes(owner.local_id) && ownerState.localModel===true && !ownerState.candidateModel);
      }
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
    await settle(variant,detail);
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
      const label=beacons.labelPositions.find(z=>z.id===selected),gl=m.painter.context.gl;
      return {route:location.hash,name:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],mode:app.mode,
        walkDisabled:document.querySelector('#start-walk').disabled,asset:s.getLandmarkAssetState(selected),source:sourceState(owner),
        ...(extraOwners.length?{extraOwnerStates:extraOwners.map(o=>({local_id:o.local_id,state:sourceState(o)}))}:{}),
        adjacentAsset:adjacentID?s.getLandmarkAssetState(adjacentID):undefined,neighbors:neighbors.map(o=>({local_id:o.local_id,state:sourceState(o)})),sections:ci.sourceSections?.filter(x=>x.id===id)??[],clip:ci.clips.find(c=>c.id===id)||null,
        group:ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group)||null,
        ...(groupCases.length>1?{streamedGroups:groupCases.map(g=>ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+g.id)||null)}:{}),shader:{triangles:ci.shader.triangles,limit:ci.shader.triangleLimit,macroTextures:ci.shader.macroTextures??null},
        labels:beacons.count,projectedGroundLabel:label?{x:label.x,y:label.y}:null,pick:label?s.pickBuildingBeacon(label):null,camera:{center:m.getCenter(),elevation:m.getCenterElevation(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom()},
        glError:gl.getError(),contextLost:gl.isContextLost()};
    },context);
    state.actualVisibleCityFrames=await page.evaluate(()=>window.actualCustomFrames||0);assert(state.actualVisibleCityFrames>0);result.views.push({view:name,...state});save();
    assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.equal(state.labels,catalog.resulting_city_count);
    if(!control && (phase.endsWith('-pin') || phase.endsWith('-card')))assert.equal(state.pick,selected);assert.equal(new URLSearchParams(state.route.slice(1)).get('landmark'),selected);
    for(const n of state.neighbors){if(!spec.existingCandidateOwners?.includes(n.local_id))assert.notEqual(n.state.candidateModel,true);}
    if(detail){
      assert.deepEqual(state.group.feature_local_ids,group.feature_local_ids);
      if(control){assert.equal(state.source.localModel,true);assert.equal(state.group.triangles,primaryCase.groupTriangles-primaryCase.addedTriangles);assert.deepEqual([...state.group.clip_feature_local_ids].sort((a,b)=>a-b),[...primaryCase.existingOwners].sort((a,b)=>a-b));}
      if(spec.groups)assertGroupDraws(groupCases,state.streamedGroups||[state.group],control);
      if(spec.adjacentModel){
        const adjacent=catalog.models.find(model=>model.id===spec.adjacentModel);
        const seen=state.adjacentAsset;
        assert.equal(seen.status,'loaded');assert.equal(seen.visible,true);
        assert.deepEqual(seen.anchor,[adjacent.lng,adjacent.lat]);
        assert.equal(seen.verifiedAsset.sha256,adjacent.assets[seen.variant==='full'?'web':'lod'].sha256);
        if(control){
          assert.deepEqual(state.group.clip_feature_local_ids,[...spec.existingGroupOwners]);
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
      assert.equal(state.name,row.name);assert.equal(state.mode,'overview');assert.equal(state.walkDisabled,true);
      const variant=state.asset.variant==='full'?'web':'lod';
      assert.equal(state.asset.verifiedAsset.sha256,row.assets[variant].sha256);assert.equal(state.asset.triangles,row.assets[variant].triangles);
      assert.deepEqual(state.asset.anchor,[row.lng,row.lat]);assert.equal(state.asset.heading,row.heading);
      assert.deepEqual(state.clip.owner,row.owner);assert.deepEqual(state.clip.geometry,row.replacement_geometry);
      if(detail){assert.ok(state.source.candidateModel||state.source.localModel);assert.deepEqual([...state.group.clip_feature_local_ids].sort((a,b)=>a-b),[...primaryCase.existingOwners,...primaryCase.addedOwners].sort((a,b)=>a-b));assert.equal(state.group.triangles,primaryCase.groupTriangles);if(spec.sourceSectionCount){
        assert.equal(state.sections.length,1);
        const section=state.sections[0];
        assert.equal(section.feature_local_id,source.local_id);
        assert.equal(section.macro_id,review.frozen_macro);
        assert.equal(section.segments,spec.sourceSectionCount);
        assert.equal(section.roof_m,row.source_section_caps.roof_m);
      }}
    }
    await page.waitForFunction(()=>{const el=document.getElementById('loading');if(!el)return false;const css=getComputedStyle(el);return el.classList.contains('loaded')&&css.visibility==='hidden'&&css.opacity==='0'&&css.pointerEvents==='none'&&!window.__SHANGHAI_APP__.scene.map.isMoving();},null,{polling:300,timeout:240000});
    await captureFrame(name,false);
  }
  async function captureFrame(name,secondary){
    const capture=await page.context().newCDPSession(page);
    const frame=await page.evaluate(()=>new Promise(resolve=>{
      const s=window.__SHANGHAI_APP__.scene,m=s.map;
      m.once('render',()=>{const canvas=m.getCanvas(),gl=canvas.getContext('webgl2');resolve({png:canvas.toDataURL('image/png'),width:gl.drawingBufferWidth,height:gl.drawingBufferHeight});});m.triggerRepaint();
    }));
    const glPixels=Buffer.from(frame.png.split(',')[1],'base64');
    assert(glPixels.length>500&&glPixels.readUInt32BE(16)===frame.width&&glPixels.readUInt32BE(20)===frame.height);
    fs.writeFileSync(path.join(out,name+'-webgl.png'),glPixels);
    const webgl={file:name+'-webgl.png',bytes:glPixels.length,sha256:sha(glPixels),width:frame.width,height:frame.height};
    const shot=await capture.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
    const image=Buffer.from(shot.data,'base64');fs.writeFileSync(path.join(out,name+'.png'),image);
    const compositor={file:name+'.png',method:'Page.captureScreenshot',fromSurface:true,sha256:sha(image),width:image.readUInt32BE(16),height:image.readUInt32BE(20)};
    if(secondary){result[name==='registered-vector-building'?'registeredVectorCapture':'registeredMaterialCapture']={compositor,webgl};}
    else{(result.webglCaptures??=[]).push(webgl);(result.compositorCaptures??=[]).push(compositor);result.screenshots.push({file:name+'.png',bytes:image.length,sha256:sha(image)});}
    save();
  }
  async function enterMapLabel(id, previous, position, pointer, report) {
    assert.equal(previous,localExisting);
    assert.equal(new URLSearchParams(new URL(await page.evaluate(()=>location.href)).hash.slice(1)).get('landmark'),previous);
    await page.waitForFunction(previous=>{const s=window.__SHANGHAI_APP__?.scene;const cover=document.getElementById('loading');return s && !s.map.isMoving() && cover?.classList.contains('loaded') && getComputedStyle(cover).visibility==='hidden' && new URLSearchParams(location.hash.slice(1)).get('landmark')===previous;},previous,{polling:350,timeout:240000});
    const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
    let hit;
    for(const zoom of [17.55,18.65,16.55]) {
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
    (report.realBeaconInputs??=[]).push({hit,pointer:event,landed:id});save();
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
    const pin=phase.endsWith('-pin'),entry=(control||pin)?localExisting:ID;
    assert(catalog.models.find(r=>r.id===PRIOR));
    assert(catalog.models.find(r=>r.id===localExisting));assert(localExisting!==ID);
    if(directoryHandoff){await page.goto(directoryHandoff.href);}else{
    await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
    const cards=page.locator('.landmark-card[data-landmark]');
    await page.waitForFunction(()=>document.querySelector('.landmark-card[data-landmark]')!==null,null,{timeout:120000});assert.equal(await cards.count(),catalog.resulting_city_count);
    assert.equal(await page.locator('.landmark-card[data-landmark="'+ID+'"]').count(),control?0:1);
    const card=page.locator('.landmark-card[data-landmark="'+entry+'"] .card-foot a[href="index.html#landmark='+entry+'&mode=overview"]');
    assert.equal(await card.count(),1);
    await page.evaluate(()=>document.addEventListener('pointerup',event=>{
      const card=event.target.closest('[data-landmark]');if(card)sessionStorage.setItem('jinlingTrefoilDirectoryInput',JSON.stringify({id:card.dataset.landmark,type:event.pointerType,trusted:event.isTrusted}));
    },{capture:true,once:true}));
    if(mobile)await card.tap();else await card.click();
    }
    await page.waitForFunction(entry=>{
      const scene=window.__SHANGHAI_APP__?.scene,cover=document.getElementById('loading');
      if(!scene||!cover||!cover.classList.contains('loaded')||scene.map.isMoving())return false;
      const st=getComputedStyle(cover);
      return st.visibility==='hidden'&&st.opacity==='0'&&st.pointerEvents==='none'&&new URLSearchParams(location.hash.slice(1)).get('landmark')===entry;
    },entry,{polling:300,timeout:240000});
    result.initialMapRendering=await page.evaluate(()=>({...window.initialMapRendering,covered_frames_deferred:window.coveredFramesSkipped||0}));
    const directoryInput=directoryHandoff?directoryHandoff.pointer:await page.evaluate(()=>JSON.parse(sessionStorage.getItem('jinlingTrefoilDirectoryInput')));
    assert.equal(directoryInput.id,entry);assert.equal(directoryInput.type,mobile?'touch':'mouse');assert.equal(directoryInput.trusted,true);
    result.realDirectoryEntry={...(directoryHandoff?{two_browsers:true,actual_directory_handoff:directoryHandoff}:{}),pointer:directoryInput,id:entry,route:await page.evaluate(()=>location.hash),normalStartupFinished:true};
    if(control){
      await page.evaluate(()=>window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:false,surfaceNormals:true}));
      const initial=await devtools.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
      const initialBytes=Buffer.from(initial.data,'base64');
      const initialName='ordinary-previous-city-startup.png';fs.writeFileSync(path.join(out,initialName),initialBytes);
      result.previousCityOpening={file:initialName,sha256:sha(initialBytes),bytes:initialBytes.length,width:initialBytes.readUInt32BE(16),height:initialBytes.readUInt32BE(20),
        ...(await page.evaluate(()=>({url:location.href,registered:window.__SHANGHAI_APP__.landmarks.length,covered:document.querySelector('#loading').getBoundingClientRect().width>0&&getComputedStyle(document.querySelector('#loading')).visibility!=='hidden',renderFrames:window.actualCustomFrames||0})))};
      result.previousCityOpening.surfaceState=await page.evaluate(()=>window.__SHANGHAI_APP__.scene.getRealismState().surfaces);
      assert.equal(result.previousCityOpening.surfaceState.textures,12);
      save();await closePanel();await jump(camera);
      releaseVectors();
      const expectedSourceIDs=[...neighbors,source].map(r=>r.key.replace(/^building:/,''));
      const french=catalog.models.find(r=>r.id===localExisting);expectedSourceIDs.push(french.source_feature_ids.building[0]);
      await page.waitForFunction(({id,ids})=>{
        const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState(id);
        if(a?.status!=='loaded'||!a.visible||!a.verifiedAsset?.sha256||!m.getSource('overture-buildings'))return false;
        const hits=new Set(m.querySourceFeatures('overture-buildings',{sourceLayer:'building'}).map(f=>f.id??f.properties.id));
        return ids.every(id=>hits.has(id));
      },{id:localExisting,ids:expectedSourceIDs},{polling:1200,timeout:100000});
      result.loadedVectorEvidence=await page.evaluate(({id,ids})=>{
        const s=window.__SHANGHAI_APP__.scene,m=s.map;
        const features=m.querySourceFeatures('overture-buildings',{sourceLayer:'building'});
        const matched=features.filter(f=>ids.includes(f.id??f.properties.id)).map(f=>({id:f.id??f.properties.id,type:f.geometry.type}));
        return {loaded:features.length,matched,selectedBuilding:s.getLandmarkAssetState(id)};
      },{id:localExisting,ids:expectedSourceIDs});
      const previousBuilding=catalog.models.find(r=>r.id===localExisting);
      const shown=result.loadedVectorEvidence.selectedBuilding;
      const asset=previousBuilding.assets[shown.variant==='full'?'web':'lod'];
      assert.equal(shown.verifiedAsset.sha256,asset.sha256);
      assert.equal(shown.triangles,asset.triangles);
      save();await captureFrame('registered-vector-building',true);
      await devtools.send('HeapProfiler.collectGarbage').catch(()=>{});openRegional();
      await page.waitForFunction(groupID=>{
        const s=window.__SHANGHAI_APP__.scene, textures=s.getRealismState().surfaces;
        const detail=s.getStreamingState().detail.active;
        return textures?.textures===12 && textures.byProfile.cityPlaster>0 && detail.some(t=>t.id===groupID);
      },review.frozen_macro+'/'+group.id,{timeout:90000,polling:300});
      result.previousNearBeforeVectors=await page.evaluate(()=>{
        const s=window.__SHANGHAI_APP__.scene;
        return {surfaces:s.getRealismState().surfaces,visibleFrames:window.actualCustomFrames,
          nearCells:s.getStreamingState().detail.active.map(t=>t.id)};
      });
      save();
      await captureFrame('registered-surfaces-before-vector',true);
      await devtools.send('HeapProfiler.collectGarbage').catch(()=>{});
      // Yield the idle local HTTP worker and finish submitting the real textured near draw.
      await page.evaluate(()=>new Promise(resolve=>setTimeout(resolve,6500)));
      await view('map-before',null,true);
    }
    else if(phase==='mobile-card'){await view('map-mobile',null);}
    else if(phase==='desktop-card'){await view('map-desktop','full');}
    else if(pin){
      await enterMapLabel(ID,localExisting,[contract.lng,contract.lat],mobile?'touch':'mouse',result);
      await view(mobile?'map-mobile-label':'map-desktop-label','full');
    }else{
     await closePanel();
     if(phase==='street'){
      await jump(camera);await view('map-jinling-street-front','full',true);
      result.ground=await page.evaluate(async probes=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(10000);
        return probes.map(p=>({...p,found:s.collisionAt(...p.position)}));},[
        ...spec.ground.map(w=>({name:w.name,position:point(...w.xy),expected:w.expected})),
        ...neighbors.map(n=>({name:'retained neighbor '+n.local_id,position:spec.neighborGround[n.local_id],expected:'building'}))]);
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);

     }else if(phase==='roof'){
      await jump({...camera,center:point(...spec.roof.center),bearing:contract.heading+spec.roof.bearingOffset,elevation:spec.roof.elevation,pitch:spec.roof.pitch,zoom:spec.roof.zoom});await view('map-stepped-hoods-and-cornice','full',true);
     }else if(phase==='recessed-gates'){
      await jump({...camera,center:point(13.04,-.35),bearing:-32,elevation:1.7,pitch:76,zoom:21.75});await view('map-recessed-grille-and-timber-door','full',true);
     }else if(phase==='trefoil-and-glass'){
      await jump({...camera,center:point(12.463,.121),bearing:-38,elevation:7.70,pitch:69,zoom:21.7});await view('map-trefoil-and-inset-glass','full',true);
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
    result.registeredSurfaceStats=await page.evaluate(()=>window.__SHANGHAI_APP__.scene.getRealismState().surfaces);
    assert.equal(result.registeredSurfaceStats?.textures,12,'Complete original colour, normal and roughness atlas');
    if(control)assert.ok(result.registeredSurfaceStats.byProfile.cityPlaster>0,'Original local facade surface profile');
    assert.deepEqual(result.errors,[]);
    const servedNeighborBlocks=new Set(['14-13720-6694','14-13720-6693','14-13721-6693']);
    function ordinaryNeighborFallback(message){
      const match=message.match(/^\[Shanghai map\] Error: (14-\d+-\d+) 分块暂不可用，保留在线建筑：/);
      return Boolean(control && result.loadedVectorEvidence?.matched.length>=7 && result.registeredMaterialCapture && match && servedNeighborBlocks.has(match[1]));
    }
    result.neighborFallbackWarnings=result.warnings.filter(ordinaryNeighborFallback);
    assert.deepEqual(result.warnings.filter(warning=>!ordinaryNeighborFallback(warning)),[]);
    assert.deepEqual(result.failed,[]);result.completed=true;
   }catch(e){result.failure=e.stack;result.failureState=await page.evaluate(({id,selected,group,macro})=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return {body:document.body.innerText.slice(0,1000)};
      return {route:location.hash,moving:s.map.isMoving(),stream:s.getStreamingState(),camera:{center:s.map.getCenter(),zoom:s.map.getZoom()},active:s.getLandmarkAssetState(selected),selectedTarget:s.getLandmarkAssetState(id),group:s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.id===macro+'/'+group),labels:s.getBuildingBeaconState().viewportLabelCount};
    },context).catch(err=>({error:String(err)}));throw e;}
  finally{await browser.close();result.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
