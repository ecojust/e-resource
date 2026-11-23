const {chromium}=require('./phone-devtools.cjs');
const fs=require('node:fs'),path=require('node:path');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const id='changning-huxi-villas-east-row-gable';
const root=process.env.ORDINARY_ROOT||path.resolve(__dirname,'../../../../../..');
const origin=process.env.ORDINARY_URL||'http://127.0.0.1:28874/';
const file='huxi-villas-east-row-gable.html';
const folder='assets/models/candidates/'+id+'/';
const source='source/precise/'+id+'/source/';
const report={id,page:file,devtools_sha256:sha(fs.readFileSync(path.join(__dirname,'phone-devtools.cjs'))),started:new Date().toISOString(),runs:[],downloads:{},scriptSHA256:sha(fs.readFileSync(__filename))};
function save(){const name='running.json';fs.writeFileSync(name+'.new',JSON.stringify(report,null,2)+'\n');fs.renameSync(name+'.new',name);}
function near(a,b){return a.length===b.length&&a.every((n,i)=>Math.abs(n-b[i])<1e-5);}
function world(v){return [v[0],v[2],-v[1]];}
async function get(relative){
 const response=await fetch(new URL(relative,origin));assert(response.ok,relative);
 const bytes=Buffer.from(await response.arrayBuffer());assert.equal(sha(bytes),sha(fs.readFileSync(path.join(root,relative))),relative);
 return bytes;
}
async function click(page,selector,mobile){
 const el=page.locator(selector);await el.scrollIntoViewIfNeeded();
 if(!mobile){await el.click();return;}
 const point=await el.evaluate(element=>{
   for(const rect of element.getClientRects()){
     const x=(Math.max(0,rect.left)+Math.min(innerWidth,rect.right))/2;
     const y=(Math.max(0,rect.top)+Math.min(innerHeight,rect.bottom))/2;
     const hit=document.elementFromPoint(x,y);
     if(hit && element.contains(hit))return {x,y};
   }
   return null;
 });
 assert(point,'No visible target for '+selector);
 await page.touchscreen.tap(point.x,point.y);
}
async function roleWait(page,expected) {
 try {
   await page.waitForFunction(v=>document.querySelector('#model-view').dataset.role===v,expected,{timeout:36000});
 } catch (e) {
   const details=await page.evaluate(()=>({role:document.querySelector('#model-view')?.dataset.role,
     period:document.querySelector('#period')?.value, detail:document.querySelector('#detail')?.value,
     status:document.querySelector('#status')?.textContent, retry:document.querySelector('#retry')?.hidden,
     url:location.href})).catch(ex=>({error:String(ex)}));
   throw new Error(JSON.stringify({expected,...details})+' '+e.message);
 }
}
async function recordCamera(page){
 return page.evaluate(async()=>{
   await new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done)));
   return window.__measuredView;
 });
}
async function run(){
 const manifest=JSON.parse(await get(folder+'manifest.json'));
 const catalog=JSON.parse(await get(source+'cameras.json'));assert(catalog.length===9);
 const limits=(process.env.ORDINARY_CAMERA_LIMITS||'0,9').split(',').map(Number);
 const views=catalog.slice(limits[0],limits[1]);assert(views.length>0);
 report.camera_limits=limits;
 const physical={...manifest.assets,...manifest.interchange};
 const roles=['raw','full','lod','native','fbx','obj','stl'];assert.ok(roles.every(r=>physical[r]));
 report.bound={};
 for(const rel of [file,source+'viewer.js',source+'cameras.json',folder+'manifest.json'])report.bound[rel]=sha(await get(rel));
 const stage=process.env.ORDINARY_STAGE;
 assert(['cameras','lod','files','gallery'].includes(stage));
 report.stage=stage;
 for(const mobile of [process.env.ORDINARY_DEVICE==='phone']){
   const viewport=mobile?{width:390,height:760}:{width:1024,height:690};
   const browser=await chromium.launch({downloadsPath:process.env.ORDINARY_DOWNLOAD_STAGING,executablePath:process.env.CHROMIUM_PATH||'chromium',args:['--headless=new','--ozone-platform=headless','--no-sandbox','--no-zygote','--single-process','--in-process-gpu','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disable-gpu-shader-disk-cache','--disable-gpu-program-cache','--disable-gpu-rasterization','--disable-background-networking','--disable-sync','--enable-low-end-device-mode','--disk-cache-size=1048576','--force-gpu-mem-available-mb=32','--js-flags=--optimize-for-size --max-old-space-size=64 --max-semi-space-size=1']});
   const result={device:mobile?'phone':'desktop',viewport,started:new Date().toISOString(),screens:[],errors:[],modelResponses:[],downloads:{}};report.runs.push(result);
   try{
     const page=await browser.newPage({viewport,deviceScaleFactor:.25,hasTouch:mobile,isMobile:mobile,javaScriptEnabled:stage!=='gallery'});
     result.device_pixel_ratio=await page.evaluate(()=>devicePixelRatio);
     page.on('pageerror',e=>result.errors.push(String(e)));
     page.on('response',res=>{if(res.url().includes(folder)&&res.url().endsWith('.glb'))result.modelResponses.push({file:res.url().split('/').pop(),http:res.status()});});
     const html=await page.goto(new URL(file,origin).href,{waitUntil:'domcontentloaded'});assert.equal(sha(await html.body()),report.bound[file]);
     if(stage!=='gallery')await roleWait(page,'full');
     if(stage==='cameras'){

     assert.deepEqual(await page.locator('button[data-view]').evaluateAll(a=>a.map(b=>[b.dataset.view,b.textContent])),catalog.map(v=>[v.name,v.label]));
     const canvas=page.locator('#model-view canvas');const bounds=await canvas.boundingBox(),panel=await page.locator('.panel').boundingBox();assert(bounds.width>200&&bounds.height>170);
     assert(bounds.x+bounds.width<=panel.x+1||bounds.y+bounds.height<=panel.y+1);
     await page.evaluate(async()=>{
       const T=await import('/vendor/three.module.js');
       const original=T.PerspectiveCamera.prototype.updateMatrixWorld;
       T.PerspectiveCamera.prototype.updateMatrixWorld=function(...args){
         const returned=original.apply(this,args);
         const column=this.matrixWorld.elements;
         window.__measuredView={position:this.position.toArray(),forward:[-column[8],-column[9],-column[10]],up:[column[4],column[5],column[6]],projection:[...this.projectionMatrix.elements],fov:this.fov,aspect:this.aspect};
         return returned;
       };
     });
       const photoSession=await page.context().newCDPSession(page);
       for(const pose of views){
         await photoSession.send('HeapProfiler.collectGarbage');
         await click(page,'button[data-view="'+pose.name+'"]',mobile);
         const live=await recordCamera(page);
         assert(live,pose.name);
         const eye=world(pose.eye),target=world(pose.target),delta=target.map((t,i)=>t-eye[i]);
         const distance=Math.hypot(...delta);
         const direction=delta.map(x=>x/distance);
         const expectedWidth=pose.width_m;
         const fit=Math.min(bounds.width/pose.width,bounds.height/pose.height);
         const fy=distance*pose.width/(expectedWidth*(pose.pixel_aspect_y||1));
         const fov=2*Math.atan(bounds.height/(2*fit*fy))*180/Math.PI;
         const pp=pose.principal_point_edge_px||pose.principal_point_px||[pose.width/2,pose.height/2];
         const finalProjection=live.projection;
         assert(Math.abs(finalProjection[0]-2*(fy*(pose.pixel_aspect_y||1))*fit/bounds.width)<1e-5);
         assert(Math.abs(finalProjection[5]-2*fy*fit/bounds.height)<1e-5);
         assert(Math.abs(finalProjection[8]-(pose.width-2*pp[0])*fit/bounds.width)<1e-5);
         assert(Math.abs(finalProjection[9]-(2*pp[1]-pose.height)*fit/bounds.height)<1e-5);
         assert(near(live.position,eye)&&near(live.forward,direction),JSON.stringify({pose:pose.name,live,eye,direction}));
         assert(Math.abs(live.fov-fov)<1e-6);
         if(pose.world_up)assert(near(live.up,world(pose.world_up)),JSON.stringify({pose:pose.name,up:live.up}));
         const filename=result.device+'-'+pose.name+'.jpg';
         const bytes=await canvas.screenshot({path:filename,type:'jpeg',quality:82,timeout:22000});
         result.screens.push({camera:pose.name,observed_camera:live,filename,sha256:sha(bytes),bytes:bytes.length});save();
       }
     assert.equal(new Set(result.screens.map(v=>v.sha256)).size,views.length);
     }
     if(stage==='lod'){
     const canvas=page.locator('#model-view canvas');
     const session=await page.context().newCDPSession(page);
     result.transitions=[];
     async function observe(detail,role,action) {
       await roleWait(page,role);
       const state=await page.evaluate(()=>({detail:document.querySelector('#detail').value,role:document.querySelector('#model-view').dataset.role,status:document.querySelector('#status').textContent}));
       assert.equal(state.detail,detail);assert.equal(state.role,role);
       result.transitions.push({action,...state});save();
       await session.send('HeapProfiler.collectGarbage');
     }
     if(mobile){
       for(const [detail,role] of [['full','full'],['lod','lod'],['full','full'],['auto','full']]){
         await page.selectOption('#detail',detail);await observe(detail,role,'selector');
       }
     }else{
       await page.selectOption('#detail','full');await observe('full','full','selector');
       await page.selectOption('#detail','auto');await observe('auto','full','selector');
       const box=await canvas.boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);
       for(let i=0;i<24;i++)await page.mouse.wheel(0,215);
       await observe('auto','lod','wheel');
       await page.selectOption('#detail','lod');await observe('lod','lod','selector');
       await page.selectOption('#detail','auto');await observe('auto','lod','selector');
       await click(page,'button[data-view="'+catalog[1].name+'"]',false);
       await observe('auto','full','photograph camera');result.wheel_automatic=true;
     }
     result.two_current_levels=true;
     }
     if(stage==='files'){
     for(const r of roles){
       console.log('download',result.device,r);const asset=physical[r];const pending=page.waitForEvent('download');
       await click(page,'#downloads [data-role="'+r+'"]',mobile);
       const download=await pending;assert.equal(download.suggestedFilename(),asset.file);
       const place=path.join(process.env.ORDINARY_SAVED||'saved',result.device);fs.mkdirSync(place,{recursive:true});
       const out=path.join(place,asset.file);await download.saveAs(out);assert.equal(await download.failure(),null);
       const digest=crypto.createHash('sha256');for await(const part of fs.createReadStream(out))digest.update(part);
       assert.equal(digest.digest('hex'),asset.sha256);assert.equal(fs.statSync(out).size,asset.bytes);
       const downloaded={filename:asset.file,device:result.device,bytes:asset.bytes,sha256:asset.sha256,saveAsVerified:true};
       result.downloads[r]=downloaded;
       report.downloads[r]=downloaded;
       await download.delete();save();
     }
     const archive=id+'-source.zip';
     const sourceDownload=page.waitForEvent('download');
     await click(page,'#download-source',mobile);
     const received=await sourceDownload;
     assert.equal(received.suggestedFilename(),archive);
     const saved=path.join(process.env.ORDINARY_SAVED||'saved',result.device,archive);
     await received.saveAs(saved);assert.equal(await received.failure(),null);
     const sourceBytes=fs.readFileSync(saved);assert.equal(sourceBytes.readUInt32LE(0),0x04034b50);
     assert.equal(sha(sourceBytes),sha(await get(folder+archive)));
     result.sourceArchive={file:archive,bytes:sourceBytes.length,sha256:sha(sourceBytes),saveAsVerified:true};
     await received.delete();
     assert.equal(Object.keys(result.downloads).length,7);
     }
     if(stage==='gallery'){
     result.galleryContext={javascript:false,role:'static HTML gallery links',sourceSha256:report.bound[file],viewport};
     const registration='data/audit/huxi-villas-east-row-gable-v1/final/registration/';
     result.registeredImages=[];
     for (const name of ["registered-views.jpg", "numbered-front-model.jpg", "archival-front-model.jpg", "garden-oblique-model.jpg"]) {
       const file=registration+name;
       const newTab=page.context().waitForEvent('page',{timeout:18000});
       await click(page,'a[href="'+file+'"]',mobile);
       const enlarged=await newTab;
       try {
         await enlarged.waitForURL(new URL(file,origin).href,{waitUntil:'commit',timeout:18000});
         const dimensions=await enlarged.waitForFunction(()=>{const img=document.images[0];return img && img.complete && img.naturalWidth>0 && img.naturalHeight>0 ? [img.naturalWidth,img.naturalHeight] : false;});
         const size=await dimensions.jsonValue();const expected=JSON.parse(execFileSync('python',['-c','from PIL import Image; import sys,json; print(json.dumps(Image.open(sys.argv[1]).size))',path.join(root,file)]));assert.deepEqual(size,expected);
         result.registeredImages.push({file,natural_size:size,sha256:sha(await get(file))});
       } finally { await enlarged.close(); }
     }
     result.comparison=result.registeredImages[0];
     }
     assert.deepEqual(result.errors,[]);result.passed=true;
   }finally{await browser.close();result.closed=!browser.isConnected();result.finished=new Date().toISOString();save();}
 }
 for(const device of report.runs){
   for(const frame of device.screens){
     frame.pixels=JSON.parse(execFileSync('python',[path.join(__dirname,'pixels.py'),frame.filename]));
     const p=frame.pixels;
     assert(p.foreground>300&&p.width>15&&p.height>15&&p.colors>12,JSON.stringify(frame));
   }
 }
 report.passed=true;fs.writeFileSync('report.json',JSON.stringify(report,null,2)+'\n');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
