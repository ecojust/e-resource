/* Record the actual automatically fitted view before zooming into the source's near tile.
 * Run beside check-main-map.cjs with QA_CDP_PORT set on both commands. */
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('playwright');
const {createHash}=require('node:crypto');
const assert=require('node:assert/strict');
const out=process.env.QA_OUTPUT_DIR||__dirname;
const port=Number(process.env.QA_CDP_PORT||9453);
const id='huangpu-asia-building',key='b538126a-4c24-4580-bb40-c1413c5ae04b';
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={script_sha256:sha(fs.readFileSync(__filename)),started:new Date().toISOString(),views:[]};
const save=()=>fs.writeFileSync(path.join(out,'settled-overview.json'),JSON.stringify(report,null,2)+'\n');
(async()=>{
 const browser=await chromium.connectOverCDP('http://127.0.0.1:'+port,{timeout:120000});
 try{
  const target=browser.contexts().flatMap(c=>c.pages()).find(p=>p.url().includes('index.html#landmark='+id));
  assert(target);
  for(const mode of ['desktop','mobile']){
   await target.waitForFunction(({id,key,mode})=>{
     const app=window.__SHANGHAI_APP__,s=app?.scene,m=s?.map;if(!s||m.isMoving())return false;
     if((innerWidth<500)!==(mode==='mobile'))return false;
     const label=s.getBuildingBeaconState().labelPositions.find(l=>l.id===id),a=s.getLandmarkState().find(x=>x.id===id);
     const state=m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:key});
     return a?.activeVariant==='full'&&a.status==='loaded'&&label&&s.pickBuildingBeacon(label)===id&&(state.localModel||state.candidateModel);
   },{id,key,mode},{polling:600,timeout:900000});
   const state=await target.evaluate(({id,key})=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,v=s.getLandmarkAssetState(id),c=s.getCandidateIntegrationState();
     return {url:location.href,width:innerWidth,height:innerHeight,zoom:m.getZoom(),center:m.getCenter(),pitch:m.getPitch(),bearing:m.getBearing(),
       labels:s.getBuildingBeaconState().count,variant:v.variant,sha256:v.verifiedAsset.sha256,triangles:v.triangles,source:m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:key}),
       near:c.shader.ownerScopedSources.some(g=>g.clip_feature_local_ids.includes(2141)),webgl_lost:m.painter.context.gl.isContextLost()};
   },{id,key});
   assert.equal(state.labels,99);assert.equal(state.webgl_lost,false);assert.equal(state.triangles,91276);
   const name='overview-settled-'+mode+'.png';
   const data=await target.screenshot({path:path.join(out,name),timeout:180000});
   report.views.push({mode,...state,file:name,screenshot_sha256:sha(data),bytes:data.length,at:new Date().toISOString()});save();
   // For near-group ownership checks the companion test needs a zoom above the streaming threshold.
   await target.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;
     m.jumpTo({zoom:19.15});s.loadLandmarks();s.refreshBuildingBeacons();});
  }
  report.completed=true;
 }catch(e){report.failure=e.stack;throw e;}finally{report.finished=new Date().toISOString();save();await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
