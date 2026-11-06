/* Preliminary candidate acceptance, before queue delivery and final directory generation. MIT. */
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{createHash}=require('crypto');
const {chromium}=require('playwright');
const PROJECT=process.env.SHANGHAI_PROJECT_ROOT||'/workspace/e-resource/projects/shanghai';
const WORK=process.env.QA_OUTPUT_DIR||__dirname,OUT=path.join(WORK,'candidate-stage');
const BASE=process.env.MODEL_BASE_URL||'http://127.0.0.1:8784/',ID='hongkou-general-post-office';
const sha=b=>createHash('sha256').update(b).digest('hex');
const read=file=>JSON.parse(fs.readFileSync(file,'utf8')),pause=ms=>new Promise(r=>setTimeout(r,ms));
async function main(){
  assert(process.argv.includes('--run'),'Explicit --run required');
  assert(!fs.existsSync(path.join(OUT,'candidate-stage.json')),'Preserve prior candidate-stage run before retry');
  fs.mkdirSync(OUT,{recursive:true});
  const config=read(path.join(WORK,'candidate-stage-contract.json'));
  assert.equal(config.model_id,ID);assert.equal(config.preliminary_only,true);
  const catalog=read(path.join(PROJECT,'data/candidate-city-integrations.json'));
  const row=catalog.models.find(x=>x.id===ID),manifest=read(path.join(PROJECT,`assets/models/candidates/${ID}/manifest.json`));
  assert(row);assert.equal(manifest.id,ID);assert.deepEqual(row.owner,config.owner);
  assert.equal(sha(fs.readFileSync(path.join(PROJECT,`assets/models/candidates/${ID}/manifest.json`))),config.model_manifest_sha256);
  for(const [runtime,role]of [['web','full'],['lod','lod']])for(const field of ['sha256','bytes','triangles'])assert.equal(row.assets[runtime][field],manifest.assets[role][field]);
  for(const asset of Object.values(manifest.assets)){const b=fs.readFileSync(path.join(PROJECT,`assets/models/candidates/${ID}/${asset.file}`));assert.equal(b.length,asset.bytes);assert.equal(sha(b),asset.sha256);}
  const files=['index.html','postal-office.html','src/app.js','src/map-scene.js','src/candidate-city-integrations.js','src/candidate-city-clipping.js','src/building-beacons.js','src/postal-office.js','data/candidate-city-integrations.json',`assets/models/candidates/${ID}/manifest.json`,...Object.values(manifest.assets).map(a=>`assets/models/candidates/${ID}/${a.file}`)];
  const frozen=files.map(file=>({file,sha256:sha(fs.readFileSync(path.join(PROJECT,file)))}));
  const report={schema:'postal-candidate-stage-v1',modelId:ID,preliminaryOnly:true,completed:false,browserClosed:false,startedAt:new Date().toISOString(),scope:'Actual auxiliary full/LOD and main-map candidate rendering before queue candidate_delivered and 84-entry directory generation. This does not claim final README, directory, all beacons, input, downloads or publication acceptance.',scriptSha256:sha(fs.readFileSync(__filename)),contractSha256:sha(fs.readFileSync(path.join(WORK,'candidate-stage-contract.json'))),frozen,captures:[],errors:[],warnings:[],httpErrors:[],visualAcceptance:'Pending actual image inspection.'};
  const save=()=>fs.writeFileSync(path.join(OUT,'candidate-stage.json'),JSON.stringify(report,null,2)+'\n');
  assert.equal(await fetch('http://127.0.0.1:9224/json/version',{signal:AbortSignal.timeout(1000)}).then(r=>r.ok).catch(()=>false),false,'Another QA browser active');
  const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9224']});
  const page=await browser.newPage({viewport:{width:1200,height:900}});report.browserVersion=browser.version();
  page.on('pageerror',e=>report.errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')report.errors.push(m.text());if(m.type()==='warning')report.warnings.push(m.text());});
  page.on('response',r=>{if(r.status()>=400)report.httpErrors.push({url:r.url(),status:r.status()});});
  const capture=async(label,state)=>{const file='candidate-'+label+'.png';assert(!fs.existsSync(path.join(OUT,file)));await page.screenshot({path:path.join(OUT,file),timeout:120000});const b=fs.readFileSync(path.join(OUT,file));report.captures.push({label,file,bytes:b.length,sha256:sha(b),viewport:[b.readUInt32BE(16),b.readUInt32BE(20)],state,visualAcceptance:'Pending actual image inspection.'});save();console.log('CANDIDATE_CAPTURE',file);};
  const auxiliary=async variant=>{await page.waitForFunction(v=>{const s=window.postalOfficeViewer?.getState();return s?.status==='error'||s?.status==='ready'&&s.variant===v;},variant,{timeout:180000});const s=await page.evaluate(()=>window.postalOfficeViewer.getState());assert.equal(s.status,'ready');assert.equal(s.modelId,ID);assert.equal(s.variant,variant);assert.equal(s.triangles,manifest.assets[variant].triangles);assert(s.renderedTriangles>0);const b=s.framing.screenBounds;assert(b.minX>=-.96&&b.maxX<=.96&&b.minY>=-.96&&b.maxY<=.96&&b.minZ>=0&&b.maxZ<=1);await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));return s;};
  const settled=async()=>{let previous=null,priorFrames=-1,stable=0,lastLog=0;const deadline=Date.now()+900000;
    while(Date.now()<deadline){const s=await page.evaluate(({id,macro})=>{const a=window.__SHANGHAI_APP__,m=a.scene.map,t=a.scene.getStreamingState(),b=a.scene.getBuildingBeaconState(),c=a.scene.getCandidateIntegrationState(),asset=a.scene.getLandmarkAssetState(id);m.triggerRepaint();return {ready:!m.isMoving()&&m.areTilesLoaded()&&asset.status==='loaded'&&asset.visible&&t.active.some(x=>x.id===macro&&x.visible)&&c.clips.some(x=>x.id===id)&&b.sourceIds.every(id=>m.isSourceLoaded(id)),asset,hash:location.hash,title:document.querySelector('#location-name').textContent,camera:[m.getCenter().lng,m.getCenter().lat,m.getZoom(),m.getPitch(),m.getBearing(),m.transform.elevation],viewport:[innerWidth,innerHeight],canvas:[m.getCanvas().clientWidth,m.getCanvas().clientHeight],renderedFrames:window.__candidateStageFrames||0,background:{loading:t.loading,queued:t.queued,pendingStates:t.pendingStates,detailLoading:t.detail.loading},clip:c.clips.find(x=>x.id===id),shader:c.shader};},{id:ID,macro:row.owner.macro_id});
      const fingerprint=JSON.stringify([s.camera,s.viewport,s.canvas]);stable=s.ready&&fingerprint===previous&&s.renderedFrames>priorFrames?stable+1:0;previous=fingerprint;priorFrames=s.renderedFrames;
      if(stable>=2){assert.equal(s.asset.verifiedAsset.sha256,row.assets[s.asset.variant==='full'?'web':'lod'].sha256);assert.equal(s.title,row.name);assert.equal(new URLSearchParams(s.hash.slice(1)).get('landmark'),ID);assert.deepEqual(s.clip.owner,row.owner);assert.deepEqual(s.clip.geometry,row.replacement_geometry);return s;}
      if(Date.now()-lastLog>30000){console.log('WAIT_CANDIDATE',JSON.stringify({ready:s.ready,frames:s.renderedFrames,background:s.background}));lastLog=Date.now();}await pause(500);
    }throw Error('Candidate target and actual render frames did not settle');};
  try{
    await page.goto(BASE+'postal-office.html',{waitUntil:'domcontentloaded',timeout:90000});report.auxiliaryFull=await auxiliary('full');await capture('auxiliary-full',report.auxiliaryFull);
    await page.selectOption('#detail','lod');report.auxiliaryLod=await auxiliary('lod');assert(report.auxiliaryLod.triangles<report.auxiliaryFull.triangles);await capture('auxiliary-lod',report.auxiliaryLod);
    await page.goto(BASE+`index.html#landmark=${ID}&mode=overview`,{waitUntil:'domcontentloaded',timeout:90000});await page.waitForFunction(()=>Boolean(window.__SHANGHAI_APP__),null,{timeout:240000});await page.evaluate(()=>{window.__candidateStageFrames=0;window.__SHANGHAI_APP__.scene.map.on('render',()=>window.__candidateStageFrames++);});
    report.mainDefault=await settled();await capture('main-default',report.mainDefault);
    if(await page.locator('#panel-toggle').getAttribute('aria-expanded')==='true')await page.locator('#panel-toggle').click();
    for(const view of config.visual_views||[]){await page.evaluate(camera=>{const s=window.__SHANGHAI_APP__.scene;s.setVisualQuality({shadows:false,surfaceNormals:true});s.map.setCenterClampedToGround(false);s.map.jumpTo({...camera,padding:{top:0,right:0,bottom:0,left:0}});s.loadLandmarks();},view.camera);const state=await settled();assert.equal(state.asset.variant,'full');state.expectedFeatures=view.features;await capture('main-'+view.key,state);}
    report.httpBindings=[];for(const file of ['src/postal-office.js','src/candidate-city-clipping.js','data/candidate-city-integrations.json',row.assets.web.file,row.assets.lod.file]){const response=await page.request.get(BASE+file,{timeout:120000}),b=await response.body();assert.equal(response.status(),200);assert.equal(sha(b),sha(fs.readFileSync(path.join(PROJECT,file))));report.httpBindings.push({file,status:200,bytes:b.length,sha256:sha(b)});}
    assert.deepEqual(report.errors,[]);assert.deepEqual(report.warnings,[]);assert.deepEqual(report.httpErrors,[]);for(const f of frozen)assert.equal(sha(fs.readFileSync(path.join(PROJECT,f.file))),f.sha256,'Input changed during candidate stage '+f.file);report.completed=true;save();
  }catch(error){report.failure=String(error.stack||error);save();throw error;}finally{await browser.close();report.browserClosed=true;report.closedAt=new Date().toISOString();save();}
  console.log('CANDIDATE_STAGE_COMPLETE',JSON.stringify({captures:report.captures.length,preliminaryOnly:true}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
