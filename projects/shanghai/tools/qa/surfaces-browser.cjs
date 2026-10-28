/* Run with Playwright installed; local server must serve the project at :8000. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
  const out=path.resolve('data/audit/surfaces-v1');
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[],httpErrors=[],checks=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)httpErrors.push({url:r.url(),status:r.status()});});
  const ready=async id=>{
    await page.waitForFunction(id=>window.surfaceViewer?.getState().status==='ready'&&window.surfaceViewer.getState().selection===id,id,{timeout:90000});
    await page.waitForTimeout(150);
    return page.evaluate(()=>window.surfaceViewer.getState());
  };
  await page.goto('http://127.0.0.1:8000/surfaces.html#district=310101');
  let state=await ready('310101');
  assert.equal(state.visibleDistricts.length,1); assert.equal(state.geometries,2);
  checks.push({check:'initial district hash, actual render',state});
  const options=await page.locator('#district option').count();assert.equal(options,17);
  const links=await page.locator('#downloads a').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')));
  assert.equal(links.length,3);
  for(const url of links){const res=await page.request.get('http://127.0.0.1:8000/'+url);assert.equal(res.status(),200);}
  checks.push({check:'16 districts plus all, three working asset downloads',links});
  await page.click('#top');await page.screenshot({path:path.join(out,'huangpu.png')});
  const before=state.triangles;
  await page.uncheck('#show-ground');state=await page.evaluate(()=>window.surfaceViewer.getState());
  assert(state.triangles>0 && state.triangles<before);
  await page.uncheck('#show-water');state=await page.evaluate(()=>window.surfaceViewer.getState());assert.equal(state.triangles,0);
  await page.check('#show-ground');await page.check('#show-water');
  checks.push({check:'ground and water independently hidden, both hidden draws zero triangles'});
  const manifest=await (await page.request.get('http://127.0.0.1:8000/assets/surfaces/manifest.json')).json();
  for(const record of manifest.districts){
    await page.selectOption('#district',record.id);state=await ready(record.id);
    assert.equal(state.triangles,record.triangles);assert.equal(state.geometries,2);
  }
  checks.push({check:'all 16 GLBs actually rendered, triangle counts match; old GPU geometries disposed'});
  await page.click('#top');await page.screenshot({path:path.join(out,'chongming.png')});
  await page.selectOption('#district','310118');await ready('310118');await page.click('#top');
  await page.screenshot({path:path.join(out,'qingpu.png')});
  // A late, aborted download must never replace the latest selection.
  await page.route('**/assets/surfaces/310115.glb',async route=>{await new Promise(r=>setTimeout(r,500));await route.continue().catch(()=>{});});
  await page.selectOption('#district','310115');await page.selectOption('#district','310104');await ready('310104');
  await page.waitForTimeout(700);assert.equal((await page.evaluate(()=>window.surfaceViewer.getState())).selection,'310104');
  await page.unroute('**/assets/surfaces/310115.glb');
  checks.push({check:'rapid selection cancels old load without late replacement'});
  await page.selectOption('#district','all');state=await ready('all');
  assert.equal(state.visibleDistricts.length,16);assert.equal(state.geometries,32);
  assert.equal(state.triangles,manifest.districts.reduce((n,r)=>n+r.triangles,0));
  checks.push({check:'all-district assembly actual render',state});
  await page.click('#top');await page.screenshot({path:path.join(out,'all-districts.png')});
  await page.selectOption('#district','310101');await ready('310101');
  // Return HTTP 200 with damaged bytes: must fail integrity check and retain old model.
  await page.route('**/assets/surfaces/310104.glb',route=>route.fulfill({status:200,contentType:'model/gltf-binary',body:Buffer.from('damaged')}));
  await page.selectOption('#district','310104');await page.waitForFunction(()=>window.surfaceViewer.getState().status==='error');
  state=await page.evaluate(()=>window.surfaceViewer.getState());assert.equal(state.selection,'310101');assert.equal(state.geometries,2);
  assert(await page.locator('#retry').isVisible());
  await page.unroute('**/assets/surfaces/310104.glb');await page.click('#retry');await ready('310104');
  checks.push({check:'damaged asset rejected, last model retained, retry recovers'});
  await page.reload();await ready('310104');checks.push({check:'hash survives reload'});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(out,'mobile.png')});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  checks.push({check:'mobile viewport has no horizontal overflow; screenshot captured'});
  assert.deepEqual(errors,[]);assert.deepEqual(httpErrors,[]);
  fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify({browser:await browser.version(),checks,pageErrors:errors,httpErrors},null,2)+'\n');
  await browser.close();console.log(JSON.stringify({checks:checks.length,errors,httpErrors}));
})().catch(error=>{console.error(error);process.exit(1);});
