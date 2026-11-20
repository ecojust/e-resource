/* Browser QA of the garden wing in the live Shanghai scene. Run with the postal
 * audit server at MODEL_BASE_URL. The city detail GLBs must be served intact. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');
const { PNG } = require('pngjs');

const ID = 'jingan-country-hospital';
const PROJECT = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(__dirname, '../../..');
const OUTPUT = process.env.QA_OUTPUT_DIR || __dirname;
const BASE = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/';
const zeroPadding = { left: 0, right: 0, top: 0, bottom: 0 };
const hash = (data) => createHash('sha256').update(data).digest('hex');
const filename = (file) => path.join(PROJECT, file);
const read = (file) => JSON.parse(fs.readFileSync(filename(file)));
const report = {
  model: ID,
  started: new Date().toISOString(),
  completed: false,
  server: BASE,
  scriptSha256: hash(fs.readFileSync(__filename)),
  screenshots: [],
  stages: [],
  networkErrors: [],
  consoleErrors: [],
  pageErrors: [],
  cityReceipts: [],
  notes:
    'Actual Chromium using SwiftShader. External requests direct. Local static files and unchanged sparse city assets served by the audit server. Image inspection recorded separately.',
};
const save = () =>
  fs.writeFileSync(path.join(OUTPUT, 'main-map-browser.json'), JSON.stringify(report, null, 2) + '\n');
const stage = (name) => {
  report.stages.push(name);
  console.log(name);
  save();
};
async function run() {
  fs.mkdirSync(OUTPUT, { recursive: true });
  assert.ok(!fs.existsSync(path.join(OUTPUT, 'main-map-browser.json')), 'Use a fresh QA_OUTPUT_DIR');
  const catalog = read('data/candidate-city-integrations.json');
  const row = catalog.models.find((r) => r.id === ID);
  assert.ok(row, 'Wait for the Jing’an model registration');
  assert.match(row.name, /宏恩医院/);
  assert.deepEqual([catalog.models.length, catalog.resulting_city_count, row.districtId], [45, 85, '310106']);
  const foot = read('source/precise/' + ID + '/footprint-review.json');
  assert.deepEqual(row.owner, {
    macro_id: foot.owner.macro_id,
    feature_local_id: foot.owner.feature_local_id,
  });
  assert.deepEqual(row.source_feature_ids.building, [foot.owner.source_key.slice('building:'.length)]);
  const manifest = read(row.candidate_manifest);
  const meta = [
    row.candidate_manifest,
    'data/candidate-city-integrations.json',
    'data/global-models/additional-placement.json',
    'src/map-scene.js',
    'src/candidate-city-clipping.js',
    'src/candidate-source-sections.js',
    'src/candidate-city-integrations.js',
    'src/app.js',
    'src/building-beacons.js',
    'index.html',
    'source/precise/' + ID + '/footprint-review.json',
  ];
  report.inputs = Object.fromEntries(meta.map((p) => [p, hash(fs.readFileSync(filename(p)))]));
  report.assetHashes = Object.fromEntries(
    Object.entries(manifest.assets).map(([role, v]) => [role, v.sha256]),
  );
  const expectedCity = new Map(
    Object.entries(foot.frozen_bindings).map(([file, v]) => [file.replace('projects/shanghai/', ''), v]),
  );
  const cityRequests = new Set();
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    headless: true,
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  report.browser = browser.version();
  const page = await browser.newPage({
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    ignoreHTTPSErrors: true,
  });
  page.setDefaultTimeout(180000);
  page.on('pageerror', (e) => report.pageErrors.push(String(e)));
  page.on('requestfailed', (r) => {
    const error = r.failure()?.errorText;
    if (error !== 'net::ERR_ABORTED') report.networkErrors.push({ url: r.url(), error });
  });
  page.on('console', (m) => {
    if (m.type() === 'error') report.consoleErrors.push({ message: m.text(), url: m.location().url });
  });
  page.on('response', (r) => {
    const url = new URL(r.url()),
      file = url.pathname.slice(1);
    if (url.origin === new URL(BASE).origin && expectedCity.has(file) && r.status() === 200)
      cityRequests.add(file);
    if (r.status() >= 400) report.networkErrors.push({ url: r.url(), status: r.status() });
  });
  const view = async (name) => {
    const b = await page.screenshot({ path: path.join(OUTPUT, name + '.png'), timeout: 120000 });
    report.screenshots.push({
      file: name + '.png',
      sha256: hash(b),
      bytes: b.length,
      width: b.readUInt32BE(16),
      height: b.readUInt32BE(20),
    });
    save();
  };
  // Wait for the requested variant, a painted frame after the transition and
  // (at street scale) the actual owner-scoped shared near group.
  const ready = async (variant = null, detail = false) => {
    await page.waitForFunction(
      ({ id, variant, detail, owner, source }) => {
        const a = window.__SHANGHAI_APP__,
          s = a?.scene;
        if (!s || s.map.isMoving()) return false;
        const m = s.getLandmarkAssetState(id),
          state = s.getCandidateIntegrationState();
        const group = state.shader.ownerScopedSources.find(
          (r) => r.macro_id === owner.macro_id && r.clip_feature_local_ids.includes(owner.feature_local_id),
        );
        const target = s.getStreamingState().active.some((r) => r.id === owner.macro_id && r.visible);
        const suppressed = s.map.getFeatureState({
          source: 'overture-buildings',
          sourceLayer: 'building',
          id: source,
        });
        const vectorsReady = state.vector
          .filter((x) => x.active)
          .every((x) => !x.pending && !x.residualLayer?.busy && (!x.partialIDs || x.residualLayer?.ready));
        const bounds = s.map.getCanvas().getBoundingClientRect();
        return (
          Math.round(bounds.width) === innerWidth &&
          Math.round(bounds.height) === innerHeight &&
          m.status === 'loaded' &&
          m.visible &&
          (!variant || m.variant === variant) &&
          (!detail ||
            (group &&
              target &&
              vectorsReady &&
              (suppressed.localModel || suppressed.candidateModel) &&
              s.getStreamingState().detail.active.some((r) => r.id === group.id)))
        );
      },
      { id: ID, variant, detail, owner: row.owner, source: row.source_feature_ids.building[0] },
      { timeout: 240000, polling: 500 },
    );
    await page.evaluate(
      () =>
        new Promise((resolve) => {
          const m = window.__SHANGHAI_APP__.scene.map;
          m.once('render', () => {
            m.once('render', () => resolve());
            m.triggerRepaint();
          });
          m.triggerRepaint();
        }),
    );
  };
  const state = async (name, detail = false) => {
    const d = await page.evaluate(
      ({ id, source, neighbors, row }) => {
        const a = window.__SHANGHAI_APP__,
          s = a.scene,
          m = s.map,
          st = s.getStreamingState(),
          c = s.getCandidateIntegrationState();
        const sourceState = (id) =>
          m.getFeatureState({ source: 'overture-buildings', sourceLayer: 'building', id });
        const b = s.getBuildingBeaconState(),
          label = b.labelPositions.find((p) => p.id === id);
        const g = m.painter.context.gl;
        const anchor = maplibregl.MercatorCoordinate.fromLngLat([row.lng, row.lat], row.altitude || 0);
        const unit = anchor.meterInMercatorCoordinateUnits() * row.scale;
        const r = (row.heading * Math.PI) / 180,
          cs = Math.cos(r),
          sn = Math.sin(r),
          corners = [];
        for (const x of [row.bounds_glb.min[0], row.bounds_glb.max[0]])
          for (const y of [row.bounds_glb.min[1], row.bounds_glb.max[1]])
            for (const z of [row.bounds_glb.min[2], row.bounds_glb.max[2]]) {
              const world = new maplibregl.MercatorCoordinate(
                anchor.x + (cs * x - sn * z) * unit,
                anchor.y + (sn * x + cs * z) * unit,
                anchor.z + y * unit,
              );
              const corner = m.transform.coordinatePoint(
                world,
                world.toAltitude(),
                m.transform._pixelMatrix3D,
              );
              corners.push([corner.x, corner.y]);
            }

        return {
          hash: location.hash,
          name: document.querySelector('#location-name').textContent,
          mode: a.mode,
          asset: s.getLandmarkAssetState(id),
          clip: c.clips.find((x) => x.id === id),
          sourceSections: c.sourceSections?.filter((x) => x.id === id) || [],
          activeGroup: c.shader.ownerScopedSources.find(
            (x) => x.clip_feature_local_ids.includes(2764) && x.macro_id === '14-13718-6695',
          ),
          visibleMacros: st.active.filter((r) => r.visible).map((r) => r.id),
          sceneClipTriangles: c.shader.triangles,
          nearActive: st.detail.active.map((x) => x.id),
          source: sourceState(source),
          neighbors: neighbors.map((r) => ({
            id: r.localId,
            state: sourceState(r.source_key.slice('building:'.length)),
          })),
          beacons: b.count,
          label,
          picked: label && s.pickBuildingBeacon({ x: label.x, y: label.y }),
          viewport: [innerWidth, innerHeight],
          corners,
          padding: m.getPadding(),
          camera: { center: m.getCenter(), bearing: m.getBearing(), pitch: m.getPitch(), zoom: m.getZoom() },
          glError: g.getError(),
          contextLost: g.isContextLost(),
          walkDisabled: document.querySelector('#start-walk').disabled,
        };
      },
      { id: ID, source: row.source_feature_ids.building[0], neighbors: foot.context_within_approx_60m, row },
    );
    assert.equal(d.name, row.name);
    assert.equal(d.mode, 'overview');
    assert.equal(new URLSearchParams(d.hash.slice(1)).get('landmark'), ID);
    assert.equal(d.walkDisabled, true);
    assert.equal(d.contextLost, false);
    assert.equal(d.glError, 0);
    assert.equal(d.beacons, 85);
    report[name] = d;
    save();
    if (name === 'desktop' || name === 'mobile') {
      for (const [x, y] of d.corners)
        assert.ok(
          x >= d.padding.left - 0.5 &&
            x <= d.viewport[0] - d.padding.right + 0.5 &&
            y >= d.padding.top - 0.5 &&
            y <= d.viewport[1] - d.padding.bottom + 0.5,
          'Default view cuts off the delivered elevation: ' +
            JSON.stringify({ x, y, viewport: d.viewport, padding: d.padding }),
        );
    }

    assert.equal(d.picked, ID);
    const expected = row.assets[d.asset.variant === 'full' ? 'web' : 'lod'];
    assert.equal(d.asset.verifiedAsset.sha256, expected.sha256);
    assert.equal(d.asset.verifiedAsset.bytes, expected.bytes);
    assert.equal(d.asset.triangles, expected.triangles);
    assert.equal(d.asset.heading, row.heading);
    assert.deepEqual(d.asset.anchor, [row.lng, row.lat]);
    assert.deepEqual(d.clip.owner, row.owner);
    assert.deepEqual(d.clip.geometry, row.replacement_geometry);
    for (const n of d.neighbors) assert.notEqual(n.state.candidateModel, true);
    if (detail) {
      assert.deepEqual(
        [...d.activeGroup.feature_local_ids].sort((a, b) => a - b),
        [...foot.near.local_ids].sort((a, b) => a - b),
      );
      assert.deepEqual(d.activeGroup.clip_feature_local_ids, [2764]);
      assert.ok(
        d.sourceSections.some(
          (x) =>
            x.feature_local_id === 2764 &&
            x.macro_id === row.owner.macro_id &&
            x.segments === 7 &&
            Math.abs(x.roof_m - 24.1) < 0.001,
        ),
        'Missing source section for retained geometry',
      );
      assert.ok(d.activeGroup.triangles > 0);
      assert.ok(d.nearActive.includes(d.activeGroup.id));
      assert.ok(d.visibleMacros.includes(foot.owner.macro_id));
    }
    report[name] = d;
    save();
    return d;
  };
  const camera = async (zoom, pitch, bearing, elevation) => {
    await page.evaluate(
      ({ row, zoom, pitch, bearing, elevation, padding }) => {
        const s = window.__SHANGHAI_APP__.scene;
        s.map.setCenterClampedToGround(false);
        s.map.jumpTo({ center: [row.lng, row.lat], zoom, pitch, bearing, elevation, padding });
        s.loadLandmarks();
        s.refreshBuildingBeacons();
      },
      { row, zoom, pitch, bearing, elevation, padding: zeroPadding },
    );
  };
  const select = async (id) =>
    page.evaluate(async (id) => {
      const a = window.__SHANGHAI_APP__;
      await a.selectPlace(
        a.landmarks.find((p) => p.id === id),
        { mode: 'overview' },
      );
    }, id);
  const zoomCity = async () => {
    await page.evaluate((padding) => {
      const s = window.__SHANGHAI_APP__.scene;
      s.map.setMaxBounds(null);
      s.map.setCenterClampedToGround(true);
      s.map.jumpTo({ center: [121.45, 31.2], zoom: 8, pitch: 0, bearing: 0, elevation: 0, padding });
      s.refreshBuildingBeacons();
    }, zeroPadding);
    await page.waitForFunction(
      () => window.__SHANGHAI_APP__.scene.getBuildingBeaconState().viewportLabelCount === 85,
      null,
      { polling: 500 },
    );
    const b = await page.evaluate((id) => {
      const s = window.__SHANGHAI_APP__.scene,
        b = s.getBuildingBeaconState();
      return {
        count: b.count,
        districts: b.districtCount,
        staleSourceSections: s.getCandidateIntegrationState().sourceSections.filter((x) => x.id === id),
        labels: b.labelPositions,
        allHit: b.labelPositions.every((p) => s.pickBuildingBeacon({ x: p.x, y: p.y }) === p.id),
        allSprites: b.spriteIds.every((i) => s.map.hasImage(i)),
        fallback: b.overlapFallbackCount,
        target: b.labelPositions.find((p) => p.id === id),
      };
    }, ID);
    assert.ok(b.allHit && b.allSprites);
    assert.equal(b.fallback, 0);
    assert.equal(b.districts, 16);
    assert.deepEqual(b.staleSourceSections, []);
    return b;
  };
  try {
    stage('directory');
    await page.goto(new URL('landmarks.html', BASE).href, { waitUntil: 'domcontentloaded' });
    const cards = page.locator('.landmark-card[data-landmark]');
    await page.waitForFunction(
      () => document.querySelectorAll('.landmark-card[data-landmark]').length === 85,
    );
    const link = page.locator(
      '.landmark-group[id="district-310106"] .landmark-card[data-landmark="' +
        ID +
        '"] .card-foot a[href="index.html#landmark=' +
        ID +
        '&mode=overview"]',
    );
    assert.equal(await link.count(), 1);
    assert.equal(await cards.count(), 85);
    await link.click();
    stage('mobile cold start from directory');
    await ready();
    await view('main-mobile');
    await state('mobile');
    await page.setViewportSize({ width: 1000, height: 750 });
    await page.reload({ waitUntil: 'domcontentloaded' });
    stage('desktop');
    await ready(null, true);
    await state('desktop', true);
    await view('main-desktop');
    const panel = page.locator('#panel-toggle');
    if ((await panel.getAttribute('aria-expanded')) === 'true') await panel.click();
    await camera(19.1, 55, -15, 11);
    stage('garden-front with actual near city group');
    await ready('full', true);
    await state('garden', true);
    await view('main-garden-near');
    // The preflight image exposes the basemap's pink ground through the coarse
    // building above the east pediment. Compare exactly the same fixed camera.
    const sample = { left: 712, top: 280, right: 829, bottom: 307 };
    const exposedPixels = (file) => {
      const { data, width, height } = PNG.sync.read(fs.readFileSync(file));
      assert.deepEqual([width, height], [1000, 750]);
      let pink = 0;
      for (let y = sample.top; y < sample.bottom; y++)
        for (let x = sample.left; x < sample.right; x++) {
          const i = (width * y + x) * 4,
            r = data[i],
            g = data[i + 1],
            b = data[i + 2];
          if (r > 220 && r - g > 15 && b > 210) pink++;
        }
      return pink / ((sample.right - sample.left) * (sample.bottom - sample.top));
    };
    report.eastCutImageComparison = {
      sample,
      before: exposedPixels(path.join(__dirname, 'preflight', 'garden-near-open-cut.png')),
      after: exposedPixels(path.join(OUTPUT, 'main-garden-near.png')),
    };
    save();
    assert.ok(report.eastCutImageComparison.before > 0.8);
    assert.ok(report.eastCutImageComparison.after < 0.05, 'Ground showing through east cut face');

    report.groundProbes = await page.evaluate(() => {
      const s = window.__SHANGHAI_APP__.scene;
      const probes = [
        ['garden path', 121.436924188, 31.219962492, null],
        ['front clearance inside original coarse polygon', 121.436907858, 31.220014613, null],
        ['existing source behind front elevation', 121.436875196, 31.220118854, 'building'],
        ['west unmodeled remainder', 121.436269909, 31.219896361, 'building'],
        ['east unmodeled remainder', 121.43736695, 31.220147743, 'building'],
        ['west portico base', 121.436556994, 31.219956374, 'building'],
      ];
      return probes.map(([name, lng, lat, expected]) => ({
        name,
        lng,
        lat,
        expected,
        actual: s.collisionAt(lng, lat),
      }));
    });
    save();
    for (const p of report.groundProbes) assert.equal(p.actual, p.expected, p.name);

    await camera(18.9, 20, -15, 6);
    await ready('full', true);
    await state('roof', true);
    await view('main-roof-near');
    stage('distant geometry');
    await camera(15.5, 35, -15, 0);
    await ready('distant');
    await state('distant');
    stage('mobile');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForFunction(
      () => {
        const m = window.__SHANGHAI_APP__.scene.map;
        return m.transform.width === 390 && m.transform.height === 844;
      },
      null,
      { polling: 300 },
    );
    await select(ID);
    await ready();
    await state('mobileAfterResize');
    const previous = 'hongkou-general-post-office';
    for (const input of ['mouse', 'touch']) {
      stage(input + ' on map label');
      await select(previous);
      if (input === 'touch') await page.setViewportSize({ width: 320, height: 568 });
      const beacons = await zoomCity();
      report[input + 'City'] = beacons;
      if (input === 'touch') await view('main-city-85-beacons');
      if (input === 'touch') await page.touchscreen.tap(beacons.target.x, beacons.target.y);
      else await page.mouse.click(beacons.target.x, beacons.target.y);
      await page.waitForFunction(
        (id) => new URLSearchParams(location.hash.slice(1)).get('landmark') === id,
        ID,
      );
      await ready();
      await state(input + 'Selected');
    }
    stage('city source and model downloads');
    for (const [file, r] of expectedCity) {
      const response = await page.request.get(new URL(file, BASE).href),
        b = await response.body();
      assert.equal(response.status(), 200);
      assert.equal(hash(b), r.sha256);
      assert.equal(b.length, r.bytes);
      report.cityReceipts.push({
        file,
        bytes: b.length,
        sha256: hash(b),
        observedInScene: cityRequests.has(file),
        origin: response.headers()['x-audit-origin'],
      });
    }
    assert.ok(report.cityReceipts.some((r) => r.file.endsWith(foot.near.file) && r.observedInScene));
    assert.ok(report.cityReceipts.some((r) => r.file.endsWith('/far.glb') && r.observedInScene));
    report.downloads = [];
    for (const [role, a] of Object.entries(manifest.assets)) {
      const f = path.posix.join(path.posix.dirname(row.candidate_manifest), a.file);
      const r = await page.request.get(new URL(f, BASE).href);
      const b = await r.body();
      assert.equal(r.status(), 200);
      assert.equal(b.length, a.bytes);
      assert.equal(hash(b), a.sha256);
      report.downloads.push({ role, file: f, bytes: b.length, sha256: hash(b) });
    }
    for (const [f, v] of Object.entries(report.inputs)) assert.equal(hash(fs.readFileSync(filename(f))), v);
    assert.deepEqual(report.pageErrors, []);
    assert.deepEqual(report.consoleErrors, []);
    assert.deepEqual(report.networkErrors, []);
    report.completed = true;
  } catch (error) {
    report.failure = error.stack;
    throw error;
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
