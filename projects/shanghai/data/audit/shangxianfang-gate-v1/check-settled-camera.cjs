/* Open both real directory links, wait for the street opposite, and verify the gate on the registered map. */
const assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('playwright');
const id='huangpu-shangxianfang-gate';
const base=process.env.MODEL_BASE_URL,project=process.env.SHANGHAI_PROJECT_ROOT,out=process.env.QA_OUTPUT_DIR;
const digest=b=>createHash('sha256').update(b).digest('hex');
const local=p=>fs.readFileSync(path.join(project,p));
const source=JSON.parse(local('source/precise/'+id+'/footprint-review.json'));
const group=source.frozen_macro+'/'+source.near_tiles[0].id;
const neighbors=source.owners.filter(r=>[2357,2541,2597].includes(r.local_id)).map(r=>[r.local_id,r.source_key.slice(9)]);
const catalogPath='data/candidate-city-integrations.json';
const catalog=JSON.parse(local(catalogPath)),row=catalog.models.at(-1);
const bindingNames=[catalogPath,'src/app.js','src/map-scene.js','src/candidate-overview-camera.js','src/building-beacons.js','src/walk-controller.js','src/candidate-city-integrations.js','index.html','landmarks.html',row.candidate_manifest];
const report={id,base,started:new Date().toISOString(),completed:false,count:catalog.resulting_city_count,
  checkerSha256:digest(fs.readFileSync(__filename)),bindings:Object.fromEntries(bindingNames.map(p=>[p,digest(local(p))])),views:[],downloads:[],ground:[],errors:[]};
