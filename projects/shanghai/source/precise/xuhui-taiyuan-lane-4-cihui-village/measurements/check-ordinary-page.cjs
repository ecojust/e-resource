const {chromium}=require('playwright-core');
const fs=require('node:fs'),path=require('node:path');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const id='xuhui-taiyuan-lane-4-cihui-village';
const root=process.env.ORDINARY_ROOT||path.resolve(__dirname,'../../../..');
const origin=process.env.ORDINARY_URL||'http://127.0.0.1:28768/';
const file='taiyuan-lane-4-cihui-village.html';
const folder='assets/models/candidates/'+id+'/';
const source='source/precise/'+id+'/source/';
const report={id,page:file,started:new Date().toISOString(),runs:[],downloads:{}};
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
 if(mobile){const rect=await el.boundingBox();await page.touchscreen.tap(rect.x+rect.width/2,rect.y+rect.height/2);}else await el.click();
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
 const views=JSON.parse(await get(source+'cameras.json'));assert.equal(views.length,7);
 const roles=['raw','full','lod','native'];assert.ok(roles.every(r=>manifest.assets[r]));
 report.bound={};
 for(const rel of [file,source+'viewer.js',source+'cameras.json',folder+'manifest.json'])report.bound[rel]=sha(await get(rel));
 for(const mobile of [false,true]){
   const viewport=mobile?{width:390,height:760}:{width:1024,height:690};
   const browser=await chromium.launch({downloadsPath:process.env.ORDINARY_DOWNLOAD_STAGING,executablePath:'/usr/bin/chromium',args:['--no-sandbox','--no-zygote','--single-process','--in-process-gpu','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disable-gpu-shader-disk-cache','--js-flags=--max-old-space-size=175']});
   const result={device:mobile?'phone':'desktop',viewport,started:new Date().toISOString(),screens:[],errors:[],modelResponses:[],downloads:{}};report.runs.push(result);
   try{
     const page=await browser.newPage({viewport,deviceScaleFactor:.85,hasTouch:mobile,isMobile:mobile});
     page.on('pageerror',e=>result.errors.push(String(e)));
     page.on('response',res=>{if(res.url().includes(folder)&&res.url().endsWith('.glb'))result.modelResponses.push({file:res.url().split('/').pop(),http:res.status()});});
     const html=await page.goto(new URL(file,origin).href,{waitUntil:'domcontentloaded'});assert.equal(sha(await html.body()),report.bound[file]);
     await roleWait(page,'full');

     assert.deepEqual(await page.locator('button[data-view]').evaluateAll(a=>a.map(b=>[b.dataset.view,b.textContent])),views.map(v=>[v.name,v.label]));
     const canvas=page.locator('#model-view canvas');const bounds=await canvas.boundingBox(),panel=await page.locator('.panel').boundingBox();assert(bounds.width>200&&bounds.height>170);
     assert(bounds.x+bounds.width<=panel.x+1||bounds.y+bounds.height<=panel.y+1);
     await page.evaluate(async()=>{
       const T=await import('/vendor/three.module.js');
       const original=T.PerspectiveCamera.prototype.updateMatrixWorld;
       T.PerspectiveCamera.prototype.updateMatrixWorld=function(...args){
         const returned=original.apply(this,args);
         const column=this.matrixWorld.elements;
         window.__measuredView={position:this.position.toArray(),forward:[-column[8],-column[9],-column[10]],fov:this.fov,aspect:this.aspect};
         return returned;
       };
     });
       for(const pose of views){
         await click(page,'button[data-view="'+pose.name+'"]',mobile);
         const live=await recordCamera(page);
         assert(live,pose.name);
         const eye=world(pose.eye),target=world(pose.target),delta=target.map((t,i)=>t-eye[i]);
         const distance=Math.hypot(...delta);
         const direction=delta.map(x=>x/distance);
         const fov=2*Math.atan(Math.max(pose.width_m*pose.height/pose.width,pose.width_m/live.aspect)/(2*distance))*180/Math.PI;
         assert(near(live.position,eye)&&near(live.forward,direction),JSON.stringify({pose:pose.name,live,eye,direction}));
         assert(Math.abs(live.fov-fov)<1e-6);
         const filename=result.device+'-'+pose.name+'.jpg';
         const bytes=await canvas.screenshot({path:filename,type:'jpeg',quality:82,timeout:22000});
         const pixels=JSON.parse(execFileSync('python',[path.join(__dirname,'measure_browser_frame.py'),filename]));
         assert(pixels.foreground>300&&pixels.width>15&&pixels.height>15&&pixels.colors>12,JSON.stringify({filename,pixels}));
         result.screens.push({camera:pose.name,observed_camera:live,filename,sha256:sha(bytes),bytes:bytes.length,pixels});save();
       }
     assert.equal(new Set(result.screens.map(v=>v.sha256)).size,7);
     for(const [detail,expect] of [['lod','lod'],['full','full'],['auto','full']]){
       console.log('detail',result.device,detail);await page.selectOption('#detail',detail);await roleWait(page,expect);
     }
     result.two_current_levels=true;
     if(!mobile){
       await click(page,'button[data-view="overview"]',false);const box=await canvas.boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);
       for(let i=0;i<24;i++)await page.mouse.wheel(0,215);
       await roleWait(page,'lod');await click(page,'button[data-view="grille"]',false);await roleWait(page,'full');result.wheel_automatic=true;
     }
     for(const r of roles){
       console.log('download',result.device,r);const asset=manifest.assets[r];const pending=page.waitForEvent('download');
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
     assert.equal(Object.keys(result.downloads).length,4);assert.deepEqual(result.errors,[]);result.passed=true;
   }finally{await browser.close();result.closed=!browser.isConnected();result.finished=new Date().toISOString();save();}
 }
 assert.equal(Object.keys(report.downloads).length,4);report.passed=true;fs.writeFileSync('report.json',JSON.stringify(report,null,2)+'\n');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
