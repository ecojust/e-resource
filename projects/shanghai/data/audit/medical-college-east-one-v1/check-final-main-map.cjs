/* Run against the shared Shanghai page with actual city tiles and a fresh output directory. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');

const id = 'xuhui-medical-college-east-building-one';
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
  const footPath = 'data/audit/medical-college-east-one-v1/footprint-review.json';
  const foot = json(footPath);
  const source = json('source/precise/'+id+'/footprint-review.json');
  const row = catalog.models.find(x => x.id === id);
  assert.equal(catalog.resulting_city_count,166);
  assert.equal(catalog.models.at(-1).id,id);
  assert.ok(row?.name.includes('东一号楼') && row.districtId === '310104');
  assert.deepEqual(row.owner, {macro_id: '14-13719-6696',feature_local_id: 2076});
  assert.equal(row.source_feature_ids.building[0], 'd2dc605e-5be1-4b23-89d9-bcd2c0aebdc1');
  const manifest = json(row.candidate_manifest);
  assert.deepEqual(row.owner,foot.proposed_placement_contract.owner);
  assert.deepEqual(row.collision_geometry,foot.proposed_placement_contract.collision_geometry);
  assert.deepEqual(row.source_section_caps,foot.proposed_placement_contract.source_section_caps);
  const sourceGroup=source.near_groups[0];
  assert.ok(sourceGroup.ids.length===5 && sourceGroup.ids.includes(2076));
  results.bindings = Object.fromEntries([catalogPath, footPath, row.candidate_manifest,'src/map-scene.js','src/app.js',
    'src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','src/candidate-source-sections.js','index.html',
    'landmarks.html','data/audit/medical-college-east-one-v1/inventory-increment.json','data/global-models/additional-placement.json',
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
        },null,{polling:500,timeout:300000});
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
          g.macro_id===owner.macro_id && g.clip_feature_local_ids.includes(owner.feature_local_id) && g.feature_local_ids.includes(198));
        if(near && (!group || !stream.detail.active.some(g=>g.id===group.id)))return false;
        const b=s.getBuildingBeaconState(),label=b.labelPositions.find(l=>l.id===id);
        const suppressed=s.map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:source});
        if(near && !(suppressed.candidateModel || suppressed.localModel))return false;
        return !requireLabel || (label && s.pickBuildingBeacon({x:label.x,y:label.y})===id);
      },{id,owner:row.owner,variant,near,source:row.source_feature_ids.building[0],requireLabel:name.startsWith('main-')},{polling:700,timeout:420000});
      await page.evaluate(()=>new Promise(resolve=>{
        const m=window.__SHANGHAI_APP__.scene.map;
        m.once('render',()=>{m.once('render',()=>resolve());m.triggerRepaint();});m.triggerRepaint();
      }));
      const state=await page.evaluate(({id,owner,src})=>{
        const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,c=s.getCandidateIntegrationState();
        const b=s.getBuildingBeaconState(),label=b.labelPositions.find(l=>l.id===id);
        const group=c.shader.ownerScopedSources.find(g=>g.macro_id===owner.macro_id && g.clip_feature_local_ids.includes(owner.feature_local_id) && g.feature_local_ids.includes(198));
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
        assert.deepEqual(state.near_group.clip_feature_local_ids,[2076]);
        assert.equal(state.source_cap,null);
        assert.deepEqual([...state.near_group.feature_local_ids].sort((a,b)=>a-b),[...sourceGroup.ids].sort((a,b)=>a-b));
        assert.ok(state.source_state.candidateModel || state.source_state.localModel);
      }
      results.views.push({view:name,...state});
      let focusReport=null;
      if(['main-desktop','main-mobile'].includes(name)){
   const focus=await page.evaluate(id=>{
    const s=window.__SHANGHAI_APP__.scene,m=s.map,beacons=s.getBuildingBeaconState(),a=s.getLandmarkAssetState(id),angle=a.heading*Math.PI/180,rad=Math.PI/180,k=6371008.8*Math.cos(a.anchor[1]*rad),origin=Math.asinh(Math.tan(a.anchor[1]*rad)); const points=[];
    const layers=m.getStyle().layers.filter(l=>l.id.endsWith('labels-symbol')||l.id.endsWith('labels-numbers')).map(l=>l.id);
    const drawn=new Set(m.queryRenderedFeatures({layers}).map(v=>v.properties.id));
    const visibleLabels=beacons.labelPositions.filter(l=>drawn.has(l.id));
    for(const [name,x,y,z]of [['west arch',-4.25,6.76,2.6],['middle arch',-.95,6.76,2.6],['east arch',2.35,6.76,2.6],['west red pylon',-8.04,6.68,9],['east red pylon',6.08,6.68,9],['gallery',-.95,6.62,9.7],['golden auditorium ridge',-.95,-3.25,19.6]]){
     const en=x*Math.cos(angle)+y*Math.sin(angle),nn=-x*Math.sin(angle)+y*Math.cos(angle);const h={getElevationForLngLat:()=>z,getElevationForLngLatZoom:()=>z};
     const q=m.transform.locationToScreenPoint({lng:a.anchor[0]+en/k/rad,lat:Math.atan(Math.sinh(origin+nn/k))/rad},h);
     const overlaps=visibleLabels.filter(l=>Math.abs(q.x-l.x)<=l.width/2+1&&Math.abs(q.y-l.y)<=l.height/2+1);
     points.push({name,x:q.x,y:q.y,coveredBy:overlaps.map(l=>l.id),hitElement:document.elementFromPoint(q.x,q.y)?.tagName||null});
    }
    return {points,asset:a,labels:visibleLabels.map(l=>({...l,centerPick:s.pickBuildingBeacon({x:l.x,y:l.y})})),zoom:m.getZoom(),location:m.getCenter(),dpr:devicePixelRatio,viewport:[innerWidth,innerHeight],sceneCount:beacons.count,contextLost:m.painter.context.gl.isContextLost()};
   },id);
        assert.equal(focus.sceneCount,166);assert.equal(focus.asset.triangles,165976);
        assert.ok(!focus.contextLost);assert.equal(focus.points.length,7);
        for(const p of focus.points){assert.deepEqual(p.coveredBy,[],p.name);assert.equal(p.hitElement,'CANVAS',p.name);}
        for(const label of focus.labels)assert.equal(label.id,label.centerPick,label.id);
        focusReport={...focus,group:state.near_group,catalogSha256:results.bindings[catalogPath],url:page.url()};
      }
      const img=await page.screenshot({path:path.join(output,name+'.png'),timeout:300000});
      results.screenshots.push({file:name+'.png',sha256:sha(img),bytes:img.length});
      if(focusReport){focusReport.photo=results.screenshots.at(-1);fs.writeFileSync(path.join(output,name+'-focus.json'),JSON.stringify(focusReport,null,2)+'\n');}
      save();
    };
    const camera=async(u,v,elevation,zoom,pitch,bearing)=>{
      const angle=row.heading*Math.PI/180,lat=row.lat*Math.PI/180;
      const east=u*Math.cos(angle)+v*Math.sin(angle),north=-u*Math.sin(angle)+v*Math.cos(angle);
      const center=[row.lng+east/(6371008.8*Math.cos(lat))*180/Math.PI,row.lat+north/6371008.8*180/Math.PI];
      await page.evaluate(opt=>{const s=window.__SHANGHAI_APP__.scene;
        s.map.setCenterClampedToGround(false);s.map.jumpTo(opt);s.loadLandmarks();s.refreshBuildingBeacons();
      },{center,elevation,zoom,pitch,bearing,padding:{top:0,bottom:145,left:92,right:0}});
    };
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
    const cards=page.locator('.landmark-card[data-landmark]');
    assert.equal(await cards.count(), catalog.resulting_city_count);
    await page.locator('#district-310104 [data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').click();
    await snapshot('main-desktop','full',true);
    const previousBase=process.env.QA_PREVIOUS_URL;
    assert.ok(previousBase, 'Provide the actual preceding release URL.');
    const expectedPrior=process.env.QA_PREVIOUS_CATALOG_SHA256;
    assert.match(expectedPrior,/^[a-f0-9]{64}$/);
    const beforeResponse=await page.request.get(new URL(catalogPath,previousBase).href);
    const beforeData=await beforeResponse.body();
    const before=JSON.parse(beforeData);
    assert.equal(beforeResponse.status(),200);
    assert.equal(sha(beforeData),expectedPrior);
    assert.equal(before.resulting_city_count,165);
    assert.deepEqual(before.models,catalog.models.slice(0,-1));
    results.previous_catalog={url:beforeResponse.url(),sha256:sha(beforeData),city_count:165,unchanged_models:before.models.length};
    for(const [role,a] of Object.entries(manifest.assets)){
      const file=path.posix.join(path.posix.dirname(row.candidate_manifest),a.file);
      const response=await page.request.get(new URL(file,base).href),data=await response.body();
      assert.equal(response.status(),200);assert.equal(data.length,a.bytes);assert.equal(sha(data),a.sha256);
      results.http_assets.push({role,file,bytes:data.length,sha256:sha(data),seen_in_scene:actualRequests.has(file)});
    }
    save();
    await page.setViewportSize({width:390,height:844});
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
    await page.locator('#district-310104 [data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').tap();
    await snapshot('main-mobile','full',true);
    await page.setViewportSize({width:900,height:650});
    const panel=page.locator('#panel-toggle');
    if(await panel.getAttribute('aria-expanded')==='true') await panel.click();
    await camera(-0.95,6.70,7.2,19.92,42,159);
    await snapshot('north-lawn-arches','full',true);
    const ground=foot.ground_probes.map(p=>({name:p.label,xy:p.world,expected:p.blocked?'building':null}));
    results.ground_probes=await page.evaluate(queries=>{
      const s=window.__SHANGHAI_APP__.scene;return queries.map(q=>({...q,actual:s.collisionAt(...q.xy)}));
    },ground);
    for(const p of results.ground_probes)assert.equal(p.actual,p.expected,p.name);
    await camera(-0.95,-8.5,17.2,20.07,40,-12);
    await snapshot('nine-dormers','full',true);
    await camera(48.0,16.5,13.8,19.74,43,148);
    await snapshot('pavilion-and-gallery','full',true);
    await camera(0,0,0,15.45,32,0);
    await snapshot('distant','distant',false);

    async function chooseFromMap(searchText, placeId) {
      const toggle=page.locator('#panel-toggle');
      if(await toggle.getAttribute('aria-expanded')==='false') await toggle.click();
      await page.locator('#place-search').fill(searchText);
      await page.locator('#place-list button[data-place="'+placeId+'"]').click();
      await page.waitForFunction(target=>{
        const scene=window.__SHANGHAI_APP__?.scene;
        return new URLSearchParams(location.hash.slice(1)).get('landmark')===target &&
          scene && !scene.map.isMoving() && scene.getLandmarkAssetState(target)?.visible;
      },placeId,{polling:500,timeout:180000});
    }

    const oldStates=JSON.parse(fs.readFileSync(process.env.QA_OLD_OWNER_STATES)).stages[0];
    assert.equal(oldStates.cityCount,165);assert.equal(oldStates.source??'d2dc605e-5be1-4b23-89d9-bcd2c0aebdc1',row.source_feature_ids.building[0]);
    results.restoration=[];results.priorOwnerWitness=sha(fs.readFileSync(process.env.QA_OLD_OWNER_STATES));
    const other='xuhui-shanghai-american-school-main';
    for(const variant of ['far','near']){
      if(variant==='near')await camera(0,0,0,18.52,42,159);
      await chooseFromMap('美童公学',other);
      await page.waitForFunction(target=>{
       const scene=window.__SHANGHAI_APP__.scene,c=scene.getCandidateIntegrationState();
       return !scene.getLandmarkAssetState(target)?.visible&&!c.displayClips.some(v=>v.id===target);
      },id,{polling:500,timeout:90000});
      const departure=await page.evaluate(({id,source})=>{
       const scene=window.__SHANGHAI_APP__.scene,c=scene.getCandidateIntegrationState(),stream=scene.getStreamingState();
       return {hash:location.hash,center:scene.map.getCenter(),visible:!!scene.getLandmarkAssetState(id)?.visible,
        native:stream.active.filter(v=>v.visible).map(v=>v.id),targetClips:c.displayClips.filter(v=>v.id===id),
        rawVectorState:scene.map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:source})};
      },{id,source:row.source_feature_ids.building[0]});
      const old=oldStates.states.find(q=>q.phase==='left-'+variant);
      assert.equal(departure.visible,false);assert.deepEqual(departure.targetClips,[]);assert.ok(!departure.rawVectorState.candidateModel);
      assert.deepEqual(departure.rawVectorState,old.rawVector);
      results.restoration.push({variant,departure,oldVector:old.rawVector});results.departure=departure;save();
      await chooseFromMap('东一号楼',id);
      if(variant==='far'){
        await camera(0,0,0,15.45,32,0);
        await snapshot('far-return-from-school','distant',false);
      }else{
        await camera(0,0,0,18.52,42,159);
        await snapshot('main-return-from-school','full',true);
      }
      results.restoration.at(-1).returned={view:results.views.at(-1).view,variant:results.views.at(-1).asset.variant,
        verified:results.views.at(-1).asset.verifiedAsset,sourceState:results.views.at(-1).source_state,clipOwner:results.views.at(-1).clip.owner};
      save();
    }
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
          active:s.getStreamingState().detail.active.slice(0,3),ownerState:s.getCandidateIntegrationState().shader.ownerScopedSources.filter(r=>r.feature_local_ids.includes(2076))};
      },id).catch(e=>({inspection_error:String(e)}));
    }
    throw error;
  }
  finally{await browser.close();results.browser_closed=true;results.finished_utc=new Date().toISOString();save();}
}
run().catch(err=>{console.error(err);process.exitCode=1;});
