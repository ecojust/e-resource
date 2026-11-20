/* Use the ordinary custom-place walk controller. The landmark's dedicated walk action is disabled. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createHash}=require('node:crypto');
const hash=data=>createHash('sha256').update(data).digest('hex');
module.exports = async function walkCampusGate(page,{row,contract,catalog,project,out,base}) {
  const id=row.id, heading=contract.heading*Math.PI/180;
  const k=6371008.8*Math.cos(contract.lat*Math.PI/180), n0=Math.asinh(Math.tan(contract.lat*Math.PI/180));
  function world(x,y) {
    return [contract.lng+(x*Math.cos(heading)+y*Math.sin(heading))/k*180/Math.PI,
      Math.atan(Math.sinh(n0+(-x*Math.sin(heading)+y*Math.cos(heading))/k))*180/Math.PI];
  }
  function local(lng,lat) {
    const e=k*(lng-contract.lng)*Math.PI/180,n=k*(Math.asinh(Math.tan(lat*Math.PI/180))-n0);
    return [e*Math.cos(heading)-n*Math.sin(heading),e*Math.sin(heading)+n*Math.cos(heading)];
  }
  const report={id,base,started:new Date().toISOString(),completed:false,frames:[],legs:[],screenshots:[],files:{},
    scriptSha256:hash(fs.readFileSync(__filename)),catalogCount:catalog.resulting_city_count,
    note:'An ordinary selected position is used at the start. All subsequent movement in the gate and the return journey uses the actual W/S keyboard handler.'};
  const save=()=>fs.writeFileSync(path.join(out,'walk-browser.json'),JSON.stringify(report,null,2)+'\n');
  async function state(){
    const v=await page.evaluate(id=>{
      const app=window.__SHANGHAI_APP__,c=app.controller,s=app.scene,a=s.getLandmarkAssetState(id);
      return {frame:c._previousTime,mode:app.mode,position:{...c.position},bearing:c.bearing,
        held:[...c.keys],standing:s.collisionAt(c.position.lng,c.position.lat),asset:{visible:a?.visible,status:a?.status,variant:a?.variant,sha256:a?.verifiedAsset?.sha256}};
    },id);
    v.xy=local(v.position.lng,v.position.lat);return v;
  }
  async function drive(key,endY){
    const direction=key==='w'?1:-1,started=await state(),leg={key,endY,started};let lastFrame;
    await page.keyboard.down('Shift');await page.keyboard.down(key);
    try{
      const deadline=Date.now()+420000;
      while(Date.now()<deadline){
        const v=await state();
        if(v.frame!==lastFrame){
          assert.equal(v.mode,'walk');assert.equal(v.standing,null,'Clear walk path');assert.equal(v.asset.sha256,row.assets.web.sha256);assert.equal(v.asset.visible,true);
          assert.ok(Math.abs(v.xy[0])<.50,'Held direction stays between gateposts');
          if(v.held.includes(key==='w'?'KeyW':'KeyS')){
            report.frames.push(v);lastFrame=v.frame;
            if((v.xy[1]-endY)*direction>=0){leg.finished=v;break;}
            if(report.frames.length%16===0)save();
          }
        }
        await page.waitForTimeout(110);
      }
      assert.ok(leg.finished,'Actual motion must cross the requested along-gate coordinate');
    } finally{await page.keyboard.up(key);await page.keyboard.up('Shift');}
    report.legs.push(leg);save();
  }
  async function shot(name){
    await page.evaluate(()=>new Promise(done=>{const m=window.__SHANGHAI_APP__.scene.map;m.once('render',()=>done());m.triggerRepaint();}));
    const bytes=await page.screenshot({path:path.join(out,name+'.png'),timeout:240000});
    report.screenshots.push({file:name+'.png',bytes:bytes.length,sha256:hash(bytes),pose:await state()});save();
  }
  try{
    for(const name of ['src/walk-controller.js','src/app.js','src/map-scene.js','data/candidate-city-integrations.json']){
      const response=await page.request.get(new URL(name,base).href),data=await response.body();
      assert.equal(response.status(),200);assert.equal(hash(data),hash(fs.readFileSync(path.join(project,name))));report.files[name]=hash(data);
    }
    await page.setViewportSize({width:700,height:490});
    await page.evaluate(async ({start,heading,districtId})=>{
      const a=window.__SHANGHAI_APP__;
      await a.selectPlace({id:'selected-location',name:'华山路老校门前',custom:true,districtId,walkStart:start,bearing:heading},{mode:'walk'});
    },{start:world(0,-2.72),heading:contract.heading,districtId:row.districtId});
    await page.waitForFunction(id=>{const a=window.__SHANGHAI_APP__,g=a?.scene.getLandmarkAssetState(id);return a.mode==='walk'&&g?.visible&&g.status==='loaded'&&g.variant==='full';},id,{timeout:240000});
    await page.locator('canvas.maplibregl-canvas').focus();report.start=await state();
    assert.ok(Math.abs(report.start.xy[0])<.10&&Math.abs(report.start.xy[1]+2.72)<.13);
    await drive('w',5.0);await shot('walk-under-gate');
    await drive('w',12.72);await shot('walk-inside-campus');
    await drive('s',-2.34);report.final=await state();
    assert.ok(report.frames.some(v=>v.xy[1]>12.70));assert.ok(report.final.xy[1]<-2.31);
    report.completed=true;
  }catch(error){report.failure=error.stack;throw error;}
  finally{report.finished=new Date().toISOString();save();}
};
