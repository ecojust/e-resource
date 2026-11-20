/* Compare a Bund in-place revision in independently registered predecessor and
   successor scenes, using identical, footprint-derived camera coordinates. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');

const casePath = path.resolve(process.argv[2]);
const spec = JSON.parse(fs.readFileSync(casePath));
const phase = process.argv[3];
assert.ok(['before','after'].includes(phase));
const output = path.resolve(process.env.QA_OUTPUT_DIR || path.dirname(casePath));
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:'+spec[phase+'Port']+'/';
const sha = data => createHash('sha256').update(data).digest('hex');
const reportFile = path.join(output,'main-map-'+phase+'.json');
const report = {id:spec.id,phase,base,completed:false,started:new Date().toISOString(),
  scriptSHA256:sha(fs.readFileSync(__filename)),caseSHA256:sha(fs.readFileSync(casePath)),
  downloads:[],views:[],errors:[]};
function save(){fs.writeFileSync(reportFile,JSON.stringify(report,null,2)+'\n');}

async function run(){
  fs.mkdirSync(output,{recursive:true});
  assert.ok(!fs.existsSync(reportFile),'Keep the independently observed earlier run');
  const browser = await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({viewport:{width:850,height:650}});
    page.setDefaultTimeout(120000);
    const received = new Set();
    page.on('response',response=>received.add(new URL(response.url()).pathname));
    page.on('pageerror',error=>report.errors.push(String(error)));
    for(const file of ['data/landmarks.json','data/candidate-city-integrations.json']){
      const response=await page.request.get(base+file),bytes=await response.body();
      assert.equal(response.status(),200);
      report.downloads.push({file,sha256:sha(bytes),bytes:bytes.length});
      const data=JSON.parse(bytes);
      if(file.endsWith('/landmarks.json')) report.record=data.find(row=>row.id===spec.id);
      else assert.equal(data.resulting_city_count,spec.catalogCount);
    }
    const row=report.record;
    assert.ok(row && row.web_sha256 && row.triangles);
    const route=base+'index.html#landmark='+spec.id+'&mode=overview';
    await page.goto(route,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene,null,{timeout:200000});
    const toggle=page.locator('#panel-toggle');
    if(await toggle.getAttribute('aria-expanded')==='true')await toggle.click();
    await page.waitForFunction(({id,triangles,lod})=>{
      const scene=window.__SHANGHAI_APP__.scene,state=scene.getLandmarkAssetState(id);
      return state?.visible && [triangles,lod].includes(state.triangles) && !scene.map.isMoving();
    },{id:spec.id,triangles:row.triangles,lod:row.lod_triangles},{polling:350,timeout:180000});
    const frame=()=>page.evaluate(()=>new Promise(done=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>done());m.triggerRepaint();}));
    for(const type of ['default','detail']){
      if(type==='detail')await page.evaluate(camera=>{
        const scene=window.__SHANGHAI_APP__.scene;
        scene.map.setCenterClampedToGround(false);
        scene.map.jumpTo(camera);
        scene.loadLandmarks();scene.refreshBuildingBeacons();
      },spec.camera);
      if(type==='detail')await page.waitForFunction(({id,triangles})=>{
        const scene=window.__SHANGHAI_APP__.scene,a=scene.getLandmarkAssetState(id);
        return a.visible && a.triangles===triangles && !scene.map.isMoving();
      },{id:spec.id,triangles:row.triangles},{timeout:160000,polling:300});
      await frame();await frame();
      const state=await page.evaluate(id=>{
        const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState(id);
        return {route:location.hash,asset:a,name:document.querySelector('#location-name').textContent,
          camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),bearing:m.getBearing(),
            pitch:m.getPitch(),elevation:m.getCenterElevation()},renderer:m.painter.context.gl.getParameter(m.painter.context.gl.RENDERER),
          viewport:[innerWidth,innerHeight]};
      },spec.id);
      assert.ok(state.asset.visible);
      assert.equal(state.asset.triangles,['lod','distant'].includes(state.asset.variant)?row.lod_triangles:row.triangles);
      if(type==='detail')assert.equal(state.asset.triangles,row.triangles);
      const file='main-map-'+phase+'-'+type+'.png';const png=await page.screenshot({path:path.join(output,file),timeout:240000});
      report.views.push({type,file,bytes:png.length,sha256:sha(png),state});save();
    }
    const response=await page.request.get(base+row.model),bytes=await response.body();
    assert.equal(response.status(),200);assert.equal(bytes.length,row.web_bytes);assert.equal(sha(bytes),row.web_sha256);
    assert.ok([...received].some(url=>url.endsWith('/'+row.model)),'Scene did not load registered geometry');
    report.downloads.push({file:row.model,bytes:bytes.length,sha256:sha(bytes),requestedByMap:true});
    assert.deepEqual(report.errors,[]);
    report.completed=true;report.finished=new Date().toISOString();save();
  }finally{await browser.close();}
}
run().catch(e=>{report.error=e.stack;save();console.error(e);process.exitCode=1;});
