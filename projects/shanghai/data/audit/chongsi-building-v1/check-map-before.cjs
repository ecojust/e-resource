// Select the nearby library in the actual 160-entry directory and inspect the original campus source group.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');
const sha=b=>createHash('sha256').update(b).digest('hex');
const audit=__dirname,root=process.env.SHANGHAI_PROJECT_ROOT,base=process.env.MODEL_BASE_URL,out=process.env.QA_OUTPUT_DIR;
const spec=JSON.parse(fs.readFileSync(path.join(audit,'before-map-case.json')));
const id=spec.previous,macro=spec.source_macro,owner=spec.source_owner;
async function run(){
 assert.ok(root&&base&&out);fs.mkdirSync(out,{recursive:true});const log=path.join(out,'control.json');assert.ok(!fs.existsSync(log));
 const data={phase:'before',base,selected:id,case_sha256:sha(fs.readFileSync(path.join(audit,'before-map-case.json'))),script_sha256:sha(fs.readFileSync(__filename)),complete:false,observed:{},errors:[]};
 const save=()=>fs.writeFileSync(log,JSON.stringify(data,null,2)+'\n');save();
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:850,height:650}});page.setDefaultTimeout(180000);
  const seen=new Set();page.on('response',r=>seen.add(new URL(r.url()).pathname.replace(/^\//,'')));
  page.on('pageerror',e=>data.errors.push(e.message));
  await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
  await page.locator('[data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').click();
  await page.waitForFunction(id=>{
   const a=window.__SHANGHAI_APP__;return new URLSearchParams(location.hash.slice(1)).get('landmark')===id && a?.scene && !a.scene.map.isMoving() && a.scene.getLandmarkAssetState(id)?.visible;
  },id,{timeout:240000,polling:500});
  const toggle=page.locator('#panel-toggle');if(await toggle.getAttribute('aria-expanded')==='true')await toggle.click();
  await page.evaluate(camera=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(camera);s.loadLandmarks();s.refreshBuildingBeacons();},spec.front);
  const tile=macro+'/'+spec.group;
  await page.waitForFunction(tile=>{const s=window.__SHANGHAI_APP__.scene;return !s.map.isMoving()&&s.getStreamingState().detail.active.some(t=>t.id===tile);},tile,{polling:500,timeout:300000});
  data.state=await page.evaluate(({tile,school})=>{
   const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,c=s.getCandidateIntegrationState(),beacons=s.getBuildingBeaconState();
   return {route:location.hash,camera:{center:m.getCenter(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom()},beacons:beacons.count,context_lost:m.painter.context.gl.isContextLost(),viewport:[innerWidth,innerHeight],native_group:s.getStreamingState().detail.active.find(v=>v.id===tile),
     school_asset:s.getLandmarkAssetState(school)||null,school_clips:c.displayClips.filter(r=>r.id===school),owner_scoped:c.shader.ownerScopedSources.find(r=>r.id===tile)||null};
  },{tile,school:spec.id});
  assert.equal(data.state.beacons,spec.before.count);assert.ok(!data.state.context_lost);assert.ok(!data.state.school_asset?.visible);assert.deepEqual(data.state.school_clips,[]);
  assert.ok(!data.state.owner_scoped?.clip_feature_local_ids.includes(owner));save();
  const img=await page.screenshot({path:path.join(out,'control-street.png'),timeout:140000});data.photo={file:'control-street.png',bytes:img.length,sha256:sha(img)};save();
  for(const f of ['data/candidate-city-integrations.json','index.html','src/app.js','src/map-scene.js','src/building-beacons.js','src/candidate-city-clipping.js','assets/city-detail/macros/'+macro+'/'+spec.near_file]){
   const r=await page.request.get(new URL(f,base).href),b=await r.body();assert.equal(r.status(),200);assert.ok(seen.has(f),f);
   const h=sha(b);if(f.startsWith('assets/city-detail/'))assert.equal(h,spec.near_sha256);else assert.equal(h,sha(fs.readFileSync(path.join(root,f))));
   if(f.startsWith('data/candidate-'))assert.equal(h,spec.before.catalog_sha256);
   data.observed[f]={bytes:b.length,sha256:h};
  }
  assert.deepEqual(data.errors,[]);data.complete=true;
 }catch(e){data.failure=e.stack;throw e;}finally{await browser.close();data.browser_closed=true;save();}
}
run().catch(e=>{console.error(e);process.exitCode=1});
