/* Open the actual static gallery links with a mouse or touch and read the image in each new tab. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const {setTimeout:wait}=require('node:timers/promises');
const {chromium}=require('./phone-devtools.cjs');
const root=process.env.ORDINARY_ROOT,origin=process.env.ORDINARY_URL;
const device=process.env.ORDINARY_DEVICE,id='yangpu-fudan-old-gate-timber-paifang',slug='fudan-old-gate-timber-paifang';
const names=["registered-gate.jpg", "commons-2006-model.jpg", "school-front-model.jpg", "school-postcard-model.jpg", "editorial-reverse-model.jpg"];
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
async function get(rel){
 const r=await fetch(new URL(rel,origin));assert(r.ok);const bytes=Buffer.from(await r.arrayBuffer());
 assert.equal(sha(bytes),sha(fs.readFileSync(path.join(root,rel))));return bytes;
}
async function naturalSize(wsurl){
 const socket=new WebSocket(wsurl);let id=0,awaited=new Map();
 await new Promise((ok,bad)=>{socket.onopen=ok;socket.onerror=bad;});
 socket.onmessage=e=>{const m=JSON.parse(e.data);const a=awaited.get(m.id);if(a){awaited.delete(m.id);a(m);}};
 try{
  for(let i=0;i<45;i++){
   const answer=new Promise(ok=>awaited.set(++id,ok));
   socket.send(JSON.stringify({id,method:'Runtime.evaluate',params:{expression:'document.images[0]?.complete && [document.images[0].naturalWidth,document.images[0].naturalHeight]',returnByValue:true}}));
   const val=(await answer)?.result?.result?.value;if(val?.[0]>0)return val;await wait(100);
  }
  throw Error('Popup photograph did not decode');
 }finally{socket.close();}
}
async function main(){
 const pageFile=slug+'.html',mobile=device==='phone',viewport=mobile?{width:390,height:760}:{width:1024,height:690};
 const bound={};for(const p of [pageFile,'source/precise/'+id+'/source/viewer.js','source/precise/'+id+'/source/cameras.json','assets/models/candidates/'+id+'/manifest.json'])bound[p]=sha(await get(p));
 const report={id,page:pageFile,stage:'gallery',scriptSHA256:sha(fs.readFileSync(__filename)),devtools_sha256:sha(fs.readFileSync(path.join(__dirname,'phone-devtools.cjs'))),bound,runs:[]};
 const result={device,viewport,errors:[],registeredImages:[],galleryContext:{role:'Static HTML image links',sourceSha256:bound[pageFile],viewerLoaded:false,viewport}};
 report.runs.push(result);
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH,args:['--headless=new','--disable-gpu','--disable-software-rasterizer','--no-zygote','--single-process','--disable-background-networking','--disable-sync','--disk-cache-size=262144','--js-flags=--optimize-for-size --max-old-space-size=64']});
 try {
  const page=await browser.newPage({viewport,deviceScaleFactor:.375,hasTouch:mobile,isMobile:mobile});const session=await page.context().newCDPSession(page);
  await session.send('Network.setBlockedURLs',{urls:['*/source/viewer.js']});
  const response=await page.goto(new URL(pageFile,origin).href);assert.equal(sha(await response.body()),bound[pageFile]);
  const b=await browser.newBrowserCDPSession();
  for(const name of names){
   const file='data/audit/'+slug+'-v1/final/registration/'+name,href=new URL(file,origin).href;
   const point=await page.evaluate(rel=>{
    const e=[...document.links].find(a=>a.getAttribute('href')===rel);if(!e||e.target!=='_blank')return null;
    e.scrollIntoView({block:'center',behavior:'instant'});
    for(const r of e.getClientRects()){
     const x=(Math.max(0,r.left)+Math.min(innerWidth,r.right))/2,y=(Math.max(0,r.top)+Math.min(innerHeight,r.bottom))/2;
     if(e.contains(document.elementFromPoint(x,y)))return {x,y};
    } return null;
   },file);assert(point,file);
   const old=new Set((await b.send('Target.getTargets')).targetInfos.map(t=>t.targetId));
   if(mobile)await page.touchscreen.tap(point.x,point.y);else await page.mouse.click(point.x,point.y);
   let target;
   for(let i=0;i<80&&!target;i++){const tabs=await (await fetch('http://127.0.0.1:'+process.env.QA_CDP_PORT+'/json/list')).json();target=tabs.find(t=>t.type==='page'&&!old.has(t.id)&&t.url===href);if(!target)await wait(100);}
   assert(target,'Image did not open: '+file);
   const size=await naturalSize(target.webSocketDebuggerUrl);const expected=JSON.parse(execFileSync('python',['-c','from PIL import Image;import sys,json;print(json.dumps(Image.open(sys.argv[1]).size))',path.join(root,file)]));
   assert.deepEqual(size,expected);result.registeredImages.push({file,natural_size:size,sha256:sha(await get(file)),pointer:point});
   await b.send('Target.closeTarget',{targetId:target.id});await page.bringToFront();
  }
  result.comparison=result.registeredImages[0];result.passed=true;
 }finally{await browser.close();result.closed=!browser.isConnected();}
 report.passed=true;fs.writeFileSync('report.json',JSON.stringify(report,null,2)+'\n');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
