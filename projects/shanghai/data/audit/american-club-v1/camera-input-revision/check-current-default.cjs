// Inspect the actual desktop default after the two other buildings' cameras changed.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const id='huangpu-american-club';
const project=process.env.SHANGHAI_PROJECT_ROOT||path.resolve(__dirname,'../../../..');
const base=process.env.MODEL_BASE_URL||'http://127.0.0.1:14068/';
const out=process.env.QA_OUTPUT_DIR||__dirname;
const sha=data=>createHash('sha256').update(data).digest('hex');
const local=name=>fs.readFileSync(path.join(project,name));
const read=name=>JSON.parse(local(name));
const catalogName='data/candidate-city-integrations.json';
const catalog=read(catalogName),row=catalog.models.find(x=>x.id===id);
const manifest=read(row.candidate_manifest);
const fixed=read('source/precise/'+id+'/footprint-review.json'),group=fixed.near_groups[0];
const result={id,base,started:new Date().toISOString(),script_sha256:sha(fs.readFileSync(__filename)),
              expected_city_count:114,passed:false,errors:[],assets:[],warnings:[]};
async function run(){
  assert.equal(catalog.resulting_city_count,114);assert.equal(row.owner.feature_local_id,1488);
  fs.mkdirSync(out,{recursive:true});
  const report=path.join(out,'current-default-browser.json');assert.ok(!fs.existsSync(report),'Use fresh results');
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,
    args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  try{
    const page=await browser.newPage({viewport:{width:1000,height:700},hasTouch:true});
    page.setDefaultTimeout(240000);result.chromium=browser.version();
    const responses=new Set();
    page.on('response',res=>{const url=new URL(res.url());if(url.origin===new URL(base).origin&&res.status()===200)responses.add(url.pathname.slice(1));});
    page.on('pageerror',e=>result.errors.push(String(e)));
    page.on('console',m=>{if(m.type()==='error')result.errors.push(m.text());if(m.type()==='warning')result.warnings.push(m.text().slice(0,300));});
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
    assert.equal(await page.locator('.landmark-card[data-landmark]').count(),114);
    await page.locator('#district-310101 [data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').click();
    await page.waitForFunction(()=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return false;
      const d=s.getStreamingState().detail;
      return d.available>0||d.parents>0||performance.getEntriesByType('resource').some(e=>new URL(e.name).pathname.endsWith('/assets/city/manifest.json'));
    },null,{timeout:300000,polling:650});
    result.initial_detail=await page.evaluate(()=>{const d=window.__SHANGHAI_APP__.scene.getStreamingState().detail;
      return {available:d.available,parents:d.parents,coarse:performance.getEntriesByType('resource').some(e=>new URL(e.name).pathname.endsWith('/assets/city/manifest.json'))};});
    if(!result.initial_detail.parents&&!result.initial_detail.available&&result.initial_detail.coarse){
      result.detail_retry=await page.evaluate(async()=>{const r=await window.__SHANGHAI_APP__.scene.setCityManifest('assets/city-detail/manifest.json');return {fallback:Boolean(r.fallback),error:r.error||null};});
      assert.equal(result.detail_retry.fallback,false);
    }
    await page.waitForFunction(id=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s||s.map.isMoving())return false;
      const a=s.getLandmarkAssetState(id),b=s.getBuildingBeaconState(),l=b.labelPositions.find(x=>x.id===id),c=s.getCandidateIntegrationState();
      const g=c.shader.ownerScopedSources.find(x=>x.clip_feature_local_ids.includes(1488)&&x.feature_local_ids.includes(2805));
      return a?.status==='loaded'&&a.visible&&a.variant==='full'&&l&&s.pickBuildingBeacon(l)===id&&g&&s.getStreamingState().detail.active.some(x=>x.id===g.id);
    },id,{polling:700,timeout:420000});
    result.default=await page.evaluate(id=>{
      const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,b=s.getBuildingBeaconState(),c=s.getCandidateIntegrationState();
      const l=b.labelPositions.find(x=>x.id===id);
      return {mode:a.mode,id:new URLSearchParams(location.hash.slice(1)).get('landmark'),title:document.querySelector('#location-name').textContent,
        asset:s.getLandmarkAssetState(id),count:b.count,label:l,picked:s.pickBuildingBeacon(l),viewport:[innerWidth,innerHeight],
        camera:{center:m.getCenter(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},clip:c.clips.find(x=>x.id===id),
        group:c.shader.ownerScopedSources.find(x=>x.clip_feature_local_ids.includes(1488)&&x.feature_local_ids.includes(2805)),
        cap:c.sourceSections.find(x=>x.id===id),webgl_lost:m.painter.context.gl.isContextLost()};
    },id);
    const d=result.default;assert.equal(d.id,id);assert.equal(d.picked,id);assert.equal(d.count,114);assert.equal(d.mode,'overview');assert.equal(d.title,row.name);
    assert.equal(d.webgl_lost,false);assert.deepEqual(d.clip.geometry,row.replacement_geometry);assert.deepEqual(d.group.clip_feature_local_ids,[1488]);
    assert.equal(d.cap.feature_local_id,1488);assert.equal(d.asset.verifiedAsset.sha256,manifest.assets.full.sha256);assert.equal(d.asset.triangles,manifest.assets.full.triangles);
    assert.equal(d.camera.pitch,row.overviewPitch);assert.ok(Math.abs(d.camera.bearing-row.overviewBearing)<.0001);
    await page.evaluate(()=>new Promise(ok=>requestAnimationFrame(()=>requestAnimationFrame(ok))));
    const img=await page.screenshot({path:path.join(out,'current-default-desktop.png'),timeout:300000});
    result.screenshot={file:'current-default-desktop.png',bytes:img.length,sha256:sha(img)};
    const requests=[catalogName,'index.html','src/app.js','src/map-scene.js','src/building-beacons.js',row.candidate_manifest,
      path.posix.join(path.posix.dirname(row.candidate_manifest),manifest.assets.full.file),
      'assets/city-detail/macros/'+row.owner.macro_id+'/'+group.file];
    for(const name of requests){
      const seen=responses.has(name);
      if(name!==row.candidate_manifest)assert.ok(seen,'Missing scene request '+name);
      const res=await page.request.get(new URL(name,base).href);assert.equal(res.status(),200);
      const data=await res.body();const expected=name.startsWith('assets/city-detail/macros/')?group.sha256:sha(local(name));
      assert.equal(sha(data),expected);result.assets.push({file:name,sha256:expected,bytes:data.length,seen_in_scene:seen});
    }
    assert.deepEqual(result.errors,[]);result.passed=true;
  }catch(e){result.failure=String(e.stack);throw e;}
  finally{await browser.close();result.browser_closed=true;result.finished=new Date().toISOString();fs.writeFileSync(report,JSON.stringify(result,null,2)+'\n');}
}
run().catch(e=>{process.stderr.write(String(e.stack)+'\n');process.exitCode=1;});
