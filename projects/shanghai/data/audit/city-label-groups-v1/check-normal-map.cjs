const {chromium}=require('playwright');
const {createHash}=require('node:crypto');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const [base,out,countText,variant='original']=process.argv.slice(2),count=Number(countText);
fs.mkdirSync(out,{recursive:true});const target='jingan-country-hospital';
const report={base,count,variant,started:new Date().toISOString(),actions:[],states:[],modules:{},errors:[]},sha=b=>createHash('sha256').update(b).digest('hex');
const save=()=>fs.writeFileSync(out+'/observed.json',JSON.stringify(report,null,2)+'\n');
async function run(){
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
 const page=await browser.newPage({viewport:{width:320,height:568},hasTouch:true,isMobile:true,ignoreHTTPSErrors:true});
 page.setDefaultTimeout(180000);page.on('pageerror',e=>{report.errors.push(e.message);save()});
 const pending=[];page.on('response',r=>{let p=new URL(r.url()).pathname;if(/\/(app|map-scene|building-beacons|building-beacon-groups)\.js$/.test(p)||p.endsWith('data/candidate-city-integrations.json'))pending.push(r.body().then(b=>{report.modules[p]={url:r.url(),status:r.status(),sha256:sha(b)};}).catch(()=>{}));});
 const cdp=await page.context().newCDPSession(page);
 async function screenshot(name){
  let timer;
  try{
   const {data}=await Promise.race([cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false}),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('compositor capture exceeded 12 seconds')),12000);})]);
   const bytes=Buffer.from(data,'base64');fs.writeFileSync(path.join(out,name),bytes);return sha(bytes);
  }catch(e){(report.captureErrors??=[]).push({file:name,error:e.message});return null;}finally{clearTimeout(timer);}
 }
 const state=()=>page.evaluate(()=>{
   const scene=window.__SHANGHAI_APP__.scene,map=scene.map,b=scene.getBuildingBeaconState(),p=b.labelPositions;
   const rect=selector=>document.querySelector(selector)?.getBoundingClientRect().toJSON();
   const wrong=[],overlaps=[],domWrong=[];
   for(let i=0;i<p.length;i++){const r=p[i];for(const dx of [-.35,0,.35])for(const dy of [-.35,0,.35]){
    const x=r.x+dx*r.width,y=r.y+dy*r.height,actual=scene.pickBuildingBeacon({x,y});
    if(actual!==r.id)wrong.push({x,y,expected:r.id,actual});
    if(r.memberIds){const html=document.elementFromPoint(x,y)?.closest('[data-beacon-group]')?.dataset?.beaconGroup;if(html!==r.id)domWrong.push({x,y,expected:r.id,actual:html});}
   }
   for(let j=0;j<i;j++){const q=p[j];if(Math.abs(q.x-r.x)<(q.width+r.width)/2-.01&&Math.abs(q.y-r.y)<(q.height+r.height)/2-.01)overlaps.push([q.id,r.id]);}}
   const bounds=map.getMaxBounds();return {zoom:map.getZoom(),center:map.getCenter().toArray(),pitch:map.getPitch(),bearing:map.getBearing(),maxBounds:bounds?.toArray(),title:document.querySelector('#location-name').textContent,card:rect('#location-card'),legend:rect('#building-beacon-legend'),tools:rect('.map-tools'),panelOpen:document.querySelector('#panel-toggle').getAttribute('aria-expanded'),all:b.count,visible:b.visibleBuildingCount??p.length,mode:b.labelMode,layoutCount:p.length,fallback:b.overlapFallbackCount,wrong,domWrong,overlaps,positions:p,ids:b.ids};
 });
 const stable=async()=>{await page.waitForFunction(()=>{const s=window.__SHANGHAI_APP__?.scene;return s&&!s.map.isMoving()&&s.getBuildingBeaconState().revision>0;},{},{polling:300,timeout:130000});await page.waitForTimeout(380);};
 const snap=async(label)=>{const st=await state();report.states.push({label,...st});save();console.log(label,st.zoom,st.visible,st.mode,st.layoutCount,st.fallback,st.overlaps.length,st.wrong.length);return st;};
 const tap=async(sel)=>{
  const button=page.locator(sel);
  await button.waitFor({state:'attached'});
  if(sel==='#fit-city')await button.evaluate(el=>el.scrollIntoView({block:'nearest',inline:'nearest'}));
  const point=await page.waitForFunction(selector=>{
   const el=document.querySelector(selector),r=el?.getBoundingClientRect();
   if(!r||r.width<1||r.height<1)return false;
   const x=r.x+r.width/2,y=r.y+r.height/2;
   return el.contains(document.elementFromPoint(x,y))?{x,y}:false;
  },sel,{polling:180,timeout:35000});
  const xy=await point.jsonValue();await page.touchscreen.tap(xy.x,xy.y);
  report.actions.push({tap:sel,...xy});save();
 };
 try{
  await page.goto(new URL('landmarks.html',base).href,{waitUntil:'domcontentloaded'});
  const link=page.locator('a[href*="landmark='+target+'"]').first();await link.tap();
  await page.waitForFunction(()=>window.__SHANGHAI_APP__?.scene?.getBuildingBeaconState);
  await page.waitForFunction(()=>{const e=document.querySelector('#loading');return e?.classList.contains('loaded')&&getComputedStyle(e).visibility==='hidden'&&getComputedStyle(e).opacity==='0'},null,{timeout:420000});
  await stable();await snap('district-link');if(await page.locator('#panel-toggle').getAttribute('aria-expanded')!=='true')await tap('#panel-toggle');
  try{await tap('#fit-city');}
  catch(e){report.actions.push({unavailable:'#fit-city',reason:String(e.message).slice(-600)});await page.locator('#fit-city').press('Enter');report.actions.push('keyboard Enter on 查看全市');save();}
  await page.waitForTimeout(1600);
  if(await page.locator('#panel-toggle').getAttribute('aria-expanded')==='true')await tap('#panel-toggle');
  await stable();let st=await snap('fit-city');
  if(st.visible<count){for(let i=0;i<16;i++){const previous=st.zoom;await tap('#zoom-out');await page.waitForTimeout(450);await stable();st=await snap('zoom-out-'+(i+1));if(st.visible===count||Math.abs(st.zoom-previous)<.001)break;}}
  // All camera movement above uses the public directory link and map controls.
  assert.equal(st.all,count);assert.equal(st.visible,count);
  if(variant==='fixed')assert.equal(st.mode,'groups');
  if(variant==='individual125'){assert.equal(st.mode,'numbers');assert.equal(st.fallback,0);assert.deepEqual(st.overlaps,[]);assert.deepEqual(st.wrong,[]);}
  if(variant==='original'&&count>125){assert(st.wrong.length>0&&st.overlaps.length>0);}
  // Prove that the visible group opens and resolves a real destination before
  // requesting a pixel readback from a software compositor.
  if(st.mode==='groups' && process.env.QA_ENUMERATE_EACH_GROUP!=='1'){
    const last=st.positions.at(-1);
    const known=st.positions.flatMap(g=>g.memberIds);
    assert.equal(known.length,st.visible);assert.equal(new Set(known).size,st.visible);
    assert.deepEqual(st.domWrong,[]);assert.deepEqual(st.wrong,[]);assert.deepEqual(st.overlaps,[]);
    await page.touchscreen.tap(last.x,last.y);
    await page.waitForFunction(()=>document.querySelector('.beacon-group-picker')?.open,null,{polling:150,timeout:90000});
    report.realGroupTouch={id:last.id,x:last.x,y:last.y};
    report.selection=await require('./check-keyboard-selection.cjs').selectWithKeyboard(page,path.join(out,'search-keyboard.json'));
    assert.equal(report.selection.completed,true);report.completed=true;save();return;
  }
  report.screenshot=await screenshot('map.png');save();
  if(st.mode==='groups'){
    const known=st.positions.flatMap(g=>g.memberIds);assert.equal(new Set(known).size,known.length);assert.equal(known.length,st.visible);
    assert.deepEqual(st.domWrong,[]);assert.deepEqual(st.wrong,[]);assert.deepEqual(st.overlaps,[]);
    report.groups=[];
    for(const group of st.positions){
      await page.touchscreen.tap(group.x,group.y);const dlg=page.locator('dialog.beacon-group-picker[open]');await dlg.waitFor();
      const rows=await dlg.locator('[data-landmark]').evaluateAll(ns=>ns.map(n=>({id:n.dataset.landmark,name:n.querySelector('strong').textContent,number:n.querySelector('span').textContent,pixelSize:getComputedStyle(n).fontSize,height:n.getBoundingClientRect().height})));
      assert.deepEqual(rows.map(r=>r.id),group.memberIds);assert(rows.every(r=>parseFloat(r.pixelSize)>=12&&r.height>=44));
      report.groups.push({id:group.id,point:{x:group.x,y:group.y},rows});await tap('dialog.beacon-group-picker[open] .close-picker');await dlg.waitFor({state:'hidden'});save();
    }
    const groupIndex=count===126?st.positions.length-1:count===132?0:Math.floor(st.positions.length/2);
    const g=st.positions[groupIndex],row=report.groups[groupIndex].rows.at(-1);await page.touchscreen.tap(g.x,g.y);
    const dlg=page.locator('dialog.beacon-group-picker[open]');await dlg.locator('input').fill(row.name);
    const match=dlg.locator('[data-landmark="'+row.id+'"]');await match.waitFor();report.dialogScreenshot=await screenshot('picker.png');await tap('dialog.beacon-group-picker[open] [data-landmark="'+row.id+'"]');
    await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,row.id,{timeout:60000});
    report.realTouch={label:row.name,selected:row.id};
  }else if(st.wrong.length){
    const target=st.wrong.find(m=>m.actual&&m.actual!=='jingan-country-hospital');if(target){
     await page.touchscreen.tap(target.x,target.y);await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,target.actual,{timeout:55000});report.realTouch=target;
    }
  }else if(st.positions.length){const target=st.positions.at(-1);await page.touchscreen.tap(target.x,target.y);await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,target.id,{timeout:55000});report.realTouch={selected:target.id};}
  report.completed=true;
 }catch(e){report.failure=String(e.stack);throw e;}finally{await Promise.allSettled(pending);report.finished=new Date().toISOString();save();await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
