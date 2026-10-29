const { chromium } = require('playwright');
const fs = require('node:fs');

(async () => {
  const commit = '9eb58f131439840c0a9aa01e8c6d3c7f6bafcd1c';
  const url = `https://rawcdn.githack.com/ecojust/e-resource/${commit}/projects/shanghai/yimen.html`;
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
    await page.waitForFunction(() => window.yimenViewer?.getState().status === 'ready', null, { timeout: 60000 });
    const state = await page.evaluate(() => window.yimenViewer.getState());
    if (errors.length || state.triangles !== 57896 || state.modelId !== 'chongming-yimen') throw Error(JSON.stringify({ errors, state }));
    const referenceUrl = new URL('source/precise/chongming-yimen/source-register.json', url).href;
    const reference = await page.evaluate(async refUrl => {
      const response = await fetch(refUrl);
      if (!response.ok) throw Error('Reference register HTTP ' + response.status);
      return response.json();
    }, referenceUrl);
    if (reference.museum.url !== 'https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_3.htm' || reference.asset_id !== 'chongming-yimen' || reference.identity !== '崇明学宫仪门' || reference.model_dimension_choice.estimated_model_height_m !== 7 || reference.model_dimension_choice.documented_height_m !== 9.07 || reference.model_dimension_choice.height_reconciled !== false || reference.photo.image_sha256 !== '5df50470b57599bf86df1c02c003a5f021600ef747e118f580f052f0b028a5cc') throw Error('Wrong Yimen identity or dimensional/photo reference scope');
    const result = { url, commit, state, errors, hostingNoticeClicked, referenceUrl, documentarySource: reference.museum.url,
      scope: 'Public pinned-commit page loaded and model SHA256 verified through viewer; local geometry and controls evidence retained separately' };
    fs.writeFileSync('projects/shanghai/data/audit/yimen-v1/public-browser.json', JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
