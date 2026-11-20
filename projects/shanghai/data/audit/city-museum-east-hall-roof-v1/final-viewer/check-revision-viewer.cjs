/* Confirm the existing city-museum page and map link both identify the revised asset set. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto'),{chromium}=require('playwright');
const id='yangpu-former-shanghai-city-museum',url=process.env.MODEL_BASE_URL,root=process.env.SHANGHAI_PROJECT_ROOT,out=process.env.QA_OUTPUT_DIR;
const manifestRel='assets/models/candidates/'+id+'/manifest-east-hall-roof.json',parent=path.posix.dirname(manifestRel);
const sha=data=>createHash('sha256').update(data).digest('hex');
(async()=>{
 if(!url||!root||!out)throw Error('Supply MODEL_BASE_URL, SHANGHAI_PROJECT_ROOT and QA_OUTPUT_DIR');
 fs.mkdirSync(out,{recursive:true});
 const bytes=file=>fs.readFileSync(path.join(root,file)),manifest=JSON.parse(bytes(manifestRel));
 const report={id,base:url,started:new Date().toISOString(),manifestSha256:sha(bytes(manifestRel)),scriptSha256:sha(fs.readFileSync(__filename)),seen:[],views:[],downloads:[],errors:[],completed:false};
 const save=()=>fs.writeFileSync(path.join(out,'viewer.json'),JSON.stringify(report,null,2)+'\n');
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  for(const [mode,size] of [['desktop',{width:1000,height:670}],['mobile',{width:390,height:760}]]){
   const page=await browser.newPage({viewport:size,hasTouch:mode==='mobile',ignoreHTTPSErrors:true,acceptDownloads:true});
   page.on('pageerror',e=>report.errors.push(e.message));
   const responses=new Map();page.on('response',r=>responses.set(new URL(r.url()).pathname,r));
   await page.goto(new URL('city-museum.html',url).href,{waitUntil:'domcontentloaded'});
   assert.equal(await page.locator('header a').getAttribute('href'),'index.html#landmark='+id+'&mode=overview');
   for(const variant of ['full','lod']){
    await page.locator('#detail').selectOption(variant);
    await page.waitForFunction(({variant,triangles})=>{const s=window.cityMuseumViewer?.getState();return s?.status==='ready'&&s.variant===variant&&s.triangles===triangles;},{variant,triangles:manifest.assets[variant].triangles},{timeout:190000});
    const button=variant==='full'?'roof':'rear';await page.locator('#'+button).click();
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
    const state=await page.evaluate(()=>window.cityMuseumViewer.getState());
    assert.equal(state.modelId,id);assert.ok(state.geometries>0&&state.renderedTriangles>=state.triangles);assert(!state.error);
    const asset=manifest.assets[variant];const key=new URL(path.posix.join(parent,asset.file),url).pathname;
    const res=responses.get(key);assert.ok(res);const body=await res.body();assert.equal(res.status(),200);assert.equal(body.length,asset.bytes);assert.equal(sha(body),asset.sha256);
    const filename='viewer-'+mode+'-'+variant+'.png',image=await page.screenshot({path:path.join(out,filename),timeout:180000});
    report.views.push({mode,variant,button,state,filename,bytes:image.length,screenshotSha256:sha(image),modelBytes:body.length,modelSha256:sha(body)});save();
   }
   for(const name of ['city-museum.html','src/city-museum.js',manifestRel]){const res=responses.get(new URL(name,url).pathname);assert.ok(res,name);const body=await res.body();assert.equal(sha(body),sha(bytes(name)));report.seen.push({name,mode,bytes:body.length,sha256:sha(body)});}
   if(mode==='desktop'){
    for(const [role,asset] of Object.entries(manifest.assets)){
     const link=page.locator('#downloads a[data-role="'+role+'"]');const promised=page.waitForEvent('download');await link.click();const download=await promised;
     const body=fs.readFileSync(await download.path());assert.equal(sha(body),asset.sha256);assert.equal(body.length,asset.bytes);
     report.downloads.push({role,name:download.suggestedFilename(),bytes:body.length,sha256:sha(body)});
    }
   }
   await page.close();
  }
  assert.deepEqual(report.errors,[]);report.completed=true;
 }catch(error){report.failure=error.stack;throw error;}
 finally{report.finished=new Date().toISOString();save();await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
