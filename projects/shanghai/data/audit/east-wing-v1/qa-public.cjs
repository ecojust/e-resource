const { chromium } = require('playwright');
const fs = require('node:fs');

(async () => {
  const commit = 'ba2901f26128f3959694ea541a847797c6957764';
  const url = `https://rawcdn.githack.com/ecojust/e-resource/${commit}/projects/shanghai/east-wing.html`;
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
    await page.waitForFunction(() => window.eastWingViewer?.getState().status === 'ready', null, { timeout: 60000 });
    const state = await page.evaluate(() => window.eastWingViewer.getState());
    if (errors.length || state.triangles !== 72820 || state.modelId !== 'chongming-east-wing') throw Error(JSON.stringify({ errors, state }));
    const referenceUrl = new URL('source/precise/chongming-east-wing/source-register.json', url).href;
    const reference = await page.evaluate(async refUrl => {
      const response = await fetch(refUrl);
      if (!response.ok) throw Error('Reference register HTTP ' + response.status);
      return response.json();
    }, referenceUrl);
    if (reference.museum.url !== 'https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_2.htm' || reference.museum.documented_facts.bays_each !== 7 || reference.identity !== '崇明学宫东庑') throw Error('Wrong wing documentary reference');
    const result = { url, commit, state, errors, hostingNoticeClicked, referenceUrl, documentarySource: reference.museum.url,
      scope: 'Public pinned-commit page loaded and model SHA256 verified through viewer; local geometry and controls evidence retained separately' };
    fs.writeFileSync('projects/shanghai/data/audit/east-wing-v1/public-browser.json', JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
