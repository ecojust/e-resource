const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

const id = 'huangpu-xiaotaoyuan-mosque-prayer-hall';
const previous = 'hongkou-jingling-church-north-front';
const base = process.env.QA_PREVIOUS_URL || 'http://127.0.0.1:24142/';
const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(__dirname,'../../../..');
const output = process.env.QA_OUTPUT_DIR || path.join(__dirname,'control');
const audit = 'data/audit/xiaotaoyuan-prayer-hall-v1';
const read = file => JSON.parse(fs.readFileSync(path.join(project,file)));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const contract = read(audit+'/final-placement-contract.json');
const source = read('source/precise/'+id+'/footprint-review.json');
const {catalog_sha256} = read(audit+'/city-24142-24143-preflight.json').results['142'];
const group = source.near_groups[0];
const macro = contract.owner.macro_id;
const owner = contract.owner.feature_local_id;
const witness = 2419;
const result = {
  base,id,script_sha256:hash(fs.readFileSync(__filename)),finished:false,
  errors:[],failed:[],files:[],started:new Date().toISOString()
};

// Match the newer release's court-arcade view including the viewport and padding.
const heading = contract.heading*Math.PI/180;
const latitude = contract.lat*Math.PI/180;
const east = 0.30*Math.sin(heading);
const north = 0.30*Math.cos(heading);
const camera = {
  center:[contract.lng+east/(6371008.8*Math.cos(latitude))*180/Math.PI,
          contract.lat+north/6371008.8*180/Math.PI],
  elevation:6.12,zoom:20.05,pitch:38,bearing:-110,padding:{top:0,bottom:145,left:92,right:0}
};

async function run() {
  fs.mkdirSync(output,{recursive:true});
  const browser = await chromium.launch({
    executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',
      '--remote-debugging-port='+(process.env.QA_CDP_PORT || '9713')]
  });
  const loaded = new Set();
  let page;
  try {
    page = await browser.newPage({viewport:{width:900,height:650},ignoreHTTPSErrors:true});
    page.on('pageerror',error=>result.errors.push(error.message));
    page.on('response',response=>{
      const url = new URL(response.url());
      if (response.status()>=400) result.failed.push({url:response.url(),status:response.status()});
      if (url.origin===new URL(base).origin && [200,206].includes(response.status())) {
        loaded.add(url.pathname.slice(1));
      }
    });
    const catalogResponse = await page.request.get(new URL('data/candidate-city-integrations.json',base).href);
    const bytes = await catalogResponse.body();
    const catalog = JSON.parse(bytes);
    assert.equal(catalogResponse.status(),200);
    assert.equal(hash(bytes),catalog_sha256);
    assert.equal(catalog.resulting_city_count,179);
    assert.ok(!catalog.models.some(row=>row.id===id));
    assert.equal(catalog.models.at(-1).id,previous);
    Object.assign(result,{before_count:catalog.resulting_city_count,catalog:hash(bytes),selected:previous});
    await page.goto(new URL('index.html#landmark='+previous+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene),null,{timeout:180000});
    await page.waitForFunction(()=>{
      const loading = document.getElementById('loading');
      return !loading || getComputedStyle(loading).visibility==='hidden' || getComputedStyle(loading).display==='none';
    },null,{timeout:180000});
    const panel = page.locator('#panel-toggle');
    if (await panel.getAttribute('aria-expanded')==='true') await panel.click();
    await page.evaluate(options=>{
      const scene = window.__SHANGHAI_APP__.scene;
      scene.map.setCenterClampedToGround(false);
      scene.map.jumpTo(options);
      scene.loadLandmarks();
      scene.refreshBuildingBeacons();
    },camera);
    result.pose = camera;
    await page.waitForFunction(({macro,owner,witness})=>{
      const scene = window.__SHANGHAI_APP__.scene;
      const group = scene.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>
        g.macro_id===macro && g.feature_local_ids.includes(owner) && g.feature_local_ids.includes(witness));
      return !scene.map.isMoving() && group && scene.getStreamingState().detail.active.some(g=>g.id===group.id)
        && !group.clip_feature_local_ids.includes(owner);
    },{macro,owner,witness},{polling:450,timeout:240000});
    result.state = await page.evaluate(({id,macro,owner,witness,uuid})=>{
      const scene = window.__SHANGHAI_APP__.scene, map = scene.map;
      const integration = scene.getCandidateIntegrationState();
      const group = integration.shader.ownerScopedSources.find(g=>
        g.macro_id===macro && g.feature_local_ids.includes(owner) && g.feature_local_ids.includes(witness));
      return {
        camera:{center:map.getCenter(),pitch:map.getPitch(),bearing:map.getBearing(),zoom:map.getZoom(),elevation:map.getCenterElevation(),padding:map.getPadding()},
        group,asset:scene.getLandmarkAssetState(id),ownClip:integration.clips.find(g=>g.id===id)||null,
        source:map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:uuid}),
        beacons:scene.getBuildingBeaconState().count,gl:map.painter.context.gl.getError()
      };
    },{id,macro,owner,witness,uuid:contract.source_feature_ids.building[0]});
    assert.equal(result.state.beacons,179);
    assert.equal(result.state.ownClip,null);
    assert.equal(result.state.gl,0);
    assert.deepEqual([...result.state.group.feature_local_ids].sort((a,b)=>a-b),[...group.ids].sort((a,b)=>a-b));
    assert.ok(!result.state.group.clip_feature_local_ids.includes(owner));
    const image = await page.screenshot({path:path.join(output,'map-before.png'),timeout:120000});
    result.image = {sha256:hash(image),bytes:image.length};
    for (const name of ['far.glb',group.file]) {
      const file = 'assets/city-detail/macros/'+macro+'/'+name;
      assert.ok(loaded.has(file),'Expected an actual map response for '+file);
      const response = await page.request.get(new URL(file,base).href);
      const bytes = await response.body(), binding = source.frozen_bindings[name];
      assert.equal(response.status(),200);
      assert.equal(hash(bytes),binding.sha256);
      assert.equal(bytes.length,binding.bytes);
      result.files.push({file,bytes:bytes.length,sha256:hash(bytes),loaded:true});
    }
    assert.deepEqual(result.errors,[]);
    assert.deepEqual(result.failed,[]);
    result.finished = true;
  } catch (error) {
    result.failure = String(error.stack);
    if (page) result.failure_state = await page.evaluate(()=>{
      const scene = window.__SHANGHAI_APP__?.scene;
      return scene ? {stream:scene.getStreamingState().detail,center:scene.map.getCenter(),route:location.hash}
        : {startup:document.body.innerText.slice(0,800)};
    }).catch(e=>({inspection_error:String(e)}));
    throw error;
  } finally {
    await browser.close();
    result.browserClosed = true;
    result.observedHttpPaths = [...loaded].sort();
    result.completed_at = new Date().toISOString();
    fs.writeFileSync(path.join(output,'control.json'),JSON.stringify(result,null,2)+'\n');
  }
}
run().catch(error=>{console.error(error);process.exitCode=1;});
