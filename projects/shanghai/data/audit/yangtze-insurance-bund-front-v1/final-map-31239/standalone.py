from pathlib import Path
import os,fcntl,json,hashlib,datetime,subprocess,tempfile,shutil,time
p=Path('/workspace/e-resource/projects/shanghai')
work=Path('/tmp/shanghai-main-239/final-map-31239')
audit=p/'data/audit/yangtze-insurance-bund-front-v1'
out=work/'standalone-31239';out.mkdir(exist_ok=True);ident='huangpu-yangtze-insurance-bund-front'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
read=lambda f:json.loads(f.read_bytes())
def bound(profile):
 rows=[]
 for f in Path('/proc').glob('[0-9]*/cmdline'):
  try:b=f.read_bytes()
  except OSError:continue
  if str(profile).encode()in b and b'chromium' in b: rows.append(int(f.parent.name))
 return rows
supplement=Path('/workspace/.e-resource-recovery/grace/reboot239/supplement-304.py')
assert sha(supplement)=='651cdfb7db3c53fa6b7d8662b5e3f1e716c459d204a51c2813549acc935e70b8'
assert read(work/'all-real-processes-closed.json')['phases']==7
subprocess.run([__import__('sys').executable,'-Bu',supplement,work/'distant/process.json'],check=True)
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 scratch=max([Path('/tmp'),Path('/dev/shm')],key=lambda z:shutil.disk_usage(z).free)
 with tempfile.TemporaryDirectory(prefix='yangtze239-independent-',dir=scratch)as short:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=short,MODEL_BASE_URL='http://127.0.0.1:31239/',SHANGHAI_PROJECT_ROOT=str(p))
  with(work/'independent-real.log').open('ab',buffering=0)as log:
   proc=subprocess.Popen(['node','-r',p/'data/audit/brunner-mond-v1/viewer-timeout.cjs',work/'actual-independent.cjs',out],env=env,cwd=p,stdout=log,stderr=log,start_new_session=True)
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
  report=out/'viewer.json';closed=dict(started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=proc.pid,chromium_pids=sorted(observed),remaining_observed=remaining,exit=rc,chromium_remaining=bound(short),report_sha256=sha(report)if report.exists()else None,formal_port=31239)
  (work/'standalone-closed.json').write_text(json.dumps(closed,indent=2)+'\n')
  assert rc==0 and observed and not remaining and not closed['chromium_remaining']
  doc=read(report);assert doc['id']==ident and doc['base']==env['MODEL_BASE_URL'] and doc['passed']
  assert {(v['device'],v['role'],v['pose'])for v in doc['views']}=={(device,role,pose) for device in ('desktop','mobile')for role,pose in [('full','front'),('full','oblique'),('lod','above')]}
  assert len(doc['downloads'])==4 and all(sha(out/v['file'])==v['sha256']for v in doc['views'])
  manifest=read(p/'assets/models/candidates'/ident/'manifest.json')
  assert all(doc['downloads'][k]['sha256']==manifest['assets'][k]['sha256']for k in ['raw','full','lod','native'])
 assert all(v['saveAsVerified'] and sha(out/v['saved'])==v['sha256'] for v in doc['downloads'].values())
 print('31239 separate viewer certified',flush=True)
