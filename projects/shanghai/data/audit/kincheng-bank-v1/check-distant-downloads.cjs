const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{createHash}=require('node:crypto'),{chromium}=require('playwright');
const project=process.env.SHANGHAI_PROJECT_ROOT||'/workspace/e-resource/projects/shanghai';
const out=process.env.QA_OUTPUT_DIR||'/tmp/kincheng-map/final89c';
const base=process.env.MODEL_BASE_URL||'http://127.0.0.1:8784/';
const sha=b=>createHash('sha256').update(b).digest('hex');
const read=f=>JSON.parse(fs.readFileSync(path.join(project,f)));const id='huangpu-kincheng-bank';
const row=read('data/candidate-city-integrations.json').models.find(x=>x.id===id);assert(row);
const manifest=read(row.candidate_manifest);const foot=read('source/precise/'+id+'/footprint-review.json');
const result={id,started:new Date().toISOString(),completed:false,base,scriptSha256:sha(fs.readFileSync(__filename)),catalogSha256:sha(fs.readFileSync(path.join(project,'data/candidate-city-integrations.json'))),receipts:[],errors:[],httpErrors:[]};
fs.mkdirSync(out,{recursive:true});
const save=()=>fs.writeFileSync(path.join(out,'supplement.json'),JSON.stringify(result,null,2)+'\n');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:520,height:410},ignoreHTTPSErrors:true});
 try{
  result.browser=browser.version();
  const seen=new Set();page.on('response',r=>{if(r.status()>=400)result.httpErrors.push([r.url(),r.status()]);if(r.status()===200)seen.add(new URL(r.url()).pathname.slice(1));});
  page.on('pageerror',e=>result.errors.push(e.message));page.on('console',m=>{if(m.type()==='error')result.errors.push(m.text());});
  for(const [role,a] of Object.entries(manifest.assets)){
   const file=path.posix.join(path.posix.dirname(row.candidate_manifest),a.file),resp=await page.request.get(new URL(file,base).href),value=await resp.body();
   assert.equal(resp.status(),200);assert.equal(value.length,a.bytes);assert.equal(sha(value),a.sha256);result.receipts.push({role,file,bytes:value.length,sha256:sha(value)});
  }
  const near=foot.near_tiles.find(n=>n.feature_local_ids.includes(1708));
  for(const c of foot.frozen_bindings.filter(v=>v.repository_path.endsWith('/far.glb')||v.repository_path.endsWith('/'+near.file))){
   const file=c.repository_path.replace('projects/shanghai/',''),resp=await page.request.get(new URL(file,base).href),value=await resp.body();
   assert.equal(resp.status(),200);assert.equal(value.length,c.bytes);assert.equal(sha(value),c.sha256);result.receipts.push({role:'source',file,bytes:value.length,sha256:sha(value)});
  }
  save();console.log('Verified all six HTTP files');
  await page.goto(base+'index.html#landmark='+id+'&mode=overview',{waitUntil:'domcontentloaded',timeout:360000});
  await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState()),null,{timeout:360000});
  await page.evaluate(({lng,lat})=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo({center:[lng,lat],pitch:30,zoom:15.5,elevation:0,bearing:77.56151995,padding:{top:0,right:0,bottom:0,left:0}});s.loadLandmarks();s.refreshBuildingBeacons();},row);
  await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__.scene;const a=s.getLandmarkAssetState(id);return !s.map.isMoving() && a.status==='loaded' && a.variant==='distant' && a.visible;},id,{timeout:360000,polling:300});
  result.state=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,b=s.getBuildingBeaconState(),label=b.labelPositions.find(l=>l.id===id);return{asset:s.getLandmarkAssetState(id),camera:{center:m.getCenter(),zoom:m.getZoom(),pitch:m.getPitch()},pick:s.pickBuildingBeacon(label),count:b.count,contextLost:m.painter.context.gl.isContextLost(),viewport:[innerWidth,innerHeight]};},id);
  assert.equal(result.state.asset.verifiedAsset.sha256,manifest.assets.lod.sha256);assert.equal(result.state.asset.triangles,manifest.assets.lod.triangles);
  assert.equal(result.state.pick,id);assert.equal(result.state.contextLost,false);
  assert(seen.has(row.assets.lod.file));save();console.log('Verified real distant scene');
  const png=await page.screenshot({path:path.join(out,'map-distant.png'),timeout:420000});
  result.image={file:'map-distant.png',bytes:png.length,width:png.readUInt32BE(16),height:png.readUInt32BE(20),sha256:sha(png)};
  assert.deepEqual(result.errors,[]);assert.deepEqual(result.httpErrors,[]);result.completed=true;
 }catch(e){result.failure=e.stack;throw e;}finally{await browser.close();result.finished=new Date().toISOString();save();}
})().catch(e=>{console.error(e);process.exitCode=1;});
