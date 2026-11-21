/* Exercise the signed map's real zoom-out button to reach the 1.2 km transition on a 440px canvas. */
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
async function check(){
 const b=await chromium.connectOverCDP('http://127.0.0.1:19693');
 const page=b.contexts().flatMap(c=>c.pages()).find(p=>p.url().includes(':31193/index.html'));
 if(!page)throw Error('No 31193 public city page');
 const target='hongkou-embankment-building-riverfront';
 const data=()=>page.evaluate(id=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,t=m.transform;
 const a=s.getLandmarkAssetState(id);return {zoom:m.getZoom(),lngLat:t.getCameraLngLat(),altitude:t.getCameraAltitude(),variant:a?.variant,asset:a?.verifiedAsset,
   moving:m.isMoving(),route:location.hash};},target);
 const out=path.join(__dirname,'evidence/193/real-distance-zoom.json');
 const r={control:'Shanghai map zoom-out button',signedNearToFarMetres:1200,started:new Date().toISOString(),before:await data(),steps:[]};
 const save=()=>fs.writeFileSync(out,JSON.stringify(r,null,2)+'\n');
 if(r.before.zoom!==15.5||r.before.variant!=='full')throw Error('Initial far view no longer applies');
 save();
 for(let n=0;n<3;n++){
   const zoom=page.locator('button#zoom-out');
   await zoom.click({timeout:6000});
   r.steps.push({click:n+1,at:new Date().toISOString(),aria:await zoom.getAttribute('aria-label')});save();
   await page.waitForTimeout(900);
   const state=await data();
   r.steps.at(-1).view=state;save();
   if(state.variant==='distant')break;
   if(state.altitude>1400)break;
 }
 console.log(JSON.stringify(r.steps.map(s=>[s.click,s.view.zoom,s.view.altitude,s.view.variant])));
}
check().then(()=>process.exit(0),e=>{console.error(e);process.exit(1)});
