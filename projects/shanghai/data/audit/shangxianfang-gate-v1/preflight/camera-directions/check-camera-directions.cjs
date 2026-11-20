const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto');const {chromium}=require('playwright');
const id='huangpu-shangxianfang-gate',w='/tmp/gate62/camera-compare',p='/workspace/e-resource/projects/shanghai';
const baseAfter=process.env.CAMERA_BASE||'http://127.0.0.1:8991/';
const h=b=>createHash('sha256').update(b).digest('hex');
const owner=JSON.parse(fs.readFileSync(path.join(p,'source/precise',id,'footprint-review.json')));
const group=owner.frozen_macro+'/'+owner.near_tiles[0].id;
const neighbors=owner.owners.filter(n=>[2357,2541,2597].includes(n.local_id)).map(n=>[n.local_id,n.source_key.slice(9)]);
const dir=process.env.CAMERA_OUT||w;fs.mkdirSync(dir,{recursive:true});
const result={started:new Date().toISOString(),checkerSha256:h(fs.readFileSync(__filename)),attempts:[]},save=()=>fs.writeFileSync(path.join(dir,'camera-comparison.json'),JSON.stringify(result,null,2)+'\n');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9364']});
 try{
 const cases=JSON.parse(process.env.CAMERA_CASES||JSON.stringify([['candidate-desktop',baseAfter,870,660],['candidate-mobile',baseAfter,390,844],['initial-desktop','http://127.0.0.1:8982/',870,660],['initial-mobile','http://127.0.0.1:8982/',390,844]]));
 for(const [name,base,width,height] of cases){
  const context=await browser.newContext({viewport:{width,height},hasTouch:true,ignoreHTTPSErrors:true}),page=await context.newPage();page.setDefaultTimeout(200000);
  const rec={name,base,viewport:[width,height],shots:[],errors:[],seen:[]};result.attempts.push(rec);save();
  page.on('pageerror',e=>rec.errors.push(e.message));
  page.on('response',r=>{const u=new URL(r.url());if(u.origin===new URL(base).origin&&(u.pathname.includes('shangxianfang-gate')||u.pathname.includes(owner.near_tiles[0].id)))rec.seen.push({path:u.pathname,status:r.status()});});
  const cat=await page.request.get(new URL('data/candidate-city-integrations.json',base).href),data=await cat.body(),list=JSON.parse(data);rec.catalog=h(data);assert.equal(list.resulting_city_count,108);const model=list.models.at(-1);assert.equal(model.id,id);rec.config={bearing:model.overviewBearing,pitch:model.overviewPitch};
  await page.goto(new URL('index.html#landmark='+id+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__?.scene,a=s?.getLandmarkAssetState(id);return a?.status==='loaded'&&a.visible&&!s.map.isMoving();},id);
  for(const phase of ['loaded','with-neighbors']){
   if(phase==='with-neighbors'){
    await page.waitForFunction(({g,id})=>{const s=window.__SHANGHAI_APP__.scene;const a=s.getLandmarkAssetState(id);return a?.visible&&!s.map.isMoving()&&s.getStreamingState().detail.active.some(t=>t.id===g);},{g:group,id},{timeout:220000,polling:450});
    await page.evaluate(()=>new Promise(ok=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>ok());m.triggerRepaint();}));
   }
   const state=await page.evaluate(({id,ns,g})=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState(id);return {route:location.hash,asset:a.verifiedAsset?.sha256,triangles:a.triangles,variant:a.variant,zoom:m.getZoom(),bearing:m.getBearing(),pitch:m.getPitch(),center:m.getCenter(),elevation:m.getCenterElevation(),groupLoaded:s.getStreamingState().detail.active.some(t=>t.id===g),neighbors:ns.map(([local,o])=>({local,state:m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o})})),clips:s.getCandidateIntegrationState().clips.filter(c=>c.id===id),contextLost:m.painter.context.gl.isContextLost()};},{id,ns:neighbors,g:group});
   assert.equal(state.asset,model.assets.web.sha256);assert.equal(state.triangles,59336);assert.deepEqual(state.clips,[]);assert.equal(state.contextLost,false);
   if(phase==='with-neighbors'){assert(state.groupLoaded);for(const n of state.neighbors){assert(n.state.localModel);assert(!n.state.candidateModel);}}
   const file=name+'-'+phase+'.png',png=await page.screenshot({path:path.join(dir,file),timeout:190000});rec.shots.push({phase,file,sha256:h(png),bytes:png.length,...state});save();console.log(name,phase,state.zoom,flush=true);
  }
  assert.deepEqual(rec.errors,[]);await context.close();
 }
 result.completed=true;
 }catch(e){result.failure=e.stack;throw e;}finally{save();await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
