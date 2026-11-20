/* Capture the actual last released city at the new building's coordinates. */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');

const [auditPath,beforePath,beforeURL,output]=process.argv.slice(2);
const read=file=>JSON.parse(fs.readFileSync(file));
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
const contract=read(path.join(auditPath,'final-placement-contract.json'));
const project=path.resolve(auditPath,'../../..');
const source=read(path.join(project,'source/precise',contract.id,'footprint-review.json'));
const catalogPath='data/candidate-city-integrations.json';
const before=read(path.join(beforePath,catalogPath));
const previous=before.models.at(-1).id;
assert(!before.models.some(model=>model.id===contract.id));
const macro=contract.owner.macro_id;
const url=new URL(beforeURL);
const near='assets/city-detail/macros/'+macro+'/'+source.near.file;
const result={id:contract.id,prior:previous,count:before.resulting_city_count,started:new Date().toISOString(),
  source:beforeURL,catalog_sha256:digest(fs.readFileSync(path.join(beforePath,catalogPath))),
  script_sha256:digest(fs.readFileSync(__filename)),completed:false};
fs.mkdirSync(output,{recursive:true});
async function run(){
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',
    args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  try{
    const page=await browser.newPage({ignoreHTTPSErrors:true,viewport:{width:840,height:610}});
    page.setDefaultTimeout(180000);
    const served=new Map();
    page.on('response',r=>{
      const u=new URL(r.url()),name=u.pathname.slice(1);
      if(u.origin===url.origin&&r.status()===200&&[catalogPath,near].includes(name))
        served.set(name,r.body().then(digest).catch(()=>null));
    });
    await page.goto(new URL('index.html#landmark='+previous+'&mode=overview',url).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()),null,{timeout:650000});
    const panel=page.locator('#panel-toggle');
    if(await panel.getAttribute('aria-expanded')==='true')await panel.click({force:true});
    const readyRequest=await page.request.get(new URL('assets/city-detail/macros/'+macro+'/READY.json',url).href);
    const readyBytes=await readyRequest.body();assert.equal(digest(readyBytes),source.frozen_bindings['READY.json'].sha256);
    const group=JSON.parse(readyBytes).near.find(x=>x.file===source.near.file);
    assert.deepEqual(group.featureLocalIds,source.near.local_ids);
    const camera={center:[contract.lng,contract.lat],elevation:7,zoom:19.06,pitch:58,bearing:contract.overviewBearing,padding:{left:35,right:0,top:0,bottom:60}};
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
    const groupID=macro+'/'+group.id;
    await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene,c=s.getCandidateIntegrationState(),t=s.getStreamingState();
      return !s.map.isMoving()&&t.detail.active.some(g=>g.id===id)&&c.shader.ownerScopedSources.some(g=>g.id===id && g.clip_feature_local_ids.includes(2602));},groupID,{polling:650,timeout:600000});
    result.state=await page.evaluate(({id,group,owner,uuid})=>{
      const s=window.__SHANGHAI_APP__.scene,c=s.getCandidateIntegrationState();
      return {group:c.shader.ownerScopedSources.find(g=>g.id===group),clip:c.clips.find(r=>r.id===id)||null,
        destination_present:s.getBuildingBeaconState().labelPositions.some(r=>r.id===id),
        city_count:s.getBuildingBeaconState().count,webgl_lost:s.map.painter.context.gl.isContextLost(),
        source:s.map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:uuid}),
        points:{registered_owner:owner},center:s.map.getCenter(),zoom:s.map.getZoom(),pitch:s.map.getPitch(),bearing:s.map.getBearing()};
    },{id:contract.id,group:groupID,owner:contract.owner.feature_local_id,uuid:contract.source_feature_ids.building[0]});
    assert.equal(result.state.city_count,before.resulting_city_count);assert.equal(result.state.webgl_lost,false);
    assert.equal(result.state.clip,null);assert.notEqual(result.state.source.candidateModel,true);
    assert.deepEqual(result.state.group.feature_local_ids,group.featureLocalIds);
    assert.deepEqual(result.state.group.clip_feature_local_ids,[2602]);
    assert(!result.state.group.clip_feature_local_ids.includes(contract.owner.feature_local_id));
    assert.equal(await served.get(catalogPath),result.catalog_sha256);
    assert.equal(await served.get(near),source.frozen_bindings[source.near.file].sha256);
    result.map_files={catalog:result.catalog_sha256,near:source.frozen_bindings[source.near.file].sha256,ready:digest(readyBytes)};
    await page.waitForFunction(()=>{const style=getComputedStyle(document.querySelector('#loading'));return style.opacity==='0'&&style.visibility==='hidden'&&style.pointerEvents==='none';},null,{timeout:420000});
    const image=await page.screenshot({path:path.join(output,'map-before.png'),timeout:180000});
    result.image_sha256=digest(image);result.completed=true;
  }catch(error){result.failure=String(error);throw error;}
  finally{await browser.close();result.finished=new Date().toISOString();fs.writeFileSync(path.join(output,'before-browser.json'),JSON.stringify(result,null,2)+'\n');}
}
run().catch(error=>{console.error(error);process.exitCode=1;});
