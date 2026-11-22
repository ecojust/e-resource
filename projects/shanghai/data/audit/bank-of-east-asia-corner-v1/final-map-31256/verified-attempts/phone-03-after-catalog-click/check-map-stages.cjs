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
  desktopOnly,caseSha256:sha(fs.readFileSync(caseFile)),scriptSha256:sha(fs.readFileSync(__filename)),sourceCommit:review.baseline_commit,camera,views:[],screenshots:[],files:[],errors:[],warnings:[],failed:[]};
result.servedRuntime={};
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
    assert.equal(result.catalog.sha256,process.env.QA_CONTROL_CATALOG_SHA256,'Frozen predecessor catalog SHA-256');
    assert.equal(result.catalog.count,Number(process.env.QA_CONTROL_CITY_COUNT),'Frozen predecessor catalog size');
  }
  assert.equal(Boolean(row),!control);
  if(row) for(const key of ['owner','source_feature_ids','replacement_geometry','collision_geometry','model_geometry_sha256'])
    assert.deepEqual(row[key],contract[key],key);
  result.bindings=Object.fromEntries(['src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/building-beacon-groups.js','index.html','landmarks.html']
    .map(f=>[f,sha(frozenControl?fs.readFileSync(path.join(controlRoot,f)):bytes(f))]));
  const received=new Set();
  const retainedDrawModels=new Set(catalog.models.filter(item=>
    (item.owners??[item.owner]).some(owner=>owner?.macro_id===review.frozen_macro&&spec.existingGroupOwners.includes(owner.feature_local_id))).map(item=>item.id));
  async function configureBacking(){
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.map));
    await page.evaluate(()=>{const scene=window.__SHANGHAI_APP__.scene;scene.setVisualQuality({shadows:false,surfaceNormals:true});scene.map.setPixelRatio(.5);});
  }

  const browser=await chromium.launch({headless:false,env:{...process.env,DISPLAY:':53'},executablePath:'/usr/bin/chromium',args:['--disable-translate','--disable-features=Translate,TranslateUI','--lang=zh-CN','--ozone-platform=x11','--window-position=0,0','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disable-background-networking','--disable-component-update','--disable-sync','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--max-old-space-size=300 --max-semi-space-size=4','--disk-cache-size=1048576','--disable-gpu-shader-disk-cache','--force-gpu-mem-available-mb=96',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const page=await browser.newPage({viewport:control?{width:420,height:380}:['desktop','mouse'].includes(phase)?{width:768,height:410}:phase==='distant'?{width:440,height:380}:phase==='architecture'?{width:838,height:560}:{width:390,height:505},locale:'zh-CN',deviceScaleFactor:1,ignoreHTTPSErrors:true,hasTouch:!desktopOnly});
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
  result.browser=browser.version();result.phase=phase;
  await page.addInitScript(()=>{
    let api;
    Object.defineProperty(window,'maplibregl',{configurable:true,
      get(){return api;},set(value){api=value;if(typeof api?.setWorkerCount==='function')api.setWorkerCount(1);}});
  });
  const physicalMemory=await page.evaluate(()=>navigator.deviceMemory??null);
  await page.addInitScript(()=>Object.defineProperty(navigator,'deviceMemory',{value:4,configurable:true}));
  result.browserProfile={physicalMemory,deviceMemoryProfileGiB:4,shadowQuality:'off',normalMaps:true};

  page.setDefaultTimeout(180000);
  if(control&&!frozenControl)await page.route('**/data/candidate-city-integrations.json*',r=>r.fulfill({contentType:'application/json',body:data}));
  let resumeTransfers=null, holdTransfers=null;
  function trace(request, state) {
    const u=new URL(request.url());
    if (u.origin===new URL(base).origin && u.pathname.includes('/assets/city-detail/') && u.pathname.includes('/near/'))
      console.log('[normal near asset]', Date.now(), state, u.pathname);
  }
  page.on('request',request=>trace(request,'requested'));
  page.on('response',response=>trace(response.request(),'HTTP '+response.status()));
  page.on('requestfinished',request=>trace(request,'finished'));
  page.on('requestfailed',request=>trace(request,request.failure()?.errorText));
  page.on('pageerror',e=>result.errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')result.errors.push({url:m.location().url,message:m.text()});if(m.type()==='warning'&&m.text().includes('[Shanghai map]'))result.warnings.push(m.text());});
  const pendingDelays=new Set();
  browser.once('disconnected',()=>{for(const wake of pendingDelays)wake();pendingDelays.clear();});
  async function delayTransfer(ms) {
    if(!browser.isConnected())return;
    await new Promise(resolve=>{
      const wake=()=>{clearTimeout(timer);pendingDelays.delete(wake);resolve();};
      const timer=setTimeout(wake,ms);pendingDelays.add(wake);
    });
  }
  let nextOtherTile=Date.now()+12000;
  const prescribedNear=groupCases.map(g=>'/near/'+path.posix.basename(g.tile.file));
  result.transferTiming={spacingOtherNearMs:9000,otherNearFirstDelayMs:42000,priorityPath:prescribedNear,requests:[]};
  await page.route(/\/assets\/city-detail\/macros\/[^?#]+\/near\/[^?#]+\.glb(?:\.gz)?(?:[?#]|$)/i,async route=>{
    const u=new URL(route.request().url());const started=Date.now();
    if(!prescribedNear.some(p=>u.pathname.includes(p))){
      const when=Math.max(started+42000,nextOtherTile);nextOtherTile=when+9000;
      if(when>started)await delayTransfer(when-started);
    }
    result.transferTiming.requests.push({path:u.pathname,queuedAt:started,continuedAt:Date.now()});
    try{await route.continue();}catch(error){if(!page.isClosed()&&!String(error).includes('Invalid InterceptionId'))throw error;}
  });
  let nextLandmark = Date.now();
  result.otherLandmarkTransfers=[];
  await page.route(/\/assets\/models\/(?!landmarks\/index)[^?#]+\.glb(?:\.gz)?(?:[?#]|$)/i,async route=>{
    const u=new URL(route.request().url()),queued=Date.now();
    if(![...retainedDrawModels].some(id=>u.pathname.includes(id))&&!u.pathname.includes(ID)&&!u.pathname.includes(PRIOR)&&(!spec.adjacentModel||!u.pathname.includes(spec.adjacentModel))){
      const scheduled=Math.max(queued+2000,nextLandmark);nextLandmark=scheduled+2400;
      await delayTransfer(scheduled-queued);
    }
    result.otherLandmarkTransfers.push({path:u.pathname,queuedAt:queued,continuedAt:Date.now()});
    try{await route.continue();}catch(error){if(browser.isConnected()&&!page.isClosed()&&!String(error).includes('Invalid InterceptionId'))throw error;}
  });
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
    if(!control && !detail && spec.sourceSectionCount && name!=='map-distant'){
      await page.waitForFunction(({id,adjacentID,expected})=>{
        const scene=window.__SHANGHAI_APP__.scene;
        const section=scene.getCandidateIntegrationState().sourceSections.find(item=>item.id===id);
        const adjacentReady=!adjacentID||scene.getLandmarkAssetState(adjacentID)?.visible;
        return adjacentReady && section?.segments===expected;
      },{...context,expected:spec.sourceSectionCount},{polling:400,timeout:240000});
    }
    console.log('[map]',name);
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
      if(detail){assert.ok(state.source.candidateModel||state.source.localModel);assert.deepEqual([...state.group.clip_feature_local_ids].sort((a,b)=>a-b),[...primaryCase.existingOwners,...primaryCase.addedOwners].sort((a,b)=>a-b));assert.equal(state.group.triangles,primaryCase.groupTriangles);if(spec.sourceSectionCount){
        assert.equal(state.sections.length,1);
        const section=state.sections[0];
        assert.equal(section.feature_local_id,source.local_id);
        assert.equal(section.macro_id,review.frozen_macro);
        assert.equal(section.segments,spec.sourceSectionCount);
        assert.equal(section.roof_m,row.source_section_caps.roof_m);
      }}
    }
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
    holdTransfers=new Promise(resolve=>{resumeTransfers=resolve;});
    console.log('[capture] viewport ready',name);
    try {
      const bounds=await page.evaluate(()=>({left:screenX,top:screenY,outerWidth,outerHeight,width:innerWidth,height:innerHeight,dpr:devicePixelRatio,focus:document.hasFocus(),href:location.href}));
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
      (result.displayCaptures??=[]).push({display:':53',bounds,rectangle:rect,displayImage:path.basename(source),displayImageSha256:sha(root)});
      save();
    } finally {if(holdTransfers){resumeTransfers();holdTransfers=null;}}
  }
  async function jump(camera){
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
    await jump({...camera,center:[contract.lng,contract.lat],elevation:0,pitch:0,bearing:0,zoom:16.4});
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
    await settle('full',true);
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
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));
      await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene;s.setVisualQuality({shadows:false,surfaceNormals:true});s.map.setPixelRatio(.65);});
      await closePanel();await jump(camera);await view('map-before',null,true);
    }else{
      if (['phone','desktop'].includes(phase)) {
        await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
        assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
        const card=page.locator('#district-'+row.districtId+' [data-landmark="'+ID+'"] .card-foot a[href="index.html#landmark='+ID+'&mode=overview"]');
        if (phone) await card.tap(); else await card.click();
        await configureBacking();
        await view(phone?'map-mobile':'map-desktop',null);
        await view(phone?'map-mobile-settled':'map-desktop-settled','full',true);
      } else if (['mouse','touch'].includes(phase)) {
        await selectPhysical(phone);
      } else {
        await page.goto(base+'index.html#landmark='+ID+'&mode=overview',{waitUntil:'domcontentloaded'});
        await configureBacking();
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
      await architecturalView('map-four-column-entrance',{center:point(0,.26),bearing:contract.heading-8,pitch:58,elevation:3.1,zoom:21.1},[["variegated marble column", -1.968, -0.0449, 1.07], ["marble lintel", 0.42, 0.079, 2.52], ["shoulder of pediment", 1.12, 0.083, 4.52], ["recessed red square", 0.1, 0.0795, 3.21]]);
      await architecturalView('map-square-crown-and-slits',{center:point(0,1.95),bearing:contract.heading+9,pitch:48,elevation:30.8,zoom:21.6},[["small crown dark slit", -0.35, 2.17, 31.34], ["small crown dark slit", 0.04, 2.17, 31.34], ["small crown dark slit", 0.43, 2.17, 31.34], ["crown side pier", 0.71, 1.95, 31.16]]);
      result.ground=await page.evaluate(async probes=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(10000);
        return probes.map(p=>({...p,found:s.collisionAt(...p.position)}));},[
        ...spec.ground.map(w=>({name:w.name,position:point(...w.xy),expected:w.expected})),
        ...neighbors.map(n=>({name:'retained neighbor '+n.local_id,position:spec.neighborGround[n.local_id],expected:'building'}))]);
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);
        }else {
          await jump({...camera,zoom:15.15,pitch:15,elevation:0});await view('map-distant','distant');
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
