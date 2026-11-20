// Supplement the context frames with closer, unobstructed approaches in the same 96-landmark city.
const {chromium} = require('playwright');
const {createHash} = require('node:crypto');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8951/';
const out = process.env.QA_OUTPUT_DIR || __dirname;
const id = 'changning-sun-ke-villa';
const sha = v => createHash('sha256').update(v).digest('hex');
const report = {id, base, started_utc:new Date().toISOString(), completed:false, views:[], errors:[],script_sha256:sha(fs.readFileSync(__filename))};

async function main() {
  fs.mkdirSync(out,{recursive:true});
  assert.ok(!fs.existsSync(path.join(out,'close-details.json')),'Use a fresh output directory');
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',
    args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1000,height:680},ignoreHTTPSErrors:true});
  page.setDefaultTimeout(240000);
  page.on('pageerror', e=>report.errors.push(String(e)));
  page.on('response', r=>{if(r.status()>=400)report.errors.push([r.status(),r.url()]);});
  try {
    report.browser=browser.version();
    const res=await page.request.get(new URL('data/candidate-city-integrations.json',base).href);
    const data=await res.body();assert.equal(res.status(),200);report.catalog_sha256=sha(data);
    const table=JSON.parse(data), row=table.models.at(-1);
    assert.equal(table.resulting_city_count,96); assert.equal(row.id,id);
    await page.goto(new URL('index.html#landmark='+id+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(id=>window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id)?.status==='loaded',id,{polling:800,timeout:420000});
    const panel=page.locator('#panel-toggle');
    if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
    const views=[
      ['north-portico-detail',-.24,8.5,2.75,21.52,59,207],
      ['north-portico-oblique',.70,8.6,2.60,21.22,49,222],
      ['south-arches-detail',-.30,-6.90,2.80,21.42,65,22],
    ];
    for(const [name,x,y,elevation,zoom,pitch,bearing] of views) {
      console.log('Checking',name);
      const deg=Math.PI/180, center=[row.lng+x/(6371008.8*Math.cos(row.lat*deg))/deg,row.lat+y/6371008.8/deg];
      await page.evaluate(o=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(o);s.loadLandmarks();s.refreshBuildingBeacons();},
        {center,elevation,zoom,pitch,bearing,padding:{top:0,bottom:152,left:75,right:0}});
      await page.waitForFunction(id=>{
        const s=window.__SHANGHAI_APP__.scene, a=s.getLandmarkAssetState(id);
        const group=s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.clip_feature_local_ids.includes(2445));
        return !s.map.isMoving() && a?.visible && a.variant==='full' && group && s.getStreamingState().detail.active.some(r=>r.id===group.id);
      },id,{polling:850,timeout:420000});
      await page.evaluate(()=>new Promise(done=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>{m.once('render',done);m.triggerRepaint()});m.triggerRepaint()}));
      const state=await page.evaluate(id=>{
        const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState(id);
        return {mode:window.__SHANGHAI_APP__.mode,model_sha256:a.verifiedAsset.sha256,triangles:a.triangles,center:m.getCenter(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),beacon_count:s.getBuildingBeaconState().count,
          visible_source_owners:s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.clip_feature_local_ids.includes(2445)).feature_local_ids,clipped_owner:2445,webgl_context_lost:m.painter.context.gl.isContextLost()};
      },id);
      assert.equal(state.model_sha256,row.model_geometry_sha256.web);assert.equal(state.beacon_count,96);assert.equal(state.webgl_context_lost,false);
      const file=name+'.png',img=await page.screenshot({path:path.join(out,file),timeout:180000});
      report.views.push({name,file,bytes:img.length,sha256:sha(img),...state});
      fs.writeFileSync(path.join(out,'close-details.json'),JSON.stringify(report,null,2)+'\n');
    }
    assert.deepEqual(report.errors,[]);report.completed=true;
  } catch(e){report.failure=String(e.stack);throw e;}
  finally {
    await browser.close();report.finished_utc=new Date().toISOString();
    fs.writeFileSync(path.join(out,'close-details.json'),JSON.stringify(report,null,2)+'\n');
  }
}
main().catch(e=>{console.error(e);process.exitCode=1});
