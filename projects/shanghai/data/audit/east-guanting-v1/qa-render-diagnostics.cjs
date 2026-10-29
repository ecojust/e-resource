const { chromium } = require('playwright');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const results=[];
  for (const variant of ['baseline','normal-zero','plaster-flat','no-shadow','raw-source']) {
    const context=await browser.newContext({viewport:{width:1440,height:1000}});
    const page=await context.newPage(); const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/src/east-guanting.js',async route=>{
      const response=await route.fetch(); let body=await response.text();
      if(variant==='raw-source')body=body.replace("const record=manifest.assets[variant];","const record=variant==='full'?manifest.assets.raw:manifest.assets[variant];");
      if(variant==='normal-zero')body=body.replace('sun.shadow.normalBias=.025','sun.shadow.normalBias=0');
      if(variant==='no-shadow')body=body.replace('renderer.shadowMap.enabled=true','renderer.shadowMap.enabled=false');
      body=body.replace('candidate.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});',`window.shadowDiagnosticMaterials=[];candidate.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;for(const material of (Array.isArray(o.material)?o.material:[o.material])){if(${JSON.stringify(variant)}==='plaster-flat'&&material.name==='plaster'){material.flatShading=true;material.needsUpdate=true;}window.shadowDiagnosticMaterials.push({name:material.name,flatShading:material.flatShading});}}});`);
      await route.fulfill({response,body});
    });
    await page.goto('http://127.0.0.1:8774/east-guanting.html');
    await page.waitForFunction(()=>window.eastGuantingViewer?.getState().status==='ready',null,{timeout:60000});
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    await page.screenshot({path:`/tmp/east-guanting-shadow-${variant}.png`});
    results.push({variant,viewer:await page.evaluate(()=>window.eastGuantingViewer.getState()),materials:await page.evaluate(()=>window.shadowDiagnosticMaterials),errors});
    await context.close();
  }
  fs.writeFileSync('/tmp/east-guanting-render-diagnostic.json',JSON.stringify(results,null,2)+'\n');
  console.log(JSON.stringify(results));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
