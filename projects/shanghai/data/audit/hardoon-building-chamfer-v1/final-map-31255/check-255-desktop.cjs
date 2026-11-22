'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process'),{createHash}=require('node:crypto');
const sha=b=>createHash('sha256').update(b).digest('hex');
const dest=process.env.QA_OUTPUT_DIR,child=path.join(__dirname,'check-255-desktop-stage.cjs');
const stages=[];const reports=[];let prior='';
for(const kind of ['initial','settled']){
 const dir=path.join(dest,kind);fs.mkdirSync(dir,{recursive:true});
 if(kind==='initial'){
   const actual=path.join(__dirname,'attempts','desktop-09-architectural-camera');
   const closedBody=fs.readFileSync(path.join(actual,'desktop-stage-exits.json'));
   const closed=JSON.parse(closedBody)[0],attempt=JSON.parse(fs.readFileSync(path.join(actual,'process.json')));
   const src=path.join(actual,kind),body=fs.readFileSync(path.join(src,'main-browser.json')),r=JSON.parse(body);
   assert.equal(sha(body),'931c42c3374c16774c3b797585b6195b383adcd10b01d68e5523469a567563cb');
   assert.equal(closed.exit,0);assert.equal(closed.reportSHA256,sha(body));assert.ok(attempt.node_pids.includes(closed.pid));
   assert.ok(attempt.node_closed && attempt.remaining_chromium.length===0 && attempt.remaining_children.length===0);
   assert.ok(r.completed && r.part==='initial' && r.screenshots.length===1 && r.displayCaptures.length===1);
   assert.equal(r.scriptSha256,sha(fs.readFileSync(path.join(actual,'check-255-desktop-stage.cjs'))));
   const captures=[[r.screenshots[0].file,r.screenshots[0].sha256],[r.displayCaptures[0].displayImage,r.displayCaptures[0].displayImageSha256],[r.viewportCalibration.image,r.viewportCalibration.sha256]];
   for(const [name,digest] of captures){
     assert.equal(sha(fs.readFileSync(path.join(src,name))),digest);
     fs.linkSync(path.join(src,name),path.join(dir,name));
   }
   for(const name of [r.screenshots[0].file,r.displayCaptures[0].displayImage])fs.linkSync(path.join(dir,name),path.join(dest,name));
   fs.copyFileSync(path.join(src,'main-browser.json'),path.join(dir,'main-browser.json'));
   fs.copyFileSync(path.join(actual,'check-255-desktop-stage.cjs'),path.join(dir,'original-driver.cjs'));
   fs.copyFileSync(path.join(actual,'process.json'),path.join(dir,'original-process.json'));
   fs.copyFileSync(path.join(actual,'desktop-stage-exits.json'),path.join(dir,'original-stage-exits.json'));
   stages.push({...closed,earlierAttempt:'desktop-09-architectural-camera',originalProcessSHA256:sha(fs.readFileSync(path.join(actual,'process.json'))),originalDriverSHA256:r.scriptSha256});
   reports.push(r);prior=path.join(dir,'main-browser.json');
   fs.writeFileSync(path.join(dest,'desktop-stage-exits.json'),JSON.stringify(stages,null,2)+'\n');
   continue;
 }
 const work=spawnSync(process.execPath,[child,...process.argv.slice(2)],{env:{...process.env,QA_OUTPUT_DIR:dir,HARDOON_DESKTOP_STAGE:kind,HARDOON_INITIAL_REPORT:prior},stdio:'inherit'});
 stages.push({kind,pid:work.pid,exit:work.status,signal:work.signal});
 fs.writeFileSync(path.join(dest,'desktop-stage-exits.json'),JSON.stringify(stages,null,2)+'\n');
 const file=path.join(dir,'main-browser.json');
 if(work.status!==0||!fs.existsSync(file)){process.exitCode=work.status||1;break;}
 const body=fs.readFileSync(file),r=JSON.parse(body);assert.ok(r.completed&&r.part===kind&&r.screenshots.length===1&&r.displayCaptures.length===1);
 assert.equal(r.scriptSha256,sha(fs.readFileSync(child))); stages.at(-1).reportSHA256=sha(body);reports.push(r);
 for(const name of [r.screenshots[0].file,r.displayCaptures[0].displayImage])fs.linkSync(path.join(dir,name),path.join(dest,name));prior=file;
}
if(reports.length===2){
 const [a,b]=reports;for(const key of ['id','server','catalog','caseSha256','clickedUrl','bindings'])assert.deepEqual(a[key],b[key]);
 const total={...b,started:a.started,scriptSha256:sha(fs.readFileSync(__filename)),stageDriverSha256:sha(fs.readFileSync(child)),stages,screenshots:[...a.screenshots,...b.screenshots],views:[...a.views,...b.views],displayCaptures:[...a.displayCaptures,...b.displayCaptures],viewportCalibrations:[a.viewportCalibration,b.viewportCalibration],completed:true};
 fs.writeFileSync(path.join(dest,'main-browser.json'),JSON.stringify(total,null,2)+'\n');
}
