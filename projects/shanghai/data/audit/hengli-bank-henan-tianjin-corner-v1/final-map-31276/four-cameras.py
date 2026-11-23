"""Run each of the four surveyed architecture cameras in a fresh Chromium session."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,os,sys,time,psutil,shutil
w=Path(__file__).parent;out=w/'architecture';stamp=lambda:datetime.now(timezone.utc).isoformat();h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda f:json.loads(f.read_bytes())
def save(f,j):f.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
parts=[];reports=[];allnodes=[];allchrome=[]
for part in ('street','roof','portal','upper'):
 d=out/'captures'/part;d.mkdir(parents=True,exist_ok=True);report=d/'main-browser.json';receipt=d/'closed.json'
 if not receipt.exists():
  assert not report.exists(),d
  local=d/'actual-driver.cjs'
  if not local.exists():shutil.copyfile(w/'check-hengli-camera.cjs',local)
  assert h(local)==h(w/'check-hengli-camera.cjs')
  t=stamp();proc=subprocess.Popen([sys.executable,'-Bu',w/'run-live.py','architecture'],env={**os.environ,'QA_ARCH_PART':part});children={}
  while proc.poll() is None:
   try:kids=psutil.Process(proc.pid).children(recursive=True)
   except psutil.Error:kids=[]
   for p in kids:
    try:children[p.pid]=(p.create_time(),p.name())
    except psutil.Error:pass
   time.sleep(.12)
  exited=[]
  for pid,(born,name)in children.items():
   try:p=psutil.Process(pid);live=p.create_time()==born and p.status()!=psutil.STATUS_ZOMBIE
   except psutil.Error:live=False
   if live:exited.append(pid)
  raw=dict(phase='architecture',camera=part,started=t,finished=stamp(),exit_code=proc.returncode,remaining=exited,
     node_pids=[i for i,(_,n)in children.items()if n in ('MainThread','node','nodejs')],chromium_pids=[i for i,(_,n)in children.items()if n in ('chromium','chrome')],report_sha256=h(report)if report.exists()else None,driver_sha256=h(w/'check-hengli-camera.cjs'))
  save(receipt,raw)
 r=read(receipt);assert r['exit_code']==0 and not r['remaining'] and r['node_pids'] and r['chromium_pids'] and h(report)==r['report_sha256'],r
 j=read(report);assert h(d/'actual-driver.cjs')==r['driver_sha256'];assert j['completed'] and j['scriptSha256']==r['driver_sha256'] and len(j['screenshots'])==1 and not j['errors'] and not j['failed']
 parts.append(r);reports.append(j);allnodes.extend(r['node_pids']);allchrome.extend(r['chromium_pids'])
 for img in d.glob('*.png'):
  dest=out/img.name
  if img.name.startswith('viewport-calibration')and part!='street':continue
  if not dest.exists():os.link(img,dest)
  assert h(img)==h(dest)
combined=dict(reports[0])
for j in reports[1:]:
 for k in ('caseSha256','sourceCommit','bindings','servedRuntime','server','catalog','ground'):assert j[k]==combined[k],(k,part)
for k in ('views','screenshots','displayCaptures','webglCaptures','architecturalPixels','warnings'):
 combined[k]=[i for j in reports for i in j.get(k,[])]
assert len(combined['ground'])==62 and len(combined['screenshots'])==4 and len(combined['architecturalPixels'])==2
combined['scriptSha256']=h(out/'actual-driver.cjs')
assert reports[-1]['scriptSha256']==combined['scriptSha256']
combined['assembly']={'type':'independently captured cameras','camera_script_sha256':{r['camera']:r['driver_sha256'] for r in parts},'latest_accepted_script_sha256':combined['scriptSha256'],'combiner_sha256':h(Path(__file__))}
combined['finished']=reports[-1]['finished'];combined['camera_sessions']=parts
target=out/'main-browser.json';save(target,combined)
save(out/'process.json',dict(order=276,phase='architecture',report=str(target),report_sha256=h(target),driver_sha256=h(out/'actual-driver.cjs'),exit_code=0,node_pids=allnodes,chromium_pids=allchrome,node_closed=True,remaining_children=[],remaining_chromium=[],started=parts[0]['started'],finished=parts[-1]['finished'],camera_sessions=parts))
(w/'architecture.exit').write_text('0\n')
