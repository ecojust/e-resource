const { chromium } = require('playwright');
const fs = require('node:fs');

(async () => {
  const commit = '6673d31dee681d219078b58bc658d77a0aa4e1e5';
  const url = `https://rawcdn.githack.com/ecojust/e-resource/${commit}/projects/shanghai/west-paifang.html`;
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
    await page.waitForFunction(() => window.westPaifangViewer?.getState().status === 'ready', null, { timeout: 60000 });
    const state = await page.evaluate(() => window.westPaifangViewer.getState());
    if (errors.length || state.triangles !== 92848 || state.modelId !== 'chongming-xuehai-paifang') throw Error(JSON.stringify({ errors, state }));
    const referenceUrl = new URL('source/precise/chongming-xuehai-paifang/source-register.json', url).href;
    const reference = await page.evaluate(async refUrl => {
      const response = await fetch(refUrl);
      if (!response.ok) throw Error('Reference register HTTP ' + response.status);
      return response.json();
    }, referenceUrl);
    if (reference.museum.url !== 'https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_1.htm' || reference.asset_id !== 'chongming-xuehai-paifang' || reference.identity !== '崇明学宫西牌坊（题名面待核）' || reference.inscription_face_acceptance !== false || reference.official_physical_identity.url !== 'https://www.shcm.gov.cn/zjcm/006008/20210423/8c183cc2-f5a9-4d52-b152-9d72ec7eb5a7.html') throw Error('Wrong West Paifang identity or inscription acceptance');
    const result = { url, commit, state, errors, hostingNoticeClicked, referenceUrl, documentarySource: reference.museum.url,
      scope: 'Public pinned-commit page loaded and model SHA256 verified through viewer; local geometry and controls evidence retained separately' };
    fs.writeFileSync('projects/shanghai/data/audit/west-paifang-v1/public-browser.json', JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
