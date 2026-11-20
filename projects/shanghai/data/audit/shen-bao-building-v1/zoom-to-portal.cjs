/* Apply a real mouse wheel over the modelled sign to keep the target in the open part of the map. */
const fs=require('node:fs');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.connectOverCDP(process.env.QA_CDP_URL);
 const page=browser.contexts()[0].pages()[0];
 const id='huangpu-shen-bao-building';
 const data=JSON.parse((await (await page.request.get(new URL('data/candidate-city-integrations.json',page.url()).href)).body()).toString());
 const row=data.models.find(v=>v.id===id),steps=[];
 const read=()=>page.evaluate(row=>{
  const s=window.__SHANGHAI_APP__.scene,m=s.map,r=Math.PI/180,h=row.heading*r,k=6371008.8*Math.cos(row.lat*r);
  const e=-.09*Math.sin(h),n=-.09*Math.cos(h),lng=row.lng+e/k/r,lat=Math.atan(Math.sinh(Math.asinh(Math.tan(row.lat*r))+n/k))/r;
  const p=m.transform.locationToScreenPoint({lng,lat},{getElevationForLngLat:()=>3.95});
  return {xy:[p.x,p.y],zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing(),center:m.getCenter()};
 },row);
 let st=await read();
 for(let i=0;i<4 && st.zoom<22.60;i++){
  const at=st.xy.map(Math.round);if(at[0]<20||at[1]<90||at[0]>946||at[1]>478)break;
  await page.mouse.move(...at);await page.mouse.wheel(0,-450);await page.waitForTimeout(1400);await page.waitForFunction(()=>!window.__SHANGHAI_APP__.scene.map.isMoving(),null,{timeout:90000});
  const next=await read();steps.push({before:st,input:{at,deltaY:-450},after:next});st=next;
  fs.writeFileSync(process.env.QA_RESULT,JSON.stringify({id,route:page.url(),steps},null,2)+'\n');console.log(next.zoom,next.xy);
 }
 process.exit(0);
})().catch(error=>{console.error(error);process.exit(1)});
