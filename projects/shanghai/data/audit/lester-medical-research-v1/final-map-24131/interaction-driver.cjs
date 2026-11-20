/* Run against the shared Shanghai page with actual city tiles and a fresh output directory. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');

const id = 'jingan-lester-medical-research-institute';
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
  const footPath = 'data/audit/lester-medical-research-v1/footprint-review.json';
  const foot = json(footPath);
  const source = json('source/precise/'+id+'/footprint-review.json');
  const row = catalog.models.find(x => x.id === id);
  assert.equal(catalog.resulting_city_count,169);
  assert.equal(catalog.models.at(-1).id,id);
  assert.ok(row?.name.includes('雷士德') && row.districtId === '310106');
  assert.deepEqual(row.owner, {macro_id: '14-13719-6694',feature_local_id: 260});
  assert.equal(row.source_feature_ids.building[0], '1404ca67-d804-4bee-952f-b1cf6d6e17a1');
  const manifest = json(row.candidate_manifest);
  assert.deepEqual(row.owner,foot.proposed_placement_contract.owner);
  assert.deepEqual(row.collision_geometry,foot.proposed_placement_contract.collision_geometry);
  assert.deepEqual(row.source_section_caps,foot.proposed_placement_contract.source_section_caps);
  const sourceGroup=source.near_groups[0];
  assert.ok(sourceGroup.ids.length===11 && sourceGroup.ids.includes(260));
  results.bindings = Object.fromEntries([catalogPath, footPath, row.candidate_manifest,'src/map-scene.js','src/app.js',
    'src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/candidate-source-sections.js','index.html',
    'landmarks.html','data/audit/lester-medical-research-v1/inventory-increment.json','data/global-models/additional-placement.json',
    'data/global-models/candidate-inventory.json','data/audit/global-model-integration-v1/inventory.json'].map(f=>[f,sha(local(f))]));
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
    const overlayAssets=new Set(['src/map-scene.js','src/building-beacons.js','src/building-beacon-groups.js']);
    const overlayReceipts=new Map(),pendingOverlay=[];
    page.on('response',r=>{
      const u=new URL(r.url());
      const relative=u.pathname.slice(1);
      if(u.origin===new URL(base).origin && r.status()===200 && overlayAssets.has(relative)){
        const at=new Date().toISOString();
        pendingOverlay.push(r.body().then(bytes=>{
          const receipt={url:r.url(),at,bytes:bytes.length,sha256:sha(bytes)};
          assert.equal(receipt.sha256,sha(local(relative)),relative);
          overlayReceipts.set(relative,receipt);
        }));
      }
      if(r.status()>=400) results.request_errors.push({url:r.url(),status:r.status()});
      if(u.protocol===new URL(base).protocol&&u.origin===new URL(base).origin&&[200,206].includes(r.status()))actualRequests.add(u.pathname.slice(1));
    });
    let sawStartupTimeout=false;
    page.on('console',msg=>{
      if(msg.type()==='warning' && msg.text().includes('本地建筑目录暂不可用') && msg.text().includes('timed out'))sawStartupTimeout=true;
    });
    const snapshot = async (name, variant, near) => {
      console.log('Preparing',name);
      if(near && name.startsWith('main-')){
        // The directory click returns before the application finishes selecting
        // its city index. Observe the actual initial selection before inspecting
        // warnings or waiting for a tile that the coarse fallback cannot serve.
        await page.waitForFunction(()=>{
          const scene=window.__SHANGHAI_APP__?.scene;
          if(!scene)return false;
          const detail=scene.getStreamingState().detail;
          const coarse=performance.getEntriesByType('resource').some(entry=>
            new URL(entry.name).pathname.endsWith('/assets/city/manifest.json'));
          return detail.available>0 || detail.parents>0 || coarse;
        },null,{polling:500,timeout:80000});
        const selection=await page.evaluate(()=>{
          const state=window.__SHANGHAI_APP__.scene.getStreamingState();
          return {parents:state.detail.parents,available:state.detail.available,
            coarseRequested:performance.getEntriesByType('resource').some(entry=>
              new URL(entry.name).pathname.endsWith('/assets/city/manifest.json'))};
        });
        (results.initial_city_indices ||= {})[name]=selection;
        if((sawStartupTimeout || selection.coarseRequested) && !selection.parents && !selection.available){
          const recovered=await page.evaluate(async()=>{
            const s=window.__SHANGHAI_APP__.scene,r=await s.setCityManifest('assets/city-detail/manifest.json');
            return {source:'assets/city-detail/manifest.json',fallback:Boolean(r.fallback),error:r.error||null};
          });
          (results.detail_index_retries ||= {})[name]=recovered;
          assert.equal(recovered.fallback,false);
        }
        sawStartupTimeout=false;
      }
      console.log('Checking',name);
      await page.waitForFunction(({id,owner,variant,near,source,requireLabel})=>{
        const s=window.__SHANGHAI_APP__?.scene;
        if(!s || s.map.isMoving())return false;
        const asset=s.getLandmarkAssetState(id);
        if(!asset || asset.status!=='loaded' || !asset.visible || (variant && asset.variant!==variant))return false;
        const stream=s.getStreamingState();
        const group=s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>
          g.macro_id===owner.macro_id && g.clip_feature_local_ids.includes(owner.feature_local_id) && g.feature_local_ids.includes(1130));
        if(near && (!group || !stream.detail.active.some(g=>g.id===group.id)))return false;
        const b=s.getBuildingBeaconState(),label=b.labelPositions.find(l=>l.id===id);
        const suppressed=s.map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:source});
        if(near && !(suppressed.candidateModel || suppressed.localModel))return false;
        return !requireLabel || (label && s.pickBuildingBeacon({x:label.x,y:label.y})===id);
      },{id,owner:row.owner,variant,near,source:row.source_feature_ids.building[0],requireLabel:name.startsWith('main-')},{polling:700,timeout:80000});
      await page.evaluate(()=>new Promise(resolve=>{
        const m=window.__SHANGHAI_APP__.scene.map;
        m.once('render',()=>{m.once('render',()=>resolve());m.triggerRepaint();});m.triggerRepaint();
      }));
      const state=await page.evaluate(({id,owner,src})=>{
        const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,c=s.getCandidateIntegrationState();
        const b=s.getBuildingBeaconState(),label=b.labelPositions.find(l=>l.id===id);
        const group=c.shader.ownerScopedSources.find(g=>g.macro_id===owner.macro_id && g.clip_feature_local_ids.includes(owner.feature_local_id) && g.feature_local_ids.includes(1130));
        return {id,selected: new URLSearchParams(location.hash.slice(1)).get('landmark'),name:document.querySelector('#location-name').textContent,
          mode:app.mode,asset:s.getLandmarkAssetState(id),clip:c.clips.find(g=>g.id===id),near_group:group||null,source_cap:c.sourceSections.find(section=>section.id===id)||null,
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
        assert.deepEqual(state.near_group.clip_feature_local_ids,[260]);
        assert.equal(state.source_cap,null);
        assert.deepEqual([...state.near_group.feature_local_ids].sort((a,b)=>a-b),[...sourceGroup.ids].sort((a,b)=>a-b));
        assert.ok(state.source_state.candidateModel || state.source_state.localModel);
      }
      console.log('[observed]',name,state.asset.variant,state.beacons);
      results.views.push({view:name,...state});
      const img=await page.screenshot({path:path.join(output,name+'.png'),timeout:80000});
      results.screenshots.push({file:name+'.png',sha256:sha(img),bytes:img.length}); save();
    };
    const camera=async(u,v,elevation,zoom,pitch,bearing)=>{
      const angle=row.heading*Math.PI/180,lat=row.lat*Math.PI/180;
      const east=u*Math.cos(angle)+v*Math.sin(angle),north=-u*Math.sin(angle)+v*Math.cos(angle);
      const center=[row.lng+east/(6371008.8*Math.cos(lat))*180/Math.PI,row.lat+north/6371008.8*180/Math.PI];
      await page.evaluate(opt=>{const s=window.__SHANGHAI_APP__.scene;
        s.map.setCenterClampedToGround(false);s.map.jumpTo(opt);s.loadLandmarks();s.refreshBuildingBeacons();
      },{center,elevation,zoom,pitch,bearing,padding:{top:0,bottom:145,left:92,right:0}});
    };
    results.recovery_from_desktop='Earlier real desktop frame, 168 input binding and four file receipts live in ../main; this new process starts fresh on mobile.';
    results.http_assets=JSON.parse(fs.readFileSync('/dev/shm/lestermed131-final/main/main-map-browser.json')).http_assets;
    console.log('Started mobile-only continuation');save();
    await page.setViewportSize({width:390,height:844});
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
    console.log('Reached 169-card directory');
    await page.locator('#district-310106 [data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').tap();
    await page.waitForFunction(id=>{const scene=window.__SHANGHAI_APP__?.scene;return scene&&!scene.map.isMoving()&&scene.getLandmarkAssetState(id)?.visible;},id,{polling:250,timeout:80000});
    console.log('Default mobile re-entered via catalog');
    const mobileToggle=page.locator('#panel-toggle');if(await mobileToggle.getAttribute('aria-expanded')==='true')await mobileToggle.tap();
    const fromZoom=await page.evaluate(()=>window.__SHANGHAI_APP__.scene.map.getZoom());
    const plus=page.locator('#zoom-in');assert.equal(await plus.count(),1);
    await plus.tap();await page.waitForFunction(z=>{const m=window.__SHANGHAI_APP__.scene.map;return !m.isMoving()&&m.getZoom()>z+.65;},fromZoom,{timeout:60000});
    await snapshot('mobile-public-zoom','full',false);
    const keyboardSelect=async(text,target)=>{
      await page.keyboard.press('/');const input=page.locator('#place-search');
      assert.equal(await input.evaluate(e=>e===document.activeElement),true);
      await input.fill(text);const item=page.locator('#place-list [data-place="'+target+'"]');assert.equal(await item.count(),1);
      let tabs=0;while(!await item.evaluate(e=>e===document.activeElement)&&tabs<16){await page.keyboard.press('Tab');tabs++;}
      assert.equal(await item.evaluate(e=>e===document.activeElement),true);
      await item.evaluate(b=>b.addEventListener('click',ev=>{window.__LESTER_TAP__={trusted:ev.isTrusted,detail:ev.detail,pick:b.dataset.place};},{once:true}));
      await page.keyboard.press('Enter');const receipt=await page.evaluate(()=>window.__LESTER_TAP__);
      assert.deepEqual(receipt,{trusted:true,detail:0,pick:target});
      await page.waitForFunction(t=>new URLSearchParams(location.hash.slice(1)).get('landmark')===t,target);
      const overview=page.locator('#overview-mode');await overview.focus();await page.keyboard.press('Enter');
      await page.waitForFunction(()=>document.querySelector('#overview-mode').getAttribute('aria-pressed')==='true');
      return {text,tabs,...receipt};
    };
    results.keyboard_search=[];
    results.keyboard_search.push(await keyboardSelect('雷氏德工学院','hongkou-lester-institute'));
    await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene,g=s.getLandmarkAssetState(id);return !s.map.isMoving()&&!g?.visible&&!s.getCandidateIntegrationState().clips.some(c=>c.id===id);},id,{polling:400,timeout:65000});
    results.unloaded_on_other_selection=await page.evaluate(id=>{const scene=window.__SHANGHAI_APP__.scene;return {selected:new URLSearchParams(location.hash.slice(1)).get('landmark'),own_visible:scene.getLandmarkAssetState(id)?.visible??false,own_clip:scene.getCandidateIntegrationState().clips.some(c=>c.id===id)};},id);
    results.keyboard_search.push(await keyboardSelect('雷士德医学研究院',id));
    await snapshot('returned-mobile','full',false);
    save();
    await page.setViewportSize({width:900,height:650});
    const panel=page.locator('#panel-toggle');
    if(await panel.getAttribute('aria-expanded')==='true') await panel.click();
    await camera(0,5,8,18.87,44,-14);await snapshot('street-front','full',true);
    await camera(0,-1.6,3.2,20.90,50,-14);
    await snapshot('bronze-lamp-pair','full',true);
    const ground=foot.ground_probes.map(p=>({name:p.label,xy:p.world,expected:p.blocked?'building':null}));
    ground.push(...[{"name": "retained neighboring source 583", "xy": [121.444587705, 31.23095637], "expected": "building"}, {"name": "retained neighboring source 679", "xy": [121.44490398798396, 31.231011414999998], "expected": "building"}, {"name": "retained neighboring source 1130", "xy": [121.44577726045037, 31.230782065], "expected": "building"}, {"name": "retained neighboring source 1156", "xy": [121.44469728585028, 31.230575645000002], "expected": "building"}, {"name": "retained neighboring source 2657", "xy": [121.44504654959366, 31.23084628], "expected": "building"}]);
    results.ground_probes=await page.evaluate(queries=>{
      const s=window.__SHANGHAI_APP__.scene;return queries.map(q=>({...q,actual:s.collisionAt(...q.xy)}));
    },ground);
    save();for(const p of results.ground_probes)assert.equal(p.actual,p.expected,p.name);
    await camera(0,-0.7,14.2,20.28,43,-13);
    await snapshot('stepped-parapet','full',true);
    await camera(-33.5,15.25,4.8,20.25,45,62);
    await snapshot('western-entry','full',true);
    await camera(0,0,0,15.45,32,0);
    await snapshot('distant','distant',false);
    for(const asset of results.http_assets){
      asset.seen_in_scene=actualRequests.has(asset.file);
      if(['full','lod'].includes(asset.role))assert.ok(asset.seen_in_scene);
    }
    const root='assets/city-detail/macros/'+row.owner.macro_id+'/';
    results.map_files_seen=[];
    for(const suffix of ['far.glb',sourceGroup.file]){
      const file=root+suffix;
      assert.ok(actualRequests.has(file),'Expected real shared source response: '+file);
      const response=await page.request.get(new URL(file,base).href),data=await response.body();
      const digest=sha(data);
      assert.equal(response.status(),200);
      assert.equal(digest,source.frozen_bindings[suffix].sha256);
      results.map_files_seen.push({file,sha256:digest,bytes:data.length,origin:response.headers()['x-audit-origin']});
    }
    for(const [f,sum] of Object.entries(results.bindings))assert.equal(sha(local(f)),sum,'Input changed: '+f);
    assert.deepEqual(results.page_errors,[]);assert.deepEqual(results.console_errors,[]);assert.deepEqual(results.request_errors,[]);
    results.http_response_paths=[...actualRequests].sort();
    await Promise.all(pendingOverlay);
    assert.equal(overlayReceipts.size,3);
    results.actual_overlay_response_bodies=Object.fromEntries(overlayReceipts);
    results.completed=true;
  } catch(error) {
    results.failure=String(error.stack);
    if(page) {
      results.failure_state=await page.evaluate(id=>{
        const a=window.__SHANGHAI_APP__,s=a?.scene;
        if(!s)return {startup:document.body.innerText.slice(0,1500)};
        const beacons=s.getBuildingBeaconState();
        return {hash:location.hash,asset:s.getLandmarkAssetState(id),label:beacons.labelPositions.find(l=>l.id===id),
          active:s.getStreamingState().detail.active.slice(0,3),ownerState:s.getCandidateIntegrationState().shader.ownerScopedSources.filter(r=>r.feature_local_ids.includes(260))};
      },id).catch(e=>({inspection_error:String(e)}));
    }
    throw error;
  }
  finally{await browser.close();results.browser_closed=true;results.finished_utc=new Date().toISOString();save();}
}
run().catch(err=>{console.error(err);process.exitCode=1;});
