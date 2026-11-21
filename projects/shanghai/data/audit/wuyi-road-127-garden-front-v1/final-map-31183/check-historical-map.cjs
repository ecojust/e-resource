/** Exercise an archive-only location from the public district directory across its two releases. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const assert=require('node:assert/strict');
const [mode,binding,output,oldFile]=process.argv.slice(2);
assert.ok(['before','after-desktop','after-mobile'].includes(mode));
const input=JSON.parse(fs.readFileSync(binding));
const current=mode!=='before',n=current?'183':'182',site=input.origins[n];
const id=input.id, prior=input.previous, archive='wuyi-road-127-history.html';
const base=site.url, locationName='武夷路127号历史住宅南立面';
const pose={center:[121.424,31.216], zoom:17.4,pitch:60,bearing:35};
const digest=b=>createHash('sha256').update(b).digest('hex');
fs.mkdirSync(output,{recursive:true});
const file=path.join(output,mode+'.json');
const r={mode,base,id,started:new Date().toISOString(),script_sha256:digest(fs.readFileSync(__filename)),
  signed_input_sha256:digest(fs.readFileSync(binding)),catalog:site.catalog_sha256,count:site.count,
  captures:[],signed_responses:{},page_errors:[],request_failures:[],http_errors:[],states:[],passed:false,browser_closed:false};
function save(){fs.writeFileSync(file+'.part',JSON.stringify(r,null,2)+'\n');fs.renameSync(file+'.part',file);}
async function main(){
 const launch=()=>chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--enable-low-end-device-mode','--num-raster-threads=1','--disable-gpu-rasterization','--js-flags=--max-old-space-size=384','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9883']});
 let browser=await launch();
 try{
  for(const [device,width,height,touch] of (mode==='after-mobile'?[['mobile',390,844,true]]:[['desktop',930,695,false]])){
   let page;
   const openDevice=()=>browser.newPage({viewport:{width,height},hasTouch:touch});
   const pending=new Set();
   const observe=()=>{
   page.on('pageerror',e=>r.page_errors.push(e.message));
   page.on('requestfailed',request=>{if(request.failure()?.errorText==='net::ERR_ABORTED'){r.canceled_requests??=[];r.canceled_requests.push(request.url());}else r.request_failures.push({url:request.url(),reason:request.failure()});});
   page.on('response',res=>{
    const u=new URL(res.url());if(u.origin!==new URL(base).origin)return;
    if(res.status()>=400)r.http_errors.push({url:res.url(),status:res.status()});
    const name=u.pathname.slice(1);if(!site.files[name]||res.status()!==200)return;
    const promise=res.body().then(b=>{const h=digest(b);assert.equal(h,site.files[name].sha256,name);r.signed_responses[name]=h;})
      .catch(e=>{r.unread_bodies??=[];r.unread_bodies.push([name,e.message]);});
    pending.add(promise);promise.finally(()=>pending.delete(promise));
   });
   };
   page=await openDevice();observe();
  async function enterMapLabel(id, previous, position, pointer, report) {
    await page.goto(new URL('index.html#landmark='+previous+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(previous=>{const s=window.__SHANGHAI_APP__?.scene;const cover=document.getElementById('loading');return s && !s.map.isMoving() && cover?.classList.contains('loaded') && getComputedStyle(cover).visibility==='hidden' && new URLSearchParams(location.hash.slice(1)).get('landmark')===previous;},previous,{polling:350,timeout:240000});
    const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
    let hit;
    for(const zoom of [17.55,18.65,16.55]) {
      await jump({center:position,zoom,pitch:0,bearing:0,elevation:0,padding:{top:0,right:0,bottom:0,left:0}});
      const handle=await page.waitForFunction(id=>{
        const s=window.__SHANGHAI_APP__.scene;if(s.map.isMoving())return false;
        const c=s.map.getCanvas(),r=c.getBoundingClientRect();const b=s.getBuildingBeaconState().labelPositions.find(b=>b.id===id||b.memberIds?.includes(id));if(!b)return false;
        for(const dx of [0,-.22,.22])for(const dy of [0,-.18,.18]){
          const px=b.x+dx*(b.width||0),py=b.y+dy*(b.height||0);if(document.elementFromPoint(r.x+px,r.y+py)===c && s.pickBuildingBeacon({x:px,y:py})===b.id)return {x:r.x+px,y:r.y+py,id:b.id,member:b.id!==id,previous:location.hash,viewport:[innerWidth,innerHeight]};
        }return false;
      },id,{polling:250,timeout:24000}).catch(()=>null);
      if(handle){hit=await handle.jsonValue();break;}
    }
    assert.ok(hit,'Target must be reachable by a visible map label');
    await page.evaluate(()=>{window.__verifiedPointer=null;window.addEventListener('pointerup',e=>{const s=window.__SHANGHAI_APP__.scene,c=s.map.getCanvas(),r=c.getBoundingClientRect();window.__verifiedPointer={trusted:e.isTrusted,on_canvas:e.target===c,type:e.pointerType,x:e.clientX,y:e.clientY,picked:s.pickBuildingBeacon({x:e.clientX-r.left,y:e.clientY-r.top})};},{capture:true,once:true});});
    if(pointer==='touch')await page.touchscreen.tap(hit.x,hit.y);else await page.mouse.click(hit.x,hit.y);
    await page.waitForFunction(()=>window.__verifiedPointer!==null,null,{timeout:24000});const event=await page.evaluate(()=>window.__verifiedPointer);
    assert.ok(event.trusted&&event.on_canvas);assert.equal(event.type,pointer);assert.equal(event.picked,hit.id);
    if(hit.member){const choice=page.locator('dialog.beacon-group-picker[open] [data-landmark="'+id+'"]');if(pointer==='touch')await choice.tap();else await choice.click();}
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id,{timeout:120000});
    (report.realBeaconInputs??=[]).push({hit,pointer:event,landed:id});save();
  }

  async function jump(camera){
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo(c);s.loadLandmarks();s.refreshBuildingBeacons();},camera);
  }

   const press=loc=>touch?loc.tap({timeout:60000}):loc.click({timeout:60000});
   const shot=async(name)=>{
    const b=await page.screenshot({path:path.join(output,name+'.png'),timeout:260000});
    const gl=await page.evaluate(()=>{const m=window.__SHANGHAI_APP__.scene.map;const gl=m.getCanvas().getContext('webgl2');return {lost:gl.isContextLost(),error:gl.getError(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()};});
    assert.equal(gl.lost,false);assert.equal(gl.error,0);
    r.captures.push({device,viewport:[width,height],file:name+'.png',sha256:digest(b),bytes:b.length,gl});save();
   };
   await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded',timeout:180000});
   const all=page.locator('.landmark-card[data-landmark]');await all.first().waitFor({timeout:120000});assert.equal(await all.count(),site.count);
   const selected=current?id:prior;
   assert.equal(await page.locator(`.landmark-card[data-landmark="${id}"]`).count(),current?1:0);
   const anchor=page.locator(`.landmark-card[data-landmark="${selected}"] .card-foot a[href="index.html#landmark=${selected}&mode=overview"]`);
   await press(anchor);
   await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene?.getCandidateIntegrationState,undefined,{timeout:200000});
   await page.waitForFunction(s=>location.hash.includes(s)&&!window.__SHANGHAI_APP__.scene.map.isMoving(),selected,{timeout:160000});
   if(!current){
    await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(true);s.map.jumpTo({...c,padding:{top:0,right:0,bottom:0,left:0}});s.map.triggerRepaint();},pose);
   }else{
    await page.waitForFunction(()=>Math.abs(window.__SHANGHAI_APP__.scene.map.getZoom()-17.4)<.025&&document.querySelector('#history-open')?.hidden===false,undefined,{timeout:100000});
   }
   await page.waitForFunction(()=>{const map=window.__SHANGHAI_APP__?.scene?.map;return map?.getSource('overture-buildings')&&map.isSourceLoaded('overture-buildings')&&!map.isMoving();},undefined,{polling:400,timeout:180000});
   const samples=[];
   for(let i=0;i<3;i++){
    samples.push(await page.evaluate(pt=>window.__SHANGHAI_APP__.scene.collisionAt(...pt),pose.center));
    if(i<2)await page.waitForTimeout(550);
   }
   assert.ok(samples.every(value=>value===samples[0]),'Ground at the public register marker has not stabilized');
   const state=await page.evaluate(({id,pose})=>{
    const app=window.__SHANGHAI_APP__,s=app.scene,ci=s.getCandidateIntegrationState(),m=s.map,st=s.getLandmarkAssetState(id);
    return {center:m.getCenter().toArray(),zoom:m.getZoom(),mode:app.mode,selected_name:document.querySelector('#location-name').textContent,
      location_caption:document.querySelector('#location-district').textContent,show_history:!document.querySelector('#history-open').hidden,
      walk_disabled:document.querySelector('#start-walk').disabled,current_triangles:st.triangles,current_visible:st.visible,
      selected_source_cut:ci.clips.some(x=>x.id===id),selected_display_cut:ci.displayClips.some(x=>x.id===id),
      selected_current_entry:ci.active.some(x=>x.id===id),unchanged_ground_at_rounded_register_point:s.collisionAt(...pose.center)};
   },{id,pose});
   assert.equal(state.current_triangles,0);assert.equal(state.current_visible,false);
   assert.equal(state.selected_source_cut,false);assert.equal(state.selected_display_cut,false);assert.equal(state.selected_current_entry,false);
   assert.ok(Math.abs(state.zoom-pose.zoom)<.025&&state.center.every((v,k)=>Math.abs(v-pose.center[k])<.000003));
   const frozen=JSON.parse(fs.readFileSync(path.join(__dirname,'public-neighborhood.json')));
   const neighborhood=await page.evaluate(async({lng,lat,frozen,stage})=>{
    const scene=window.__SHANGHAI_APP__.scene,map=scene.map;
    await scene.waitForData(10000);
    async function load(url){
     const response=await fetch(url);
     if(response.status!==200)throw new Error('Failed '+url+' '+response.status);
     const bytes=new Uint8Array(await response.arrayBuffer());
     const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
     return {bytes,digest};
    }
    const expected=frozen.stages[stage];
    const table=await load(frozen.table),registry=await load(frozen.registry);
    if(registry.digest!==expected.catalog_sha256||table.digest!==expected.feature_table_sha256)throw new Error('The live neighborhood differs from its two signed inputs');
    const macro=JSON.parse(new TextDecoder().decode(registry.bytes)).macros.find(v=>v.id===frozen.id);
    if(macro.baseline_feature_table_sha256!==table.digest)throw new Error('Wrong macro source');
    const stream=new Blob([table.bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
    const records=JSON.parse(await new Response(stream).text()).features;
    if(records.length!==expected.count)throw new Error('Incomplete ordinary source table');
    const originals={};
    for(const witness of expected.features){
     const row=records.find(r=>r.localId===witness.id);
     if(row?.key!==witness.source_key||!['Polygon','MultiPolygon'].includes(row.geometry.type))throw new Error('Missing nearby native footprint '+witness.id);
     originals[String(witness.id)]={source:row.key,geometry:row.geometry};
    }
    const drawing={};
    for(const source of [...new Set([scene.sourceId,'overture-buildings'])]){
     if(!map.getSource(source))continue;
     const names=[...new Set(map.getStyle().layers.filter(l=>l.source===source&&['building','building_part'].includes(l['source-layer'])).map(l=>l['source-layer']))];
     for(const sourceLayer of names){
      const nearby=[];
      for(const ft of map.querySourceFeatures(source,{sourceLayer})){
       const geom=ft.geometry;if(!['Polygon','MultiPolygon'].includes(geom.type))continue;
       const polys=geom.type==='Polygon'?[geom.coordinates]:geom.coordinates;
       if(polys.some(p=>p[0].some(([x,y])=>Math.abs(x-lng)<.00065&&Math.abs(y-lat)<.00055)))nearby.push(String(ft.properties?.id??ft.id??''));
      }
      drawing[source+'/'+sourceLayer]=[...new Set(nearby)].sort();
     }
    }
    const probes=[[0,0],[-.00015,0],[.00015,0],[0,-.00012],[0,.00012]].map(([x,y])=>({lng:lng+x,lat:lat+y,collision:scene.collisionAt(lng+x,lat+y)}));
    return {mode:scene.getCollisionState().buildingSource,registry:registry.digest,table:table.digest,originals,drawing,probes};
   },{lng:pose.center[0],lat:pose.center[1],frozen,stage:n});
   assert.equal(Object.keys(neighborhood.originals).length,6);
   const originalFootprints=Object.fromEntries(Object.entries(neighborhood.originals).map(([id,r])=>[id,{source:r.source,sha256:digest(JSON.stringify(r.geometry))}]));
   state.retainedNeighborhood={probes:neighborhood.probes,originalFootprints,currentDrawing:neighborhood.drawing,mode:neighborhood.mode,registry_sha256:neighborhood.registry,table_sha256:neighborhood.table};
   if(current){
    const before=JSON.parse(fs.readFileSync(oldFile)).states[0].retainedNeighborhood;
    assert.deepEqual(neighborhood.probes,before.probes);
    assert.deepEqual(originalFootprints,before.originalFootprints);
    assert.equal(neighborhood.table,before.table_sha256);
   }
   r.states.push({device,...state,stabilized_ground:samples});save();
   if(!current){
    assert.equal(state.show_history,true);assert.equal(state.selected_name,'建国西路618号住宅挑阳台与窗列');
    await shot('before-same-overview');
   }else{
    const former=JSON.parse(fs.readFileSync(oldFile));assert.ok(former.passed&&former.browser_closed);
    assert.equal(state.unchanged_ground_at_rounded_register_point,former.states[0].unchanged_ground_at_rounded_register_point);
    assert.equal(state.show_history,true);assert.equal(state.walk_disabled,true);assert.equal(state.selected_name,locationName);assert.match(state.location_caption,/1925年建筑原址/);
    await shot(device+'-location');
    await press(page.locator('#history-open')); await page.locator('#history-dialog[open]').waitFor();
    const title=await page.locator('#history-title').innerText();assert.equal(title,locationName+' · 2018—2024年照片');
    const frame=page.frameLocator('#history-frame');await frame.locator('#status').filter({hasText:'近景 ·'}).waitFor({timeout:180000});
    const scope=await frame.locator('.panel > p').first().innerText();assert.match(scope,/三跨玻璃廊上方是宝瓶栏杆/);
    const framePath=await page.locator('#history-frame').getAttribute('src');assert.equal(framePath,archive+'?embed=history');
    await shot(device+'-archive-near');
    const detail=frame.locator('#detail');await detail.selectOption('lod');await frame.locator('#status').filter({hasText:'远景 ·'}).waitFor({timeout:120000});
    await press(frame.locator('[data-view="oblique"]'));await page.waitForTimeout(300);await shot(device+'-archive-lod');
    if(touch)await press(frame.locator('#site-return'));else await press(page.locator('#history-close'));
    await page.waitForFunction(()=>!document.querySelector('#history-dialog').open&&!document.querySelector('#history-frame').hasAttribute('src'),undefined,{timeout:30000});
    assert.ok(page.url().includes('#landmark='+id));assert.equal(await page.locator('#location-name').textContent(),locationName);
    r.states[r.states.length-1].archive={title,scope,framePath,near:true,lod:true,closed:true};save();
    await Promise.all([...pending]);await page.close();await browser.close();
    r.archive_browser_closed=new Date().toISOString();save();
    browser=await launch();page=await openDevice();observe();
    await enterMapLabel(id,'changning-sun-ke-villa',pose.center,touch?'touch':'mouse',r);
    await page.waitForFunction(v=>document.querySelector('#location-name')?.textContent===v&&!window.__SHANGHAI_APP__.scene.map.isMoving()&&!document.querySelector('#history-open')?.hidden,locationName,{timeout:120000});
    await shot(device+'-label-return');
   }
   await Promise.all([...pending]);await page.close();
  }
  for(const f of ['src/app.js','src/map-scene.js','src/candidate-overview-camera.js','src/building-beacons.js','src/building-beacon-groups.js','data/candidate-city-integrations.json',...(current?[archive,'src/historical-view.js','assets/models/candidates/'+id+'/'+id+'-web.glb','assets/models/candidates/'+id+'/'+id+'-lod.glb']:[])])
   assert.ok(r.signed_responses[f],'Missing signed page response: '+f);
  assert.deepEqual(r.page_errors,[]);assert.deepEqual(r.http_errors,[]);assert.deepEqual(r.request_failures,[]);
  r.passed=true;
 }catch(e){r.failure=e.stack;throw e;}finally{await browser.close();r.browser_closed=true;r.closed_at=new Date().toISOString();save();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
