/* Open both ordinary city-directory entries. Apply candidate camera parameters only during comparison. */
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const target='xuhui-yongjia-village-no15';
const args=process.argv.slice(2);
const [base,mode,device,output,casesFile]=args;
assert.ok(['comparison','signed'].includes(mode) && ['desktop','phone'].includes(device));
const original=mode==='comparison', phone=device==='phone', cases=JSON.parse(fs.readFileSync(casesFile));
const hash=b=>createHash('sha256').update(b).digest('hex');
const evidence={target,base,mode,device,selectedBy:phone?'directory link touched':'directory link clicked',script:hash(fs.readFileSync(__filename)),cases_sha256:hash(fs.readFileSync(casesFile)),start:new Date().toISOString(),views:[],failed:[],errors:[],passed:false};
const out=path.resolve(output);fs.mkdirSync(out,{recursive:true});
function save(){fs.writeFileSync(path.join(out,'overview.json'),JSON.stringify(evidence,null,2)+'\n');}
(async()=>{
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--disk-cache-size=8388608','--num-raster-threads=1','--renderer-process-limit=2']});
  const page=await browser.newPage({viewport:phone?{width:390,height:844}:{width:870,height:660},ignoreHTTPSErrors:true,hasTouch:phone});
  const resources=[];
  page.on('pageerror',e=>evidence.errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)evidence.failed.push({status:r.status(),url:r.url()});else if(r.status()===200)resources.push(r.url());});
  page.on('requestfailed',r=>{if(r.failure()?.errorText!=='net::ERR_ABORTED')evidence.failed.push({error:r.failure()?.errorText,url:r.url()});});
  try{
    await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded',timeout:120000});
    const card=page.locator('article[data-landmark="'+target+'"] .card-foot a[href*="mode=overview"]');
    assert.equal(await card.count(),1);
    if(phone)await card.tap();else await card.click();
    await page.waitForFunction(id=>{
      const s=window.__SHANGHAI_APP__?.scene;if(!s)return false;
      const a=s.getLandmarkAssetState(id),c=s.getCandidateIntegrationState();
      return location.hash.includes(id)&&!s.map.isMoving()&&a?.visible&&a.status==='loaded'&&a.variant==='full'&&
        Number(getComputedStyle(document.querySelector('#loading')).opacity)<.015&&
        c.shader.ownerScopedSources.some(g=>g.id==='14-13719-6695/14-13719-6695--4_2-s0-s1-s1'&&g.clip_feature_local_ids.includes(4151));
    },target,{timeout:220000,polling:400});
    console.log(device,"selected, geometry and owner verified");
    const actualModule=resources.find(x=>/\/candidate-overview-camera\.js(?:\?|$)/.test(x));
    const actualCatalog=resources.find(x=>/\/data\/candidate-city-integrations\.json(?:\?|$)/.test(x));
    assert.ok(actualModule&&actualCatalog);
    for(const [role,url]of Object.entries({camera:actualModule,catalog:actualCatalog})){
      const response=await page.request.get(url);const b=await response.body();assert.equal(response.status(),200);evidence[role]={url,bytes:b.length,sha256:hash(b)};
    }
    const row=await page.evaluate(async({actualCatalog,target})=>{const j=await(await fetch(actualCatalog)).json();return j.models.find(v=>v.id===target);},{actualCatalog,target});
    assert.equal(row.owner.feature_local_id,4151);
    evidence.owner=row.owner;evidence.web=row.assets.web;
    const signedFiles=JSON.parse(fs.readFileSync(process.env.YONGJIA_PRODUCTION_JSON)).files;
    evidence.modelFiles=[];
    for(const [key,sha256]of Object.entries(signedFiles).filter(([k])=>k.startsWith('assets/models/candidates/'+target+'/') && /\.(?:blend|glb)$/.test(k))){
      const res=await page.request.get(new URL(key,base).href);const bytes=await res.body();assert.equal(res.status(),200);assert.equal(hash(bytes),sha256);
      evidence.modelFiles.push({file:key,bytes:bytes.length,sha256});
    }
    assert.equal(evidence.modelFiles.length,4);

    const web=resources.find(url=>new URL(url).pathname.endsWith('/'+row.assets.web.file.split('/').pop()));assert.ok(web);
    const webres=await page.request.get(web);assert.equal(hash(await webres.body()),row.assets.web.sha256);
    const extras=phone?[]:cases.filter(x=>x.detail);
    for(const sample of [{name:'signed',proposal:null},...extras]){
      if(sample.detail && await page.locator('#panel-toggle').getAttribute('aria-expanded')==='true')await page.locator('#panel-toggle').click();
      const result=await page.evaluate(async({actualModule,row,sample})=>{
        const app=window.__SHANGHAI_APP__,s=app.scene,m=s.map;
        const bounds=id=>document.querySelector(id).getBoundingClientRect();
        const width=m.getCanvas().clientWidth,height=m.getCanvas().clientHeight;
        const panel=bounds('#explore-panel'),card=bounds('#location-card'),legend=bounds('#building-beacon-legend'),tools=bounds('.map-tools');
        const mobile=window.matchMedia('(max-width:760px)').matches;
        const insets={left:!mobile&&document.querySelector('#panel-toggle').getAttribute('aria-expanded')==='true'?panel.right+16:16,right:Math.max(64,width-tools.left+8),top:Math.max(mobile?182:154,legend.bottom+8),bottom:Math.max(mobile?174:152,height-card.top+8)};
        if(sample.detail){
          const [x,y,h]=sample.detail.localFocus, angle=row.heading*Math.PI/180,rad=Math.PI/180;
          const east=x*Math.cos(angle)+y*Math.sin(angle),north=-x*Math.sin(angle)+y*Math.cos(angle),radius=6371008.8*Math.cos(row.lat*rad);
          const center=[row.lng+east/radius/rad,Math.atan(Math.sinh(Math.asinh(Math.tan(row.lat*rad))+north/radius))/rad];
          const focal=height/(2*Math.tan(36.87*rad/2));
          const camera={center,elevation:h,bearing:sample.detail.bearing,pitch:sample.detail.pitch,zoom:Math.min(24,Math.log2(focal*2*Math.PI*radius/(512*sample.detail.distance))),padding:insets};
          m.stop();m.setCenterClampedToGround(false);m.jumpTo(camera);s.refreshBuildingBeacons();
        }
        await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
        const state=s.getCandidateIntegrationState();const native=state.shader.ownerScopedSources.find(g=>g.id==='14-13719-6695/14-13719-6695--4_2-s0-s1-s1');
        const keyinfo=s.getBuildingBeaconState(),asset=s.getLandmarkAssetState(row.id),angle=asset.heading*Math.PI/180,rad=Math.PI/180,k=6371008.8*Math.cos(asset.anchor[1]*rad),origin=Math.asinh(Math.tan(asset.anchor[1]*rad));
        const features=[['left arch opening',-4.02,-1.38,1.88],['right arch opening',-3.06,-1.38,1.88],['left arch crown',-4.02,-1.38,2.64],['right arch crown',-3.06,-1.38,2.64],['number 15',-2.41,-1.21,1.86],['tiled hood',-3.48,-.55,3.25]];
        const samples=features.map(([name,x,y,z])=>{
          const en=x*Math.cos(angle)+y*Math.sin(angle),nn=-x*Math.sin(angle)+y*Math.cos(angle);
          const elev={getElevationForLngLat:()=>z,getElevationForLngLatZoom:()=>z};
          const a=m.transform.locationToScreenPoint({lng:asset.anchor[0]+en/k/rad,lat:Math.atan(Math.sinh(origin+nn/k))/rad},elev);
          const hit=document.elementFromPoint(a.x,a.y);return {name,x:a.x,y:a.y,hit:hit?.tagName||null,control:hit?.closest('#location-card,#explore-panel,.map-tools,#building-beacon-legend')?.id||null};
        });
        return {width,height,insets,samples,eye:{...m.transform.getCameraLngLat(),alt:m.transform.getCameraAltitude()},center:m.getCenter(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom(),elevation:m.getCenterElevation(),padding:m.getPadding(),selection:location.hash,selectedAsset:s.getLandmarkAssetState(row.id),ownerGroup:native?.feature_local_ids,clippedOwners:native?.clip_feature_local_ids,label:keyinfo.labelPositions.find(b=>b.id===row.id),contextLost:m.painter.context.gl.isContextLost()};
      },{actualModule,row,sample});
      assert.ok(result.selection.includes(target)&&result.selectedAsset?.visible&&!result.contextLost);
      if(sample.name==='signed')assert.equal(result.samples.filter(s=>s.control||s.hit!=='CANVAS').length,0,'A target detail is behind a public control');
      const f=sample.name+'.png',b=await page.screenshot({path:path.join(out,f),timeout:60000});
      evidence.views.push({...sample,...result,image:f,bytes:b.length,sha256:hash(b)});save();console.log(device,sample.name,result.zoom);
    }
    assert.deepEqual(evidence.errors,[]);assert.deepEqual(evidence.failed,[]);evidence.passed=true;
  }catch(e){evidence.failure=e.stack;throw e;}
  finally{await browser.close();evidence.closed=new Date().toISOString();save();}
})().catch(e=>{console.error(e);process.exitCode=1;});
