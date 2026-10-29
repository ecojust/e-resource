const { chromium } = require('playwright');
const fs = require('node:fs');

(async () => {
  const commit = '0edf42c76ba0ffaabeaf8047d71f01297c0f9161';
  const url = `https://rawcdn.githack.com/ecojust/e-resource/${commit}/projects/shanghai/minglun-hall.html`;
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
    await page.waitForFunction(() => window.minglunHallViewer?.getState().status === 'ready', null, { timeout: 60000 });
    const state = await page.evaluate(() => window.minglunHallViewer.getState());
    if (errors.length || state.triangles !== 52884 || state.modelId !== 'chongming-minglun-hall') throw Error(JSON.stringify({ errors, state }));
    const referenceUrl = new URL('source/precise/chongming-minglun-hall/source-register.json', url).href;
    const reference = await page.evaluate(async refUrl => {
      const response = await fetch(refUrl);
      if (!response.ok) throw Error('Reference register HTTP ' + response.status);
      return response.json();
    }, referenceUrl);
    if (reference.museum.url !== 'https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_3.htm' || reference.asset_id !== 'chongming-minglun-hall' || reference.identity !== '崇明学宫明伦堂' || reference.height_choice.model_height_m !== 10.37 || reference.height_choice.alternate_official_height_m !== 10.5 || reference.height_choice.resolved !== false || reference.photo.sha256 !== 'f8bdcb9fcca717b05a74edceb86fd87824847e1e0c99c0be545d75b30ee2c6c4') throw Error('Wrong Minglun Hall identity or reference scope');
    const result = { url, commit, state, errors, hostingNoticeClicked, referenceUrl, documentarySource: reference.museum.url,
      scope: 'Public pinned-commit page loaded and model SHA256 verified through viewer; local geometry and controls evidence retained separately' };
    fs.writeFileSync('projects/shanghai/data/audit/minglun-hall-v1/public-browser.json', JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
