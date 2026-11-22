/* Complete the three original file transfers after the four city cameras and
 * twelve collision observations were saved in the preceding physical runs. */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const {chromium}=require('/tmp/shanghai-main-231/cdp-city-page.cjs');
const sha=x=>createHash('sha256').update(x).digest('hex');
const exact=(p,hash)=>{const b=fs.readFileSync(p);if(hash)assert.equal(sha(b),hash,p);return b;};
const read=(p,hash)=>JSON.parse(exact(p,hash));
const w='/tmp/shanghai-main-231', out=process.env.QA_OUTPUT_DIR, previous=path.join(w,'evidence/231/previous-attempts');
const base='http://127.0.0.1:31231/';
const caseFile=process.argv[2], spec=read(caseFile);
const archive=(folder,hash)=>{
  const dir=path.join(previous,folder), r=read(path.join(dir,'main-browser.json'),hash), end=read(path.join(dir,'closed.json'));
  assert.equal(end.report_sha256,hash);assert(end.chromium_pids.length&&end.node_closed&&!end.remaining.length);
  assert.equal(r.scriptSha256,end.driver_sha256);exact(path.join(dir,'executed-driver.cjs'),r.scriptSha256);
  assert.equal(r.server,base);assert.equal(r.caseSha256,sha(exact(caseFile)));assert.equal(r.id,spec.id);
  return {dir,r,end};
};
(async()=>{
 const orig=archive('architecture-01-roof','01c1d2175d8763757e62b7668f9f2d01ae7e10881b4fbe0a3caa441766c620e9');
 const next=archive('architecture-03-final-image','72243bf3a6ddd27b554229bdded922353ce284f678a501b6818798d97905e392');
 const last=archive('architecture-04-all-images-and-ground','990f6561fb27ad4a66c46ef92e68afdd78d098237f52c11db4822c5764bc8800');
 const rows=last.r.views, images=last.r.screenshots;assert.equal(rows.length,4);assert.equal(images.length,4);
 assert.deepEqual(rows.map(x=>x.view),['map-street-facade','map-roof','map-three-street-portals','map-fluted-pilasters-and-window-bays']);
 const actuals=[orig,next,next,last];
 for(const [i,v] of rows.entries()){
   const parent=actuals[i];
   assert.deepEqual(v,parent.r.views.find(x=>x.view===v.view));
   assert(v.glError===0&&!v.contextLost&&v.asset.visible&&v.asset.status==='loaded'&&v.asset.variant==='full');
   assert(v.group.clip_feature_local_ids.includes(1876)&&v.group.triangles>0);
   assert(v.source.candidateModel||v.source.localModel);assert.deepEqual(v.neighbors.map(x=>x.local_id).sort((a,b)=>a-b),[733,1846]);
   const img=images.find(x=>x.file===v.view+'.png');assert(img);
   const b=exact(path.join(parent.dir,img.file),img.sha256);assert.equal(b.length,img.bytes);assert(b.subarray(0,8).equals(Buffer.from('89504e470d0a1a0a','hex')));
   fs.writeFileSync(path.join(out,img.file),b);
 }
 assert.equal(last.r.ground.length,12);assert(last.r.ground.every(x=>x.found===x.expected));
 const side=path.join(w,'evidence/231/separate/details'), ss=read(path.join(side,'closed.json')), mouse=read(path.join(side,'main-browser.json'),ss.report_sha256);
 assert(ss.exit===0&&ss.node_closed&&!ss.remaining.length&&mouse.completed&&mouse.server===base);
 assert.deepEqual(mouse.bindings,last.r.bindings);assert.deepEqual(mouse.catalog,last.r.catalog);
 const observed=rows.at(-1).asset.verifiedAsset;
 const originalFiles=[{file:observed.file,bytes:observed.bytes,sha256:observed.sha256,loadedByScene:true,sceneWitness:'four actual architecture views, matched against loaded asset identity and SHA'},...mouse.files.filter(x=>x.file.includes('/14-13721-6693/')&&x.loadedByScene).map(x=>({...x,sceneWitness:'completed pointer session and four owner-scoped source draws'}))];
 assert.equal(originalFiles.length,3);
 const doc={...last.r,started:new Date().toISOString(),completed:false,scriptSha256:sha(exact(__filename)),actualCdpProgramSha256:sha(exact(path.join(w,'cdp-city-page.cjs'))),files:[],sourcePhysicalRuns:actuals.filter((a,i,all)=>all.indexOf(a)===i).map(a=>({directory:path.basename(a.dir),node:a.end.node,chromium:a.end.chromium_pids,exit:a.end.exit,reportSha256:a.end.report_sha256,exitSha256:sha(exact(path.join(a.dir,'closed.json')))})),loadedFileWitness:sha(exact(path.join(side,'main-browser.json')))};
 delete doc.finished;delete doc.failureState;
 const save=()=>fs.writeFileSync(path.join(out,'main-browser.json'),JSON.stringify(doc,null,2)+'\n');save();
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--single-process','--no-zygote','--disable-gpu','--disable-extensions','--disable-background-networking','--disable-component-update','--remote-debugging-port='+process.env.QA_CDP_PORT]});
 try {
   const page=await browser.newPage({viewport:{width:450,height:320},deviceScaleFactor:1,hasTouch:false});
   const live=path.join(out,'verification-browser-start.json'), acknowledged=path.join(out,'external-observer.json');
   const starttime=fs.readFileSync('/proc/'+browser.physicalPid+'/stat','utf8').split(') ')[1].split(' ')[19];
   fs.writeFileSync(live,JSON.stringify({node:process.pid,pid:browser.physicalPid,starttime}));
   const deadline=Date.now()+20000;
   while(!fs.existsSync(acknowledged)&&Date.now()<deadline)await new Promise(resolve=>setTimeout(resolve,50));
   const witness=read(acknowledged);assert.equal(witness.node,process.pid);assert.equal(witness.pid,browser.physicalPid);assert.equal(witness.starttime,starttime);doc.externalObserver=witness;save();
   const manifestPath=observed.file.substring(0,observed.file.lastIndexOf('/')+1)+'manifest.json';
   await page.goto(base+manifestPath);
   for(const next of originalFiles){
     const capture=await page.evaluate(async url=>{const res=await fetch(url,{cache:'no-store'});const bytes=await res.arrayBuffer();const digest=await crypto.subtle.digest('SHA-256',bytes);return {status:res.status,url:res.url,bytes:bytes.byteLength,sha256:Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('')};},base+next.file);
     assert.equal(capture.status,200);assert.equal(capture.url,base+next.file);assert.equal(capture.bytes,next.bytes);assert.equal(capture.sha256,next.sha256);
     doc.files.push({...next,actualBrowserGet:capture});save();
   }
 }catch(error){doc.failure=String(error.stack||error);save();throw error;}
 finally{await browser.close();doc.fileVerificationProcess={pid:browser.physicalPid,exit:await browser.physicalExit()};}
 assert.equal(doc.fileVerificationProcess.exit.code,0);assert.equal(doc.files.length,3);
 doc.finished=new Date().toISOString();doc.completed=true;save();
})().catch(e=>{console.error(e);process.exitCode=1;});
