/* Actual WebGL load, variants, camera controls and local outdoor walking. MIT. */
const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];
 page.on('console',m=>{if(m.type()==='error')console.error(m.text())});page.on('pageerror',e=>{errors.push(e.message);console.error(e.message)});page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('favicon.svg'))errors.push(`${r.status()} ${r.url()}`)});
 await page.goto(process.env.MODEL_URL||'http://127.0.0.1:8782/park-hotel.html');
 const ready=async v=>{await page.waitForFunction(v=>window.parkHotelViewer?.getState().status==='error'||(window.parkHotelViewer?.getState().status==='ready'&&window.parkHotelViewer.getState().variant===v),v,{timeout:90000});const state=await page.evaluate(()=>parkHotelViewer.getState());if(state.status!=='ready'||state.variant!==v)throw Error(JSON.stringify({state,errors}));};
 await ready('full');const full=await page.evaluate(()=>parkHotelViewer.getState());
 if(full.modelId!=='huangpu-park-hotel')throw Error('wrong model identity');
 await page.click('#front');await page.screenshot({path:'/workspace/park-browser-front.png'});
 await page.click('#rear');await page.screenshot({path:'/workspace/park-browser-rear.png'});
 await page.selectOption('#detail','lod');await ready('lod');const lod=await page.evaluate(()=>parkHotelViewer.getState());
 if(lod.triangles>=full.triangles)throw Error('LOD failed');
 await page.screenshot({path:'/workspace/park-browser-lod.png'});
 await page.selectOption('#detail','full');await ready('full');await page.click('#oblique');
 await page.screenshot({path:'/workspace/park-browser-oblique.png'});
 await page.click('#enter-model-walk');await page.waitForFunction(()=>document.body.classList.contains('candidate-walking'));
 await page.keyboard.down('w');await page.waitForFunction(()=>window.candidateWalk.getState().distance>.05,null,{timeout:30000});await page.keyboard.up('w');
 const walk=await page.evaluate(()=>window.candidateWalk.getState());
 if(!(walk.distance>0)||walk.geographicRegistration!==false)throw Error('outdoor walking failed');
 await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.body.classList.contains('candidate-walking'));
 if(await page.locator('#downloads a').count()!==4)throw Error('downloads missing');
 await page.setViewportSize({width:390,height:844});await ready('full');
 await page.screenshot({path:'/workspace/park-browser-mobile.png'});
 const report={full,lod,walk,returnedToInspector:true,downloadLinks:4,mobileViewport:[390,844],errors};
 fs.writeFileSync('/workspace/park-browser.json',JSON.stringify(report,null,2)+'\n');await browser.close();if(errors.length)throw Error(JSON.stringify(errors));
})().catch(e=>{console.error(e);process.exit(1)});
