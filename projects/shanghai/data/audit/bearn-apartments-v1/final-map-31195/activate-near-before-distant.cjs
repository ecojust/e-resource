const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {chromium}=require('playwright');
(async()=>{
  const browser=await chromium.connectOverCDP('http://127.0.0.1:19595');
  const page=browser.contexts()[0].pages()[0];
  const snapshot=()=>page.evaluate(()=>{
    const s=window.__SHANGHAI_APP__.scene;
    const a=s.getLandmarkAssetState('huangpu-bearn-apartments');
    return {site:location.href,zoom:s.map.getZoom(),viewport:[innerWidth,innerHeight],variant:a?.variant,
      asset:a?.verifiedAsset?.sha256,near:s.getStreamingState().detail.active.map(c=>c.id)};
  });
  const before=await snapshot();
  if(!before.site.startsWith('http://127.0.0.1:31195/index.html#landmark=huangpu-bearn-apartments')||before.variant!=='full')throw Error('Wrong site or model');
  const label=await page.locator('#zoom-in').getAttribute('aria-label');
  await page.locator('#zoom-in').click();
  await page.waitForFunction(v=>window.__SHANGHAI_APP__.scene.map.getZoom()>v+.04,before.zoom);
  const after=await snapshot();
  const receipt={before,control:label,after,checkedAt:new Date().toISOString(),
    driverSHA256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex')};
  fs.writeFileSync(path.join(__dirname,'distant','operator-zoom.json'),JSON.stringify(receipt,null,2)+'\n');
  process.exit(0);
})().catch(error=>{console.error(error);process.exit(1)});
