/* Visit the public front and portico buttons after the city camera review. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');
const hash = data => createHash('sha256').update(data).digest('hex');
const out = process.argv[2];
const base = 'http://127.0.0.1:31271/';
const production = JSON.parse(fs.readFileSync('/tmp/shanghai-main-271/271-production.json'));
const pageFile = 'central-trust-beijing-front.html';
const root = 'assets/models/candidates/huangpu-central-trust-beijing-front/';
const record = {url: base+pageFile, written: new Date().toISOString(), frames:[], responses:[], errors:[]};
async function main() {
  fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--num-raster-threads=1','--enable-low-end-device-mode']});
  try {
    for (const [device,viewport] of Object.entries({desktop:{width:1060,height:750},phone:{width:390,height:844}})){
      const isPhone=device==='phone';
      const context=await browser.newContext({viewport,isMobile:isPhone,hasTouch:isPhone,deviceScaleFactor:1});
      const page=await context.newPage();
      page.on('pageerror',e=>record.errors.push(String(e)));
      await page.addInitScript(()=>document.addEventListener('pointerup',e=>{
        const button=e.target.closest?.('[data-view]');if(button)window.lastExteriorAction={view:button.dataset.view,trusted:e.isTrusted,type:e.pointerType};
      },true));
      const manifestPending=page.waitForResponse(r=>r.url()===base+root+'manifest.json');
      const meshPending=page.waitForResponse(r=>r.url().startsWith(base+root)&&r.url().endsWith('-web.glb'));
      const pageResponse=await page.goto(base+pageFile,{waitUntil:'domcontentloaded',timeout:60000});
      for(const response of [pageResponse,await manifestPending,await meshPending]){
        const file=response.url().slice(base.length),body=await response.body();
        assert.equal(response.status(),200);assert.equal(hash(body),production.files[file],file);
        record.responses.push({device,file,bytes:body.length,sha256:hash(body)});
      }
      await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('近景 ·'));
      const frames=[];
      for (const view of ['front','oblique']){
        const button=page.locator('button[data-view="'+view+'"]');
        if(isPhone)await button.tap();else await button.click();
        await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
        const operation=await page.evaluate(()=>window.lastExteriorAction);
        assert.deepEqual(operation,{view,trusted:true,type:isPhone?'touch':'mouse'});
        const canvas=page.locator('#model-view canvas');
        const canvasState=await canvas.evaluate(c=>{const gl=c.getContext('webgl2');return {width:c.width,height:c.height,gl:gl?.getParameter(gl.VERSION),lost:gl?.isContextLost()};});
        assert.ok(canvasState.gl?.startsWith('WebGL 2')&&!canvasState.lost);
        const name=device+'-'+view+'.png';
        const bytes=await page.screenshot({path:path.join(out,name)});
        const crop=await canvas.screenshot({path:path.join(out,device+'-'+view+'-canvas.png')});
        frames.push(hash(crop));
        record.frames.push({device,view,button:await button.innerText(),operation,viewport,canvasState,file:name,sha256:hash(bytes),canvas:device+'-'+view+'-canvas.png',canvas_sha256:hash(crop)});
      }
      assert.notEqual(frames[0],frames[1]);await context.close();
    }
    assert.equal(record.frames.length,4);assert.deepEqual(record.errors,[]);record.passed=true;
  }finally {
    await browser.close();record.closed=!browser.isConnected();record.finished=new Date().toISOString();fs.writeFileSync(path.join(out,'exterior-views.json'),JSON.stringify(record,null,2)+'\n');
  }
}
main().catch(e=>{console.error(e);process.exitCode=1});
