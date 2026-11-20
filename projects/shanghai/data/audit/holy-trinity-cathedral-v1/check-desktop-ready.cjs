/* Capture the normal desktop registration after the city building has been suppressed. */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../../..');
const id='huangpu-holy-trinity-cathedral', macro='14-13720-6694';
const url=process.env.MODEL_BASE_URL||'http://127.0.0.1:8948/';
const out=process.env.QA_OUTPUT_DIR||__dirname;
const owner='37f57e01-bb54-4170-8fd5-5540c7c33690';
const hash=b=>createHash('sha256').update(b).digest('hex');
async function run(){
 const catalog=JSON.parse(fs.readFileSync(path.join(__dirname,'production-snapshot.json'))).files['data/candidate-city-integrations.json'];
 const manifest=JSON.parse(fs.readFileSync(path.join(root,'assets/models/candidates',id,'manifest.json')));
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const result={id,catalog_sha256:catalog,viewport:[870,660],started:new Date().toISOString(),errors:[],failed:[],script_sha256:hash(fs.readFileSync(__filename))};
 let page;
 try{
  page=await browser.newPage({viewport:{width:870,height:660},ignoreHTTPSErrors:true});
  page.on('pageerror',err=>result.errors.push(err.message));
  page.on('response',r=>{if(r.status()>=400)result.failed.push([r.url(),r.status()]);});
  const catalogResponse=page.waitForResponse(r=>r.url().includes('/data/candidate-city-integrations.json'));
  await page.goto(new URL('index.html#landmark='+id+'&mode=overview',url).href,{waitUntil:'domcontentloaded'});
  assert.equal(hash(await(await catalogResponse).body()),catalog);
  await page.waitForFunction(({id,owner,macro})=>{
   const app=window.__SHANGHAI_APP__,s=app?.scene,m=s?.map;
   if(!m||m.isMoving())return false;
   const a=s.getLandmarkAssetState(id),state=m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:owner});
   const c=s.getCandidateIntegrationState(),t=s.getStreamingState();
   return a?.visible && a?.status==='loaded' && (state.localModel||state.candidateModel) && c.clips.some(r=>r.id===id) &&
    t.active.some(g=>g.id===macro&&g.visible) && t.detail.loading===0;
  },{id,owner,macro},{polling:500,timeout:480000});
  const state=await page.evaluate(async({id,owner})=>{
   const s=window.__SHANGHAI_APP__.scene,m=s.map;
   await new Promise(r=>{m.once('render',r);m.triggerRepaint()});
   const a=s.getLandmarkAssetState(id),c=s.getBuildingBeaconState(),gl=m.painter.context.gl;
   return {hash:location.hash,count:c.count,model:a.verifiedAsset,variant:a.variant,visible:a.visible,owner:m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:owner}),
    pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom(),center:m.getCenter(),glError:gl.getError(),contextLost:gl.isContextLost(),panel:document.querySelector('#panel-toggle').getAttribute('aria-expanded')};
  },{id,owner});
  assert.equal(state.count,94);assert.equal(state.variant,'full');assert.equal(state.model.sha256,manifest.assets.full.sha256);
  assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.ok(Math.abs(state.pitch-45)<.001);
  assert.ok(Math.abs(state.bearing-(-74.58646501))<.001);assert.ok(state.hash.includes(id));assert.equal(state.panel,'true');
  fs.mkdirSync(out,{recursive:true});const png=await page.screenshot({path:path.join(out,'map-desktop-ready.png'),timeout:300000});
  Object.assign(result,{state,bytes:png.length,sha256:hash(png),passed:true});
  assert.deepEqual(result.errors,[]);assert.deepEqual(result.failed,[]);
 }catch(e){result.passed=false;result.error=e.stack;throw e;}
 finally{await browser.close();result.finished=new Date().toISOString();fs.writeFileSync(path.join(out,'desktop-ready.json'),JSON.stringify(result,null,2)+'\n');}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
