// node tools/check-candidate-viewer.cjs <model-id> <output-directory>
// MODEL_BASE_URL points to the Shanghai site root. Requires Playwright and Chromium.
const {chromium} = require('./standalone-devtools.cjs');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:31349/';
const [id, output] = process.argv.slice(2);
if (!/^[a-z0-9]+(-[a-z0-9]+)+$/.test(id || '') || !output) {
  throw new Error('Supply a registered model id and an audit output directory');
}
const project = process.env.SHANGHAI_SIGNED_VIEWER_ROOT;
assert(project && path.isAbsolute(project));
const manifestPath = path.join(project, 'assets/models/candidates', id, 'manifest.json');
const expectedManifest = fs.readFileSync(manifestPath);
const route = JSON.parse(expectedManifest).viewer_page;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

async function check() {
  fs.mkdirSync(output, {recursive: true});
  assert.equal(id,'huangpu-jiang-twin-villas-east-garden-loggia');
  assert.equal(new URL(base).port,'31349');
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  const device=process.env.SHANGHAI_349_DEVICE;assert(['desktop','mobile'].includes(device));
  const report = {device,id, route, started: new Date().toISOString(), browser: browser.version(), base, files: {}, views: [], pageErrors: []};
  for (const name of [route, 'src/candidate-asset-viewer.js']) {
    report.files[name] = sha(fs.readFileSync(path.join(project, name)));
  }
  report.scriptSHA256 = sha(fs.readFileSync(__filename));
  try {
    for (const mobile of [process.env.SHANGHAI_349_DEVICE==='mobile']) {
      const viewport = mobile ? {width: 390, height: 844} : {width: 1250, height: 820};
      const page = await browser.newPage({viewport, hasTouch: mobile, isMobile: mobile, deviceScaleFactor:0.375});
      page.on('pageerror', e => report.pageErrors.push(e.message));
      const moduleResponse = page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/src/candidate-asset-viewer.js'));
      const manifestResponse = page.waitForResponse(r => r.url().endsWith('/manifest.json'));
      const firstModel = page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/' + JSON.parse(expectedManifest).assets.full.file));
      const html = await page.goto(new URL(route, base).href);
      assert.equal(sha(await html.body()), report.files[route]);
      assert.equal(sha(await (await moduleResponse).body()), report.files['src/candidate-asset-viewer.js']);
      assert.equal(await page.locator('#model-view').getAttribute('data-front'),'positive-z');

      assert.equal(await page.locator('[data-view="front"]').innerText(),"正看三层柱廊");
      assert.equal(await page.locator('[data-view="oblique"]').innerText(),"斜看廊深与窗扇");
      assert.equal(await page.locator('[data-view="above"]').innerText(),"俯看檐口与廊顶");
      const fullResponse=await firstModel;
      assert(fullResponse.ok());
      assert.equal(sha(await fullResponse.body()),JSON.parse(expectedManifest).assets.full.sha256);
      const response = await manifestResponse;
      const manifestBytes = await response.body();
      assert(response.ok());
      report.manifestSHA256 = sha(manifestBytes);
      const manifest = JSON.parse(manifestBytes);
      assert.equal(manifest.id, id);
      assert.equal(sha(manifestBytes), sha(expectedManifest));
      const status = page.locator('#status');
      await page.waitForFunction(() => document.getElementById('status').textContent.startsWith('近景 ·'));
      assert.equal(await page.locator('#downloads a').count(), 4);
      for (const role of ['full', 'lod']) {
        const received = role === 'lod' ? page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/' + manifest.assets.lod.file)) : null;
        await page.locator('#detail').selectOption(role);
        if (received) assert.equal(sha(await (await received).body()), manifest.assets.lod.sha256);
        const prefix = role === 'full' ? '近景' : '远景';
        await page.waitForFunction(p => document.getElementById('status').textContent.startsWith(p + ' ·'), prefix);
        const modes=role==='full'?['front','oblique']:['above'];
        for(const mode of modes) {
          const view=page.locator('[data-view="'+mode+'"]');
          const filename='viewer-'+(mobile?'mobile-':'desktop-')+role+(mode==='front'?'':'-'+mode)+'.png';
          await page.evaluate(name=>{
            window.__lastCheckedFrame=null;
            const button=document.querySelector('[data-view="'+name+'"]');
            button.addEventListener('click',()=>{
              try{
                const gl=document.querySelector('#model-view canvas').getContext('webgl2');
                if(!gl||gl.isContextLost())throw Error('Lost WebGL context');
                  const width=gl.drawingBufferWidth, height=gl.drawingBufferHeight;
                  const rgba=new Uint8Array(width*height*4);
                  gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,rgba);
                  const background=Array.from(rgba.slice(0,4)), colors=new Set();
                  let different=0, opaque=0;
                  for(let offset=0;offset<rgba.length;offset+=4) {
                    const r=rgba[offset], g=rgba[offset+1], b=rgba[offset+2], a=rgba[offset+3];
                    if(a===255) opaque++;
                    if(Math.abs(r-background[0])+Math.abs(g-background[1])+Math.abs(b-background[2])>18) different++;
                    colors.add((r>>4)<<8 | (g>>4)<<4 | (b>>4));
                  }
                  if(different<width*height*.003 || opaque!==width*height || colors.size<8) throw Error('Garden frame lacks visible colour');
                  window.__lastCheckedFrame={width,height,background,opaque,foreground_pixels:different,quantized_colors:colors.size};

              }catch(error){window.__lastCheckedFrame={error:String(error)};}
            },{once:true});
          },mode);
          if(mobile)await view.tap();else await view.click();
          const rgba=await page.evaluate(()=>window.__lastCheckedFrame);
          assert(rgba && !rgba.error,rgba?.error);
          const bytes=await page.screenshot({scale:'css',path:path.join(output,filename)});
          report.views.push({filename,deviceScaleFactor:await page.evaluate(()=>devicePixelRatio),sha256:sha(bytes),viewport,role,mode,rgba,status:await status.innerText()});
        }
      }
      if (!mobile) {
        report.downloads = {};
        for (const role of ['raw', 'full', 'lod', 'native']) {
          const item = manifest.assets[role];
          const link = page.locator('#downloads a').filter({hasText: {raw:'原始',full:'网页',lod:'远景',native:'Blender'}[role]});
          const downloadEvent = page.waitForEvent('download');
          await link.click();
          const download = await downloadEvent;
          assert.equal(download.suggestedFilename(), item.file);
          assert.equal(path.basename(item.file), item.file);
          const dir=path.join(output,'saved');fs.mkdirSync(dir,{recursive:true});const saved=path.join(dir,'observed-'+item.file);
          try {
            await download.saveAs(saved);
            assert.equal(await download.failure(),null);
            const hash = createHash('sha256');
            let length = 0;
            for await (const block of fs.createReadStream(saved)) { hash.update(block); length += block.length; }
            const checksum = hash.digest('hex');
            assert.equal(length, item.bytes);
            assert.equal(checksum, item.sha256);
            report.downloads[role] = {file:item.file, bytes:length, sha256:checksum, saved_as:path.basename(saved), saveAsVerified:true};
          } finally {
            await download.delete();
            /* The verified download remains part of the device receipt. */
          }
        }
      }
      await page.close();
    }
    assert.deepEqual(report.pageErrors, []);
    report.passed = true;
  } finally {
    await browser.close();
    report.closed=!browser.isConnected();report.finished=new Date().toISOString();
    fs.writeFileSync(path.join(output,device+'-viewer.json'), JSON.stringify(report, null, 2) + '\n');
  }
}
check().catch(error => { console.error(error); process.exitCode = 1; });
