/* Capture the ordinary 1280-pixel desktop map with the production panel and signs. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const [site,base,out]=process.argv.slice(2),id='huangpu-moore-memorial-church';
const sha=value=>crypto.createHash('sha256').update(value).digest('hex');
const catalog=JSON.parse(fs.readFileSync(path.join(site,'data/candidate-city-integrations.json')));
const row=catalog.models.find(a=>a.id===id);
const result={id,started:new Date().toISOString(),source:base,completed:false,script_sha256:sha(fs.readFileSync(__filename))};
async function run(){
  fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  try{
    const page=await browser.newPage({viewport:{width:1280,height:800},ignoreHTTPSErrors:true});
    const loads=new Map();
    page.on('response',r=>{const u=new URL(r.url());if(u.origin===new URL(base).origin&&r.status()===200)loads.set(u.pathname.slice(1),r);});
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
    const card=page.locator('#district-310101 [data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]');
    await card.click({timeout:90000});
    await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__?.scene,m=s?.map,a=s?.getLandmarkAssetState(id);
      return !m?.isMoving()&&a?.variant==='full'&&a.verifiedAsset?.sha256&&s.getBuildingBeaconState().labelPositions.some(p=>p.id===id);
    },id,{polling:650,timeout:420000});
    result.page=await page.evaluate(id=>{
      const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState(),m=s.map,l=b.labelPositions.find(p=>p.id===id);
      return {url:location.href,view:[innerWidth,innerHeight],center:m.getCenter(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),selected:s.pickBuildingBeacon({x:l.x,y:l.y}),total:b.count,labels:b.labelPositions,asset:s.getLandmarkAssetState(id),panel:document.querySelector('#panel-toggle').getAttribute('aria-expanded'),webgl_lost:m.painter.context.gl.isContextLost()};
    },id);
    assert.equal(result.page.selected,id);assert.equal(result.page.total,109);assert.equal(result.page.webgl_lost,false);
    const manifest=JSON.parse(fs.readFileSync(path.join(site,row.candidate_manifest)));
    assert.equal(result.page.asset.verifiedAsset.sha256,manifest.assets.full.sha256);
    const file=path.posix.join(path.posix.dirname(row.candidate_manifest),manifest.assets.full.file);
    result.receipts={};for(const f of ['index.html','data/candidate-city-integrations.json','src/app.js','src/map-scene.js',file]){const r=loads.get(f);assert(r,f);const h=sha(await r.body());assert.equal(h,sha(fs.readFileSync(path.join(site,f))));result.receipts[f]=h;}
    // A loaded verified GLB can appear behind the startup screen while the main
    // city waits for its baseline data. Wait for the same visible map a user sees.
    await page.waitForFunction(()=>{
      const el=document.querySelector('#loading'),s=el&&getComputedStyle(el),map=window.__SHANGHAI_APP__?.scene?.map;
      return el?.classList.contains('loaded')&&s.opacity==='0'&&s.visibility==='hidden'&&s.pointerEvents==='none'&&!map.isMoving();
    },null,{polling:300,timeout:420000});
    result.visible_frames=await page.evaluate(async()=>{
      const states=[],map=window.__SHANGHAI_APP__.scene.map;
      for(let i=0;i<4;i++){
        await new Promise(resolve=>requestAnimationFrame(resolve));
        const style=getComputedStyle(document.getElementById('loading'));
        states.push({opacity:Number(style.opacity),visibility:style.visibility,pointer_events:style.pointerEvents,
          moving:map.isMoving(),bearing:map.getBearing(),pitch:map.getPitch(),zoom:map.getZoom(),center:map.getCenter().toArray()});
      }
      return states;
    });
    for(const state of result.visible_frames){
      assert.equal(state.opacity,0);assert.equal(state.visibility,'hidden');assert.equal(state.moving,false);
      assert.deepEqual(state,result.visible_frames[0]);
    }
    const img=await page.screenshot({path:path.join(out,'main-wide.png'),timeout:180000});result.image_sha256=sha(img);result.completed=true;
  }catch(e){result.failure=String(e);throw e;}
  finally{await browser.close();result.finished=new Date().toISOString();fs.writeFileSync(path.join(out,'wide-browser.json'),JSON.stringify(result,null,2)+'\n');}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
