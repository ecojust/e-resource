/* Exercise the registered residence, both source owners and the actual open courtyards. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');

const id = 'jingan-huaye-apartments';
const audit = __dirname;
const root = process.env.SHANGHAI_PROJECT_ROOT || path.resolve(audit,'../../..');
const base = process.env.MODEL_BASE_URL || 'http://127.0.0.1:8897/';
const out = process.env.QA_OUTPUT_DIR || audit;
const read = file => JSON.parse(fs.readFileSync(file));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const spec = read(path.join(audit,'map-case.json'));
const contract = read(path.join(audit,'final-placement-contract.json'));
const geometry = read(path.join(audit,'placement-geometry.json'));
const source = read(path.join(root,'source/precise',id,'footprint-review.json'));
const catalogFile = 'data/candidate-city-integrations.json';
const catalog = read(path.join(root,catalogFile));
const model = catalog.models.find(row=>row.id===id);
const owners = source.owners.map(({local_id,key})=>({local_id,key}));
const context = {id,macro:source.macro_id,groups:spec.native_groups,owners,neighbors:spec.neighbor_probes};
const report = {id,base,started:new Date().toISOString(),catalogSha256:sha(fs.readFileSync(path.join(root,catalogFile))),
  bindings:{},files:[],views:[],screenshots:[],pageErrors:[],requestErrors:[],completed:false};
const save = () => fs.writeFileSync(path.join(out,'main-browser.json'),JSON.stringify(report,null,2)+'\n');

async function run(){
  assert.equal(catalog.resulting_city_count,spec.required_city_count);
  assert.equal(report.catalogSha256,spec.city_catalog_sha256);
  for (const field of ['owners','source_feature_ids','replacement_geometry','collision_geometry','model_geometry_sha256']) assert.deepEqual(model[field],contract[field]);
  fs.mkdirSync(out,{recursive:true});
  report.cases={script:sha(fs.readFileSync(__filename)),map:sha(fs.readFileSync(path.join(audit,'map-case.json'))),geometry:sha(fs.readFileSync(path.join(audit,'placement-geometry.json'))),contract:sha(fs.readFileSync(path.join(audit,'final-placement-contract.json')))};
  for(const f of ['index.html','landmarks.html','src/app.js','src/map-scene.js','src/building-beacons.js','src/candidate-city-integrations.js','src/candidate-city-clipping.js','src/candidate-vector-geometry.js','src/candidate-vector-clipping.js',catalogFile,model.candidate_manifest]) report.bindings[f]=sha(fs.readFileSync(path.join(root,f)));
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  report.browser=browser.version();
  const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,ignoreHTTPSErrors:true});
  const received=new Set();
  page.setDefaultTimeout(240000);
  page.on('pageerror',err=>report.pageErrors.push(err.message));
  page.on('requestfailed',req=>{if(req.failure()?.errorText!=='net::ERR_ABORTED') report.requestErrors.push({url:req.url(),error:req.failure().errorText});});
  page.on('response',res=>{const url=new URL(res.url());if(res.status()>=400)report.requestErrors.push({url:res.url(),status:res.status()});if(url.origin===new URL(base).origin&&res.ok()) received.add(decodeURIComponent(url.pathname.slice(1)));});
  async function navigate(camera){
    await page.evaluate(camera=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo({...camera,padding:{top:0,left:0,right:0,bottom:0}});s.loadLandmarks();s.refreshBuildingBeacons();},camera);
  }
  async function capture(name){
    const destination=path.join(out,name+'.png');
    try{
      return {bytes:await page.screenshot({path:destination,timeout:30000}),method:'Playwright visible viewport'};
    }catch(error){
      if(!String(error).includes('Timeout'))throw error;
      const session=await page.context().newCDPSession(page);
      try{
        const frame=await Promise.race([
          session.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false,optimizeForSpeed:true}),
          new Promise((_,reject)=>{const timer=setTimeout(()=>reject(new Error('Chromium viewport capture timed out')),60000);timer.unref();}),
        ]);
        const bytes=Buffer.from(frame.data,'base64');fs.writeFileSync(destination,bytes);
        return {bytes,method:'Chromium visible viewport'};
      }finally{await session.detach();}
    }
  }
  async function view(name,variant,detail){
    console.log('Checking '+name,new Date().toISOString());
    await page.waitForFunction(({id,macro,groups,owners,variant,detail})=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s||s.map.isMoving()||s.map.getCanvas().clientWidth!==innerWidth)return false;
      const asset=s.getLandmarkAssetState(id),c=s.getCandidateIntegrationState();
      if(asset.status!=='loaded'||!asset.visible||(variant&&asset.variant!==variant)||!c.clips.some(r=>r.id===id))return false;
      if(!detail)return true;
      const stream=s.getStreamingState();
      return stream.active.some(r=>r.id===macro&&r.visible)&&groups.every(g=>{
        const scoped=c.shader.ownerScopedSources.find(x=>x.macro_id===macro&&x.feature_local_ids.includes(g.owners[0]));
        return scoped&&stream.detail.active.some(x=>x.id===scoped.id)&&scoped.clip_feature_local_ids.includes(g.owners[0]);
      })&&owners.every(o=>{const f=s.map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o.key.slice(9)});return f.candidateModel||f.localModel;})&&c.vector.filter(v=>v.active).every(v=>!v.pending&&!v.residualLayer?.busy&&(!v.partialIDs||v.residualLayer?.ready));
    },{...context,variant,detail},{timeout:420000,polling:650});
    await page.evaluate(()=>new Promise(done=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>done());m.triggerRepaint();}));
    const state=await page.evaluate(({id,macro,groups,owners,neighbors})=>{
      const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,c=s.getCandidateIntegrationState(),a=s.getLandmarkAssetState(id),b=s.getBuildingBeaconState();
      const vec=o=>({local_id:o.local_id,state:m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o.key.slice(9)})});
      const visible=c.shader.ownerScopedSources.filter(g=>g.macro_id===macro);
      const label=b.labelPositions.find(p=>p.id===id),gl=m.painter.context.gl;
      return {route:location.hash,title:document.querySelector('#location-name').textContent,mode:app.mode,walkDisabled:document.querySelector('#walk-mode').disabled,viewport:[innerWidth,innerHeight],
        labels:b.count,hit:label?s.pickBuildingBeacon(label):null,model:{variant:a.variant,visible:a.visible,sha256:a.verifiedAsset.sha256,bytes:a.verifiedAsset.bytes,triangles:a.triangles,anchor:a.anchor,heading:a.heading,scale:a.scale},
        owners:owners.map(vec),neighbors:neighbors.map(vec),groups:groups.map(g=>visible.find(v=>v.feature_local_ids.includes(g.owners[0]))||null),
        neighborMasks:visible.flatMap(g=>g.clip_feature_local_ids).filter(value=>neighbors.some(n=>n.local_id===value)),
        clip:c.clips.find(r=>r.id===id),shader:{triangles:c.shader.triangles,limit:c.shader.triangleLimit},camera:{center:m.getCenter(),elevation:m.getCenterElevation(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},glError:gl.getError(),contextLost:gl.isContextLost()};
    },context);
    report.views.push({name,...state});save();
    assert.equal(state.labels,spec.required_city_count);assert.equal(state.hit,id);assert.equal(state.title,model.name);assert.equal(state.mode,'overview');assert.equal(state.walkDisabled,true);
    assert.equal(new URLSearchParams(state.route.slice(1)).get('landmark'),id);assert.equal(state.glError,0);assert.equal(state.contextLost,false);
    const file=model.assets[state.model.variant==='full'?'web':'lod'];
    assert.equal(state.model.sha256,file.sha256);assert.equal(state.model.triangles,file.triangles);assert.equal(state.model.bytes,file.bytes);assert.deepEqual(state.model.anchor,[model.lng,model.lat]);assert.equal(state.model.heading,model.heading);assert.equal(state.model.scale,model.scale);
    assert.deepEqual(state.clip.owners,contract.owners);assert.deepEqual(state.clip.geometry,contract.replacement_geometry);
    assert.deepEqual(state.neighborMasks,[]);for(const n of state.neighbors)assert.notEqual(n.state.candidateModel,true);
    if(detail)for(const [i,g] of spec.native_groups.entries()){
      assert.deepEqual(state.groups[i].feature_local_ids,g.ids);assert.deepEqual(state.groups[i].clip_feature_local_ids,g.owners);assert.equal(state.groups[i].triangles,3);
    }
    const screenshot=await capture(name);
    report.screenshots.push({name:name+'.png',bytes:screenshot.bytes.length,sha256:sha(screenshot.bytes),viewport:state.viewport,method:screenshot.method});save();
  }
  async function receipt(name,expected,seen){
    const response=await page.request.get(new URL(name,base).href),data=await response.body();
    assert(response.ok(),name);assert.equal(sha(data),expected.sha256,name);assert.equal(data.length,expected.bytes,name);
    if(seen)assert(received.has(name),'Not observed in real scene '+name);
    report.files.push({file:name,bytes:data.length,sha256:sha(data),requestedByScene:received.has(name)});
  }
  try{
    await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
    assert.equal(await page.locator('.landmark-card[data-landmark]').count(),spec.required_city_count);
    await page.locator('#district-'+model.districtId+' [data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').tap();
    await view('map-mobile',null,false);
    await page.setViewportSize({width:900,height:690});
    await page.reload({waitUntil:'domcontentloaded'});await view('map-desktop','full',false);
    const button=page.locator('#panel-toggle');if(await button.getAttribute('aria-expanded')==='true')await button.click();
    await navigate(spec.camera_front);await view('map-southwest','full',true);
    const ground=geometry.ground_probes.map(p=>({label:p.label,point:p.world,expected:p.blocked?'building':null}));
    for(const p of spec.neighbor_probes.slice(0,2))ground.push({label:'preserved lower building '+p.local_id,point:p.position,expected:'building'});
    report.ground=await page.evaluate(async probes=>{const s=window.__SHANGHAI_APP__.scene;await s.waitForData(12000);return probes.map(p=>({...p,actual:s.collisionAt(...p.point)}));},ground);
    save();for(const p of report.ground)assert.equal(p.actual,p.expected,p.label);
    await navigate(spec.camera_roof);await view('map-roof','full',true);
    await page.setViewportSize({width:520,height:440});
    await navigate({...spec.camera_front,zoom:15.5,pitch:34,elevation:0});await view('map-distant','distant',false);
    const manifest=read(path.join(root,model.candidate_manifest));
    for(const [role,file] of Object.entries(manifest.assets))await receipt(path.posix.join(path.posix.dirname(model.candidate_manifest),file.file),file,['full','lod'].includes(role));
    for(const [name,file] of Object.entries(source.frozen_bindings))await receipt('assets/city-detail/macros/'+source.macro_id+'/'+name,file,name==='far.glb'||name.startsWith('near/'));
    for(const [f,sum] of Object.entries(report.bindings))assert.equal(sha(fs.readFileSync(path.join(root,f))),sum,'Changed input '+f);
    assert.deepEqual(report.pageErrors,[]);assert.deepEqual(report.requestErrors,[]);report.completed=true;
  }catch(error){
    report.error=error.stack;report.failureState=await page.evaluate(({id,macro})=>{const s=window.__SHANGHAI_APP__?.scene;if(!s)return {text:document.body.innerText.slice(0,900)};return {camera:s.map.getCenter(),model:s.getLandmarkAssetState(id),groups:s.getCandidateIntegrationState().shader.ownerScopedSources.filter(g=>g.macro_id===macro),stream:s.getStreamingState().detail,route:location.hash};},context).catch(String);throw error;
  }finally{save();await browser.close();}
}
run().catch(err=>{console.error(err);process.exitCode=1;});
