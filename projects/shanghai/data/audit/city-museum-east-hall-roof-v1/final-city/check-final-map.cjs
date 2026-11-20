/* Walk and render the same registered museum before and after the isolated roof revision. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto'),{chromium}=require('playwright');
const before=process.argv.includes('--before'),id='yangpu-former-shanghai-city-museum';
const base=process.env.MODEL_BASE_URL,project=process.env.SHANGHAI_PROJECT_ROOT,out=process.env.QA_OUTPUT_DIR;
const sha=b=>createHash('sha256').update(b).digest('hex');
(async()=>{
 if(!base||!project||!out)throw Error('Supply MODEL_BASE_URL, SHANGHAI_PROJECT_ROOT and QA_OUTPUT_DIR');
 fs.mkdirSync(out,{recursive:true});
 const getBytes=f=>fs.readFileSync(path.join(project,f)),catPath='data/candidate-city-integrations.json',catalog=JSON.parse(getBytes(catPath));
 const rows=catalog.models.filter(r=>r.id===id);assert.equal(rows.length,1);const row=rows[0];
 assert.equal(path.basename(row.candidate_manifest),before?'manifest.json':'manifest-east-hall-roof.json');
 const response=await fetch(new URL(row.candidate_manifest,base));assert.equal(response.status,200);
 const manifestBody=Buffer.from(await response.arrayBuffer()),manifest=JSON.parse(manifestBody),root=path.posix.dirname(row.candidate_manifest);
 for(const [variant,role]of [['full','web'],['lod','lod']])assert.equal(manifest.assets[variant].sha256,row.assets[role].sha256);
 const role=variant=>variant==='full'?'web':'lod';
 function point(x,y){
  const r=6371008.8*Math.cos(row.lat*Math.PI/180);return [row.lng+x/r*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(row.lat*Math.PI/180))+y/r))*180/Math.PI];
 }
 const probes=[['west tower',-13.52,-.79],['east hall',3,-1.1],['north open court',18,16],['south open court',18,-15],['retained source 510',3.553,-16.335],['retained source 1262',2.670,16.282]].map(([name,x,y])=>({name,x,y,wgs:point(x,y)}));
 const report={before,id,base,catalogCount:catalog.resulting_city_count,catalogSha256:sha(getBytes(catPath)),manifest:row.candidate_manifest,manifestHttpSha256:sha(manifestBody),scriptSha256:sha(fs.readFileSync(__filename)),started:new Date().toISOString(),completed:false,views:[],ground:[],bindings:[],errors:[]};
 const save=()=>fs.writeFileSync(path.join(out,before?'control-browser.json':'main-browser.json'),JSON.stringify(report,null,2)+'\n');
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
 try{
  const page=await browser.newPage({viewport:before?{width:810,height:580}:{width:390,height:790},hasTouch:!before,ignoreHTTPSErrors:true});
  const events=new Map();page.on('response',r=>events.set(new URL(r.url()).pathname,r));page.on('pageerror',e=>report.errors.push(e.message));page.setDefaultTimeout(230000);
  await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
  const card=page.locator('.landmark-card[data-landmark="'+id+'"]');assert.equal(await card.count(),1);
  const destination=card.locator('.card-foot a[href="index.html#landmark='+id+'&mode=overview"]');await destination.click();
  async function view(name,variant){
   await page.waitForFunction(()=>{const el=document.querySelector('#loading'),style=el&&getComputedStyle(el);
     return el?.classList.contains('loaded')&&style.opacity==='0'&&style.visibility==='hidden'&&style.pointerEvents==='none';
   },null,{timeout:420000,polling:400});
   if(name==='east-roof') await page.waitForFunction(({id,macro})=>{
      const scene=window.__SHANGHAI_APP__.scene,stream=scene.getStreamingState();
      return stream.active.some(r=>r.id===macro&&r.visible)&&stream.detail.active.some(r=>r.id.startsWith(macro+'/'))&&scene.getLandmarkAssetState(id)?.visible;
   },{id,macro:row.owner.macro_id},{timeout:300000,polling:400});
   await page.waitForFunction(({id,variant})=>{const s=window.__SHANGHAI_APP__?.scene,a=s?.getLandmarkAssetState(id);return a?.status==='loaded'&&a.visible&&a.variant===variant&&!s.map.isMoving();},{id,variant},{timeout:245000,polling:350});
   const s=await page.evaluate(id=>{const app=window.__SHANGHAI_APP__,s=app.scene,a=s.getLandmarkAssetState(id),t=s.getStreamingState(),ci=s.getCandidateIntegrationState(),b=s.getBuildingBeaconState(),label=b.labelPositions.find(r=>r.id===id),gl=s.map.painter.context.gl;return {route:location.hash,place:document.querySelector('#location-name').textContent,count:b.count,picked:label&&s.pickBuildingBeacon(label),variant:a.variant,triangles:a.triangles,sha256:a.verifiedAsset.sha256,anchor:a.anchor,heading:a.heading,contextLost:gl.isContextLost(),glError:gl.getError(),activeNative:t.active.map(x=>x.id),activeGroups:t.detail.active.map(x=>x.id),modelClips:ci.clips.filter(r=>r.id===id)};},id);
   assert.equal(s.count,catalog.resulting_city_count);assert.equal(s.picked,id);assert.equal(s.triangles,row.assets[role(variant)].triangles);assert.equal(s.sha256,row.assets[role(variant)].sha256);assert.deepEqual(s.anchor,[row.lng,row.lat]);assert.equal(s.heading,row.heading);assert(!s.contextLost);assert.equal(s.glError,0);
   await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>resolve());m.triggerRepaint();}));
   s.visibleFrames=await page.evaluate(async()=>{
    const states=[],map=window.__SHANGHAI_APP__.scene.map;
    for(let i=0;i<4;i++){await new Promise(done=>requestAnimationFrame(done));const css=getComputedStyle(document.querySelector('#loading'));
      states.push({opacity:css.opacity,visibility:css.visibility,pointerEvents:css.pointerEvents,moving:map.isMoving(),bearing:map.getBearing(),pitch:map.getPitch(),zoom:map.getZoom(),center:map.getCenter().toArray()});}
    return states;
   });
   for(const frame of s.visibleFrames){assert.equal(frame.opacity,'0');assert.equal(frame.moving,false);assert.equal(frame.visibility,'hidden');assert.deepEqual(frame,s.visibleFrames[0]);}
   const file=(before?'before-':'map-')+name+'.png',b=await page.screenshot({path:path.join(out,file),timeout:230000});
   report.views.push({file,...s,bytes:b.length,imageSha256:sha(b)});save();
  }
  const jump=async (x,y,elevation,zoom,pitch,bearing)=>page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.refreshBuildingBeacons();s.loadLandmarks();},{center:point(x,y),elevation,zoom,pitch,bearing,padding:{left:0,right:0,top:0,bottom:55}});
  if(!before){await view('mobile','full');await page.setViewportSize({width:810,height:580});await view('desktop','full');}
  else await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene);
  const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
  await jump(3,-1.1,10.3,20.2,35,-12);await view('east-roof','full');
  report.ground=await page.evaluate(ps=>ps.map(p=>({...p,actual:window.__SHANGHAI_APP__.scene.collisionAt(...p.wgs)})),probes);
  if(!before){
   const baseline=JSON.parse(fs.readFileSync(process.env.QA_CONTROL_REPORT));
   assert.equal(baseline.catalogCount,report.catalogCount);assert(baseline.completed);assert.deepEqual(report.ground,baseline.ground);
   assert.equal(report.ground.find(r=>r.name==='east hall').actual,'building');
   assert(report.ground.filter(r=>r.name.includes('open court')).every(r=>r.actual===null));
   assert(report.ground.filter(r=>r.name.includes('retained source')).every(r=>r.actual==='building'));
  }
  await jump(0,0,0,15.45,30,-7);await view('distant','distant');
  for(const variant of ['full','lod']){
   const meta=manifest.assets[variant],name=path.posix.join(root,meta.file),r=events.get(new URL(name,base).pathname);assert(r,name);assert.equal(r.status(),200);
   const b=await r.body();assert.equal(b.length,meta.bytes);assert.equal(sha(b),meta.sha256);report.bindings.push({name,bytes:b.length,sha256:sha(b)});
  }
  assert.deepEqual(report.errors,[]);report.completed=true;
 }catch(e){report.failure=e.stack;throw e;}
 finally{report.finished=new Date().toISOString();save();await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
