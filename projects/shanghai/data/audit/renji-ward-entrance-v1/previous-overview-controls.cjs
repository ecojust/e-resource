/* Switch the original site's walking default to overview before restoring the measured camera. */
const fs=require('node:fs');
const {chromium}=require('playwright');
(async()=>{
 const [port,cameraFile,reportFile]=process.argv.slice(2);
 const browser=await chromium.connectOverCDP('http://127.0.0.1:'+port);
 const page=browser.contexts()[0].pages().find(p=>p.url().includes('15079'));
 await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene),null,{timeout:300000});
 const before=await page.evaluate(()=>window.__SHANGHAI_APP__.mode);
 if(before==='walk')await page.locator('#overview-mode').click({timeout:90000});
 const camera=JSON.parse(fs.readFileSync(cameraFile));
 const state=await page.evaluate(c=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map;
   m.stop();m.setCenterClampedToGround(false);m.jumpTo({center:c.center,padding:c.padding,elevation:c.elevation,zoom:c.zoom,bearing:c.bearing,pitch:c.pitch});
   s.loadLandmarks();s.refreshBuildingBeacons();return {mode:a.mode,center:m.getCenter().toArray(),padding:m.getPadding()};
 },camera);
 fs.writeFileSync(reportFile,JSON.stringify({before,state,time:new Date().toISOString()},null,2)+'\n');process.exit(0);
})().catch(e=>{console.error(e);process.exit(1)});
