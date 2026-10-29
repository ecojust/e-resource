const {chromium}=require('playwright');
const fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
 const base=process.argv[2]||'http://127.0.0.1:8000/', label=process.argv[3]||'local';
 const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try {
  const p=await b.newPage({viewport:{width:390,height:844}}),errors=[],failures=[];
  p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)failures.push({url:r.url(),status:r.status()})});
  const consent=async()=>{const link=p.getByText('Open the page',{exact:true});if(await link.count())await link.click()};
  await p.goto(base+'landmarks.html');await consent();await p.waitForSelector('.directory-search:not([hidden])');
  assert.equal(await p.locator('[data-landmark]').count(),38);assert.equal(await p.locator('[data-viewer]').count(),8);
  await p.fill('#landmark-search','徐家汇藏书楼');assert.equal(await p.locator('.landmark-card:visible').count(),1);
  assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await p.screenshot({path:__dirname+'/directory-'+label+'.png'});
  await p.locator('[data-viewer="xuhui-zikawei-south-building"]').click();await consent();
  await p.waitForFunction(()=>window.zikaweiViewer?.getState().status==='ready',null,{timeout:120000});
  const state=await p.evaluate(()=>window.zikaweiViewer.getState());assert.equal(state.actualTriangles,150176);
  assert.ok(p.url().endsWith('/zikawei-library.html'));assert.deepEqual(errors,[]);assert.deepEqual(failures,[]);
  fs.writeFileSync(__dirname+'/directory-'+label+'.json',JSON.stringify({base,entries:46,walkEntries:38,viewerEntries:8,searchPassed:true,mobileNoOverflow:true,clickedViewer:p.url(),state,errors,failures},null,2)+'\n');
  console.log('PASS directory search, mobile layout and actual model load',label);
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exit(1)});
