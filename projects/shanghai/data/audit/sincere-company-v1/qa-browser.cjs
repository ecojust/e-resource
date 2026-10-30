/* Actual WebGL variants, downloads and desktop/touch outdoor walking. MIT. */
const {chromium}=require('playwright');
const fs=require('fs');
const path=require('path');
const {createHash}=require('crypto');
// Candidate-specific limits for the wide historic main building.
const expectedWalk={modelExtentLimit:60,walkLimit:80};

(async()=>{
 const output=process.env.QA_OUTPUT_DIR||__dirname;
 fs.mkdirSync(output,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000},hasTouch:true});const errors=[];
  page.on('console',m=>{if(m.type()==='error'){errors.push(m.text());console.error(m.text());}});
  page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});
  page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('favicon.svg'))errors.push(`${r.status()} ${r.url()}`);});
  await page.goto(process.env.MODEL_URL||'http://127.0.0.1:8782/sincere-company.html');
  const ready=async variant=>{
   await page.waitForFunction(v=>window.sincereCompanyViewer?.getState().status==='error'||(window.sincereCompanyViewer?.getState().status==='ready'&&window.sincereCompanyViewer.getState().variant===v),variant,{timeout:90000});
   const state=await page.evaluate(()=>window.sincereCompanyViewer.getState());
   if(state.status!=='ready'||state.variant!==variant)throw Error(JSON.stringify({state,errors}));
  };
  const screenshot=name=>page.screenshot({path:path.join(output,`browser-${name}.png`)});
  const assertFits=(framing,label)=>{
   const b=framing?.screenBounds;
   if(!b||b.minX<-.96||b.maxX>.96||b.minY<-.96||b.maxY>.96||b.minZ<0||b.maxZ>1)throw Error(`${label} model framing failed: ${JSON.stringify(framing)}`);
  };
  await ready('full');const full=await page.evaluate(()=>window.sincereCompanyViewer.getState());
  if(full.modelId!=='huangpu-sincere-company'||!(full.renderedTriangles>0))throw Error('full model identity or rendering failed');
  await page.click('#front');await screenshot('front');
  await page.click('#rear');await screenshot('rear');
  await page.selectOption('#detail','lod');await ready('lod');const lod=await page.evaluate(()=>window.sincereCompanyViewer.getState());
  if(lod.triangles>=full.triangles||lod.modelId!==full.modelId)throw Error('LOD identity or reduction failed');
  await screenshot('lod');
  await page.selectOption('#detail','full');await ready('full');await page.click('#oblique');await screenshot('oblique');
  const desktopFraming=await page.evaluate(()=>window.sincereCompanyViewer.getState().framing);assertFits(desktopFraming,'desktop');
  await page.click('#enter-model-walk');await page.waitForFunction(()=>window.candidateWalk.getState().active);
  const initialWalk=await page.evaluate(async()=>{
   const {blockedAt}=await import('./src/candidate-walk-motion.js');
   const state=window.candidateWalk.getState();
   return {...state,startBlocked:blockedAt(state.position.x,state.position.z,state.bounds,undefined,state.walkLimit),frontClearance:state.position.z-state.bounds.maxZ};
  });
  if(initialWalk.startBlocked||initialWalk.distance!==0||initialWalk.frontClearance<5.9)throw Error('initial outdoor walking position failed');
  await page.keyboard.down('w');await page.waitForFunction(()=>window.candidateWalk.getState().distance>.05,null,{timeout:30000});await page.keyboard.up('w');
  await page.waitForFunction(()=>window.candidateWalk.getState().keys.length===0);
  const walk=await page.evaluate(()=>window.candidateWalk.getState());
  if(!(walk.distance>0)||walk.geographicRegistration!==false||walk.walkLimit!==expectedWalk.walkLimit||walk.modelExtentLimit!==expectedWalk.modelExtentLimit)throw Error('wide-model outdoor walking configuration failed');
  const released=await page.evaluate(async()=>{
   const before=window.candidateWalk.getState();
   await new Promise(resolve=>{let frames=0;const step=()=>++frames===8?resolve():requestAnimationFrame(step);requestAnimationFrame(step);});
   const after=window.candidateWalk.getState();
   return {keys:after.keys,distanceBefore:before.distance,distanceAfter:after.distance};
  });
  if(released.keys.length||released.distanceAfter!==released.distanceBefore)throw Error('keyboard release did not stop walking');
  const boundary=await page.evaluate(async()=>{
   const {moveOutside,blockedAt}=await import('./src/candidate-walk-motion.js');
   const {bounds,walkLimit}=window.candidateWalk.getState();
   const start={x:47,z:bounds.maxZ+6};
   const beyondDefaultLimit=moveOutside(start,5,0,bounds,walkLimit);
   const stopped=moveOutside({x:walkLimit-1,z:bounds.maxZ+6},5,0,bounds,walkLimit);
   return {walkLimit,beyondDefaultLimit,stopped,defaultBlocks:blockedAt(start.x,start.z,bounds),configuredAllows:!blockedAt(start.x,start.z,bounds,undefined,walkLimit),outsideBlocked:blockedAt(walkLimit+.1,bounds.maxZ+6,bounds,undefined,walkLimit),insideModelBlocked:blockedAt((bounds.minX+bounds.maxX)/2,(bounds.minZ+bounds.maxZ)/2,bounds,undefined,walkLimit)};
  });
  if(!(boundary.beyondDefaultLimit.x>51.9&&boundary.stopped.x<=boundary.walkLimit&&boundary.stopped.x>boundary.walkLimit-.2&&boundary.defaultBlocks&&boundary.configuredAllows&&boundary.outsideBlocked&&boundary.insideModelBlocked))throw Error('configured walking boundary failed');
  await page.keyboard.press('Escape');await page.waitForFunction(()=>!window.candidateWalk.getState().active&&!document.body.classList.contains('candidate-walking'));
  const manifestResponse=await page.request.get(new URL('assets/models/candidates/huangpu-sincere-company/manifest.json',page.url()).href);
  if(!manifestResponse.ok())throw Error('download manifest unavailable');
  const manifest=await manifestResponse.json();
  const links=await page.locator('#downloads a').evaluateAll(nodes=>nodes.map(node=>({role:node.dataset.role,url:node.href,download:node.hasAttribute('download')})));
  if(links.length!==4||new Set(links.map(link=>link.role)).size!==4)throw Error('four download roles missing');
  const downloads=[];
  for(const role of ['raw','full','lod','native']){
   const link=links.find(link=>link.role===role),record=manifest.assets[role];
   if(!link?.download||new URL(link.url).pathname.split('/').pop()!==record.file)throw Error(`download link mismatch: ${role}`);
   const response=await page.request.get(link.url);if(!response.ok())throw Error(`download unavailable: ${role}`);
   const bytes=await response.body(),sha256=createHash('sha256').update(bytes).digest('hex');
   if(bytes.length!==record.bytes||sha256!==record.sha256||bytes.length>=100000000)throw Error(`download metadata mismatch: ${role}`);
   downloads.push({role,file:record.file,bytes:bytes.length,sha256,verified:true});
  }
  await page.setViewportSize({width:390,height:844});await ready('full');await screenshot('mobile');
  const mobileFraming=await page.evaluate(()=>window.sincereCompanyViewer.getState().framing);assertFits(mobileFraming,'mobile');
  const mobileLayout=await page.evaluate(()=>({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,canvasWidth:document.querySelector('canvas').getBoundingClientRect().width,canvasHeight:document.querySelector('canvas').getBoundingClientRect().height}));
  if(mobileLayout.scrollWidth>mobileLayout.viewport||mobileLayout.canvasWidth<300||mobileLayout.canvasHeight<200)throw Error('mobile viewport layout failed');
  await page.click('#enter-model-walk');await page.waitForFunction(()=>window.candidateWalk.getState().active);
  const pad=await page.locator('.walk-pad [data-key="w"]').boundingBox();
  const touch=await page.context().newCDPSession(page);
  await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:pad.x+pad.width/2,y:pad.y+pad.height/2}]});
  await page.waitForFunction(()=>window.candidateWalk.getState().distance>.05,null,{timeout:30000});
  await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await page.waitForFunction(()=>window.candidateWalk.getState().keys.length===0);
  const mobileWalk=await page.evaluate(()=>window.candidateWalk.getState());await screenshot('mobile-walk');
  await page.click('[data-exit]');await page.waitForFunction(()=>!window.candidateWalk.getState().active);
  if(errors.length)throw Error(JSON.stringify(errors));
  const report={modelId:full.modelId,full,lod,desktopFraming,initialWalk,walk,released,boundary,returnedToInspector:true,downloadLinks:4,downloads,mobileViewport:[390,844],mobileLayout,mobileFraming,mobileWalk,errors};
  fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify(report,null,2)+'\n');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
