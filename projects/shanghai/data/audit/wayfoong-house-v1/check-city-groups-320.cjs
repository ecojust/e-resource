/* Live 320px map group inspection for the corrected Wayfoong House scene. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto'),{chromium}=require('playwright');
const base='http://127.0.0.1:18090/',project='/tmp/wayfoong90/city-group-stages/stage90/projects/shanghai',id='huangpu-wayfoong-house';
const out='/tmp/wayfoong90/browser132-official/city-groups',hash=b=>createHash('sha256').update(b).digest('hex');
fs.mkdirSync(out,{recursive:true});const report={base,id,started:new Date().toISOString(),checker:hash(fs.readFileSync(__filename)),bindings:{},completed:false,errors:[]};
const save=()=>fs.writeFileSync(path.join(out,'groups320.json'),JSON.stringify(report,null,2)+'\n');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:320,height:568},isMobile:true,hasTouch:true,ignoreHTTPSErrors:true});
  page.setDefaultTimeout(300000);page.on('pageerror',err=>report.errors.push(err.message));
  for(const rel of ['index.html','src/app.js','src/map-scene.js','src/building-beacons.js','src/building-beacon-groups.js','data/candidate-city-integrations.json']){
   const r=await page.request.get(base+rel);assert.equal(r.status(),200);const bytes=await r.body();assert.equal(hash(bytes),hash(fs.readFileSync(path.join(project,rel))));report.bindings[rel]=hash(bytes);
  }
  await page.goto(base+'index.html#landmark=jingan-country-hospital&mode=overview',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>!!window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState);
  await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;m.setMaxBounds(null);m.setCenterClampedToGround(true);m.jumpTo({center:[121.45,31.2],zoom:8,pitch:0,bearing:0,elevation:0,padding:{left:0,right:0,top:0,bottom:0}});s.refreshBuildingBeacons();});
  await page.waitForFunction(()=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState();return !s.map.isMoving()&&b.labelMode==='groups'&&b.visibleBuildingCount===132&&document.querySelectorAll('.beacon-group-buttons button').length===b.labelPositions.length;});
  const data=await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState(),rect=sel=>document.querySelector(sel)?.getBoundingClientRect().toJSON();
   return {camera:{center:s.map.getCenter(),zoom:s.map.getZoom(),pitch:s.map.getPitch(),bearing:s.map.getBearing()},hud:{legend:rect('#building-beacon-legend'),card:rect('#location-card'),tools:rect('.maplibregl-ctrl-top-right')},
    layout:b,buttons:[...document.querySelectorAll('.beacon-group-buttons button')].map(btn=>{const r=btn.getBoundingClientRect(),hits=[];for(const x of [.15,.5,.85])for(const y of [.15,.5,.85])hits.push(document.elementFromPoint(r.x+r.width*x,r.y+r.height*y)===btn);return {id:btn.dataset.beaconGroup,rect:r.toJSON(),name:btn.getAttribute('aria-label'),touchSampleHits:hits};})};});
  report.data=data;const ids=data.layout.labelPositions.flatMap(g=>g.memberIds);assert.equal(new Set(ids).size,132);assert.equal(ids.length,132);assert.equal(data.layout.overlapFallbackCount,0);assert(data.buttons.every(b=>b.touchSampleHits.every(Boolean)));
  report.cityFrame=hash(await page.screenshot({path:path.join(out,'map-320-groups.png'),timeout:95000}));save();
  const seen=[];let targetGroup;
  for(const g of data.layout.labelPositions){
   await page.locator('button[data-beacon-group="'+g.id+'"]').tap();const dialog=page.locator('dialog.beacon-group-picker[open]');await dialog.waitFor();
   const options=await dialog.locator('button[data-landmark]').evaluateAll(el=>el.map(b=>b.dataset.landmark));assert.deepEqual(options,g.memberIds);seen.push(...options);if(options.includes(id))targetGroup=g.id;
   await dialog.locator('header button').tap();await dialog.waitFor({state:'hidden'});
  }
  assert.equal(new Set(seen).size,132);assert(targetGroup);report.visitedMembers=seen;report.targetGroup=targetGroup;save();
  await page.locator('button[data-beacon-group="'+targetGroup+'"]').tap();
  const dialog=page.locator('dialog.beacon-group-picker[open]');await dialog.waitFor();await dialog.locator('input').fill('汇丰');
  const option=dialog.locator('button[data-landmark="'+id+'"]');await option.scrollIntoViewIfNeeded();report.dialogFrame=hash(await page.screenshot({path:path.join(out,'map-320-selection.png'),timeout:95000}));
  await option.tap();await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id);report.selected=await page.evaluate(()=>({hash:location.hash,name:document.querySelector('#location-name').textContent}));assert.equal(report.errors.length,0);report.completed=true;
 }catch(e){report.failure=e.stack;throw e;}finally{report.finished=new Date().toISOString();save();await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
