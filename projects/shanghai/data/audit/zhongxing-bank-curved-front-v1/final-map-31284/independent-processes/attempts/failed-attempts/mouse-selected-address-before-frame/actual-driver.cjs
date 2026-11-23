/* Compare an audited, source-owned model with the frozen pre-delivery city view.
 * Run with its map-case.json path, and --control for the prior state. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {createHash} = require('node:crypto');
const {chromium} = require('./system-chromium-cdp-284.cjs');
const caseFile = path.resolve(process.argv[2]);
const spec = JSON.parse(fs.readFileSync(caseFile));
const audit = path.dirname(caseFile);
const ID = spec.id;
const PRIOR = spec.previous;
const control = process.argv.includes('--control');
const phase=process.argv[3];
const phone=['phone','touch'].includes(phase);
const desktopOnly=!phone;
const compositor=['before','mouse','touch','distant'].includes(phase);
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
const addedOwners=[2362];
const declaredOwners=(contract.owners??[contract.owner]).map(o=>o.feature_local_id);
assert.deepEqual(declaredOwners,[2362]);assert.equal(contract.replacement_geometry.type,"Polygon");assert.equal(contract.altitude,0);assert.equal(contract.collision_geometry.type,"Polygon");
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
  const browser=await chromium.launch({headless:false,env:{...process.env,DISPLAY:':53'},executablePath:'/usr/bin/chromium',args:[...(compositor?['--headless=new','--disable-gpu-compositing','--disable-threaded-animation','--disable-threaded-scrolling','--enable-webgl','--disable-client-side-phishing-detection']:[]),'--disable-translate','--disable-features=Translate,TranslateUI','--lang=zh-CN','--ozone-platform=x11','--disable-gpu-program-cache','--no-zygote','--single-process','--in-process-gpu','--window-position=0,0','--no-sandbox',...(process.env.QA_ANGLE_BACKEND?.startsWith('gl')?['--use-gl=angle','--ignore-gpu-blocklist','--disable-gpu-watchdog']:[]),'--use-angle='+(process.env.QA_ANGLE_BACKEND||'swiftshader'),'--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disable-background-networking','--disable-component-update','--disable-sync','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--expose-gc --optimize-for-size --max-old-space-size=114 --max-semi-space-size=1','--disk-cache-size=1048576','--disable-gpu-shader-disk-cache','--force-gpu-mem-available-mb=48',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const mobile=phone;
  const viewport=mobile?{width:390,height:675}:phase==='before'?{width:390,height:315}:phase==='mouse'?{width:480,height:385}:phase==='distant'?{width:460,height:395}:phase==='closeups'?{width:685,height:520}:{width:750,height:545};
  const page=await browser.newPage({viewport,locale:'zh-CN',deviceScaleFactor:1,ignoreHTTPSErrors:true,hasTouch:mobile});
  let calibrated=null; const calibrationView=page.viewportSize();
  if(compositor){result.capture_mode='headless-compositor';}else try {
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
  await page.addInitScript(initialCamera=>{
     Object.defineProperty(navigator,'hardwareConcurrency',{value:1,configurable:true});
     let api;
     Object.defineProperty(window,'maplibregl',{configurable:true,get(){return api},set(v){
       api=v;
       if(typeof v?.setWorkerCount==='function')v.setWorkerCount(1);
       if(typeof v?.Map==='function'){
         const OriginalMap=v.Map;
         v.Map=class extends OriginalMap {
           constructor(options){
             super({...options,center:initialCamera.center,zoom:initialCamera.zoom,bearing:initialCamera.bearing,pitch:initialCamera.pitch,pixelRatio:0.25,maxTileCacheSize:1,antialias:false,canvasContextAttributes:{...options.canvasContextAttributes,antialias:false}});
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
  },['mouse','touch'].includes(phase)&&!fs.existsSync(path.join(out,'selection-origin','process.json'))?{...camera,center:[contract.lng,contract.lat],elevation:0,pitch:0,bearing:0,zoom:20.3,alignAtStartup:true}:{...camera,alignAtStartup:control});
  const physicalMemory=await page.evaluate(()=>navigator.deviceMemory??null);
  await page.addInitScript(()=>Object.defineProperty(navigator,'deviceMemory',{value:2,configurable:true}));
  result.browserProfile={physicalMemory,deviceMemoryProfileGiB:2,shadowQuality:'disabled with scene.setVisualQuality',normalMaps:!control};

  const heap=await page.context().newCDPSession(page);
  let busy=false;
  const trim=setInterval(async()=>{if(busy)return;busy=true;try{await heap.send('Memory.simulatePressureNotification',{level:'moderate'});await heap.send('HeapProfiler.collectGarbage');}catch{}finally{busy=false;}},3000);trim.unref();
  result.browser=browser.version();result.phase=phase;
  page.setDefaultTimeout(180000);
  if(control&&!frozenControl)await page.route('**/data/candidate-city-integrations.json*',r=>r.fulfill({contentType:'application/json',body:data}));
  let permitPicked;
  const selectionFolder=path.join(out,'selection-origin');
  const priorSelection=['mouse','touch'].includes(phase)&&fs.existsSync(path.join(selectionFolder,'process.json'));
  const pickPhase=['mouse','touch'].includes(phase)&&!priorSelection;
  const picked=pickPhase?new Promise(resolve=>{permitPicked=resolve}):Promise.resolve();
  let nextVector=0;
  await page.route(/\.pbf(?:\?|$)/i,async route=>{
    if(pickPhase)await picked;
    const now=Date.now(),start=Math.max(nextVector,now);nextVector=start+900;
    await new Promise(resolve=>setTimeout(resolve,start-now).unref());if(!page.isClosed())await route.continue();
  });
  let permitNear;
  const controlReady=control?new Promise(resolve=>{permitNear=resolve}):Promise.resolve();
  if(pickPhase){await page.addInitScript(()=>document.addEventListener('pointerdown',e=>{
    if(e.target.closest?.('.maplibregl-canvas-container'))window.qa284TrustedPointer={trusted:e.isTrusted,type:e.pointerType,x:e.clientX,y:e.clientY};
  },true));}
  if(control){const guard=setTimeout(()=>permitNear(),45000);guard.unref();}
  const startNetwork=Date.now(),keepPath='/'+review.frozen_macro+'/';
  await page.route(/(?:\.(?:glb|gltf)(?:\.gz)?|\/macros\/[^/]+\/READY\.json)(?:\?|$)|\/assets\/materials\/realism-v[45]\//i,async route=>{
    const file=new URL(route.request().url()).pathname;
    const target=file.includes('/'+ID+'/')||file.includes('/'+PRIOR+'/')||file.includes('/'+(spec.adjacentModel||'no-other-model')+'/');
    const subjectGroup=file.includes(keepPath)&&(file.endsWith('/far.glb')||file.endsWith('/READY.json')||file.includes(group.id)||file.endsWith('/'+group.file));
    const localCell=file.includes(keepPath+'near/'+group.file.split('/').pop().split('-s')[0]+'-');
    const earlierOnly=['mouse','touch'].includes(phase)&&file.includes('/'+PRIOR+'/');
    const delay=subjectGroup?0:localCell?1200:earlierOnly||control&&target?130000:target?0:file.includes('/assets/materials/')?150000:file.includes('/macros/')?130000:155000;
    fs.appendFileSync(path.join(out,'request-order.jsonl'),JSON.stringify({file,delay,at:Date.now()})+'\n');
    if(control && !file.includes('/assets/materials/'))await controlReady;
    if(pickPhase&&(subjectGroup||localCell||file.includes('/'+ID+'/')))await picked;
    if(delay)await new Promise(resolve=>setTimeout(resolve,Math.max(0,startNetwork+delay-Date.now())).unref());
    if(!page.isClosed())await route.continue();
  });
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
  const context={id:ID,selected,control,macro:review.frozen_macro,group:group.id,owner:source,extraOwners,neighbors,adjacentID:spec.adjacentModel};
  const manifest = row && read(row.candidate_manifest);
  async function settle(variant,detail=false){
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.setVisualQuality));
    await page.evaluate(normals=>{const sc=window.__SHANGHAI_APP__.scene;if(sc!==window.__quality){sc.setVisualQuality({shadows:false,surfaceNormals:normals});window.__quality=sc;}},!control);
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
      return !!active && active.feature_local_ids.includes(owner.local_id) && (active.clip_feature_local_ids.includes(owner.local_id)===!control)
        && vectors.every(v=>!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer?.ready));
    },{...context,variant,detail},{polling:400,timeout:240000});
    await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>resolve());m.triggerRepaint();}));
  }
  async function view(name,variant,detail=false){
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
    if(control)await captureFrame(name);
    const state=await page.evaluate(({id,selected,macro,group,owner,extraOwners,neighbors,adjacentID})=>{
      const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,beacons=s.getBuildingBeaconState(),ci=s.getCandidateIntegrationState();
      const sourceState=o=>m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o.key.slice(9)});
      const label=beacons.labelPositions.find(z=>z.id===selected),gl=m.painter.context.gl;
      return {route:location.hash,name:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],mode:app.mode,
        walkDisabled:document.querySelector('#start-walk').disabled,asset:s.getLandmarkAssetState(selected),source:sourceState(owner),
        ...(extraOwners.length?{extraOwnerStates:extraOwners.map(o=>({local_id:o.local_id,state:sourceState(o)}))}:{}),
        adjacentAsset:adjacentID?s.getLandmarkAssetState(adjacentID):undefined,neighbors:neighbors.map(o=>({local_id:o.local_id,state:sourceState(o)})),sections:ci.sourceSections?.filter(x=>x.id===id)??[],clip:ci.clips.find(c=>c.id===id)||null,
        group:ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group)||null,shader:{triangles:ci.shader.triangles,limit:ci.shader.triangleLimit,macroTextures:ci.shader.macroTextures??null,denseMacroTables:ci.shader.denseMacroTables??[]},
        labels:beacons.count,pick:label?s.pickBuildingBeacon(label):null,camera:{center:m.getCenter(),elevation:m.getCenterElevation(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom(),padding:m.getPadding(),viewport:[m.getCanvas().clientWidth,m.getCanvas().clientHeight]},
        glError:gl.getError(),contextLost:gl.isContextLost()};
    },context);
    result.views.push({view:name,...state});save();
    assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.equal(state.labels,catalog.resulting_city_count);
    if(!control && (phase!=='architecture' || state.pick!==null))assert.equal(state.pick,selected);assert.equal(new URLSearchParams(state.route.slice(1)).get('landmark'),selected);
    for(const n of state.neighbors){if(!spec.existingCandidateOwners.includes(n.local_id))assert.notEqual(n.state.candidateModel,true);}
    if(detail){
      assert.deepEqual(state.group.feature_local_ids,group.feature_local_ids);
      if(control){assert.deepEqual([...state.group.clip_feature_local_ids].sort((a,b)=>a-b),[...spec.existingGroupOwners].sort((a,b)=>a-b));assert.equal(state.group.triangles,spec.groupTriangles-spec.addedTriangles);}
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
      assert.deepEqual(state.clip.owner,row.owner);assert.deepEqual(state.clip.geometry,row.replacement_geometry);
      if(detail && !spec.sourceSectionCount)assert.deepEqual(state.sections,[]);
      if(detail){assert.ok(state.source.candidateModel||state.source.localModel);assert.deepEqual([...state.group.clip_feature_local_ids].sort((a,b)=>a-b),[...(spec.existingGroupOwners||[]),...addedOwners].sort((a,b)=>a-b));assert.equal(state.group.triangles,spec.groupTriangles);if(spec.sourceSectionCount){
        assert.equal(state.sections.length,1);
        const section=state.sections[0];
        assert.equal(section.feature_local_id,source.local_id);
        assert.equal(section.macro_id,review.frozen_macro);
        assert.equal(section.segments,spec.sourceSectionCount);
        assert.equal(section.roof_m,row.source_section_caps.roof_m);
      }}
    }
    if(!control)await captureFrame(name);
  }
  async function captureFrame(name){
    if(compositor){clearInterval(trim);await heap.send('HeapProfiler.collectGarbage');console.log('[frame] collecting signed image',name);}
    await page.waitForFunction(() => {
      const loading = document.getElementById('loading');
      if (!loading) return true;
      const style = getComputedStyle(loading);
      return style.visibility === 'hidden' || (Number(style.opacity) === 0 && style.pointerEvents === 'none');
    }, undefined, {polling: 254,timeout: 180000});
    await page.waitForFunction(()=>{
      const cover=document.querySelector('#loading');if(!cover)return false;
      const css=getComputedStyle(cover),scene=window.__SHANGHAI_APP__?.scene;
      return cover.classList.contains('loaded')&&css.visibility==='hidden'&&css.opacity==='0'&&css.pointerEvents==='none'&&scene&&!scene.map.isMoving();
    },null,{polling:300,timeout:300000});
    console.log('[frame] scene opaque and settled',name);
    const frame=await page.evaluate(()=>new Promise(resolve=>{
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
    assert.equal(frame.profile.pixelRatio,.25);assert.ok(frame.profile.renderer);
    result.browserProfile.map=frame.profile;
      const bounds=frame.bounds;
      assert.equal(bounds.dpr,1);
      assert.ok(bounds.href.startsWith(base));
      if(!compositor)assert.ok(bounds.focus,'X11 browser must have keyboard focus');
      const target=path.join(out,name+'.png');
      assert.deepEqual([bounds.width,bounds.height],[calibrationView.width,calibrationView.height]);
      if(compositor){
        const devtools=await page.context().newCDPSession(page);
        console.log('[frame] compositor export',name);
        const shot=await devtools.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
        storeCapture(target,Buffer.from(shot.data,'base64'));
        (result.compositorCaptures??=[]).push({file:name+'.png',sha256:sha(fs.readFileSync(target)),width:bounds.width,height:bounds.height,canvas:frame.canvas,method:'Page.captureScreenshot',fromSurface:true});
      }else{
        const displaySource=path.join(out,name+'-x11-root.png');
        const x=calibrated[0],y=calibrated[1];
        const rect=bounds.width+'x'+bounds.height+'+'+x+'+'+y;
        const commandEnv={...process.env,DISPLAY:':53',MAGICK_THREAD_LIMIT:'1',OMP_NUM_THREADS:'1'};
        x11(displaySource,commandEnv,12500);
        let root=fs.readFileSync(displaySource);
        assert.ok(x+bounds.width<=root.readUInt32BE(16)&&y+bounds.height<=root.readUInt32BE(20));
        crop(displaySource,rect,target,commandEnv);
        (result.displayCaptures??=[]).push({display:':53',bounds,rectangle:rect,displayImage:path.basename(displaySource),displayImageSha256:sha(root)});
      }
      let image=fs.readFileSync(target);
      assert.ok(image.length>1000&&image.readUInt32BE(16)===bounds.width&&image.readUInt32BE(20)===bounds.height);
      result.screenshots.push({file:name+'.png',bytes:image.length,sha256:sha(image)});
      const webgl=Buffer.from(frame.png.split(',')[1],'base64'),filename=name+'-webgl.png';
      assert.equal(webgl.readUInt32BE(16),frame.canvas.width);
      assert.equal(webgl.readUInt32BE(20),frame.canvas.height);assert.ok(webgl.length>1000);
      storeCapture(path.join(out,filename),webgl);
      (result.webglCaptures??=[]).push({file:filename,sha256:sha(webgl),bytes:webgl.length,...frame.canvas});
      save();
  }
  async function jump(camera){
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
  }
  async function architecturalView(name,shot,coordinates){
    const targets=coordinates.map(([label,x,y,z])=>({name:label,lnglat:point(x,y),z}));
    const attempts=[];
    const options=name.includes('upper-windows')
      ? [[300,50,165,19.85],[420,45,185,19.85],[400,35,185,19.65],[260,60,130,20.1],[400,50,230,19.95],[0,0,0,shot.zoom]]
      : [[0,0,0,shot.zoom],[390,68,150,shot.zoom],[260,60,130,shot.zoom],[120,68,195,shot.zoom]];
    for(const [left,top,bottom,zoom] of options){
      await jump({...camera,...shot,zoom,padding:{left,right:left?30:0,top,bottom}});
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
      attempts.push({left,top,bottom,zoom,targets:clearPoints});
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
    const start=point(0,-4);const city=base+'index.html#lng='+start[0].toFixed(6)+'&lat='+start[1].toFixed(6)+'&mode=overview';
    await page.goto('about:blank');
    await page.goto(city,{waitUntil:'domcontentloaded'});
    let last='';
    const progress=setInterval(async()=>{
      try {
        const current=await page.evaluate(()=>[document.querySelector('#loading-message')?.textContent,!!window.__SHANGHAI_APP__?.scene?.map,location.hash].join(' | '));
        if(current!==last){console.log('[map progress]',current);last=current;}
      } catch {}
    },1500);progress.unref();
    try {
    await page.waitForFunction(()=>!!window.__SHANGHAI_APP__?.scene?.map);
    await closePanel();
    await jump({...camera,center:[contract.lng,contract.lat],elevation:0,pitch:0,bearing:0,zoom:20.3});
    const getHit=id=>{const scene=window.__SHANGHAI_APP__?.scene,map=scene?.map,el=document.querySelector('#loading');
      if(!map||map.isMoving()||!el?.classList.contains('loaded')||getComputedStyle(el).visibility!=='hidden')return false;
      const b=scene.getBuildingBeaconState(),p=b.labelPositions.find(v=>v.id===id||v.memberIds?.includes(id));
      if(!p||scene.pickBuildingBeacon(p)!==p.id)return false;
      const box=map.getCanvas().getBoundingClientRect(),x=box.x+p.x,y=box.y+p.y,hit=document.elementFromPoint(x,y);
      if(!hit||!map.getCanvasContainer().contains(hit)){
        const previous=window.qa284MarkerAdjustments??=[];
        if(previous.length<4 && Date.now()-(previous.at(-1)?.at||0)>900){
          const padding=[{left:250,right:0,top:10,bottom:135},{left:0,right:100,top:100,bottom:30},{left:0,right:0,top:10,bottom:160},{left:220,right:0,top:10,bottom:220}][previous.length];
          previous.push({x,y,at:Date.now(),hit:hit?.tagName,padding});map.jumpTo({padding});
        }
        return false;
      }
      return {x,y,label:p.id,group:Boolean(p.memberIds),members:p.memberIds||[],route:location.hash,element:hit.tagName,adjustments:window.qa284MarkerAdjustments||[]};};
    const answer=await page.waitForFunction(getHit,ID,{polling:254,timeout:240000});
    const p=await answer.jsonValue();assert.ok(!p.route.includes('landmark='+ID));
    if(touch)await page.touchscreen.tap(p.x,p.y);else await page.mouse.click(p.x,p.y);
    if(p.group){const option=page.locator('dialog.beacon-group-picker[open] [data-landmark="'+ID+'"]');if(touch)await option.tap();else await option.click();}
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,ID);
    const pointer=await page.evaluate(()=>window.qa284TrustedPointer);
    assert.ok(pointer?.trusted&&pointer.type===(touch?'touch':'mouse'));
    (result.physicalSelections??=[]).push({...p,input:touch?'touch':'mouse',selected:ID,pointer,startURL:city});save();permitPicked();
    await view('map-after-physical-'+phase,'full',true);
    } finally { clearInterval(progress); }
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
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));await closePanel();await jump(camera);permitNear();await view('map-before',null,true);
    }else{
      if (['phone','desktop'].includes(phase)) {
        await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
        assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
        const card=page.locator('#district-'+row.districtId+' [data-landmark="'+ID+'"] .card-foot a[href="index.html#landmark='+ID+'&mode=overview"]');
        if (phone) await card.tap(); else await card.click();
        await view(phone?'map-mobile':'map-desktop',null);
        await view(phone?'map-mobile-settled':'map-desktop-settled','full',true);
      } else if (['mouse','touch'].includes(phase)) {
        if(priorSelection){
          const originFile=path.join(selectionFolder,'main-browser.json');
          const origin=JSON.parse(fs.readFileSync(originFile)),closed=JSON.parse(fs.readFileSync(path.join(selectionFolder,'process.json')));
          assert.equal(sha(fs.readFileSync(originFile)),closed.report_sha256);
          assert.equal(sha(fs.readFileSync(path.join(selectionFolder,'actual-driver.cjs'))),closed.driver_sha256);
          assert.equal(origin.scriptSha256,closed.driver_sha256);assert.equal(origin.catalog.sha256,result.catalog.sha256);
          assert.ok(closed.node_closed && closed.remaining_chromium.length===0 && closed.chromium_pids.length);
          const selection=origin.physicalSelections[0];assert.ok(selection.pointer.trusted && selection.input===phase && selection.selected===ID && selection.pointer.type===phase);
          const route='#landmark='+ID+'&mode=overview';
          assert.ok(fs.readFileSync(path.join(selectionFolder,'run.log'),'utf8').includes(route));
          result.physicalSelections=origin.physicalSelections;
          result.selectionCapture={sameBrowser:false,priorExit:closed.exit_code,report:closed.report_sha256,driver:closed.driver_sha256,chromiumPids:closed.chromium_pids,selectedURL:base+'index.html'+route};
          await page.goto(result.selectionCapture.selectedURL,{waitUntil:'domcontentloaded'});
          await page.waitForFunction(()=>!!window.__SHANGHAI_APP__?.scene?.map);
          await closePanel();
          await jump(camera);
          await view('map-after-physical-'+phase,'full',true);
        }else await selectPhysical(phone);
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
      await architecturalView('map-curved-stone-base-and-paired-windows',{center:point(0.0,0.2),bearing:217.54184485088695,pitch:47,elevation:7.07,zoom:20.7},[["中央底层玻璃", 0.3284091494596514, 0.33635518740838677, 2.219352109849595], ["四川中路侧底层石面", -5.520796979496285, 1.7193772062141903, 2.34758733153231], ["福州路侧基座石面", 5.3631290575715225, 1.6114743468171326, 2.3492981852913886], ["中央第一对窗", -0.6371492430448543, 0.3530282456920162, 5.628590237976468], ["南侧中层双窗", -3.4432809696550937, 0.9846150016552713, 9.178556283471053], ["浅陷窗裙", 0.2967236625125862, 0.11106105961379598, 10.908638849664456]]);
      await architecturalView('map-upper-windows-brackets-and-cornice',{center:point(0.0,0.22),bearing:217.54184485088695,pitch:42,elevation:17.22,zoom:20.7},[["北侧中层双窗", 3.4702359887033256, 0.9952855564031466, 12.688626248228118], ["连续腰檐", 0.5368507348752208, -0.3044061848847832, 4.4187208867797665], ["中央檐下双托臂", 1.7410635557192393, -0.2897868380600386, 18.18989833862355], ["挑檐边线", 2.320280219750986, -0.3561240486900701, 18.589570415609437], ["顶层一对窄窗", 0.5985855010139826, 0.3502207243981559, 19.829111646472036], ["弧形女儿墙顶", 0.504926336079176, -0.0855673960939356, 21.578904087292713]]);
      result.ground=await page.evaluate(async probes=>{const scene=window.__SHANGHAI_APP__.scene;await scene.waitForData(10000);
        return probes.map(p=>({...p,found:scene.collisionAt(...p.position)}));},[...spec.ground.map(w=>({name:w.name,position:point(...w.xy),expected:w.expected})),...spec.neighbors.map(id=>({name:'retained neighbor '+id,position:spec.neighborGround[id],expected:'building'}))]);
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
