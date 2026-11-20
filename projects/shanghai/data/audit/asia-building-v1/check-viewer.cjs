/* Check the real single-building entry, both meshes and the initial southeast viewpoint. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(__dirname, '../../..');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const output = process.env.QA_OUTPUT_DIR || __dirname;
const pageFile = 'asia-building.html';
const moduleFile = 'src/candidate-asset-viewer.js';
const moduleKey = moduleFile + '?v=asia-building-v1';
const assetDir = 'assets/models/candidates/huangpu-asia-building/';
const local = file => fs.readFileSync(path.join(project,file));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const manifestBytes = local(assetDir+'manifest.json');
const manifest = JSON.parse(manifestBytes);
const report = {model:manifest.id, started:new Date().toISOString(), base, completed:false,
  script_sha256:digest(fs.readFileSync(__filename)), screenshots:[], files:{}, downloads:{}, errors:[]};
const reportPath = path.join(output,'viewer.json');
const save = () => fs.writeFileSync(reportPath, JSON.stringify(report,null,2)+'\n');

async function main() {
  fs.mkdirSync(output,{recursive:true});
  assert(!fs.existsSync(reportPath),'Use a fresh output directory');
  const browser = await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  report.browser = browser.version();
  try {
    for (const mode of ['desktop', 'mobile', 'previous-framing-comparison']) {
      const mobile=mode==='mobile', compare=mode==='previous-framing-comparison';
      const viewport=mobile?{width:390,height:844}:{width:1100,height:760};
      const page=await browser.newPage({viewport,hasTouch:mobile,isMobile:mobile});
      page.setDefaultTimeout(180000);
      page.on('pageerror',e=>report.errors.push(e.message));
      page.on('response',r=>{if(r.status()>=400)report.errors.push(r.status()+' '+r.url());});
      const table = new Map();
      page.on('response',response=>{
        const url=new URL(response.url());
        table.set(url.pathname.slice(1)+url.search,response);
      });
      // Only the comparison page omits the new angle. The desktop/mobile runs use actual served bytes.
      if(compare) await page.route(new URL(pageFile,base).href,async route=>{
        const response=await route.fetch(); const text=await response.text();
        assert(text.includes(' data-oblique-x="2.2"'));
        await route.fulfill({response,body:text.replace(' data-oblique-x="2.2"','')});
      });
      await page.goto(new URL(pageFile,base).href,{waitUntil:'domcontentloaded'});
      const ready=prefix=>page.waitForFunction(prefix=>document.getElementById('status').textContent.startsWith(prefix+' ·'),prefix);
      await ready('近景');
      assert.equal(await page.locator('#model-view').getAttribute('data-oblique-x'),compare?null:'2.2');
      assert.equal(await page.locator('#downloads a').count(),4);
      const check = async (key,expected) => {
        const r=table.get(key); assert(r,key); assert(r.ok(),key);
        const bytes=await r.body();assert.equal(digest(bytes),expected,key);
        report.files[key]={sha256:expected,bytes:bytes.length};
      };
      if(!compare) await check(pageFile,digest(local(pageFile)));
      await check(moduleKey,digest(local(moduleFile)));
      await check(assetDir+'manifest.json',digest(manifestBytes));
      await check(assetDir+manifest.assets.full.file,manifest.assets.full.sha256);
      const capture=async view=>{
        const file='viewer-'+mode+'-'+view+'.png';
        const bytes=await page.screenshot({path:path.join(output,file),timeout:180000});
        report.screenshots.push({mode,view,file,viewport,sha256:digest(bytes),bytes:bytes.length,status:await page.locator('#status').innerText()});save();
      };
      await capture('initial');
      if(!compare){
        const action=async key=>{const button=page.locator('[data-view="'+key+'"]');if(mobile)await button.tap();else await button.click();};
        await action('front'); await capture('front');
        await action('above'); await capture('roof');
        await page.locator('#detail').selectOption('lod');await ready('远景');
        await check(assetDir+manifest.assets.lod.file,manifest.assets.lod.sha256);
        await action('oblique');await capture('lod');
        if(!mobile) for(const [role,asset] of Object.entries(manifest.assets)){
          const link=page.locator('#downloads a').filter({hasText:{raw:'原始',full:'网页',lod:'远景',native:'Blender'}[role]});
          const pending=page.waitForEvent('download'); await link.click();
          const download=await pending;assert.equal(download.suggestedFilename(),asset.file);
          const bytes=fs.readFileSync(await download.path());assert.equal(digest(bytes),asset.sha256);assert.equal(bytes.length,asset.bytes);
          report.downloads[role]={file:asset.file,bytes:bytes.length,sha256:digest(bytes)};
        }
      }
      await page.close();
    }
    assert.deepEqual(report.errors,[]);report.completed=true;
  } catch(error){report.failure=error.stack;throw error;}
  finally{await browser.close();report.finished=new Date().toISOString();save();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
