/* Compare a Bund in-place revision in independently registered predecessor and
   successor scenes, using identical, footprint-derived camera coordinates. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');
const screens=[[1000,720],[390,844]];
const onlyScreen=process.env.QA_VIEWPORT;
assert.ok(!onlyScreen || ['desktop','mobile'].includes(onlyScreen));
const dimensions=onlyScreen ? screens.filter(([width])=>(width===1000?'desktop':'mobile')===onlyScreen) : screens;
const viewKind=process.env.QA_VIEW_KIND;
assert.ok(!viewKind || ['default','detail'].includes(viewKind));
const views=viewKind ? [viewKind] : ['default','detail'];

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
  const browser = await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-features=BackForwardCache','--renderer-process-limit=2']});
  try {
    const page = await browser.newPage({viewport:{width:1000,height:720},ignoreHTTPSErrors:true});
    const cdp=await page.context().newCDPSession(page);
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
    assert.equal(row.web_sha256,spec[phase].web_sha256);
    assert.equal(row.triangles,spec[phase].triangles);
    assert.equal(row.model,spec[phase].web);
    const listed=report.downloads.find(r=>r.file==='data/candidate-city-integrations.json');
    assert.equal(listed.sha256,spec.catalog_sha256);
    assert.ok(row && row.web_sha256 && row.triangles);
    const directory=base+'landmarks.html';
    for(const [width,height] of dimensions){
    await page.setViewportSize({width,height});
    if(process.env.QA_OVERVIEW_ENTRY==='1'){
      const destination=base+'index.html#landmark='+spec.id+'&mode=overview';
      report.entry={type:'public overview deep link',href:destination};
      await page.goto(destination,{waitUntil:'domcontentloaded'});
      await page.waitForFunction(id=>window.__SHANGHAI_APP__?.scene?.map && new URLSearchParams(location.hash.slice(1)).get('landmark')===id && document.querySelector('#overview-mode')?.getAttribute('aria-pressed')==='true',spec.id,{polling:500,timeout:400000});
    }else{
    await page.goto(directory,{waitUntil:'domcontentloaded'});
    const link=page.locator('[data-landmark="'+spec.id+'"] .card-foot a');
    assert.equal(await link.getAttribute('href'),'index.html#landmark='+spec.id+'&mode=walk');
    await link.click();
    await page.waitForFunction(id=>window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id)?.visible &&
      document.querySelector('#loading')?.classList.contains('loaded')&&getComputedStyle(document.querySelector('#loading')).visibility==='hidden',spec.id,{polling:500,timeout:540000});
    await page.locator('#overview-mode').click();
    await page.waitForFunction(()=>document.querySelector('#overview-mode')?.getAttribute('aria-pressed')==='true');
    }
    await page.waitForFunction(()=>{const intro=document.querySelector('#loading');return !intro || (intro.classList.contains('loaded') && getComputedStyle(intro).visibility==='hidden');},{},{polling:400,timeout:350000});
    const toggle=page.locator('#panel-toggle');
    if(width===1000 && await toggle.getAttribute('aria-expanded')==='true')await toggle.click();
    await page.waitForFunction(({id,triangles,lod})=>{
      const scene=window.__SHANGHAI_APP__.scene,state=scene.getLandmarkAssetState(id);
      return state?.visible && [triangles,lod].includes(state.triangles) && !scene.map.isMoving();
    },{id:spec.id,triangles:row.triangles,lod:row.lod_triangles},{polling:350,timeout:180000});
    const frame=()=>page.evaluate(()=>new Promise(done=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>done());m.triggerRepaint();}));
    for(const type of views){
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
          viewport:[innerWidth,innerHeight],introVisibility:document.querySelector('#loading') ? getComputedStyle(document.querySelector('#loading')).visibility : 'absent'};
      },spec.id);
      const active=new URLSearchParams(state.route.slice(1));
      assert.equal(active.get('landmark'),spec.id);assert.equal(active.get('mode'),'overview');
      assert.equal(state.name,row.name);assert.ok(state.asset.visible);
      assert.equal(state.asset.triangles,['lod','distant'].includes(state.asset.variant)?row.lod_triangles:row.triangles);
      if(type==='detail')assert.equal(state.asset.triangles,row.triangles);
      const file='main-map-'+phase+'-'+(width===1000?'desktop':'mobile')+'-'+type+'.png';
      const observed={type,device:width===1000?'desktop':'mobile',file,state};
      report.views.push(observed);save();
      const screen=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false,optimizeForSpeed:true});
      const png=Buffer.from(screen.data,'base64');fs.writeFileSync(path.join(output,file),png);
      observed.bytes=png.length;observed.sha256=sha(png);save();
    }
    }
    const response=await page.request.get(base+row.model),bytes=await response.body();
    assert.equal(response.status(),200);assert.equal(bytes.length,row.web_bytes);assert.equal(sha(bytes),row.web_sha256);
    assert.ok([...received].some(url=>url.endsWith('/'+row.model)),'Scene did not load registered geometry');
    report.downloads.push({file:row.model,bytes:bytes.length,sha256:sha(bytes),requestedByMap:true});
    for(const name of ['src/app.js','src/map-scene.js','src/building-beacons.js']){
      const resp=await page.request.get(base+name),data=await resp.body();
      assert.equal(resp.status(),200);assert.ok([...received].some(p=>p.endsWith('/'+name)));
      report.downloads.push({file:name,bytes:data.length,sha256:sha(data),requestedByMap:true});
    }
    if(phase==='after'){
      const resp=await page.request.get(base+spec.sourceFrame),data=await resp.body();
      assert.equal(resp.status(),200);assert.equal(sha(data),spec.sourceFrameSHA256);
      report.downloads.push({file:spec.sourceFrame,bytes:data.length,sha256:sha(data)});
    }
    assert.deepEqual(report.errors,[]);
    report.completed=true;report.finished=new Date().toISOString();save();
  }finally{await browser.close();}
}
run().catch(e=>{report.error=e.stack;save();console.error(e);process.exitCode=1;});
