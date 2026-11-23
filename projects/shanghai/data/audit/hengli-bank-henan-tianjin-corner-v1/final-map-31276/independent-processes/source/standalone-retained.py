from pathlib import Path
import os,fcntl,json,hashlib,datetime,subprocess,tempfile,shutil,time
p=Path('/workspace/e-resource/projects/shanghai')
work=Path('/tmp/shanghai-main-276/final-map-31276')
audit=p/'data/audit/hengli-bank-henan-tianjin-corner-v1'
out=work/'standalone-31276';out.mkdir(exist_ok=True);ident='huangpu-hengli-bank-henan-tianjin-corner'
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
 with tempfile.TemporaryDirectory(prefix='yangtze276-independent-',dir=scratch)as short:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=short,MODEL_BASE_URL='http://127.0.0.1:31276/',SHANGHAI_PROJECT_ROOT='/dev/shm/hengli276-new-artifacts/standalone-frozen-root')
  with(work/'independent-real.log').open('ab',buffering=0)as log:
   proc=subprocess.Popen(['node','-r',p/'data/audit/brunner-mond-v1/viewer-timeout.cjs',work/'verify-standalone-retained.cjs',out],env=env,cwd=p,stdout=log,stderr=log,start_new_session=True)
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
  report=out/'viewer.json';closed=dict(started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=proc.pid,chromium_pids=sorted(observed),remaining_observed=remaining,exit=rc,chromium_remaining=bound(short),report_sha256=sha(report)if report.exists()else None,formal_port=31276)
  (work/'standalone-closed.json').write_text(json.dumps(closed,indent=2)+'\n')
  assert rc==0 and observed and not remaining and not closed['chromium_remaining']
  doc=read(report);assert doc['id']==ident and doc['base']==env['MODEL_BASE_URL'] and doc['passed']
  assert len(doc['views'])==6 and {(v['viewport'][0] if isinstance(v['viewport'],list) else v['viewport']['width']) for v in doc['views']}=={390,1250}
  assert all(sum(1 for v in doc['views'] if (v['viewport'][0] if isinstance(v['viewport'],list) else v['viewport']['width'])==width and v['role']==role)==count for width in (390,1250) for role,count in [('full',2),('lod',1)])
  assert len(doc['downloads'])==4 and all(sha(out/v.get('filename',v.get('file')))==v['sha256'] for v in doc['views'])
  manifest=read(p/'assets/models/candidates'/ident/'manifest.json')
  assert all(doc['downloads'][k]['sha256']==manifest['assets'][k]['sha256']for k in ['raw','full','lod','native'])
 print('31276 separate viewer certified',flush=True)

for role,entry in doc['downloads'].items():
 saved=out/'saved'/entry['file']
 assert entry['saveAsVerified'] and saved.stat().st_size==entry['bytes'] and sha(saved)==entry['sha256']
