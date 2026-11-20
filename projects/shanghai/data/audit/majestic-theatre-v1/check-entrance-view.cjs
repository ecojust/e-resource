/* Center the street entrance to the right of the production location card. */
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const {createHash}=require('node:crypto'), {chromium}=require('playwright');
const project=process.env.SHANGHAI_PROJECT_ROOT||path.resolve(__dirname,'../../..');
const out=process.env.QA_OUTPUT_DIR||__dirname,base=process.env.MODEL_BASE_URL||'http://127.0.0.1:8784/';
const id='jingan-majestic-theatre', macro='14-13719-6694', sha=b=>createHash('sha256').update(b).digest('hex');
const bytes=fs.readFileSync(path.join(project,'data/candidate-city-integrations.json')),cat=JSON.parse(bytes),row=cat.models.find(r=>r.id===id);
const camera={center:[121.4513915,31.2312208],zoom:20.35,pitch:70,bearing:12,elevation:9.4,padding:{left:400,right:24,top:16,bottom:120}};
const report={model:id,base,started:new Date().toISOString(),camera,count:cat.resulting_city_count,catalogSha256:sha(bytes),scriptSha256:sha(fs.readFileSync(__filename)),completed:false,errors:[]};
async function run(){
  fs.mkdirSync(out,{recursive:true});const f=path.join(out,'entrance-map.json');assert(!fs.existsSync(f));assert(row);
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  report.browser=browser.version();
  const page=await browser.newPage({viewport:{width:960,height:720},ignoreHTTPSErrors:true});
  page.on('pageerror',e=>report.errors.push(e.message));
  try{
    await page.goto(base+'index.html#landmark='+id+'&mode=overview',{waitUntil:'domcontentloaded',timeout:120000});
    await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene,null,{timeout:240000});
    const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
    await page.waitForFunction(({id,macro})=>{const s=window.__SHANGHAI_APP__.scene,m=s.getLandmarkAssetState(id),c=s.getCandidateIntegrationState();
      const g=c.shader.ownerScopedSources.find(r=>r.macro_id===macro&&r.clip_feature_local_ids.includes(360));
      return m.visible&&m.variant==='full'&&m.status==='loaded'&&g&&s.getStreamingState().detail.active.some(r=>r.id===g.id)&&!s.map.isMoving();},{id,macro},{timeout:360000,polling:800});
    report.state=await page.evaluate(({id,macro})=>{const s=window.__SHANGHAI_APP__.scene,m=s.getLandmarkAssetState(id),c=s.getCandidateIntegrationState(),box=document.querySelector('#location-card').getBoundingClientRect();
      return {hash:location.hash,sha256:m.verifiedAsset.sha256,bytes:m.verifiedAsset.bytes,triangles:m.triangles,card:[box.left,box.top,box.right,box.bottom],source:c.shader.ownerScopedSources.find(g=>g.macro_id===macro&&g.clip_feature_local_ids.includes(360)),lost:s.map.painter.context.gl.isContextLost()};},{id,macro});
    for(const k of ['sha256','bytes','triangles'])assert.equal(report.state[k],row.assets.web[k]);
    assert(!report.state.lost);assert.deepEqual(report.state.source.clip_feature_local_ids,[360]);
    const name='map-entrance-doors.png',b=await page.screenshot({path:path.join(out,name),timeout:180000});
    report.image={name,sha256:sha(b),bytes:b.length};
    // Save the actual 320-pixel map framebuffer immediately after paint. This
    // preserves the labels while avoiding a second browser compositor capture.
    try {
      await page.setViewportSize({width:320,height:568});
      await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;m.setMaxBounds(null);m.setCenterClampedToGround(true);
        m.jumpTo({center:[121.45,31.2],zoom:8,pitch:0,bearing:0,elevation:0,padding:{left:0,right:0,top:0,bottom:0}});s.refreshBuildingBeacons();});
      await page.waitForFunction(()=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState();
        return b.viewportLabelCount===90&&b.overlapFallbackCount===0&&b.sourceIds.every(i=>s.map.isSourceLoaded(i));},null,{timeout:120000,polling:600});
      const capture=await page.evaluate(()=>new Promise(done=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;
        m.once('render',()=>{const b=s.getBuildingBeaconState(),p=b.labelPositions;
          done({image:m.getCanvas().toDataURL('image/png'),pixelSize:[m.getCanvas().width,m.getCanvas().height],count:p.length,allHit:p.every(x=>s.pickBuildingBeacon(x)===x.id)});});m.triggerRepaint();}));
      assert(capture.allHit&&capture.count===90);
      const canvas=Buffer.from(capture.image.split(',')[1],'base64'),file='map-city-labels-canvas.png';
      assert.equal(canvas.readUInt32BE(16),320);assert.equal(canvas.readUInt32BE(20),568);assert(canvas.length>5000);
      fs.writeFileSync(path.join(out,file),canvas);
      report.mapCanvas={file,sha256:sha(canvas),bytes:canvas.length,count:capture.count,allHit:capture.allHit,pixelSize:capture.pixelSize};
    } catch(error) { report.mapCanvasFailure=String(error); }
    assert.deepEqual(report.errors,[]);report.completed=true;
  }catch(e){report.failure=String(e.stack||e);throw e;}finally{await browser.close();report.finished=new Date().toISOString();fs.writeFileSync(f,JSON.stringify(report,null,2)+'\n');}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
