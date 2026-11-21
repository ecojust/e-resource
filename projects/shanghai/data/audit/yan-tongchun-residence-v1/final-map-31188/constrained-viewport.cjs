// The browser context retains the CSS layout of a small desktop; recorded pixels and all model requests are real.
const { createRequire } = require('node:module');
const resolveFromChecker=createRequire(__dirname+'/check-independent-city.cjs');
const {chromium}=resolveFromChecker('playwright');
const original=chromium.launch.bind(chromium);
chromium.launch=async function(options){
  const browser=await original(options);
  const newPage=browser.newPage.bind(browser);
  browser.newPage=async function(settings){
    let viewport=settings.viewport;
    if(viewport.width===960 && viewport.height===700){viewport={width:790,height:510};}
    const page=await newPage({...settings,viewport});
    const setViewportSize=page.setViewportSize.bind(page);
    page.setViewportSize=async v=>setViewportSize(v.width===960 && v.height===700?{width:790,height:510}:v);
    return page;
  };
  return browser;
};
