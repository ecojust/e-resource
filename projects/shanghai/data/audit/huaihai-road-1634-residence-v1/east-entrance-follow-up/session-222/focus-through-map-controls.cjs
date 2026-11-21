/** Follow the public landmark link and use the ordinary map controls to view the split-level entrance. */
const {chromium}=require('playwright'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const output=process.argv[2],prefix='http://127.0.0.1:31217/',id='xuhui-huaihai-road-1634-residence';
const project='/workspace/e-resource/projects/shanghai',audit=project+'/data/audit/huaihai-road-1634-residence-v1/';
const contract=JSON.parse(fs.readFileSync(audit+'final-placement-contract.json'));
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const angle=(x)=>((x+540)%360)-180;
const stepNames=[['upper-door',6.52,1.07,2.65],['sloping-rail',8.24,2.28,1.64],['stair-tread',8.50,1.18,.64],['lower-door',9.25,3.63,1.05]];
const rad=Math.PI/180,h=contract.heading*rad,k=6371008.8*Math.cos(contract.lat*rad),log=Math.asinh(Math.tan(contract.lat*rad));
const points=stepNames.map(([name,x,y,z])=>({name,z,lng:contract.lng+(x*Math.cos(h)+y*Math.sin(h))/k/rad,lat:Math.atan(Math.sinh(log+(-x*Math.sin(h)+y*Math.cos(h))/k))/rad}));
const record={id,base:prefix,method:'Ordinary street directory, camera rotation with the right mouse button, zoom buttons, and left-button panning',program_sha256:sha(fs.readFileSync(__filename)),placement_sha256:sha(fs.readFileSync(audit+'final-placement-contract.json')),started:new Date().toISOString(),actions:[],frames:[],responses:{},errors:[]};
function write(){fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(record,null,2)+'\n');}
async function main(){
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--single-process','--no-zygote','--in-process-gpu','--window-size=430,350','--disable-background-networking','--disable-extensions','--disable-gpu-shader-disk-cache','--disable-back-forward-cache','--disable-breakpad','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--enable-low-end-device-mode','--disable-gpu-rasterization','--renderer-process-limit=1','--js-flags=--max-old-space-size=240 --max-semi-space-size=3','--disk-cache-size=2097152',...(process.env.QA_CDP_PORT?['--remote-debugging-port='+process.env.QA_CDP_PORT]:[])]});
 try{
  const page=await browser.newPage({viewport:{width:830,height:570},deviceScaleFactor:.68});page.setDefaultTimeout(90000);
  page.on('pageerror',e=>record.errors.push(e.message));const pending=[];const wanted=['data/candidate-city-integrations.json','src/app.js','src/ordinary-scene-adapter.js',id+'-web.glb'];
  page.on('response',r=>{const u=new URL(r.url());if(u.origin!==new URL(prefix).origin||r.status()!==200)return;const key=wanted.find(k=>u.pathname.endsWith(k));if(!key||record.responses[key])return;pending.push(r.body().then(b=>{record.responses[key]={url:r.url(),sha256:sha(b),bytes:b.length};}).catch(()=>{}));});
  const directory=await page.request.get(prefix+'landmarks.html');const href='index.html#landmark='+id+'&mode=overview';assert((await directory.text()).includes('href="'+href+'"'));record.directory={url:directory.url(),href};write();await page.goto(prefix+href,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__?.scene;let a=s?.getLandmarkAssetState(id);return a?.visible&&a.status==='loaded'&&a.variant==='full'&&!s.map.isMoving()&&document.getElementById('loading')?.classList.contains('loaded');},id);
  const toggle=page.locator('#panel-toggle');if(await toggle.getAttribute('aria-expanded')==='true'){await toggle.click();record.actions.push({closeNavigation:true});}
  const projection=()=>page.evaluate(({id,points})=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,c=m.getCanvas(),rect=c.getBoundingClientRect();return {camera:{bearing:m.getBearing(),pitch:m.getPitch(),zoom:m.getZoom(),center:m.getCenter(),elevation:m.getCenterElevation()},asset:s.getLandmarkAssetState(id),canvas:{w:rect.width,h:rect.height},ui:['#location-card','#controls-hint','#explore-panel'].flatMap(k=>{const e=document.querySelector(k)?.getBoundingClientRect();return e?[[k,e.x,e.y,e.width,e.height]]:[]}),points:points.map(p=>{const v=()=>p.z,xy=m.transform.locationToScreenPoint({lng:p.lng,lat:p.lat},{getElevationForLngLat:v,getElevationForLngLatZoom:v});const x=xy.x+rect.x,y=xy.y+rect.y;const el=document.elementFromPoint(x,y);return{name:p.name,x,y,clear:el===c&&!s.pickBuildingBeacon(xy),element:el?.id||el?.tagName,beacon:s.pickBuildingBeacon(xy)};})};},{id,points});
  const wait=async()=>{await page.waitForTimeout(170);await page.waitForFunction(()=>!window.__SHANGHAI_APP__.scene.map.isMoving(),null,{timeout:10000}).catch(()=>{});};
  async function drag(button,x,y,dx,dy){await page.mouse.move(x,y);await page.mouse.down({button});await page.mouse.move(x+dx,y+dy,{steps:10});await page.mouse.up({button});await wait();record.actions.push({button,x,y,dx,dy});}
  function capped(value,limit){return Math.min(Math.max(value,-limit),limit);}
  async function angleTo(key,target){
   const diff=(a,b)=>key==='bearing'?angle(a-b):a-b;let state=await projection();if(Math.abs(diff(target,state.camera[key]))<1.8)return;
   const shift=key==='bearing'?32:30;await drag('right',475,180,key==='bearing'?shift:0,key==='pitch'?shift:0);
   let next=await projection();let slope=diff(next.camera[key],state.camera[key])/shift;if(Math.abs(slope)<.035){state=next;await drag('right',475,180,key==='bearing'?-shift:0,key==='pitch'?-shift:0);next=await projection();slope=diff(next.camera[key],state.camera[key])/-shift;}
   assert(Math.abs(slope)>.035,'Public right-drag did not change '+key);
   for(let i=0;i<5;i++){const err=diff(target,next.camera[key]);if(Math.abs(err)<2)break;const dx=capped(err/slope,key==='bearing'?220:135);state=next;await drag('right',475,180,key==='bearing'?dx:0,key==='pitch'?dx:0);next=await projection();const actual=diff(next.camera[key],state.camera[key])/dx;if(Math.abs(actual)>.1)slope=actual;}
  }
  async function place(cx,cy){
   for(let j=0;j<5;j++){const v=await projection(),x=v.points.reduce((s,p)=>s+p.x,0)/4,y=v.points.reduce((s,p)=>s+p.y,0)/4;if(Math.hypot(cx-x,cy-y)<9)break;
    await drag('left',475,175,capped(cx-x,260),capped(cy-y,160));}
  }
  const cdp=await page.context().newCDPSession(page);
  async function photo(label){await wait();const state=await projection();const png=Buffer.from((await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false})).data,'base64');const filename=label+'.png';fs.writeFileSync(path.join(output,filename),png);record.frames.push({filename,sha256:sha(png),bytes:png.length,...state,clearTargets:state.points.filter(x=>x.clear).length});write();}
  await photo('public-selected-entrance');await angleTo('bearing',-112);await angleTo('pitch',76);
  await place(456,184);await photo('public-east-entrance-before-zoom');
  for(let i=0;i<4;i++){const z=(await projection()).camera.zoom;if(z>=21.9)break;await page.locator('#zoom-in').click();await wait();record.actions.push({zoomIn:true});await place(470,185);}
  await photo('east-door-and-lower-entrance');
  await angleTo('bearing',-96);await angleTo('pitch',74);await place(456,180);await photo('east-door-and-stone-steps');
  await angleTo('bearing',-122);await angleTo('pitch',78);await place(481,196);await photo('east-door-stair-handrail');
  await Promise.allSettled(pending);
  const model=JSON.parse(fs.readFileSync(project+'/assets/models/candidates/'+id+'/manifest.json'));assert.equal(record.responses[id+'-web.glb']?.sha256,model.assets.full.sha256);
  const prod=JSON.parse(fs.readFileSync('/tmp/shanghai-yongjia-porch/scenes/217-comparison.json'));assert.equal(record.responses['data/candidate-city-integrations.json']?.sha256,prod.catalog_sha256);
  assert(record.frames.some(f=>f.clearTargets===4&&f.asset.visible&&f.asset.variant==='full'&&Math.abs(f.points[0].y-f.points[2].y)>22),'No frame with four unoccluded and separated targets');
  record.completed=true;
 }finally{await browser.close();record.finished=new Date().toISOString();write();}
}
fs.mkdirSync(output,{recursive:true});main().catch(e=>{record.error=e.stack;write();process.exitCode=1;});
