const {chromium}=require('playwright-core');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
async function run(){
 const mobile=process.env.QA_DEVICE==='phone',root=process.env.QA_SITE,out=process.env.QA_OUT,origin=process.env.QA_ORIGIN;
 const control=JSON.parse(fs.readFileSync(process.env.QA_EXPECTATION));
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'chromium',args:['--no-sandbox','--no-zygote','--single-process','--in-process-gpu','--disable-gpu','--disable-dev-shm-usage','--disable-background-networking','--num-raster-threads=1','--enable-low-end-device-mode']});
 const result={device:process.env.QA_DEVICE,viewport:mobile?{width:390,height:760}:{width:1024,height:690},javascript:false,images:[],started:new Date().toISOString(),source_sha256:sha(fs.readFileSync(__filename))};
 try{
  const p=await browser.newPage({viewport:result.viewport,deviceScaleFactor:.375,isMobile:mobile,hasTouch:mobile,javaScriptEnabled:false,acceptDownloads:true});
  const html=await p.goto(origin+'/xiyan-church-north-belfry.html');result.page_sha256=sha(await html.body());assert.equal(result.page_sha256,control.page);
  async function activate(el){await el.scrollIntoViewIfNeeded();if(mobile){await el.tap();}else{await el.click();}}
  for(const row of control.images){
   const el=p.locator('a[href="'+row.path+'"]');
   const got=p.context().waitForEvent('page');await activate(el);const img=await got;
   try{
    await img.waitForURL(origin+'/'+row.path,{waitUntil:'load'});
    const handle=await img.waitForFunction(()=>document.images[0]?.complete&&document.images[0].naturalWidth>0?[document.images[0].naturalWidth,document.images[0].naturalHeight]:false);
    const dim=await handle.jsonValue();assert.deepEqual(dim,row.size);
    const bytes=await (await img.request.get(img.url())).body();assert.equal(sha(bytes),row.sha256);result.images.push({path:row.path,opened:true,dimensions:dim,sha256:sha(bytes)});
   }finally{await img.close();}
  }
  const dl=p.waitForEvent('download');await activate(p.locator('#download-source'));const file=await dl;
  assert.equal(file.suggestedFilename(),control.archive.file);
  const dest=path.join(out,file.suggestedFilename());await file.saveAs(dest);assert.equal(await file.failure(),null);
  const bytes=fs.readFileSync(dest);assert.equal(sha(bytes),control.archive.sha256);assert.equal(bytes.length,control.archive.bytes);
  result.source={...control.archive,saved:true};await file.delete();result.passed=true;
 }finally{await browser.close();result.closed=!browser.isConnected();result.finished=new Date().toISOString();fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(result,null,2)+'\n');}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
