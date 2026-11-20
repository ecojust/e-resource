/* Reproduce the chamfered portal using only the normal navigation, zoom and drag controls. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { chromium } = require('playwright');
const id = 'huangpu-shen-bao-building';
const base = process.env.MODEL_BASE_URL;
const out = process.env.QA_OUTPUT_DIR;
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const files = JSON.parse(fs.readFileSync(process.env.QA_PRODUCTION)).files;
const report = {id, base, scriptSha256:hash(fs.readFileSync(__filename)), steps:[], views:[], errors:[], completed:false};
fs.mkdirSync(out, {recursive:true});
const save = () => fs.writeFileSync(path.join(out, 'entrance-plaque.json'), JSON.stringify(report,null,2)+'\n');
(async () => {
 const browser = await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader','--remote-debugging-port=9594']});
 const page = await browser.newPage({viewport:{width:1000,height:720},ignoreHTTPSErrors:true});
 page.setDefaultTimeout(240000);
 page.on('pageerror', e=>report.errors.push(e.message));
 try {
  const response = await page.request.get(base+'data/candidate-city-integrations.json');
  const bytes = await response.body();
  report.catalogSha256 = hash(bytes);
  assert.equal(report.catalogSha256, files['data/candidate-city-integrations.json']);
  const catalog = JSON.parse(bytes), row = catalog.models.find(r=>r.id===id);
  assert.equal(catalog.resulting_city_count,142);
  report.count = catalog.resulting_city_count;
  await page.goto(base+'index.html#landmark='+id+'&mode=overview',{waitUntil:'domcontentloaded'});
  async function state() {
   await page.waitForFunction(id=>{
    const s=window.__SHANGHAI_APP__?.scene,m=s?.map;
    if(!m || m.isMoving() || !s.getLandmarkAssetState(id)?.visible) return false;
    const group=s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.clip_feature_local_ids.includes(2422));
    return group && s.getStreamingState().detail.active.some(it=>it.id===group.id);
   },id,{timeout:240000,polling:400});
   return page.evaluate(({row,id})=>{
    const s=window.__SHANGHAI_APP__.scene,m=s.map,r=Math.PI/180,k=6371008.8*Math.cos(row.lat*r),h=row.heading*r;
    function project(x,y,z) {
     const e=x*Math.cos(h)+y*Math.sin(h),n=-x*Math.sin(h)+y*Math.cos(h);
     const lng=row.lng+e/k/r,lat=Math.atan(Math.sinh(Math.asinh(Math.tan(row.lat*r))+n/k))/r;
     const p=m.transform.locationToScreenPoint({lng,lat},{getElevationForLngLat:()=>z});
     return [p.x,p.y];
    }
    function rectangle(x,y,b,t) {return [[-x,y,b],[x,y,b],[x,y,t],[-x,y,t]].map(a=>project(...a));}
    const controls=['#location-card','#building-beacon-legend','.topbar','.map-tools'].flatMap(q=>{
     const e=document.querySelector(q);if(!e)return [];const a=e.getBoundingClientRect();
     return a.width&&a.height?[{selector:q,left:a.left,top:a.top,right:a.right,bottom:a.bottom}]:[];
    });
    const layers=m.getStyle().layers.filter(l=>l.id.endsWith('labels-symbol')||l.id.endsWith('labels-numbers')).map(l=>l.id);
    const rendered=new Set(m.queryRenderedFeatures({layers}).map(f=>f.properties.id));
    const asset=s.getLandmarkAssetState(id),group=s.getCandidateIntegrationState().shader.ownerScopedSources.find(g=>g.clip_feature_local_ids.includes(2422));
    return {camera:{center:m.getCenter(),zoom:m.getZoom(),bearing:m.getBearing(),pitch:m.getPitch(),centerElevation:m.getCenterElevation()},asset:asset.verifiedAsset,
     triangles:asset.triangles,variant:asset.variant,nearGroup:group.id,location:location.hash,
     navExpanded:document.querySelector('#panel-toggle').getAttribute('aria-expanded'),controls,labels:s.getBuildingBeaconState().labelPositions.filter(v=>rendered.has(v.id)),
     center:project(0,-.09,3.95),letters:rectangle(.715,-.09,3.81,4.09),stone:rectangle(1.605,-.07,3.69,4.19),portal:rectangle(1.8,-.07,.12,4.60)};
   },{id,row});
  }
  function check(st) {
   assert.equal(st.asset.sha256,row.assets.web.sha256);assert.equal(st.triangles,41640);assert.equal(st.variant,'full');
   return st;
  }
  async function measure(action){
   const st=check(await state());
   report.steps.push({action,...st});save();console.log(action,st.camera.zoom,st.center);return st;
  }
  async function waitForMotion() {
   await page.waitForTimeout(450);
   await page.waitForFunction(()=>!window.__SHANGHAI_APP__.scene.map.isMoving());
  }
  async function pan(st) {
   const [x,y]=st.center;
   const dx=Math.round(Math.max(-320,Math.min(285,571-x)));
   const dy=Math.round(Math.max(-245,Math.min(165,340-y)));
   if(Math.hypot(dx,dy)<22)return st;
   const start=[560,343],end=[start[0]+dx,start[1]+dy];
   await page.mouse.move(...start);await page.mouse.down();await page.mouse.move(...end,{steps:14});
   await page.waitForTimeout(180);await page.mouse.up();await waitForMotion();
   return measure({type:'left-drag',from:start,to:end});
  }
  let st=await measure('default overview');
  if(st.navExpanded==='true') {
   await page.locator('#panel-toggle').click();
   await page.waitForFunction(()=>document.querySelector('#panel-toggle').getAttribute('aria-expanded')==='false');
   st=await measure('close navigation');
  }
  // Real MapLibre right drag tilts towards the street and preserves the longitudinal viewing direction.
  if(st.camera.pitch<54) {
   const start=[625,290],end=[625,355];await page.mouse.move(...start);await page.mouse.down({button:'right'});
   await page.mouse.move(...end,{steps:15});await page.waitForTimeout(200);await page.mouse.up({button:'right'});
   await waitForMotion();st=await measure({type:'right-drag',from:start,to:end});
  }
  function bounds(points){
   const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
   return {left:Math.min(...xs),right:Math.max(...xs),top:Math.min(...ys),bottom:Math.max(...ys)};
  }
  for(let n=0;n<6;n++){
   for(let j=0;j<3;j++){const next=await pan(st);if(next===st)break;st=next;}
   const b=bounds(st.letters);
   if(b.right-b.left>=105 && b.bottom-b.top>=11)break;
   if(st.camera.zoom>=23.9)break;
   await page.locator('#zoom-in').click();await waitForMotion();st=await measure('click zoom in');
  }
  for(let n=0;n<4;n++){const next=await pan(st);if(next===st)break;st=next;}
  const b=bounds(st.letters);const margin=16;
  const screenshot=await page.screenshot({path:path.join(out,'map-entrance-plaque.png'),timeout:200000});
  report.views.push({file:'map-entrance-plaque.png',bytes:screenshot.length,sha256:hash(screenshot),...st});save();
  assert.ok(b.left>margin && b.top>margin && b.right<1000-margin && b.bottom<720-margin);
  assert.ok(b.right-b.left>=53 && b.bottom-b.top>=8,JSON.stringify(b));
  assert.ok(st.controls.every(q=>q.right<b.left||q.left>b.right||q.bottom<b.top||q.top>b.bottom));
  assert.deepEqual(report.errors,[]);report.completed=true;
 }catch(error){report.failure=error.stack;throw error;}
 finally{await browser.close();report.finished=new Date().toISOString();save();}
})().catch(error=>{console.error(error);process.exitCode=1;});
