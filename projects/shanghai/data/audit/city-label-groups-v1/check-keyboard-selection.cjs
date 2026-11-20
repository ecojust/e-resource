/** Confirm that a group can be searched and that its last full-name row opens its production map location. */
const fs=require('node:fs');
async function selectWithKeyboard(page,file){
 const r={url:page.url(),started:new Date().toISOString(),completed:false};
 const state=()=>page.evaluate(()=>{
  const b=window.__SHANGHAI_APP__.scene.getBuildingBeaconState(),dlg=document.querySelector('.beacon-group-picker');
  return {city:b.count,groups:b.labelPositions.filter(g=>g.memberIds),open:dlg.open,other:document.querySelector('dialog[open]:not(.beacon-group-picker)')?.id,
   rows:[...dlg.querySelectorAll('[data-landmark]')].map(el=>({id:el.dataset.landmark,name:el.querySelector('strong').textContent,number:el.querySelector('span').textContent,visible:getComputedStyle(el).display!=='none',height:el.getBoundingClientRect().height,font:getComputedStyle(el).fontSize})),
   selected:new URLSearchParams(location.hash.slice(1)).get('landmark'),title:document.querySelector('#location-name').textContent};
 });
 const save=()=>fs.writeFileSync(file,JSON.stringify(r,null,2)+'\n');
 try{
  let s=await state();if(s.other){await page.keyboard.press('Escape');s=await state();}
  const g=s.groups.at(-1),btn=page.locator('[data-beacon-group="'+g.id+'"]');
  r.count=s.city;r.expectedMemberIds=g.memberIds;
  if(s.open&&s.rows.at(-1)?.id!==g.memberIds.at(-1)){await page.keyboard.press('Escape');s=await state();}
  if(!s.open)await btn.press('Enter');s=await state();
  if(!s.open||JSON.stringify(s.rows.map(r=>r.id))!==JSON.stringify(g.memberIds))throw Error('Group open or membership mismatch');
  r.realRows=s.rows;const target=s.rows.at(-1);
  const search=page.locator('dialog.beacon-group-picker[open] input');
  await search.fill(target.name);s=await state();const visible=s.rows.filter(x=>x.visible);
  if(visible.length!==1||visible[0].id!==target.id)throw Error('Filter selected another building');
  r.filter={text:target.name,visible};save();
  await page.locator('dialog.beacon-group-picker[open] [data-landmark="'+target.id+'"]').press('Enter');
  await page.waitForFunction(id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id,target.id,{polling:200,timeout:45000});
  s=await state();if(s.open||s.title!==target.name||s.selected!==target.id)throw Error('Building title or hash mismatch');
  r.selection={id:s.selected,title:s.title};r.completed=true;return r;
 }catch(e){r.failure=e.stack;throw e;}finally{r.finished=new Date().toISOString();save();}
}
module.exports={selectWithKeyboard};
