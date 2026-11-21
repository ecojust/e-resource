/* End-to-end city run. Require the real 27k signature and its signed predecessor. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict'),{chromium}=require('playwright');
const n=Number(process.argv[2]),out=process.argv[3],width=Number(process.argv[4]||880),height=width<500?844:650;
if(![221,223,230].includes(n)||!out)throw Error('Usage: node real-map-current.cjs 221|223|230 OUTPUT [WIDTH]');
const source='/tmp/shanghai-bridge-walking-221',proof=JSON.parse(fs.readFileSync(source+'/scenes/'+n+'-comparison.json'));
const complete=JSON.parse(fs.readFileSync(source+'/scenes/'+n+'-all-http.json'));
const stages=JSON.parse(process.env.BRIDGE_VIEW_LAYERS || '[{"base":28000,"dir":"/tmp/shanghai-riyue-courtyard/scenes"},{"base":31000,"dir":"/tmp/shanghai-yongjia-porch/scenes"}]');
if(!Array.isArray(stages)||!stages.length)throw Error('Expected at least one real signed presentation layer');
let upstream=proof.production_receipt_sha256,previousView,currentView;
const checked=[];
for(const layer of stages){
 currentView=JSON.parse(fs.readFileSync(path.join(layer.dir,n+'-comparison.json')));
 previousView=JSON.parse(fs.readFileSync(path.join(layer.dir,(n-1)+'-comparison.json')));
 assert(currentView.passed && previousView.passed && currentView.port===layer.base+n);
 assert.equal(currentView.parent_receipt_sha256,upstream);
 assert.equal(currentView.catalog_sha256,proof.catalog_sha256);
 assert.equal(previousView.catalog_sha256,proof.previous_catalog_sha256);
 checked.push({port:currentView.port,signature:currentView.production_receipt_sha256});
 upstream=currentView.production_receipt_sha256;
}
const id={221:'huangpu-waibaidu-bridge',223:'huangpu-sichuan-road-bridge',230:'huangpu-zhapu-road-bridge'}[n];
const base='http://127.0.0.1:'+currentView.port+'/',before='http://127.0.0.1:'+previousView.port+'/';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
assert(proof.passed&&complete.passed&&proof.production_receipt_sha256===complete.production_receipt_sha256);
const report={order:n,id,base,before,checkedPresentationLayers:checked,walkRuntimeSnapshot:proof.production_receipt_sha256,finalViewSnapshot:currentView.production_receipt_sha256,fullHttp27:complete.count,catalog_sha256:currentView.catalog_sha256,viewport:{width,height},cases:[]};fs.mkdirSync(out,{recursive:true});const save=()=>fs.writeFileSync(out+'/real-city.json',JSON.stringify(report,null,2)+'\n');
(async()=>{
 const previous=await(await fetch(before+'data/candidate-city-integrations.json')).arrayBuffer();assert.equal(sha(Buffer.from(previous)),proof.previous_catalog_sha256);
 assert(!JSON.parse(Buffer.from(previous)).models.some(r=>r.id===id));report.predecessor_catalog_sha256=proof.previous_catalog_sha256;
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--renderer-process-limit=1','--js-flags=--max-old-space-size=384','--disk-cache-size=2097152']});
 try{
  const page=await browser.newPage({ignoreHTTPSErrors:true,viewport:{width,height},isMobile:width<500,hasTouch:width<500}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  report.tileResponses=[];report.failedRequests=[];page.on('response',r=>{if(r.status()>=400)report.failedRequests.push({url:r.url(),status:r.status()});});
  page.on('response',res=>{const address=res.url();if(/\/14\/13720\/6693\.pbf(?:\?|$)/.test(address))report.tileResponses.push({url:address,status:res.status()});});
  page.on('requestfailed',request=>{if(request.failure()?.errorText!=='net::ERR_ABORTED')report.failedRequests.push({url:request.url(),error:request.failure()?.errorText});});
  await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});const link=page.locator('article[data-landmark="'+id+'"] a[href$="mode=walk"]');
  await link.waitFor({state:'visible'});report.walkHref=await link.getAttribute('href');if(width<500)await link.tap();else await link.click();
  await page.waitForFunction(()=>window.__SHANGHAI_APP__?.mode==='walk',{},{timeout:150000});
  const r=await page.evaluate(id=>window.__SHANGHAI_APP__.landmarks.find(x=>x.id===id),id);assert(r.navigation.listed&&r.bridge_walk);
  const shaFull=r.assets.web.sha256,shaLod=r.assets.lod.sha256;
  const active=async hash=>page.waitForFunction(({id,hash})=>window.__SHANGHAI_APP__.scene.getCandidateIntegrationState().active.some(a=>a.id===id&&a.assetSha256===hash),{id,hash},{timeout:180000});
  await active(shaFull);
  await page.evaluate(async()=>{await window.__SHANGHAI_APP__.scene.waitForData(8500);});
  await page.evaluate(async id=>{
   const {bridgePosition}=await import('/src/candidate-bridge-walk.js?v=bridge-walk-v1');const app=window.__SHANGHAI_APP__,r=app.landmarks.find(x=>x.id===id),b=r.bridge_walk,rad=Math.PI/180;
   const point=(s,v)=>{const [lng,lat]=bridgePosition(r,s,v);return{lng,lat};},m=(b.half_road_m+b.half_deck_m)/2;
   window.bridgeCheck={point,m,local:p=>{const k=6371008.8*Math.cos(r.lat*rad),e=(p.lng-r.lng)*rad*k,y=(Math.asinh(Math.tan(p.lat*rad))-Math.asinh(Math.tan(r.lat*rad)))*k,a=r.heading*rad,x=e*Math.cos(a)-y*Math.sin(a),north=e*Math.sin(a)+y*Math.cos(a),v=b.longitudinal_axis==='x'?north:x;return[(b.longitudinal_axis==='x'?x:north)-b.shear*v,v];},
    read:()=>{const ctl=app.controller,s=app.scene,tests=[];
     for(const station of [b.stations_m[0][0]+.25,0,b.stations_m.at(-1)[0]-.25])for(const v of [-m,0,m,14]){
       const p=point(station,v);tests.push({station,v,ground:s.groundAt(p.lng,p.lat),native:s.collisionAt(p.lng,p.lat)});
     }
     return{mode:app.mode,position:{...ctl.position},sole_m:ctl.groundHeight,support:ctl.groundSurface,interaction:s.getStreetInteractionState(),active:s.getCandidateIntegrationState().active.filter(o=>o.id===id),tests,rail:s.sweepLocalCollision(point(0,m),point(0,b.half_deck_m-.03),{radius:.38}),camera:{center:s.map.getCenter(),bearing:s.map.getBearing(),pitch:s.map.getPitch(),zoom:s.map.getZoom()}};}
   };
  },id);
  async function photo(name){const state=await page.evaluate(()=>window.bridgeCheck.read());const file=path.join(out,name+'.png');await page.waitForFunction(()=>{const elm=document.querySelector('#loading');return !window.__SHANGHAI_APP__.scene.map.isMoving()&&elm&&getComputedStyle(elm).visibility==='hidden';},null,{timeout:150000});const session=await page.context().newCDPSession(page);try{const actual=await session.send('Page.captureScreenshot',{format:'png',fromSurface:true});fs.writeFileSync(file,Buffer.from(actual.data,'base64'));}finally{await session.detach();}report.cases.push({name,file:path.basename(file),sha256:sha(fs.readFileSync(file)),state});save();return state;}
  report.footwaySource=await page.evaluate(id=>{
    const app=window.__SHANGHAI_APP__,s=app.scene,r=app.landmarks.find(row=>row.id===id);
    const ids=r.bridge_walk.transportation_feature_ids,road=s.map.querySourceFeatures(s.sourceId,{sourceLayer:'transportation'}),water=s.map.querySourceFeatures(s.sourceId,{sourceLayer:'water'});
    return {source:s.sourceId,expected:ids,observed:[...new Set(road.filter(f=>ids.includes(f.id)&&f.properties?.brunnel==='bridge').map(f=>f.id))],waterFeatureCount:water.length,collision:s.getCollisionState(),model:s.getLandmarkAssetState(id)};
  },id);save();
  assert.deepEqual([...report.footwaySource.observed].sort(),[...report.footwaySource.expected].sort());
  assert(report.footwaySource.waterFeatureCount>0);assert.equal(report.footwaySource.model.verifiedAsset.sha256,shaFull);
  let start=await photo('map-south-footway');assert.equal(start.support.ownerId,id);assert.equal(start.rail.type,'street-obstacle');assert.equal(start.tests.find(q=>q.station===0&&q.v===14).native,'water');
  await page.evaluate(()=>{
   const app=window.__SHANGHAI_APP__,check=window.bridgeCheck,r=app.landmarks.find(row=>row.id===app.controller.groundSurface?.ownerId),b=r.bridge_walk;
   check.trace=[];check.traceRunning=true;
   const trace=now=>{
     if(!check.traceRunning)return;
     const p=app.controller.position,[station,across]=check.local(p),last=check.trace.at(-1);
     if(!last||Math.abs(station-last.station_m)>.65){
       const upper=b.stations_m.findIndex(k=>k[0]>=station);
       let mesh=null;
       if(upper>0&&Math.abs(across)<=b.half_deck_m){
         const lo=b.stations_m[upper-1],hi=b.stations_m[upper],coef=(station-lo[0])/(hi[0]-lo[0]);
         mesh=r.altitude+(r.scale??1)*(lo[1]+coef*(hi[1]-lo[1])+(Math.abs(across)>b.half_road_m?b.sidewalk_rise_m:0));
       }
       check.trace.push({ms:Math.round(now),station_m:station,across_m:across,station_plane_m:mesh,model_sha256:app.scene.getCandidateIntegrationState().active.find(q=>q.id===r.id)?.assetSha256??null,sole_m:app.controller.groundHeight,owner:app.controller.groundSurface?.ownerId??null});
     }
     requestAnimationFrame(trace);
   };
   requestAnimationFrame(trace);
  });
  if(width>=500){
   await page.keyboard.down('Shift');await page.keyboard.down('w');
   try{await page.waitForFunction(l=>window.bridgeCheck.local(window.__SHANGHAI_APP__.controller.position)[0]>l,r.bridge_walk.stations_m.at(-1)[0]+1.05,{timeout:340000});}
   finally{await page.keyboard.up('w');await page.keyboard.up('Shift');}
   const landed=await photo('map-north-bank');assert.equal(landed.support,null);assert(Math.abs(landed.sole_m-.075)<1e-6);
  }else{
   const stick=page.locator('#joystick');await stick.waitFor({state:'visible'});const rect=await stick.boundingBox(),cx=rect.x+rect.width/2,cy=rect.y+rect.height/2,cdp=await page.context().newCDPSession(page);
   await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:cx,y:cy}]});
   await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:cx,y:cy-30}]});
   try{await page.waitForFunction(l=>window.bridgeCheck.local(window.__SHANGHAI_APP__.controller.position)[0]>l,r.bridge_walk.stations_m[0][0]+8,{timeout:60000});}
   finally{await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await cdp.detach();}
   const moved=await photo('map-touch-walking');assert.equal(moved.support.ownerId,id);
  }
  report.path=await page.evaluate(()=>{window.bridgeCheck.traceRunning=false;return window.bridgeCheck.trace;});save();
  const supported=report.path.filter(p=>p.station_plane_m!==null);
  assert(supported.length>=(width<500?4:38),'Insufficient measured walking frames');
  assert(supported.every(p=>p.owner===id&&Math.abs(p.station_plane_m-p.sole_m)<.002),'Actual avatar sole diverged from registered deck height');
  require('node:child_process').execFileSync(process.execPath,[path.join(source,'tests/trace-mesh.mjs'),path.join(out,'real-city.json')],{stdio:'inherit'});
  assert(report.path.every((p,i)=>i===0||p.station_m>=report.path[i-1].station_m-.06),'Unexpected backwards movement');
  await page.locator('#overview-mode').click();await page.evaluate(()=>{const {scene}=window.__SHANGHAI_APP__,{point}=window.bridgeCheck;scene.setCameraFromTo({from:{...point(7,34),alt:3.8},to:{...point(0,0),alt:1.9}});});
  await active(shaFull);await page.waitForTimeout(500);await photo('map-river-side');
  await page.evaluate(()=>{const {scene}=window.__SHANGHAI_APP__,{point}=window.bridgeCheck;scene.setCameraFromTo({from:{...point(150,150),alt:650},to:{...point(0,0),alt:.2}});});await active(shaLod);const far=await photo('map-distant');assert.equal(far.rail.type,'street-obstacle');
  await page.evaluate(()=>{location.hash='lng=121.4500&lat=31.2100&mode=walk';});
  await page.waitForFunction(id=>!window.__SHANGHAI_APP__.scene.getCandidateIntegrationState().active.some(r=>r.id===id),id,{timeout:90000});
  let hidden=await page.evaluate(()=>window.bridgeCheck.read());assert(!hidden.rail);assert(!hidden.tests.some(q=>q.ground?.ownerId===id));report.departure=hidden;save();
  await page.evaluate(id=>{location.hash='landmark='+id+'&mode=walk';},id);await active(shaFull);let returned=await page.evaluate(()=>window.bridgeCheck.read());
  assert(returned.active.length&&returned.rail);report.returned=returned;report.errors=errors;assert.deepEqual(errors,[]);assert.deepEqual(report.failedRequests,[]);report.passed=true;
 }finally{await browser.close();report.closed=true;save();}
})().catch(e=>{report.error=String(e.stack||e);save();process.exitCode=1;});
