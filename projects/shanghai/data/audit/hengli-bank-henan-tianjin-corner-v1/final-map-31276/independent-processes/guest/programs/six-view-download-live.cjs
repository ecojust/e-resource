// node tools/check-candidate-viewer.cjs <model-id> <output-directory>
// MODEL_BASE_URL points to the Shanghai site root. Requires Playwright and Chromium.
const {chromium} = require('playwright');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:31341/';
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
  assert.equal(id,'huangpu-fuxing-fang-553-inscribed-balcony');
  assert.equal(new URL(base).port,'31341');
  const device=process.env.SHANGHAI_341_DEVICE;assert(['desktop','mobile'].includes(device));
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    args: ['--no-sandbox','--no-zygote','--single-process','--in-process-gpu','--disable-dev-shm-usage','--num-raster-threads=1','--js-flags=--max-old-space-size=160'],
  });
  const report = {id, route, started: new Date().toISOString(), browser: browser.version(), base, files: {}, views: [], pageErrors: []};
  for (const name of [route, 'src/candidate-asset-viewer.js']) {
    report.files[name] = sha(fs.readFileSync(path.join(project, name)));
  }
  report.scriptSHA256 = sha(fs.readFileSync(__filename));
  try {
    for (const mobile of [device==='mobile']) {
      const viewport = mobile ? {width: 390, height: 844} : {width: 1250, height: 820};
      const page = await browser.newPage({viewport, hasTouch: mobile, isMobile: mobile});
      page.on('pageerror', e => report.pageErrors.push(e.message));
      const moduleResponse = page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/src/candidate-asset-viewer.js'));
      const manifestResponse = page.waitForResponse(r => r.url().endsWith('/manifest.json'));
      const firstModel = page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/' + JSON.parse(expectedManifest).assets.full.file));
      const html = await page.goto(new URL(route, base).href);
      assert.equal(sha(await html.body()), report.files[route]);
      assert.equal(sha(await (await moduleResponse).body()), report.files['src/candidate-asset-viewer.js']);
      assert.equal(await page.locator('#model-view').getAttribute('data-front'),'positive-z');

      assert.equal(await page.locator('[data-view="front"]').innerText(),"正看红字题名");
      assert.equal(await page.locator('[data-view="oblique"]').innerText(),"斜看折面与木百叶");
      assert.equal(await page.locator('[data-view="above"]').innerText(),"俯看阳台压顶");
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
          if(mobile)await view.tap();else await view.click();
          await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
          const filename='viewer-'+(mobile?'mobile-':'desktop-')+role+(mode==='front'?'':'-'+mode)+'.png';
          const rgba = await page.evaluate(async mode => {
            const canvas = document.querySelector('#model-view canvas');
            const gl = canvas.getContext('webgl2');
            if (!gl || gl.isContextLost()) throw Error('Window elevation WebGL context is unavailable');
            // Request a camera redraw and read the default buffer before its next swap.
            return new Promise((resolve, reject) => {
              const orbit = document.querySelector('[data-view="'+mode+'"]');
              const button = orbit || document.querySelector('[data-view="front"]');
              requestAnimationFrame(() => {
                try {
                  button.click();
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
                  if(different<width*height*.003 || opaque!==width*height || colors.size<8) throw Error('Window elevation frame lacks visible colour');
                  resolve({width,height,background,opaque,foreground_pixels:different,quantized_colors:colors.size});
                } catch(error) { reject(error.toString()); }
              });
            });
          }, mode);
          const bytes=await page.screenshot({path:path.join(output,filename)});
          report.views.push({filename,sha256:sha(bytes),viewport,role,mode,rgba,status:await status.innerText()});
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
          assert.equal(await download.failure(), null);
          assert.equal(download.suggestedFilename(), item.file);
          assert.equal(path.basename(item.file), item.file);
          const saved = path.join(output, 'saved', 'observed-' + item.file);fs.mkdirSync(path.dirname(saved),{recursive:true});
          try {
            await download.saveAs(saved);
            const hash = createHash('sha256');
            let length = 0;
            for await (const block of fs.createReadStream(saved)) { hash.update(block); length += block.length; }
            const checksum = hash.digest('hex');
            assert.equal(length, item.bytes);
            assert.equal(checksum, item.sha256);
            report.downloads[role] = {file:item.file, bytes:length, sha256:checksum, saved_as:path.basename(saved),saved:path.relative(output,saved), saveAsVerified:true};
          } finally {
            await download.delete();

          }
        }
      }
      await page.close();
    }
    assert.deepEqual(report.pageErrors, []);
    report.passed = true;
  } finally {
    await browser.close();report.device=device;report.closed=!browser.isConnected();report.finished=new Date().toISOString();
    fs.writeFileSync(path.join(output, device+'-viewer.json'), JSON.stringify(report, null, 2) + '\n');
  }
}
check().catch(error => { console.error(error); process.exitCode = 1; });
