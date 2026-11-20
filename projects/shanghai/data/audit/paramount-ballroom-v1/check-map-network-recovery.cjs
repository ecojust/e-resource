/* Exercise the cold-start city manifest retry in the unmodified production map.
 * MODEL_BASE_URL must serve the frozen 118-landmark site. The proxy streams
 * 32 bytes from the real first detail response, then waits for the app timeout. */
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');

const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:9118/';
const out = process.env.QA_OUTPUT_DIR || __dirname;
const hash = value => createHash('sha256').update(value).digest('hex');
const id = 'jingan-paramount-ballroom';
const macro = '14-13718-6694';
const group = macro + '/' + macro + '-2_2-s1-s1';
const detail = '/assets/city-detail/manifest.json';
const coarse = '/assets/city/manifest.json';
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

async function run() {
  fs.mkdirSync(out, {recursive:true});
  const read = async relative => {
    const response = await fetch(new URL(relative, base));
    assert.equal(response.status, 200, relative);
    return Buffer.from(await response.arrayBuffer());
  };
  const [catalog, app, scene, prior, current] = await Promise.all([
    'data/candidate-city-integrations.json','src/app.js','src/map-scene.js',coarse,detail
  ].map(read));
  const expected = JSON.parse(catalog);
  assert.equal(expected.resulting_city_count,118);
  assert.equal(expected.models.at(-1).id,id);
  const payloads = {[coarse]:prior,[detail]:current};
  const start = Date.now();
  const events = [];
  const ms = () => Date.now()-start;
  let retryHeld, detailAttempts=0;
  const proxy = http.createServer((req,res) => {
    const route = new URL(req.url,base).pathname;
    if (!(route in payloads)) {
      const target = http.request(new URL(req.url,base),{method:req.method,headers:{...req.headers,host:new URL(base).host}},up => {
        res.writeHead(up.statusCode,up.headers);
        up.pipe(res);
      });
      target.on('error',()=>res.destroy());
      res.on('close',()=>target.destroy());
      req.pipe(target);
      return;
    }
    const bytes=payloads[route];
    const receipt={route,started_ms:ms(),source_bytes:bytes.length,source_sha256:hash(bytes),sent_bytes:0};
    events.push(receipt);
    res.writeHead(200,{'Content-Type':'application/json','Content-Length':bytes.length,'Cache-Control':'no-store'});
    res.on('close',()=>{receipt.closed_ms=ms();});
    const deliver=()=>{receipt.sent_bytes=bytes.length;receipt.complete_ms=ms();res.end(bytes);};
    if(route===detail && ++detailAttempts===1) {
      receipt.sent_bytes=32;
      res.write(bytes.subarray(0,32));
    } else if(route===detail) {
      retryHeld=deliver;
    } else {
      deliver();
    }
  });
  await new Promise(resolve=>proxy.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',
    args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const output={model:id,started:new Date(start).toISOString(),browser:browser.version(),catalog_sha256:hash(catalog),
    app_sha256:hash(app),map_scene_sha256:hash(scene),driver_sha256:hash(fs.readFileSync(__filename)),requests:events,completed:false,errors:[],messages:[]};
  const save=()=>fs.writeFileSync(path.join(out,'cold-map-directory-recovery.json'),JSON.stringify(output,null,2)+'\n');
  try {
    const page=await browser.newPage({viewport:{width:640,height:580},ignoreHTTPSErrors:true});
    let documentLoads=0;
    page.on('request',r=>{if(r.isNavigationRequest()&&r.frame()===page.mainFrame())documentLoads++;});
    page.on('pageerror',e=>output.errors.push(e.message));
    page.on('console',m=>{if(m.text().includes('建筑目录'))output.messages.push(m.text());});
    await page.goto('http://127.0.0.1:'+proxy.address().port+'/index.html#landmark='+id+'&mode=overview',{waitUntil:'domcontentloaded'});
    save();
    const fetchState=async()=>page.evaluate(({id,macro,group})=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return null;
      const t=s.getStreamingState(),b=s.getBuildingBeaconState(),a=s.getLandmarkAssetState(id);
      return {document_origin:performance.timeOrigin,route:location.hash,
        macro:t.active.find(c=>c.id===macro&&c.visible)||null,detail:t.detail.active.find(c=>c.id===group)||null,
        beacons:b.count,candidate:a&&{visible:a.visible,status:a.status,variant:a.variant},context_lost:s.map.getCanvas().getContext('webgl2')?.isContextLost()};
    },{id,macro,group});
    const rows=[prior,current].map(data=>JSON.parse(data).tiles.find(t=>t.id===macro));
    async function waitFor(check) {
      const end=Date.now()+270000;
      let seen;
      while(Date.now()<end) {
        seen=await fetchState();
        if(seen && check(seen))return seen;
        await pause(350);
      }
      throw Error('Timed out waiting for a streamed city state. Last state '+JSON.stringify(seen));
    }
    output.coarse=await waitFor(s=>retryHeld && s.macro?.sizeBytes===rows[0].size_bytes);
    assert.equal(output.coarse.beacons,118);assert.ok(!output.coarse.detail);save();console.log('[cold] fallback city shown before releasing the full directory');
    retryHeld();
    output.automatic=await waitFor(s=>s.macro?.sizeBytes===rows[1].size_bytes && s.candidate?.visible);
    assert.equal(output.coarse.document_origin,output.automatic.document_origin);save();
    console.log('[cold] detailed macro replaced fallback on the original page');
    if(!output.automatic.detail){
      const target=expected.models.find(model=>model.id===id);
      const camera={center:[target.lng,target.lat],zoom:19.1,pitch:48,bearing:target.heading};
      await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.jumpTo(c);s.loadLandmarks();},camera);
      output.camera_after_automatic_recovery=camera;
    }
    output.detailed=await waitFor(s=>s.macro?.sizeBytes===rows[1].size_bytes && s.detail && s.candidate?.visible);save();
    output.document_requests=documentLoads;
    assert.equal(documentLoads,1);assert.equal(output.coarse.document_origin,output.detailed.document_origin);
    assert.equal(output.detailed.beacons,118);assert.equal(output.detailed.context_lost,false);
    assert.equal(output.detailed.candidate.status,'loaded');assert.equal(output.errors.length,0);
    assert.deepEqual(events.map(x=>x.route),[detail,coarse,detail]);assert.equal(events[0].sent_bytes,32);
    assert.ok(events[1].started_ms-events[0].started_ms>=24500);
    const screenshot=await page.screenshot({path:path.join(out,'cold-map-directory-restored.png'),timeout:300000});
    output.image={file:'cold-map-directory-restored.png',bytes:screenshot.length,sha256:hash(screenshot)};
    output.completed=true;
  } catch(error) {output.error=String(error);throw error;}
  finally {await browser.close();proxy.closeAllConnections();proxy.close();output.finished=new Date().toISOString();save();}
}
run().catch(error=>{console.error(error);process.exitCode=1;});
