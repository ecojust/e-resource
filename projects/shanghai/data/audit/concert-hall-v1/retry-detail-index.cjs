/* Retry the normal same-origin city detail loader after an observed startup timeout. */
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const {chromium} = require('playwright');
const endpoint = process.env.QA_CDP_ENDPOINT;
const out = process.env.QA_RETRY_REPORT;
async function run() {
  assert.ok(endpoint && out && !fs.existsSync(out));
  const browser = await chromium.connectOverCDP(endpoint);
  const page = browser.contexts().flatMap(ctx => ctx.pages()).find(p => p.url().includes('#landmark=huangpu-shanghai-concert-hall'));
  assert.ok(page);
  const session = await page.context().newCDPSession(page);
  const warnings = [];
  session.on('Runtime.consoleAPICalled', event => {
    if(event.type === 'warning') warnings.push(event.args.map(a => a.value || a.description || '').join(' ').split('\n')[0]);
  });
  await session.send('Runtime.enable');
  const at = new Date().toISOString();
  assert.ok(warnings.some(text => text.includes('本地建筑目录暂不可用') && text.includes('timed out')));
  const change = await page.evaluate(async () => {
    const scene = window.__SHANGHAI_APP__.scene;
    const old = scene.getStreamingState().detail;
    const retried = await scene.setCityManifest('assets/city-detail/manifest.json');
    return {before:{parents:old.parents,visible:old.visible},fallback:Boolean(retried.fallback),error:retried.error||null};
  });
  const proof = {at,action:'Retry the unchanged city-detail manifest through scene.setCityManifest after the application reported its 25-second startup timeout.',run:page.url(),startup_warnings:warnings,change,script_sha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex')};
  fs.writeFileSync(out,JSON.stringify(proof,null,2)+'\n');
  assert.equal(change.fallback,false);
  await session.detach();
}
run().then(()=>process.exit(0)).catch(error=>{console.error(error);process.exit(1);});
