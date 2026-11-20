const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright'),{createHash}=require('node:crypto');
const id='huangpu-dongjiadu-cathedral',out=process.argv[3],base=process.argv[2];
const sha=b=>createHash('sha256').update(b).digest('hex');
const audit='/workspace/e-resource/projects/shanghai/source/precise/'+id+'/footprint-review.json',review=JSON.parse(fs.readFileSync(audit));
const native=review.frozen_macro+'/'+review.near_tiles[0].id,key=review.owners.find(r=>r.local_id===854)?.key?.slice(9);
fs.mkdirSync(out,{recursive:true});const result={started:new Date().toISOString(),sha256:sha(fs.readFileSync(__filename)),base,views:[],errors:[]};const save=()=>fs.writeFileSync(path.join(out,'previews.json'),JSON.stringify(result,null,2)+'\n');
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{for(const [kind,width,height]of [['desktop',870,660],['mobile',390,844]]){
 const ctx=await browser.newContext({viewport:{width,height},hasTouch:true,ignoreHTTPSErrors:true});const page=await ctx.newPage();page.setDefaultTimeout(200000);
 page.on('pageerror',e=>result.errors.push(e.message));await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
 const link=page.locator('[data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]');
 if(kind==='mobile')await link.tap();else await link.click();
 async function photo(name,expectedBearing,expectedPitch){
  await page.waitForFunction(({id,native,b,p})=>{
   const s=window.__SHANGHAI_APP__?.scene;if(!s||s.map.isMoving())return false;const a=s.getLandmarkAssetState(id),m=s.map,l=document.querySelector('#loading'),style=l&&getComputedStyle(l);
   return a?.visible&&a.status==='loaded'&&Math.abs(m.getBearing()-b)<.005&&Math.abs(m.getPitch()-p)<.005&&s.getStreamingState().detail.active.some(t=>t.id===native)&&!s.getCandidateIntegrationState().vector.some(v=>v.active&&(v.pending||v.residualLayer?.busy))&&(!l||style.visibility==='hidden'&&Number(style.opacity)===0&&style.pointerEvents==='none');
  },{id,native,b:expectedBearing,p:expectedPitch},{timeout:300000,polling:400});
  await page.evaluate(async()=>{for(let i=0;i<4;i++)await new Promise(ok=>requestAnimationFrame(()=>ok()));});
  const info=await page.evaluate(({id,native,key})=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState(id),l=document.querySelector('#loading');return{bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),center:m.getCenter(),elevation:m.getCenterElevation(),padding:m.getPadding(),native:s.getStreamingState().detail.active.some(x=>x.id===native),neighbor854:key?m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:key}):null,triangles:a.triangles,sha256:a.verifiedAsset.sha256,visible:a.visible,route:location.hash,overlay:l?[getComputedStyle(l).visibility,getComputedStyle(l).opacity]:null};},{id,native,key});
  assert.equal(info.triangles,59244);assert(info.native&&info.visible);
  const file=kind+'-'+name+'.png',data=await page.screenshot({path:path.join(out,file),timeout:190000});result.views.push({...info,kind,name,file,screenshotSha256:sha(data)});save();console.log(kind,name);
 }
 await photo('frontal-warm',1,60);
 if(kind==='desktop'){
  await page.evaluate(async id=>{const {candidateOverviewCamera}=await import('./src/candidate-overview-camera.js');const raw=await (await fetch('data/candidate-city-integrations.json')).json();const row=raw.models.find(r=>r.id===id);const s=window.__SHANGHAI_APP__.scene,m=s.map,canvas=m.getCanvas();
   const camera=candidateOverviewCamera({...row,city_integration:true,overviewBearing:61,overviewPitch:48},{width:canvas.clientWidth,height:canvas.clientHeight,insets:m.getPadding()});m.setCenterClampedToGround(false);m.jumpTo(camera);s.loadLandmarks();s.refreshBuildingBeacons();},id);
  await photo('oblique-warm',61,48);
 }
 await ctx.close();
}assert.equal(result.errors.length,0);result.completed=true;}catch(e){result.failure=e.stack;throw e;}finally{save();await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
