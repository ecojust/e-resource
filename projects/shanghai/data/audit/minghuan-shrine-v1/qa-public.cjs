const { chromium } = require('playwright');
const fs = require('node:fs');

(async () => {
  const commit = '0727e5441bcbab99979ea05dfce753a07edbfba2';
  const url = `https://rawcdn.githack.com/ecojust/e-resource/${commit}/projects/shanghai/minghuan-shrine.html`;
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
    await page.waitForFunction(() => window.minghuanShrineViewer?.getState().status === 'ready', null, { timeout: 60000 });
    const state = await page.evaluate(() => window.minghuanShrineViewer.getState());
    if (errors.length || state.triangles !== 25324) throw Error(JSON.stringify({ errors, state }));
    const referenceUrl = new URL('source/precise/chongming-minghuan-shrine/source-register.json', url).href;
    const reference = await page.evaluate(async refUrl => {
      const response = await fetch(refUrl);
      if (!response.ok) throw Error('Reference register HTTP ' + response.status);
      return response.json();
    }, referenceUrl);
    if (reference.official_location.url !== 'https://www.shcm.gov.cn/zjcm/006008/20210423/8c183cc2-f5a9-4d52-b152-9d72ec7eb5a7.html') throw Error('Wrong official location reference');
    const result = { url, commit, state, errors, hostingNoticeClicked, referenceUrl, officialLocationSource: reference.official_location.url,
      scope: 'Public pinned-commit page loaded and model SHA256 verified through viewer; local geometry and controls evidence retained separately' };
    fs.writeFileSync('projects/shanghai/data/audit/minghuan-shrine-v1/public-browser.json', JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
