// Resume the 390px touchscreen views after the desktop photos and four downloads.
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');
const assert = require('node:assert/strict');
const project = path.resolve(__dirname, '../../..');
const out = path.resolve(process.argv[2] || __dirname);
const id = 'huangpu-sino-french-school-teaching-building';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const html = 'sino-french-school.html';
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const viewport = {width: 390, height: 844};

async function main() {
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  const result = {id, viewport, browser: browser.version(), base, started: new Date().toISOString(), scriptSHA256: hash(fs.readFileSync(__filename)), files: {}, views: [], errors: []};
  try {
    const page = await browser.newPage({viewport, hasTouch: true, isMobile: true});
    page.setDefaultTimeout(120000);
    page.on('pageerror', error => result.errors.push(String(error)));
    const manifestFile = `assets/models/candidates/${id}/manifest.json`;
    const manifest = JSON.parse(fs.readFileSync(path.join(project, manifestFile)));
    const modelFile = role => `assets/models/candidates/${id}/${manifest.assets[role].file}`;
    const expected = [html, 'src/candidate-asset-viewer.js', manifestFile, modelFile('full'), modelFile('lod')];
    const received = new Map(expected.map(name => [name, page.waitForResponse(res => new URL(res.url()).pathname.endsWith('/' + name))]));
    await page.goto(new URL(html, base).href, {waitUntil: 'domcontentloaded'});
    for (const role of ['full', 'lod']) {
      await page.waitForFunction(() => document.querySelector('#status').textContent.startsWith('近景 ·'));
      await page.locator('#detail').selectOption(role);
      const prefix = role === 'full' ? '近景 ·' : '远景 ·';
      await page.waitForFunction(p => document.querySelector('#status').textContent.startsWith(p), prefix);
      const button = await page.locator('[data-view="front"]').evaluate(el => {
        const {x,y,width,height} = el.getBoundingClientRect();
        const point = {x: x + width/2, y: y + height/2};
        return {...point, target: el === document.elementFromPoint(point.x, point.y), name: el.textContent};
      });
      assert.ok(button.target);
      const click = page.evaluate(() => new Promise(resolve => document.querySelector('[data-view="front"]').addEventListener('click', ev => resolve({trusted: ev.isTrusted, label: ev.currentTarget.textContent}), {once: true})));
      await page.touchscreen.tap(button.x, button.y);
      const action = await click;
      assert.ok(action.trusted && action.label === '操场一侧的外廊');
      const filename = `viewer-mobile-${role}.png`;
      const bytes = await page.screenshot({path: path.join(out, filename)});
      result.views.push({filename, sha256: hash(bytes), viewport, role, status: await page.locator('#status').innerText(), button, action});
    }
    for (const [name, response] of received) {
      const res = await response;
      assert.ok(res.ok());
      result.files[name] = hash(await res.body());
      assert.equal(result.files[name], hash(fs.readFileSync(path.join(project, name))));
    }
    assert.deepEqual(result.errors, []);
    result.passed = true;
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(out, 'mobile-viewer.json'), JSON.stringify(result, null, 2) + '\n');
  }
}
main().catch(err => { console.error(err); process.exitCode = 1; });
