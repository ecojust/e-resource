const { chromium } = require('playwright');
const { createHash } = require('node:crypto');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const [base, route, label, expectedPage, output] = process.argv.slice(2);
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

async function main() {
  fs.mkdirSync(output, {recursive: true});
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']
  });
  const report = {base, route, label, expectedPage, script: sha(fs.readFileSync(__filename)), views: []};
  try {
    for (const [type, viewport] of [['desktop', {width: 1250, height: 820}], ['mobile', {width: 390, height: 844}]]) {
      const mobile = type === 'mobile';
      const page = await browser.newPage({viewport, isMobile: mobile, hasTouch: mobile});
      const response = await page.goto(new URL(route, base).href);
      assert.equal(sha(await response.body()), expectedPage);
      await page.waitForFunction(() => document.querySelector('#status').textContent.startsWith('近景 ·'));
      const control = page.getByRole('button', {name: label, exact: true});
      assert.equal(await control.getAttribute('data-view'), 'oblique');
      const canvas = page.locator('#model-view canvas');
      const front = page.getByRole('button', {name: '南园敞廊', exact: true});
      if (mobile) await front.tap(); else await front.click();
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const before = sha(await canvas.screenshot());
      if (mobile) await control.tap();
      else await control.click();
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
      const after = sha(await canvas.screenshot());
      assert.notEqual(after, before);
      const file = 'oblique-' + type + '.png';
      const bytes = await page.screenshot({path: path.join(output, file)});
      report.views.push({type, file, sha256: sha(bytes), viewport, before, after, status: await page.locator('#status').innerText()});
      await page.close();
    }
    report.passed = true;
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(output, 'oblique.json'), JSON.stringify(report, null, 2) + '\n');
  }
}
main().catch(error => {console.error(error); process.exitCode=1;});
