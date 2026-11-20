const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{createHash}=require('node:crypto'),{chromium}=require('playwright');
const dir=__dirname, base='http://127.0.0.1:24138/', file=path.join(dir,'post/main-browser.json'), first=JSON.parse(fs.readFileSync(file)), id=first.id;
const sha=b=>createHash('sha256').update(b).digest('hex');
(async()=>{
 const resolved=JSON.parse(fs.readFileSync(path.join(dir,'cache-recovery.json')));
 const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9838']});
 const page=await b.newPage({hasTouch:true,viewport:{width:390,height:844}}),fails=[],errors=[],co=[],images=[];
 const report={origin:base,target:id,started:new Date().toISOString(),firstReportSha256:sha(fs.readFileSync(file)),initialErrors:first.errors.length,initialFailedRequests:first.failed.length,individualRestoredUrls:resolved.unique_urls,files:[],images,errors,failed:fails,consoleErrors:co};
 const save=()=>fs.writeFileSync(path.join(dir,'retest.json'),JSON.stringify(report,null,2)+'\n');
 page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')fails.push([r.url(),r.failure()]);});
 page.on('response',r=>{if(r.status()>=400)fails.push([r.url(),r.status()]);});
 page.on('console',m=>{if(m.type()==='error')co.push([m.location().url,m.text()])});
 try{
  for(const row of resolved.recovered){
   const r=await page.request.get(row.url,{timeout:40000});assert.equal(r.status(),200);const data=await r.body();assert.equal(sha(data),row.sha256);report.files.push([row.rel,data.length,row.sha256]);await r.dispose();
  }
  const c=await page.request.get(base+'data/candidate-city-integrations.json');assert.equal(sha(await c.body()),first.catalog.sha256);await c.dispose();
  await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});await page.locator('[data-landmark="'+id+'"] .card-foot a[href^="index.html#"]').tap();
  async function shot(name,v){
   await page.waitForFunction(({id,v})=>{const s=window.__SHANGHAI_APP__?.scene,a=s?.getLandmarkAssetState(id);return a?.visible&&a.variant===v&&!s.map.isMoving()},{id,v},{timeout:180000,polling:350});
   await page.evaluate(async()=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(20000);await new Promise(r=>{s.map.once('render',r);s.map.triggerRepaint();});});
   const actual=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,c=s.getCandidateIntegrationState(),asset=s.getLandmarkAssetState(id);return {asset,contextLost:m.painter.context.gl.isContextLost(),glError:m.painter.context.gl.getError(),zoom:m.getZoom(),center:m.getCenter(),cuts:c.clips.find(q=>q.id===id),beacons:s.getBuildingBeaconState().count}},id);
   assert.equal(actual.glError,0);assert.equal(actual.contextLost,false);assert.equal(actual.beacons,176);assert.equal(actual.asset.variant,v);assert.equal(actual.cuts.owner.feature_local_id,338);
   const out=path.join(dir,name+'.png'),raw=await page.screenshot({path:out,timeout:240000});images.push({name:name+'.png',sha256:sha(raw),actual});save();
  }
  await shot('restored-mobile-default','full');
  await page.setViewportSize({width:600,height:460});
  const final=first.views.find(q=>q.view==='map-distant').camera;
  await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;m.setCenterClampedToGround(false);m.jumpTo({center:[c.center.lng,c.center.lat],zoom:c.zoom,pitch:c.pitch,bearing:c.bearing,elevation:c.elevation,padding:{top:0,right:0,bottom:0,left:0}});s.loadLandmarks();s.refreshBuildingBeacons();},final);
  await shot('restored-distant','distant');
  await page.waitForTimeout(1500);assert.deepEqual([errors,fails,co],[[],[],[]]);report.completed=true;
 }catch(e){report.failure=String(e);throw e;}finally{await b.close();report.finished=new Date().toISOString();save();}
})().catch(e=>{console.error(e);process.exitCode=1});
