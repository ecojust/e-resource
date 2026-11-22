/** Exercise an archive-only location from the public district directory across its two releases. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');
const [mode,binding,output,oldFile,deviceFilter]=process.argv.slice(2);
assert.ok(['before','after'].includes(mode));
const input=JSON.parse(fs.readFileSync(binding));
const current=mode==='after',n=current?'259':'258',site=input.origins[n];
const id=input.id, prior=input.previous, archive=input.page;
const base=site.url, locationName=input.name;
const pose={center:input.point, zoom:17.4,pitch:60,bearing:35};
const digest=b=>createHash('sha256').update(b).digest('hex');
fs.mkdirSync(output,{recursive:true});
const file=path.join(output,mode+'.json');
const r={mode,base,id,started:new Date().toISOString(),script_sha256:digest(fs.readFileSync(__filename)),
  signed_input_sha256:digest(fs.readFileSync(binding)),catalog:site.catalog_sha256,count:site.count,
  captures:[],signed_responses:{},page_errors:[],request_failures:[],http_errors:[],states:[],passed:false,browser_closed:false};
function save(){fs.writeFileSync(file+'.part',JSON.stringify(r,null,2)+'\n');fs.renameSync(file+'.part',file);}
async function main(){
 const browser=await chromium.launch({headless:false,env:{...process.env,DISPLAY:':53'},executablePath:'/usr/bin/chromium',args:['--disable-translate','--disable-features=Translate,TranslateUI','--lang=zh-CN','--ozone-platform=x11','--window-position=0,0','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disable-background-networking','--disable-component-update','--disable-sync','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--max-old-space-size=300 --max-semi-space-size=4','--disk-cache-size=1048576','--disable-gpu-shader-disk-cache','--force-gpu-mem-available-mb=96','--remote-debugging-port=46359']});
 try{
  for(const [device,width,height,touch] of (current?[['desktop',790,510,false],['mobile',390,540,true]]:[['desktop',440,380,false]])){
   if(deviceFilter && device!==deviceFilter)continue;
   const page=await browser.newPage({viewport:{width,height},hasTouch:touch,locale:'zh-CN',deviceScaleFactor:1});
   const sizing=await page.context().newCDPSession(page);
   const nativeWindow=await sizing.send('Browser.getWindowForTarget');
   await sizing.send('Browser.setWindowBounds',{windowId:nativeWindow.windowId,bounds:{left:0,top:0,width:Math.max(520,width+32),height:height+120}});
   await sizing.detach();
   await page.setContent('<style>body{margin:0;background:rgb(22,17,43)}i,b{position:fixed;display:block;width:9px;height:9px}i{left:0;top:0;background:rgb(207,43,171)}b{right:0;bottom:0;background:rgb(31,211,93)}</style><i></i><b></b>');
   await page.bringToFront();
   const magick={env:{...process.env,DISPLAY:':53',MAGICK_THREAD_LIMIT:'1',OMP_NUM_THREADS:'1'},timeout:12000};
   const probe=path.join(output,'viewport-calibration.png');
   const locate="from PIL import Image; import sys,json; im=Image.open(sys.argv[1]).convert('RGB'); a=im.load(); w,h=map(int,sys.argv[2:4]); print(json.dumps(next(([x,y] for y in range(im.height-h+1) for x in range(im.width-w+1) if a[x,y]==(207,43,171) and a[x+8,y+8]==(207,43,171) and a[x+w-1,y+h-1]==(31,211,93) and a[x+w-9,y+h-9]==(31,211,93)),None)))";
   let rect=null;
   for(let n=0;!rect&&n<15;n++){
    await new Promise(done=>setTimeout(done,120));
    execFileSync('import',['-silent','-display',':53','-window','root',probe],magick);
    rect=JSON.parse(execFileSync('python',['-c',locate,probe,String(width),String(height)],{encoding:'utf8'}));
   }
   assert.ok(rect,'Viewport registration needs both opposite corners');
   r.viewportCalibration={x:rect[0],y:rect[1],width,height,file:path.basename(probe),sha256:digest(fs.readFileSync(probe))};
   let nextTile=0,nextLandmark=0,dialogOpen=false;
   const sleepers=new Set();
   const wakeAll=()=>{for(const wake of sleepers)wake();};
   browser.once('disconnected',wakeAll);page.once('close',wakeAll);
   const delay = ms => new Promise(done=>{const wake=()=>{clearTimeout(t);sleepers.delete(wake);done();};const t=setTimeout(wake,ms);sleepers.add(wake);});
   r.realGlbTransfers=[];
   await page.route(/\/assets\/(?:city-detail|models)\/[^?#]+\.glb(?:\.gz)?(?:[?#]|$)/i,async route=>{
     const url=new URL(route.request().url()),queued=Date.now();let earliest=queued;
     const archiveAsset=url.pathname.includes('/'+id+'/');
     if(current&&url.pathname.includes('/far.glb')){earliest=Math.max(queued+7000,nextTile);nextTile=earliest+2600;}
     else if(url.pathname.includes('/near/')){earliest=Math.max(queued+26000,nextTile);nextTile=earliest+9500;}
     else if(url.pathname.includes('/assets/models/')&&!archiveAsset){earliest=Math.max(queued+(current?42000:4000),nextLandmark);nextLandmark=earliest+12000;}
     if(earliest>queued)await delay(earliest-queued);
     while(dialogOpen&&!archiveAsset&&browser.isConnected()&&!page.isClosed())await delay(1000);
     if(!browser.isConnected()||page.isClosed())return;
     try{await route.continue();r.realGlbTransfers.push({path:url.pathname,queued,continued:Date.now()});}
     catch(error){if(browser.isConnected()&&!page.isClosed()&&!String(error).includes('Invalid InterceptionId'))r.transferErrors??=[];if(r.transferErrors)r.transferErrors.push(String(error));}
   });
   const hostReportedMemory=await page.evaluate(()=>navigator.deviceMemory??null);
   await page.addInitScript(()=>{
     Object.defineProperty(navigator,'deviceMemory',{value:4,configurable:true});
     let api;
     Object.defineProperty(window,'maplibregl',{configurable:true,get(){return api},set(v){api=v;if(typeof v?.setWorkerCount==='function')v.setWorkerCount(1)}});
   });
   r.browser_profile={host_reported_memory_gib:hostReportedMemory,device_memory_gib:4,workers:1,backing_ratio:0.5};
   await page.addInitScript(()=>{
     if(!location.pathname.endsWith('landmarks.html'))return;
     document.addEventListener('pointerup',event=>{
       const card=event.target.closest('[data-landmark]');
       if(card)sessionStorage.setItem('observedDirectoryPointer',JSON.stringify({id:card.dataset.landmark,type:event.pointerType,trusted:event.isTrusted}));
     },true);
   });
   const pending=new Set();
   const webModelRequests=[];
   page.on('request',req=>{const name=new URL(req.url()).pathname;if(name.includes('/'+id+'/')&&name.endsWith('.glb'))webModelRequests.push(name);});
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
    await page.waitForFunction(()=>{
     const cover=document.querySelector('#loading');
     return cover && (getComputedStyle(cover).display==='none'||Number(getComputedStyle(cover).opacity)<.015)
       && !window.__SHANGHAI_APP__.scene.map.isMoving();
   },null,{timeout:180000});
   await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
   const rootFile=path.join(output,name+'-x11-root.png'), view=path.join(output,name+'.png');
   execFileSync('import',['-silent','-display',':53','-window','root',rootFile],magick);
   execFileSync('convert',[rootFile,'-crop',`${width}x${height}+${rect[0]}+${rect[1]}`,'+repage',view],magick);
   const b=fs.readFileSync(view); (r.displayCaptures??=[]).push({file:name+'.png',root:path.basename(rootFile),root_sha256:digest(fs.readFileSync(rootFile)),sha256:digest(b),rect:[...rect,width,height]});
    const gl=await page.evaluate(()=>{const m=window.__SHANGHAI_APP__.scene.map;const gl=m.getCanvas().getContext('webgl2');return {lost:gl.isContextLost(),error:gl.getError(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()};});
    assert.equal(gl.lost,false);assert.equal(gl.error,0);
    r.captures.push({device,viewport:[width,height],file:name+'.png',sha256:digest(b),bytes:b.length,gl});save();
   };
   await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded',timeout:180000});
   const all=page.locator('.landmark-card[data-landmark]');await all.first().waitFor({timeout:120000});assert.equal(await all.count(),site.count);
   const directoryIds=await all.evaluateAll(cards=>cards.map(card=>card.dataset.landmark));
   assert.equal(new Set(directoryIds).size,directoryIds.length);
   if(current){
    const before=JSON.parse(fs.readFileSync(oldFile));
    assert.deepEqual(directoryIds.filter(entry=>entry!==id),before.directory_ids);
   }
   r.directory_ids=directoryIds;
   const selected=current?id:prior;
   assert.equal(await page.locator(`.landmark-card[data-landmark="${id}"]`).count(),current?1:0);
   const anchor=page.locator(`.landmark-card[data-landmark="${selected}"] .card-foot a[href="index.html#landmark=${selected}&mode=overview"]`);
   await press(anchor);
   await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene?.getCandidateIntegrationState,undefined,{timeout:200000});
   await page.evaluate(()=>{const scene=window.__SHANGHAI_APP__.scene;scene.setVisualQuality({shadows:false,surfaceNormals:true});scene.map.setPixelRatio(.5);});
   await page.waitForFunction(s=>location.hash.includes(s)&&!window.__SHANGHAI_APP__.scene.map.isMoving(),selected,{timeout:160000});
   const inputEvent=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('observedDirectoryPointer')));
   assert.equal(inputEvent.id,selected);assert.equal(inputEvent.trusted,true);assert.equal(inputEvent.type,touch?'touch':'mouse');
   (r.trusted_inputs??=[]).push(inputEvent);
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
    return {center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),mode:app.mode,selected_name:document.querySelector('#location-name').textContent,
      location_caption:document.querySelector('#location-district').textContent,show_history:!document.querySelector('#history-open').hidden,
      walk_disabled:document.querySelector('#start-walk').disabled,current_triangles:st.triangles,current_visible:st.visible,
      selected_source_cut:ci.clips.some(x=>x.id===id),selected_display_cut:ci.displayClips.some(x=>x.id===id),
      selected_current_entry:ci.active.some(x=>x.id===id),ground_at_street_reference_point:s.collisionAt(...pose.center),
      neighborhood_ground_samples:[[0,0],[.00008,0],[-.00008,0],[0,.00006],[0,-.00006]].map(([x,y])=>s.collisionAt(pose.center[0]+x,pose.center[1]+y))};
   },{id,pose});
   assert.equal(state.current_triangles,0);assert.equal(state.current_visible,false);
   assert.equal(state.selected_source_cut,false);assert.equal(state.selected_display_cut,false);assert.equal(state.selected_current_entry,false);
   assert.ok(Math.abs(state.bearing-pose.bearing)<.025 && Math.abs(state.pitch-pose.pitch)<.025);
   assert.ok(Math.abs(state.zoom-pose.zoom)<.025&&state.center.every((v,k)=>Math.abs(v-pose.center[k])<.000003));
   r.states.push({device,...state,stabilized_ground:samples});save();
   if(!current){
    assert.equal(state.show_history,true);assert.equal(state.walk_disabled,true);assert.notEqual(state.selected_name,locationName);
    await shot('before-same-overview');
   }else{
    const former=JSON.parse(fs.readFileSync(oldFile));assert.ok(former.passed&&former.browser_closed);
    assert.equal(state.ground_at_street_reference_point,former.states[0].ground_at_street_reference_point);
    assert.deepEqual(state.neighborhood_ground_samples,former.states[0].neighborhood_ground_samples);
    assert.equal(state.show_history,true);assert.equal(state.walk_disabled,true);assert.equal(state.selected_name,locationName);assert.equal(state.location_caption,'黄浦区 · 1930年建筑原址');
    assert.deepEqual(webModelRequests,[],'The historical facade must only load on demand');
    await shot(device+'-location');
    dialogOpen=true;
    const actualButton=page.locator('#history-open');
    await actualButton.scrollIntoViewIfNeeded();
    const unobstructed=await page.waitForFunction(()=>{
      const button=document.querySelector('#history-open');
      const box=button.getBoundingClientRect();
      for(const dy of [.5,.3,.7])for(const dx of [.5,.25,.75,.1,.9]){
        const x=Math.round(box.width*dx),y=Math.round(box.height*dy);
        const hit=document.elementFromPoint(box.left+x,box.top+y);
        if(hit&&button.contains(hit))return {x,y,clientX:box.left+x,clientY:box.top+y};
      }
      return false;
    },undefined,{timeout:30000});
    const where=await unobstructed.jsonValue();const position={x:where.x,y:where.y};
    await actualButton.evaluate(el=>el.addEventListener('pointerup',event=>{
      window.historicalButtonPointer={clientX:event.clientX,clientY:event.clientY,trusted:event.isTrusted,type:event.pointerType,target:event.target.id};
    },{once:true}));
    if(touch)await actualButton.tap({position});else await actualButton.click({position});
    r.history_open_pointer=await page.evaluate(()=>window.historicalButtonPointer);
    assert.ok(r.history_open_pointer.trusted&&r.history_open_pointer.target==='history-open');
    assert.equal(r.history_open_pointer.type,touch?'touch':'mouse'); await page.locator('#history-dialog[open]').waitFor();
    const title=await page.locator('#history-title').innerText();assert.equal(title,locationName+' · 2014年照片');
    const frame=page.frameLocator('#history-frame');await frame.locator('#status').filter({hasText:'近景 ·'}).waitFor({timeout:180000});
    const scope=await frame.locator('.panel p').filter({hasText:'民国照片与2014年11月23日的正面照'}).innerText();assert.match(scope,/五个开间、两层通高的柱列和山花圆窗/);
    const framePath=await page.locator('#history-frame').getAttribute('src');assert.equal(framePath,archive+'?embed=history');
    assert.match(await frame.locator('#status').innerText(),/15,656/);
    const front=frame.locator('[data-view="front"]');assert.equal(await front.textContent(),'正看山花五窗');await press(front);
    const frames=()=>frame.locator('canvas').evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(done)))));
    await frames();await shot(device+'-archive-near');
    const sides=frame.locator('[data-view="oblique"]');
    assert.equal(await sides.textContent(),'斜看柱头与窗列');await press(sides);
    await frames();await shot(device+'-capitals-and-window-bays');
    assert.equal(await frame.locator('[data-view="above"]').textContent(),'俯看圆窗石键');await press(frame.locator('[data-view="above"]'));await frames();
    await shot(device+'-oculus-keystone');
    const area=await frame.locator('#model-view canvas').boundingBox();
    const bounds=[Math.max(0,Math.ceil(area.x)),Math.max(0,Math.ceil(area.y)),
       Math.min(width,Math.floor(area.x+area.width)),Math.min(height,Math.floor(area.y+area.height))];
    const names=['archive-near','capitals-and-window-bays','oculus-keystone'].map(name=>path.join(output,device+'-'+name+'.png'));
    const change="from PIL import Image; import json,sys; import numpy as np; box=tuple(map(int,sys.argv[4:])); a=[np.asarray(Image.open(f).convert('RGB').crop(box)) for f in sys.argv[1:4]]; print(json.dumps([int((a[i]!=a[j]).any(2).sum()) for i,j in [(0,1),(0,2),(1,2)]]))";
    const changes=JSON.parse(execFileSync('python',['-c',change,...names,...bounds.map(String)],{encoding:'utf8',env:{...process.env,OPENBLAS_NUM_THREADS:'1'}}));
    assert.ok(changes.every(n=>n>1000),'Original independent archival views must produce distinct canvas pixels');
    r.archiveCameraComparison={counts:changes,rect_xyxy:bounds,views:['front','oblique','above']};save();
    const detail=frame.locator('#detail');await detail.selectOption('lod');await frame.locator('#status').filter({hasText:'远景 ·'}).waitFor({timeout:120000});
    await press(frame.locator('[data-view="oblique"]'));await page.waitForTimeout(300);assert.match(await frame.locator('#status').innerText(),/10,452/);await shot(device+'-archive-lod');
    if(!touch){
     const links=frame.locator('#downloads a');
     assert.equal(await links.count(),4);
     r.saved_downloads=[];
     for(let i=0;i<4;i++){
      const link=links.nth(i);
      const href=await link.getAttribute('href');
      const url=new URL(href,new URL(archive,base));const relative=url.pathname.slice(1);
      assert.equal(url.origin,new URL(base).origin);assert.ok(site.files[relative],relative);
      const event=page.waitForEvent('download');
      await press(link);
      const downloaded=await event;
      assert.equal(downloaded.suggestedFilename(),path.basename(relative));
      const bytes=fs.readFileSync(await downloaded.path());
      assert.equal(bytes.length,site.files[relative].bytes);
      assert.equal(digest(bytes),site.files[relative].sha256);
      const filename=path.basename(relative),directory=path.join(output,'saved');
      fs.mkdirSync(directory,{recursive:true});
      const saved=path.join(directory,filename);assert.ok(!fs.existsSync(saved));
      await downloaded.saveAs(saved);
      const retained=fs.readFileSync(saved);assert.equal(digest(retained),digest(bytes));assert.equal(retained.length,bytes.length);
      r.saved_downloads.push({file:relative,bytes:retained.length,sha256:digest(retained),download_event:true,temporary_file_read:true,saved:'saved/'+filename,saveAsVerified:true});
      await downloaded.delete();
     }
     assert.equal(new Set(r.saved_downloads.map(item=>item.file)).size,4);
     save();
    }
    if(touch)await press(frame.locator('#site-return'));else await press(page.locator('#history-close'));
    await page.waitForFunction(()=>!document.querySelector('#history-dialog').open&&!document.querySelector('#history-frame').hasAttribute('src'),undefined,{timeout:30000});
    dialogOpen=false;assert.ok(page.url().includes('#landmark='+id));assert.equal(await page.locator('#location-name').textContent(),locationName);
    assert.ok(await page.locator('#history-open').evaluate(el=>el===document.activeElement));
    assert.ok(webModelRequests.some(url=>url.endsWith('-web.glb'))&&webModelRequests.some(url=>url.endsWith('-lod.glb')));
    r.states[r.states.length-1].archive={title,scope,framePath,near:true,lod:true,closed:true,model_requests:webModelRequests,focus_restored:true};save();
   }
   await Promise.all([...pending]);await page.close();
  }
  for(const f of ['src/app.js','src/map-scene.js','data/candidate-city-integrations.json',...(current?[archive,'src/historical-view.js','assets/models/candidates/'+id+'/'+id+'-web.glb','assets/models/candidates/'+id+'/'+id+'-lod.glb']:[])])
   assert.ok(r.signed_responses[f],'Missing signed page response: '+f);
  assert.deepEqual(r.page_errors,[]);assert.deepEqual(r.http_errors,[]);assert.deepEqual(r.request_failures,[]);
  r.passed=true;r.completed=true;r.section=mode==='before'?'before':deviceFilter==='mobile'?'phone':'desktop';
 }catch(e){r.failure=e.stack;throw e;}finally{await browser.close();r.browser_closed=true;r.closed_at=new Date().toISOString();save();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
