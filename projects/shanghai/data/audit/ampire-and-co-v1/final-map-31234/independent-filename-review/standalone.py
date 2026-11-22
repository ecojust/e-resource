from pathlib import Path
import os,fcntl,json,hashlib,datetime,subprocess,tempfile,shutil,time
p=Path('/workspace/e-resource/projects/shanghai')
work=Path('/tmp/shanghai-main-234/final-map-31234')
audit=p/'data/audit/ampire-and-co-v1'
out=work/'standalone-31234';out.mkdir(exist_ok=True);ident='huangpu-ampire-and-co-building'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
read=lambda f:json.loads(f.read_bytes())
def bound(profile):
 rows=[]
 for f in Path('/proc').glob('[0-9]*/cmdline'):
  try:b=f.read_bytes()
  except OSError:continue
  if str(profile).encode()in b and b'chromium' in b: rows.append(int(f.parent.name))
 return rows
signed=work/'standalone-signed'
subprocess.run([os.sys.executable,'-Bu',signed/'signed-inputs.py'],check=True)
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 scratch=max([Path('/tmp'),Path('/dev/shm')],key=lambda z:shutil.disk_usage(z).free)
 with tempfile.TemporaryDirectory(prefix='ampire234-independent-',dir=scratch)as short:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=short,MODEL_BASE_URL='http://127.0.0.1:31234/',SHANGHAI_PROJECT_ROOT=str(signed))
  with(work/'independent-real.log').open('ab',buffering=0)as log:
   proc=subprocess.Popen(['node','-r',p/'data/audit/brunner-mond-v1/viewer-timeout.cjs',work.parent/'signed-four-downloads.cjs',ident,out],env=env,cwd=p,stdout=log,stderr=log,start_new_session=True)
   from psutil import Process, NoSuchProcess
   observed={}
   while proc.poll() is None:
    try:
     for child in Process(proc.pid).children(recursive=True):
      try:
       if child.name() in ('chromium','chrome'):observed[child.pid]=child.create_time()
      except NoSuchProcess:pass
    except NoSuchProcess:pass
    time.sleep(.18)
   rc=proc.returncode
   remaining=[]
   for pid,born in observed.items():
    try:
     child=Process(pid)
     if child.create_time()==born and child.status() not in ('zombie','dead'):remaining.append(pid)
    except NoSuchProcess:pass
  for _ in range(20):
   if not bound(short):break
   time.sleep(.3)
  report=out/'viewer.json';closed=dict(started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=proc.pid,chromium_pids=sorted(observed),remaining_observed=remaining,exit=rc,chromium_remaining=bound(short),report_sha256=sha(report)if report.exists()else None,formal_port=31234)
  (work/'standalone-closed.json').write_text(json.dumps(closed,indent=2)+'\n')
  assert rc==0 and observed and not remaining and not closed['chromium_remaining']
  doc=read(report);assert doc['id']==ident and doc['base']==env['MODEL_BASE_URL'] and doc['passed']
  assert {v['filename']for v in doc['views']}=={'viewer-'+device+'-'+role+'.png'for device in ('desktop','mobile')for role in ('full','lod')}
  assert len(doc['downloads'])==4 and all(sha(out/v['filename'])==v['sha256']for v in doc['views'])
  manifest=read(signed/'assets/models/candidates'/ident/'manifest.json')
  for role,asset in manifest['assets'].items():
   item=doc['downloads'][role];actual=out/item['saved']
   assert item['saveAsVerified'] and actual.name==item['file']==asset['file'] and sha(actual)==item['sha256']==asset['sha256']and actual.stat().st_size==item['bytes']==asset['bytes']
  closed['source_inputs']=str(signed/'source-inputs.json');closed['source_inputs_sha256']=sha(signed/'source-inputs.json')
  closed['driver_sha256']=sha(work.parent/'signed-four-downloads.cjs')
  (work/'standalone-closed.json').write_text(json.dumps(closed,indent=2)+'\n')
 print('31234 separate viewer certified',flush=True)
