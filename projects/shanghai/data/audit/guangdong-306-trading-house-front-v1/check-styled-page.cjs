// node tools/check-candidate-viewer.cjs <model-id> <output-directory>
// MODEL_BASE_URL points to the Shanghai site root. Requires Playwright and Chromium.
const {chromium} = require('playwright-core');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const [id, output] = process.argv.slice(2);
if (!/^[a-z0-9]+(-[a-z0-9]+)+$/.test(id || '') || !output) {
  throw new Error('Supply a registered model id and an audit output directory');
}
const project = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(__dirname, '../../..');
const manifestPath = path.join(project, 'assets/models/candidates', id, 'manifest.json');
const expectedManifest = fs.readFileSync(manifestPath);
const route = JSON.parse(expectedManifest).viewer_page;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

async function check() {
  fs.mkdirSync(output, {recursive: true});
  let browser;
  const settings = {
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    downloadsPath:process.env.TMPDIR,
    args: ['--use-angle=swiftshader','--enable-unsafe-swiftshader','--single-process','--no-zygote','--in-process-gpu','--renderer-process-limit=1','--disable-gpu-shader-disk-cache'],
  };
  const report = {id, route, started: new Date().toISOString(), browser: null, base, files: {}, views: [], pageErrors: []};
  for (const name of [route, 'src/candidate-asset-viewer.js']) {
    report.files[name] = sha(fs.readFileSync(path.join(project, name)));
  }
  report.scriptSHA256 = sha(fs.readFileSync(__filename));
  try {
    for (const mobile of [false, true]) {
      browser = await chromium.launch(settings); report.browser=browser.version();
      const viewport = mobile ? {width: 390, height: 844} : {width: 920, height: 640};
      const page = await browser.newPage({viewport, hasTouch: mobile, isMobile: mobile});
      page.on('pageerror', e => report.pageErrors.push(e.message));
      const styleReceipt=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/src/dacheng-hall.css'));
      const bad=[];page.on('response',r=>{if(r.status()>=400)bad.push([r.status(),r.url()])});
      const moduleResponse = page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/src/candidate-asset-viewer.js'));
      const manifestResponse = page.waitForResponse(r => r.url().endsWith('/manifest.json'));
      const html = await page.goto(new URL(route, base).href);
      assert.equal(sha(await html.body()), report.files[route]);
      assert.equal(sha(await (await moduleResponse).body()), report.files['src/candidate-asset-viewer.js']);
      const response = await manifestResponse;
      const css=await styleReceipt;
      assert.equal(css.status(),200);assert.match(css.headers()['content-type'],/text\/css/);
      const icon=await page.request.get(new URL('assets/favicon.svg',base).href);assert.equal(icon.status(),200);
      report.layout ||= {};
      const measured=await page.locator('#model-view').evaluate(el=>{const box=el.getBoundingClientRect();return {width:box.width,height:box.height,left:box.left,top:box.top,position:getComputedStyle(el).position,panel:getComputedStyle(document.querySelector('aside')).position}});
      assert.ok(measured.width>=385 && measured.height>=280 && measured.position==='fixed' && measured.panel==='absolute',JSON.stringify(measured));
      report.layout[mobile?'phone':'desktop']={...measured,css_sha256:sha(await css.body()),favicon_sha256:sha(await icon.body())};
      const manifestBytes = await response.body();
      assert(response.ok());
      report.manifestSHA256 = sha(manifestBytes);
      const manifest = JSON.parse(manifestBytes);
      assert.equal(manifest.id, id);
      assert.equal(sha(manifestBytes), sha(expectedManifest));
      const status = page.locator('#status');
      await page.waitForFunction(() => document.getElementById('status').textContent.startsWith('近景 ·'));
      assert.equal(await page.locator('#downloads a').count(), 4);
      const labels = {"front": "正看八个窗轴", "oblique": "斜看长阳台与栏杆", "above": "俯看小阳台与折线饰带"};
      for (const [key, label] of Object.entries(labels)) {
        assert.equal(await page.locator('[data-view="' + key + '"]').innerText(), label);
      }
      for (const role of ['full', 'lod']) {
        const received = role === 'lod' ? page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/' + manifest.assets.lod.file)) : null;
        await page.locator('#detail').selectOption(role);
        if (received) assert.equal(sha(await (await received).body()), manifest.assets.lod.sha256);
        const prefix = role === 'full' ? '近景' : '远景';
        await page.waitForFunction(p => document.getElementById('status').textContent.startsWith(p + ' ·'), prefix);
        const view = page.locator('[data-view="front"]');
        if (mobile) await view.tap();
        else await view.click();
        const filename = 'viewer-' + (mobile ? 'mobile-' : 'desktop-') + role + '.png';
        const bytes = await page.screenshot({path: path.join(output, filename)});
        report.views.push({filename, sha256: sha(bytes), viewport, role, status: await status.innerText()});
        if (role === 'full') {
          const oblique = page.locator('[data-view="oblique"]');
          if (mobile) await oblique.tap();
          else await oblique.click();
          const obliqueFile = 'viewer-' + (mobile ? 'mobile-' : 'desktop-') + 'upper-windows-and-balconies.png';
          const obliqueBytes = await page.screenshot({path: path.join(output, obliqueFile)});
          assert.notEqual(sha(obliqueBytes), sha(bytes));
          report.views.push({filename: obliqueFile, sha256: sha(obliqueBytes), viewport, role, selectedView:'oblique', status: await status.innerText()});
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
          const saved = path.join(process.env.TMPDIR, 'observed-' + item.file);
          await download.saveAs(saved);
          const bytes = fs.readFileSync(saved);
          assert.equal(bytes.length, item.bytes);
          assert.equal(sha(bytes), item.sha256);
          report.downloads[role] = {file: item.file, bytes: bytes.length, sha256: sha(bytes), savedAs: item.file};
          fs.unlinkSync(saved);
          await download.delete();
        }
      }
      assert.deepEqual(bad,[]);await browser.close(); browser=null;
    }
    assert.deepEqual(report.pageErrors, []);
    report.passed = true;
  } finally {
    if(browser) await browser.close();
    fs.writeFileSync(path.join(output, 'viewer.json'), JSON.stringify(report, null, 2) + '\n');
  }
}
check().catch(error => { console.error(error); process.exitCode = 1; });
