/* When the initial right drag flattens the public map, restore a streetward tilt using the same button. */
const {chromium}=require('playwright');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.connectOverCDP(process.env.QA_CDP_URL);
 const page=browser.contexts()[0].pages()[0];
 const get=()=>page.evaluate(()=>{const m=window.__SHANGHAI_APP__.scene.map;return {pitch:m.getPitch(),zoom:m.getZoom(),bearing:m.getBearing(),center:m.getCenter()};});
 const start=[685,425],end=[685,297];
 const result={url:page.url(),before:await get(),action:{type:'right-drag',from:start,to:end}};
 await page.mouse.move(...start);await page.mouse.down({button:'right'});await page.mouse.move(...end,{steps:6});await page.waitForTimeout(150);await page.mouse.up({button:'right'});
 await page.waitForTimeout(450);await page.waitForFunction(()=>!window.__SHANGHAI_APP__.scene.map.isMoving(),null,{timeout:90000});
 result.after=await get();fs.writeFileSync(process.env.QA_RESULT,JSON.stringify(result,null,2)+'\n');
 if(result.after.pitch<35)throw Error('streetward tilt failed');
 process.exit(0);
})().catch(error=>{console.error(error);process.exit(1)});
