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
  const bounded=true;
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--single-process','--window-size=420,330','--in-process-gpu','--no-zygote','--disable-background-networking','--disable-extensions','--disable-gpu-shader-disk-cache','--disable-back-forward-cache','--disable-features=MediaRouter,OptimizationHints,Translate,Prerender2','--disable-breakpad','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1',bounded?'--js-flags=--max-old-space-size=205 --max-semi-space-size=2 --optimize-for-size':'--js-flags=--max-old-space-size=240 --max-semi-space-size=3',...(bounded?['--force-gpu-mem-available-mb=48','--msaa-sample-count=0','--disable-zero-copy']:[]),'--disk-cache-size=2107152',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const viewport=phone ? {width:390,height:844} : phase==='distant' ? {width:820,height:580} :
    control ? {width:390,height:304} : {width:870,height:660};
  const page=await browser.newPage({viewport,deviceScaleFactor:control?0.60:phone?0.70:0.80,ignoreHTTPSErrors:true,hasTouch:true});
  if(bounded){
  const cdp=await page.context().newCDPSession(page);
  await cdp.send('Emulation.setHardwareConcurrencyOverride',{hardwareConcurrency:1});
  result.logicalCores=1;save();
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
    serializedBinaryTransfers:true,mode:control?'One live binary transfer at a time with the original URLs and bytes.':'Two live binary transfers at a time with the original URLs and bytes.'};
  // Stagger starts. If the map cancels an in-flight request, subsequent live requests
  // remain independent. Chromium still fetches every requested URL from its real origin.
  let nextStart=0;
  result.bootstrap.serializedBinaryTransfers=false;
  result.bootstrap.mode='Stagger request starts, without waiting for canceled responses or rewriting any request.';
  await page.route(/\.(glb|glb\.gz|pbf)(?:\?|$)/,async route=>{
    result.bootstrap.productionResourceRequests++;
    const delay=Math.max(0,nextStart-Date.now());
    nextStart=Date.now()+delay+35;
    if(delay)await new Promise(resolve=>setTimeout(resolve,Math.min(delay,600)));
    await route.continue().catch(()=>{});
  });
  page.on('response',r=>{if(/\.(glb|glb\.gz|pbf)(?:\?|$)/.test(r.url()))result.bootstrap.productionResourceResponses++;});
  }
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
  const context={id:ID,selected,control,macro:review.frozen_macro,group:group.id,owner:source,extraOwners,neighbors,adjacentID:spec.adjacentModel};
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
      return t.active.some(t=>t.id===macro&&t.visible)&&t.detail.active.some(t=>t.id===macro+'/'+group)
        && active && (control || (active.clip_feature_local_ids.includes(owner.local_id)
          && (ownerState.candidateModel || ownerState.localModel) && vectors.length>0))
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
    const state=await page.evaluate(({id,selected,macro,group,owner,extraOwners,neighbors,adjacentID})=>{
      const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,beacons=s.getBuildingBeaconState(),ci=s.getCandidateIntegrationState();
      const sourceState=o=>m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o.key.slice(9)});
      const label=beacons.labelPositions.find(z=>z.id===selected || z.memberIds?.includes(selected)),gl=m.painter.context.gl;
      const eye=m.transform.getCameraLngLat(),alt=m.transform.getCameraAltitude();
      const asset=s.getLandmarkAssetState(selected);
      const metres=asset?.anchor ? Math.hypot(eye.distanceTo({lng:asset.anchor[0],lat:asset.anchor[1]}),alt):null;
      return {route:location.hash,name:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],mode:app.mode,
        walkDisabled:document.querySelector('#start-walk').disabled,asset:s.getLandmarkAssetState(selected),source:sourceState(owner),
        ...(extraOwners.length?{extraOwnerStates:extraOwners.map(o=>({local_id:o.local_id,state:sourceState(o)}))}:{}),
        adjacentAsset:adjacentID?s.getLandmarkAssetState(adjacentID):undefined,neighbors:neighbors.map(o=>({local_id:o.local_id,state:sourceState(o)})),sections:ci.sourceSections?.filter(x=>x.id===id)??[],clip:ci.clips.find(c=>c.id===id)||null,
        group:ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group)||null,shader:{triangles:ci.shader.triangles,limit:ci.shader.triangleLimit,macroTextures:ci.shader.macroTextures??null,denseMacroTables:ci.shader.denseMacroTables??[]},
        cameraDistanceMetres:metres,regionalLabel:label?{id:label.id,members:label.memberIds??[]}:null,labels:beacons.count,pick:label?s.pickBuildingBeacon(label):null,camera:{center:m.getCenter(),elevation:m.getCenterElevation(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom(),padding:m.getPadding(),viewport:[m.getCanvas().clientWidth,m.getCanvas().clientHeight]},
        glError:gl.getError(),contextLost:gl.isContextLost()};
    },context);
    result.views.push({view:name,...state});save();
    assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.equal(state.labels,catalog.resulting_city_count);
    if(phase==='distant'){
      assert.equal(state.asset.variant,'distant');assert.ok(state.cameraDistanceMetres>row.lod_switch_out_m);
      assert.ok(state.regionalLabel && (state.regionalLabel.id===selected || state.regionalLabel.members.includes(selected)));
      assert.equal(state.pick,state.regionalLabel.id);
    }else if(!control && (phase!=='architecture' || state.pick!==null))assert.equal(state.pick,selected);const route=new URLSearchParams(state.route.slice(1));
    if(control){assert.equal(route.get('mode'),'overview');assert.equal(route.get('lng'),camera.center[0].toFixed(6));assert.equal(route.get('lat'),camera.center[1].toFixed(6));}
    else assert.equal(route.get('landmark'),selected);
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
    const image=await page.screenshot({path:path.join(out,name+'.png'),timeout:300000});result.screenshots.push({file:name+'.png',bytes:image.length,sha256:sha(image)});save();
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
    const answer=await page.waitForFunction(getHit,ID,{polling:250,timeout:240000});
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
      const priorCard=await page.request.get(new URL('landmarks.html',base).href);
      assert.equal(priorCard.status(),200);
      const priorHtml=await priorCard.body();
      assert.equal(sha(priorHtml),result.bindings['landmarks.html']);
      assert.ok(priorHtml.toString().includes('index.html#landmark='+PRIOR+'&amp;mode=overview') || priorHtml.toString().includes('index.html#landmark='+PRIOR+'&mode=overview'));
      assert.ok(catalog.models.some(model=>model.id===PRIOR));
      const controlUrl=new URL('index.html',base);
      controlUrl.hash=new URLSearchParams({lng:camera.center[0].toFixed(6),lat:camera.center[1].toFixed(6),mode:'overview'}).toString();
      result.previousSite={card:PRIOR,catalog:result.catalog.sha256,listingSha256:sha(priorHtml),site:base,coordinateRoute:controlUrl.href};
      await page.goto(controlUrl.href,{waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));
      await closePanel();await jump(camera);await view('map-before',null,true);
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
          await closePanel();
          await jump(camera);
        }
        await settle('full',true);await closePanel();
        if(phase==='architecture'){
      await jump(camera);await view('map-street-facade','full',true);
      await jump({...camera,center:point(...spec.roof.center),bearing:contract.heading+spec.roof.bearingOffset,elevation:spec.roof.elevation,pitch:spec.roof.pitch,zoom:spec.roof.zoom});await view('map-roof','full',true);
      await architecturalView('map-mint-six-columns',{center:point(0,-2.6),bearing:contract.heading+(-5),pitch:50,elevation:7.5,zoom:20.8},[["left outer shaft", -7.4, -2.61, 5.8], ["paired left capitals", -2.55, -2.68, 9.46], ["paired right capitals", 2.55, -2.68, 9.46], ["outer right shaft", 7.4, -2.61, 5.8]]);
      await architecturalView('map-pediment-and-windows',{center:point(0,-1.48),bearing:contract.heading+(-4),pitch:44,elevation:10.75,zoom:20.3},[["central triangular pediment", 0.0, -2.9, 13.8], ["left window", -10.42, -0.32, 8.3], ["right window", 10.42, -0.32, 8.3]]);
      result.ground=await page.evaluate(async probes=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(10000);
        return probes.map(p=>({...p,found:s.collisionAt(...p.position)}));},[
        ...spec.ground.map(w=>({name:w.name,position:point(...w.xy),expected:w.expected})),
        ...neighbors.map(n=>({name:'retained neighbor '+n.local_id,position:spec.neighborGround[n.local_id],expected:'building'}))]);
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);
        }else {
          await jump({...camera,zoom:15.65,pitch:15,elevation:0});await view('map-distant','distant');
          for(const [role,item] of Object.entries(manifest.assets))await receipt(path.posix.join(path.posix.dirname(row.candidate_manifest),item.file),item,role==='lod');
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
    if(phase==='architecture')await receipt(path.posix.join(path.posix.dirname(row.candidate_manifest),manifest.assets.full.file),manifest.assets.full,true);
    for(const rec of review.frozen_bindings.filter(r=>r.repository_path.endsWith('/far.glb')||r.repository_path.endsWith('/'+group.file))){
      const isRepacked=Boolean(override)&&rec.repository_path.endsWith('/'+group.file);
      const key=rec.repository_path.replace('projects/shanghai/','');
      const nearInDistant=phase==='distant' && key.includes('/near/');
      if(nearInDistant){
        const folder=path.join(__dirname,'architecture');
        const report=fs.readFileSync(path.join(folder,'main-browser.json'));
        const closure=JSON.parse(fs.readFileSync(path.join(folder,'process.json')));
        const earlier=JSON.parse(report);
        assert.equal(closure.exit_code,0);assert.equal(closure.report_sha256,sha(report));
        assert.ok(earlier.completed && earlier.server===base && earlier.scriptSha256===result.scriptSha256);
        const actual=earlier.files.find(item=>item.file===(isRepacked?override.model.file:key));
        assert.ok(actual && actual.loadedByScene);assert.equal(actual.sha256,isRepacked?override.model.sha256:rec.sha256);
        result.nearSceneReceipt={file:actual.file,phase:'architecture',reportSha256:sha(report),sha256:actual.sha256};
      }
      await receipt(key,rec,!isRepacked && !nearInDistant);
      if(isRepacked){
        assert.equal(rec.sha256,override.baseline_sha256);assert.deepEqual(override.featureLocalIds,group.feature_local_ids);
        await receipt(override.model.file,{bytes:override.model.size_bytes,sha256:override.model.sha256},!nearInDistant);
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
