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
const PRIOR = 'xuhui-libo-garden-east-house';
const control = process.argv.includes('--control');
const phoneZoom = process.argv.includes('--phone-zoom');
const phoneOnly = process.argv.includes('--phone-only') || phoneZoom;
const desktopOnly = !phoneOnly;
const partition = process.argv.find(v => ['--desktop-card','--street','--paired','--architecture','--terraces','--roof','--distant'].includes(v));
const desktopViewport = control || partition==='--paired' ? {width:440,height:380}
  : partition==='--desktop-card' ? {width:820,height:600}
  : partition==='--distant' ? {width:620,height:650} : partition==='--street' ? {width:720,height:532} : partition==='--roof' ? {width:910,height:750} : {width:794,height:568};
const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(audit,'../../..');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const out = process.env.QA_OUTPUT_DIR || audit;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
function fixtureBytes(file) {
  if (fs.existsSync(file)) return fs.readFileSync(file);
  if (path.basename(file) !== 'candidate-city-integrations.json') return fs.readFileSync(file);
  const stage = path.basename(path.dirname(path.dirname(file)));
  const input = JSON.parse(fs.readFileSync(path.join(__dirname, 'bound.json'))).pairs[stage];
  assert.ok(input, 'Missing signed city source for stage ' + stage);
  const compressed = fs.readFileSync(path.join(__dirname, stage + '-' + input.catalog + '.json.gz'));
  const catalog = require('node:zlib').gunzipSync(compressed);
  assert.equal(sha(catalog), input.catalog, 'Reconstructed frozen city catalog');
  return catalog;
}
const bytes = f => fixtureBytes(path.join(project,f));
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
  controlDirectoryEntry:control?{id:PRIOR,distanceToComparisonMetres:277.0,previousEditionNewLandmark:spec.previous}:null,
  desktopOnly,caseSha256:sha(fs.readFileSync(caseFile)),scriptSha256:sha(fs.readFileSync(__filename)),sourceCommit:review.baseline_commit,camera,views:[],screenshots:[],files:[],errors:[],warnings:[],failed:[]};
