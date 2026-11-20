// Run with Playwright installed and MODEL_BASE_URL pointing to the Shanghai site.
const {chromium} = require('playwright');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const output = process.env.QA_OUTPUT_DIR || __dirname;
const project = path.resolve(__dirname, '../../..');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

async function check() {
  fs.mkdirSync(output, {recursive: true});
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  const report = {started: new Date().toISOString(), browser: browser.version(), base, files: {}, views: [], pageErrors: []};
  for (const name of ['country-hospital.html', 'src/country-hospital.js']) {
    report.files[name] = sha(fs.readFileSync(path.join(project, name)));
  }
  report.scriptSHA256 = sha(fs.readFileSync(__filename));
  try {
    for (const mobile of [false, true]) {
      const viewport = mobile ? {width: 390, height: 844} : {width: 1250, height: 820};
      const page = await browser.newPage({viewport, hasTouch: mobile, isMobile: mobile});
      page.on('pageerror', e => report.pageErrors.push(e.message));
      const manifestResponse = page.waitForResponse(r => r.url().endsWith('/manifest.json'));
      await page.goto(new URL('country-hospital.html', base).href);
      const response = await manifestResponse;
      const manifestBytes = await response.body();
      assert(response.ok());
      report.manifestSHA256 = sha(manifestBytes);
      const manifest = JSON.parse(manifestBytes);
      assert.equal(manifest.id, 'jingan-country-hospital');
      const status = page.locator('#status');
      await page.waitForFunction(() => document.getElementById('status').textContent.startsWith('近景 ·'));
      assert.equal(await page.locator('#downloads a').count(), 4);
      for (const role of ['full', 'lod']) {
        await page.locator('#detail').selectOption(role);
        const prefix = role === 'full' ? '近景' : '远景';
        await page.waitForFunction(p => document.getElementById('status').textContent.startsWith(p + ' ·'), prefix);
        const view = page.locator('[data-view="front"]');
        if (mobile) await view.tap();
        else await view.click();
        const filename = 'viewer-' + (mobile ? 'mobile-' : 'desktop-') + role + '.png';
        const bytes = await page.screenshot({path: path.join(output, filename)});
        report.views.push({filename, sha256: sha(bytes), viewport, role, status: await status.innerText()});
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
          const bytes = fs.readFileSync(await download.path());
          assert.equal(bytes.length, item.bytes);
          assert.equal(sha(bytes), item.sha256);
          report.downloads[role] = {file: item.file, bytes: bytes.length, sha256: sha(bytes)};
        }
      }
      await page.close();
    }
    assert.deepEqual(report.pageErrors, []);
    report.passed = true;
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(output, 'viewer.json'), JSON.stringify(report, null, 2) + '\n');
  }
}
check().catch(error => { console.error(error); process.exitCode = 1; });
