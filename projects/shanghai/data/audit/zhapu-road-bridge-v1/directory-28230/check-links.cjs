/* Check the delivered catalog's ordinary links in Chromium without starting a WebGL map.
   The map controller and avatar are measured separately in real-map-current.cjs. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {chromium}=require('playwright');
const dir=__dirname;
const read = f => JSON.parse(fs.readFileSync(path.join(dir,f)));
const pins=read('http-controls.json').stages;
const id='huangpu-zhapu-road-bridge';
const hash = b=>crypto.createHash('sha256').update(b).digest('hex');
const outcome={passed:false,scope:'真实前后目录和导航动作。此轻量运行关闭页面脚本，仅验证浏览器加载正确的正式入口；地图与角色另有排期。',views:[]};
const save=()=>fs.writeFileSync(path.join(dir,'actual-link-actions.json'),JSON.stringify(outcome,null,2)+'\n');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--disk-cache-size=1048576','--renderer-process-limit=1','--disable-background-networking']});
 try{
  for(const device of ['keyboard','touch']){
   const mobile=device==='touch';
   const ctx=await browser.newContext({javaScriptEnabled:false,viewport:mobile?{width:390,height:844}:{width:870,height:660},hasTouch:mobile,isMobile:mobile});
   try{
    const page=await ctx.newPage();
    const negative=await page.goto('http://127.0.0.1:'+pins[229].port+'/landmarks.html',{waitUntil:'domcontentloaded'});
    assert.equal(negative.status(),200);assert.equal(hash(await negative.body()),pins[229].requests['landmarks.html'].sha256);
    assert.equal(await page.locator('article[data-landmark]').count(),266);
    assert.equal(await page.locator('article[data-landmark="'+id+'"]').count(),0);
    const base='http://127.0.0.1:'+pins[230].port+'/';
    const response=await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});
    assert.equal(response.status(),200);assert.equal(hash(await response.body()),pins[230].requests['landmarks.html'].sha256);
    assert.equal(await page.locator('article[data-landmark]').count(),267);
    const link=page.locator('article[data-landmark="'+id+'"] .card-foot a[href$="mode=walk"]');
    const href=await link.getAttribute('href'),text=await link.innerText();
    assert.equal(href,'index.html#landmark='+id+'&mode=walk');
    const dest=page.waitForResponse(r=>r.request().isNavigationRequest()&&new URL(r.url()).pathname==='/index.html');
    if(mobile){await link.tap();}else{await link.focus();await page.keyboard.press('Enter');}
    const target=await dest;await page.waitForURL(base+href);
    assert.equal(target.status(),200);assert.equal(hash(await target.body()),pins[230].requests['index.html'].sha256);
    assert.equal(await page.locator('#joystick[aria-label="拖动摇杆行走"]').count(),1);
    assert.equal(await page.locator('#touch-run').count(),1);assert.equal(await page.locator('#start-walk').count(),1);
    outcome.views.push({device,viewport:page.viewportSize(),before:{count:266,entry:false,sign:pins[229].signature},after:{count:267,sign:pins[230].signature},label:text,action:mobile?'physical touch tap':'keyboard Enter on focused ordinary walk link',target:page.url(),status:target.status(),http_sha256:hash(await target.body())});save();
   }finally{await ctx.close();}
  }
  outcome.passed=true;
 }finally{await browser.close();outcome.closed=true;save();}
})().catch(e=>{outcome.failure=e.stack;save();process.exitCode=1;});
