/* Follow real keyboard locomotion and distinguish independent animation frames at each wall. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');

const base = process.env.MODEL_BASE_URL;
const out = process.env.QA_OUTPUT_DIR;
const project = process.env.SHANGHAI_PROJECT_ROOT;
const id = 'jingan-bubbling-well-lane-gate';
const hash = data => createHash('sha256').update(data).digest('hex');
const contract = JSON.parse(fs.readFileSync(path.join(__dirname,'final-placement-contract.json')));
const heading = contract.heading * Math.PI / 180;
const radius = 6371008.8 * Math.cos(contract.lat * Math.PI / 180);
const north0 = Math.asinh(Math.tan(contract.lat * Math.PI / 180));
function point(x, y) {
  const east = x * Math.cos(heading) + y * Math.sin(heading);
  const north = -x * Math.sin(heading) + y * Math.cos(heading);
  return [contract.lng + east / radius * 180 / Math.PI, Math.atan(Math.sinh(north0 + north / radius)) * 180 / Math.PI];
}
function local(lng, lat) {
  const e = radius * (lng - contract.lng) * Math.PI / 180, n = radius * (Math.asinh(Math.tan(lat * Math.PI / 180)) - north0);
  return [e * Math.cos(heading) - n * Math.sin(heading), e * Math.sin(heading) + n * Math.cos(heading)];
}
async function run() {
  if (!base || !out || !project) throw Error('Supply MODEL_BASE_URL, QA_OUTPUT_DIR and SHANGHAI_PROJECT_ROOT');
  fs.mkdirSync(out,{recursive:true});
  const files = ['data/candidate-city-integrations.json','src/app.js','src/map-scene.js','src/walk-controller.js'];
  const report = {id, base, started:new Date().toISOString(), scriptSha256:hash(fs.readFileSync(__filename)), files:{}, views:[], wallTests:[], poses:[], errors:[], completed:false};
  const save = () => fs.writeFileSync(path.join(out,'passage-browser.json'),JSON.stringify(report,null,2)+'\n');
  const browser = await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const page = await browser.newPage({viewport:{width:820,height:580},ignoreHTTPSErrors:true});
  page.setDefaultTimeout(280000);
  page.on('pageerror',e=>report.errors.push(e.message));
  async function snapshot(key) {
    const s = await page.evaluate(({key,id}) => {
      const app=window.__SHANGHAI_APP__, c=app.controller, scene=app.scene, asset=scene.getLandmarkAssetState(id);
      const side=key==='a'?-1:key==='d'?1:0;
      const h=c.bearing*Math.PI/180;
      const e=(side?side*Math.cos(h):Math.sin(h))*.425, n=(side?-side*Math.sin(h):Math.cos(h))*.425;
      const target={lng:c.position.lng+e/6378137/Math.cos(c.position.lat*Math.PI/180)*180/Math.PI,lat:c.position.lat+n/6378137*180/Math.PI};
      return {frame:c._previousTime,position:{...c.position},speed:c.speed,held:[...c.keys],standing:scene.collisionAt(c.position.lng,c.position.lat),nextSweep:c._canOccupy(target,e,n),bearing:c.bearing,mode:c.mode,visible:asset.visible,variant:asset.variant,sha256:asset.verifiedAsset.sha256,notice:document.querySelector('#toast')?.textContent||null};
    },{key,id});
    return {...s,xy:local(s.position.lng,s.position.lat)};
  }
  async function select(x, y) {
    await page.evaluate(async ({start,bearing}) => {
      const app=window.__SHANGHAI_APP__;
      await app.selectPlace({id:'selected-location',name:'自选街区',custom:true,districtId:'310106',walkStart:start,bearing},{mode:'walk'});
    },{start:point(x,y),bearing:contract.heading});
    await page.waitForFunction(id=>{const a=window.__SHANGHAI_APP__,state=a.scene.getLandmarkAssetState(id);return a.mode==='walk'&&state?.visible&&state.status==='loaded';},id);
    await page.locator('canvas.maplibregl-canvas').focus();
  }
  async function drive(key, finished) {
    const captures=[],end=Date.now()+700000;let lastFrame;
    await page.keyboard.down('Shift');await page.keyboard.down(key);
    try {
      while(Date.now()<end){
        const s=await snapshot(key);
        if(s.frame!==lastFrame){
          captures.push(s);lastFrame=s.frame;
          report.current={key,captures};save();
          if(finished(captures))return captures;
        }
        await page.waitForTimeout(350);
      }
      throw Error('Held '+key+' exceeded run limit '+JSON.stringify(captures.at(-1)));
    } finally {await page.keyboard.up(key);await page.keyboard.up('Shift');}
  }
  async function picture(name) {
    await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>resolve());m.triggerRepaint();}));
    const bytes=await page.screenshot({path:path.join(out,name+'.png'),timeout:210000});
    report.views.push({file:name+'.png',width:820,height:580,bytes:bytes.length,sha256:hash(bytes),pose:await snapshot('w')});save();
  }
  try {
    for(const f of files){
      const res=await page.request.get(new URL(f,base).href);
      const b=await res.body();assert.equal(res.status(),200);assert.equal(hash(b),hash(fs.readFileSync(path.join(project,f))));report.files[f]=hash(b);
    }
    const cat=JSON.parse(fs.readFileSync(path.join(project,files[0])));
    assert.equal(cat.resulting_city_count,104);assert.equal(cat.models.at(-1).id,id);
    await page.goto(new URL('index.html#landmark='+id+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(id=>{const a=window.__SHANGHAI_APP__;return a?.scene.getLandmarkAssetState(id)?.status==='loaded';},id);
    const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
    // Each view repeats part of the previously verified 12.31m trip at desktop width.
    for(const [name,start,stop] of [['map-passage-desktop',2.2,2.8],['map-courtyard-desktop',8.45,9.0]]){
      await select(0,start);const frames=await drive('w', rows=>rows.at(-1).xy[1]>=stop);
      assert.ok(frames.every(f=>f.held.includes('KeyW')&&!f.standing&&Math.abs(f.xy[0])<.01&&f.sha256===cat.models.at(-1).assets.web.sha256));
      report.poses.push({name,frames});delete report.current;await picture(name);
    }
    await page.setViewportSize({width:460,height:360});
    for(const [key,sign] of [['a',-1],['d',1]]){
      await select(sign*.80,3.55);
      const frames=await drive(key, rows=>{
        const last=rows.slice(-4);return last.length===4&&last.every(r=>sign*r.xy[0]>1.10&&r.nextSweep==='building')&&Math.max(...last.map(r=>r.xy[0]))-Math.min(...last.map(r=>r.xy[0]))<.08;
      });
      assert.ok(frames.every(r=>!r.standing&&Math.abs(r.xy[0])<1.96&&r.held.includes(key==='a'?'KeyA':'KeyD')));
      const last=frames.slice(-4);assert.equal(new Set(last.map(r=>r.frame)).size,4);
      report.wallTests.push({key,side:sign<0?'left':'right',first:frames[0],last:frames.at(-1),blockedAnimationFrames:last.map(r=>r.frame),frames});delete report.current;save();
    }
    assert.deepEqual(report.errors,[]);report.completed=true;
  } catch(e) {report.failure=e.stack;throw e;}
  finally {report.finished=new Date().toISOString();save();await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
