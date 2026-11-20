/* Verify the suspended north bridge in the production Shanghai renderer. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');

const id = 'huangpu-wing-on-skybridges';
const parents = ['huangpu-old-wing-on-company', 'huangpu-new-wing-on-company'];
const root = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(__dirname, '../../..');
const out = process.env.QA_OUTPUT_DIR || __dirname;
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const sha = (b) => createHash('sha256').update(b).digest('hex');
const read = (f) => JSON.parse(fs.readFileSync(path.join(root,f)));
const catalog = read('data/candidate-city-integrations.json');
const row = catalog.models.find(r => r.id === id);
const manifest = read(row.candidate_manifest);
const ground = JSON.parse(fs.readFileSync(path.join(__dirname,'footprint-review.json'))).ground_probes.map(p=>p.position);
const comparisonPoints=parents.map(i=>{const r=catalog.models.find(m=>m.id===i);return {id:i,point:[r.lng,r.lat]};});
const padding = {top:0, right:0, bottom:0, left:0};
const report = {model:id, scriptSha256:sha(fs.readFileSync(__filename)), started:new Date().toISOString(),
  base, count:catalog.resulting_city_count, catalogSha256:sha(fs.readFileSync(path.join(root,'data/candidate-city-integrations.json'))),
  manifestSha256:sha(fs.readFileSync(path.join(root,row.candidate_manifest))), completed:false, errors:[], warnings:[], httpErrors:[], screenshots:[], views:[]};
const save = () => fs.writeFileSync(path.join(out,'main-map-browser.json'),JSON.stringify(report,null,2)+'\n');

async function run() {
  fs.mkdirSync(out,{recursive:true});
  assert(!fs.existsSync(path.join(out,'main-map-browser.json')),'Use a fresh output directory');
  assert.equal(row.collision_geometry,null); assert.equal(row.replacement_geometry,null);
  assert.equal(row.ground_collision_mode,'overhead-connector'); assert.equal(row.ground_clearance_m,13);
  report.inputSha256 = Object.fromEntries(['index.html','src/map-scene.js','src/candidate-city-integrations.js','src/building-beacons.js','data/landmarks.json','data/candidate-city-integrations.json']
    .map(file=>[file,sha(fs.readFileSync(path.join(root,file)))]));
  const browser = await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  report.browser = browser.version();
  const page = await browser.newPage({viewport:{width:960,height:720},hasTouch:true,ignoreHTTPSErrors:true});
  page.on('pageerror', e => report.errors.push(e.message));
  page.on('console', m => { if(m.type()==='error')report.errors.push(m.text()); if(m.type()==='warning')report.warnings.push(m.text()); });
  page.on('response', r => {if(r.status()>=400)report.httpErrors.push([r.status(),r.url()]);});
  const state = async (label,variant) => {
    console.log(label);
    await page.waitForFunction(({id,parents,variant})=>{
      const a=window.__SHANGHAI_APP__,s=a?.scene;if(!s||s.map.isMoving())return false;
      const assets=[id,...parents].map(i=>s.getLandmarkAssetState(i)),current=assets[0];
      const active=s.getCandidateIntegrationState();
      return (!variant || current.variant===variant) && assets.every(r=>r?.visible&&r.status==='loaded')
        && parents.every(i=>active.clips.some(c=>c.id===i)) && active.active.some(r=>r.id===id)
        && s.getStreamingState().active.some(x=>x.id==='14-13720-6694'&&x.visible)
        && s.map.getCanvas().clientWidth===innerWidth;
    },{id,parents,variant},{timeout:480000,polling:800});
    await page.evaluate(()=>new Promise(done=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>{m.once('render',()=>done());m.triggerRepaint();});m.triggerRepaint();}));
    const snapshot=await page.evaluate(({id,parents,ground,comparisonPoints})=>{
      const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,cs=s.getCandidateIntegrationState();
      const assets=[id,...parents].map(i=>{const r=s.getLandmarkAssetState(i);return {id:i,variant:r.variant,sha256:r.verifiedAsset.sha256,bytes:r.verifiedAsset.bytes,triangles:r.triangles,visible:r.visible};});
      s.getCollisionState();
      return {assets,clipIds:cs.clips.map(c=>c.id),displayClipIds:cs.displayClips.map(c=>c.id),roadProbes:ground.map(point=>({point,obstacle:s.collisionAt(...point)})),
        comparisonPoints:comparisonPoints.map(p=>({...p,obstacle:s.collisionAt(...p.point)})),
        walkDisabled:document.querySelector('#walk-mode').disabled, title:document.querySelector('#location-name').textContent,
        labels:s.getBuildingBeaconState().count, viewport:[innerWidth,innerHeight], hash:location.hash,
        camera:{zoom:m.getZoom(),bearing:m.getBearing(),pitch:m.getPitch(),elevation:m.transform.elevation,center:m.getCenter()},
        nearGroups:s.getStreamingState().detail.active.map(r=>r.id),webglLost:m.painter.context.gl.isContextLost()};
    },{id,parents,ground,comparisonPoints});
    assert(!snapshot.webglLost);assert.equal(snapshot.title,row.name);for(const probe of snapshot.roadProbes)assert.equal(probe.obstacle,null);
    for(const control of snapshot.comparisonPoints)assert.equal(control.obstacle,'building',control.id);
    assert.equal(snapshot.labels,catalog.resulting_city_count);assert(snapshot.walkDisabled);
    assert(!snapshot.clipIds.includes(id));assert(!snapshot.displayClipIds.includes(id));
    assert.equal(new URLSearchParams(snapshot.hash.slice(1)).get('landmark'),id);
    for(const r of snapshot.assets){const expected=catalog.models.find(m=>m.id===r.id).assets[r.variant==='full'?'web':'lod'];assert.equal(r.sha256,expected.sha256);assert.equal(r.bytes,expected.bytes);}
    report.views.push({label,...snapshot});save();
  };
  const capture=async(label)=>{
    const file=label+'.png';await page.screenshot({path:path.join(out,file),timeout:180000});
    const b=fs.readFileSync(path.join(out,file));report.screenshots.push({file,bytes:b.length,sha256:sha(b)});save();
  };
  const jump=async(camera)=>page.evaluate(({camera,padding})=>{const s=window.__SHANGHAI_APP__.scene;
    s.map.setCenterClampedToGround(false);s.map.jumpTo({...camera,padding});s.loadLandmarks();s.refreshBuildingBeacons();
  },{camera,padding});
  const select=async(target)=>page.evaluate(async i=>{const a=window.__SHANGHAI_APP__;await a.selectPlace(a.landmarks.find(r=>r.id===i),{mode:'overview'});},target);
  try{
    await page.goto(base+'index.html#landmark='+id+'&mode=overview',{waitUntil:'domcontentloaded'});
    await state('desktop entry');await capture('map-desktop');
    if(await page.locator('#panel-toggle').getAttribute('aria-expanded')==='true')await page.locator('#panel-toggle').click();
    await page.evaluate(()=>window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:false,surfaceNormals:true}));
    report.detailLighting='shadows off, surface normals on';
    await jump({center:[row.lng,row.lat],zoom:20.1,pitch:72,bearing:164.25,elevation:16.3});
    await state('north elevation','full');await capture('map-north-bridge');
    await jump({center:[row.lng,row.lat],zoom:19.4,pitch:33,bearing:164.25,elevation:16.3});
    await state('roof and connections','full');await capture('map-bridge-roof');
    await jump({center:[row.lng,row.lat],zoom:15.5,pitch:35,bearing:164.25,elevation:0});
    await state('city LOD','distant');
    await page.setViewportSize({width:390,height:844});
    await page.waitForFunction(()=>window.__SHANGHAI_APP__.scene.map.transform.width===390);
    await page.evaluate(()=>window.__SHANGHAI_APP__.scene.setVisualQuality({shadows:true,surfaceNormals:true}));
    await select(id);
    await state('mobile entry','full');await capture('map-mobile');
    for(const method of ['mouse','touch']){
      await select(parents[0]);
      if(method==='touch')await page.setViewportSize({width:320,height:568});
      await page.evaluate(pad=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;m.setMaxBounds(null);m.setCenterClampedToGround(true);
        m.jumpTo({center:[121.45,31.2],zoom:8,pitch:0,bearing:0,elevation:0,padding:pad});s.refreshBuildingBeacons();},padding);
      await page.waitForFunction(count=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState();return b.viewportLabelCount===count&&b.overlapFallbackCount===0&&b.sourceIds.every(i=>s.map.isSourceLoaded(i));},catalog.resulting_city_count,{timeout:180000,polling:400});
      const target=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,pos=s.getBuildingBeaconState().labelPositions;
        return {point:pos.find(p=>p.id===id),hits:pos.filter(p=>s.pickBuildingBeacon(p)===p.id).length,count:pos.length};},id);
      assert.equal(target.hits,catalog.resulting_city_count);report[method]=target;
      if(method==='touch'){await capture('map-city-beacons');await page.touchscreen.tap(target.point.x,target.point.y);}
      else await page.mouse.click(target.point.x,target.point.y);
      await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id,{timeout:120000});
      await state(method+' selected','full');
    }
    report.downloads=[];
    for(const [role,asset] of Object.entries(manifest.assets)){
      const file=path.posix.join(path.posix.dirname(row.candidate_manifest),asset.file);
      const response=await page.request.get(new URL(file,base).href);const bytes=await response.body();
      assert.equal(response.status(),200);assert.equal(sha(bytes),asset.sha256);assert.equal(bytes.length,asset.bytes);
      report.downloads.push({role,file,bytes:bytes.length,sha256:sha(bytes)});
    }
    assert.deepEqual(report.errors,[]);assert.deepEqual(report.httpErrors,[]);
    report.completed=true;
  }catch(error){
    report.failure=String(error.stack||error);
    report.failureState=await page.evaluate(({id,parents})=>{
      const s=window.__SHANGHAI_APP__?.scene;
      return {url:location.href,title:document.querySelector('#location-name')?.textContent,macros:s?.getStreamingState().active,
        active:s?.getCandidateIntegrationState().active,assets:[id,...parents].map(i=>s?.getLandmarkAssetState(i)),viewport:[innerWidth,innerHeight]};
    },{id,parents}).catch(()=>null);
    await capture('failure-state').catch(()=>{});
    throw error;
  }
  finally{await browser.close();report.browserClosed=true;report.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
