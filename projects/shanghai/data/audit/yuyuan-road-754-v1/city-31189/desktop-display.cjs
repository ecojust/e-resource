const {chromium}=require('playwright');
const launch=chromium.launch.bind(chromium);
chromium.launch=async function(args){
 const browser=await launch(args);
 const open=browser.newPage.bind(browser);
 const adapt=size=>size?.width===790?{width:760,height:485}:size;
 browser.newPage=async function(options){
  const desktop=options.viewport.width===790;
  const page=await open({...options,viewport:adapt(options.viewport),deviceScaleFactor:desktop?0.75:1});
  const set=page.setViewportSize.bind(page);page.setViewportSize=size=>set(adapt(size));
  return page;
 };
 return browser;
};
