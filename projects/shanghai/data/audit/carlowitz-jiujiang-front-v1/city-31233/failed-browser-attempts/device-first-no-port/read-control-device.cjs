const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict'), crypto=require('node:crypto');
const {chromium}=require('./cdp-city-page-233.cjs');
const root=__dirname, out=path.join(root,'control-device-followup'), source=fs.readFileSync(path.join(root,'fifth-control-composited/control/control-browser.json'));
const map=JSON.parse(source);const first=map.compositorFrame;assert(first.cameraAtRead.visibleGroup);
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--single-process','--in-process-gpu','--no-zygote','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-extensions','--disable-background-networking','--num-raster-threads=1','--enable-low-end-device-mode','--disk-cache-size=2097152']});
 const start=new Date().toISOString();const st=fs.readFileSync('/proc/'+browser.physicalPid+'/stat','utf8').split(') ')[1].split(' ')[19];
 try {
 const page=await browser.newPage({viewport:{width:570,height:445},deviceScaleFactor:.5,hasTouch:false});const cdp=await page.context().newCDPSession(page);
 await cdp.send('Emulation.setHardwareConcurrencyOverride',{hardwareConcurrency:1});
 await page.addInitScript(()=>Object.defineProperty(Navigator.prototype,'deviceMemory',{get:()=>2,configurable:true}));
 await page.goto(map.server+'landmarks.html',{waitUntil:'domcontentloaded'});await page.locator('.landmark-card[data-landmark]').first().waitFor({timeout:30000});
 const data=await page.evaluate(()=>({url:location.href,touchPoints:navigator.maxTouchPoints,viewport:[innerWidth,innerHeight],count:document.querySelectorAll('.landmark-card[data-landmark]').length,memory:navigator.deviceMemory,cores:navigator.hardwareConcurrency,dpr:devicePixelRatio}));
 assert.equal(data.url,map.server+'landmarks.html');assert.equal(data.count,map.catalog.count);assert.equal(data.touchPoints,0);assert.equal(data.memory,2);assert.equal(data.cores,1);assert.equal(data.dpr,.5);assert.deepEqual(data.viewport,first.cameraAtRead.cssViewport);
 await browser.close();const exit=await browser.physicalExit();assert.deepEqual(exit,{code:0,signal:null});
 fs.writeFileSync(path.join(out,'input-device.json'),JSON.stringify({passed:true,node_pid:process.pid,chromium_pid:browser.physicalPid,birth:st,browser:browser.version(),exit,started:start,finished:new Date().toISOString(),inputDevice:data,source_map_session_sha256:crypto.createHash('sha256').update(source).digest('hex')},null,2)+'\n');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
