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
const PRIOR = 'huangpu-electric-company-corner-tower';
const phase=process.env.QA_PHASE;
const phases=['control','mobile-card','mobile-pin','desktop-card','desktop-pin','street','roof','octagon','inscription','distant'];
assert(phases.includes(phase));
const control=phase==='control',mobile=phase.startsWith('mobile-'),desktopOnly=!control&&!mobile;
const localExisting='huangpu-ampire-and-co-building';
const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(audit,'../../..');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const out = process.env.QA_OUTPUT_DIR || audit;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const localBytes=f=>fs.existsSync(f)?fs.readFileSync(f):require('node:zlib').gunzipSync(fs.readFileSync(f+'.gz'));
const bytes=f=>localBytes(path.join(project,f));
const read = f => JSON.parse(bytes(f));
const review = read('source/precise/'+ID+'/footprint-review.json');
const contract = JSON.parse(fs.readFileSync(path.join(audit,'final-placement-contract.json')));
spec.sourceSectionCount=contract.source_section_caps.geometry.coordinates.reduce((total,line)=>total+line.length-1,0);
assert.equal(spec.sourceSectionCount,1,'One source section seam on the retained 2274 museum');
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
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--enable-low-end-device-mode','--num-raster-threads=1','--disable-gpu-rasterization','--js-flags=--max-old-space-size=384','--use-angle=swiftshader','--enable-unsafe-swiftshader',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const viewport=control?{width:480,height:500}:mobile?{width:390,height:844}:phase.startsWith('desktop')?{width:740,height:548}:phase==='distant'?{width:760,height:560}:phase==='inscription'?{width:640,height:440}:['octagon','roof'].includes(phase)?{width:740,height:580}:{width:640,height:480};
  const page=await browser.newPage({viewport,deviceScaleFactor:control?.85:1,ignoreHTTPSErrors:true,hasTouch:mobile});
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
    result.views.push({view:name,...state});save();
    assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.equal(state.labels,catalog.resulting_city_count);
    if(!control && (phase.endsWith('-pin') || phase.endsWith('-card')))assert.equal(state.pick,selected);assert.equal(new URLSearchParams(state.route.slice(1)).get('landmark'),selected);
    for(const n of state.neighbors){if(!spec.existingCandidateOwners?.includes(n.local_id))assert.notEqual(n.state.candidateModel,true);}
    if(detail){
      assert.deepEqual(state.group.feature_local_ids,group.feature_local_ids);
      if(control){assert.equal(state.source.localModel,true);assert.equal(state.group.triangles,primaryCase.groupTriangles-primaryCase.addedTriangles);assert.deepEqual(state.group.clip_feature_local_ids,primaryCase.existingOwners);}
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
    const cdp=await page.context().newCDPSession(page);
    const frame=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false,optimizeForSpeed:true});await cdp.detach();
    const image=Buffer.from(frame.data,'base64');fs.writeFileSync(path.join(out,name+'.png'),image);result.screenshots.push({file:name+'.png',bytes:image.length,sha256:sha(image)});save();
  }
  async function enterMapLabel(id, previous, position, pointer, report) {
    assert.equal(previous,localExisting);
    assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('landmark'),previous);
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
    await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
    const cards=page.locator('.landmark-card[data-landmark]');
    await cards.first().waitFor({timeout:120000});assert.equal(await cards.count(),catalog.resulting_city_count);
    assert.equal(await page.locator('.landmark-card[data-landmark="'+ID+'"]').count(),control?0:1);
    const card=page.locator('.landmark-card[data-landmark="'+entry+'"] .card-foot a[href="index.html#landmark='+entry+'&mode=overview"]');
    assert.equal(await card.count(),1);
    await page.evaluate(()=>document.addEventListener('pointerup',event=>{
      const card=event.target.closest('[data-landmark]');if(card)sessionStorage.setItem('huqiuDirectoryInput',JSON.stringify({id:card.dataset.landmark,type:event.pointerType,trusted:event.isTrusted}));
    },{capture:true,once:true}));
    if(mobile)await card.tap();else await card.click();
    await page.waitForFunction(entry=>{
      const scene=window.__SHANGHAI_APP__?.scene,cover=document.getElementById('loading');
      if(!scene||!cover||!cover.classList.contains('loaded')||scene.map.isMoving())return false;
      const st=getComputedStyle(cover);
      return st.visibility==='hidden'&&st.opacity==='0'&&st.pointerEvents==='none'&&new URLSearchParams(location.hash.slice(1)).get('landmark')===entry;
    },entry,{polling:300,timeout:240000});
    const directoryInput=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('huqiuDirectoryInput')));
    assert.equal(directoryInput.id,entry);assert.equal(directoryInput.type,mobile?'touch':'mouse');assert.equal(directoryInput.trusted,true);
    result.realDirectoryEntry={pointer:directoryInput,id:entry,route:await page.evaluate(()=>location.hash),normalStartupFinished:true};
    if(control){await closePanel();await jump(camera);await view('map-before',null,true);}
    else if(phase==='mobile-card'){await view('map-mobile',null);}
    else if(phase==='desktop-card'){await view('map-desktop','full');}
    else if(pin){
      await enterMapLabel(ID,localExisting,[contract.lng,contract.lat],mobile?'touch':'mouse',result);
      await view(mobile?'map-mobile-label':'map-desktop-label','full');
    }else{
     await closePanel();
     if(phase==='street'){
      await jump(camera);await view('map-huqiu-three-stone-arches','full',true);
      result.ground=await page.evaluate(async probes=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(10000);
        return probes.map(p=>({...p,found:s.collisionAt(...p.position)}));},[
        ...spec.ground.map(w=>({name:w.name,position:point(...w.xy),expected:w.expected})),
        ...neighbors.map(n=>({name:'retained neighbor '+n.local_id,position:spec.neighborGround[n.local_id],expected:'building'}))]);
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);

     }else if(phase==='roof'){
      await jump({...camera,center:point(...spec.roof.center),bearing:contract.heading+spec.roof.bearingOffset,elevation:spec.roof.elevation,pitch:spec.roof.pitch,zoom:spec.roof.zoom});await view('map-ras-stepped-parapet','full',true);
     }else if(phase==='octagon'){
      await jump({...camera,center:point(-4.45,0),bearing:contract.heading+3,elevation:2.23,pitch:69,zoom:22.05});await view('map-octagonal-window-and-gate','full',true);
     }else if(phase==='inscription'){
      await jump({...camera,center:point(0,0),bearing:contract.heading-4,elevation:8.69,pitch:68,zoom:21.8});await view('map-chinese-inscription-and-balcony','full',true);
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
