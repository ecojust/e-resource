'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process'),{createHash}=require('node:crypto');
const sha=b=>createHash('sha256').update(b).digest('hex');
const root=process.env.QA_OUTPUT_DIR,driver=path.join(__dirname,'check-255-architecture-shot.cjs');
const reports=[],parts=[];
for (const name of ['street','roof','balcony','dormer']){
  const dir=path.join(root,name);fs.mkdirSync(dir,{recursive:true});
  const brought=JSON.parse(fs.readFileSync(path.join(__dirname,'retained-architecture-steps.json')))[name];
  if(brought){
    const origin=path.join(__dirname,'attempts',brought.attempt),stageDir=path.join(origin,name),rt=path.join(stageDir,'main-browser.json');
    const body=fs.readFileSync(rt),r=JSON.parse(body),rec=JSON.parse(fs.readFileSync(path.join(origin,'architecture-stage-exits.json'))).find(e=>e.kind===name);
    const processBody=fs.readFileSync(path.join(origin,'process.json')),proc=JSON.parse(processBody);
    assert.ok(rec.exit===0 && proc.node_closed && proc.node_pids.includes(rec.pid) && !proc.remaining_children.length && !proc.remaining_chromium.length);
    assert.equal(rec.reportSHA256,sha(body));assert.equal(brought.report,sha(body));assert.ok(r.completed && r.shot===name);
    assert.equal(r.scriptSha256,sha(fs.readFileSync(path.join(origin,'check-255-architecture-shot.cjs'))));
    for(const [n,h] of [[r.screenshots[0].file,r.screenshots[0].sha256],[r.displayCaptures[0].displayImage,r.displayCaptures[0].displayImageSha256],[r.webglCaptures[0].file,r.webglCaptures[0].sha256],[r.viewportCalibration.image,r.viewportCalibration.sha256]]){
      assert.equal(sha(fs.readFileSync(path.join(stageDir,n))),h);fs.linkSync(path.join(stageDir,n),path.join(dir,n));
      if(n!==r.viewportCalibration.image)fs.linkSync(path.join(dir,n),path.join(root,n));
    }
    fs.copyFileSync(rt,path.join(dir,'main-browser.json'));fs.copyFileSync(path.join(origin,'check-255-architecture-shot.cjs'),path.join(dir,'original-driver.cjs'));fs.copyFileSync(path.join(origin,'process.json'),path.join(dir,'original-process.json'));
    parts.push({...rec,earlierAttempt:brought.attempt,originalProcessSHA256:sha(processBody),originalDriverSHA256:r.scriptSha256});reports.push(r);
    fs.writeFileSync(path.join(root,'architecture-stage-exits.json'),JSON.stringify(parts,null,2)+'\n');continue;
  }
  const work=spawnSync(process.execPath,[driver,...process.argv.slice(2)],{env:{...process.env,QA_OUTPUT_DIR:dir,HARDOON_ARCH_SHOT:name},stdio:'inherit'});
  parts.push({kind:name,pid:work.pid,exit:work.status,signal:work.signal});
  const rec=()=>fs.writeFileSync(path.join(root,'architecture-stage-exits.json'),JSON.stringify(parts,null,2)+'\n');
  rec();const file=path.join(dir,'main-browser.json');
  if(work.status!==0||!fs.existsSync(file)){process.exitCode=work.status||1;break;}
  const body=fs.readFileSync(file),r=JSON.parse(body);
  assert.ok(r.completed&&r.shot===name&&r.screenshots.length===1&&r.displayCaptures.length===1&&r.webglCaptures.length===1);
  assert.equal(r.scriptSha256,sha(fs.readFileSync(driver)));parts.at(-1).reportSHA256=sha(body);rec();
  for(const [n,h] of [[r.screenshots[0].file,r.screenshots[0].sha256],[r.displayCaptures[0].displayImage,r.displayCaptures[0].displayImageSha256],[r.webglCaptures[0].file,r.webglCaptures[0].sha256]]){
    assert.equal(sha(fs.readFileSync(path.join(dir,n))),h);fs.linkSync(path.join(dir,n),path.join(root,n));
  }
  reports.push(r);
}
if(reports.length===4){
  for(const r of reports)for(const k of ['id','server','catalog','caseSha256','bindings'])assert.deepEqual(r[k],reports[0][k]);
  const flat=k=>reports.flatMap(r=>r[k]||[]);
  const out={...reports[3],scriptSha256:sha(fs.readFileSync(__filename)),stageDriverSha256:sha(fs.readFileSync(driver)),stages:parts,started:reports[0].started,views:flat('views'),screenshots:flat('screenshots'),displayCaptures:flat('displayCaptures'),webglCaptures:flat('webglCaptures'),architecturalPixels:flat('architecturalPixels'),viewportCalibrations:reports.map(r=>r.viewportCalibration)};
  fs.writeFileSync(path.join(root,'main-browser.json'),JSON.stringify(out,null,2)+'\n');
}
