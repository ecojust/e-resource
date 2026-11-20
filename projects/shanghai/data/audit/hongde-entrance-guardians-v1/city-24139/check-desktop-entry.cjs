/* Open the released directory from a fresh desktop viewport and verify the selected ordinary model. */
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const base = process.env.MODEL_BASE_URL;
const output = process.env.QA_OUTPUT_DIR;
const id = 'hongkou-hongde-church';
const sha256 = data => crypto.createHash('sha256').update(data).digest('hex');
const report = { base, id, started: new Date().toISOString(), httpErrors: [], errors: [], completed: false };
async function run() {
  fs.mkdirSync(output, { recursive: true });
  const save = () => fs.writeFileSync(path.join(output, 'desktop-entry.json'), JSON.stringify(report, null, 2) + '\n');
  report.script_sha256 = sha256(fs.readFileSync(__filename));
  const manifest = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../../../source/precise/hongkou-hongde-church/revisions/entrance-guardians/manifest.json')));
  report.expected = manifest.assets.full;
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-dev-shm-usage', '--disk-cache-size=8388608', '--num-raster-threads=1', '--renderer-process-limit=2'],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1100, height: 744 }, deviceScaleFactor: 1, ignoreHTTPSErrors: true });
    page.setDefaultTimeout(90000);
    let full;
    page.on('response', response => {
      const uri = new URL(response.url());
      if (uri.origin !== new URL(base).origin) return;
      if (response.status() >= 400) report.httpErrors.push({ url: response.url(), status: response.status() });
      if (uri.pathname === '/' + report.expected.file && response.status() === 200) full = response;
    });
    page.on('pageerror', error => report.errors.push(error.message));
    await page.goto(new URL('landmarks.html', base).href, { waitUntil: 'domcontentloaded' });
    const card = page.locator('article[data-landmark="' + id + '"] .card-foot a');
    report.entries = await page.locator('.landmark-card[data-landmark]').count(); assert.equal(report.entries, 176);
    assert.equal(await card.getAttribute('href'), 'index.html#landmark=' + id + '&mode=walk');
    await card.click();
    await page.waitForFunction(({ id, hash }) => {
      const app = window.__SHANGHAI_APP__, scene = app?.scene, curtain = document.querySelector('#loading');
      if (!scene || !curtain || getComputedStyle(curtain).opacity > .015) return false;
      const model = scene.getLandmarkAssetState(id), renderer = scene.getStreamingState().renderer;
      return app.mode === 'walk' && model.visible && model.verifiedAsset?.sha256 === hash &&
        scene.getOrdinaryCatalogState().activeMacros.includes('14-13720-6692') && renderer.drawCalls > 100 && renderer.triangles > 900000;
    }, { id, hash: report.expected.sha256 }, { timeout: 300000, polling: 650 });
    report.state = await page.evaluate(id => {
      const app = window.__SHANGHAI_APP__, scene = app.scene, map = scene.map, model = scene.getLandmarkAssetState(id);
      return { mode: app.mode, route: location.hash, width: innerWidth, height: innerHeight, canvas: [map.getCanvas().width, map.getCanvas().height],
        selected: document.querySelector('#location-name').textContent, count: scene.getBuildingBeaconState().count, model: model.verifiedAsset,
        triangles: model.triangles, renderer: scene.getStreamingState().renderer, geography: model.anchor, activeMacros: scene.getOrdinaryCatalogState().activeMacros,
        camera: { center: map.getCenter().toArray(), bearing: map.getBearing(), pitch: map.getPitch(), zoom: map.getZoom() },
        gl: map.painter.context.gl.getError(), contextLost: map.painter.context.gl.isContextLost() };
    }, id);
    assert.equal(report.state.selected, '鸿德堂 · 多伦路59号'); assert.equal(report.state.count, 176);
    assert.equal(report.state.triangles, report.expected.triangles); assert.equal(report.state.gl, 0); assert.equal(report.state.contextLost, false);
    assert.deepEqual(report.state.canvas, [1100, 744]); assert.ok(full);
    const body = await full.body(); assert.equal(sha256(body), report.expected.sha256); assert.equal(body.length, report.expected.bytes);
    report.received = { url: full.url(), bytes: body.length, sha256: sha256(body) }; save();
    const file = 'north-entrance-desktop-fresh.png';
    const image = await page.screenshot({ path: path.join(output, file), timeout: 120000 });
    report.image = { file, bytes: image.length, sha256: sha256(image) };
    assert.deepEqual(report.httpErrors, []); assert.deepEqual(report.errors, []); report.completed = true;
  } catch (error) {
    report.failure = String(error); throw error;
  } finally {
    await browser.close(); report.finished = new Date().toISOString(); save();
  }
}
run().catch(error => { console.error(error); process.exitCode = 1; });
