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
const phoneOnly = process.argv.includes('--phone-only');
const desktopOnly = !phoneOnly;
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
const neighborEvidence = JSON.parse(fs.readFileSync(path.join(__dirname,'neighbor-owner-keys.json')));
const neighbors = neighborEvidence.neighbors;
assert.deepEqual(neighbors.map(v=>v.local_id).sort((a,b)=>a-b),Object.keys(spec.neighborGround).map(Number).sort((a,b)=>a-b));
const point = (x,y) => {
  const h=contract.heading*Math.PI/180,k=6371008.8*Math.cos(contract.lat*Math.PI/180);
  const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
  return [contract.lng+east/k*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(contract.lat*Math.PI/180))+north/k))*180/Math.PI];
};
const camera = {center:point(...spec.front.center),elevation:spec.front.elevation,pitch:spec.front.pitch,bearing:contract.heading+spec.front.bearingOffset,zoom:spec.front.zoom,padding:{top:0,right:0,bottom:0,left:0}};
const result = {id:ID,mode:control?'frozen-before':'delivered',started:new Date().toISOString(),completed:false,server:base,
  desktopOnly,caseSha256:sha(fs.readFileSync(caseFile)),scriptSha256:sha(fs.readFileSync(__filename)),sourceCommit:review.baseline_commit,camera,views:[],screenshots:[],files:[],errors:[],warnings:[],failed:[]};
result.viewportMode=phoneOnly?'independent-phone':'independent-desktop';
const reportPath=path.join(out,control?'control-browser.json':phoneOnly?'phone-browser.json':'main-browser.json');
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
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--disk-cache-size=8388608','--num-raster-threads=1','--renderer-process-limit=2',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const page=await browser.newPage({viewport:phoneOnly?{width:390,height:844}:{width:1280,height:800},ignoreHTTPSErrors:true,hasTouch:phoneOnly,isMobile:phoneOnly,deviceScaleFactor:1});
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
        &&c.vector.filter(v=>v.active).every(v=>!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer?.ready));
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
    if(!control)assert.equal(state.pick,selected);assert.equal(new URLSearchParams(state.route.slice(1)).get('landmark'),selected);
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
    result.phase='capturing '+name;save();const image=await page.screenshot({path:path.join(out,name+'.png'),timeout:300000});result.screenshots.push({file:name+'.png',bytes:image.length,sha256:sha(image)});save();
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
      result.entryInput='mouse click on prior city directory';
      await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()));await closePanel();await jump(camera);await view('map-before',null,true);
    }else{
      await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
      assert.equal(await page.locator('.landmark-card[data-landmark]').count(),catalog.resulting_city_count);
      const card=page.locator('#district-'+row.districtId+' [data-landmark="'+ID+'"] .card-foot a[href="index.html#landmark='+ID+'&mode=overview"]');
      if(phoneOnly){
        await card.tap();
        result.entryInput='touch on a newly opened 390 × 844 city directory';
        await view('map-mobile',null);
        await closePanel();
        const zoom=await page.evaluate(()=>window.__SHANGHAI_APP__.scene.map.getZoom());
        await page.locator('#zoom-in').tap();
        await page.waitForFunction(z=>{const m=window.__SHANGHAI_APP__.scene.map;return !m.isMoving()&&m.getZoom()>z+.6;},zoom);
        await view('map-mobile-zoom','full',true);
        assert.deepEqual(result.errors,[]);assert.deepEqual(result.failed,[]);result.completed=true;
        return;
      }
      await card.click();
      result.entryInput='mouse click on a newly opened 1280 × 800 city directory';
      await view('map-desktop',null);
      await closePanel();await jump(camera);await view('map-street-facade','full',true);
      await jump({...camera,center:point(-3.55,1.4),elevation:5.2,pitch:58,bearing:contract.heading-8,zoom:21.58});await view('map-garden-terrace-and-windows','full',true);
      await jump({...camera,center:point(...spec.roof.center),bearing:contract.heading+spec.roof.bearingOffset,elevation:spec.roof.elevation,pitch:spec.roof.pitch,zoom:spec.roof.zoom});await view('map-roof','full',true);
      await page.waitForFunction(()=>window.__SHANGHAI_APP__.scene.map.querySourceFeatures('overture-buildings',{sourceLayer:'building'}).length>0,null,{polling:900,timeout:150000});
      result.ground=await page.evaluate(async probes=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(10000);
        return probes.map(p=>({...p,found:s.collisionAt(...p.position)}));},[
        ...spec.ground.map(w=>({name:w.name,position:point(...w.xy),expected:w.expected})),
        ...neighbors.map(n=>({name:'retained neighbor '+n.local_id,position:spec.neighborGround[n.local_id],expected:'building'}))]);
      for(const witness of result.ground)assert.equal(witness.found,witness.expected,witness.name);
      await jump({...camera,zoom:15.5,pitch:32,elevation:0});await view('map-distant','distant');
      for(const [role,item] of Object.entries(manifest.assets))await receipt(path.posix.join(path.posix.dirname(row.candidate_manifest),item.file),item,role==='full'||role==='lod');
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
    for(const rec of review.frozen_bindings.filter(r=>r.repository_path.endsWith('/far.glb')||r.repository_path.endsWith('/'+group.file)))
      await receipt(rec.repository_path.replace('projects/shanghai/',''),rec,true);
    assert.deepEqual(result.errors,[]);assert.deepEqual(result.failed,[]);result.completed=true;
   }catch(e){result.failure=e.stack;result.failureState=await page.evaluate(({id,selected,group,macro})=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return {body:document.body.innerText.slice(0,1000)};
      return {route:location.hash,moving:s.map.isMoving(),stream:s.getStreamingState(),camera:{center:s.map.getCenter(),zoom:s.map.getZoom()},active:s.getLandmarkAssetState(selected),selectedTarget:s.getLandmarkAssetState(id),group:s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.id===macro+'/'+group),labels:s.getBuildingBeaconState().viewportLabelCount};
    },context).catch(err=>({error:String(err)}));throw e;}
  finally{await browser.close();result.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
