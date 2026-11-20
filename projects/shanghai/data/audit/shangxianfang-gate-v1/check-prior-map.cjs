/* Confirm the pre-delivery gap, the independent neighboring buildings, and the real approaching view. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');
const project=process.env.SHANGHAI_PROJECT_ROOT;
const base=process.env.MODEL_BASE_URL;
const output=process.env.QA_OUTPUT_DIR||__dirname;
const audit=__dirname;
const id='huangpu-shangxianfang-gate';
const digest=b=>createHash('sha256').update(b).digest('hex');
const json=p=>JSON.parse(fs.readFileSync(p));
const catalog='data/candidate-city-integrations.json';
const contract=json(path.join(audit,'final-placement-contract.json'));
const e=json(path.join(audit,'placement-geometry.json'));
const review=json(path.join(audit,'../../../source/precise',id,'footprint-review.json'));
const files=['index.html','src/app.js','src/map-scene.js','src/walk-controller.js','src/building-beacons.js',catalog];
const report={id,started:new Date().toISOString(),base,passed:false,views:[],ground:[],errors:[],responseFiles:{},
  inputFiles:Object.fromEntries(files.map(f=>[f,digest(fs.readFileSync(path.join(project,f)))])),
  checkerSha256:digest(fs.readFileSync(__filename))};
const expected='cc9af234bcc840e566bfc107faa8bcd77ee62022604f63b875b6d8ab72826ff8';
assert.equal(report.inputFiles[catalog],expected);
const old=json(path.join(project,catalog));
assert.equal(old.resulting_city_count,107);assert(!old.models.some(m=>m.id===id));
const ground=e.ground.witnesses.map(p=>({name:p.name,position:p.wgs84,blocked:false,changesAfterDelivery:p.blocked}));
for(const n of review.owners.slice(0,3)){
  const ring=n.geometry.coordinates[0].slice(0,-1);
  const c=ring.reduce((v,p)=>[v[0]+p[0]/ring.length,v[1]+p[1]/ring.length],[0,0]);
  ground.push({name:'retained native '+n.local_id,position:c,blocked:true,changesAfterDelivery:false});
}
// Match the registered street detail view, including frame padding, after the 300-degree correction.
const camera={center:[contract.lng,contract.lat],elevation:6,zoom:20.5,pitch:58,bearing:300,
  padding:{left:60,right:30,top:20,bottom:112}};
async function main(){
  fs.mkdirSync(output,{recursive:true});
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:870,height:660},hasTouch:true,ignoreHTTPSErrors:true});page.setDefaultTimeout(210000);
  page.on('pageerror',err=>report.errors.push(err.message));
  try{
    const href=new URL('index.html#landmark=huangpu-shanghai-concert-hall&mode=overview',base);
    const response=await page.goto(href.href,{waitUntil:'domcontentloaded'});assert.equal(digest(await response.body()),report.inputFiles['index.html']);
    await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getStreamingState));
    const toggle=page.locator('#panel-toggle');if(await toggle.getAttribute('aria-expanded')==='true')await toggle.click();
    await page.evaluate(c=>{const app=window.__SHANGHAI_APP__,s=app.scene;s.map.setMaxBounds(null);s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.refreshBuildingBeacons();s.loadLandmarks();},camera);
    const group=review.frozen_macro+'/'+review.near_tiles[0].id;
    await page.waitForFunction(group=>{const s=window.__SHANGHAI_APP__.scene;return !s.map.isMoving()&&s.getStreamingState().detail.active.some(g=>g.id===group);},group,{polling:400,timeout:210000});
    const state=await page.evaluate(({id,ground,neighbors})=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,gl=m.painter.context.gl;
      return {registered:a.landmarks.some(r=>r.id===id),markers:s.getBuildingBeaconState().count,renderer:gl.getError(),contextLost:gl.isContextLost(),
        center:m.getCenter().toArray(),bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),active:s.getStreamingState().detail.active.map(g=>g.id),
        neighboringFeatureStates:neighbors.map(r=>({local_id:r.local_id,state:m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:r.source_key.slice(9)})})),candidateClips:s.getCandidateIntegrationState().clips.map(c=>c.id),ground:ground.map(p=>({...p,found:s.collisionAt(...p.position)}))};
    },{id,ground,neighbors:review.owners.slice(0,5)});
    assert(!state.registered&&!state.contextLost&&!state.candidateClips.includes(id));assert.equal(state.renderer,0);assert.equal(state.markers,107);
    for(const p of state.ground)assert.equal(p.found,p.blocked?'building':null,p.name);
    report.ground=state.ground;delete state.ground;report.views.push(state);
    const image=await page.screenshot({path:path.join(output,'map-before.png'),timeout:220000});
    report.image={file:'map-before.png',sha256:digest(image),bytes:image.length};
    for(const f of files){
      const r=await page.request.get(new URL(f,base).href);assert.equal(r.status(),200);
      report.responseFiles[f]=digest(await r.body());assert.equal(report.responseFiles[f],report.inputFiles[f]);
    }
    assert.deepEqual(report.errors,[]);report.passed=true;
  }catch(err){report.error=err.stack;throw err;}
  finally{report.finished=new Date().toISOString();fs.writeFileSync(path.join(output,'control-browser.json'),JSON.stringify(report,null,2)+'\n');await browser.close();}
}
main().catch(err=>{console.error(err);process.exitCode=1;});
