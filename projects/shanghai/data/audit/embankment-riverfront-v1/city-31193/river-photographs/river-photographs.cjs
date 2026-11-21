/* Read two frames straight from the signed production WebGL canvas. */
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const work=__dirname,root=process.env.RIVER_FRAME_DIR,base='http://127.0.0.1:31193/';
const id='hongkou-embankment-building-riverfront';
const contract=JSON.parse(fs.readFileSync('/workspace/e-resource/projects/shanghai/data/audit/embankment-riverfront-v1/final-placement-contract.json'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const sig='d33c5d13c7e33ef645201ffed6c69aa35c321464c3b39aed204a1db2f7c85ac8';
const point=(x,y)=>{
 const h=contract.heading*Math.PI/180,k=6371008.8*Math.cos(contract.lat*Math.PI/180);
 const east=x*Math.cos(h)+y*Math.sin(h),north=-x*Math.sin(h)+y*Math.cos(h);
 return [contract.lng+east/k*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(contract.lat*Math.PI/180))+north/k))*180/Math.PI];
};
const settings=[
 {name:'riverfront-from-suzhou-creek',target:point(32.,0.),elevation:14.6,pitch:63,bearing:contract.heading+5,zoom:17.50},
 {name:'riverfront-terrace-and-turret',target:point(60.3,7.27),elevation:29.9,pitch:53,bearing:contract.heading+14,zoom:19.45}
];
async function run(){
 const r={id,route:base+'index.html#landmark='+id+'&mode=overview',started:new Date().toISOString(),browser:null,frames:[],errors:[],completed:false};
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--enable-low-end-device-mode','--disable-gpu-rasterization','--js-flags=--max-old-space-size=344','--renderer-process-limit=2','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage','--num-raster-threads=1','--disk-cache-size=2097152','--remote-debugging-port=19694']});
 try{
 r.browser=browser.version();const page=await browser.newPage({viewport:{width:704,height:500},deviceScaleFactor:1,ignoreHTTPSErrors:true});
 page.on('pageerror',e=>r.errors.push(String(e)));
 const catalog=await page.request.get(base+'data/candidate-city-integrations.json');const data=await catalog.body();assert.equal(catalog.status(),200);
 const expected=JSON.parse(fs.readFileSync(path.join(work,'193-production.json'))).files['data/candidate-city-integrations.json'];assert.equal(sha(data),expected);
 r.catalog_sha256=expected;
 await page.goto(r.route,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState(),null,{timeout:150000});
 for(const c of settings){
   await page.evaluate(v=>{const s=window.__SHANGHAI_APP__.scene;s.map.setCenterClampedToGround(false);s.map.jumpTo({center:v.target,elevation:v.elevation,pitch:v.pitch,bearing:v.bearing,zoom:v.zoom,padding:{top:0,left:0,right:0,bottom:0}});s.loadLandmarks();s.refreshBuildingBeacons();},c);
   await page.waitForFunction(({id,sig})=>{const scene=window.__SHANGHAI_APP__.scene,m=scene.map,state=scene.getLandmarkAssetState(id),stream=scene.getStreamingState();return !m.isMoving()&&state?.visible&&state.status==='loaded'&&state.verifiedAsset?.sha256===sig&&stream.active.some(t=>t.id==='14-13720-6693'&&t.visible)&&stream.detail.active.length>0;},{id,sig},{timeout:180000,polling:500});
   const v=await page.evaluate(async id=>{const scene=window.__SHANGHAI_APP__.scene,m=scene.map;
     const frame=await new Promise(resolve=>{m.once('render',()=>resolve(m.getCanvas().toDataURL('image/png')));m.triggerRepaint();});
     const gl=m.painter.context.gl;
     return {frame,verified:scene.getLandmarkAssetState(id).verifiedAsset,zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),center:m.getCenter(),elevation:m.getCenterElevation(),glError:gl.getError(),contextLost:gl.isContextLost()};
   },id);
   assert.equal(v.verified.sha256,sig);assert.equal(v.glError,0);assert.equal(v.contextLost,false);
   const png=Buffer.from(v.frame.split(',')[1],'base64');delete v.frame;assert.ok(png.length>20000);
   fs.writeFileSync(path.join(root,c.name+'.png'),png);
   r.frames.push({...v,file:c.name+'.png',bytes:png.length,sha256:sha(png),captured:new Date().toISOString()});console.log(c.name,png.length);
 }
 assert.deepEqual(r.errors,[]);r.completed=true;
 }catch(e){r.error=String(e);throw e;}finally{await browser.close();r.finished=new Date().toISOString();fs.writeFileSync(path.join(root,'production-canvas.json'),JSON.stringify(r,null,2)+'\n');}
}
run().catch(e=>{console.error(e);process.exitCode=1});
