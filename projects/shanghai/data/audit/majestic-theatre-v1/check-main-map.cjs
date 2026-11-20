/* Inspect the Majestic Theatre and its retained eastern neighbor in the Shanghai renderer. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');

const id = 'jingan-majestic-theatre';
const previous = 'jingan-country-hospital-north-block';
const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(__dirname, '../../..');
const output = process.env.QA_OUTPUT_DIR || __dirname;
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const read = file => JSON.parse(fs.readFileSync(path.join(project, file)));
const sha = data => createHash('sha256').update(data).digest('hex');
const source = read('source/precise/' + id + '/footprint-review.json');
const catalog = read('data/candidate-city-integrations.json');
const row = catalog.models.find(r => r.id === id);
const macro = source.owner.macro_id;
const neighbor = source.adjacent_near_group;
const controls = read('data/audit/majestic-theatre-v1/map-probes.json');
const count = catalog.resulting_city_count;
const zero = {left:0, top:0, right:0, bottom:0};
const report = {model:id, started:new Date().toISOString(), count, base, completed:false, stages:[], views:[], screenshots:[], downloads:[], errors:[], warnings:[], httpErrors:[], cityRequests:[]};
const save = () => fs.writeFileSync(path.join(output, 'main-map-browser.json'), JSON.stringify(report, null, 2) + '\n');
const phase = label => { console.log(label); report.stages.push(label); save(); };

async function run() {
  fs.mkdirSync(output, {recursive:true});
  assert(!fs.existsSync(path.join(output, 'main-map-browser.json')), 'Use a fresh output directory');
  assert(row && row.owner.feature_local_id === 360 && neighbor.feature_local_id === 1995);
  assert.deepEqual(row.source_feature_ids.building, [source.owner.key.slice('building:'.length)]);
  assert.equal(row.navigation.listed, false);
  assert(row.osm_replacement_geometry);
  assert.notDeepEqual(row.osm_replacement_geometry, row.replacement_geometry);
  const manifest = read(row.candidate_manifest);
  report.scriptSha256 = sha(fs.readFileSync(__filename));
  report.inputs = Object.fromEntries(['index.html', 'src/app.js', 'src/map-scene.js', 'src/candidate-city-integrations.js', 'src/candidate-city-clipping.js','src/candidate-vector-geometry.js','src/candidate-vector-clipping.js', 'src/building-beacons.js', 'data/candidate-city-integrations.json', row.candidate_manifest, 'data/audit/majestic-theatre-v1/map-probes.json'].map(f=>[f, sha(fs.readFileSync(path.join(project, f)))]));
  const browser = await chromium.launch({executablePath:'/usr/bin/chromium', args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const page = await browser.newPage({viewport:{width:960,height:720},hasTouch:true,ignoreHTTPSErrors:true});
  report.browser = browser.version();
  page.on('pageerror', e => report.errors.push(e.message));
  page.on('console', e => {
    if (e.type() === 'error') report.errors.push(e.text());
    if (e.type() === 'warning') report.warnings.push(e.text());
  });
  const prefix = 'assets/city-detail/macros/' + macro + '/';
  const bindings = Object.fromEntries(Object.entries(source.frozen_bindings).map(([k,v])=>[prefix+k,v]));
  page.on('response', r => {
    const file = new URL(r.url()).pathname.slice(1);
    if (r.status() >= 400) report.httpErrors.push([r.status(), r.url()]);
    if (bindings[file] && r.status() === 200) report.cityRequests.push({file, sha256:r.headers()['x-audit-sha256'], origin:r.headers()['x-audit-origin']});
  });
  const capture = async (name, timeout=180000) => {
    const file = name + '.png';
    let bytes;
    let captureMethod='playwright viewport';
    try {
      bytes=await page.screenshot({path:path.join(output,file),timeout});
    } catch(error) {
      if (!String(error).includes('Timeout') || page.isClosed()) throw error;
      const session=await page.context().newCDPSession(page);
      try {
        const frame=await Promise.race([session.send('Page.captureScreenshot',{format:'png',fromSurface:false,captureBeyondViewport:false}),
          new Promise((_,reject)=>{const limit=setTimeout(()=>reject(Error('Chromium viewport capture timeout')),45000);limit.unref();})]);
        bytes=Buffer.from(frame.data,'base64');
        fs.writeFileSync(path.join(output,file),bytes);
        captureMethod='Chromium visible viewport after Playwright capture timeout';
      } finally { await session.detach(); }
    }
    report.screenshots.push({file, captureMethod, sha256:sha(bytes), bytes:bytes.length, width:bytes.readUInt32BE(16), height:bytes.readUInt32BE(20)});
    save();
  };
  const move = camera => page.evaluate(({camera,zero})=>{
    const s=window.__SHANGHAI_APP__.scene;
    s.map.setCenterClampedToGround(false);
    s.map.jumpTo({...camera,padding:zero});
    s.loadLandmarks(); s.refreshBuildingBeacons();
  },{camera,zero});
  const select = target => page.evaluate(target=>{
    const a=window.__SHANGHAI_APP__;
    return a.selectPlace(a.landmarks.find(r=>r.id===target),{mode:'overview'});
  },target);
  async function inspect(label, variant, detail=false) {
    phase(label);
    await page.waitForFunction(({id,variant,detail,macro,key})=>{
      const s=window.__SHANGHAI_APP__?.scene;
      if(!s || s.map.isMoving() || s.map.getCanvas().clientWidth!==innerWidth) return false;
      const asset=s.getLandmarkAssetState(id);
      if(!asset?.visible || asset.status!=='loaded' || (variant && asset.variant!==variant)) return false;
      const c=s.getCandidateIntegrationState();
      if(!c.clips.some(r=>r.id===id)) return false;
      if(!detail) return true;
      const stream=s.getStreamingState(), states=c.vector.filter(v=>v.active);
      const feature=s.map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:key});
      const group=c.shader.ownerScopedSources.find(g=>g.macro_id===macro && g.clip_feature_local_ids.includes(360));
      return (feature.localModel||feature.candidateModel) && states.every(v=>!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer.ready))
        && stream.active.some(r=>r.id===macro&&r.visible) && group && stream.detail.active.some(r=>r.id===group.id);
    }, {id,variant,detail,macro,key:row.source_feature_ids.building[0]}, {timeout:480000,polling:800});
    await page.evaluate(()=>new Promise(done=>{
      const m=window.__SHANGHAI_APP__.scene.map;
      m.once('render',()=>{m.once('render',()=>done());m.triggerRepaint();}); m.triggerRepaint();
    }));
    const d=await page.evaluate(({id,macro,key,neighbor,controls})=>{
      const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,c=s.getCandidateIntegrationState(),st=s.getStreamingState();
      const v=s.getLandmarkAssetState(id), beacons=s.getBuildingBeaconState();
      const vec=k=>m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:k});
      return {title:document.querySelector('#location-name').textContent, selection:location.hash, mode:a.mode,
        streetWalkDisabled:document.querySelector('#walk-mode').disabled, viewport:[innerWidth,innerHeight], labels:beacons.count,
        zoom:m.getZoom(),bearing:m.getBearing(),pitch:m.getPitch(),center:m.getCenter(),contextLost:m.painter.context.gl.isContextLost(),
        asset:{variant:v.variant,sha256:v.verifiedAsset.sha256,bytes:v.verifiedAsset.bytes,triangles:v.triangles},
        ownerSource:vec(key),neighborSource:vec(neighbor),vector:c.vector.map(v=>({source:v.source,active:v.active,pending:v.pending,partialIDs:v.partialIDs,clippingErrors:v.clippingErrors,residual:v.residualLayer})),clip:c.clips.find(r=>r.id===id),
        ownerGroup:c.shader.ownerScopedSources.find(g=>g.macro_id===macro&&g.clip_feature_local_ids.includes(360)),
        neighborGroups:c.shader.ownerScopedSources.filter(g=>g.macro_id===macro&&g.feature_local_ids.includes(1995)),
        nearGroups:st.detail.active.map(r=>r.id),probes:controls.map(p=>({...p,actual:s.collisionAt(...p.point)}))};
    },{id,macro,key:row.source_feature_ids.building[0],neighbor:neighbor.key.slice('building:'.length),controls});
    assert.equal(d.title,row.name);assert.equal(d.mode,'overview');assert(d.streetWalkDisabled);assert(!d.contextLost);assert.equal(d.labels,count);
    assert.equal(new URLSearchParams(d.selection.slice(1)).get('landmark'),id);
    assert.deepEqual(d.clip.owner,row.owner);assert.deepEqual(d.clip.geometry,row.replacement_geometry);assert.deepEqual(d.clip.osm_replacement_geometry,row.osm_replacement_geometry);
    assert(!d.neighborSource.candidateModel);
    const expected=row.assets[d.asset.variant==='full'?'web':'lod'];
    for(const k of ['bytes','sha256','triangles']) assert.equal(d.asset[k],expected[k]);
    if(detail){
      assert(d.ownerSource.localModel||d.ownerSource.candidateModel);
      assert.deepEqual(d.ownerGroup.feature_local_ids.toSorted((a,b)=>a-b),source.near.local_ids.toSorted((a,b)=>a-b));
      assert.deepEqual(d.ownerGroup.clip_feature_local_ids,[360]);
      for(const g of d.neighborGroups) assert(!g.clip_feature_local_ids.includes(1995));
      for(const p of d.probes) assert.equal(p.actual,p.expected,p.name);
    }
    report.views.push({label,detail,...d});save();
  }
  try {
    await page.goto(base+'index.html#landmark='+id+'&mode=overview',{waitUntil:'domcontentloaded'});
    await inspect('desktop selected',null); await capture('map-desktop');
    const panel=page.locator('#panel-toggle');
    if(await panel.getAttribute('aria-expanded')==='true') await panel.click();
    await move({center:[121.4513915,31.2312208],zoom:20.5,bearing:12,pitch:70,elevation:9.2});
    await inspect('rounded street entrance, sign and windows','full',true); await capture('map-street-corner');
    await move({center:[row.lng,row.lat],zoom:18.85,bearing:28,pitch:36,elevation:10});
    await inspect('roof and east party wall','full',true); await capture('map-roof-and-neighbor');
    const easternTile=macro+'/'+macro+'-'+path.posix.basename(neighbor.file,'.glb.gz');
    if (!report.views.at(-1).nearGroups.includes(easternTile)) {
      const east=controls.find(p=>p.sourceLocalIds.includes(1995));
      await move({center:east.point,zoom:19.45,bearing:20,pitch:38,elevation:12});
    }
    await page.waitForFunction(tile=>window.__SHANGHAI_APP__.scene.getStreamingState().detail.active.some(r=>r.id===tile),easternTile,{timeout:300000,polling:800});
    const eastState=await page.evaluate(({macro,tile,point})=>{
      const s=window.__SHANGHAI_APP__.scene, c=s.getCandidateIntegrationState();
      return {tile,loaded:s.getStreamingState().detail.active.some(g=>g.id===tile),ground:s.collisionAt(...point),
        groups:c.shader.ownerScopedSources.filter(g=>g.macro_id===macro && g.feature_local_ids.includes(1995))};
    },{macro,tile:easternTile,point:controls.find(p=>p.sourceLocalIds.includes(1995)).point});
    assert(eastState.loaded);assert.equal(eastState.ground,'building');
    assert(eastState.groups.every(g=>!g.clip_feature_local_ids.includes(1995)));report.eastBuilding=eastState;save();
    await move({center:[row.lng,row.lat],zoom:15.5,bearing:12,pitch:35,elevation:0});
    await inspect('city LOD','distant');
    await page.setViewportSize({width:390,height:844});
    await page.waitForFunction(()=>window.__SHANGHAI_APP__.scene.map.transform.width===390);
    await select(id);await inspect('mobile selected',null);await capture('map-mobile');
    for(const input of ['mouse','touch']){
      phase('all city markers and '+input);
      await select(previous);
      if(input==='touch') await page.setViewportSize({width:320,height:568});
      await page.evaluate(zero=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;m.setMaxBounds(null);m.setCenterClampedToGround(true);
        m.jumpTo({center:[121.45,31.2],zoom:8,pitch:0,bearing:0,elevation:0,padding:zero});s.refreshBuildingBeacons();},zero);
      await page.waitForFunction(count=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState();return b.viewportLabelCount===count&&b.overlapFallbackCount===0&&b.sourceIds.every(i=>s.map.isSourceLoaded(i));},count,{timeout:240000,polling:600});
      const b=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState(),p=b.labelPositions;return {count:p.length,allHit:p.every(x=>s.pickBuildingBeacon(x)===x.id),target:p.find(x=>x.id===id)};},id);
      assert.equal(b.count,count);assert(b.allHit&&b.target);report[input]=b;
      if(input==='touch'){
        try { await capture('map-city-beacons',45000); } catch(error) { report.denseScreenshotFailure=String(error);save(); }
        const target=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,p=s.getBuildingBeaconState().labelPositions.find(v=>v.id===id);
          return {x:p.x,y:p.y,picked:s.pickBuildingBeacon(p)};},id);
        assert.equal(target.picked,id);report.touch.tapPoint=target;
        await page.touchscreen.tap(target.x,target.y);
      } else await page.mouse.click(b.target.x,b.target.y);
      await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id,{timeout:120000});
      await inspect(input+' selected',null);
    }
    for(const [role,asset] of Object.entries(manifest.assets)){
      const file=path.posix.join(path.posix.dirname(row.candidate_manifest),asset.file);
      const r=await page.request.get(new URL(file,base).href),b=await r.body();
      assert.equal(r.status(),200);assert.equal(sha(b),asset.sha256);assert.equal(b.length,asset.bytes);
      report.downloads.push({file,role,bytes:b.length,sha256:sha(b)});
    }
    for(const leaf of ['READY.json','far.glb',source.near.file,neighbor.file]){
      const req=report.cityRequests.find(r=>r.file===prefix+leaf);
      assert(req,'Missing live city input '+leaf);assert.equal(req.sha256,source.frozen_bindings[leaf].sha256);
    }
    assert.deepEqual(report.errors,[]);assert.deepEqual(report.httpErrors,[]);report.completed=true;
  } catch(error) {
    report.failure=String(error.stack||error);
    await capture('failure-state').catch(()=>{});throw error;
  } finally {
    await browser.close();report.finished=new Date().toISOString();report.browserClosed=true;save();
  }
}
run().catch(error=>{console.error(error);process.exitCode=1;});
