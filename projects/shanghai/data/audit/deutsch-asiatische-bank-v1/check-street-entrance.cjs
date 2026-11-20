/* View the photographed corner door and north colonnade from inside the Jiujiang/Sichuan junction. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');

const base=process.env.MODEL_BASE_URL;
const out=process.env.QA_OUTPUT_DIR;
const root=process.env.SHANGHAI_PROJECT_ROOT;
const read=file=>JSON.parse(fs.readFileSync(file));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const contract=read(path.join(__dirname,'final-placement-contract.json'));
const id=contract.id;
const catalogFile=path.join(root,'data/candidate-city-integrations.json');
const catalog=read(catalogFile);
const row=catalog.models.find(v=>v.id===id);
const source=read(path.join(root,'source/precise',id,'footprint-review.json'));
const near='/assets/city-detail/macros/'+contract.owner.macro_id+'/'+source.near.file;
const result={id,started:new Date().toISOString(),server:base,script_sha256:sha(fs.readFileSync(__filename)),
  catalog_sha256:sha(fs.readFileSync(catalogFile)),city_count:catalog.resulting_city_count,views:[],errors:[],passed:false};
const outFile=path.join(out,'street-entrance-browser.json');
const write=()=>fs.writeFileSync(outFile,JSON.stringify(result,null,2)+'\n');

async function run(){
  fs.mkdirSync(out,{recursive:true});assert(!fs.existsSync(outFile));
  assert.equal(catalog.resulting_city_count,143);
  const h=row.heading*Math.PI/180,k=6371008.8*Math.cos(row.lat*Math.PI/180);
  const mapPoint=(u,v)=>[row.lng+(u*Math.cos(h)+v*Math.sin(h))/k*180/Math.PI,
    Math.atan(Math.sinh(Math.asinh(Math.tan(row.lat*Math.PI/180))+(-u*Math.sin(h)+v*Math.cos(h))/k))*180/Math.PI];
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  try{
    const page=await browser.newPage({viewport:{width:1280,height:800},ignoreHTTPSErrors:true});
    const hashes=new Map();
    page.on('response',r=>{const u=new URL(r.url());if(u.origin!==new URL(base).origin||r.status()!==200)return;
      if(u.pathname.endsWith('data/candidate-city-integrations.json')||u.pathname==='/'+row.assets.web.file||u.pathname===near)
        hashes.set(u.pathname,r.body().then(b=>sha(b)).catch(()=>null));
    });
    page.on('pageerror',e=>result.errors.push(String(e)));
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
    await page.locator('#district-310101 [data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').click();
    await page.waitForFunction(id=>window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id)?.status==='loaded',id,{timeout:480000});
    const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click({force:true});
    const positions=[
      ['baroque-portal-from-jiujiang-junction',-9.46,11.765,132,71,21.93,5.3],
      ['north-corinthian-column-heads',-.65,13.27,132,72,22.55,13.65],
    ];
    for(const [name,u,v,bearing,pitch,zoom,elevation] of positions){
      const center=mapPoint(u,v);
      await page.evaluate(camera=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(camera);s.loadLandmarks();s.refreshBuildingBeacons();},
        {center,bearing,pitch,zoom,elevation,padding:{left:0,right:0,top:0,bottom:0}});
      await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene,overlay=document.querySelector('#loading');
        const g=s.getCandidateIntegrationState().shader.ownerScopedSources.find(x=>x.feature_local_ids.includes(1064)&&x.feature_local_ids.includes(431));
        return !s.map.isMoving()&&getComputedStyle(overlay).visibility==='hidden' &&g?.clip_feature_local_ids.includes(1064)&&s.getStreamingState().detail.active.some(x=>x.id===g.id)&&s.getLandmarkAssetState(id)?.visible;
      },id,{polling:500,timeout:420000});
      await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;let frames=0;function tick(){if(++frames===3)return resolve();m.once('render',tick);m.triggerRepaint();}m.once('render',tick);m.triggerRepaint();}));
      const state=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,g=s.getCandidateIntegrationState().shader.ownerScopedSources.find(x=>x.feature_local_ids.includes(1064)&&x.feature_local_ids.includes(431));
        return {hash:location.hash,asset:s.getLandmarkAssetState(id),group:g,visibleCount:s.getBuildingBeaconState().count,center:m.getCenter(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),contextLost:m.painter.context.gl.isContextLost()};
      },id);
      assert.equal(state.contextLost,false);assert.equal(state.visibleCount,143);assert.deepEqual([...state.group.clip_feature_local_ids].sort((a,b)=>a-b),[1064,2602]);assert.equal(state.asset.verifiedAsset.sha256,row.assets.web.sha256);
      const nameWithExt=name+'.png';const bytes=await page.screenshot({path:path.join(out,nameWithExt),timeout:180000});
      result.views.push({view:name,file:nameWithExt,sha256:sha(bytes),state});write();
    }
    result.http={catalog:await hashes.get('/data/candidate-city-integrations.json'),web:await hashes.get('/'+row.assets.web.file),near:await hashes.get(near)};
    assert.equal(result.http.catalog,result.catalog_sha256);assert.equal(result.http.web,row.assets.web.sha256);assert.equal(result.http.near,source.frozen_bindings[source.near.file].sha256);
    assert.deepEqual(result.errors,[]);result.passed=true;
  }catch(e){result.failure=e.stack;throw e;}
  finally{await browser.close();result.finished=new Date().toISOString();write();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
