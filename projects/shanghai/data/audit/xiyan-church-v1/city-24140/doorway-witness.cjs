const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const root = '/workspace/e-resource/projects/shanghai';
const audit = path.join(root, 'data/audit/xiyan-church-v1');
const read = file => JSON.parse(fs.readFileSync(file));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const baseline = read(path.join(__dirname,'city/main-browser.json'));
const contract = read(path.join(audit, 'final-placement-contract.json'));
const site = baseline.server;
const id = baseline.id;
const baseView = baseline.views.find(v => v.view === 'map-recessed-arch-entrance');
const door = baseline.ground.find(v => v.name === 'closed northeast door');
const out = path.resolve(process.argv[2]);
fs.mkdirSync(out,{recursive:true});
const report = {id,site,started:new Date().toISOString(),caseSha256:sha(fs.readFileSync(path.join(audit,'map-case.json'))),scriptSha256:sha(fs.readFileSync(__filename)),responses:{},httpErrors:[],pageErrors:[],passed:false};
const file = path.join(out,'doorway.json');
assert.ok(!fs.existsSync(file));
const save=()=>fs.writeFileSync(file,JSON.stringify(report,null,2)+'\n');
async function run() {
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  try {
    const page=await browser.newPage({viewport:{width:1024,height:680}});
    const pending=[];
    const high=baseline.files.find(x=>x.file.endsWith('-web.glb'));
    assert.ok(high);
    const expect={'data/candidate-city-integrations.json':baseline.catalog.sha256,'src/map-scene.js':baseline.bindings['src/map-scene.js'],[high.file]:high.sha256};
    page.on('pageerror',err=>report.pageErrors.push(String(err)));
    page.on('response',r=>{
      const url=new URL(r.url());
      if(url.origin!==new URL(site).origin)return;
      if(r.status()>=400){report.httpErrors.push({status:r.status(),url:r.url()});save();}
      const k=url.pathname.slice(1);
      if(r.status()===200 && Object.hasOwn(expect,k))pending.push(r.body().then(b=>{assert.equal(sha(b),expect[k]);report.responses[k]={bytes:b.length,sha256:sha(b)};}));
    });
    await page.goto(new URL('index.html#landmark='+id+'&mode=overview',site).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()),null,{timeout:180000});
    const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
    const camera={...baseView.camera,center:[baseView.camera.center.lng,baseView.camera.center.lat],elevation:2.7,pitch:65,zoom:21.63,padding:{left:350,right:0,top:0,bottom:12}};
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
    await page.waitForFunction(id=>{
      const s=window.__SHANGHAI_APP__?.scene,l=document.querySelector('#loading'),a=s?.getLandmarkAssetState(id);
      return l?.classList.contains('loaded')&&getComputedStyle(l).visibility==='hidden'&&!s.map.isMoving()&&a?.status==='loaded'&&a.visible&&a.variant==='full';
    },id,{polling:250,timeout:240000});
    report.scene=await page.evaluate(({id,door})=>{
      const s=window.__SHANGHAI_APP__.scene,map=s.map,gl=map.painter.context.gl;
      const rect=document.querySelector('#location-name').closest('section').getBoundingClientRect().toJSON();
      const p=map.project(door.position);const box=map.getCanvas().getBoundingClientRect();
      return {camera:{center:map.getCenter(),zoom:map.getZoom(),pitch:map.getPitch(),bearing:map.getBearing(),padding:map.getPadding()},viewport:[innerWidth,innerHeight],door_ground:s.collisionAt(...door.position),screen:{x:p.x+box.x,y:p.y+box.y},card:rect,asset:s.getLandmarkAssetState(id),glError:gl.getError(),contextLost:gl.isContextLost(),route:location.hash};
    },{id,door});
    assert.equal(report.scene.door_ground,'building');assert.equal(report.scene.asset.verifiedAsset.sha256,high.sha256);assert.equal(report.scene.asset.triangles,baseView.asset.triangles);
    const {screen,card}=report.scene;const clear=screen.x>card.right+35||screen.x<card.left-35||screen.y<card.top-45||screen.y>card.bottom+35;
    assert.ok(clear&&screen.x>115&&screen.x<945&&screen.y>120&&screen.y<600,JSON.stringify({screen,card}));
    assert.equal(report.scene.glError,0);assert.equal(report.scene.contextLost,false);
    const name='map-door-beside-place-card.png';const image=await page.screenshot({path:path.join(out,name),timeout:180000});
    await Promise.all(pending);
    assert.deepEqual(Object.keys(report.responses).sort(),Object.keys(expect).sort());
    assert.deepEqual(report.pageErrors,[]);assert.deepEqual(report.httpErrors,[]);
    report.image={file:name,bytes:image.length,sha256:sha(image)};report.passed=true;
  }catch(e){report.error=e.stack;throw e;}
  finally{await browser.close();report.closed=true;report.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
