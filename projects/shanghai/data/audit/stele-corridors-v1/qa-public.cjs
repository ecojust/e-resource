const { chromium } = require('playwright');
const fs = require('node:fs');

(async () => {
  const commit = '9c2ae34985b47c260fd230b602c855d11ec46176';
  const url = `https://rawcdn.githack.com/ecojust/e-resource/${commit}/projects/shanghai/stele-corridors.html`;
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', headless: true,
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('response', r => { if (r.status() >= 400) errors.push(`${r.status()} ${r.url()}`); });
    await page.goto(url);
    let hostingNoticeClicked = false;
    if (await page.getByText('Open the page', { exact: true }).count()) {
      await page.getByText('Open the page', { exact: true }).click();
      hostingNoticeClicked = true;
      errors.length = 0;
    }
    await page.waitForFunction(() => window.steleCorridorsViewer?.getState().status === 'ready', null, { timeout: 60000 });
    const state = await page.evaluate(() => window.steleCorridorsViewer.getState());
    if (errors.length || state.triangles !== 232696 || state.modelId !== 'chongming-stele-corridors') throw Error(JSON.stringify({ errors, state }));
    const referenceUrl = new URL('source/precise/chongming-stele-corridors/source-register.json', url).href;
    const reference = await page.evaluate(async refUrl => {
      const response = await fetch(refUrl);
      if (!response.ok) throw Error('Reference register HTTP ' + response.status);
      return response.json();
    }, referenceUrl);
    if (reference.museum.url !== 'https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_3.htm' || reference.asset_id !== 'chongming-stele-corridors' || reference.identity !== '崇明学宫碑廊（两长边分段候选）' || reference.museum.documented_facts.total_length_m !== 76.7 || reference.modeled_scope.long_side_baseline_total_length_m !== 61 || reference.modeled_scope.north_south_geometry_created !== false || reference.display_layout.centre_separation_m !== 7 || reference.display_layout.placement_only_not_courtyard_measurement !== true) throw Error('Wrong stele corridors identity or incomplete-layout scope');
    const result = { url, commit, state, errors, hostingNoticeClicked, referenceUrl, documentarySource: reference.museum.url,
      scope: 'Public pinned-commit page loaded and model SHA256 verified through viewer; local geometry and controls evidence retained separately' };
    fs.writeFileSync('projects/shanghai/data/audit/stele-corridors-v1/public-browser.json', JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
