/* Complete the touch transition and downloads after the dense screenshot timed out. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto'),{chromium}=require('playwright');
const project=process.env.SHANGHAI_PROJECT_ROOT||path.resolve(__dirname,'../../..');
const out=process.env.QA_OUTPUT_DIR||__dirname,base=process.env.MODEL_BASE_URL||'http://127.0.0.1:8784/';
const sha=b=>createHash('sha256').update(b).digest('hex'),id='huangpu-wing-on-skybridges',previous='huangpu-old-wing-on-company';
const bytes=fs.readFileSync(path.join(project,'data/candidate-city-integrations.json')),catalog=JSON.parse(bytes);
const row=catalog.models.find(r=>r.id===id),manifest=JSON.parse(fs.readFileSync(path.join(project,row.candidate_manifest)));
const report={started:new Date().toISOString(),base,model:id,catalogSha256:sha(bytes),scriptSha256:sha(fs.readFileSync(__filename)),completed:false,downloads:[],errors:[],httpErrors:[],steps:[]};
const file=path.join(out,'touch-return.json'),save=()=>fs.writeFileSync(file,JSON.stringify(report,null,2)+'\n');
const step=s=>{console.log(s);report.steps.push(s);save();};
(async()=>{
  fs.mkdirSync(out,{recursive:true});assert(!fs.existsSync(file));assert.equal(catalog.resulting_city_count,87);
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  report.browser=browser.version();const page=await browser.newPage({viewport:{width:320,height:568},hasTouch:true,ignoreHTTPSErrors:true});
  page.on('pageerror',e=>report.errors.push(e.message));page.on('console',m=>{if(m.type()==='error')report.errors.push(m.text())});
  page.on('response',r=>{if(r.status()>=400)report.httpErrors.push([r.status(),r.url()])});
  try {
    step('Download all four delivery files');
    for(const [role,r] of Object.entries(manifest.assets)){
      const file=path.posix.join(path.posix.dirname(row.candidate_manifest),r.file);
      const response=await page.request.get(new URL(file,base).href),b=await response.body();
      assert.equal(response.status(),200);assert.equal(sha(b),r.sha256);assert.equal(b.length,r.bytes);
      report.downloads.push({role,file,bytes:b.length,sha256:sha(b)});
    }
    step('Open another landmark at 320 × 568');
    await page.goto(base+'index.html#landmark='+previous+'&mode=overview',{waitUntil:'domcontentloaded',timeout:120000});
    await page.waitForFunction(previous=>window.__SHANGHAI_APP__?.scene&&new URLSearchParams(location.hash.slice(1)).get('landmark')===previous,previous,{timeout:240000});
    await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;m.setMaxBounds(null);m.setCenterClampedToGround(true);
      m.jumpTo({center:[121.45,31.2],zoom:8,bearing:0,pitch:0,elevation:0,padding:{left:0,right:0,top:0,bottom:0}});s.refreshBuildingBeacons()});
    step('Check all live targets and tap the bridge label');
    await page.waitForFunction(()=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState();return s.map.getZoom()===8&&b.viewportLabelCount===87&&!b.overlapFallbackCount&&b.sourceIds.every(i=>s.map.isSourceLoaded(i))},null,{timeout:240000,polling:600});
    report.dense=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState(),p=b.labelPositions;return {hash:location.hash,viewport:[innerWidth,innerHeight],count:p.length,correct:p.filter(q=>s.pickBuildingBeacon(q)===q.id).length,overlapFallback:b.overlapFallbackCount,target:p.find(q=>q.id===id)}},id);
    assert.deepEqual(report.dense.viewport,[320,568]);assert.equal(report.dense.correct,87);assert.equal(report.dense.target.number,87);
    await page.touchscreen.tap(report.dense.target.x,report.dense.target.y);
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id,{timeout:120000});
    step('Check the selected full bridge in the renderer');
    await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene,r=s.getLandmarkAssetState(id);return r.status==='loaded'&&r.variant==='full'&&r.visible&&s.getCandidateIntegrationState().active.some(x=>x.id===id)},id,{timeout:240000,polling:600});
    report.selected=await page.evaluate(id=>{const a=window.__SHANGHAI_APP__,s=a.scene,r=s.getLandmarkAssetState(id);return {hash:location.hash,title:document.querySelector('#location-name').textContent,mode:a.mode,viewport:[innerWidth,innerHeight],walkDisabled:document.querySelector('#walk-mode').disabled,visible:r.visible,variant:r.variant,sha256:r.verifiedAsset.sha256,bytes:r.verifiedAsset.bytes,triangles:r.triangles,zoom:s.map.getZoom(),contextLost:s.map.painter.context.gl.isContextLost()}},id);
    assert.equal(report.selected.title,row.name);assert.equal(report.selected.mode,'overview');assert(report.selected.walkDisabled);assert(!report.selected.contextLost);
    for(const k of ['sha256','bytes','triangles'])assert.equal(report.selected[k],row.assets.web[k]);
    assert.deepEqual(report.errors,[]);assert.deepEqual(report.httpErrors,[]);report.completed=true;
  } catch(e) {report.failure=String(e.stack||e);throw e;}
  finally {await browser.close();report.browserClosed=true;report.finished=new Date().toISOString();save();}
})().catch(error=>{console.error(error);process.exitCode=1});
