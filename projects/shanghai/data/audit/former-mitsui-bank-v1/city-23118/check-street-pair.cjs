/* Compare the actual two frozen maps from one independently surveyed camera. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');
const {PNG} = require('pngjs');
const work='/tmp/mitsui118', out=process.env.QA_OUTPUT_DIR||work+'/facade-pair-23118';
const audit='/workspace/e-resource/projects/shanghai/data/audit/former-mitsui-bank-v1';
const read=(file)=>JSON.parse(fs.readFileSync(file));
const sha=(bytes)=>createHash('sha256').update(bytes).digest('hex');
const ct=read(audit+'/final-placement-contract.json'), spec=read(audit+'/map-case.json');
const checked=read(work+'/alternate-camera.json').selected, angle=ct.heading*Math.PI/180;
const earth=6371008.8*Math.cos(ct.lat*Math.PI/180);
const e=checked.center[0]*Math.cos(angle)+checked.center[1]*Math.sin(angle),n=-checked.center[0]*Math.sin(angle)+checked.center[1]*Math.cos(angle);
const camera={center:[ct.lng+e/earth*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(ct.lat*Math.PI/180))+n/earth))*180/Math.PI],elevation:checked.elevation,zoom:checked.zoom,pitch:checked.pitch,bearing:checked.bearing,padding:{left:0,right:0,top:0,bottom:0}};
const groups=spec.ownerGroups.map(g=>({...g,full:ct.owner.macro_id+'/'+g.id}));
const input=read(audit+'/street-selection-parent-controls.json').endpoints;
const dest=out+'/street-facade-pair.json';fs.mkdirSync(out,{recursive:true});assert.ok(!fs.existsSync(dest));
const result={completed:false,camera,scriptSha256:sha(fs.readFileSync(__filename)),cameraStudySha256:sha(fs.readFileSync(work+'/alternate-camera.json')),started:new Date().toISOString(),records:[]};
const save=()=>fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n');
function diversity(img){const v=PNG.sync.read(img);const hist=new Map();let all=0;
  for(let y=130;y<Math.min(488,v.height);y+=2)for(let x=130;x<Math.min(744,v.width);x+=2){const i=(y*v.width+x)*4;const q=((v.data[i]>>3)<<10)|((v.data[i+1]>>3)<<5)|(v.data[i+2]>>3);hist.set(q,(hist.get(q)||0)+1);all++;}
  return {distinctQuantizedRGB:hist.size,largestFlatFraction:Math.max(...hist.values())/all};
}
async function run(){
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{for(const proof of input){const current=proof.stage===118,id=current?ct.id:spec.previous,base='http://127.0.0.1:'+proof.port+'/';
  const context=await browser.newContext({viewport:{width:870,height:660},ignoreHTTPSErrors:true});const page=await context.newPage();
  page.setDefaultTimeout(180000);const row={port:proof.port,id,current,errors:[]};result.records.push(row);page.on('pageerror',err=>row.errors.push(err.message));
  const resp=await page.request.get(base+'data/candidate-city-integrations.json');const bytes=await resp.body();const cat=JSON.parse(bytes);assert.equal(sha(bytes),proof.catalog_sha256);assert.equal(cat.resulting_city_count,proof.entry_count);row.catalog={entries:cat.resulting_city_count,sha256:sha(bytes)};save();console.log('Fetched catalogue',proof.port,cat.resulting_city_count);
  const model=cat.models.find(v=>v.id===id);assert.ok(model);const requests=new Map();page.on('response',r=>requests.set(new URL(r.url()).pathname.slice(1),r));
  await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});assert.equal(await page.locator('.landmark-card[data-landmark]').count(),cat.resulting_city_count);
  await page.locator('[data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').click();
  await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()),null,{timeout:180000});
  const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
  await page.evaluate(view=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(view);s.loadLandmarks();s.refreshBuildingBeacons();},camera);row.cameraApplied=true;save();console.log('Applied surveyed view',proof.port);
  await page.waitForFunction(({id,current,groups})=>{const s=window.__SHANGHAI_APP__.scene;const a=s.getLandmarkAssetState(id),c=s.getCandidateIntegrationState(),stream=s.getStreamingState();
   return a?.visible&&a.status==='loaded'&&a.variant==='full'&&!s.map.isMoving()&&groups.every(g=>{const d=c.shader.ownerScopedSources.find(x=>x.id===g.full);return d&&stream.detail.active.some(v=>v.id===g.full)&&g.targetOwners.every(t=>d.clip_feature_local_ids.includes(t)===current);});
  },{id,current,groups},{timeout:240000,polling:350});
  const state=await page.evaluate(({id,groups})=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;const ci=s.getCandidateIntegrationState(),gl=m.painter.context.gl;return {asset:s.getLandmarkAssetState(id),groups:groups.map(g=>ci.shader.ownerScopedSources.find(v=>v.id===g.full)),viewport:[innerWidth,innerHeight],route:location.hash,currentCamera:{center:m.getCenter(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),elevation:m.getCenterElevation()},contextLost:gl.isContextLost()};},{id,groups});
  assert.ok(Math.abs(state.currentCamera.center.lng-camera.center[0])<.000003&&Math.abs(state.currentCamera.center.lat-camera.center[1])<.000003,'camera centre changed');assert.ok(Math.abs(state.currentCamera.zoom-camera.zoom)<.001&&Math.abs(state.currentCamera.pitch-camera.pitch)<.001&&Math.abs(((state.currentCamera.bearing-camera.bearing+540)%360)-180)<.001,'camera angle changed');assert.equal(state.asset.verifiedAsset.sha256,model.assets.web.sha256);assert.equal(state.asset.triangles,model.assets.web.triangles);assert.equal(state.contextLost,false);row.state=state;save();console.log('Verified near geometry',proof.port,state.asset.triangles);
  const match=requests.get(state.asset.verifiedAsset.file);assert.ok(match,'model was requested from the map origin');assert.equal(sha(await match.body()),model.assets.web.sha256);
  const marker=current?'after':'before';let shot,score;
  for(let i=0;i<5;i++){await page.evaluate(()=>new Promise(done=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>done());m.triggerRepaint();}));shot=await page.screenshot({timeout:150000});score=diversity(shot);if(score.largestFlatFraction<.85&&score.distinctQuantizedRGB>20)break;await page.waitForTimeout(550);}
  const f='facade-'+marker+'.png';fs.writeFileSync(out+'/'+f,shot);row.image={file:f,bytes:shot.length,sha256:sha(shot),...score};save();await context.close();console.log('captured',proof.port,score);
 }}
 finally{await browser.close();result.finished=new Date().toISOString();result.completed=result.records.length===2&&result.records.every(r=>r.image&&r.errors.length===0);save();}
 assert.ok(result.completed);assert.ok(result.records.every(r=>r.image.largestFlatFraction<.85&&r.image.distinctQuantizedRGB>20),'Facade remained obscured at this one viewpoint');
}
run().catch(e=>{result.failure=String(e.stack||e);save();console.error(e);process.exitCode=1;});
