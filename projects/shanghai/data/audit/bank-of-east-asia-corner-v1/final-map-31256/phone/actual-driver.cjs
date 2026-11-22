'use strict';
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process'), {createHash}=require('node:crypto');
const hash=b=>createHash('sha256').update(b).digest('hex');
const output=process.env.QA_OUTPUT_DIR, phase=process.argv[3], child=path.join(__dirname,'directory-part.cjs');
const write=(name,data)=>fs.writeFileSync(path.join(output,name),JSON.stringify(data,null,2)+'\n');
const reports=[], events=[];
let prior='';
for (const part of ['initial','settled']){
  const dir=path.join(output,part);fs.mkdirSync(dir,{recursive:true});
  const used=path.join(dir,'actual-driver.cjs');fs.copyFileSync(child,used);
  const started=new Date().toISOString();
  const q=spawnSync(process.execPath,[child,...process.argv.slice(2)],{env:{...process.env,CITY_VIEW_PART:part,CITY_CLICKED_VIEW:prior,QA_OUTPUT_DIR:dir},stdio:'inherit'});
  const f=path.join(dir,'main-browser.json');
  const event={part,pid:q.pid,exit:q.status,signal:q.signal,started,finished:new Date().toISOString(),driverSha256:hash(fs.readFileSync(used)),reportSha256:fs.existsSync(f)?hash(fs.readFileSync(f)):null};
  events.push(event);write('directory-processes.json',events);
  const r=fs.existsSync(f)?JSON.parse(fs.readFileSync(f)):{completed:false,screenshots:[],views:[],errors:['No report written']};
  reports.push(r);
  for(const image of [...r.screenshots,...(r.displayCaptures||[]).map(c=>({file:c.displayImage,sha256:c.displayImageSha256}))]){
    assert.equal(hash(fs.readFileSync(path.join(dir,image.file))),image.sha256);
    fs.linkSync(path.join(dir,image.file),path.join(output,image.file));
  }
  const current={...r,completed:false,scriptSha256:hash(fs.readFileSync(__filename)),phase,views:reports.flatMap(x=>x.views),screenshots:reports.flatMap(x=>x.screenshots),displayCaptures:reports.flatMap(x=>x.displayCaptures||[]),separateBrowserProcesses:events};
  delete current.viewportCalibration;
  if(q.status!==0||q.signal||!r.completed){
    write('main-browser.json',current);process.exit(q.status||1);
  }
  assert.equal(event.driverSha256,r.scriptSha256);assert.equal(r.screenshots.length,1);assert.equal(r.part,part);
  if (part==='initial') prior=f;
  else {
    assert.equal(r.clickedUrl,reports[0].clickedUrl);assert.equal(reports[0].phase,phase);
    assert.deepEqual(r.errors,[]);assert.deepEqual(r.failed,[]);
    current.completed=true;current.started=reports[0].started;write('main-browser.json',current);
  }
}
