/* Check the river-facing preset through its labelled button on the published page. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');

const output = process.argv[2];
const origin = process.env.MODEL_BASE_URL;
const project = path.resolve(__dirname, '../../..');
const folder = 'assets/models/candidates/huangpu-yokohama-specie-bank/';
const route = 'yokohama-specie-bank.html';
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const manifest = JSON.parse(fs.readFileSync(path.join(project,folder,'manifest.json')));
const modulePath = 'src/candidate-asset-viewer.js';
async function run(){
  fs.mkdirSync(output,{recursive:true});
  const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const result = {id:manifest.id,origin,script_sha256:digest(fs.readFileSync(__filename)),started:new Date().toISOString(),views:[],errors:[],passed:false};
  try{
    for(const mobile of [false,true]){
      const viewport=mobile ? {width:390,height:844} : {width:1250,height:820};
      const page=await browser.newPage({viewport,hasTouch:mobile,isMobile:mobile});
      page.on('pageerror',error=>result.errors.push(error.message));
      const module=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith(modulePath));
      const mesh=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith(manifest.assets.full.file));
      const html=await page.goto(new URL(route,origin).href);
      assert.equal(digest(await html.body()),digest(fs.readFileSync(path.join(project,route))));
      assert.equal(digest(await (await module).body()),digest(fs.readFileSync(path.join(project,modulePath))));
      assert.equal(digest(await (await mesh).body()),manifest.assets.full.sha256);
      page.setDefaultTimeout(180000);
      await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('近景 ·'));
      const button=page.getByRole('button',{name:'外滩主立面'});
      await page.evaluate(()=>{
        document.addEventListener('click',event=>{
          const button=event.target.closest('[data-view]');
          if(button) window.riverViewInput={view:button.dataset.view,trusted:event.isTrusted};
        },true);
      });
      const point=await button.evaluate(el=>{
        const box=el.getBoundingClientRect(),x=box.left+box.width/2,y=box.top+box.height/2;
        return {x,y,hit:document.elementFromPoint(x,y)===el};
      });
      assert(point.hit,'Preset button has an unobstructed centre');
      if(mobile) await page.touchscreen.tap(point.x,point.y); else await page.mouse.click(point.x,point.y);
      await page.waitForFunction(()=>window.riverViewInput?.trusted && window.riverViewInput.view==='oblique');
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))));
      const file='river-'+(mobile?'mobile':'desktop')+'.png';
      const image=await page.screenshot({path:path.join(output,file)});
      result.views.push({viewport,file,sha256:digest(image),full_sha256:manifest.assets.full.sha256,button:await button.innerText(),input_point:point,native_click:await page.evaluate(()=>window.riverViewInput),status:await page.locator('#status').innerText()});
      await page.close();
    }
    assert.deepEqual(result.errors,[]);result.passed=true;
  }finally{
    await browser.close();result.finished=new Date().toISOString();
    fs.writeFileSync(path.join(output,'river-views.json'),JSON.stringify(result,null,2)+'\n');
  }
}
run().catch(error=>{console.error(error);process.exitCode=1;});
