/* Verify the historical street facade from the public street on the registered map. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto'),{chromium}=require('playwright');
const id='hongkou-tilanqiao-historic-front',before=process.argv.includes('--before');
const project=process.env.SHANGHAI_PROJECT_ROOT,base=process.env.MODEL_BASE_URL,out=process.env.QA_OUTPUT_DIR;
const bytes=f=>fs.readFileSync(f==='data/candidate-city-integrations.json'&&process.env.QA_CATALOG_OVERRIDE?process.env.QA_CATALOG_OVERRIDE:path.join(project,f)),read=f=>JSON.parse(bytes(f)),digest=b=>createHash('sha256').update(b).digest('hex');
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const catalogFile='data/candidate-city-integrations.json',catalog=read(catalogFile),row=catalog.models.find(r=>r.id===id);
 assert.equal(!!row,!before);
 const doc=JSON.parse(fs.readFileSync(process.env.QA_STREET_CONTRACT||path.join(__dirname,'final-placement-contract.json')));
 const review=JSON.parse(fs.readFileSync(process.env.QA_STREET_REFERENCE||path.join(project,'source/precise',id,'footprint-review.json')));
 const group=review.near_tiles.find(g=>g.feature_local_ids.includes(1447)),macro=group.id.split('-').slice(0,3).join('-');
 const sources=review.owners.filter(o=>[1447,2013].includes(o.local_id));assert.equal(sources.length,2);
 if(row){assert.deepEqual(row.source_feature_ids,{building:[],building_part:[]});assert.equal(row.replacement_geometry,null);assert.equal(row.navigation.listed,false);assert(!row.owner&&!row.owners);assert.deepEqual(row.collision_geometry,doc.collision_geometry);}
 const selected=before?catalog.models.at(-1).id:id;
 const report={before,started:new Date().toISOString(),base,model:id,selected,catalog:{count:catalog.resulting_city_count,sha256:digest(bytes(catalogFile))},script_sha256:digest(fs.readFileSync(__filename)),views:[],http:[],errors:[],warnings:[],completed:false};
 const save=()=>fs.writeFileSync(path.join(out,before?'control-browser.json':'main-browser.json'),JSON.stringify(report,null,2)+'\n');
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
 const page=await browser.newPage({viewport:before?{width:870,height:660}:{width:390,height:844},hasTouch:true,ignoreHTTPSErrors:true});page.setDefaultTimeout(240000);
 const loaded=new Set();page.on('response',r=>{const u=new URL(r.url());if(r.status()===200&&u.origin===new URL(base).origin)loaded.add(decodeURIComponent(u.pathname.slice(1)));});page.on('pageerror',e=>report.errors.push(e.message));page.on('console',m=>{if(m.type()==='warning'&&m.text().includes('[Shanghai map]'))report.warnings.push(m.text());});
 const jump=async(elevation,pitch,zoom)=>page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},{center:[doc.lng,doc.lat],elevation,pitch,bearing:doc.overviewBearing,zoom,padding:{top:0,left:160,right:5,bottom:115}});
 async function picture(name,variant,requireNative){
   const args={id,variant,requireNative,group:macro+'/'+group.id,macro,before};
   await page.waitForFunction(({id,variant,requireNative,group,macro,before})=>{
     const sc=window.__SHANGHAI_APP__?.scene,m=sc?.map,l=document.querySelector('#loading'),css=l&&getComputedStyle(l);if(!sc||m.isMoving()||css?.opacity!=='0'||css.visibility!=='hidden')return false;
     const a=sc.getLandmarkAssetState(id);if(!before&&(!a?.visible||a?.status!=='loaded'||a.variant!==variant))return false;
     const st=sc.getStreamingState();return !requireNative||(st.active.some(g=>g.id===macro&&g.visible)&&st.detail.active.some(g=>g.id===group));
   },args,{timeout:310000,polling:400});
   const v=await page.evaluate(async({id,sources,group,before})=>{const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,c=s.getCandidateIntegrationState(),b=s.getBuildingBeaconState(),label=b.labelPositions.find(q=>q.id===id);
     const frames=[];for(let i=0;i<4;i++){await new Promise(done=>requestAnimationFrame(done));const css=getComputedStyle(document.querySelector('#loading'));frames.push([m.getBearing(),m.getPitch(),m.getZoom(),m.getCenter().toArray(),m.isMoving(),css.opacity,css.visibility]);}
     const gl=m.painter.context.gl;return {route:location.hash,rows:b.count,place:document.getElementById('location-name').textContent,frames,asset:before?null:s.getLandmarkAssetState(id),picked:label?s.pickBuildingBeacon(label):null,nativeGroup:s.getStreamingState().detail.active.find(i=>i.id===group),scope:c.shader.ownerScopedSources.find(i=>i.id===group)||null,clips:c.clips.filter(i=>i.id===id),sections:c.sourceSections.filter(i=>i.id===id),sources:sources.map(o=>({id:o.local_id,state:m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o.key.slice(9)})})),glError:gl.getError(),contextLost:gl.isContextLost()};
   },{id,group:args.group,sources,before});
   assert.equal(v.rows,report.catalog.count);assert.equal(v.glError,0);assert.equal(v.contextLost,false);assert.deepEqual(v.clips,[]);assert.deepEqual(v.sections,[]);
   for(const f of v.frames){assert.deepEqual(f,v.frames[0]);assert.deepEqual(f.slice(-3),[false,'0','hidden']);}
   if(!before){if(name==='map-mobile'||name==='map-desktop'){assert.equal(Math.round(v.frames[0][0]),row.overviewBearing);assert.equal(Math.round(v.frames[0][1]),row.overviewPitch);}assert.equal(v.picked,id);assert.equal(v.place,row.name);assert.equal(v.asset.verifiedAsset.sha256,row.assets[variant==='full'?'web':'lod'].sha256);}
   if(requireNative){assert.equal(v.nativeGroup.id,args.group);if(v.scope){assert.deepEqual(v.scope.feature_local_ids,group.feature_local_ids);assert(!v.scope.clip_feature_local_ids.some(i=>[1447,2013].includes(i)));}assert(v.sources.every(s=>!s.state.candidateModel));}
   const file=name+'.png',image=await page.screenshot({path:path.join(out,file),timeout:220000});report.views.push({name,...v,file,image_sha256:digest(image),image_bytes:image.length});save();
 }
 try{
   if(before){
     const prior=catalog.models.at(-1);await page.goto(base+'index.html#landmark='+prior.id+'&mode=overview',{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene&&getComputedStyle(document.getElementById('loading')).visibility==='hidden',null,{timeout:420000});
     await jump(5.3,54,20.15);await picture('street-before',null,true);
   }else{
     await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});const card=page.locator('.landmark-card[data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]');assert.equal(await card.count(),1);await card.tap();
     await picture('map-mobile','full',true);await page.setViewportSize({width:870,height:660});
     await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});await page.locator('.landmark-card[data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').click();
     await picture('map-desktop','full',true);if(process.env.QA_DEFAULTS_ONLY==='1'){assert.deepEqual(report.errors,[]);assert.equal(row.overviewPitch,57);report.completed=true;return;}const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
     await jump(5.3,54,20.15);await picture('street-historical-front','full',true);
     await page.setViewportSize({width:600,height:460});await jump(0,30,15.4);await picture('map-distant','distant',false);
     const manifest=read(row.candidate_manifest);for(const[role,a]of Object.entries(manifest.assets)){
       const file=path.posix.join(path.posix.dirname(row.candidate_manifest),a.file),res=await page.request.get(new URL(file,base).href),body=await res.body();assert.equal(res.status(),200);assert.equal(digest(body),a.sha256);if(['full','lod'].includes(role))assert(loaded.has(file));
       report.http.push({role,file,status:200,bytes:body.length,sha256:digest(body),seen:loaded.has(file)});
     }
   }
   assert.deepEqual(report.errors,[]);report.completed=true;
 }catch(e){report.failure=e.stack;throw e;}
 finally{report.finished=new Date().toISOString();save();await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
