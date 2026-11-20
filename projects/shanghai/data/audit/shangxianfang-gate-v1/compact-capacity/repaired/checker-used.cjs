/* Measure the real numbered map without waiting for overlap errors to disappear. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto');const {chromium}=require('playwright');const {PNG}=require('pngjs');
const id='huangpu-shangxianfang-gate',longTitle='jingan-country-hospital';
const base=process.env.MODEL_BASE_URL,project=process.env.SHANGHAI_PROJECT_ROOT,out=process.env.QA_OUTPUT_DIR;
const fixed=process.env.QA_EXPECTED_LAYOUT==='separate',hash=x=>createHash('sha256').update(x).digest('hex');
const input=p=>fs.readFileSync(path.join(project,p));
const names=['index.html','src/app.js','src/building-beacons.js','src/map-scene.js','data/candidate-city-integrations.json'];
const report={id,base,started:new Date().toISOString(),expected:fixed?'separate-labels':'original-overlap',completed:false,
  checkerSha256:hash(fs.readFileSync(__filename)),bindings:Object.fromEntries(names.map(p=>[p,hash(input(p))])),seenModules:[],errors:[]};
fs.mkdirSync(out,{recursive:true});const save=()=>fs.writeFileSync(path.join(out,'capacity-browser.json'),JSON.stringify(report,null,2)+'\n');
async function run(){
 const catalog=JSON.parse(input(names[4]));assert.equal(catalog.resulting_city_count,108);
 const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
 const page=await b.newPage({viewport:{width:320,height:568},hasTouch:true,isMobile:true,ignoreHTTPSErrors:true});page.setDefaultTimeout(175000);
 page.on('pageerror',e=>report.errors.push(e.message));page.on('response',r=>{const u=new URL(r.url());if(u.pathname.endsWith('building-beacons.js'))report.seenModules.push({url:r.url(),status:r.status()});});
 try{
  await page.goto(new URL('index.html#landmark='+longTitle+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState);
  await page.evaluate(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;m.setMaxBounds(null);m.setCenterClampedToGround(true);m.jumpTo({center:[121.45,31.2],zoom:8,pitch:0,bearing:0,elevation:0,padding:{top:0,left:0,bottom:0,right:0}});s.refreshBuildingBeacons();});
  await page.waitForFunction(()=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState();return !s.map.isMoving()&&b.viewportLabelCount===108&&b.labelMode==='numbers';},{},{timeout:130000,polling:320});
  async function state(){return page.evaluate(()=>{
   const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState(),p=b.labelPositions;
   const rect=sel=>document.querySelector(sel).getBoundingClientRect().toJSON();
   const misses=[],overlaps=[];
   for(let i=0;i<p.length;i++){const r=p[i];
    for(const dx of [-.35,0,.35])for(const dy of [-.35,0,.35]){const point={x:r.x+dx*r.width,y:r.y+dy*r.height},actual=s.pickBuildingBeacon(point);
     if(actual!==r.id)misses.push({expected:r.id,number:r.number,actual,dx,dy,...point});}
    for(let j=i+1;j<p.length;j++){const q=p[j];if(Math.abs(q.x-r.x)<(q.width+r.width)/2-.01&&Math.abs(q.y-r.y)<(q.height+r.height)/2-.01)overlaps.push([r.number,q.number]);}
   }
   return {viewport:[innerWidth,innerHeight],selection:location.hash,cardTitle:document.querySelector('#location-name').textContent,card:rect('#location-card'),legend:rect('#building-beacon-legend'),tools:rect('.map-tools'),count:b.count,
    displayed:b.viewportLabelCount,overlapFallbacks:b.overlapFallbackCount,distinctCenters:new Set(p.map(r=>r.x+','+r.y)).size,allSourcesLoaded:b.sourceIds.every(k=>s.map.isSourceLoaded(k)),
    cellSizes:[...new Set(p.map(r=>r.width+'×'+r.height))],overlaps,misses,positions:p,svgRendered:s.map.queryRenderedFeatures({layers:['shanghai-building-beacons-labels-numbers']}).length};
  });}
  report.layout=await state();save();
  await page.waitForFunction(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;return m.isStyleLoaded()&&m.queryRenderedFeatures({layers:['shanghai-building-beacons-labels-numbers']}).length>0;},{},{timeout:150000,polling:450});
  report.layout=await state();save();
  const screenshot=await page.screenshot({path:path.join(out,'map-108-markers.png'),timeout:190000});const png=PNG.sync.read(screenshot),l=report.layout;
  report.frame={file:'map-108-markers.png',sha256:hash(screenshot),width:png.width,height:png.height};
  const sx=png.width/320,sy=png.height/568,visible=[];
  for(const r of l.positions){
   let inside=0,edge=0;
   for(let y=Math.max(0,Math.round((r.y-r.height/2)*sy));y<Math.min(png.height,Math.round((r.y+r.height/2)*sy));y++)
    for(let x=Math.max(0,Math.round((r.x-r.width/2)*sx));x<Math.min(png.width,Math.round((r.x+r.width/2)*sx));x++){
     const i=(y*png.width+x)*4,[red,g,blue]=png.data.subarray(i,i+3);
     if(red<90&&g>45&&g<128&&blue>42&&blue<128&&g-red>12)inside++;
     if(red>120&&g>90&&red-g>9&&g-blue>14)edge++;
    }
   if(inside>=16*sx*sy&&edge>=7*sx*sy)visible.push(r.number);
  }
  report.paintedNumbers=visible;save();
  assert.equal(l.count,108);assert.equal(l.displayed,108);assert(l.cardTitle.includes('宏恩医院'));
  if(fixed){assert.equal(l.overlapFallbacks,0);assert.equal(l.overlaps.length,0);assert.equal(l.misses.length,0);assert.equal(visible.length,108);}
  else{assert(l.overlapFallbacks>0);assert(l.overlaps.length>0);assert(l.misses.length>0);}
  const target=fixed?l.positions.find(r=>r.id===id):l.misses[0];const expected=fixed?id:target.actual;
  await page.touchscreen.tap(target.x,target.y);
  await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,expected,{timeout:50000});
  report.touch={x:target.x,y:target.y,displayedId:fixed?id:target.expected,actualSelected:await page.evaluate(()=>new URLSearchParams(location.hash.slice(1)).get('landmark'))};
  assert.equal(report.touch.actualSelected,expected);assert.deepEqual(report.errors,[]);assert.ok(report.seenModules.some(r=>r.status===200));report.completed=true;
 }catch(e){report.failure=e.stack;throw e;}finally{report.finished=new Date().toISOString();save();await b.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