const save=()=>fs.writeFileSync(path.join(out,'registered-camera-browser.json'),JSON.stringify(report,null,2)+'\n');
async function run(){
  assert.equal(row.id,id);assert.equal(report.count,108);assert.equal(row.overviewBearing,300);assert.equal(row.overviewPitch,61);
  assert.equal(report.bindings[catalogPath],process.env.EXPECTED_CATALOG_SHA256);
  fs.mkdirSync(out,{recursive:true});save();
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
  const seen=new Set();
  try{
    const verifiedMobile=process.env.QA_VERIFIED_MOBILE_REPORT;
    if(verifiedMobile){
      const previous=JSON.parse(fs.readFileSync(verifiedMobile));
      assert.deepEqual(previous.bindings,report.bindings);assert.deepEqual(previous.errors,[]);
      assert.equal(previous.base,base);assert.equal(previous.views.length,2);
      for(const r of previous.views){
        assert.deepEqual(r.viewport,[390,844]);assert.equal(r.beacons,108);assert.equal(r.picked,id);
        assert.ok(Math.abs(r.bearing+60)<.0001&&Math.abs(r.pitch-61)<.0001);
        const image=fs.readFileSync(path.join(path.dirname(verifiedMobile),r.file));assert.equal(digest(image),r.sha256);
        fs.writeFileSync(path.join(out,r.file),image);report.views.push(r);
      }
      assert.ok(report.views.at(-1).groupLoaded);
      report.mobileEvidenceSha256=digest(fs.readFileSync(verifiedMobile));save();
    }
    const entries=verifiedMobile?[['desktop',870,660]]:[['mobile',390,844],['desktop',870,660]];
    for(const [name,width,height]of entries){
      const context=await browser.newContext({viewport:{width,height},hasTouch:true,ignoreHTTPSErrors:true});
      const page=await context.newPage();page.setDefaultTimeout(220000);
      page.on('pageerror',e=>report.errors.push(e.message));page.on('response',r=>{
        const u=new URL(r.url());if(r.status()===200&&u.origin===new URL(base).origin)seen.add(decodeURIComponent(u.pathname.slice(1)));
      });
      await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
      assert.equal(await page.locator('.landmark-card[data-landmark]').count(),108);
      await page.locator('#district-310101 [data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').tap();
      async function shot(phase,near,variant){
        await page.waitForFunction(({id,g,near,variant})=>{
          const s=window.__SHANGHAI_APP__?.scene,a=s?.getLandmarkAssetState(id);
          return a?.status==='loaded'&&a.visible&&a.variant===variant&&!s.map.isMoving()&&
            (!near||s.getStreamingState().detail.active.some(e=>e.id===g));
        },{id,g:group,near,variant},{polling:450,timeout:210000});
        await page.evaluate(()=>new Promise(done=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>done());m.triggerRepaint();}));
        const state=await page.evaluate(({id,g,ns})=>{
          const a=window.__SHANGHAI_APP__,s=a.scene,m=s.map,mesh=s.getLandmarkAssetState(id),b=s.getBuildingBeaconState();
          const label=b.labelPositions.find(p=>p.id===id),gl=m.painter.context.gl;
          return {route:location.hash,mode:a.mode,name:document.querySelector('#location-name').textContent,asset:mesh.verifiedAsset.sha256,
            triangles:mesh.triangles,variant:mesh.variant,zoom:m.getZoom(),bearing:m.getBearing(),pitch:m.getPitch(),center:m.getCenter(),elevation:m.getCenterElevation(),
            beacons:b.count,picked:label&&s.pickBuildingBeacon(label),group:g,groupLoaded:s.getStreamingState().detail.active.some(t=>t.id===g),
            neighbors:ns.map(([localId,key])=>({localId,state:m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:key})})),
            clips:s.getCandidateIntegrationState().clips.filter(c=>c.id===id),contextLost:gl.isContextLost(),glError:gl.getError()};
        },{id,g:group,ns:neighbors});
        assert.equal(state.asset,row.assets[variant==='full'?'web':'lod'].sha256);assert.equal(state.mode,'overview');assert.equal(state.name,row.name);
        assert.equal(state.beacons,108);assert.equal(state.picked,id);assert.equal(state.glError,0);assert.equal(state.contextLost,false);assert.deepEqual(state.clips,[]);
        if(near)for(const n of state.neighbors){assert.equal(n.state.localModel,true);assert.notEqual(n.state.candidateModel,true);}
        const file='registered-'+name+'-'+phase+'.png',png=await page.screenshot({path:path.join(out,file),timeout:200000});
        report.views.push({viewport:[width,height],phase,file,sha256:digest(png),bytes:png.length,...state});save();console.log(name,phase);
      }
      await shot('arrival',false,'full');await shot('with-neighbors',true,'full');
      assert.ok(Math.abs(report.views.at(-1).bearing+60)<.0001);assert.ok(Math.abs(report.views.at(-1).pitch-61)<.0001);
      if(name==='desktop'){
        const control=page.locator('#panel-toggle');if(await control.getAttribute('aria-expanded')==='true')await control.click();
        const original=JSON.parse(fs.readFileSync(path.join(__dirname,'placement-geometry.json')));
        const extra=source.owners.slice(0,3).map(n=>{const ring=n.geometry.coordinates[0].slice(0,-1);return {name:'retained '+n.local_id,
          wgs84:ring.reduce((a,p)=>[a[0]+p[0]/ring.length,a[1]+p[1]/ring.length],[0,0]),blocked:true};});
        report.ground=await page.evaluate(points=>{const s=window.__SHANGHAI_APP__.scene;return points.map(p=>({...p,actual:s.collisionAt(...p.wgs84)}));},[...original.ground.witnesses,...extra]);
        for(const p of report.ground)assert.equal(p.actual,p.blocked?'building':null,p.name);
        const jump=async(zoom,pitch,elevation)=>page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.refreshBuildingBeacons();s.loadLandmarks();},
          {center:[row.lng,row.lat],bearing:300,pitch,zoom,elevation,padding:{left:60,right:30,top:20,bottom:112}});
        await jump(20.5,58,6);await shot('street',true,'full');
        await page.setViewportSize({width:560,height:440});await jump(15.5,30,0);await shot('distant',false,'distant');
        const manifest=JSON.parse(local(row.candidate_manifest));
        const paths=Object.entries(manifest.assets).map(([role,item])=>({role,path:path.posix.join(path.posix.dirname(row.candidate_manifest),item.file),sha256:item.sha256,bytes:item.bytes}));
        for(const x of source.frozen_bindings.filter(x=>x.repository_path.includes('/near/')||x.repository_path.endsWith('/far.glb')))paths.push({role:'city-source',path:x.repository_path.replace('projects/shanghai/',''),sha256:x.sha256});
        for(const item of paths){const res=await page.request.get(new URL(item.path,base).href),b=await res.body();assert.equal(res.status(),200);assert.equal(digest(b),item.sha256);
          if(item.bytes)assert.equal(b.length,item.bytes);if(!['raw','native'].includes(item.role))assert.ok(seen.has(item.path),item.path);
          report.downloads.push({...item,bytes:b.length,seenByScene:seen.has(item.path)});}
        const res=await page.request.get(new URL(catalogPath,base).href);assert.equal(digest(await res.body()),report.bindings[catalogPath]);
      }
      await context.close();
    }
    assert.deepEqual(report.errors,[]);report.completed=true;
  }catch(e){report.failure=e.stack;throw e;}
  finally{report.finished=new Date().toISOString();save();await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
