/* Compare an audited, source-owned model with the frozen pre-delivery city view.
 * Run with its map-case.json path, and --control for the prior state. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {createHash} = require('node:crypto');
const {chromium} = require('./system-chromium-cdp-tiles.cjs');
const caseFile = path.resolve(process.argv[2]);
const spec = JSON.parse(fs.readFileSync(caseFile));
const audit = process.env.MODEL_AUDIT_DIR || path.dirname(caseFile);
const ID = spec.id;
assert.equal(ID,'huangpu-russell-company-fuzhou-three-bay-front');
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
const group = review.near_tiles.find(g=>g.feature_local_ids.includes(contract.owner.feature_local_id));
const source = review.owners.find(r => r.local_id===contract.owner.feature_local_id);
const groupCases=[{id:group.id,tile:group,addedOwners:[]}];
const addedOwners=[];const peers=spec.existing_group_sources.flatMap(entry=>entry.sources).sort((a,b)=>a-b);
assert.deepEqual(peers,[...spec.existingGroupOwners].sort((a,b)=>a-b));assert(!peers.includes(source.local_id));
const extraOwners=review.owners.filter(r=>r.local_id!==source.local_id&&addedOwners.includes(r.local_id));
const neighbors = review.owners.filter(r=>spec.neighbors.includes(r.local_id));
const point = (x,y) => {
  const h=contract.heading*Math.PI/180,k=6371008.8*Math.cos(contract.lat*Math.PI/180);
  const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
  return [contract.lng+east/k*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(contract.lat*Math.PI/180))+north/k))*180/Math.PI];
};
const camera = {center:point(...spec.front.center),elevation:spec.front.elevation,pitch:spec.front.pitch,bearing:spec.front.bearing,zoom:spec.front.zoom,padding:{top:0,right:0,bottom:0,left:0}};
const detailCameras=JSON.parse(fs.readFileSync(path.join(__dirname,'geometry/formal-cameras.json')));
const result = {id:ID,mode:control?'frozen-before':'delivered',started:new Date().toISOString(),completed:false,server:base,
  desktopOnly,section,caseSha256:sha(fs.readFileSync(caseFile)),scriptSha256:sha(fs.readFileSync(__filename)),sourceCommit:review.baseline_commit,camera,views:[],screenshots:[],files:[],errors:[],warnings:[],failed:[]};
const reportPath=path.join(out,control?'control-browser.json':'main-browser.json');
const save=()=>{const tmp=reportPath+'.pending';fs.writeFileSync(tmp,JSON.stringify(result,null,2)+'\n');fs.renameSync(tmp,reportPath);};
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
  result.bindings=Object.fromEntries(['src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','index.html','landmarks.html']
    .map(f=>[f,sha(frozenControl?fs.readFileSync(path.join(controlRoot,f)):bytes(f))]));
  const received=new Set();
  const browser=await chromium.launch({headless:false,env:{...process.env,DISPLAY:':53'},executablePath:'/usr/bin/chromium',args:['--headless=new','--disable-accelerated-2d-canvas','--disable-translate','--disable-features=Translate,TranslateUI','--lang=zh-CN','--ozone-platform=x11','--disable-gpu-program-cache','--no-zygote','--single-process','--in-process-gpu','--window-position=0,0','--no-sandbox',...(process.env.QA_ANGLE_BACKEND?.startsWith('gl')?['--use-gl=angle','--ignore-gpu-blocklist','--disable-gpu-watchdog']:[]),'--use-angle='+(process.env.QA_ANGLE_BACKEND||'swiftshader'),'--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disable-background-networking','--disable-component-update','--disable-sync','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--expose-gc --optimize-for-size --max-old-space-size=152 --max-semi-space-size=1','--disk-cache-size=1048576','--disable-gpu-shader-disk-cache','--force-gpu-mem-available-mb=48',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const mobile=['phone','touch'].includes(section);
  const viewport=mobile?{width:390,height:675}:section==='before'?{width:495,height:405}:section==='distant'?{width:460,height:395}:section==='closeups'?{width:600,height:475}:{width:550,height:405};
  const page=await browser.newPage({viewport,locale:'zh-CN',deviceScaleFactor:1,ignoreHTTPSErrors:true,hasTouch:mobile});
  const calibrationView=page.viewportSize();
  result.capture_mode='headless-compositor';
  result.compositorViewport={width:calibrationView.width,height:calibrationView.height,deviceScaleFactor:1};
  await page.addInitScript(center=>{
     let api;
     Object.defineProperty(window,'maplibregl',{configurable:true,get(){return api},set(v){
       api=v;
       if(typeof v?.setWorkerCount==='function')v.setWorkerCount(1);
       if(typeof v?.Map==='function'){
         const OriginalMap=v.Map;
         v.Map=class extends OriginalMap {
           constructor(options){
             super({...options,center,zoom:17.65,pitch:0,bearing:0,pixelRatio:0.25,maxTileCacheSize:2,antialias:false,canvasContextAttributes:{...options.canvasContextAttributes,antialias:false}});
             this.setCenterClampedToGround(false);
             this.jumpTo({center,zoom:17.65,elevation:990,pitch:0,bearing:0});
             window.qa283PhysicalMap=this;window.qa283InitialPhysicalCamera={at:Date.now(),zoom:this.getZoom(),altitude:this.transform.getCameraAltitude()};
             const gl=this.getCanvas().getContext('webgl2');const ext=gl&&gl.getExtension('WEBGL_debug_renderer_info');
             window.initialMapRendering={antialias:gl?.getContextAttributes().antialias,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):null,pixelRatio:this.getPixelRatio(),width:this.getCanvas().width,height:this.getCanvas().height};
           }
         };
       }
     }});
  },[contract.lng,contract.lat]);
  await page.addInitScript(({id,center})=>{
    Object.defineProperty(navigator,'hardwareConcurrency',{value:1,configurable:true});
    const observe=new MutationObserver(()=>{
      const map=window.qa283PhysicalMap;
      if(!map||!document.querySelector('#loading-message')?.textContent.includes('正在铺开道路')||!location.hash.includes(id))return;
      observe.disconnect();
      map.stop();map.setCenterClampedToGround(false);
      map.jumpTo({center,zoom:17.65,elevation:990,bearing:0,pitch:0});
      window.qa283RouteCamera={at:Date.now(),height:map.transform.getCameraAltitude(),zoom:map.getZoom()};
    });
    observe.observe(document,{childList:true,subtree:true,characterData:true});
  },{id:ID,center:[contract.lng,contract.lat]});
  const physicalMemory=await page.evaluate(()=>navigator.deviceMemory??null);
  await page.addInitScript(()=>Object.defineProperty(navigator,'deviceMemory',{value:2,configurable:true}));
  result.browserProfile={physicalMemory,deviceMemoryProfileGiB:2,shadowQuality:'disabled with scene.setVisualQuality',normalMaps:true};

  await page.addInitScript(() => {
    document.addEventListener('pointerdown', event => {
      const card=event.target.closest?.('.landmark-card');
      if(card) sessionStorage.setItem('qa282DirectoryPointer', JSON.stringify({id:card.dataset.landmark, type:event.pointerType, trusted:event.isTrusted}));
      if(event.target.closest?.('.maplibregl-canvas-container')) window.qa282MapPointer={type:event.pointerType,trusted:event.isTrusted,x:event.clientX,y:event.clientY};
    },true);
  });
  await page.addInitScript(() => {
    document.addEventListener('pointerdown', event => {
      const card=event.target.closest?.('.landmark-card');
      if(card) sessionStorage.setItem('qa283DirectoryPointer', JSON.stringify({id:card.dataset.landmark, type:event.pointerType, trusted:event.isTrusted}));
      if(event.target.closest?.('.maplibregl-canvas-container')) window.qa283MapPointer={type:event.pointerType,trusted:event.isTrusted,x:event.clientX,y:event.clientY};
    },true);
  });
  result.browser=browser.version();
  page.setDefaultTimeout(180000);
  if(control&&!frozenControl)await page.route('**/data/candidate-city-integrations.json*',r=>r.fulfill({contentType:'application/json',body:data}));
  const keptNear=group.file.split('/').pop();
  const manifestSizes=new Map(catalog.models.flatMap(v=>Object.values(v.assets??{}).filter(a=>a?.file&&a.bytes).map(a=>['/'+a.file,a.bytes])));
  let startNetwork=0,vectorSlot=0,rangePhase='near';
  await page.route(/\/assets\/materials\/realism-v4\//i,async route=>{
    fs.appendFileSync(path.join(out,'material-request-order.jsonl'),JSON.stringify({url:route.request().url(),at:Date.now()})+'\n');
    await new Promise(resolve=>setTimeout(resolve,75000).unref());
    if(!page.isClosed())await route.continue();
  });
  await page.route(/\.pbf(?:\?|$)/i,async route=>{
    const now=Date.now();const slot=Math.max(now,vectorSlot);vectorSlot=slot+180;
    fs.appendFileSync(path.join(out,'vector-tile-order.jsonl'),JSON.stringify({url:route.request().url(),waitMs:slot-now})+'\n');
    await new Promise(resolve=>setTimeout(resolve,Math.max(0,slot-now)).unref());
    if(!page.isClosed())await route.continue();
  });
  await page.route(/(?:\.(?:glb|gltf)(?:\.gz)?|\/macros\/[^/]+\/READY\.json)(?:\?|$)/i,async route=>{
    const file=new URL(route.request().url()).pathname;
    if(!startNetwork)startNetwork=Date.now();
    const critical=file.includes('/'+ID+'/')||file.includes('/huangpu-caldbeck-macgregor-building/')||file.endsWith('/'+keptNear);
    const near=file.includes('/'+review.frozen_macro+'/');
    const otherMacro=file.includes('/macros/')||file.includes('/city-overrides-');
    const bytes=manifestSizes.get(file);
    const cheapPeer=file.includes('/huangpu-mitsui-bussan-pediment-front/')||file.includes('/huangpu-wayfoong-house/');
    const delay=critical?0:near?350:otherMacro?90000:cheapPeer?30000:bytes&&bytes<1800000?32000:bytes&&bytes<6000000?54000:98000;
    if(cheapPeer){
      while(rangePhase!=='far'&&!page.isClosed())await new Promise(resolve=>setTimeout(resolve,125).unref());
      if(!page.isClosed())await route.continue();return;
    }
    fs.appendFileSync(path.join(out,'city-request-order.jsonl'),JSON.stringify({file,bytes,delay,at:Date.now()})+'\n');
    await new Promise(resolve=>setTimeout(resolve,Math.max(0,startNetwork+delay-Date.now())).unref());
    try{await route.continue();}catch(e){if(!page.isClosed())throw e;}
  });
  page.on('pageerror',e=>result.errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')result.errors.push({url:m.location().url,message:m.text()});if(m.type()==='warning'&&m.text().includes('[Shanghai map]'))result.warnings.push(m.text());});
  page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')result.failed.push({url:r.url(),failure:r.failure()});});
  page.on('response',r=>{const u=new URL(r.url());if(r.status()>=400)result.failed.push({url:r.url(),status:r.status()});
    if(u.origin===new URL(base).origin&&r.status()===200)received.add(decodeURIComponent(u.pathname.slice(1)));});
  const context={id:ID,selected,control,macro:review.frozen_macro,group:group.id,groupCases,owner:source,extraOwners,neighbors,adjacentID:spec.adjacentModel};
  const manifest = row && read(row.candidate_manifest);
  async function settle(variant,detail=false){
    await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene?.setVisualQuality!=null);
    await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene;if(window.__qaQualityForScene!==s){s.setVisualQuality({shadows:false,surfaceNormals:true});window.__qaQualityForScene=s;}});
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
        return t.detail.active.some(v=>v.id===key) && draw && draw.clip_feature_local_ids.includes(1960) && (control || draw.clip_feature_local_ids.includes(owner.local_id));
      });
      return t.active.some(t=>t.id===macro&&t.visible)&&t.detail.active.some(t=>t.id===macro+'/'+group)
        && activeGroups
        &&c.vector.filter(v=>v.active).every(v=>!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer?.ready));
    },{...context,variant,detail},{polling:400,timeout:240000});
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(resolve)));
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
    const state=await page.evaluate(({id,selected,macro,group,groupCases,owner,extraOwners,neighbors,adjacentID})=>{
      const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,beacons=s.getBuildingBeaconState(),ci=s.getCandidateIntegrationState();
      const sourceState=o=>m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o.key.slice(9)});
      const label=beacons.labelPositions.find(z=>z.id===selected)||beacons.labelPositions.find(z=>z.memberIds?.includes(selected)),gl=m.painter.context.gl;
      return {route:location.hash,name:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],mode:app.mode,
        walkDisabled:document.querySelector('#start-walk').disabled,asset:s.getLandmarkAssetState(selected),source:sourceState(owner),
        ...(extraOwners.length?{extraOwnerStates:extraOwners.map(o=>({local_id:o.local_id,state:sourceState(o)}))}:{}),
        adjacentAsset:adjacentID?s.getLandmarkAssetState(adjacentID):undefined,neighbors:neighbors.map(o=>({local_id:o.local_id,state:sourceState(o)})),sections:ci.sourceSections?.filter(x=>x.id===id)??[],clip:ci.clips.find(c=>c.id===id)||null,bands:ci.displayClips.filter(c=>c.id.startsWith(id+'-')),
        group:ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group)||null,
        ...(groupCases.length>1?{streamedGroups:groupCases.map(g=>ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+g.id)||null)}:{}),shader:{triangles:ci.shader.triangles,limit:ci.shader.triangleLimit,macroTextures:ci.shader.macroTextures??null},
        labels:beacons.count,visibleLandmarkLabel:label?{id:label.id,memberIds:label.memberIds??[],x:label.x,y:label.y}:null,pick:label?s.pickBuildingBeacon(label):null,camera:{center:m.getCenter(),elevation:m.getCenterElevation(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom()},
        glError:gl.getError(),contextLost:gl.isContextLost()};
    },context);
    result.views.push({view:name,...state});save();
    assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.equal(state.labels,catalog.resulting_city_count);
    const route=new URLSearchParams(state.route.slice(1));
    if(control){
      assert.equal(route.get('landmark'),null);
      assert.ok(Math.abs(Number(route.get('lng'))-contract.lng)<.0002 && Math.abs(Number(route.get('lat'))-contract.lat)<.0002);
    }else{
      assert.equal(route.get('landmark'),selected);
      assert.equal(state.asset.id,selected);
      if(section==='distant'){const marker=state.visibleLandmarkLabel;assert.ok(marker && (marker.id===selected || marker.memberIds.includes(selected)));assert.equal(state.pick,marker.id);}else if(!['architecture','closeups'].includes(section))assert.equal(state.pick,selected);
      else if(state.pick!==null)assert.equal(state.pick,selected);
    }
    for(const n of state.neighbors){if(!spec.existingCandidateOwners.includes(n.local_id))assert.notEqual(n.state.candidateModel,true);}
    if(detail){
      assert.deepEqual(state.group.feature_local_ids,group.feature_local_ids);
      const expectedOwners=control?peers:[source.local_id,...peers].sort((a,b)=>a-b);assert.deepEqual([...state.group.clip_feature_local_ids].sort((a,b)=>a-b),expectedOwners);assert.equal(state.group.clip_feature_local_ids.includes(source.local_id),!control);
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
      assert.deepEqual(state.clip.owner,contract.owner);
      assert.deepEqual(state.clip.geometry,contract.replacement_geometry);
      if(detail) {
        assert.equal(state.sections.length,1);
        const section=state.sections[0];
        assert.equal(section.feature_local_id,source.local_id);
        assert.equal(section.macro_id,review.frozen_macro);
        assert.equal(section.segments,spec.sourceSectionCount);
        assert.equal(section.roof_m,contract.source_section_caps.roof_m);
      }
      const heightBands=state.bands.map(({id,owner,geometry,min_height,max_height,height_reference})=>({id,owner,geometry,min_height,max_height,height_reference}));
      assert.deepEqual(heightBands,contract.display_height_clips||[]);
      if(detail){
        const priorReport=JSON.parse(fs.readFileSync(path.join(__dirname,'evidence/283/before/control-browser.json')));
        const old=priorReport.views.find(v=>v.group)?.group;assert(old);
        assert.deepEqual(state.group.feature_local_ids,old.feature_local_ids);
        assert.equal(state.group.triangles-old.triangles,spec.addedGroupTriangles);
      }
    }
    await page.waitForFunction(()=>{const app=window.__SHANGHAI_APP__,loader=document.querySelector('#loading');if(!app?.scene||!loader)return false;const css=getComputedStyle(loader);return !app.scene.map.isMoving()&&loader.classList.contains('loaded')&&css.opacity==='0'&&css.visibility==='hidden'&&css.pointerEvents==='none';},null,{timeout:240000,polling:300});
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
      const bounds=frame.bounds;assert.equal(bounds.dpr,1);
      assert.ok(bounds.href.startsWith(base));assert.deepEqual([bounds.width,bounds.height],[calibrationView.width,calibrationView.height]);
      const cdp=await page.context().newCDPSession(page);
      const compositor=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
      const png=Buffer.from(compositor.data,'base64');
      assert.equal(png.readUInt32BE(16),bounds.width);assert.equal(png.readUInt32BE(20),bounds.height);assert.ok(png.length>1000);
      storeCapture(path.join(out,name+'.png'),png);result.screenshots.push({file:name+'.png',bytes:png.length,sha256:sha(png)});
      const gl=Buffer.from(frame.png.split(',')[1],'base64'),glFile=name+'-webgl.png';
      assert.equal(gl.readUInt32BE(16),frame.canvas.width);assert.equal(gl.readUInt32BE(20),frame.canvas.height);assert.ok(gl.length>1000);
      storeCapture(path.join(out,glFile),gl);(result.webglCaptures??=[]).push({file:glFile,bytes:gl.length,sha256:sha(gl),...frame.canvas});
      (result.compositorCaptures??=[]).push({file:name+'.png',sha256:sha(png),bounds,drawingBuffer:frame.canvas,source:'Page.captureScreenshot',captureBeyondViewport:false,fromSurface:true});
      await cdp.detach();save();


  }

  async function clickBeacon(id,prev,center,report) {
    await startWithBothBuildings(prev);
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()),null,{timeout:180000});
    await jump({center,zoom:16.4,pitch:0,bearing:0,elevation:0,padding:{left:0,right:0,top:0,bottom:0}});
    await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene;const p=s.getBuildingBeaconState().labelPositions.find(x=>x.id===id||x.memberIds?.includes(id));if(!p||s.pickBuildingBeacon(p)!==p.id)return false;const b=s.map.getCanvas().getBoundingClientRect(),el=document.elementFromPoint(b.x+p.x,b.y+p.y);return el===s.map.getCanvas()||el?.closest('.maplibregl-canvas-container');},id,{polling:300,timeout:180000});
    const action=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,p=s.getBuildingBeaconState().labelPositions.find(x=>x.id===id||x.memberIds?.includes(id)),b=s.map.getCanvas().getBoundingClientRect();return {x:b.x+p.x,y:b.y+p.y,id:p.id,group:p.memberIds?.length>0,previous:location.hash,viewport:[innerWidth,innerHeight]};},id);
    assert.equal(new URLSearchParams(action.previous.slice(1)).get('landmark'),prev);
    const touch=section==='touch';
    if(touch)await page.touchscreen.tap(action.x,action.y);else await page.mouse.click(action.x,action.y);
    if(action.group){const choice=page.locator('dialog.beacon-group-picker[open] [data-landmark="'+id+'"]');if(touch)await choice.tap();else await choice.click();}
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id,{timeout:180000});
    const pointer=await page.evaluate(()=>window.qa283MapPointer);assert.ok(pointer?.trusted);assert.equal(pointer.type,touch?'touch':'mouse');
    report.realBeacon={...action,pointer,landed:id,action:touch?'physical canvas touch':'physical canvas mouse click'};save();
  }
  async function startWithBothBuildings(id){
    const peer='huangpu-caldbeck-macgregor-building';
    await page.goto(new URL('index.html?retained-owner=1960#landmark='+peer+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(peer=>window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(peer)?.visible===true,peer,{polling:200});
    result.retainedPeer=await page.evaluate(peer=>window.__SHANGHAI_APP__.scene.getLandmarkAssetState(peer),peer);
    assert.equal(result.retainedPeer.verifiedAsset.sha256,catalog.models.find(m=>m.id===peer).assets[result.retainedPeer.variant==='full'?'web':'lod'].sha256);
    await page.evaluate(id=>{const a=window.__SHANGHAI_APP__;void a.selectPlace(a.landmarks.find(p=>p.id===id),{mode:'overview'});},id);
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id);
  }
  async function jump(camera){
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
  }
  async function closePanel(){const p=page.locator('#panel-toggle');if(await p.getAttribute('aria-expanded')==='true')await p.click();}
  async function receipt(file,rec,seen){
    if(seen&&!received.has(file)&&file.endsWith('/near/3_-3-s0-s1.glb.gz')){
      const cfgResponse=await page.request.get(new URL('data/precise-buildings-v6.json',base).href);
      const cfgBytes=await cfgResponse.body();
      assert.equal(cfgResponse.status(),200);assert.equal(sha(cfgBytes),'88138c2fd55c02790965e7f24e8904f9b74b6082ab84ab8bb26918a131f5f80a');
      const macro=JSON.parse(cfgBytes).macros.find(x=>x.id===review.frozen_macro);
      const item=macro.near.find(x=>file.endsWith('/'+x.baseline_file));
      assert.equal(item.baseline_sha256,rec.sha256);
      const active=Object.values(item).find(x=>x&&typeof x==='object'&&x.file&&x.sha256);
      assert.ok(active&&received.has(active.file),'Scene must have loaded its configured replacement file');
      assert.deepEqual(item.featureLocalIds,group.feature_local_ids);
      const actual=await page.request.get(new URL(active.file,base).href);const wire=await actual.body();
      assert.equal(actual.status(),200);assert.equal(wire.length,active.size_bytes);assert.equal(sha(wire),active.sha256);
      result.effectiveStreamedTile={file:active.file,bytes:wire.length,sha256:active.sha256,baselineFile:file,baselineSha256:rec.sha256,configurationSha256:sha(cfgBytes),loadedByScene:true,owners:item.featureLocalIds};
    }else if(seen)assert.ok(received.has(file),'Scene never downloaded '+file);
    const resp=await page.request.get(new URL(file,base).href),data=await resp.body();
    assert.equal(resp.status(),200);assert.equal(data.length,rec.bytes);assert.equal(sha(data),rec.sha256);
    result.files.push({file,bytes:data.length,sha256:sha(data),loadedByScene:received.has(file)});
  }
  try {
    if(control){
      await page.goto(base+'index.html#lng='+contract.lng+'&lat='+contract.lat+'&mode=overview',{waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));await closePanel();await jump(camera);await view('map-before',null,true);
    }else{
      if(section==='desktop'||section==='phone'){
        const mobile=section==='phone';
        await page.setViewportSize(mobile?{width:390,height:675}:{width:600,height:475});
        await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
        assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
        const card=page.locator('#district-'+row.districtId+' [data-landmark="'+ID+'"] .card-foot a[href="index.html#landmark='+ID+'&mode=overview"]');
        if(mobile) await card.tap(); else await card.click();
        await view(mobile?'map-mobile':'map-desktop','full',true);
        result.directoryPointer=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('qa283DirectoryPointer')));assert.ok(result.directoryPointer?.trusted);assert.equal(result.directoryPointer.id,ID);assert.equal(result.directoryPointer.type,mobile?'touch':'mouse');
      }
      if(section==='details'||section==='touch'){
        await clickBeacon(ID,PRIOR,[contract.lng,contract.lat],result);
        await view(section==='touch'?'map-touch-beacon-return':'map-beacon-return','full',true);
      }
      if(section==='architecture'){
        await startWithBothBuildings(ID);
        await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));
        await closePanel();await jump(camera);await view('map-street-facade','full',true);
        await jump({...camera,center:point(...spec.roof.center),bearing:spec.roof.bearing,elevation:spec.roof.elevation,pitch:spec.roof.pitch,zoom:spec.roof.zoom});
        await view('map-roof','full',true);
      result.ground=await page.evaluate(async probes=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(10000);
        return probes.map(p=>({...p,found:s.collisionAt(...p.position)}));},[
        ...spec.ground.map(w=>({name:w.name,position:w.wgs84,expected:w.expected}))]);
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);
      }
      if(section==='closeups'){
        await page.setViewportSize(viewport);
        await startWithBothBuildings(ID);
        await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));
        await closePanel();
        await jump(detailCameras.entrance);
        await view('map-fuzhou-road-three-round-doors-and-eastern-steps','full',true);
        await jump(detailCameras.upper);
        await view('map-three-upper-arches-and-stone-brackets','full',true);
      }
      if(section==='distant'){
        await page.setViewportSize(viewport);
        const desktopReport=path.resolve(out,'../desktop/main-browser.json');
        const desktopClosed=JSON.parse(fs.readFileSync(path.resolve(out,'../desktop/closed.json')));
        const nearBytes=fs.readFileSync(desktopReport),previousNear=JSON.parse(nearBytes).views.find(v=>v.asset?.variant==='full');
        assert.equal(sha(nearBytes),desktopClosed.report_sha256);assert.equal(desktopClosed.exit,0);
        assert.equal(previousNear.asset.verifiedAsset.sha256,manifest.assets.full.sha256);
        const targetCamera={lng:contract.lng,lat:contract.lat,zoom:17.65,pitch:0,bearing:0,altitude:990};
        result.distantTransition={before:{variant:'full',source:'separately verified desktop camera',reportSha256:sha(nearBytes),verified:previousNear.asset.verifiedAsset},publishedDistances:{in:row.lod_switch_in_m,out:row.lod_switch_out_m},camera:targetCamera};save();
        await page.addInitScript(({id,c})=>{
          const move=()=>{const s=window.__SHANGHAI_APP__?.scene;
            if(!s||!s.getBuildingBeaconState()||!location.hash.includes(id)){requestAnimationFrame(move);return;}
            s.map.stop();s.map.setCenterClampedToGround(false);s.setCamera(c);s.loadLandmarks();s.refreshBuildingBeacons();
            window.qa283InitialFar={height:s.map.transform.getCameraAltitude(),zoom:s.map.getZoom(),at:Date.now()};
          };requestAnimationFrame(move);
        },{id:ID,c:targetCamera});
        rangePhase='far';
        await page.goto(new URL('index.html#landmark='+ID+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
        await page.waitForFunction(()=>Boolean(window.qa283InitialFar));
        result.distantTransition.farInput=await page.evaluate(()=>window.qa283InitialFar);result.distantTransition.initialCamera=await page.evaluate(()=>window.qa283InitialPhysicalCamera);result.distantTransition.selectedRouteCamera=await page.evaluate(()=>window.qa283RouteCamera);save();
        let measuring=true;
        const measure=async()=>{
          while(measuring&&!page.isClosed()){
            try{
              const state=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,a=s.getLandmarkAssetState(id);return {variant:a?.variant,status:a?.status,visible:a?.visible,altitude:s.map.transform.getCameraAltitude(),zoom:s.map.getZoom()};},ID);
              fs.appendFileSync(path.join(out,'range-samples.jsonl'),JSON.stringify({at:Date.now(),...state})+'\n');
            }catch{return;}
            await new Promise(resolve=>setTimeout(resolve,1400).unref());
          }
        };void measure();
        await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene;const v=s.getBuildingBeaconState().labelPositions.find(z=>z.id===id||z.memberIds?.includes(id));return v && s.pickBuildingBeacon(v)===v.id;},ID,{timeout:45000,polling:350});
        await view('map-distant','distant');
        measuring=false;result.distantTransition.after=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene;return {variant:s.getLandmarkAssetState(id).variant,altitude:s.map.transform.getCameraAltitude()};},ID);
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
    assert.deepEqual(result.errors,[]);assert.deepEqual(result.failed,[]);result.completed=true;
   }catch(e){result.failure=e.stack;result.failureState=await page.evaluate(({id,selected,group,macro})=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return {body:document.body.innerText.slice(0,1000)};
      return {route:location.hash,moving:s.map.isMoving(),stream:s.getStreamingState(),camera:{center:s.map.getCenter(),zoom:s.map.getZoom()},active:s.getLandmarkAssetState(selected),selectedTarget:s.getLandmarkAssetState(id),group:s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.id===macro+'/'+group),labels:s.getBuildingBeaconState().viewportLabelCount};
    },context).catch(err=>({error:String(err)}));throw e;}
  finally{await browser.close();result.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