result.viewportMode=phoneOnly?'independent-phone':'independent-desktop';
const reportPath=path.join(out,control?'control-browser.json':phoneOnly?'phone-browser.json':'main-browser.json');
const save=()=>fs.writeFileSync(reportPath,JSON.stringify(result,null,2)+'\n');
async function run() {
  fs.mkdirSync(out,{recursive:true});assert.ok(!fs.existsSync(reportPath),'Use a fresh output directory');
  const catalogFile='data/candidate-city-integrations.json';
  const frozenControl=control && process.env.QA_CONTROL_CATALOG;
  const controlRoot=frozenControl && path.dirname(path.dirname(path.resolve(frozenControl)));
  const data=frozenControl?fixtureBytes(frozenControl):control?execFileSync('git',['show',review.baseline_commit+':projects/shanghai/'+catalogFile],{cwd:path.resolve(project,'../..')}):bytes(catalogFile);
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
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',env:{...process.env,PICARDIE_208_AUDIT_PARENT:String(process.pid)},args:['--no-sandbox','--single-process','--in-process-gpu','--no-zygote','--enable-low-end-device-mode','--disable-gpu-rasterization','--disable-background-networking','--js-flags=--max-old-space-size=320 --max-semi-space-size=4','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--disk-cache-size=2097152','--num-raster-threads=1','--renderer-process-limit=1',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  let page=await browser.newPage({viewport:phoneOnly?{width:390,height:844}:desktopViewport,ignoreHTTPSErrors:true,hasTouch:phoneOnly,isMobile:phoneOnly,deviceScaleFactor:phoneZoom ? .59 : (control || phoneOnly || partition==='--paired' ? 1 : ['--roof','--distant'].includes(partition) ? .46 : .72)});
  await page.addInitScript(() => {
    document.addEventListener('pointerdown', event => {
      const card = event.target.closest?.('article[data-landmark]');
      if (!card) return;
      sessionStorage.setItem('map-qa-directory-input', JSON.stringify({
        id: card.dataset.landmark, type: event.pointerType, trusted: event.isTrusted,
        href: event.target.closest?.('a')?.getAttribute('href') || '',
        point: [event.clientX, event.clientY], page: location.pathname
      }));
    }, true);
  });
  async function checkDirectoryPointer(expectedId, type) {
    const input = await (await page.waitForFunction(id => {
      const observed = JSON.parse(sessionStorage.getItem('map-qa-directory-input'));
      return observed?.id === id && observed;
    }, expectedId, { timeout: 30000 })).jsonValue();
    assert.equal(input.id, expectedId);
    assert.equal(input.trusted, true);
    assert.equal(input.type, type);
    assert.ok(input.point.every(value => Number.isFinite(value) && value >= 0));
    result.trustedDirectoryInput = input;
  }
  result.browser=browser.version();
  page.setDefaultTimeout(180000);
  if(control&&!frozenControl)await page.route('**/data/candidate-city-integrations.json*',r=>r.fulfill({contentType:'application/json',body:data}));
  page.on('pageerror',e=>result.errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')result.errors.push({url:m.location().url,message:m.text()});if(m.type()==='warning'&&m.text().includes('[Shanghai map]'))result.warnings.push(m.text());});
  page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')result.failed.push({url:r.url(),failure:r.failure()});});
  page.on('response',r=>{const u=new URL(r.url());if(r.status()>=400){result.failed.push({url:r.url(),status:r.status()});save();}
    if(u.origin===new URL(base).origin&&r.status()===200)received.add(decodeURIComponent(u.pathname.slice(1)));});
  const context={id:ID,selected,control,macro:review.frozen_macro,group:group.id,owner:source,extraOwners,neighbors,adjacentID:spec.adjacentModel};
  const manifest = row && read(row.candidate_manifest);
  async function settle(variant,detail=false){
    await page.waitForFunction(({selected,variant,detail,macro,group,owner,control,adjacentID})=>{
      const s=window.__SHANGHAI_APP__?.scene;
      const curtain=document.querySelector('#loading');
      if(!s||s.map.isMoving()||(!curtain||Number(getComputedStyle(curtain).opacity)>.015))return false;
      const a=s.getLandmarkAssetState(selected);
      if(!control&&(!a?.visible||a.status!=='loaded'||(variant&&a.variant!==variant)))return false;
      if(!detail)return true;
      if(adjacentID&&!s.getLandmarkAssetState(adjacentID)?.visible)return false;
      const c=s.getCandidateIntegrationState(),t=s.getStreamingState();
      const active=c.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group);
      return t.active.some(t=>t.id===macro&&t.visible)&&t.detail.active.some(t=>t.id===macro+'/'+group)
        && active && (control||active.clip_feature_local_ids.includes(owner.local_id))
        && Boolean(active.feature_local_ids.includes(owner.local_id));
    },{...context,variant,detail},{polling:400,timeout:240000});
    await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>resolve());m.triggerRepaint();}));
  }
  async function view(name,variant,detail=false){
    result.phase='waiting for '+name;save();await settle(variant,detail);
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
        group:ci.shader.ownerScopedSources.find(v=>v.id===macro+'/'+group)||null,shader:{triangles:ci.shader.triangles,limit:ci.shader.triangleLimit,macroTextures:ci.shader.macroTextures??null,denseMacroTables:ci.shader.denseMacroTables??[],renderer:s.getStreamingState().renderer},
        labels:beacons.count,pick:label?s.pickBuildingBeacon(label):null,camera:{center:m.getCenter(),elevation:m.getCenterElevation(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom()},
        glError:gl.getError(),contextLost:gl.isContextLost()};
    },context);
    result.views.push({view:name,...state});save();
    assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.equal(state.labels,catalog.resulting_city_count);
    if(!control && ['map-mobile','map-desktop'].includes(name))assert.equal(state.pick,selected);
    assert.equal(new URLSearchParams(state.route.slice(1)).get('landmark'),selected);
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
      if(detail){assert.ok(state.source.candidateModel||state.source.localModel);assert.deepEqual([...state.group.clip_feature_local_ids].sort((a,b)=>a-b),[...(spec.existingGroupOwners||[]),...addedOwners].sort((a,b)=>a-b));assert.equal(state.group.triangles,spec.groupTriangles);if(spec.sourceSectionCount){
        assert.equal(state.sections.length,1);
        const section=state.sections[0];
        assert.equal(section.feature_local_id,source.local_id);
        assert.equal(section.macro_id,review.frozen_macro);
        assert.equal(section.segments,spec.sourceSectionCount);
        assert.equal(section.roof_m,row.source_section_caps.roof_m);
      }}
    }
    result.phase='capturing '+name;save();await page.waitForFunction(()=>{const cover=document.getElementById('loading');return cover?.classList.contains('loaded')&&getComputedStyle(cover).visibility==='hidden'&&Number(getComputedStyle(cover).opacity)===0;},null,{timeout:180000});
    const cdp=await page.context().newCDPSession(page);let image;
    try{const timeout=new Promise((_,reject)=>{const handle=setTimeout(()=>reject(new Error('Chromium did not return surface pixels in 45 seconds')),45000);handle.unref();});const frame=await Promise.race([cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false}),timeout]);image=Buffer.from(frame.data,'base64');}
    finally{await cdp.detach();}
    fs.writeFileSync(path.join(out,name+'.png'),image);result.screenshots.push({file:name+'.png',bytes:image.length,sha256:sha(image)});save();
  }
  async function jump(camera){
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.stop();s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
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
      await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
      assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
      assert.equal(await page.locator('article[data-landmark="'+ID+'"]').count(),0);
      await page.locator('article[data-landmark="'+PRIOR+'"] .card-foot a[href*="mode=overview"]').click();
      await checkDirectoryPointer(PRIOR, 'mouse');
      result.entryInput='mouse click on prior city directory';
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));await closePanel();await jump(camera);await view('map-before',null,true);
    }else{
      const specialized = !phoneOnly && partition && partition !== '--desktop-card';
      let card;
      if (specialized) {
        const url = new URL('index.html#landmark='+ID+'&mode=overview',base).href;
        await page.goto(url,{waitUntil:'domcontentloaded'});
        result.specialistPermalink = url;
      } else {
        await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
        assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
        card=page.locator('#district-'+row.districtId+' [data-landmark="'+ID+'"] .card-foot a[href="index.html#landmark='+ID+'&mode=overview"]');
      }
      if(phoneOnly){
        await card.tap();
        await checkDirectoryPointer(ID, 'touch');
        result.entryInput='touch on a newly opened 390 × 844 city directory';
        if (!phoneZoom) {
          await view('map-mobile',null);
          assert.deepEqual(result.errors,[]);assert.deepEqual(result.failed,[]);result.completed=true;return;
        }
        await settle(null);
        await closePanel();
        const zoom=await page.evaluate(()=>window.__SHANGHAI_APP__.scene.map.getZoom());
        await page.locator('#zoom-in').tap();
        await page.waitForFunction(z=>{const m=window.__SHANGHAI_APP__.scene.map;return !m.isMoving()&&m.getZoom()>z+.6;},zoom);
        await view('map-mobile-zoom','full');
        assert.deepEqual(result.errors,[]);assert.deepEqual(result.failed,[]);result.completed=true;
        return;
      }
      if (specialized) {
        result.entryInput='ordinary public link to the selected city location';
      } else {
        await card.click();
        await checkDirectoryPointer(ID, 'mouse');
        result.entryInput='mouse click on a newly opened '+desktopViewport.width+' × '+desktopViewport.height+' city directory';
      }
      if(partition==='--desktop-card') {
        await view('map-desktop',null);
      } else {
        await page.waitForFunction(id=>window.__SHANGHAI_APP__?.scene?.map.isStyleLoaded() && window.__SHANGHAI_APP__.scene.getBuildingBeaconState().count>0 &&
          new URLSearchParams(location.hash.slice(1)).get('landmark')===id,ID,{timeout:180000});
        await closePanel();
      }
      if(partition==='--street'||partition==='--paired'){
        await jump(camera);
        await view(partition==='--street'?'map-street-facade':'map-street-paired-440','full',true);
      }
      if(partition==='--architecture'){await jump({...camera,center:point(0,-.18),elevation:2.12,pitch:83.5,bearing:contract.heading+3,zoom:21.76,padding:{left:192,right:0,bottom:86,top:0}});await view('map-three-doors-and-lamps','full',true);}
      if(partition==='--terraces'){await jump({...camera,center:point(.2,2),elevation:46.15,pitch:62,bearing:contract.heading-12,zoom:20.08,padding:{left:176,right:0,bottom:58,top:0}});await view('map-stepped-crown-and-balconies','full',true);}
      if(partition==='--roof'){await jump({...camera,center:point(...spec.roof.center),bearing:contract.heading+spec.roof.bearingOffset,elevation:43.1,pitch:49,zoom:19.66,padding:{left:220,right:0,top:72,bottom:0}});await view('map-roof-wide','full',true);}
      if (partition==='--street') {
        await page.waitForFunction(()=>window.__SHANGHAI_APP__.scene.map.querySourceFeatures('overture-buildings',{sourceLayer:'building'}).length>0,null,{polling:900,timeout:150000});
        result.ground=await page.evaluate(async probes=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(10000);
          return probes.map(p=>({...p,found:s.collisionAt(...p.position)}));},[
          ...spec.ground.map(w=>({name:w.name,position:point(...w.xy),expected:w.expected})),
          ...neighbors.map(n=>({name:'retained neighbor '+n.local_id,position:spec.neighborGround[n.local_id],expected:'building'}))]);
        for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);
      }
      if (!partition || partition==='--distant') {
        await jump({...camera,zoom:16.38,pitch:48,elevation:19,padding:{left:110,right:0,bottom:55,top:0}});await view('map-distant','distant');
        for(const [role,item] of Object.entries(manifest.assets))await receipt(path.posix.join(path.posix.dirname(row.candidate_manifest),item.file),item,role==='lod'||(!partition&&role==='full'));
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
    for(const rec of review.frozen_bindings.filter(r=>r.repository_path.endsWith('/far.glb')||(partition!=='--distant'&&partition!=='--desktop-card'&&r.repository_path.endsWith('/'+group.file))))
      await receipt(rec.repository_path.replace('projects/shanghai/',''),rec,true);
    if (partition === '--distant') {
      await page.close();
      page=await browser.newPage({viewport:{width:830,height:620},acceptDownloads:true,deviceScaleFactor:.67});
      result.mapTabClosedBeforeDirectoryDownload=true;
      await page.goto(new URL('landmarks.html', base).href, {waitUntil: 'domcontentloaded'});
      const preview = page.locator('article[data-landmark="'+ID+'"] a[href="picardie-apartments.html"]');
      await preview.click();
      await page.waitForURL('**/picardie-apartments.html');
      const downloads = page.locator('#downloads a[download]');
      await downloads.first().waitFor();
      assert.equal(await downloads.count(), 4);
      result.savedDownloads = [];
      for (const [role, expected] of Object.entries(manifest.assets)) {
        const link = downloads.filter({hasText:{raw:'原始',full:'网页',lod:'远景',native:'Blender'}[role]});
        const href = await link.getAttribute('href');
        const started = page.waitForEvent('download');
        await link.click();
        const download = await started;
        assert.equal(await download.failure(), null);
        assert.equal(download.suggestedFilename(), expected.file);
        const saved = fs.readFileSync(await download.path());
        assert.equal(saved.length, expected.bytes);
        assert.equal(sha(saved), expected.sha256);
        result.savedDownloads.push({role, href, filename: download.suggestedFilename(), bytes: saved.length, sha256: sha(saved)});
        await download.delete();
      }
    }

    assert.deepEqual(result.errors,[]);assert.deepEqual(result.failed,[]);result.completed=true;
   }catch(e){result.failure=e.stack;result.failureState=await page.evaluate(({id,selected,group,macro})=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return {body:document.body.innerText.slice(0,1000)};
      return {route:location.hash,moving:s.map.isMoving(),stream:s.getStreamingState(),camera:{center:s.map.getCenter(),zoom:s.map.getZoom()},active:s.getLandmarkAssetState(selected),selectedTarget:s.getLandmarkAssetState(id),group:s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.id===macro+'/'+group),labels:s.getBuildingBeaconState().viewportLabelCount};
    },context).catch(err=>({error:String(err)}));throw e;}
  finally{await browser.close();result.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
