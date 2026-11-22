'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process'),{createHash}=require('node:crypto');
const sha=b=>createHash('sha256').update(b).digest('hex');
const dest=process.env.QA_OUTPUT_DIR,child=path.join(__dirname,'check-255-desktop-stage.cjs');
const stages=[];const reports=[];let prior='';
for(const kind of ['initial','settled']){
 const dir=path.join(dest,kind);fs.mkdirSync(dir,{recursive:true});
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
