/* Actual Chromium map QA. --control runs the unchanged #39 catalogue alone,
   in a private page, with the same original near/far city bytes and camera. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const ID = 'jingan-country-hospital-north-block';
const GARDEN = 'jingan-country-hospital';
const audit = __dirname;
const project = path.resolve(audit, '../../..');
const repo = path.resolve(project, '../..');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const output = process.env.QA_OUTPUT_DIR || audit;
const control = process.argv.includes('--control');
const hash = (b) => createHash('sha256').update(b).digest('hex');
const read = (f) => JSON.parse(fs.readFileSync(path.join(project, f)));
const source = read('source/precise/' + ID + '/footprint-review.json');
const camera = {
  center: [source.author_frame.anchor.lng, source.author_frame.anchor.lat],
  bearing: 165,
  pitch: 57,
  zoom: 19.5,
  elevation: 9,
  padding: { left: 0, right: 0, top: 0, bottom: 0 },
};
const fromGit = (f) =>
  execFileSync('git', ['show', source.baseline_commit + ':projects/shanghai/' + f], { cwd: repo });
const report = {
  id: ID,
  control,
  scriptSha256: hash(fs.readFileSync(__filename)),
  started: new Date().toISOString(),
  completed: false,
  camera,
  server: base,
  phases: [],
  screenshots: [],
  errors: [],
  failedRequests: [],
  sourceHTTP: [],
};
const resultFile = path.join(output, control ? 'control-browser.json' : 'main-browser.json');
const save = () => fs.writeFileSync(resultFile, JSON.stringify(report, null, 2) + '\n');
const phase = (name) => {
  report.phases.push(name);
  console.log(name);
  save();
};
async function run() {
  assert.ok(!fs.existsSync(resultFile), 'Use a fresh QA_OUTPUT_DIR');
  fs.mkdirSync(output, { recursive: true });
  const registryFile = 'data/candidate-city-integrations.json';
  const catalogBytes = control ? fromGit(registryFile) : fs.readFileSync(path.join(project, registryFile));
  const catalog = JSON.parse(catalogBytes);
  const row = catalog.models.find((r) => r.id === ID),
    count = catalog.resulting_city_count;
  const macro = source.frozen_macro;
  assert.equal(Boolean(row), !control);
  report.catalog = {
    sha256: hash(catalogBytes),
    count,
    overriddenWithBaseline: control ? source.baseline_commit : null,
  };
  const inputs = Object.fromEntries(
    [
      'src/map-scene.js',
      'src/candidate-city-integrations.js',
      'src/candidate-source-sections.js',
      'src/candidate-city-clipping.js',
      'src/building-beacons.js',
      'index.html',
    ].map((f) => [f, hash(fs.readFileSync(path.join(project, f)))]),
  );
  report.runtime = inputs;
  let manifest;
  if (!control) {
    assert.ok(count >= 86);
    assert.equal(row.districtId, '310106');
    assert.match(row.name, /宏恩医院/);
    assert.equal(row.owner.feature_local_id, 848);
    assert.equal(row.site_replacement.owner.feature_local_id, 2764);
    manifest = read(row.candidate_manifest);
    report.manifestSha256 = hash(fs.readFileSync(path.join(project, row.candidate_manifest)));
  }
  const g = source.near_tiles.filter(
    (r) => r.feature_local_ids.includes(848) || r.feature_local_ids.includes(2764),
  );
  const seen = new Set();
  const browser = await chromium.launch({
    executablePath: '/usr/bin/chromium',
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  report.browser = browser.version();
  const page = await browser.newPage({
    viewport: { width: control ? 960 : 390, height: control ? 720 : 844 },
    hasTouch: true,
    ignoreHTTPSErrors: true,
  });
  page.setDefaultTimeout(180000);
  if (control)
    await page.route('**/data/candidate-city-integrations.json*', (r) =>
      r.fulfill({ body: catalogBytes, contentType: 'application/json' }),
    );
  page.on('pageerror', (e) => report.errors.push(String(e)));
  page.on('console', (m) => {
    if (m.type() === 'error') report.errors.push({ url: m.location().url, message: m.text() });
  });
  page.on('requestfailed', (r) => {
    if (r.failure()?.errorText !== 'net::ERR_ABORTED')
      report.failedRequests.push({ url: r.url(), reason: r.failure() });
  });
  page.on('response', (r) => {
    const u = new URL(r.url());
    if (r.status() >= 400) report.failedRequests.push({ url: r.url(), status: r.status() });
    if (r.status() === 200 && u.origin === new URL(base).origin)
      seen.add(decodeURIComponent(u.pathname).slice(1));
  });
  async function shot(name) {
    const bytes = await page.screenshot({ path: path.join(output, name + '.png'), timeout: 120000 });
    report.screenshots.push({
      file: name + '.png',
      width: bytes.readUInt32BE(16),
      height: bytes.readUInt32BE(20),
      sha256: hash(bytes),
      bytes: bytes.length,
    });
    save();
  }
  async function settle(id, variant, detail = false) {
    await page.waitForFunction(
      ({ id, variant, detail, groups, control, macro }) => {
        const s = window.__SHANGHAI_APP__?.scene;
        if (!s || s.map.isMoving()) return false;
        const a = s.getLandmarkAssetState(id),
          c = s.getCandidateIntegrationState(),
          t = s.getStreamingState();
        if (!(a.status === 'loaded' && a.visible && (!variant || a.variant === variant))) return false;
        if (!detail) return true;
        return (
          t.active.some((x) => x.id === macro && x.visible) &&
          groups.every((z) => t.detail.active.some((x) => x.id === macro + '/' + z.id)) &&
          c.vector
            .filter((x) => x.active)
            .every(
              (v) => !v.pending && !v.residualLayer?.busy && (!v.partialIDs || v.residualLayer?.ready),
            ) &&
          (control ||
            (c.sourceSections.some((x) => x.id === id) &&
              c.sourceSections.some((x) => x.id === id + '-spine')))
        );
      },
      { id, variant, detail, groups: g, control, macro },
      { polling: 500, timeout: 240000 },
    );
    await page.evaluate(
      () =>
        new Promise((resolve) => {
          const m = window.__SHANGHAI_APP__.scene.map;
          m.once('render', () => resolve());
          m.triggerRepaint();
        }),
    );
  }
  async function snapshot(tag, id, detail = false) {
    const state = await page.evaluate(
      ({ id, neighbors, control }) => {
        const a = window.__SHANGHAI_APP__,
          s = a.scene,
          m = s.map,
          c = s.getCandidateIntegrationState(),
          stream = s.getStreamingState(),
          b = s.getBuildingBeaconState();
        const v = s.getLandmarkAssetState(id),
          label = b.labelPositions.find((p) => p.id === id);
        const gl = m.painter.context.gl;
        return {
          route: location.hash,
          title: document.querySelector('#location-name').textContent,
          viewport: [innerWidth, innerHeight],
          camera: {
            center: m.getCenter(),
            pitch: m.getPitch(),
            bearing: m.getBearing(),
            zoom: m.getZoom(),
            padding: m.getPadding(),
          },
          asset: v,
          clips: c.clips.filter((x) => x.id.startsWith('jingan-country-hospital')),
          sections: c.sourceSections.filter((x) => x.id.startsWith('jingan-country-hospital')),
          groups: c.shader.ownerScopedSources.filter(
            (z) => z.macro_id === '14-13718-6695' && z.feature_local_ids.some((i) => i === 848 || i === 2764),
          ),
          triangles: c.shader.triangles,
          limit: c.shader.triangleLimit,
          visibleMacros: stream.active.filter((r) => r.visible).map((r) => r.id),
          neighbors: neighbors.map((r) => ({
            id: r.local_id,
            state: m.getFeatureState({
              source: 'overture-buildings',
              sourceLayer: 'building',
              id: r.key.slice(9),
            }),
          })),
          beacons: b.count,
          hit: label ? s.pickBuildingBeacon(label) : null,
          walking: !document.querySelector('#start-walk').disabled,
          glError: gl.getError(),
          contextLost: gl.isContextLost(),
        };
      },
      { id, neighbors: source.owners.filter((i) => [3292, 1805].includes(i.local_id)), control },
    );
    report[tag] = state;
    save();
    assert.equal(state.glError, 0);
    assert.equal(state.contextLost, false);
    assert.equal(state.beacons, count);
    for (const n of state.neighbors) assert.notEqual(n.state.candidateModel, true);
    if (control) {
      assert.ok(!state.clips.some((x) => x.id === ID || x.id === ID + '-spine'));
    } else {
      assert.equal(state.title, row.name);
      assert.equal(new URLSearchParams(state.route.slice(1)).get('landmark'), ID);
      assert.equal(state.walking, false);
      assert.equal(
        state.asset.verifiedAsset.sha256,
        row.assets[state.asset.variant === 'full' ? 'web' : 'lod'].sha256,
      );
      assert.equal(
        state.asset.triangles,
        row.assets[state.asset.variant === 'full' ? 'web' : 'lod'].triangles,
      );
      assert.deepEqual(state.asset.anchor, [row.lng, row.lat]);
      assert.equal(state.asset.heading, row.heading);
      assert.equal(state.hit, ID);
      const major = state.clips.find((z) => z.id === ID),
        other = state.clips.find((z) => z.id === row.site_replacement.id);
      assert.deepEqual(major.geometry, row.replacement_geometry);
      assert.deepEqual(other.geometry, row.site_replacement.geometry);
      if (detail) {
        const northCap = state.sections.find((x) => x.id === ID),
          stemCap = state.sections.find((x) => x.id === row.site_replacement.id);
        assert.equal(northCap.segments, 1);
        assert.equal(stemCap.segments, 3);
        for (const n of [northCap, stemCap]) {
          const expected = n.id === ID ? row : row.site_replacement;
          assert.equal(n.feature_local_id, expected.owner.feature_local_id);
          assert.equal(n.roof_m, expected.source_section_caps.roof_m);
        }
        assert.ok(
          state.clips.some((c) => c.id === GARDEN),
          'Garden facade not active',
        );
        assert.ok(
          state.sections.some((c) => c.id === GARDEN),
          'Garden source cap lost',
        );
      }
    }
    if (detail) {
      for (const tile of g) {
        const current = state.groups.find((s) => s.id === macro + '/' + tile.id);
        assert.deepEqual(current.feature_local_ids, tile.feature_local_ids);
        if (!control)
          assert.ok(
            current.clip_feature_local_ids.includes(tile.feature_local_ids.includes(848) ? 848 : 2764),
          );
      }
    }
    return state;
  }
  async function panelClosed() {
    const panel = page.locator('#panel-toggle');
    if ((await panel.getAttribute('aria-expanded')) === 'true') await panel.click();
  }
  async function jump(config) {
    await page.evaluate((c) => {
      const s = window.__SHANGHAI_APP__.scene;
      s.map.setCenterClampedToGround(false);
      s.map.jumpTo(c);
      s.loadLandmarks();
      s.refreshBuildingBeacons();
    }, config);
  }
  async function select(id) {
    await page.evaluate(async (id) => {
      const a = window.__SHANGHAI_APP__;
      await a.selectPlace(
        a.landmarks.find((r) => r.id === id),
        { mode: 'overview' },
      );
    }, id);
  }
  async function dense(input, previous) {
    await select(previous);
    await page.evaluate(() => {
      const s = window.__SHANGHAI_APP__.scene;
      s.map.setMaxBounds(null);
      s.map.setCenterClampedToGround(true);
      s.map.jumpTo({
        center: [121.45, 31.2],
        zoom: 8,
        pitch: 0,
        bearing: 0,
        elevation: 0,
        padding: { left: 0, right: 0, top: 0, bottom: 0 },
      });
      s.refreshBuildingBeacons();
    });
    await page.waitForFunction(
      (n) => window.__SHANGHAI_APP__.scene.getBuildingBeaconState().viewportLabelCount === n,
      count,
      { polling: 500 },
    );
    const d = await page.evaluate((id) => {
      const s = window.__SHANGHAI_APP__.scene,
        b = s.getBuildingBeaconState();
      return {
        count: b.count,
        labels: b.labelPositions.length,
        fallback: b.overlapFallbackCount,
        allHit: b.labelPositions.every((p) => s.pickBuildingBeacon({ x: p.x, y: p.y }) === p.id),
        target: b.labelPositions.find((p) => p.id === id),
        staleSections: s.getCandidateIntegrationState().sourceSections.filter((x) => x.id.startsWith(id)),
        viewport: [innerWidth, innerHeight],
      };
    }, ID);
    assert.equal(d.allHit, true);
    assert.equal(d.fallback, 0);
    assert.deepEqual(d.staleSections, []);
    assert.equal(d.labels, count);
    report[input + 'Dense'] = d;
    save();
    if (input === 'touch') await shot('map-beacons-mobile');
    if (input === 'touch') await page.touchscreen.tap(d.target.x, d.target.y);
    else await page.mouse.click(d.target.x, d.target.y);
    await page.waitForFunction(
      (id) => new URLSearchParams(location.hash.slice(1)).get('landmark') === id,
      ID,
    );
    await settle(ID);
    await snapshot(input + 'Selected', ID);
  }
  try {
    if (control) {
      phase('Unaltered pre-delivery coarse buildings');
      await page.goto(base + 'index.html#landmark=' + GARDEN + '&mode=overview', {
        waitUntil: 'domcontentloaded',
      });
      await settle(GARDEN);
      await panelClosed();
      await jump(camera);
      await settle(GARDEN, null, true);
      await snapshot('before', GARDEN, true);
      await shot('map-before-north-block');
    } else {
      phase('Mobile route from district directory');
      await page.goto(base + 'landmarks.html', { waitUntil: 'domcontentloaded' });
      assert.equal(await page.locator('.landmark-card[data-landmark]').count(), count);
      await page
        .locator(
          '#district-310106 [data-landmark="' +
            ID +
            '"] .card-foot a[href="index.html#landmark=' +
            ID +
            '&mode=overview"]',
        )
        .click();
      await settle(ID);
      await snapshot('mobile', ID);
      await shot('map-mobile');
      phase('Desktop default');
      await page.setViewportSize({ width: 960, height: 720 });
      await page.reload({ waitUntil: 'domcontentloaded' });
      await settle(ID, 'full', true);
      await snapshot('desktop', ID, true);
      await shot('map-desktop');
      phase('Active owner groups and clipping');
      await panelClosed();
      await jump(camera);
      await settle(ID, 'full', true);
      await snapshot('northFace', ID, true);
      await shot('map-north-face');
      await jump({ ...camera, bearing: 115, pitch: 33, zoom: 19.4 });
      await settle(ID, 'full', true);
      await snapshot('roof', ID, true);
      await shot('map-spine-roof');
      phase('Distant model and real label inputs');
      await jump({ ...camera, zoom: 15.5, pitch: 35, elevation: 0 });
      await settle(ID, 'distant');
      await snapshot('lod', ID);
      await dense('mouse', GARDEN);
      await page.setViewportSize({ width: 320, height: 568 });
      await page.waitForFunction(() => window.__SHANGHAI_APP__.scene.map.transform.width === 320);
      await dense('touch', GARDEN);
      phase('Verify posted files');
      report.downloads = [];
      for (const [role, a] of Object.entries(manifest.assets)) {
        const f = path.posix.join(path.posix.dirname(row.candidate_manifest), a.file);
        const r = await page.request.get(new URL(f, base).href);
        const b = await r.body();
        assert.equal(r.status(), 200);
        assert.equal(b.length, a.bytes);
        assert.equal(hash(b), a.sha256);
        report.downloads.push({ role, bytes: b.length, sha256: hash(b) });
      }
    }
    for (const rec of source.frozen_bindings) {
      const f = rec.repository_path.replace('projects/shanghai/', '');
      if (!f.endsWith('/far.glb') && !g.some((n) => f.endsWith('/' + n.file))) continue;
      assert.ok(seen.has(f), f + ' was not actually requested by the scene');
      const response = await page.request.get(new URL(f, base).href),
        b = await response.body();
      assert.equal(response.status(), 200);
      assert.equal(hash(b), rec.sha256);
      assert.equal(b.length, rec.bytes);
      report.sourceHTTP.push({ file: f, bytes: b.length, sha256: hash(b) });
    }
    if (!control) {
      for (const [f, d] of Object.entries(inputs))
        assert.equal(hash(fs.readFileSync(path.join(project, f))), d, 'Runtime changed: ' + f);
      assert.equal(hash(fs.readFileSync(path.join(project, registryFile))), report.catalog.sha256);
    }
    assert.deepEqual(report.errors, []);
    assert.deepEqual(report.failedRequests, []);
    report.completed = true;
  } catch (e) {
    report.failure = e.stack;
    throw e;
  } finally {
    await browser.close();
    report.finished = new Date().toISOString();
    save();
  }
}
run().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
