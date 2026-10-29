// Usage: node qa-browser.cjs BASE_URL OUTPUT_DIRECTORY
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const assert = require('node:assert/strict');
const base = process.argv[2] || 'http://127.0.0.1:8000/';
const output = process.argv[3] || __dirname;
const project = path.resolve(__dirname, '../../..');
const viewers = JSON.parse(fs.readFileSync(path.join(project, 'data/model-viewers.json')));
const globals = ['soongViewer','luxunViewer','sunYatsenViewer','zunjingViewer','panPoolViewer','dachengHallViewer','surfaceViewer'];
const consent = async p => { const button = p.getByText('Open the page', {exact:true}); if (await button.count()) await button.click(); };
(async () => {
  fs.mkdirSync(output,{recursive:true});
  const browser = await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors = [], failures = [], report = {base, viewers:[], errors, failures};
    page.on('pageerror',e=>errors.push(e.message));
    page.on('response',r=>{if(r.status()>=400 && r.url().startsWith(base)) failures.push({url:r.url(),status:r.status()});});
    const directory = async () => { await page.goto(base+'landmarks.html'); await consent(page); await page.waitForSelector('.directory-search:not([hidden])'); };
    await directory();
    assert.equal(await page.locator('[data-landmark]').count(),38);
    assert.equal(await page.locator('[data-viewer]').count(),7);
    for (const [query,count] of [['崇明',3],['宋庆龄',1],['不存在的模型',0]]) {
      await page.fill('#landmark-search',query);
      assert.equal(await page.locator('.landmark-card:visible').count(),count);
    }
    await page.click('.group-nav a[href="#models"]');
    assert.equal(await page.inputValue('#landmark-search'),'');
    assert.equal(await page.locator('.landmark-card:visible').count(),45);
    await page.screenshot({path:path.join(output,'directory-desktop.png')});
    for (let i=0;i<viewers.length;i++) {
      const row=viewers[i], global=globals[i];
      await directory();
      await page.locator(`[data-viewer="${row.id}"]`).click();
      await consent(page);
      await page.waitForFunction(name=>window[name]?.getState().status==='ready',global,{timeout:120000});
      assert.equal(new URL(page.url()).pathname.split('/').pop(),row.page);
      const record={id:row.id,url:page.url()};
      if(row.kind==='candidate') {
        const manifest=JSON.parse(fs.readFileSync(path.join(project,row.manifest)));
        for(const variant of ['full','lod']) {
          await page.selectOption('#detail',variant);
          await page.waitForFunction(({name,variant})=>{const s=window[name].getState();return s.status==='ready'&&s.variant===variant&&s.renderedTriangles>0},{name:global,variant},{timeout:120000});
          const state=await page.evaluate(name=>window[name].getState(),global);
          assert.equal(state.triangles,manifest.assets[variant].triangles);
          assert.equal(state.error,null);
          record[variant]=state;
        }
      } else {
        record.state=await page.evaluate(name=>window[name].getState(),global);
        assert.ok(record.state.triangles>0 && record.state.visibleDistricts.length>0);
      }
      await page.screenshot({path:path.join(output,row.id+'.png')});
      report.viewers.push(record);
      console.log('PASS',row.id);
    }
    await page.setViewportSize({width:390,height:844});
    await directory();
    await page.fill('#landmark-search','宋庆龄');
    assert.equal(await page.locator('.landmark-card:visible').count(),1);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:path.join(output,'directory-mobile.png')});
    report.mobile={width:390,height:844,noHorizontalOverflow:true,searchPassed:true};
    const nojs=await browser.newPage({javaScriptEnabled:false});
    await nojs.goto(base+'landmarks.html');await consent(nojs);
    assert.equal(await nojs.locator('[data-landmark]').count(),38);
    assert.equal(await nojs.locator('[data-viewer]').count(),7);
    report.noJavaScriptLinks=45;
    assert.deepEqual(errors,[]);assert.deepEqual(failures,[]);
    fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify(report,null,2)+'\n');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exit(1)});
