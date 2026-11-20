/* Reach the same selected building and put the survey camera inside the real court under the glazed canopy. */
const {chromium}=require('playwright');
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict'), crypto=require('node:crypto');
const out=process.env.QA_OUTPUT_DIR, base=process.env.MODEL_BASE_URL, id='huangpu-cixiu-nunnery-courtyard';
const sum=b=>crypto.createHash('sha256').update(b).digest('hex');
const project=process.env.SHANGHAI_PROJECT_ROOT;
const catalogBytes=fs.readFileSync(path.join(project,'data/candidate-city-integrations.json'));
const catalog=JSON.parse(catalogBytes), row=catalog.models.find(r=>r.id===id);
const rad=Math.PI/180, k=6371008.8*Math.cos(row.lat*rad), h=row.heading*rad;
function world([x,y,z]){
  const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
  return {lng:row.lng+east/k/rad,lat:Math.atan(Math.sinh(Math.asinh(Math.tan(row.lat*rad))+north/k))/rad,alt:z};
}
const plans=[
  {name:'central-north-hall',eye:[0,-6.82,3.8],target:[0,.98,2.68]},
  {name:'east-gallery-to-hall',eye:[2.48,-5.66,3.56],target:[-1.18,.98,2.43]},
];
async function run(){
  fs.mkdirSync(out,{recursive:true});
  const report={completed:false,started:new Date().toISOString(),id,base,driver:sum(fs.readFileSync(__filename)),catalog:sum(catalogBytes),views:[],httpErrors:[],errors:[]};
  const save=()=>fs.writeFileSync(path.join(out,'inside-court.json'),JSON.stringify(report,null,2)+'\n');
  const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader','--disable-dev-shm-usage','--disk-cache-size=8388608','--num-raster-threads=1']});
  try{
    const page=await b.newPage({viewport:{width:1160,height:760},deviceScaleFactor:1,ignoreHTTPSErrors:true});page.setDefaultTimeout(80000);
    page.on('pageerror',e=>{report.errors.push(e.message);save();});
    page.on('response',r=>{if(r.status()>=400){report.httpErrors.push({url:r.url(),status:r.status()});save();}});
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});assert.equal(await page.locator('.landmark-card[data-landmark]').count(),182);
    await page.locator('article[data-landmark="'+id+'"] .card-foot a[href*="mode=overview"]').click();
    await page.waitForFunction(id=>window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id).visible&&getComputedStyle(document.querySelector('#loading')).opacity<.015,id,{timeout:180000});
    const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
    for(const plan of plans){
      const eye=world(plan.eye),target=world(plan.target);report.phase=plan.name;save();
      const camera=await page.evaluate(({eye,target})=>{
        const s=window.__SHANGHAI_APP__.scene,m=s.map;m.stop();m.setCenterClampedToGround(false);m.setPadding({top:0,bottom:0,left:0,right:0});
        const options=m.calculateCameraOptionsFromTo([eye.lng,eye.lat],eye.alt,[target.lng,target.lat],target.alt);
        m.jumpTo(options);s.loadLandmarks();s.refreshBuildingBeacons();
        const actual=m.transform.getCameraLngLat(),alt=m.transform.getCameraAltitude();
        return {mapCamera:options,actualEye:[actual.lng,actual.lat,alt],eyeGround:s.collisionAt(eye.lng,eye.lat)};
      },{eye,target});
      assert.equal(camera.eyeGround,null);
      await page.waitForFunction(({id,hash})=>{const s=window.__SHANGHAI_APP__.scene,r=s.getLandmarkAssetState(id),c=s.getCandidateIntegrationState();return !s.map.isMoving()&&r.visible&&r.verifiedAsset?.sha256===hash&&c.sourceSections.some(z=>z.id===id&&z.segments===2)&&c.shader.ownerScopedSources.some(z=>z.clip_feature_local_ids.includes(448)&&z.triangles===2);},{id,hash:row.assets.web.sha256},{timeout:150000,polling:500});
      await page.evaluate(()=>new Promise(done=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>requestAnimationFrame(done));m.triggerRepaint();}));
      const state=await page.evaluate(id=>{const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,r=s.getLandmarkAssetState(id);return{route:location.hash,name:document.querySelector('#location-name').textContent,viewport:[innerWidth,innerHeight],mode:a.mode,asset:r.verifiedAsset,triangles:r.triangles,renderer:s.getStreamingState().renderer,count:s.getBuildingBeaconState().count,gl:m.painter.context.gl.getError(),lost:m.painter.context.gl.isContextLost()};},id);
      assert.equal(state.count,182);assert.equal(state.gl,0);assert.equal(state.lost,false);assert.equal(state.triangles,row.assets.web.triangles);
      const file=plan.name+'.png';const data=await page.screenshot({path:path.join(out,file),timeout:100000});
      report.views.push({...plan,worldEye:eye,worldTarget:target,camera,state,file,bytes:data.length,sha256:sum(data)});save();
    }
    assert.deepEqual(report.httpErrors,[]);assert.deepEqual(report.errors,[]);report.completed=true;
  }catch(e){report.failure=String(e);throw e;}finally{await b.close();report.finished=new Date().toISOString();save();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
