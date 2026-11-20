/* Look at the native hospital frontage in the actual immediately preceding scene. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');
const id='huangpu-renji-hospital-ward-entrance';
const sha=data=>createHash('sha256').update(data).digest('hex');
const [cameraFile,frozen,folder]=process.argv.slice(2);
const camera=JSON.parse(fs.readFileSync(cameraFile));
const source=JSON.parse(fs.readFileSync(path.join(__dirname,'../../../source/precise',id,'footprint-review.json')));
const base=process.env.MODEL_BASE_URL;
const tile=source.near_groups[0];
const root='assets/city-detail/macros/'+source.macro_id+'/';
const meta='data/candidate-city-integrations.json';
const local=fs.readFileSync(path.join(frozen,meta));
const old=JSON.parse(local);assert.equal(old.resulting_city_count,123);
assert.ok(!old.models.some(r=>r.id===id));assert.ok(!old.models.some(r=>r.owner?.macro_id===source.macro_id&&r.owner.feature_local_id===1977));
assert.equal(camera.model_id,id);assert.deepEqual(camera.viewport,[900,650]);
const result={case:'original native frontage and neighbouring owners before registration',model_id:id,
  previous_url:base,previous_count:123,source_id:1977,camera_sha256:sha(fs.readFileSync(cameraFile)),
  script_sha256:sha(fs.readFileSync(__filename)),camera_from_124:camera,started:new Date().toISOString(),page_errors:[],http_errors:[]};
const file=path.join(folder,'previous-native-desktop.json');
fs.mkdirSync(folder,{recursive:true});assert.ok(!fs.existsSync(file));
const dump=()=>fs.writeFileSync(file,JSON.stringify(result,null,2)+'\n');
(async()=>{
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  let page;
  try{
    page=await browser.newPage({viewport:{width:900,height:650},ignoreHTTPSErrors:true});
    page.setDefaultTimeout(300000);result.chromium=browser.version();
    const seen=new Set();page.on('response',r=>{const u=new URL(r.url());if(u.origin===new URL(base).origin&&u.protocol===new URL(base).protocol){if(r.status()>=400)result.http_errors.push([u.pathname,r.status()]);else seen.add(u.pathname.slice(1));}});
    page.on('pageerror',e=>result.page_errors.push(String(e)));
    await page.goto(new URL('index.html',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.map),null,{timeout:300000});
    const c=await page.request.get(new URL(meta,base).href);assert.equal(c.status(),200);
    const data=await c.body();assert.equal(sha(data),sha(local));result.catalog_sha256=sha(data);
    const pose={center:camera.center,bearing:camera.bearing,pitch:camera.pitch,zoom:camera.zoom,elevation:camera.elevation,padding:camera.padding};
    const jump=()=>page.evaluate(p=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(p);s.loadLandmarks();s.refreshBuildingBeacons();},pose);
    await jump();
    await page.waitForFunction(()=>{
      const s=window.__SHANGHAI_APP__.scene,d=s.getStreamingState().detail;
      return d.available>0||d.parents>0||performance.getEntriesByType('resource').some(r=>r.name.endsWith('/assets/city/manifest.json'));
    },null,{timeout:300000,polling:500});
    result.initial_stream=await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene,d=s.getStreamingState().detail;return {parents:d.parents,available:d.available};});
    if(!result.initial_stream.parents&&!result.initial_stream.available){
      result.real_manifest_retry=await page.evaluate(async()=>{const s=window.__SHANGHAI_APP__.scene,z=await s.setCityManifest('assets/city-detail/manifest.json');return {fallback:Boolean(z.fallback),error:z.error||null};});
      assert.equal(result.real_manifest_retry.fallback,false);await jump();
    }
    const ready=await page.request.get(new URL(root+'READY.json',base).href);assert.equal(ready.status(),200);
    const readyData=await ready.body();assert.equal(sha(readyData),source.frozen_bindings['READY.json'].sha256);
    const group=JSON.parse(readyData).near.find(r=>r.file===tile.file);
    assert.deepEqual(group.featureLocalIds,tile.ids);const fullId=source.macro_id+'/'+group.id;
    await page.waitForFunction(g=>window.__SHANGHAI_APP__.scene.getStreamingState().detail.active.some(t=>t.id===g),fullId,{polling:1000,timeout:300000});
    await page.waitForFunction(p=>{const m=window.__SHANGHAI_APP__.scene.map,c=m.getCenter();return !m.isMoving()&&Math.abs(c.lng-p[0])<1e-6&&Math.abs(c.lat-p[1])<1e-6;},camera.center,{timeout:120000});
    result.state=await page.evaluate(({k,key})=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,r=s.getCandidateIntegrationState();return {pose:{center:m.getCenter().toArray(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),padding:m.getPadding()},native_group:s.getStreamingState().detail.active.find(x=>x.id===key),candidate_clip:r.clips.find(c=>c.id===k)||null,corresponding_asset:s.getLandmarkAssetState(k)||null,lost_context:m.painter.context.gl.isContextLost()};},{k:id,key:fullId});
    assert.equal(result.state.candidate_clip,null);
    const missing=result.state.corresponding_asset;
    assert.ok(!missing||(!missing.anchor&&!missing.verifiedAsset&&!missing.visible&&!missing.cityIntegration&&missing.triangles===0));
    assert.equal(result.state.lost_context,false);
    for(const k of ['bearing','pitch','zoom'])assert.ok(Math.abs(result.state.pose[k]-camera[k])<.001,k);
    result.source_responses=[];
    for(const suffix of ['far.glb',tile.file]){
      const file=root+suffix;assert.ok(seen.has(file),'Native stream response '+file);
      const response=await page.request.get(new URL(file,base).href),bytes=await response.body();
      assert.equal(response.status(),200);assert.equal(sha(bytes),source.frozen_bindings[suffix].sha256);result.source_responses.push({file,bytes:bytes.length,sha256:sha(bytes)});
    }
    const png=await page.screenshot({path:path.join(folder,'previous-native-desktop.png'),timeout:300000});
    result.screenshot={file:'previous-native-desktop.png',sha256:sha(png),bytes:png.length};
    assert.deepEqual(result.page_errors,[]);assert.deepEqual(result.http_errors,[]);result.completed=true;
  }catch(e){result.failure=String(e.stack);throw e;}finally{await browser.close();result.browser_closed=true;result.finished=new Date().toISOString();dump();}
})().catch(e=>{console.error(e);process.exitCode=1});
