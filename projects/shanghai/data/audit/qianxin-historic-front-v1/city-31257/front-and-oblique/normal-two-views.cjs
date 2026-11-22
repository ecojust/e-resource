const {chromium}=require('playwright-core'),fs=require('node:fs'),assert=require('node:assert/strict'),crypto=require('node:crypto'),cp=require('node:child_process');
const digest=data=>crypto.createHash('sha256').update(data).digest('hex');
async function main(){
 const mobile=process.argv[2]==='phone',device=mobile?'phone':'desktop',viewport=mobile?{width:390,height:620}:{width:790,height:510};
 const origin='http://127.0.0.1:31257/',route='qianxin-six-arches-history.html',id='huangpu-qianxin-building-historic-front';
 const r={device,viewport,id,route,port:31257,started:new Date().toISOString(),driver_sha256:digest(fs.readFileSync(__filename)),inputs:[],captures:[],responses:[],errors:[]};
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--no-zygote','--single-process','--in-process-gpu','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--disk-cache-size=1048576','--disable-gpu-shader-disk-cache']});
 try {
  const page=await browser.newPage({viewport,isMobile:mobile,hasTouch:mobile,deviceScaleFactor:1,locale:'zh-CN'});
  await page.exposeFunction('recordNativeInput',data=>r.inputs.push(data));
  await page.addInitScript(()=>document.addEventListener('pointerup',ev=>{const b=ev.target.closest('[data-view]');if(b)window.recordNativeInput({view:b.dataset.view,trusted:ev.isTrusted,device:ev.pointerType,x:ev.clientX,y:ev.clientY})},true));
  page.on('pageerror',e=>r.errors.push(e.message));page.on('response',res=>{const url=new URL(res.url());if(url.origin===origin.replace(/\/$/,''))r.responses.push({path:url.pathname.slice(1),status:res.status()});});
  await page.goto(origin+route,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>document.querySelector('#status')?.textContent.includes('近景'),null,{timeout:90000});
  const canvas=page.locator('#model-view canvas');r.geometry_status=await page.locator('#status').innerText();
  for(const view of ['front','oblique']){
    const button=page.locator('[data-view="'+view+'"]');const text=await button.innerText();
    if(mobile)await button.tap();else await button.click();
    await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(done)))));
    await page.waitForTimeout(420);
    const box=await canvas.boundingBox(),x=Math.max(0,Math.ceil(box.x)),y=Math.max(0,Math.ceil(box.y));
    assert.ok(box.width>200 && box.height>110);const w=Math.min(viewport.width-x,Math.floor(box.x+box.width)-x),h=Math.min(viewport.height-y,Math.floor(box.y+box.height)-y);
    const file=device+'-'+view+'.png',bytes=await page.screenshot({path:file,timeout:22000,animations:'disabled'});r.captures.push({file,view,button:text,bytes:bytes.length,sha256:digest(bytes),canvas_rect:[x,y,w,h]});
  }
  assert.deepEqual(r.captures[0].canvas_rect,r.captures[1].canvas_rect);r.display_difference=JSON.parse(cp.execFileSync('python',['verify-pixels.py',...r.captures.map(i=>i.file),...r.captures[0].canvas_rect.map(String)],{encoding:'utf8'}));
  assert.ok(r.display_difference.changed>1000 && r.display_difference.foreground.every(x=>x>900));assert.deepEqual(r.inputs.map(x=>[x.view,x.trusted,x.device]),[['front',true,mobile?'touch':'mouse'],['oblique',true,mobile?'touch':'mouse']]);assert.deepEqual(r.errors,[]);r.completed=true;
 } finally{await browser.close();r.browser_closed=true;r.finished=new Date().toISOString();fs.writeFileSync(device+'-viewer.json',JSON.stringify(r,null,2)+'\n');}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
