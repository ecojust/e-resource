/* Sample rendered objects, true projected panel positions, actual vector layers and two registered asset versions. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{createHash}=require('node:crypto'),{chromium}=require('playwright');
const sha=b=>createHash('sha256').update(b).digest('hex');
const id='yangpu-former-shanghai-city-museum',out=process.argv[2],base=process.argv[3],before=process.argv.includes('--before');
const points=[['center',3,-1.1],['northwest',-2.3,1.45],['southeast',8.3,-3.65],['east',11,-1.1]];
async function sample(page){
 return await page.evaluate(async ({id,points})=>{
  const s=window.__SHANGHAI_APP__.scene,m=s.map,T=await import('./vendor/three.module.js'),state=s.getLandmarkAssetState(id);
  let activeScene,camera;const proto=T.Object3D.prototype,old=proto.onBeforeRender;
  try{proto.onBeforeRender=function(...args){if(args[1]?.isScene&&args[2]?.type==='Camera'){activeScene=args[1];camera=args[2];}return old.apply(this,args);};
   for(let i=0;i<6&&!activeScene;i++)await new Promise(done=>{m.once('render',()=>done());m.triggerRepaint()});}
  finally{proto.onBeforeRender=old;}
  if(!activeScene)throw Error('Cannot inspect the real rendered scene');
  const names=[];activeScene.traverseVisible(o=>{if(o.isMesh)names.push(o)});
  const coords=state.position,scale=Math.cos(31.2304*Math.PI/180)/Math.cos(state.anchor[1]*Math.PI/180),v=new T.Vector3();
  function project(x,y,z){const p=new T.Vector3(x,y,z).project(camera);return [(p.x+1)*innerWidth/2,(1-p.y)*innerHeight/2]}
  const tests=points.map(([label,e,n])=>{
   const x=coords[0]+e*scale,z=coords[2]-n*scale,ray=new T.Raycaster(new T.Vector3(x,coords[1]+180*scale,z),new T.Vector3(0,-1,0));
   const hits=ray.intersectObjects(names,false).filter(hit=>hit.point.y>3*scale).slice(0,24).map(h=>{
    let node=h.object,names=[];while(node){names.push(node.name||node.type);node=node.parent}
    const a=h.object.geometry.getAttribute('_feature_id_0'),fid=a&&a.getX(h.face.a),mat=Array.isArray(h.object.material)?h.object.material[h.face.materialIndex]:h.object.material;
    return {h:(h.point.y-coords[1])/scale,at:project(...h.point.toArray()),names,material:mat?.name,feature:fid,tag:mat?.userData?Object.keys(mat.userData):[]};
   });
   const aim=new T.Vector3(x,coords[1]+10.42*scale,z),eye=new T.Vector3().setFromMatrixPosition(camera.matrixWorld);
   const eyeRay=new T.Raycaster(eye,aim.clone().sub(eye).normalize(),0,eye.distanceTo(aim)+.25);
   const oblique=eyeRay.intersectObjects(names,false).slice(0,30).map(h=>{let node=h.object,group=[];while(node){group.push(node.name||node.type);node=node.parent}
     const a=h.object.geometry.getAttribute('_feature_id_0');return {local:[(h.point.x-coords[0])/scale,-(h.point.z-coords[2])/scale,(h.point.y-coords[1])/scale],tree:group,feature:a?.getX(h.face.a)}});
   const xy=project(x,coords[1]+10.42*scale,z);
   const layers=m.getStyle().layers.filter(l=>l.type==='fill-extrusion').map(l=>l.id);
   const features=m.queryRenderedFeatures(xy,{layers}).map(f=>({id:f.id,layer:f.layer.id,p:Object.fromEntries(Object.entries(f.properties).filter(([k])=>['height','render_height','elevation','name','id','num_floors','kind'].includes(k))),state:f.state}));
   return {label,e,n,xy,hits,oblique,eye:eye.toArray().map((x,i)=>(x-coords[i])/scale),features};
  });
  return {state,drawnMeshCount:names.length,tests,camera:{center:m.getCenter().toArray(),elevation:m.getCenterElevation(),zoom:m.getZoom(),bearing:m.getBearing(),pitch:m.getPitch(),width:innerWidth,height:innerHeight},active:s.getStreamingState().detail.active,vector:s.getCandidateIntegrationState().vector.map(v=>({source:v.source,active:v.active,counts:v.stats}))};
 },{id,points});
}
(async()=>{fs.mkdirSync(out,{recursive:true});const report={base,id,before,script:sha(fs.readFileSync(__filename)),views:[],completed:false};
const save=()=>fs.writeFileSync(path.join(out,'close.json'),JSON.stringify(report,null,2)+'\n');const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=15576']});
try{const page=await browser.newPage({viewport:{width:850,height:620}});await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded'});await page.locator('.landmark-card[data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]').click();
await page.waitForFunction(id=>{const s=window.__SHANGHAI_APP__?.scene,t=s?.getStreamingState(),l=document.querySelector('#loading');return s?.getLandmarkAssetState(id)?.visible&&l?.classList.contains('loaded')&&getComputedStyle(l).opacity==='0'},id,{timeout:420000,polling:400});
const toggle=page.locator('#panel-toggle');if(await toggle.getAttribute('aria-expanded')==='true')await toggle.click();
for(const [name,bearing,pitch,zoom]of [['plan',0,0,21.35],['first-angle',-12,35,20.20]]){
 if(name==='first-angle')await page.setViewportSize({width:810,height:580});
 await page.evaluate(({id,bearing,pitch,zoom,name})=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,a=s.getLandmarkAssetState(id).anchor;const r=6371008.8*Math.cos(a[1]*Math.PI/180);
 m.setCenterClampedToGround(false);m.jumpTo({center:[a[0]+3/r*180/Math.PI,Math.atan(Math.sinh(Math.asinh(Math.tan(a[1]*Math.PI/180))-1.1/r))*180/Math.PI],elevation:name==='first-angle'?10.3:10.42,zoom,bearing,pitch,padding:name==='first-angle'?{left:0,right:0,top:0,bottom:55}:{left:145,right:0,top:45,bottom:100}});s.loadLandmarks();s.refreshBuildingBeacons();},{id,bearing,pitch,zoom,name});
 await page.waitForFunction(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;return !m.isMoving()&&s.getStreamingState().detail.active.some(x=>x.id.startsWith('14-13722-6690/'))},null,{timeout:200000});
 const data=await sample(page);assert.equal(data.state.variant,'full');const file=name+'.png',b=await page.screenshot({path:path.join(out,file),timeout:220000});report.views.push({name,file,sha256:sha(b),...data});save();
}report.completed=true;}catch(e){report.failure=e.stack;throw e}finally{save();await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
