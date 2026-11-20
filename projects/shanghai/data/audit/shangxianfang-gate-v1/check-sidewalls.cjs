/* Confirm the controller reports the building after actual movement into either interior wall. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const id='huangpu-shangxianfang-gate';
const audit=__dirname;
const base=process.env.MODEL_BASE_URL;
const output=process.env.QA_OUTPUT_DIR||audit;
const project=process.env.SHANGHAI_PROJECT_ROOT;
const read=p=>JSON.parse(fs.readFileSync(p));
const sha=b=>createHash('sha256').update(b).digest('hex');
const contract=read(path.join(audit,'final-placement-contract.json'));
const catalog='data/candidate-city-integrations.json';
const h=contract.heading*Math.PI/180,c=Math.cos(h),s=Math.sin(h);
const k=6371008.8*Math.cos(contract.lat*Math.PI/180),my=Math.asinh(Math.tan(contract.lat*Math.PI/180));
function point(x,y){
  return [contract.lng+(x*c+y*s)/k*180/Math.PI,Math.atan(Math.sinh(my+(-x*s+y*c)/k))*180/Math.PI];
}
function local(lng,lat){
  const east=k*(lng-contract.lng)*Math.PI/180,north=k*(Math.asinh(Math.tan(lat*Math.PI/180))-my);
  return [east*c-north*s,east*s+north*c];
}
async function run(){
  fs.mkdirSync(output,{recursive:true});
  const data=fs.readFileSync(path.join(project,catalog)),rows=JSON.parse(data);
  assert.equal(rows.resulting_city_count,108);
  const model=rows.models.find(r=>r.id===id);
  const report={id,base,started:new Date().toISOString(),completed:false,scriptSha256:sha(fs.readFileSync(__filename)),
    catalogSha256:sha(data),controllerSha256:sha(fs.readFileSync(path.join(project,'src/walk-controller.js'))),sides:[],errors:[]};
  const save=()=>fs.writeFileSync(path.join(output,'wall-controller.json'),JSON.stringify(report,null,2)+'\n');
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:320,height:418},ignoreHTTPSErrors:true});page.setDefaultTimeout(190000);
  page.on('pageerror',e=>report.errors.push(e.message));
  async function state(){
    const r=await page.evaluate(id=>{
      const a=window.__SHANGHAI_APP__,w=a.controller,mesh=a.scene.getLandmarkAssetState(id);
      return {position:[w.position.lng,w.position.lat],mode:a.mode,frame:w._previousTime,notice:Number.isFinite(w._lastNotice)?w._lastNotice:null,
        obstruction:a.scene.collisionAt(w.position.lng,w.position.lat),speed:w.speed,keys:[...w.keys],asset:mesh?.verifiedAsset?.sha256,
        visible:mesh?.visible,buildingNotice:document.body.innerText.includes('前方有建筑，请沿道路绕行。')};
    },id);
    return {...r,xy:local(...r.position)};
  }
  try{
    await page.goto(new URL('index.html#landmark='+id+'&mode=overview',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(id=>window.__SHANGHAI_APP__?.scene?.getLandmarkAssetState(id)?.visible,id);
    for(const [key,side] of [['a',-1],['d',1]]){
      const origin=point(side*2.15,5.55);
      await page.evaluate(async ({start,heading})=>{
        const a=window.__SHANGHAI_APP__;
        await a.selectPlace({id:'selected-location',name:'自选街区',custom:true,districtId:'310101',walkStart:start,bearing:heading},{mode:'walk'});
      },{start:origin,heading:contract.heading});
      await page.waitForFunction(id=>{const a=window.__SHANGHAI_APP__;return a.mode==='walk'&&a.scene.getLandmarkAssetState(id)?.visible;},id);
      await page.locator('canvas.maplibregl-canvas').focus();
      const first=await state(),samples=[];
      assert.ok(Math.abs(first.xy[0]-side*2.15)<.03&&Math.abs(first.xy[1]-5.55)<.03);
      // A plain walk gives the avatar enough room to move before it contacts the wall.
      await page.keyboard.down(key);
      let lastFrame=first.frame;
      const limit=Date.now()+360000;
      try{
        do{
          const s=await state();
          if(lastFrame!==s.frame){
            lastFrame=s.frame;samples.push(s);
            if(s.notice!==null&&s.notice>(first.notice??-1)&&s.speed<.02&&s.buildingNotice)break;
          }
          await page.waitForTimeout(400);
        }while(Date.now()<limit);
      }finally{await page.keyboard.up(key);}
      const stop=samples.at(-1);
      report.sides.push({key,origin:first,frames:samples});save();
      assert.ok(stop&&stop.notice!==null&&stop.notice>(first.notice??-1)&&stop.speed<.02&&stop.buildingNotice,'Native walk controller must report an actual building contact');
      assert.ok(stop.keys.includes('Key'+key.toUpperCase())&&stop.visible&&stop.asset===model.assets.web.sha256);
      assert.ok(samples.every(s=>s.mode==='walk'&&!s.obstruction&&Math.abs(s.xy[0])<2.77));
      assert.ok(side*stop.xy[0]>=2.15&&side*stop.xy[0]<2.77);
      const png=await page.screenshot({path:path.join(output,'map-wall-'+key+'.png'),timeout:180000});
      report.sides.at(-1).screenshot={file:'map-wall-'+key+'.png',sha256:sha(png),bytes:png.length};save();
    }
    assert.equal(report.sides.length,2);assert.deepEqual(report.errors,[]);report.completed=true;
  }catch(e){report.failure=e.stack;throw e;}
  finally{report.finished=new Date().toISOString();save();await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
