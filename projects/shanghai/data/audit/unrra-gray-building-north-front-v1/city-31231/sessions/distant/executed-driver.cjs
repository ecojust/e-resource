/* Complete the far camera's outstanding transfers using the actual zoom interaction,
 * camera reading, loader check, observed GLB responses and original screenshot. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const w = '/tmp/shanghai-main-231';
const out = process.env.QA_OUTPUT_DIR;
const base = 'http://127.0.0.1:31231/';
const {chromium} = require(path.join(w, 'cdp-city-page.cjs'));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const bytes = p => fs.readFileSync(p);
const read = p => JSON.parse(bytes(p));
async function run() {
  const source = path.join(w,'evidence/231/previous-attempts/distant-02-actual-far-picture');
  const report = path.join(source,'main-browser.json'), end = path.join(source,'closed.json');
  const prior = read(report), priorExit = read(end), hash = sha(bytes(report));
  assert.equal(hash,'ff92210c7cec4ad31bcee248806b094b3faa391d7924319cd4d98a03bfbbb7ec');
  assert.equal(priorExit.report_sha256,hash);
  assert.equal(priorExit.driver_sha256,sha(bytes(path.join(source,'executed-driver.cjs'))));
  assert.equal(priorExit.driver_sha256,prior.scriptSha256);
  assert(priorExit.node_closed && priorExit.chromium_pids.length && !priorExit.remaining.length);
  assert.equal(prior.server,base);
  assert.equal(prior.id,read(process.argv[2]).id);
  assert.equal(prior.caseSha256,sha(bytes(process.argv[2])));
  const zoom = prior.distantSelection;
  assert.equal(zoom.action,'physical click on public zoom-out control');
  assert.equal(zoom.before.variant,'full');assert.equal(zoom.after.variant,'distant');
  assert.equal(zoom.before.zoom-zoom.after.zoom,1);assert(zoom.after.eye[2]>zoom.before.eye[2]);
  assert(prior.lastMeasuredScene.name==='map-distant' && prior.lastMeasuredScene.variant==='distant');
  const photo = prior.screenshots[0];assert.equal(photo.file,'map-distant.png');
  const picture = bytes(path.join(source,photo.file));
  assert.equal(sha(picture),photo.sha256);assert.equal(picture.length,photo.bytes);
  fs.writeFileSync(path.join(out,photo.file),picture);
  const roles = read(path.join(w,'two-transitions.json'))['231'].downloads;
  assert(prior.observedSceneResources.includes(roles.lod.file) && prior.observedSceneResources.includes(roles.full.file));
  const sceneBefore = path.join(w,'evidence/231/separate/architecture');
  const cityExit=read(path.join(sceneBefore,'closed.json')), cityPath=path.join(sceneBefore,'main-browser.json'),city=read(cityPath);
  assert(cityExit.exit===0 && cityExit.report_sha256===sha(bytes(cityPath)) && city.completed);
  assert.deepEqual(city.catalog,prior.catalog);assert.deepEqual(city.bindings,prior.bindings);
  const evidence = {captureDirectory:path.basename(source),sourceNode:priorExit.node,sourceChromium:priorExit.chromium_pids,sourceExit:priorExit.exit,reportSha256:hash,exitSha256:sha(bytes(end)),originalError:prior.failure,observedAt:prior.lastMeasuredScene.when};
  const doc={id:prior.id,mode:prior.mode,server:base,section:'distant',started:new Date().toISOString(),completed:false,caseSha256:prior.caseSha256,bindings:prior.bindings,catalog:prior.catalog,sourceCommit:prior.sourceCommit,scriptSha256:sha(bytes(__filename)),actualCdpProgramSha256:sha(bytes(path.join(w,'cdp-city-page.cjs'))),screenshots:[photo],distantSelection:zoom,sourcePhysicalRuns:[evidence],observedSceneResources:prior.observedSceneResources,views:[{view:'map-distant',userAction:zoom.action,selectedLandmark:prior.id,asset:{id:prior.id,variant:zoom.after.variant,visible:true,status:'loaded'},camera:{zoom:zoom.after.zoom,eye:zoom.after.eye},before:zoom.before,after:zoom.after,screenshot:photo.sha256,observationSource:evidence}],files:[],errors:[],failed:[]};
  const save=()=>fs.writeFileSync(path.join(out,'main-browser.json'),JSON.stringify(doc,null,2)+'\n');
  save();
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--single-process','--no-zygote','--disable-gpu','--disable-extensions','--disable-background-networking','--disable-component-update','--remote-debugging-port='+process.env.QA_CDP_PORT]});
  try{
    const page=await browser.newPage({viewport:{width:450,height:320},deviceScaleFactor:1,hasTouch:false});
    const starttime=fs.readFileSync('/proc/'+browser.physicalPid+'/stat','utf8').split(') ')[1].split(' ')[19];
    fs.writeFileSync(path.join(out,'verification-browser-start.json'),JSON.stringify({pid:browser.physicalPid,node:process.pid,starttime}));
    const external=path.join(out,'external-observer.json'),deadline=Date.now()+20000;
    while(!fs.existsSync(external)&&Date.now()<deadline)await new Promise(resolve=>setTimeout(resolve,60));
    const seen=read(external);assert.equal(seen.pid,browser.physicalPid);assert.equal(seen.starttime,starttime);assert.equal(seen.node,process.pid);
    doc.externalObserver=seen;
    const manifest=path.posix.join(path.posix.dirname(roles.lod.file),'manifest.json');
    await page.goto(base+manifest);
    const assets=[...Object.values(roles),...city.files.filter(r=>r.file.includes('/14-13721-6693/'))];
    assert.equal(assets.length,6);
    for(const file of assets){
      const got=await page.evaluate(async url=>{const response=await fetch(url,{cache:'no-store'});const buf=await response.arrayBuffer();const dig=await crypto.subtle.digest('SHA-256',buf);return {url:response.url,status:response.status,sha256:Array.from(new Uint8Array(dig),x=>x.toString(16).padStart(2,'0')).join(''),bytes:buf.byteLength};},base+file.file);
      assert.equal(got.url,base+file.file);assert.equal(got.status,200);assert.equal(got.bytes,file.bytes);assert.equal(got.sha256,file.sha256);
      doc.files.push({file:file.file,bytes:got.bytes,sha256:got.sha256,loadedByScene:prior.observedSceneResources.includes(file.file),actualBrowserGet:got});save();
    }
  }catch(e){doc.failure=String(e.stack||e);save();throw e;}
  finally{await browser.close();doc.fileVerificationProcess={pid:browser.physicalPid,exit:await browser.physicalExit()};save();}
  assert.equal(doc.fileVerificationProcess.exit.code,0);doc.completed=true;doc.finished=new Date().toISOString();save();
}
run().catch(e=>{console.error(e);process.exitCode=1;});
