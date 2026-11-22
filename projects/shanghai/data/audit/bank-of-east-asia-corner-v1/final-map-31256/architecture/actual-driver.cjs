'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process'),{createHash}=require('node:crypto');
const sha=b=>createHash('sha256').update(b).digest('hex');
const root=process.env.QA_OUTPUT_DIR,driver=path.join(__dirname,'check-256-architecture-shot.cjs');
const reports=[],parts=[];
for (const name of ['street','roof','entrance','crown']){
  const dir=path.join(root,name);fs.mkdirSync(dir,{recursive:true});
  if(['street','roof','entrance'].includes(name)){
    const attempt=name==='street'?'architecture-02-roof-renderer':'architecture-03-crown-renderer';
    const origin=path.join(process.env.BANK_ARCHIVE_ROOT||__dirname,'attempts',attempt);
    const pins=name==='street'?{"actual-driver.cjs": "059a3963eca33fd8b9b27d4c3e69f2004b727700704efa6bfc50d2cf8f2a60ed", "street/actual-driver.cjs": "5d8cd9641e94280543886b23a999f063f36af3dd208ffc3eebb4824535bcb613", "street/main-browser.json": "0a8cd17b4c0980916bd225c32a68400f285ffa61ad56993e6c24eb82842fa897", "process.json": "6eb6c558171dbca3c76bc08a6ad666c716dc1eac2298d9b480b3f83da3549c8f", "architecture-stage-exits.json": "a896610d51db6aced2dda58362e4ed7b32010b3765de434284e6c7ba6dcd2962"}:{"actual-driver.cjs": "3ed84c6616cc567add15ff070241a3a2545f95f36bf11fd6a52f2d3f4beb24e7", "process.json": "7caf5da46cf0c2777ccabb0c11fb0ed4f9078b9d1817ff8e30ec8d663467be7d", "architecture-stage-exits.json": "e799376e70540fbc24c1dfd04e8b353a913f8719674d78c2c9ee956267866e49", "roof/actual-driver.cjs": "a5ef015b062dd0a35639877577a48b7c7c504275dc755c883c25e4b1f25fed68", "roof/main-browser.json": "ba962aaaa3bb3521a16668e705281c875052a78eb6b159bb5e01aba666ffc3d9", "entrance/actual-driver.cjs": "a5ef015b062dd0a35639877577a48b7c7c504275dc755c883c25e4b1f25fed68", "entrance/main-browser.json": "c7e1cbb48fa918defe000bfa9d8070bae8942bf3ba9e81463d4fe1cf8d6c38de"};
    const get=f=>{const body=fs.readFileSync(path.join(origin,f));assert.equal(sha(body),pins[f],f);return body;};
    const originalAggregate=get('actual-driver.cjs'),originalDriver=get(name+'/actual-driver.cjs');
    const processes=get('process.json'),closed=JSON.parse(processes),stageExits=get('architecture-stage-exits.json');
    const entries=JSON.parse(stageExits),entry=entries.find(e=>e.kind===name);
    assert.equal(closed.phase,'architecture');assert.equal(closed.exit_code,1);assert.equal(closed.node_closed,true);
    assert.deepEqual(closed.remaining_children,[]);assert.deepEqual(closed.remaining_chromium,[]);assert.ok(closed.chromium_pids.length);
    assert.equal(entry.exit,0);assert.equal(entry.signal,null);assert.ok(closed.node_pids.includes(entry.pid));
    const report=get(name+'/main-browser.json'),r=JSON.parse(report);
    assert.equal(entry.reportSHA256,sha(report));assert.equal(r.scriptSha256,sha(originalDriver));
    assert.ok(r.completed&&r.shot===name&&Date.parse(closed.started)<=Date.parse(r.started)&&Date.parse(r.finished)<=Date.parse(closed.finished));
    assert.equal(r.caseSha256,sha(fs.readFileSync(process.argv[2])));assert.equal(r.phase,'architecture');
    assert.equal(r.entry.status,200);assert.equal(r.entry.sha256,r.bindings['index.html']);
    assert.equal(r.views.length,1);assert.equal(r.views[0].sections.length,1);assert.equal(r.views[0].sections[0].segments,6);
    assert.equal(r.views[0].group.triangles,12);assert.deepEqual([...r.views[0].group.clip_feature_local_ids].sort((a,b)=>a-b),[53,1718,1782]);
    assert.deepEqual([r.screenshots.length,r.displayCaptures.length,r.webglCaptures.length],[1,1,1]);
    const retain=(src,dst)=>{try{fs.linkSync(src,dst);}catch(err){if(err.code!=='EXDEV')throw err;fs.copyFileSync(src,dst,fs.constants.COPYFILE_EXCL);}};
    for(const [n,h] of [[r.screenshots[0].file,r.screenshots[0].sha256],[r.displayCaptures[0].displayImage,r.displayCaptures[0].displayImageSha256],[r.webglCaptures[0].file,r.webglCaptures[0].sha256],[r.viewportCalibration.image,r.viewportCalibration.sha256]]){
      assert.equal(path.basename(n),n);const source=path.join(origin,name,n);assert.equal(sha(fs.readFileSync(source)),h);retain(source,path.join(dir,n));
      if(n!==r.viewportCalibration.image)retain(path.join(dir,n),path.join(root,n));
    }
    for(const [n,b] of [['main-browser.json',report],['actual-driver.cjs',originalDriver],['original-process.json',processes],['original-aggregate.cjs',originalAggregate],['original-stage-exits.json',stageExits]])fs.writeFileSync(path.join(dir,n),b,{flag:'wx'});
    reports.push(r);parts.push({...entry,earlierAttempt:attempt,originalProcessSHA256:sha(processes),originalDriverSHA256:r.scriptSha256,originalStageExitsSHA256:sha(stageExits)});
    fs.writeFileSync(path.join(root,'architecture-stage-exits.json'),JSON.stringify(parts,null,2)+'\n');
    if(process.argv.includes('--check-retained-only')&&name==='entrance')break;
    continue;
  }
  const original=path.join(dir,'actual-driver.cjs');fs.copyFileSync(driver,original);
  const work=spawnSync(process.execPath,[driver,...process.argv.slice(2)],{env:{...process.env,QA_OUTPUT_DIR:dir,BANK_ARCHITECTURE_SHOT:name},stdio:'inherit'});
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
  assert.equal(r.entry.status,200);assert.equal(r.entry.sha256,r.bindings['index.html']);
  assert.equal(r.views[0].sections.length,1);assert.equal(r.views[0].sections[0].segments,6);
  assert.deepEqual([...r.views[0].group.clip_feature_local_ids].sort((a,b)=>a-b),[53,1718,1782]);
  assert.equal(r.views[0].group.triangles,12);
  if(name==='crown'){assert.equal(r.ground.length,43);assert.ok(r.ground.every(q=>q.expected===q.found));}
  reports.push(r);
}
if(reports.length===4){
  for(const r of reports)for(const k of ['id','server','catalog','caseSha256','bindings'])assert.deepEqual(r[k],reports[0][k]);
  const flat=k=>reports.flatMap(r=>r[k]||[]);
  const out={...reports[3],scriptSha256:sha(fs.readFileSync(__filename)),entryRequests:reports.map(r=>r.entry),stageDriverSha256:sha(fs.readFileSync(driver)),stages:parts,started:reports[0].started,views:flat('views'),screenshots:flat('screenshots'),displayCaptures:flat('displayCaptures'),webglCaptures:flat('webglCaptures'),architecturalPixels:flat('architecturalPixels'),viewportCalibrations:reports.map(r=>r.viewportCalibration)};
  fs.writeFileSync(path.join(root,'main-browser.json'),JSON.stringify(out,null,2)+'\n');
}
