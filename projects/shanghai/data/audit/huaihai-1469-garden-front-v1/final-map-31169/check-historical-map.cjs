/** Exercise an archive-only location from the public district directory across its two releases. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const assert=require('node:assert/strict');
const [mode,binding,output,oldFile]=process.argv.slice(2);
assert.ok(['before','after'].includes(mode));
const input=JSON.parse(fs.readFileSync(binding));
const current=mode==='after',n=current?'169':'168',site=input.origins[n];
const id=input.id, prior=input.previous, archive='huaihai-1469-garden-front-history.html';
const base=site.url, locationName='淮海中路1469号历史花园立面';
const pose={center:[121.443,31.21], zoom:17.4,pitch:60,bearing:35};
const digest=b=>createHash('sha256').update(b).digest('hex');
fs.mkdirSync(output,{recursive:true});
const file=path.join(output,mode+'.json');
const r={mode,base,id,started:new Date().toISOString(),script_sha256:digest(fs.readFileSync(__filename)),
  signed_input_sha256:digest(fs.readFileSync(binding)),catalog:site.catalog_sha256,count:site.count,
  captures:[],signed_responses:{},page_errors:[],request_failures:[],http_errors:[],states:[],passed:false,browser_closed:false};
function save(){fs.writeFileSync(file+'.part',JSON.stringify(r,null,2)+'\n');fs.renameSync(file+'.part',file);}
async function main(){
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9869']});
 try{
  const devices=current?[['desktop',930,695,false],['mobile',390,844,true]]:[['desktop',930,695,false]];
  const selectedDevices=process.env.CHECK_DEVICE ? devices.filter(v=>v[0]===process.env.CHECK_DEVICE) : devices;
  assert.ok(selectedDevices.length>0);
  for(const [device,width,height,touch] of selectedDevices){
   const page=await browser.newPage({viewport:{width,height},hasTouch:touch});
   const pending=new Set();
   page.on('pageerror',e=>r.page_errors.push(e.message));
   page.on('requestfailed',request=>{if(request.failure()?.errorText==='net::ERR_ABORTED'){r.canceled_requests??=[];r.canceled_requests.push(request.url());}else r.request_failures.push({url:request.url(),reason:request.failure()});});
   page.on('response',res=>{
    const u=new URL(res.url());if(u.origin!==new URL(base).origin)return;
    if(res.status()>=400)r.http_errors.push({url:res.url(),status:res.status()});
    const name=u.pathname.slice(1);if(!site.files[name]||res.status()!==200)return;
    let timer;
    const timeout=new Promise((resolve,reject)=>{timer=setTimeout(()=>reject(new Error('Response body did not complete in 60 seconds')),60000);});
    const promise=Promise.race([res.body(),timeout]).finally(()=>clearTimeout(timer)).then(b=>{const h=digest(b);assert.equal(h,site.files[name].sha256,name);r.signed_responses[name]=h;})
      .catch(e=>{r.unread_bodies??=[];r.unread_bodies.push([name,e.message]);});
    pending.add(promise);promise.finally(()=>pending.delete(promise));
   });
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
   r.states.push({device,...state,stabilized_ground:samples});save();
   if(!current){
    assert.equal(state.show_history,false);
    await shot('before-same-overview');
   }else{
    const former=JSON.parse(fs.readFileSync(oldFile));assert.ok(former.passed&&former.browser_closed);
    assert.equal(state.unchanged_ground_at_rounded_register_point,former.states[0].unchanged_ground_at_rounded_register_point);
    assert.equal(state.show_history,true);assert.equal(state.walk_disabled,true);assert.equal(state.selected_name,locationName);assert.match(state.location_caption,/1921年建筑原址/);
    await shot(device+'-location');
    await press(page.locator('#history-open')); await page.locator('#history-dialog[open]').waitFor();
    const title=await page.locator('#history-title').innerText();assert.equal(title,locationName+' · 影像资料年份 2010—2011');
    const frame=page.frameLocator('#history-frame');await frame.locator('#status').filter({hasText:'近景 ·'}).waitFor({timeout:180000});
    const scope=await frame.locator('.scope').innerText();assert.match(scope,/摄影日期未详/);
    const framePath=await page.locator('#history-frame').getAttribute('src');assert.equal(framePath,archive+'?embed=history');
    await shot(device+'-archive-near');
    const detail=frame.locator('#detail');await detail.selectOption('lod');await frame.locator('#status').filter({hasText:'远景 ·'}).waitFor({timeout:120000});
    await press(frame.locator('[data-view="oblique"]'));await page.waitForTimeout(300);await shot(device+'-archive-lod');
    if(touch)await press(frame.locator('#site-return'));else await press(page.locator('#history-close'));
    await page.waitForFunction(()=>!document.querySelector('#history-dialog').open&&!document.querySelector('#history-frame').hasAttribute('src'),undefined,{timeout:30000});
    assert.ok(page.url().includes('#landmark='+id));assert.equal(await page.locator('#location-name').textContent(),locationName);
    r.states[r.states.length-1].archive={title,scope,framePath,near:true,lod:true,closed:true};save();
   }
   await Promise.all([...pending]);await page.close();
  }
  for(const f of ['src/app.js','src/map-scene.js','data/candidate-city-integrations.json',...(current?[archive,'src/historical-view.js','assets/models/candidates/'+id+'/'+id+'-web.glb','assets/models/candidates/'+id+'/'+id+'-lod.glb']:[])])
   assert.ok(r.signed_responses[f],'Missing signed page response: '+f);
  assert.deepEqual(r.page_errors,[]);assert.deepEqual(r.http_errors,[]);assert.deepEqual(r.request_failures,[]);
  r.passed=true;
 }catch(e){r.failure=e.stack;throw e;}finally{await browser.close();r.browser_closed=true;r.closed_at=new Date().toISOString();save();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
