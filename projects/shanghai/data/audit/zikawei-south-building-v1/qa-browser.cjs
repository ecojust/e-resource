const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});let errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.ZIKAWEI_URL||'http://127.0.0.1:8000/zikawei-library.html');
 const ready=async v=>page.waitForFunction(v=>window.zikaweiViewer?.getState().status==='ready'&&window.zikaweiViewer.getState().variant===v,v,{timeout:60000});
 await ready('full');console.log('initial full');let report={full:await page.evaluate(()=>window.zikaweiViewer.getState())};
 if(report.full.actualTriangles!==150176||report.full.textures.length!==4||Math.abs(report.full.normalScale[0]-.35)>1e-7||Math.abs(report.full.normalScale[1]+.35)>1e-7)throw Error('Full geometry or PBR absent');
 const out=__dirname+'/';
 await page.screenshot({path:out+'browser-desktop.png',timeout:30000});
 await page.selectOption('#detail','lod');await ready('lod');console.log('manual lod');report.lod=await page.evaluate(()=>window.zikaweiViewer.getState());if(report.lod.actualTriangles!==23140||report.lod.textures.length!==4)throw Error('LOD geometry or PBR absent');
 await page.selectOption('#detail','full');await ready('full');
 await page.route('**/*-lod.glb',r=>r.fulfill({status:200,body:'corrupt'}));
 await page.selectOption('#detail','lod');await page.waitForFunction(()=>window.zikaweiViewer.getState().status==='error');console.log('corrupt rejected');report.corrupt=await page.evaluate(()=>window.zikaweiViewer.getState());
 if(report.corrupt.variant!=='full')throw Error('Previous model lost');
 await page.unroute('**/*-lod.glb');await page.click('#retry');await ready('lod');report.retry=true;console.log('retry passed');
 await page.selectOption('#detail','auto');await ready('full');
 await page.locator('canvas').hover();await page.mouse.wheel(0,2500);await page.waitForTimeout(1000);
 // Multiple wheel events are needed because OrbitControls applies a capped step per event.
 for(let i=0;i<35;i++){await page.mouse.wheel(0,200);await page.waitForTimeout(30);}
 console.log('after wheels',await page.evaluate(()=>window.zikaweiViewer.getState()));await ready('lod');report.autoFar=await page.evaluate(()=>window.zikaweiViewer.getState());
 await page.click('#fit');await ready('full');report.autoNear=await page.evaluate(()=>window.zikaweiViewer.getState());
 for(const v of ['front','rear','oblique']){await page.click('#'+v);await page.screenshot({path:out+'browser-'+v+'.png',timeout:30000});}
 await page.setViewportSize({width:390,height:844});await ready('full');await page.screenshot({path:out+'browser-mobile.png',timeout:30000});
 report.mobileOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);report.errors=errors;
 if(errors.length||report.mobileOverflow)throw Error(JSON.stringify(report));
 fs.writeFileSync(out+'browser.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
