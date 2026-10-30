/* Actual WebGL load, variants, camera controls and local outdoor walking. MIT. */
const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000},hasTouch:true});const errors=[];
  page.on('console',m=>{if(m.type()==='error')console.error(m.text())});page.on('pageerror',e=>{errors.push(e.message);console.error(e.message)});page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('favicon.svg'))errors.push(`${r.status()} ${r.url()}`)});
  await page.goto(process.env.MODEL_URL||'http://127.0.0.1:8782/race-club.html');
  const ready=async v=>{await page.waitForFunction(v=>window.raceClubViewer?.getState().status==='error'||(window.raceClubViewer?.getState().status==='ready'&&window.raceClubViewer.getState().variant===v),v,{timeout:90000});const state=await page.evaluate(()=>raceClubViewer.getState());if(state.status!=='ready'||state.variant!==v)throw Error(JSON.stringify({state,errors}));};
  await ready('full');const full=await page.evaluate(()=>raceClubViewer.getState());
  if(full.modelId!=='huangpu-shanghai-race-club-east-building')throw Error('wrong model identity');
  await page.click('#front');await page.screenshot({path:'/workspace/race-browser-front.png'});
  await page.click('#rear');await page.screenshot({path:'/workspace/race-browser-rear.png'});
  await page.selectOption('#detail','lod');await ready('lod');const lod=await page.evaluate(()=>raceClubViewer.getState());
  if(lod.triangles>=full.triangles||lod.modelId!==full.modelId)throw Error('LOD identity or reduction failed');
  await page.screenshot({path:'/workspace/race-browser-lod.png'});
  await page.selectOption('#detail','full');await ready('full');await page.click('#oblique');
  await page.screenshot({path:'/workspace/race-browser-oblique.png'});
  await page.click('#enter-model-walk');await page.waitForFunction(()=>document.body.classList.contains('candidate-walking'));
  await page.keyboard.down('w');await page.waitForFunction(()=>window.candidateWalk.getState().distance>.05,null,{timeout:30000});await page.keyboard.up('w');
  const walk=await page.evaluate(()=>window.candidateWalk.getState());
  if(!(walk.distance>0)||walk.geographicRegistration!==false||walk.walkLimit!==80||walk.modelExtentLimit!==60)throw Error('outdoor walking configuration failed');
  if(!(Math.max(Math.abs(walk.bounds.minX),Math.abs(walk.bounds.maxX))>46))throw Error('wide model bounds missing');
  const boundary=await page.evaluate(async()=>{
   const {moveOutside,blockedAt}=await import('./src/candidate-walk-motion.js');
   const {bounds,walkLimit}=window.candidateWalk.getState();
   const start={x:55,z:bounds.maxZ+6};
   const beyondOldLimit=moveOutside(start,10,0,bounds,walkLimit);
   const stopped=moveOutside(beyondOldLimit,100,0,bounds,walkLimit);
   return {beyondOldLimit,stopped,defaultBlocks:blockedAt(start.x,start.z,bounds),configuredAllows:!blockedAt(start.x,start.z,bounds,undefined,walkLimit)};
  });
  if(!(boundary.beyondOldLimit.x>64&&boundary.stopped.x<=80&&boundary.stopped.x>79.8&&boundary.defaultBlocks&&boundary.configuredAllows))throw Error('configured walking boundary failed');
  await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.body.classList.contains('candidate-walking'));
  if(await page.locator('#downloads a').count()!==4)throw Error('downloads missing');
  await page.setViewportSize({width:390,height:844});await ready('full');
  await page.screenshot({path:'/workspace/race-browser-mobile.png'});
  await page.click('#enter-model-walk');await page.waitForFunction(()=>window.candidateWalk.getState().active);
  const pad=await page.locator('.walk-pad [data-key="w"]').boundingBox();
  const touch=await page.context().newCDPSession(page);
  await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:pad.x+pad.width/2,y:pad.y+pad.height/2}]});
  await page.waitForFunction(()=>window.candidateWalk.getState().distance>.05,null,{timeout:30000});
  await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await page.waitForFunction(()=>window.candidateWalk.getState().keys.length===0);
  const mobileWalk=await page.evaluate(()=>window.candidateWalk.getState());
  await page.screenshot({path:'/workspace/race-browser-mobile-walk.png'});
  await page.click('[data-exit]');await page.waitForFunction(()=>!window.candidateWalk.getState().active);
  const report={full,lod,walk,boundary,returnedToInspector:true,downloadLinks:4,mobileViewport:[390,844],mobileWalk,errors};
  fs.writeFileSync('/workspace/race-browser.json',JSON.stringify(report,null,2)+'\n');
  if(errors.length)throw Error(JSON.stringify(errors));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
