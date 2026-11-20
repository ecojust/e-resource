const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {chromium}=require('playwright'),id='xuhui-remi-apartments-181-183',base='http://127.0.0.1:31161/';
const d=process.argv[2];fs.mkdirSync(d,{recursive:true});const report={passed:false,base,id,actions:[],errors:[],failed:[]},sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const save=()=>fs.writeFileSync(path.join(d,'numbered-doors.json'),JSON.stringify(report,null,2)+'\n');
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--disk-cache-size=6291456','--num-raster-threads=1','--renderer-process-limit=2']});
const p=await b.newPage({viewport:{width:870,height:660},ignoreHTTPSErrors:true});p.setDefaultTimeout(120000);p.on('pageerror',e=>report.errors.push(String(e)));p.on('response',r=>{if(r.status()>=400)report.failed.push({url:r.url(),status:r.status()});});
try{
await p.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});await p.locator('[data-landmark="'+id+'"] .card-foot a[href*="mode=overview"]').click();
const groups=['14-13719-6695/14-13719-6695--2_0-s1-s0-s0','14-13719-6695/14-13719-6695--2_0-s1-s0-s1'];
const settle=async()=>p.waitForFunction(({id,groups})=>{const s=window.__SHANGHAI_APP__?.scene,m=s?.map,a=s?.getLandmarkAssetState(id);if(!s||m.isMoving()||!a?.visible||a.variant!=='full'||Number(getComputedStyle(document.querySelector('#loading')).opacity)>.012)return false;return groups.every((g,i)=>s.getCandidateIntegrationState().shader.ownerScopedSources.some(r=>r.id===g&&r.clip_feature_local_ids.includes([2268,2598][i])));},{id,groups},{timeout:220000,polling:400});
await settle();
const sample=async()=>await p.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState(id),r=Math.PI/180,cos=Math.cos(a.heading*r),sin=Math.sin(a.heading*r),rad=6371008.8*Math.cos(a.anchor[1]*r),orig=Math.asinh(Math.tan(a.anchor[1]*r));
const marks=[[-.622,-.035,2.026,'181'],[1.708,-.035,1.865,'183']].map(([x,y,z,n])=>{const e=x*cos+y*sin,h=-x*sin+y*cos;const p=m.transform.locationToScreenPoint({lng:a.anchor[0]+e/rad/r,lat:Math.atan(Math.sinh(orig+h/rad))/r},{getElevationForLngLat:()=>z,getElevationForLngLatZoom:()=>z});return{n,x:p.x,y:p.y,hit:document.elementFromPoint(p.x,p.y)?.tagName};});
return{marks,zoom:m.getZoom(),elevation:m.getCenterElevation(),bearing:m.getBearing(),pitch:m.getPitch(),eye:{...m.transform.getCameraLngLat(),alt:m.transform.getCameraAltitude()},center:m.getCenter(),viewport:[innerWidth,innerHeight],asset:a,groups:s.getCandidateIntegrationState().shader.ownerScopedSources.filter(g=>g.clip_feature_local_ids.includes(2268)||g.clip_feature_local_ids.includes(2598)),bits:s.getBuildingBeaconState().count,gpuLost:m.painter.context.gl.isContextLost()};},id);
if(await p.locator('#panel-toggle').getAttribute('aria-expanded')==='true'){await p.locator('#panel-toggle').click();report.actions.push('收起目录');}
await p.locator('#zoom-in').click();report.actions.push('点击地图加号');await settle();
for(let i=0;i<3;i++){
 const state=await sample();const [x,y]=['x','y'].map(k=>state.marks.reduce((n,r)=>n+r[k],0)/2);
 const safe=await p.evaluate(()=>{const m=document.querySelector('.maplibregl-canvas'),c=document.querySelector('#location-card').getBoundingClientRect();return{w:m.clientWidth,h:m.clientHeight,top:Math.max(145,document.querySelector('#building-beacon-legend').getBoundingClientRect().bottom+12),bottom:c.top-24};});
 const tx=.52*safe.w,ty=(safe.top+safe.bottom)/2,dx=Math.max(-260,Math.min(260,tx-x)),dy=Math.max(-220,Math.min(220,ty-y));
 if(Math.hypot(dx,dy)>9){const sx=tx-dx/2,sy=ty-dy/2;await p.mouse.move(sx,sy);await p.mouse.down();await p.mouse.move(sx+dx,sy+dy,{steps:12});await p.mouse.up();report.actions.push({drag:[sx,sy,sx+dx,sy+dy]});await settle();}
 if(i<2){const st=await sample();let z=st.marks.reduce((v,a)=>[v[0]+a.x/2,v[1]+a.y/2],[0,0]);if(st.marks.every(a=>a.hit==='CANVAS')&&z[0]>32&&z[0]<safe.w-70&&z[1]>safe.top&&z[1]<safe.bottom){await p.mouse.dblclick(z[0],z[1],{delay:80});report.actions.push({normalMapDoubleClick:z});}else{await p.locator('#zoom-in').click();report.actions.push('点击地图加号');}await settle();}
}
const result=await sample();assert(!result.gpuLost&&result.asset.visible&&result.marks.every(a=>a.hit==='CANVAS'));assert.equal(result.groups.length,2);const span=Math.hypot(result.marks[0].x-result.marks[1].x,result.marks[0].y-result.marks[1].y);assert(span>=70,'House numbers are still too small');
report.view=result;report.projectedNumberCenterSeparationPx=span;const img=await p.screenshot({path:path.join(d,'map-181-and-183.png'),timeout:95000});report.image_sha256=sha(img);assert.deepEqual(report.errors,[]);assert.deepEqual(report.failed,[]);report.passed=true;
}finally{await b.close();report.closed=true;save();}
})().catch(e=>{report.error=e.stack;save();process.exitCode=1;});
