const {chromium} = require('playwright');
const {createHash} = require('node:crypto');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');

const [base, output, local] = process.argv.slice(2);
const id = 'huangpu-bank-of-taiwan-building';
const sha = b => createHash('sha256').update(b).digest('hex');
const catalogPath = 'data/candidate-city-integrations.json';
const catalogBytes = fs.readFileSync(path.join(local, catalogPath));
const catalog = JSON.parse(catalogBytes);
const row = catalog.models.find(m => m.id === id);
assert.equal(catalog.resulting_city_count, 153);
const manifest = JSON.parse(fs.readFileSync(path.join(local,row.candidate_manifest)));
const report = {id,base,viewport:[390,844],catalog:sha(catalogBytes),script:sha(fs.readFileSync(__filename)),views:[],errors:[],files:[]};
fs.mkdirSync(output,{recursive:true});
const save = () => fs.writeFileSync(path.join(output,'phone-zoom.json'),JSON.stringify(report,null,2)+'\n');

async function main() {
  const browser = await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page = await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  const expectedFiles = [catalogPath,row.candidate_manifest,path.posix.join(path.posix.dirname(row.candidate_manifest),manifest.assets.full.file)];
  const match = new Map(); const pending = [];
  page.on('pageerror', e=>report.errors.push(e.message));
  page.on('response', response=>{
    const url=new URL(response.url()),file=url.pathname.slice(1);
    if(url.origin!==new URL(base).origin||response.status()!==200||!expectedFiles.includes(file))return;
    pending.push(response.body().then(bytes=>{
      match.set(file,{file,sha256:sha(bytes),bytes:bytes.length,url:response.url(),via:'page response'});
    }).catch(()=>{}));
  });
  async function view(name) {
    await page.waitForFunction(id => {
      const s=window.__SHANGHAI_APP__?.scene;
      const c=document.querySelector('#loading');
      if(!s || !c || !c.classList.contains('loaded') || getComputedStyle(c).visibility!=='hidden' || s.map.isMoving())return false;
      const model=s.getLandmarkAssetState(id);
      const target=s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.clip_feature_local_ids?.includes(228));
      return model?.visible && model.status==='loaded' && model.variant==='full' && target;
    },id,{polling:350,timeout:300000});
    const state=await page.evaluate(id=>{
      const s=window.__SHANGHAI_APP__.scene,m=s.map;
      return {name:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],camera:{center:m.getCenter(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},target:s.getLandmarkAssetState(id),label:s.getBuildingBeaconState().labelPositions.find(v=>v.id===id)};
    },id);
    const f=name+'.png';const bytes=await page.screenshot({path:path.join(output,f),timeout:240000});
    report.views.push({name,file:f,sha256:sha(bytes),...state});save();console.log(name, state.camera.zoom);
  }
  try {
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
    assert.equal(await page.locator('.landmark-card[data-landmark]').count(),153);
    await page.locator('[data-landmark="'+id+'"] .card-foot a[href^="index.html"]').tap();
    await view('phone-warm-default');
    for(const [name,step] of [['phone-normal-plus',1],['phone-second-plus',2]]){
      const old=report.views.at(-1).camera.zoom;
      await page.locator('#zoom-in').tap();
      await page.waitForFunction(z=>window.__SHANGHAI_APP__?.scene?.map?.getZoom()>z+.49,old,{polling:200,timeout:120000});
      await view(name);
    }
    await Promise.all(pending);
    for(const file of expectedFiles){
      if(!match.has(file)){
        const response=await page.request.get(new URL(file,base).href);
        assert.equal(response.status(),200,file);const bytes=await response.body();
        match.set(file,{file,sha256:sha(bytes),bytes:bytes.length,url:response.url(),via:'explicit browser re-fetch'});
      }
      const receipt=match.get(file);assert.equal(receipt.sha256,sha(fs.readFileSync(path.join(local,file))),file);
      report.files.push(receipt);
    }
    assert.deepEqual(report.errors,[]);report.completed=true;
  } catch(e) {report.failure=e.stack;throw e;}
  finally{await browser.close();report.browser_closed=true;save();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
