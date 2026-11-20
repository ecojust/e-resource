/* Evaluate street sightlines with the released app's fitted-camera entry point. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto');const {chromium}=require('playwright');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const root=process.env.SHANGHAI_PROJECT_ROOT||path.resolve(__dirname,'../../..');
const base=process.env.MODEL_BASE_URL||'http://127.0.0.1:8784/';
const output=process.env.QA_OUTPUT_DIR||__dirname;fs.mkdirSync(output,{recursive:true});
const id='hongkou-duolun-250',file='data/candidate-city-integrations.json',catalog=JSON.parse(fs.readFileSync(path.join(root,file)));assert.equal(catalog.resulting_city_count,103);
const row=catalog.models.find(r=>r.id===id),mf=JSON.parse(fs.readFileSync(path.join(root,row.candidate_manifest)));
const r={id,started:new Date().toISOString(),catalog:sha(fs.readFileSync(path.join(root,file))),script:sha(fs.readFileSync(__filename)),views:[],errors:[]};
const save=()=>fs.writeFileSync(path.join(output,'overview-cameras.json'),JSON.stringify(r,null,2)+'\n');
(async()=>{const attach=process.env.QA_EXISTING_PAGE==='1';const browser=attach?await chromium.connectOverCDP('http://127.0.0.1:9457'):await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9457']});
 try{
  const page=attach?browser.contexts().flatMap(c=>c.pages()).find(p=>p.url().includes('index.html#landmark='+id)):await browser.newPage({viewport:{width:840,height:610},hasTouch:true,ignoreHTTPSErrors:true});
  page.on('pageerror',e=>r.errors.push(e.message));page.on('console',m=>{if(m.text().includes('模型加载失败'))r.errors.push(m.text())});
  if(!attach){await page.goto(new URL('qa-blank.html',base).href);
  const preload=[row.candidate_manifest,...['full','lod'].map(role=>path.posix.dirname(row.candidate_manifest)+'/'+mf.assets[role].file),'assets/city-detail/manifest.json','assets/city-detail/macros/14-13720-6692/READY.json','assets/city-detail/macros/14-13720-6692/near/0_1-s1-s0-s0.glb.gz'];
  await page.evaluate(async a=>{for(const u of a){const r=await fetch(u);if(!r.ok)throw Error(u);await r.arrayBuffer();}},preload);
  await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
  await page.locator('#district-310109 [data-landmark="'+id+'"] .card-foot a[href^="index.html"]').click();}
  console.log('Waiting for full scene',new Date().toISOString());
  await page.waitForFunction(id=>window.__SHANGHAI_APP__?.scene.getLandmarkAssetState(id)?.verifiedAsset?.variant==='web',id,{timeout:750000,polling:600});
  const sample=async(width,bearing,pitch)=>{
   if(width!==await page.evaluate(()=>innerWidth))await page.setViewportSize({width,height:width<500?844:610});
   const panel=page.locator('#panel-toggle');
   if(width>=500 && await panel.getAttribute('aria-expanded')==='false')await panel.click({force:true});
   await page.evaluate(async({id,bearing,pitch})=>{
    const a=window.__SHANGHAI_APP__,p=a.landmarks.find(l=>l.id===id);if(!p)throw Error(id);
    await a.selectPlace({...p,overviewBearing:bearing,overviewPitch:pitch},{mode:'overview'});
    a.scene.loadLandmarks();a.scene.refreshBuildingBeacons();
   },{id,bearing,pitch});
   await page.waitForFunction(({id,bearing,pitch})=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState(id);const b=s.getBuildingBeaconState(),l=b.labelPositions.find(q=>q.id===id),c=s.getCandidateIntegrationState();
    return !m.isMoving()&&Math.abs(m.getBearing()-bearing)<.05&&Math.abs(m.getPitch()-pitch)<.05&&a.verifiedAsset?.variant==='web'&&b.count===103&&l&&s.pickBuildingBeacon(l)===id&&c.shader.ownerScopedSources.some(g=>g.clip_feature_local_ids.includes(808));
   },{id,bearing,pitch},{timeout:420000,polling:500});
   await page.evaluate(()=>new Promise(r=>{const m=window.__SHANGHAI_APP__.scene.map;let count=0;function draw(){if(++count===3){m.off('render',draw);r();}else m.triggerRepaint();}m.on('render',draw);m.triggerRepaint();}));
   const state=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState(id);return {width:innerWidth,height:innerHeight,bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),center:m.getCenter(),selected:document.querySelector('#location-name').textContent,model_sha256:a.verifiedAsset.sha256,triangles:a.triangles,near:s.getCandidateIntegrationState().shader.ownerScopedSources.filter(g=>g.clip_feature_local_ids.includes(808)).map(g=>g.id),camera_eye:m.transform.getCameraLngLat?.(),camera_ground_height:m.transform.getCameraAltitude?.(),webgl_lost:m.painter.context.gl.isContextLost()};},id);
   const name='overview-'+width+'-'+bearing+'-'+pitch+'.png';const bytes=await page.screenshot({path:path.join(output,name),timeout:180000});
   assert.equal(state.model_sha256,mf.assets.full.sha256);assert.equal(state.webgl_lost,false);r.views.push({...state,file:name,sha256:sha(bytes)});save();console.log('Captured',name,new Date().toISOString());
  };
  const desktopAngles=process.env.QA_CAMERAS?JSON.parse(process.env.QA_CAMERAS):[[168,52],[100,49],[168,39]];
  for(const [b,p] of desktopAngles)await sample(840,b,p);
  const phoneAngles=process.env.QA_PHONE_CAMERAS?JSON.parse(process.env.QA_PHONE_CAMERAS):[[168,52],[100,49]];
  for(const [b,p] of phoneAngles)await sample(390,b,p);
  r.completed=true;
 }catch(e){r.error=e.stack;throw e;}finally{r.finished=new Date().toISOString();save();await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
