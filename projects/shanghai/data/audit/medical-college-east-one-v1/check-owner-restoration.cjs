/* Compare the same local tile, camera and route before and after adding East Building One. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto'),{chromium}=require('playwright');
const bytes=b=>createHash('sha256').update(b).digest('hex');
const out=process.env.QA_OUTPUT_DIR,inputs=process.env.QA_INPUTS,stages=JSON.parse(process.env.QA_STAGES);
const east='xuhui-medical-college-east-building-one',hospital='xuhui-zhongshan-hospital-main-building',school='xuhui-shanghai-american-school-main';
const native='14-13719-6696',source='d2dc605e-5be1-4b23-89d9-bcd2c0aebdc1',center=[121.4473914,31.19958155];
fs.mkdirSync(out,{recursive:true});
const report={scriptSha256:bytes(fs.readFileSync(__filename)),source,native,stages:[],completed:false};
const save=()=>fs.writeFileSync(path.join(out,'owner-restoration.json'),JSON.stringify(report,null,2)+'\n');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader','--remote-debugging-port=9631']});
 try{
  for(const config of stages){
   const {base,sha256,after}=config;
   const page=await browser.newPage({viewport:{width:900,height:650},hasTouch:true,ignoreHTTPSErrors:true});
   page.setDefaultTimeout(190000);const record={...config,states:[],files:[],signedRuntime:{},errors:[]},seen=new Set(),pending=[];
   report.stages.push(record);save();
   page.on('pageerror',e=>record.errors.push(e.message));page.on('response',response=>{
    const u=new URL(response.url());if(u.origin!==new URL(base).origin||![200,206].includes(response.status()))return;
    const rel=u.pathname.slice(1);seen.add(rel);
    if(['src/map-scene.js','src/building-beacons.js','src/building-beacon-groups.js'].includes(rel))pending.push(response.body().then(b=>{record.signedRuntime[rel]={url:response.url(),sha256:bytes(b),bytes:b.length};}));
   });
   const data=await(await page.request.get(base+'data/candidate-city-integrations.json')).body();assert.equal(bytes(data),sha256);
   const catalog=JSON.parse(data);assert.equal(catalog.resulting_city_count,after?166:165);assert.equal(catalog.models.some(r=>r.id===east),after);record.cityCount=catalog.resulting_city_count;
   const tile=await(await page.request.get(base+'assets/city-detail/macros/'+native+'/online-ids.json.gz')).body();
   const ids=JSON.parse(tile[0]===31?require('node:zlib').gunzipSync(tile):tile);assert.ok(ids.building.includes(source));record.nativeFeatureIds={file:'assets/city-detail/macros/'+native+'/online-ids.json.gz',sha256:bytes(tile),containsTarget:true};
   const original=after?east:hospital;
   await page.goto(base+'index.html#landmark='+original+'&mode=overview',{waitUntil:'domcontentloaded'});
   async function readySelected(id){await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__?.scene;return s&&!s.map.isMoving()&&new URLSearchParams(location.hash.slice(1)).get('landmark')===id&&s.getLandmarkAssetState(id)?.visible;},id,{timeout:220000,polling:500});}
   await readySelected(original);
   async function jump(near){await page.evaluate(({center,near})=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo({center,zoom:near?18.52:15.45,pitch:near?42:32,bearing:near?159:0,elevation:0});s.loadLandmarks();s.refreshBuildingBeacons();},{center,near});}
   async function choose(id,name){
    const toggle=page.locator('#panel-toggle');if(await toggle.getAttribute('aria-expanded')==='false')await toggle.click();
    await page.locator('#place-search').fill(name);await page.locator('#place-list button[data-place="'+id+'"]').click();await readySelected(id);
   }
   async function observe(phase,near,departed=false,photo=false){
    await page.waitForFunction(({east,native,after,near,departed})=>{
     const s=window.__SHANGHAI_APP__?.scene;if(!s||s.map.isMoving())return false;
     const a=s.getLandmarkAssetState(east),c=s.getCandidateIntegrationState(),group=c.shader.ownerScopedSources.find(g=>g.macro_id===native&&g.feature_local_ids.includes(2076)&&g.feature_local_ids.includes(198));
     if(departed)return !a?.visible&&!c.displayClips.some(r=>r.id===east);
     if(near&&(!group||!s.getStreamingState().detail.active.some(v=>v.id===group.id)))return false;
     if(after)return a?.visible&&a.variant===(near?'full':'distant')&&c.displayClips.some(r=>r.id===east);
     return !a?.visible&&!c.displayClips.some(r=>r.id===east);
    },{east,native,after,near,departed},{timeout:225000,polling:450});
    const state=await page.evaluate(({east,hospital,school,native,source})=>{
     const s=window.__SHANGHAI_APP__.scene,m=s.map,c=s.getCandidateIntegrationState(),st=s.getStreamingState();
     const feature=(id)=>m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id});
     return {route:location.hash,camera:{center:m.getCenter(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},rawVector:feature(source),
      hospitalVector:feature('dc2ae254-febe-43be-98b0-bae3cda9398b'),schoolVector:feature('bef5e562-b7a8-4f55-80c5-400d32d288b9'),
      tileSources:st.active?.filter(v=>v.visible).map(v=>v.id)||[],nearActive:st.detail.active.map(v=>v.id),nearGroup:c.shader.ownerScopedSources.find(g=>g.macro_id===native&&g.feature_local_ids.includes(2076)&&g.feature_local_ids.includes(198))||null,
      target:c.displayClips.filter(r=>r.id===east),asset:s.getLandmarkAssetState(east),hospitalVisible:!!s.getLandmarkAssetState(hospital)?.visible,schoolVisible:!!s.getLandmarkAssetState(school)?.visible,
      pendingTileStates:st.pendingStates,featureReferences:st.hiddenFeatures,terrain:!m.painter.context.gl.isContextLost()};
    },{east,hospital,school,native,source});
    assert.ok(state.terrain);assert.equal(!!state.asset.visible,after&&!departed);assert.equal(state.target.length,after&&!departed?1:0);
    if(near&&!departed){assert.deepEqual(state.nearGroup.clip_feature_local_ids,after?[2076]:[]);assert.deepEqual([...state.nearGroup.feature_local_ids].sort((a,b)=>a-b),[198,1408,1426,2076,2361]);}
    if(departed)assert.ok(!state.rawVector.candidateModel);
    if(photo){const file=phase+'.png';const b=await page.screenshot({path:path.join(out,file),timeout:150000});state.photo={file,bytes:b.length,sha256:bytes(b)};}
    record.states.push({phase,...state});record.files=[...seen].sort();save();console.log(after,phase,state.rawVector,state.asset?.variant,state.tileSources.includes(native));
   }
   await jump(true);await observe('campus-near',true);
   await choose(school,'美童公学');await observe('left-near',false,true);
   await choose(original,after?'东一号楼':'中山医院3号楼');await jump(true);await observe('returned-near',true,false,after);
   await jump(false);await observe('campus-far',false);
   await choose(school,'美童公学');await observe('left-far',false,true);
   await choose(original,after?'东一号楼':'中山医院3号楼');await jump(false);await observe('returned-far',false,false,after);
   await Promise.all(pending);record.files=[...seen].sort();assert.deepEqual(record.errors,[]);
   await page.close();record.pageClosed=true;save();
  }
  const [before,after]=report.stages;
  for(const [i,b] of before.states.entries()){
   const a=after.states[i];assert.equal(a.phase,b.phase);
   if(a.phase.startsWith('left-')){assert.equal(!!a.rawVector.localModel,!!b.rawVector.localModel);assert.equal(!!a.rawVector.candidateModel,!!b.rawVector.candidateModel);}
  }
  report.completed=true;
 }catch(e){report.failure=String(e.stack);throw e;}
 finally{await browser.close();report.browserClosed=true;save();}
})().catch(e=>{console.error(e);process.exitCode=1;});
