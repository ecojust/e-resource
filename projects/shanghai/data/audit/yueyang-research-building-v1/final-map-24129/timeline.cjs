/* Capture public 390px card entry through the final source transition in one session and one camera. */
const fs=require('node:fs'),path=require('node:path'),{createHash}=require('node:crypto'),assert=require('node:assert/strict'),{chromium}=require('playwright');
const dir=process.env.OUTPUT_DIR||__dirname,base=process.env.MODEL_BASE_URL||'http://127.0.0.1:24129/';
const id='xuhui-yueyang-320-research-building',ids=['4c58102c-0fab-4ca4-a1e9-e65020a3fbd5','4c6bfb34-e60a-4163-9038-2ed59b765dce'];
const hash=b=>createHash('sha256').update(b).digest('hex');
const report={id,base,scriptSHA:hash(fs.readFileSync(__filename)),started:new Date().toISOString(),errors:[],failedHTTP:[],complete:false};
const save=()=>fs.writeFileSync(path.join(dir,'timeline.json'),JSON.stringify(report,null,2)+'\n');
async function main(){
 fs.mkdirSync(dir,{recursive:true});
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=9830']});
 const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:false,hasTouch:true,ignoreHTTPSErrors:true});
 page.on('pageerror',e=>report.errors.push(e.message));page.on('response',r=>{if(r.status()>=400)report.failedHTTP.push({url:r.url(),status:r.status()});});
 try{
  const snap=JSON.parse(fs.readFileSync('/tmp/shanghai-east-medical-focus/scenes/129-production.json'));const catPath='data/candidate-city-integrations.json';
  const resp=await page.request.get(base+catPath),buf=await resp.body(),cat=JSON.parse(buf);assert.equal(hash(buf),snap.files[catPath]);const row=cat.models.find(o=>o.id===id);
  report.catalog={items:cat.resulting_city_count,sha256:hash(buf),source:base+catPath,web_sha256:row.assets.web.sha256};
  await page.addInitScript(({id,ids,target})=>{
   if(!location.pathname.endsWith('/index.html'))return;
   const tr=window.__YUEYANG_TIMELINE__={events:[],observations:[],images:{},lastKey:'',stableSince:null};
   const now=()=>Math.round(performance.now()*10)/10;
   function hook(){
    const scene=window.__SHANGHAI_APP__?.scene;if(!scene){setTimeout(hook,20);return}
    const m=scene.map;let idsPresent=[],totalFeatures=null,lastQuery=-1000,sourceEvents=0,lastState=null;
    function sample(origin){
     const a=scene.getLandmarkAssetState(id),time=now();const c=m.getCenter();
     if(time-lastQuery>220||origin==='source'){
      try{const f=m.querySourceFeatures('overture-buildings',{sourceLayer:'building',filter:['in',['get','id'],['literal',ids]]});idsPresent=[...new Set(f.map(o=>String(o.id)))].sort();}catch{}
      lastQuery=time;
     }
     let states;try{states=ids.map(key=>m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:key}));}catch{return}
     const suppressed=states.map(o=>!!(o?.candidateModel||o?.localModel)),mode=m.isMoving(),cam={lng:c.lng,lat:c.lat,zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),elevation:m.getCenterElevation()};
     const fixed=!mode&&Math.abs(cam.lng-121.44788187)<0.000025&&Math.abs(cam.lat-31.20320756)<0.000025&&Math.abs(cam.zoom-17.36149)<0.05&&Math.abs(cam.pitch-45)<0.1&&Math.abs(cam.bearing+106)<0.1;
     const verified=a?.visible===true&&a?.verifiedAsset?.sha256===target,exists=ids.every(key=>idsPresent.includes(key));
     const state={t:time,origin,assetStatus:a?.status,variant:a?.variant,visible:a?.visible,assetSHA:a?.verifiedAsset?.sha256||null,sourceEvents,queriedIDs:idsPresent,ownerStates:states,sourceLoaded:m.isSourceLoaded('overture-buildings'),camera:cam,fixed,verified,allOwnerFeaturesPresent:exists};
     const k=JSON.stringify([verified,exists,states,fixed,mode,state.sourceLoaded,a?.status]);
     if(k!==tr.lastKey){tr.observations.push(state);tr.lastKey=k}
     if(verified&&exists&&fixed&&suppressed.every(Boolean)){if(tr.stableSince===null)tr.stableSince=time;}else tr.stableSince=null;
     function frame(name){if(tr.images[name])return;try{const image=m.getCanvas().toDataURL('image/png');tr.images[name]={state:{...state},image};}catch(e){tr.images[name]={error:String(e)}}}
     if(origin==='render'&&verified&&fixed){frame('first-verified-frame');if(exists&&!suppressed.every(Boolean))frame('first-unsuppressed-frame');if(tr.stableSince!==null&&time-tr.stableSince>=1400){frame('stable-frame');tr.stableDuration=time-tr.stableSince;}}
     if(origin==='timer'&&tr.stableSince!==null&&time-tr.stableSince>=1400&&!tr.images['stable-frame'])m.triggerRepaint();lastState=state;
    }
    m.on('sourcedata',e=>{if(e.sourceId==='overture-buildings'){sourceEvents++;if(tr.events.length<300)tr.events.push({t:now(),type:e.sourceDataType,loaded:e.isSourceLoaded});sample('source')}});
    m.on('render',()=>sample('render'));setInterval(()=>sample('timer'),120);sample('start');
   }hook();
  },{id,ids,target:row.assets.web.sha256});
  await page.goto(base+'landmarks.html',{waitUntil:'domcontentloaded',timeout:30000});
  const card=page.locator('.landmark-card[data-landmark="'+id+'"] .card-foot a[href="index.html#landmark='+id+'&mode=overview"]');
  report.catalogCardCount=await page.locator('.landmark-card[data-landmark]').count();assert.equal(report.catalogCardCount,167);
  await card.tap({timeout:18000});await page.waitForFunction(()=>window.__YUEYANG_TIMELINE__?.images['stable-frame'],null,{timeout:90000,polling:150});
  const ui=await page.screenshot({path:path.join(dir,'stable-public-mobile.png'),timeout:22000});report.ui={file:'stable-public-mobile.png',bytes:ui.length,sha256:hash(ui),viewport:page.viewportSize()};
  report.complete=true;
 }catch(e){report.error=String(e);console.error(e);process.exitCode=1;}
 finally{
  const timeline=await page.evaluate(()=>window.__YUEYANG_TIMELINE__).catch(()=>null);
  if(timeline){for(const [tag,data]of Object.entries(timeline.images)){if(!data.image)continue;const b=Buffer.from(data.image.split(',')[1],'base64');fs.writeFileSync(path.join(dir,tag+'.png'),b);data.sha256=hash(b);data.file=tag+'.png';data.bytes=b.length;delete data.image;}report.timeline=timeline;}
  await browser.close();report.finished=new Date().toISOString();save();console.log(report.complete,Object.keys(report.timeline?.images||{}));
 }
}
main().catch(e=>{report.error=String(e);save();process.exitCode=1;});
