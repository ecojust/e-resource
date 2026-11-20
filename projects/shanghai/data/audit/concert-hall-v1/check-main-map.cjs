/* Run against the shared Shanghai page with actual city tiles and a fresh output directory. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');

const id = 'huangpu-shanghai-concert-hall';
const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(__dirname, '../../..');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const output = process.env.QA_OUTPUT_DIR || __dirname;
const reportPath = path.join(output, 'main-map-browser.json');
const sha = data => createHash('sha256').update(data).digest('hex');
const local = file => fs.readFileSync(path.join(project, file));
const json = file => JSON.parse(local(file));
const results = {model_id: id, started_utc: new Date().toISOString(), completed: false,
  screenshots: [], views: [], http_assets: [], page_errors: [], request_errors: [], console_errors: [],
  server: base, script_sha256: sha(fs.readFileSync(__filename))};
const save = () => fs.writeFileSync(reportPath, JSON.stringify(results, null, 2) + '\n');

async function run() {
  fs.mkdirSync(output, {recursive: true});
  assert.ok(!fs.existsSync(reportPath), 'Use a fresh output directory');
  const catalogPath = 'data/candidate-city-integrations.json';
  const catalog = json(catalogPath);
  const footPath = 'data/audit/concert-hall-v1/footprint-review.json';
  const foot = json(footPath);
  const row = catalog.models.find(x => x.id === id);
  assert.ok(row?.name.includes('音乐厅') && row.districtId === '310101');
  assert.deepEqual(row.owner, {macro_id: '14-13720-6694',feature_local_id: 2500});
  assert.equal(row.source_feature_ids.building[0], 'd49e6b9c-1cbb-47f7-a73f-bb8c59295130');
  const manifest = json(row.candidate_manifest);
  results.bindings = Object.fromEntries([catalogPath, footPath, row.candidate_manifest,'src/map-scene.js','src/app.js',
    'src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','index.html',
    'landmarks.html'].map(f=>[f,sha(local(f))]));
  results.city_count = catalog.resulting_city_count;
  const actualRequests = new Set();
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    headless: true, args: ['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',...(process.env.QA_CDP_PORT ? ['--remote-debugging-port='+process.env.QA_CDP_PORT] : [])]});
  let page;
  try {
    results.browser = browser.version();
    page = await browser.newPage({viewport: {width:900,height:650},hasTouch:true,ignoreHTTPSErrors:true});
    page.setDefaultTimeout(180000);
    page.on('pageerror', e => results.page_errors.push(String(e)));
    page.on('console', msg=>{if (msg.type()==='error') results.console_errors.push({text:msg.text(),url:msg.location().url});});
    page.on('requestfailed', req=>{if(req.failure()?.errorText !== 'net::ERR_ABORTED') results.request_errors.push({url:req.url(),error:req.failure()?.errorText});});
    page.on('response',r=>{
      const u=new URL(r.url());
      if(r.status()>=400) results.request_errors.push({url:r.url(),status:r.status()});
      if(u.origin===new URL(base).origin&&r.status()===200)actualRequests.add(u.pathname.slice(1));
    });
    const snapshot = async (name, variant, near) => {
      console.log('Checking',name);
      await page.waitForFunction(({id,owner,variant,near,source,requireLabel})=>{
        const s=window.__SHANGHAI_APP__?.scene;
        if(!s || s.map.isMoving())return false;
        const asset=s.getLandmarkAssetState(id);
        if(!asset || asset.status!=='loaded' || !asset.visible || (variant && asset.variant!==variant))return false;
        const stream=s.getStreamingState();
        const group=s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>
          g.macro_id===owner.macro_id && g.clip_feature_local_ids.includes(owner.feature_local_id) && g.feature_local_ids.includes(199));
        if(near && (!group || !stream.detail.active.some(g=>g.id===group.id)))return false;
        const b=s.getBuildingBeaconState(),label=b.labelPositions.find(l=>l.id===id);
        const suppressed=s.map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:source});
        if(near && !(suppressed.candidateModel || suppressed.localModel))return false;
        return !requireLabel || (label && s.pickBuildingBeacon({x:label.x,y:label.y})===id);
      },{id,owner:row.owner,variant,near,source:row.source_feature_ids.building[0],requireLabel:name.startsWith('main-')},{polling:700,timeout:300000});
      await page.evaluate(()=>new Promise(resolve=>{
        const m=window.__SHANGHAI_APP__.scene.map;
        m.once('render',()=>{m.once('render',()=>resolve());m.triggerRepaint();});m.triggerRepaint();
      }));
      const state=await page.evaluate(({id,owner,src})=>{
        const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,c=s.getCandidateIntegrationState();
        const b=s.getBuildingBeaconState(),label=b.labelPositions.find(l=>l.id===id);
        const group=c.shader.ownerScopedSources.find(g=>g.macro_id===owner.macro_id && g.clip_feature_local_ids.includes(owner.feature_local_id) && g.feature_local_ids.includes(199));
        return {id,selected: new URLSearchParams(location.hash.slice(1)).get('landmark'),name:document.querySelector('#location-name').textContent,
          mode:app.mode,asset:s.getLandmarkAssetState(id),clip:c.clips.find(g=>g.id===id),near_group:group||null,
          source_state:m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:src}),
          selected_label:label,picked:label?s.pickBuildingBeacon({x:label.x,y:label.y}):null,beacons:b.count,
          viewport:[innerWidth,innerHeight],camera:{center:m.getCenter(),zoom:m.getZoom(),bearing:m.getBearing(),pitch:m.getPitch()},
          webgl_context_lost:m.painter.context.gl.isContextLost(),walk_disabled:document.querySelector('#start-walk').disabled};
      },{id,owner:row.owner,src:row.source_feature_ids.building[0]});
      assert.equal(state.selected,id); assert.equal(state.name,row.name);
      if(name.startsWith('main-'))assert.equal(state.picked,id);
      assert.equal(state.mode,'overview'); assert.equal(state.walk_disabled,true);
      assert.equal(state.beacons,catalog.resulting_city_count); assert.equal(state.webgl_context_lost,false);
      const resolved=state.asset.variant==='full'?'full':'lod';
      const expected=manifest.assets[resolved];
      assert.equal(state.asset.verifiedAsset.sha256,expected.sha256); assert.equal(state.asset.triangles,expected.triangles);
      assert.deepEqual(state.clip.owner,row.owner); assert.deepEqual(state.clip.geometry,row.replacement_geometry);
      if (near) {
        assert.equal(state.near_group.clip_feature_local_ids.includes(199),false);
        assert.ok(state.source_state.candidateModel || state.source_state.localModel);
      }
      results.views.push({view:name,...state});
      const img=await page.screenshot({path:path.join(output,name+'.png'),timeout:90000});
      results.screenshots.push({file:name+'.png',sha256:sha(img),bytes:img.length}); save();
    };
    const camera=async(u,v,elevation,zoom,pitch,bearing)=>{
      const angle=row.heading*Math.PI/180,lat=row.lat*Math.PI/180;
      const east=u*Math.cos(angle)+v*Math.sin(angle),north=-u*Math.sin(angle)+v*Math.cos(angle);
      const center=[row.lng+east/(6371008.8*Math.cos(lat))*180/Math.PI,row.lat+north/6371008.8*180/Math.PI];
      await page.evaluate(opt=>{const s=window.__SHANGHAI_APP__.scene;
        s.map.setCenterClampedToGround(false);s.map.jumpTo(opt);s.loadLandmarks();s.refreshBuildingBeacons();
      },{center,elevation,zoom,pitch,bearing,padding:{top:0,bottom:0,left:0,right:0}});
    };
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
    const cards=page.locator('.landmark-card[data-landmark]');
    assert.equal(await cards.count(), catalog.resulting_city_count);
    await page.locator('#district-310101 [data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').click();
    await snapshot('main-desktop', null, false);
    const panel=page.locator('#panel-toggle');
    if(await panel.getAttribute('aria-expanded')==='true') await panel.click();
    await camera(0,13,9,19.15,58,row.heading);
    await snapshot('northwest-entrance','full',true);
    await camera(0,45,10,18.85,45,row.heading-155);
    await snapshot('southeast-entrance','full',true);
    await camera(-1,33,12,18.8,20,row.heading-35);
    await snapshot('auditorium-roof','full',true);
    await camera(0,30,0,15.5,30,row.heading);
    await snapshot('distant', 'distant', false);
    await page.setViewportSize({width:390,height:844});
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
    await page.locator('#district-310101 [data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').tap();
    await snapshot('main-mobile',null,false);
    for(const [role,a] of Object.entries(manifest.assets)) {
      const file=path.posix.join(path.posix.dirname(row.candidate_manifest),a.file);
      const response=await page.request.get(new URL(file,base).href),data=await response.body();
      assert.equal(response.status(),200);assert.equal(data.length,a.bytes);assert.equal(sha(data),a.sha256);
      if(['full','lod'].includes(role))assert.ok(actualRequests.has(file));
      results.http_assets.push({role,file,bytes:data.length,sha256:sha(data),seen_in_scene:actualRequests.has(file)});
    }
    const root='assets/city-detail/macros/'+row.owner.macro_id+'/';
    results.map_files_seen=[];
    for(const suffix of ['far.glb',foot.shared_near_file]){
      const file=root+suffix;
      assert.ok(actualRequests.has(file),'Expected real shared source response: '+file);
      const response=await page.request.get(new URL(file,base).href),data=await response.body();
      const digest=sha(data);
      assert.equal(response.status(),200);
      assert.equal(digest,foot.inputs[path.posix.basename(suffix)]);
      results.map_files_seen.push({file,sha256:digest,bytes:data.length,origin:response.headers()['x-audit-origin']});
    }
    for(const [f,sum] of Object.entries(results.bindings))assert.equal(sha(local(f)),sum,'Input changed: '+f);
    assert.deepEqual(results.page_errors,[]);assert.deepEqual(results.console_errors,[]);assert.deepEqual(results.request_errors,[]);
    results.completed=true;
  } catch(error) {
    results.failure=String(error.stack);
    if(page) {
      results.failure_state=await page.evaluate(id=>{
        const a=window.__SHANGHAI_APP__,s=a?.scene;
        if(!s)return {startup:document.body.innerText.slice(0,1500)};
        const beacons=s.getBuildingBeaconState();
        return {hash:location.hash,asset:s.getLandmarkAssetState(id),label:beacons.labelPositions.find(l=>l.id===id),
          active:s.getStreamingState().detail.active.slice(0,3),ownerState:s.getCandidateIntegrationState().shader.ownerScopedSources.filter(r=>r.feature_local_ids.includes(2500))};
      },id).catch(e=>({inspection_error:String(e)}));
    }
    throw error;
  }
  finally{await browser.close();results.browser_closed=true;results.finished_utc=new Date().toISOString();save();}
}
run().catch(err=>{console.error(err);process.exitCode=1;});
