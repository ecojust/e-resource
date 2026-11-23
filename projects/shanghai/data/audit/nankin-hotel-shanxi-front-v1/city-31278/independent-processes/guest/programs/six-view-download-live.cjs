// node tools/check-candidate-viewer.cjs <model-id> <output-directory>
// MODEL_BASE_URL points to the Shanghai site root. Requires Playwright and Chromium.
const {chromium} = require('playwright');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:31343/';
const [id, output] = process.argv.slice(2);
if (!/^[a-z0-9]+(-[a-z0-9]+)+$/.test(id || '') || !output) {
  throw new Error('Supply a registered model id and an audit output directory');
}
const project = process.env.MODEL_FROZEN_ROOT;
assert(project);
const manifestPath = path.join(project, 'assets/models/candidates', id, 'manifest.json');
const expectedManifest = fs.readFileSync(manifestPath);
const route = JSON.parse(expectedManifest).viewer_page;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

async function check() {
  fs.mkdirSync(output, {recursive: true});
  assert.equal(id,'huangpu-wanyi-taofen-museum-no53-south-front');
  assert.equal(new URL(base).port,'31343');
  const device=process.env.SHANGHAI_343_DEVICE;assert(['desktop','mobile'].includes(device));
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  const report = {id, route, started: new Date().toISOString(), browser: browser.version(), base, files: {}, views: [], pageErrors: []};
  for (const name of [route, 'src/candidate-asset-viewer.js']) {
    report.files[name] = sha(fs.readFileSync(path.join(project, name)));
  }
  report.actual_inputs_sha256=sha(fs.readFileSync(path.join(project,'three-http-inputs.json')));
  report.scriptSHA256 = sha(fs.readFileSync(__filename));
  try {
    for (const mobile of [device==='mobile']) {
      const viewport = mobile ? {width: 390, height: 844} : {width: 1250, height: 820};
      const page = await browser.newPage({viewport, hasTouch: mobile, isMobile: mobile});
      page.on('pageerror', e => report.pageErrors.push(e.message));
      const moduleResponse = page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/src/candidate-asset-viewer.js'));
      const manifestResponse = page.waitForResponse(r => r.url().endsWith('/manifest.json'));
      const firstModel = page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/' + JSON.parse(expectedManifest).assets.full.file));
      const styleResponse=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/src/dacheng-hall.css'));
      const html = await page.goto(new URL(route, base).href);
      assert.equal(sha(await html.body()), report.files[route]);
      const css=await styleResponse;assert(css.ok());assert.equal(sha(await css.body()),sha(fs.readFileSync(path.join(project,'src/dacheng-hall.css'))));
      const stage=await page.locator('#model-view').boundingBox();assert(stage.width>=300&&stage.height>=240,JSON.stringify(stage));
      assert.equal(sha(await (await moduleResponse).body()), report.files['src/candidate-asset-viewer.js']);
      assert.equal(await page.locator('#model-view').getAttribute('data-oblique'),'positive-x');
      assert.equal(await page.locator('[data-view="front"]').innerText(),'正看53号院门与馆名');
      assert.equal(await page.locator('[data-view="above"]').innerText(),'高看老虎窗与坡瓦');
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
        const modes=role==='full'&&!mobile?['front','oblique','above']:['front'];
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
          assert.equal(download.suggestedFilename(), item.file);
          const saved=path.join(output,'saved-'+item.file);await download.saveAs(saved);
          const bytes = fs.readFileSync(saved);
          assert.equal(bytes.length, item.bytes);
          assert.equal(sha(bytes), item.sha256);
          report.downloads[role] = {file: item.file, bytes: bytes.length, sha256: sha(bytes), savedAs:item.file,saved:path.basename(saved)};
          await download.delete();
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
