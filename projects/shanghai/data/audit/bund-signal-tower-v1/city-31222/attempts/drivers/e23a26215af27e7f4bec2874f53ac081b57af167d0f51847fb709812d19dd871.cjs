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
const segment=process.env.QA_SEGMENT;
const desktopOnly=segment!=='phone' && !control;
const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(audit,'../../..');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const out = process.env.QA_OUTPUT_DIR || audit;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const bytes = f => fs.readFileSync(path.join(project,f));
const read = f => JSON.parse(bytes(f));
const review = read('source/precise/'+ID+'/footprint-review.json');
const contract = JSON.parse(fs.readFileSync(path.join(audit,'final-placement-contract.json')));
const localSectionSegments=(contract.source_section_caps?.geometry?.coordinates??[]).reduce((sum,line)=>sum+line.length-1,0);
assert.equal(localSectionSegments,0);
spec.sourceSectionCount=localSectionSegments;
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
const result = {segment,id:ID,mode:control?'frozen-before':'delivered',started:new Date().toISOString(),completed:false,server:base,
  desktopOnly,caseSha256:sha(fs.readFileSync(caseFile)),scriptSha256:sha(fs.readFileSync(__filename)),sourceCommit:review.baseline_commit,camera,views:[],screenshots:[],files:[],errors:[],warnings:[],failed:[]};
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
  result.bindings=Object.fromEntries(['src/app.js','src/candidate-overview-camera.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','index.html','landmarks.html']
    .map(f=>[f,sha(frozenControl?fs.readFileSync(path.join(controlRoot,f)):bytes(f))]));
  const received=new Set();
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--single-process','--no-zygote','--in-process-gpu','--window-size=430,350','--disable-background-networking','--disable-extensions','--disable-gpu-shader-disk-cache','--disable-back-forward-cache','--disable-breakpad','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--force-gpu-mem-available-mb=48','--disable-accelerated-2d-canvas','--disable-image-animation-resync','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--max-old-space-size=198 --max-semi-space-size=2 --optimize-for-size','--msaa-sample-count=0','--disable-zero-copy','--disk-cache-size=1310720',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const page=await browser.newPage({viewport:{width:segment==='desktop'?870:segment==='return'?790:segment==='phone'?390:segment==='distant'?385:segment==='placement'?844:480,height:segment==='desktop'?660:segment==='return'?550:segment==='phone'?844:segment==='distant'?460:segment==='placement'?636:360},deviceScaleFactor:segment==='phone'?.8:segment==='placement'?.62:.74,ignoreHTTPSErrors:true,hasTouch:segment==='phone'});
  result.browser=browser.version();
  page.setDefaultTimeout(180000);
  if(segment==='placement'||segment==='distant'){
  const cdp=await page.context().newCDPSession(page);
  let gcBusy=false;
  async function reclaim() {
    if(gcBusy||page.isClosed())return;
    gcBusy=true;
    try {await cdp.send('HeapProfiler.collectGarbage');}catch(e){/* The page may close between the two calls. */}
    finally{gcBusy=false;}
  }
  const gcTimer=setInterval(()=>{void reclaim()},9000);gcTimer.unref();
  const networkStart=Date.now();
  result.bootstrap={initialViewport:page.viewportSize(),productionResourceRequests:0,productionResourceResponses:0,
    serializedBinaryTransfers:true,mode:'Two live binary transfers at a time; all original URLs and all HTTP bytes.'};
  const waiting=[],outstanding=new Set();let transfers=0;
  async function gate(route){
    if(transfers>=2)await new Promise(resolve=>waiting.push(resolve));else transfers++;
    outstanding.add(route.request());
    try{await route.continue();}catch(e){release(route.request());}
  }
  function release(request){
    if(!outstanding.delete(request))return;
    const next=waiting.shift();
    if(next)setTimeout(next,120);else transfers--;
  }
  await page.route(/\.(glb|glb\.gz|pbf)(?:\?|$)/,gate);
  page.on('requestfinished',release);page.on('requestfailed',release);
  }
  if(control&&!frozenControl)await page.route('**/data/candidate-city-integrations.json*',r=>r.fulfill({contentType:'application/json',body:data}));
  page.on('pageerror',e=>result.errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')result.errors.push({url:m.location().url,message:m.text()});if(m.type()==='warning'&&m.text().includes('[Shanghai map]'))result.warnings.push(m.text());});
  page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')result.failed.push({url:r.url(),failure:r.failure()});});
  page.on('response',r=>{const u=new URL(r.url());if(r.status()>=400)result.failed.push({url:r.url(),status:r.status()});
    if(u.origin===new URL(base).origin&&r.status()===200)received.add(decodeURIComponent(u.pathname.slice(1)));});
  const context={id:ID,selected,control,macro:review.frozen_macro,group:group.id,owner:source,extraOwners,neighbors,adjacentID:spec.adjacentModel};
  const court=[{"name": "southern doorway", "enu": [5.992193848752323, -7.980852891701164, 2.1]}, {"name": "south window", "enu": [5.992193848752323, -7.980852891701164, 6.45]}, {"name": "north rotunda", "enu": [-3.304544126258287, 8.648265035116111, 6.87]}, {"name": "lower gallery", "enu": [-0.9458646032892006, 7.35550407193447, 11.55]}, {"name": "lower shaft band", "enu": [-2.693109908937436, 5.918585896849263, 17.42]}, {"name": "middle shaft band", "enu": [-2.7650815282012746, 5.864548076569934, 24.53]}, {"name": "crown gallery", "enu": [-2.661122522597953, 5.942602705862298, 36.62]}, {"name": "signal mast and vane", "enu": [-3.8126684308193632, 5.077997581393025, 47.25]}].map(anchor=>{
    const [east,north,height]=anchor.enu;
    const lat=contract.lat+north*180/(Math.PI*6371008.8);
    const lng=contract.lng+east*180/(Math.PI*6371008.8*Math.cos(contract.lat*Math.PI/180));
    return {...anchor,lng,lat,height};
  });
  const manifest = row && read(row.candidate_manifest);
  async function settle(variant,detail=false){
    await page.waitForFunction(({selected,variant,detail,macro,group,owner,control,adjacentID})=>{
      const s=window.__SHANGHAI_APP__?.scene;
      if(!s||s.map.isMoving())return false;
      const a=s.getLandmarkAssetState(selected);
      if(!control&&(!a?.visible||a.status!=='loaded'||(variant&&a.variant!==variant)))return false;
      if(!detail)return true;
      if(adjacentID&&!s.getLandmarkAssetState(adjacentID)?.visible)return false;
      const c=s.getCandidateIntegrationState(),t=s.getStreamingState();
      const active=c.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group);
      return t.active.some(t=>t.id===macro&&t.visible)&&t.detail.active.some(t=>t.id===macro+'/'+group)
        && active && (control||active.clip_feature_local_ids.includes(owner.local_id))
        &&c.vector.filter(v=>v.active).every(v=>!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer?.ready));
    },{...context,variant,detail},{polling:1100,timeout:240000});
    await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>resolve());m.triggerRepaint();}));
  }
  async function view(name,variant,detail=false){
    await settle(variant,detail);
    if(segment==='placement') console.log('[map] near owner ready',name,Date.now());
    if(!control && !detail && spec.sourceSectionCount && name!=='map-distant'){
      await page.waitForFunction(({id,adjacentID,expected})=>{
        const scene=window.__SHANGHAI_APP__.scene;
        const section=scene.getCandidateIntegrationState().sourceSections.find(item=>item.id===id);
        const adjacentReady=!adjacentID||scene.getLandmarkAssetState(adjacentID)?.visible;
        return adjacentReady && section?.segments===expected;
      },{...context,expected:spec.sourceSectionCount},{polling:1100,timeout:240000});
    }
    let earlyImage=null;
    if(name==='map-distant'||name==='map-roof'){
    const frame=await page.evaluate(({id,variant})=>{
      const a=window.__SHANGHAI_APP__,e=document.getElementById('loading'),css=getComputedStyle(e),asset=a.scene.getLandmarkAssetState(id),m=a.scene.map;
      return {actualVariant:asset.variant,expected:variant,visible:asset.visible,moving:m.isMoving(),loaded:e.classList.contains('loaded'),visibility:css.visibility,opacity:css.opacity,pointerEvents:css.pointerEvents,camera:{zoom:m.getZoom(),pitch:m.getPitch(),center:m.getCenter(),bearing:m.getBearing(),elevation:m.getCenterElevation()}};
    },{id:ID,variant});result.preCaptureSurface=frame;save();
    assert.equal(frame.actualVariant,variant);assert.ok(frame.visible&&!frame.moving&&frame.loaded);
    if(frame.visibility!=='hidden'||frame.opacity!=='0'||frame.pointerEvents!=='none'){
      await page.waitForFunction(()=>{const css=getComputedStyle(document.getElementById('loading'));return css.visibility==='hidden' && css.opacity==='0' && css.pointerEvents==='none';},null,{polling:120,timeout:30000});
    }
    const capture=await page.context().newCDPSession(page);
    const picture=await capture.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false,optimizeForSpeed:true});
    earlyImage=Buffer.from(picture.data,'base64');
    const earlyFile=name==='map-roof'?'settled-roof-frame.png':'settled-far-frame.png';
    fs.writeFileSync(path.join(out,earlyFile),earlyImage);
    result.captureBeforeFurtherQueries={file:earlyFile,sha256:sha(earlyImage),received:new Date().toISOString()};save();
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
        group:ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group)||null,shader:{triangles:ci.shader.triangles,limit:ci.shader.triangleLimit,macroTextures:ci.shader.macroTextures??null},
        labels:beacons.count,pick:label?s.pickBuildingBeacon(label):null,camera:{center:m.getCenter(),elevation:m.getCenterElevation(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom()},
        glError:gl.getError(),contextLost:gl.isContextLost()};
    },context);
    if(!control){
      state.courtWitnesses=await page.evaluate(points=>{
        const scene=window.__SHANGHAI_APP__.scene;
        const m=scene.map;
        const beacons=scene.getBuildingBeaconState().labelPositions;
        const selectors=['#explore-panel','#location-card','#building-beacon-legend','.topbar','.map-tools'];
        const hud=selectors.map(sel=>{
          const e=document.querySelector(sel); if(!e||!e.getClientRects().length) return null;
          const r=e.getBoundingClientRect();return {name:sel,left:r.left,top:r.top,right:r.right,bottom:r.bottom};
        }).filter(Boolean);
        const projected=points.map(p=>{
          const elevation=()=>p.height;
          const xy=m.transform.locationToScreenPoint({lng:p.lng,lat:p.lat},{getElevationForLngLat:elevation,getElevationForLngLatZoom:elevation});
          const {x,y}=xy;
          return {name:p.name,enu:p.enu,x,y,inViewport:x>=0&&y>=0&&x<innerWidth&&y<innerHeight,
            coveringBeaconIds:beacons.filter(b=>Math.abs(x-b.x)<=b.width/2&&Math.abs(y-b.y)<=b.height/2).map(b=>b.id),
            coveringHud:hud.filter(h=>x>=h.left&&x<=h.right&&y>=h.top&&y<=h.bottom).map(h=>h.name)};
        });
        return {padding:m.getPadding(),hud,beacons,points:projected};
      },court);
    }
    result.views.push({view:name,...state});save();
    if(segment==='placement')console.log('[map] sampled',name,Date.now());
    assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.equal(state.labels,catalog.resulting_city_count);
    const params=new URLSearchParams(state.route.slice(1));
    if(control){
      assert.equal(params.get('mode'),'overview');
      assert.ok(Math.abs(Number(params.get('lng'))-camera.center[0])<1e-6 && Math.abs(Number(params.get('lat'))-camera.center[1])<1e-6);
      assert.ok(Math.abs(state.camera.center.lng-camera.center[0])<1e-6 && Math.abs(state.camera.center.lat-camera.center[1])<1e-6);
      assert.ok(Math.abs(state.camera.zoom-camera.zoom)<1e-5 && Math.abs(state.camera.bearing-camera.bearing)<1e-5 && Math.abs(state.camera.pitch-camera.pitch)<1e-5);
    }else{
      if(name==='map-roof' && state.pick!==selected){
        const label=state.courtWitnesses.beacons.find(x=>x.id===selected);
        state.roofBeacon={actual:state.pick,anchor:label||null,
          reason:'The elevated roof camera does not require a clickable ground label. Mouse and touch selected the actual label in their respective ordinary sessions.'};
        assert.equal(state.asset.visible,true);assert.equal(state.asset.verifiedAsset.sha256,row.assets.web.sha256);
        assert.equal(state.name,row.name);
      }else assert.equal(state.pick,selected);
      assert.equal(params.get('landmark'),selected);
    }
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
    if(control){assert.deepEqual(state.sections,[]);assert.equal(state.clip,null);assert.notEqual(state.source.candidateModel,true);assert.ok(!state.group.clip_feature_local_ids.includes(source.local_id));}
    else{
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
    await page.waitForFunction(()=>{
      const cover=document.querySelector('#loading'), scene=window.__SHANGHAI_APP__?.scene;
      if(!cover || !scene || scene.map.isMoving())return false;
      const css=getComputedStyle(cover);
      return cover.classList.contains('loaded') && css.visibility==='hidden' && css.opacity==='0' && css.pointerEvents==='none';
    },null,{polling:250,timeout:240000});
    let image=earlyImage;
    if(!image){
      const capture=await page.context().newCDPSession(page);
      const picture=await capture.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false,optimizeForSpeed:true});
      image=Buffer.from(picture.data,'base64');
    }
    fs.writeFileSync(path.join(out,name+'.png'),image);
    result.screenshots.push({file:name+'.png',bytes:image.length,sha256:sha(image),capture:'Chromium Page.captureScreenshot from current viewport'});save();
  }
  async function clickMapLabel(pointerType) {
    await closePanel();
    const coordinate = await page.waitForFunction(id => {
      const scene = window.__SHANGHAI_APP__.scene;
      if (scene.map.isMoving()) return false;
      const label = scene.getBuildingBeaconState().labelPositions.find(l => l.id === id);
      if (!label) return false;
      const canvas = scene.map.getCanvas();
      const rect = canvas.getBoundingClientRect();
      for (const dx of [0, -.28, .28]) {
        for (const dy of [0, -.25, .25]) {
          const x = Math.round(label.x + dx * label.width);
          const y = Math.round(label.y + dy * label.height);
          const target = document.elementFromPoint(x + rect.left, y + rect.top);
          if (target === canvas && scene.pickBuildingBeacon({x,y}) === id) {
            return {x:x+rect.left,y:y+rect.top};
          }
        }
      }
      return false;
    },ID,{polling:300,timeout:40000});
    const {x,y}=await coordinate.jsonValue();
    await page.evaluate(() => { window.__shanghaiAuditPointer = new Promise(resolve => {
      window.addEventListener('pointerup', e => {
        const scene=window.__SHANGHAI_APP__.scene, canvas=scene.map.getCanvas();
        const rect=canvas.getBoundingClientRect();
        resolve({trusted:e.isTrusted,type:e.pointerType,canvas:e.target===canvas,
          x:e.clientX,y:e.clientY,picked:scene.pickBuildingBeacon({x:e.clientX-rect.left,y:e.clientY-rect.top})});
      },{once:true,capture:true});
    }); return true; });
    if(pointerType==='mouse') await page.mouse.click(x,y);
    else await page.touchscreen.tap(x,y);
    const receipt=await page.evaluate(()=>window.__shanghaiAuditPointer);
    assert.equal(receipt.type,pointerType);assert.ok(receipt.trusted&&receipt.canvas);assert.equal(receipt.picked,ID);
    (result.beaconInputs??=[]).push(receipt);save();
    await settle('full',false);
  }

  async function stableDefault(name){
    const samples=[];
    let last='',agree=0;
    for(let i=0;i<10;i++){
      const observed=await page.evaluate(({id,macro,group,owner})=>{
        const sc=window.__SHANGHAI_APP__.scene,ci=sc.getCandidateIntegrationState();
        const stream=sc.getStreamingState();
        const asset=sc.getLandmarkAssetState(id);
        const section=ci.sourceSections.find(v=>v.id===id);
        const own=ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group);
        const map=sc.map;
        const source=map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:owner.key.slice(9)});
        return {variant:asset?.variant,visible:asset?.visible,moving:map.isMoving(),zoom:map.getZoom(),
          footprint:source,vectorCount:map.querySourceFeatures('overture-buildings',{sourceLayer:'building'}).length,
          nearGroup:Boolean(own && stream.detail.active.some(v=>v.id===own.id)),nearCutOwners:own?.clip_feature_local_ids,
          caps:section?.segments??0, overlays:ci.vector.filter(v=>v.active).map(v=>({pending:Boolean(v.pending),busy:Boolean(v.residualLayer?.busy),ready:Boolean(v.residualLayer?.ready)}))};
      },context);
      samples.push({utc:new Date().toISOString(),...observed});
      const signature=JSON.stringify([observed.zoom,observed.nearGroup,observed.nearCutOwners,observed.footprint,observed.caps,observed.overlays]);
      const ready=observed.visible&&!observed.moving&&observed.caps===(spec.sourceSectionCount??0)
        &&(observed.footprint.candidateModel||observed.footprint.localModel)&&observed.overlays.every(v=>!v.pending&&!v.busy);
      agree=ready&&signature===last?agree+1:0;
      if(agree>=2)break;
      last=signature;
      await page.waitForTimeout(700);
    }
    result.defaultTimeline??={};
    result.defaultTimeline[name]={consecutiveReady:agree,observations:samples};
    save();
    await view(name,null);
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
      const coordinateLink='index.html#lng='+camera.center[0].toFixed(7)+'&lat='+camera.center[1].toFixed(7)+'&mode=overview';
      result.controlLocationLink=coordinateLink;
      await page.goto(base+coordinateLink,{waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));await closePanel();await jump(camera);await view('map-before',null,true);
    }else{
      if(segment==='phone'){
      await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
      assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
      const card=page.locator('#district-'+row.districtId+' [data-landmark="'+ID+'"] .card-foot a[href="index.html#landmark='+ID+'&mode=overview"]');
      await card.tap();await view('map-mobile',null);await stableDefault('map-mobile-same-camera');await clickMapLabel('touch');
      await closePanel();
      const beforeZoom=await page.evaluate(()=>window.__SHANGHAI_APP__.scene.map.getZoom());
      await page.locator('#zoom-in').tap();
      await page.waitForFunction(z=>{const m=window.__SHANGHAI_APP__.scene.map;return !m.isMoving()&&m.getZoom()>z+.65;},beforeZoom);
      await view('map-mobile-public-zoom','full');

      }
      if(segment==='desktop'){
        await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
        const card=page.locator('#district-'+row.districtId+' [data-landmark="'+ID+'"] .card-foot a[href="index.html#landmark='+ID+'&mode=overview"]');
        assert.equal(await card.count(),1);
        await card.click();
      await view('map-desktop','full');await stableDefault('map-desktop-same-camera');await clickMapLabel('mouse');
      await closePanel();
      }
      if(segment==='return'){
      await page.goto(base+'index.html#landmark='+ID+'&mode=overview',{waitUntil:'domcontentloaded'});
      await page.waitForFunction(id=>{
        const sc=window.__SHANGHAI_APP__?.scene;
        return sc?.getLandmarkAssetState(id)?.status==='loaded' && sc.getLandmarkAssetState(id).visible;
      },ID,{polling:250,timeout:180000});
      await closePanel();
      const viaDirectory=async(text,target)=>{
        await page.keyboard.press('/');
        const input=page.locator('#place-search');
        assert.equal(await input.evaluate(el=>el===document.activeElement),true);
        await input.fill(text);
        const button=page.locator('#place-list [data-place="'+target+'"]');
        assert.equal(await button.count(),1);
        let tabPresses=0;
        while(!await button.evaluate(el=>el===document.activeElement)&&tabPresses<16){
          await page.keyboard.press('Tab');
          tabPresses++;
        }
        assert.equal(await button.evaluate(el=>el===document.activeElement),true);
        await button.evaluate(el=>el.addEventListener('click',evt=>{
          window.__SHANGHAI_KEYBOARD_SELECTION__={id:el.dataset.place,trusted:evt.isTrusted,detail:evt.detail};
        },{once:true}));
        await page.keyboard.press('Enter');
        const seen=await page.evaluate(()=>window.__SHANGHAI_KEYBOARD_SELECTION__);
        assert.deepEqual(seen,{id:target,trusted:true,detail:0});
        await page.waitForFunction(target=>new URLSearchParams(location.hash.slice(1)).get('landmark')===target,target);
        const overview=page.locator('#overview-mode');await overview.focus();await page.keyboard.press('Enter');
        await page.waitForFunction(()=>document.querySelector('#overview-mode').getAttribute('aria-pressed')==='true');
        return {text,tabPresses,...seen};
      };
      result.keyboardSearch=[await viaDirectory('外白渡桥',PRIOR)];
      await page.waitForFunction(id=>window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id)?.visible,PRIOR,{polling:250,timeout:180000});
      result.bridgeAtReturn=await page.evaluate(([id,prior])=>{const scene=window.__SHANGHAI_APP__.scene;return {bridgeVisible:scene.getLandmarkAssetState(prior)?.visible===true,towerVisible:scene.getLandmarkAssetState(id)?.visible===true,visibleClips:scene.getCandidateIntegrationState().clips.map(v=>v.id),time:new Date().toISOString()}},[ID,PRIOR]);save();
      result.keyboardSearch.push(await viaDirectory('东大名路378','hongkou-east-daming-road-378'));
      await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene;return !s.map.isMoving()&&!s.getLandmarkAssetState(id)?.visible&&!s.getCandidateIntegrationState().clips.some(c=>c.id===id);},ID,{timeout:70000});
      result.unloadedWhileAway=true;
      result.keyboardSearch.push(await viaDirectory('外滩信号',ID));
      await view('map-returned','full');save();
      }
      if(segment==='placement'){
      const locationLink='index.html#landmark='+ID+'&mode=overview';
      await page.goto(base+locationLink,{waitUntil:'domcontentloaded'});
      await page.waitForFunction(id=>{const app=window.__SHANGHAI_APP__;return app?.scene?.map && new URLSearchParams(location.hash.slice(1)).get('landmark')===id;},ID);
      result.initialNamedLink=locationLink;
      await closePanel();
      // Read the two accepted camera records from their original physical session.
      // That same session subsequently lost Chromium on the roof view.
      const recoveryDir='/dev/shm/signal222-final/segments/failed-placement-3';
      const recoveryBytes=fs.readFileSync(path.join(recoveryDir,'placement-closed.json'));
      assert.equal(sha(recoveryBytes),'609df616ea9195f7d6eda7a4cbbcaed8ac1f4a6ee71786c20d7deecc060be441');
      const priorExit=JSON.parse(recoveryBytes);assert.equal(priorExit.exit,1);
      assert.ok(priorExit.node_closed&&priorExit.chromium_pids.length&&priorExit.remaining_chromium.length===0);
      const sourceReport=fs.readFileSync(path.join(recoveryDir,'placement/main-browser.json'));
      assert.equal(sha(sourceReport),priorExit.report_sha256);const recovered=JSON.parse(sourceReport);
      assert.equal(recovered.caseSha256,result.caseSha256);assert.deepEqual(recovered.catalog,result.catalog);
      assert.deepEqual(recovered.bindings,result.bindings);assert.deepEqual(recovered.screenshots.map(v=>v.file),['map-street-facade.png','map-station-and-tower.png']);
      assert.deepEqual(recovered.views.map(v=>v.view),['map-street-facade','map-station-and-tower']);
      for(const oldView of recovered.views){
        assert.equal(oldView.glError,0);assert.equal(oldView.contextLost,false);
        assert.equal(oldView.asset.status,'loaded');assert.equal(oldView.asset.variant,'full');
        assert.equal(oldView.asset.verifiedAsset.sha256,row.assets.web.sha256);
        assert.deepEqual(oldView.group.feature_local_ids,group.feature_local_ids);
        assert.deepEqual([...oldView.group.clip_feature_local_ids].sort((a,b)=>a-b),[...(spec.existingGroupOwners||[]),...addedOwners].sort((a,b)=>a-b));
        assert.equal(oldView.group.triangles,spec.groupTriangles);
        assert.ok(oldView.source.candidateModel||oldView.source.localModel);

        assert.equal(oldView.pick,selected);assert.equal(oldView.courtWitnesses.points.length,court.length);
      }
      for(const shot of recovered.screenshots){
        const original=path.join(recoveryDir,'placement',shot.file);const copy=path.join(out,shot.file);
        assert.equal(sha(fs.readFileSync(original)),shot.sha256);if(!fs.existsSync(copy))fs.linkSync(original,copy);
        assert.equal(sha(fs.readFileSync(copy)),shot.sha256);
      }
      result.screenshots.push(...recovered.screenshots);result.views.push(...recovered.views);
      result.recoveredPlacement={closed:path.join(recoveryDir,'placement-closed.json'),closed_sha256:sha(recoveryBytes),exit:1,
        report:path.join(recoveryDir,'placement/main-browser.json'),report_sha256:sha(sourceReport),retained:recovered.screenshots.map(v=>v.file),
        newWork:['map-roof','ground collisions','frozen source GET']};save();
      console.log('[map] apply roof',Date.now());await jump({...camera,center:point(...spec.roof.center),bearing:contract.heading+spec.roof.bearingOffset,elevation:spec.roof.elevation,pitch:spec.roof.pitch,zoom:spec.roof.zoom});await view('map-roof','full');
      const probes=[
        ...spec.ground.map(w=>({name:w.name,position:point(...w.xy),expected:w.expected})),
        ...neighbors.map(n=>({name:'retained neighbor '+n.local_id,position:spec.neighborGround[n.local_id],expected:'building'}))];
      async function grounded(label){
        const sample=await page.evaluate(async witnesses=>{
          const sc=window.__SHANGHAI_APP__.scene;await sc.waitForData(10000);
          return {overtureFeatures:sc.map.querySourceFeatures('overture-buildings',{sourceLayer:'building'}).length,
            ground:witnesses.map(p=>({...p,found:sc.collisionAt(...p.position)}))};
        },probes);
        result.groundChecks??=[];result.groundChecks.push({label,...sample});save();
        return sample.ground;
      }
      result.ground=await grounded('reported after the roof view');
      if(result.ground.some(w=>w.found!==w.expected)){
        await page.reload({waitUntil:'domcontentloaded'});
        await settle('full',false);await closePanel();await jump(camera);await settle('full',true);
        await page.waitForFunction(()=>window.__SHANGHAI_APP__.scene.map.querySourceFeatures(
          'overture-buildings',{sourceLayer:'building'}).length>0,null,{polling:1000,timeout:180000});
        result.ground=await grounded('fresh road and building layers after normal reload');
      }
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);
      }
      if(segment==='distant'){
      await page.goto(base+'index.html#landmark='+ID+'&mode=overview',{waitUntil:'domcontentloaded'});
      await page.waitForFunction(id=>{
        const state=window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id);
        return state?.visible&&state.variant==='full'&&state.verifiedAsset?.sha256;
      },ID,{polling:100,timeout:180000});
      result.freshNear=await page.evaluate(id=>window.__SHANGHAI_APP__.scene.getLandmarkAssetState(id),ID);
      assert.equal(result.freshNear.verifiedAsset.sha256,row.assets.web.sha256);
      await closePanel();
      await jump({...camera,zoom:16.35,pitch:18,elevation:0});
      const cutoff=row.lod_switch_out_m||400;
      const measureDistance=()=>page.evaluate(({lng,lat,height_m})=>{
        const map=window.__SHANGHAI_APP__.scene.map,eye=map.transform.getCameraLngLat(),alt=map.transform.getCameraAltitude();
        const latRadians=lat*Math.PI/180;
        const east=(eye.lng-lng)*111195.08*Math.cos(latRadians), north=(eye.lat-lat)*111195.08;
        return {metres:Math.hypot(east,north,alt-(height_m||30)/2),zoom:map.getZoom(),altitude:alt};
      },{lng:row.lng,lat:row.lat,height_m:row.height_m});
      let distance=await measureDistance();
      result.distantSwitch={signed_threshold_m:cutoff,initial:distance,public_steps:[]};
      for(let step=0;distance.metres<=cutoff && step<3;step++){
        await page.evaluate(()=>document.querySelector('#zoom-out').addEventListener('click',e=>{window.__publicLodZoom={trusted:e.isTrusted,button:e.button,detail:e.detail};},{capture:true,once:true}));
        await page.locator('#zoom-out').click();
        result.distantSwitch.public_zoom_click=await page.evaluate(()=>window.__publicLodZoom);
        assert.equal(result.distantSwitch.public_zoom_click.trusted,true);
        await page.waitForFunction(z=>{const map=window.__SHANGHAI_APP__.scene.map;return !map.isMoving()&&map.getZoom()<z-.65},distance.zoom);
        distance=await measureDistance();
        result.distantSwitch.public_steps.push({trusted:result.distantSwitch.public_zoom_click.trusted,distance});
      }
      assert.ok(distance.metres>cutoff,'Scene camera crossed the signed far threshold');
      await view('map-distant','distant');
      for(const [role,item] of Object.entries(manifest.assets))await receipt(path.posix.join(path.posix.dirname(row.candidate_manifest),item.file),item,role==='full'||role==='lod');
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
    if(control || segment==='distant' || segment==='placement')for(const rec of review.frozen_bindings.filter(r=>r.repository_path.endsWith('/far.glb')||r.repository_path.endsWith('/'+group.file)))
      await receipt(rec.repository_path.replace('projects/shanghai/',''),rec,segment!=='distant');
    assert.deepEqual(result.errors,[]);assert.deepEqual(result.failed,[]);result.completed=true;
   }catch(e){result.failure=e.stack;result.failureState=await page.evaluate(({id,selected,group,macro})=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return {body:document.body.innerText.slice(0,1000)};
      return {route:location.hash,moving:s.map.isMoving(),stream:s.getStreamingState(),camera:{center:s.map.getCenter(),zoom:s.map.getZoom()},active:s.getLandmarkAssetState(selected),selectedTarget:s.getLandmarkAssetState(id),group:s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.id===macro+'/'+group),labels:s.getBuildingBeaconState().viewportLabelCount};
    },context).catch(err=>({error:String(err)}));throw e;}
  finally{await browser.close();result.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
