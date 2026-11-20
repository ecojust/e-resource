/** Exercise the normal map for a detail added where the source city has no building. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');

const [caseFile, mode, site, snapshotFile, output, beforeReceipt] = process.argv.slice(2);
if (!caseFile || !['before','after','inputs-before','inputs-after'].includes(mode) || !site || !snapshotFile || !output) {
  throw Error('Usage: node check-independent-city.cjs CASE before|after|inputs-before|inputs-after SERVED_URL SIGNED_SNAPSHOT NEW_OUTPUT [BEFORE_JSON]');
}
const current = mode.endsWith('after');
const audit = path.dirname(path.resolve(caseFile));
const project = path.resolve(audit, '../../..');
const read = file => JSON.parse(fs.readFileSync(file));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const fileDigest = file => digest(fs.readFileSync(file));
const spec = read(caseFile), id = spec.id;
const contract = read(path.join(audit, 'final-placement-contract.json'));
const review = read(path.join(project, 'source/precise', id, 'footprint-review.json'));
const groundFile = path.join(audit, spec.groundEvidence);
const evidence = read(groundFile), probes = Array.isArray(evidence) ? evidence : evidence.ground_probes;
const signed = read(snapshotFile), base = new URL(site);
const catalogName = 'data/candidate-city-integrations.json';
const asURL = file => new URL(file, base).href;
const reportFile = path.join(output, mode+'.json');
const report = {id, mode, site:base.href, started:new Date().toISOString(), completed:false,
  scriptSha256:fileDigest(__filename), caseSha256:fileDigest(caseFile), contractSha256:fileDigest(path.join(audit,'final-placement-contract.json')),
  groundSha256:fileDigest(groundFile), snapshotSha256:fileDigest(snapshotFile), files:[], actions:[], views:[], ground:[], sources:[], pageErrors:[], failedRequests:[], httpErrors:[]};
const save = () => {fs.writeFileSync(reportFile+'.part', JSON.stringify(report,null,2)+'\n');fs.renameSync(reportFile+'.part',reportFile);};
const localGeometry = (x,y) => {
  const rad=Math.PI/180, h=contract.heading*rad, k=6371008.8*Math.cos(contract.lat*rad);
  const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
  return [contract.lng+east/k/rad,Math.atan(Math.sinh(Math.asinh(Math.tan(contract.lat*rad))+north/k))/rad];
};
const owners = spec.neighbors.map(n => {
  const row=review.owners.find(o=>o.local_id===n.localId);
  assert.ok(row, 'Unknown source '+n.localId);
  return {id:n.localId, key:row.key, point:n.point};
});
const groups=review.near_tiles.filter(g=>owners.some(o=>g.feature_local_ids.includes(o.id)));
assert.ok(groups.length && owners.length && probes.length);
assert.equal(id,contract.id);assert.equal(contract.replacement_geometry,null);
assert.deepEqual(contract.source_feature_ids,{building:[],building_part:[]});
for (const k of ['owner','owners','site_replacement','source_section_caps','display_height_clips']) assert.ok(!contract[k], k);

async function get(file, expected=signed.files[file]) {
  assert.match(expected||'', /^[0-9a-f]{64}$/, 'Missing digest '+file);
  const r=await fetch(asURL(file),{signal:AbortSignal.timeout(180000)});assert.equal(r.status,200,file);
  const b=Buffer.from(await r.arrayBuffer());assert.equal(digest(b),expected,file);
  report.files.push({file,url:r.url,sha256:expected,bytes:b.length});return b;
}
async function run() {
  fs.mkdirSync(output,{recursive:true});assert.ok(!fs.existsSync(reportFile),'Choose an unused output directory');save();
  let browser;
  try {
    const catalog=JSON.parse(await get(catalogName));const row=catalog.models.find(r=>r.id===id);
    report.catalog={count:catalog.resulting_city_count,sha256:signed.files[catalogName]};
    if(signed.resulting_count!=null)assert.equal(catalog.resulting_city_count,signed.resulting_count);
    assert.equal(catalog.resulting_city_count,spec.deliveredCount-(current?0:1),'Expected this release stage');
    assert.equal(catalog.models.at(current?-2:-1).id,spec.predecessorId,'Wrong prior building');
    if(mode==='after'){
      assert.ok(beforeReceipt,'Use the before.json from the completed predecessor run');
      const before=read(beforeReceipt);
      assert.ok(before.completed&&before.browserClosed&&before.mode==='before'&&before.id===id);
      assert.equal(before.catalog.sha256,signed.previous_catalog_sha256,'The new stage must inherit the measured previous map');
      assert.equal(before.catalog.count+1,catalog.resulting_city_count);
      report.beforeReceipt={sha256:fileDigest(beforeReceipt),catalog:before.catalog};
    }
    assert.equal(Boolean(row),current);
    if(current){assert.equal(catalog.models.at(-1).id,id);for(const k of ['collision_geometry','replacement_geometry','source_feature_ids','model_geometry_sha256'])assert.deepEqual(row[k],contract[k],k);for(const k of ['owner','owners','site_replacement','source_section_caps','display_height_clips'])assert.ok(!row[k],k);}
    const previous=catalog.models.at(current?-2:-1).id;
    const manifest=row&&JSON.parse(await get(row.candidate_manifest));
    const paths=new Map();
    if(row)for(const [role,item] of Object.entries(manifest.assets)){
      const file=path.posix.join(path.posix.dirname(row.candidate_manifest),item.file);assert.equal(signed.files[file],item.sha256,role);
      paths.set(role,{file,...item,filePath:file});
    }
    const ordinary=JSON.parse(await get('data/precise-buildings-v6.json'));
    const repacked=ordinary.macros.find(m=>m.id===review.frozen_macro);
    const bound=rec=>({file:rec.repository_path.replace(/^projects\/shanghai\//,''),sha256:rec.sha256,bytes:rec.bytes});
    const far=bound(review.frozen_bindings.find(f=>f.repository_path.endsWith('/far.glb')));
    const near=groups.map(g=>{
      const original=bound(review.frozen_bindings.find(f=>f.repository_path.endsWith('/'+g.file)));
      const replacement=repacked?.near.find(n=>n.id===g.id);
      if(!replacement)return {...original,group:g.id,owners:g.feature_local_ids};
      assert.equal(original.sha256,replacement.baseline_sha256);assert.deepEqual(replacement.featureLocalIds,g.feature_local_ids);
      return {file:replacement.model.file,sha256:replacement.model.sha256,bytes:replacement.model.size_bytes,group:g.id,owners:g.feature_local_ids,baseline:original};
    });
    const runtime=['index.html','landmarks.html','src/app.js','src/map-scene.js','src/candidate-city-clipping.js','src/building-beacons.js','src/building-beacon-groups.js'];
    for(const name of runtime)await get(name);
    for(const n of [far,...near])assert.equal((await get(n.file,n.sha256)).length,n.bytes,n.file);
    if(current)for(const [role,a] of paths)assert.equal((await get(a.filePath,a.sha256)).length,a.bytes,role);
    report.nativeInputs={far,near};report.modelInputs=Object.fromEntries(paths);save();
    if(mode.startsWith('inputs-')){report.completed=true;return;}
    const {chromium}=require('playwright');
    browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});report.browser=browser.version();
    const page=await browser.newPage({viewport:{width:960,height:700},hasTouch:true,ignoreHTTPSErrors:true});page.setDefaultTimeout(180000);
    const expected=new Map([[catalogName,signed.files[catalogName]],...runtime.map(f=>[f,signed.files[f]]),...[far,...near].map(n=>[n.file,n.sha256]),...[...paths.values()].map(a=>[a.filePath,a.sha256])]);
    const received=new Map(),pending=new Set(),unread=new Map();
    page.on('pageerror',e=>report.pageErrors.push(e.message));
    page.on('requestfailed',r=>report.failedRequests.push({url:r.url(),reason:r.failure()?.errorText}));
    page.on('response',r=>{
      const u=new URL(r.url());if(u.origin===base.origin&&r.status()>=400){report.httpErrors.push({url:u.href,status:r.status()});save();}if(u.origin!==base.origin||r.status()!==200)return;
      const f=decodeURIComponent(u.pathname).slice(base.pathname.length);if(!expected.has(f))return;
      const task=r.body().then(b=>{const value=digest(b);assert.equal(value,expected.get(f),f);received.set(f,{sha256:value,bytes:b.length,url:u.href});}).catch(e=>unread.set(f,String(e)));
      pending.add(task);task.finally(()=>pending.delete(task));
    });
    const wait=(fn,args)=>page.waitForFunction(fn,args,{polling:400,timeout:300000});
    async function stable(){
      await wait(()=>{const app=window.__SHANGHAI_APP__,l=document.getElementById('loading');if(!app?.scene||!l)return false;const css=getComputedStyle(l);return !app.scene.map.isMoving()&&l.classList.contains('loaded')&&css.visibility==='hidden'&&css.opacity==='0'&&css.pointerEvents==='none';});
      await page.evaluate(()=>new Promise(done=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>done());m.triggerRepaint();}));
    }
    async function jump(camera){await page.evaluate(c=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;m.setCenterClampedToGround(false);m.jumpTo(c);s.refreshBuildingBeacons();s.loadLandmarks();},camera);await stable();}
    const front={center:localGeometry(...spec.front.center),elevation:spec.front.elevation,zoom:spec.front.zoom,bearing:contract.heading+spec.front.bearingOffset,pitch:spec.front.pitch,padding:{left:0,right:0,top:0,bottom:0}};
    async function variant(v){await wait(({id,v})=>{const a=window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id);return a?.visible&&a.status==='loaded'&&a.variant===v;},{id,v});await stable();}
    async function shot(name,variantName){
      const state=await page.evaluate(id=>{const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map,gl=m.painter.context.gl;return {name:document.querySelector('#location-name')?.textContent,route:location.hash,viewport:[innerWidth,innerHeight],mode:app.mode,asset:s.getLandmarkAssetState(id),camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),elevation:m.getCenterElevation()},lost:gl.isContextLost(),glError:gl.getError()};},id);
      assert.equal(state.lost,false);assert.equal(state.glError,0);
      if(variantName){const item=paths.get(variantName==='full'?'full':'lod');assert.equal(state.asset.triangles,item.triangles);assert.equal(state.asset.variant,variantName);assert.equal(state.asset.verifiedAsset.sha256,item.sha256);assert.ok(state.route.includes('landmark='+id));}
      else{assert.equal(state.asset.anchor,null);assert.equal(state.asset.visible,false);}
      if(variantName){
        const samples=[['西侧小拱通道',-2.76,.1,1.5],['主门黑铁扇',-.75,.25,1.45],
          ['主拱筒瓦',0,0,4.33],['竖题名',2.005,-.03,2.316],['绿色弄牌',2.002,-.041,2.724],
          ['东墙中间通孔',3.74,.02,2.12]].map(([feature,x,y,z])=>({feature,lngLat:localGeometry(x,y),z}));
        state.projections=await page.evaluate(samples=>{
          const s=window.__SHANGHAI_APP__.scene,m=s.map,labels=s.getBuildingBeaconState().labelPositions;
          const hud=['#explore-panel','#location-card','#building-beacon-legend','.topbar','.map-tools'].map(selector=>{
            const e=document.querySelector(selector);if(!e||!e.getClientRects().length)return null;
            const r=e.getBoundingClientRect();return {selector,left:r.left,top:r.top,right:r.right,bottom:r.bottom};
          }).filter(Boolean);
          return samples.map(p=>{
            const altitude=()=>p.z,xy=m.transform.locationToScreenPoint({lng:p.lngLat[0],lat:p.lngLat[1]},
              {getElevationForLngLat:altitude,getElevationForLngLatZoom:altitude});
            const x=xy.x,y=xy.y;
            return {...p,x,y,inViewport:x>=0&&y>=0&&x<innerWidth&&y<innerHeight,
              labels:labels.filter(b=>Math.abs(x-b.x)<=b.width/2&&Math.abs(y-b.y)<=b.height/2).map(b=>b.id),
              hud:hud.filter(b=>x>=b.left&&x<=b.right&&y>=b.top&&y<=b.bottom).map(b=>b.selector)};
          });
        },samples);
      }
      const file=name+'.png';const img=await page.screenshot({path:path.join(output,file),timeout:200000});report.views.push({name,file,sha256:digest(img),...state});save();
    }
    async function searchWithKeyboard(text,target){
      await page.keyboard.press('/');
      const input=page.locator('#place-search');
      assert.equal(await input.evaluate(el=>el===document.activeElement),true);
      await input.fill(text);
      const button=page.locator('#place-list [data-place="'+target+'"]');
      assert.equal(await button.count(),1);
      let tabs=0;
      while(tabs<16 && !await button.evaluate(el=>el===document.activeElement)){
        await page.keyboard.press('Tab');tabs++;
      }
      assert.equal(await button.evaluate(el=>el===document.activeElement),true);
      await button.evaluate(el=>el.addEventListener('click',e=>{window.__yiyuanKeyboard={id:el.dataset.place,trusted:e.isTrusted,detail:e.detail};},{once:true}));
      await page.keyboard.press('Enter');
      const observed=await page.evaluate(()=>window.__yiyuanKeyboard);
      assert.deepEqual(observed,{id:target,trusted:true,detail:0});
      await wait(key=>new URLSearchParams(location.hash.slice(1)).get('landmark')===key,target);
      report.keyboardSearch??=[];report.keyboardSearch.push({text,target,tabs,...observed});save();
    }
    async function selectByLabel(mobile){
      await page.goto(asURL('index.html#landmark='+previous+'&mode=overview'),{waitUntil:'domcontentloaded'});await stable();
      await jump({...front,center:[contract.lng,contract.lat],elevation:0,pitch:0,bearing:0,zoom:16.4});
      await wait(id=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState();const target=b.labelPositions.find(p=>p.id===id||p.memberIds?.includes(id));return target&&s.pickBuildingBeacon(target)===target.id;},id);
      const click=await page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState(),p=b.labelPositions.find(v=>v.id===id||v.memberIds?.includes(id));const box=s.map.getCanvas().getBoundingClientRect();return {x:box.x+p.x,y:box.y+p.y,label:p.id,group:Boolean(p.memberIds),number:p.number,memberIds:p.memberIds,mode:b.labelMode,route:location.hash};},id);
      assert.ok(!click.route.includes('landmark='+id));
      await page.evaluate(() => {
        window.__yiyuanPointer = new Promise(resolve => {
          window.addEventListener('pointerup', event => {
            const scene=window.__SHANGHAI_APP__.scene,canvas=scene.map.getCanvas();
            const rect=canvas.getBoundingClientRect();
            resolve({trusted:event.isTrusted,type:event.pointerType,canvas:event.target===canvas,
              x:event.clientX,y:event.clientY,label:scene.pickBuildingBeacon({x:event.clientX-rect.left,y:event.clientY-rect.top})});
          },{capture:true,once:true});
        });
      });
      if(mobile)await page.touchscreen.tap(click.x,click.y);else await page.mouse.click(click.x,click.y);
      const pointer=await page.evaluate(()=>window.__yiyuanPointer);
      assert.equal(pointer.type,mobile?'touch':'mouse');
      assert.ok(pointer.trusted&&pointer.canvas);
      assert.equal(pointer.label,click.label);
      if(click.group){const option=page.locator('dialog.beacon-group-picker[open] [data-landmark="'+id+'"]');if(mobile)await option.tap();else await option.click();}
      await wait(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,id);report.actions.push({device:mobile?'phone':'desktop',input:mobile?'touch':'mouse',pointer,...click,selected:id});save();await variant('full');
    }
    if(current){
      await selectByLabel(false);await shot('map-desktop','full');
      await page.goto('about:blank');await page.setViewportSize({width:390,height:844});await selectByLabel(true);await shot('map-mobile','full');
      const toggle=page.locator('#panel-toggle');if(await toggle.getAttribute('aria-expanded')==='true')await toggle.tap();
      await jump(front);await variant('full');await shot('map-mobile-same-camera','full');
      await page.goto(asURL('landmarks.html'),{waitUntil:'domcontentloaded'});
      await page.setViewportSize({width:960,height:700});
      await page.locator('.landmark-card[data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').click();
      await variant('full');
    }else{await page.goto(asURL('index.html#landmark='+previous+'&mode=overview'),{waitUntil:'domcontentloaded'});await stable();}
    const panel=page.locator('#panel-toggle');if(await panel.getAttribute('aria-expanded')==='true')await panel.click();
    await jump(front);if(current)await variant('full');
    const closest=owners.reduce((a,b)=>Math.hypot(a.point[0]-contract.lng,a.point[1]-contract.lat)<Math.hypot(b.point[0]-contract.lng,b.point[1]-contract.lat)?a:b);
    const nearestGroup=near.find(g=>g.owners.includes(closest.id));
    await wait(g=>window.__SHANGHAI_APP__.scene.getStreamingState().detail.active.some(t=>t.id===g),review.frozen_macro+'/'+nearestGroup.group);
    await stable();await shot(current?'map-front':'before-front',current?'full':null);
    if(current){
      await jump({...front,zoom:21.05,pitch:54,elevation:3.15});
      await variant('full');await shot('map-name-tablet-and-side-passage','full');
      await searchWithKeyboard('中南新邨',previous);await stable();
      await searchWithKeyboard('懿园',id);await variant('full');await shot('map-returned','full');
    }
    for(const group of near){
      const member=owners.find(o=>group.owners.includes(o.id));const camera={...front,center:member.point,zoom:19.1,pitch:25,elevation:0};await jump(camera);
      const groupId=review.frozen_macro+'/'+group.group;
      await wait(g=>window.__SHANGHAI_APP__.scene.getStreamingState().detail.active.some(x=>x.id===g),groupId);
      const includes=owners.filter(o=>group.owners.includes(o.id));
      const state=await page.evaluate(({g,id,owners})=>{const s=window.__SHANGHAI_APP__.scene,ci=s.getCandidateIntegrationState();return {group:ci.shader.ownerScopedSources.find(x=>x.id===g),registeredClip:ci.clips.find(x=>x.id===id)||null,section:ci.sourceSections?.filter(x=>x.id===id)||[],owners:owners.map(o=>({id:o.id,feature:s.map.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:o.key.slice(9)}),ground:s.collisionAt(...o.point)}))};},{g:groupId,id,owners:includes});
      assert.deepEqual(state.group.feature_local_ids,group.owners);assert.equal(state.registeredClip,null);assert.deepEqual(state.section,[]);
      for(const n of state.owners){assert.ok(!state.group.clip_feature_local_ids.includes(n.id));assert.notEqual(n.feature.candidateModel,true);assert.equal(n.ground,'building',String(n.id));}report.sources.push(state);save();
    }
    const actual=await page.evaluate(items=>items.map(p=>window.__SHANGHAI_APP__.scene.collisionAt(...p.wgs84)),probes);
    for(let i=0;i<probes.length;i++){const p=probes[i];const target=current?(p.blocked??p.expected==='building'):Boolean(p.ownerLocalId);const expect=target?'building':null;assert.equal(actual[i],expect,p.name);report.ground.push({name:p.name,wgs84:p.wgs84,expected:expect,actual:actual[i]});}save();
    if(current){await jump({...front,elevation:0,zoom:15.5,pitch:30});await variant('distant');await shot('map-distant','distant');}
    await Promise.all([...pending]);
    const required=[catalogName,'src/app.js','src/map-scene.js','src/building-beacons.js',far.file,...near.map(g=>g.file),...(current?[paths.get('full').filePath,paths.get('lod').filePath]:[])];
    for(const file of required)assert.ok(received.has(file),'No verified response to the actual page request for '+file+' '+(unread.get(file)||''));
    report.pageResponses=Object.fromEntries(received);save();
    if(current){
      // Leave the city in the same tab before opening the lighter standalone viewer.
      await page.goto(asURL('landmarks.html'),{waitUntil:'domcontentloaded'});
      const card=page.locator('.landmark-card[data-landmark="'+id+'"]');
      await card.locator('a[href="'+manifest.viewer_page+'"]').click();
      await wait(()=>document.querySelector('#status')?.textContent.startsWith('近景 ·'));
      report.downloads=[];
      for(const [role,item] of paths){
        const download=page.waitForEvent('download');
        const anchor=page.locator('#downloads a').filter({hasText:{raw:'原始',full:'网页',lod:'远景',native:'Blender'}[role]});
        await anchor.click();const file=await download;
        assert.equal(file.suggestedFilename(),item.file);
        const stream=await file.createReadStream(),hash=createHash('sha256');let size=0;
        for await(const chunk of stream){size+=chunk.length;hash.update(chunk);}
        const sha256=hash.digest('hex');assert.equal(sha256,item.sha256);assert.equal(size,item.bytes);
        report.downloads.push({role,name:file.suggestedFilename(),bytes:size,sha256});save();
      }
    }
    assert.deepEqual(report.pageErrors,[]);assert.deepEqual(report.httpErrors,[]);report.completed=true;
  }finally{if(browser){await browser.close();report.browserClosed=true;}report.finished=new Date().toISOString();save();}
}
run().catch(e=>{report.failure=e.stack;report.completed=false;save();console.error(e);process.exitCode=1;});
