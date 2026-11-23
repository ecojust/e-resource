from pathlib import Path
import os,fcntl,json,hashlib,datetime,subprocess,tempfile,shutil,time
p=Path('/workspace/e-resource/projects/shanghai')
work=Path('/tmp/shanghai-main-269/formal-31269')
audit=p/'data/audit/chekiang-industrial-bank-beijing-front-v1'
out=work/'standalone-31269';out.mkdir(exist_ok=True);ident='huangpu-chekiang-industrial-bank-beijing-front'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
read=lambda f:json.loads(f.read_bytes())
def bound(profile):
 rows=[]
 for f in Path('/proc').glob('[0-9]*/cmdline'):
  try:b=f.read_bytes()
  except OSError:continue
  if str(profile).encode()in b and b'chromium' in b: rows.append(int(f.parent.name))
 return rows
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 scratch=max([Path('/tmp'),Path('/dev/shm')],key=lambda z:shutil.disk_usage(z).free)
 with tempfile.TemporaryDirectory(prefix='bank269-independent-',dir=scratch)as short:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=short,MODEL_BASE_URL='http://127.0.0.1:31269/',SHANGHAI_PROJECT_ROOT='/workspace/shanghai-publisher-preservation/city-269/signed-ordinary-viewer')
  with(work/'independent-real.log').open('ab',buffering=0)as log:
   proc=subprocess.Popen(['node','-r',p/'data/audit/brunner-mond-v1/viewer-timeout.cjs',work/'six-view-four-downloads.cjs',ident,out],env=env,cwd=p,stdout=log,stderr=log,start_new_session=True)
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
  report=out/'viewer.json';closed=dict(started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=proc.pid,chromium_pids=sorted(observed),remaining_observed=remaining,exit=rc,chromium_remaining=bound(short),report_sha256=sha(report)if report.exists()else None,formal_port=31269)
  closed.update(order=269,exit_code=rc,node_closed=proc.poll() is not None,remaining_chromium=sorted(set(remaining+closed['chromium_remaining'])))
  if rc!=0 or remaining or closed['chromium_remaining']:
   (work/'standalone-failed.json').write_text(json.dumps(closed,indent=2)+'\n')
  assert rc==0 and observed and not remaining and not closed['chromium_remaining']
  doc=read(report);assert doc['id']==ident and doc['base']==env['MODEL_BASE_URL'] and doc['passed']
  assert len(doc['views'])==6 and {v['viewport']['width'] for v in doc['views']}=={390,1250}
  assert sorted((v['viewport']['width'],v['role'])for v in doc['views'])==sorted((v['viewport']['width'],v['role'])for v in read(audit/'viewer.json')['views'])
  assert len(doc['downloads'])==4 and all(sha(out/v['filename'])==v['sha256'] for v in doc['views'])
  manifest=read(Path('/workspace/shanghai-publisher-preservation/city-269/signed-ordinary-viewer')/'assets/models/candidates'/ident/'manifest.json')
  assert all(doc['downloads'][k]['sha256']==manifest['assets'][k]['sha256']for k in ['raw','full','lod','native'])
  for k,item in doc['downloads'].items():
   saved=out/item['saved'];assert item['saveAsVerified'] and sha(saved)==manifest['assets'][k]['sha256'] and saved.stat().st_size==item['bytes']
  closed.update(passed=True,physical_exit=True,views=6,downloads=4)
  (work/'standalone-closed.json').write_text(json.dumps(closed,indent=2)+'\n')
 print('31269 separate viewer certified',flush=True)
