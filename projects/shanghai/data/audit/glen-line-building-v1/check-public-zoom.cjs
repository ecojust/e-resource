/* Measure the same public map before and after its navigation and zoom buttons are clicked. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const {chromium}=require('playwright');
const out=process.env.QA_OUTPUT_DIR,base=process.env.MODEL_BASE_URL;
const id='huangpu-glen-line-building';
const files=JSON.parse(fs.readFileSync(process.env.QA_PRODUCTION)).files;
const sum=b=>createHash('sha256').update(b).digest('hex');
fs.mkdirSync(out,{recursive:true});
const report={id,base,started:new Date().toISOString(),scriptSha256:sum(fs.readFileSync(__filename)),views:[],errors:[],completed:false};
const save=()=>fs.writeFileSync(path.join(out,'public-zoom-steps.json'),JSON.stringify(report,null,2)+'\n');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:870,height:660},ignoreHTTPSErrors:true});
 page.setDefaultTimeout(190000);page.on('pageerror',e=>report.errors.push(e.message));
 try{
  const catalog=await page.request.get(base+'data/candidate-city-integrations.json');
  const bytes=await catalog.body();assert.equal(sum(bytes),files['data/candidate-city-integrations.json']);
  const info=JSON.parse(bytes),row=info.models.find(r=>r.id===id);report.catalogSha256=sum(bytes);report.count=info.resulting_city_count;
  assert.equal(report.count,129);
  await page.goto(base+'index.html#landmark='+id+'&mode=overview',{waitUntil:'domcontentloaded'});
  async function collect(step){
   await page.waitForFunction(id=>{
    const s=window.__SHANGHAI_APP__?.scene,m=s?.map;
    if(!m||m.isMoving()||!s.getLandmarkAssetState(id)?.visible)return false;
    const l=m.getStyle().layers.filter(l=>l.id.endsWith('labels-symbol')||l.id.endsWith('labels-numbers')).map(l=>l.id);
    return l.length===2&&m.queryRenderedFeatures({layers:l}).some(f=>f.properties.id===id);
   },id,{timeout:220000,polling:350});
   await page.evaluate(()=>new Promise(resolve=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>resolve());m.triggerRepaint();}));
   const state=await page.evaluate(({id,row})=>{
    const scene=window.__SHANGHAI_APP__.scene,m=scene.map,t=m.transform,asset=scene.getLandmarkAssetState(id);
    const b=scene.getBuildingBeaconState();
    const layers=m.getStyle().layers.filter(l=>l.id.endsWith('labels-symbol')||l.id.endsWith('labels-numbers')).map(l=>l.id);
    const rendered=new Set(m.queryRenderedFeatures({layers}).map(v=>v.properties.id));
    const labels=b.labelPositions.filter(v=>rendered.has(v.id));
    const mul=Math.PI/180,k=6371008.8*Math.cos(row.lat*mul),head=row.heading*mul;
    function project(x,y,z){
     const east=x*Math.cos(head)+y*Math.sin(head),north=-x*Math.sin(head)+y*Math.cos(head);
     const lng=row.lng+east/k/mul,lat=Math.atan(Math.sinh(Math.asinh(Math.tan(row.lat*mul))+north/k))/mul;
     const at=t.locationToScreenPoint({lng,lat},{getElevationForLngLat:()=>z});
     return [at.x,at.y];
    }
    const faces={
     'river-front':[[-5.61,0,0],[8.62,0,0],[8.62,0,26.27],[-5.61,0,26.27]],
     'south-side':[[-11.7,6.1,0],[-11.7,15.,0],[-11.7,15.,26.27],[-11.7,6.1,26.27]],
     'corner':[[-8.8,3.83,0],[-5.61,0,0],[-5.61,0,26.27],[-8.8,3.83,26.27]],
     'tower':[[-1,1.42,26.6],[3.94,1.42,26.6],[3.94,2.1,35.02],[-1,2.1,35.02]]};
    const polygons=Object.fromEntries(Object.entries(faces).map(([n,values])=>[n,values.map(v=>project(...v))]));
    const controls=['#explore-panel','#location-card','#building-beacon-legend','.topbar','.map-tools'].flatMap(sel=>{
     const e=document.querySelector(sel);if(!e)return [];const a=e.getBoundingClientRect();
     if(a.right<=0||a.bottom<=0||a.left>=innerWidth||a.top>=innerHeight||a.width<1||a.height<1||getComputedStyle(e).visibility==='hidden')return [];
     return [{selector:sel,x0:a.left,y0:a.top,x1:a.right,y1:a.bottom}];});
    return {viewport:[innerWidth,innerHeight],navExpanded:document.querySelector('#panel-toggle').getAttribute('aria-expanded'),
     camera:{center:m.getCenter(),zoom:m.getZoom(),bearing:m.getBearing(),pitch:m.getPitch(),elevation:m.getCenterElevation()},
     fill:asset.verifiedAsset,variant:asset.variant,triangles:asset.triangles,polygons,controls,labels,selectedLabel:labels.find(v=>v.id===id)};
   },{id,row});
   assert.equal(state.fill.sha256,row.assets.web.sha256);assert.equal(state.variant,'full');
   assert.ok(state.selectedLabel);const file='public-'+step+'.png';const png=await page.screenshot({path:path.join(out,file),timeout:240000});
   report.views.push({step,file,sha256:sum(png),bytes:png.length,...state});save();console.log(step,state.camera.zoom);
  }
  await collect('default');assert.equal(report.views[0].navExpanded,'true');
  await page.locator('#panel-toggle').click();await page.waitForFunction(()=>document.querySelector('#panel-toggle').getAttribute('aria-expanded')==='false');
  await collect('closed-navigation');
  for(const name of ['zoom-one','zoom-two']){
   const previous=report.views.at(-1).camera.zoom;
   await page.locator('#zoom-in').click();
   await page.waitForFunction(x=>window.__SHANGHAI_APP__.scene.map.getZoom()>x+.20,previous);
   await collect(name);
  }
  assert.deepEqual(report.errors,[]);report.completed=true;
 }catch(error){report.failure=error.stack;throw error;}
 finally{await browser.close();report.finished=new Date().toISOString();save();}
})().catch(error=>{console.error(error);process.exitCode=1;});
