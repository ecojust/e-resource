const fs=require('node:fs');
const path=require('node:path');
const {spawnSync}=require('node:child_process');
const {createHash}=require('node:crypto');
const assert=require('node:assert/strict');
const root=process.env.QA_OUTPUT_DIR;
const digest=f=>createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const read=f=>JSON.parse(fs.readFileSync(f));
const put=(f,v)=>fs.writeFileSync(f,JSON.stringify(v,null,2)+'\n');
const reports=[];
for(const part of ['street','roof']){
  const dst=path.join(root,part);fs.mkdirSync(dst,{recursive:true});
  const driver=path.join(__dirname,'check-paired-placement.cjs');
  const time=new Date().toISOString();
  const job=spawnSync(process.execPath,[driver,...process.argv.slice(2)],{env:{...process.env,QA_OUTPUT_DIR:dst,QA_PLACEMENT_PAIR:part},stdio:'inherit'});
  const f=path.join(dst,'main-browser.json');const r=read(f);
  const close={part,pid:job.pid,exit:job.status,signal:job.signal,started:time,finished:new Date().toISOString(),completed:r.completed,report:f,report_sha256:digest(f),driver_sha256:digest(driver)};
  put(path.join(dst,'exit.json'),close);assert.equal(job.status,0);assert(r.completed&&r.finished&&!r.errors.length&&!r.failed.length);assert.equal(r.screenshots.length,2);
  reports.push(r);
}
const [a,b]=reports;
for(const k of ['catalog','bindings','camera','scriptSha256','caseSha256'])assert.deepEqual(a[k],b[k]);
assert(b.ground.every(v=>v.found===v.expected));
const merged={...b,started:a.started,placementPair:'two independently closed 408 by 550 sessions',subsessions:['street','roof'].map(p=>read(path.join(root,p,'exit.json')))};
for(const key of ['screenshots','views','warnings','errors','failed'])merged[key]=[...a[key],...b[key]];
const files=new Map();for(const f of [...a.files,...b.files]){const old=files.get(f.file);if(!old||!old.loadedByScene)files.set(f.file,f);}
merged.files=[...files.values()];
for(const r of reports)for(const shot of r.screenshots){const source=path.join(root,r.placementPair,shot.file);assert.equal(digest(source),shot.sha256);fs.linkSync(source,path.join(root,shot.file));}
put(path.join(root,'main-browser.json'),merged);
