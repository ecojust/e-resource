from pathlib import Path
import os,fcntl,json,hashlib,datetime,subprocess,tempfile,shutil,time
p=Path('/workspace/e-resource/projects/shanghai')
work=Path('/tmp/shanghai-main-268/final-map-31268')
audit=p/'data/audit/somekh-building-street-corner-v1'
out=work/'standalone-31268';out.mkdir(exist_ok=True);ident='huangpu-somekh-building-street-corner'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
read=lambda f:json.loads(f.read_bytes())
def bound(profile):
 rows=[]
 for f in Path('/proc').glob('[0-9]*/cmdline'):
  try:b=f.read_bytes()
  except OSError:continue
  if str(profile).encode()in b and b'chromium' in b: rows.append(int(f.parent.name))
 return rows
from urllib.request import urlopen
isolated=work/'immutable-exhibit-inputs'
book=read(work/'bound-inputs.json')['268']
for rel in ['somekh-building-street-corner.html', 'src/candidate-asset-viewer.js','assets/models/candidates/'+ident+'/manifest.json']:
  fixed=book['fetched'][rel];dest=isolated/rel;dest.parent.mkdir(parents=True,exist_ok=True)
  with urlopen(book['origin']+rel,timeout=80) as response:assert response.status==200;raw=response.read()
  assert len(raw)==fixed['bytes'] and hashlib.sha256(raw).hexdigest()==fixed['sha256']
  if dest.exists():assert dest.read_bytes()==raw
  else:dest.write_bytes(raw)
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 scratch=max([Path('/tmp'),Path('/dev/shm')],key=lambda z:shutil.disk_usage(z).free)
 with tempfile.TemporaryDirectory(prefix='yangtze268-independent-',dir=scratch)as short:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=short,MODEL_BASE_URL='http://127.0.0.1:31268/',SHANGHAI_PROJECT_ROOT=str(isolated))
  with(work/'independent-real.log').open('ab',buffering=0)as log:
   proc=subprocess.Popen(['node','-r',p/'data/audit/brunner-mond-v1/viewer-timeout.cjs',work/'somekh-four-saveas.cjs',ident,out],env=env,cwd=p,stdout=log,stderr=log,start_new_session=True)
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
  report=out/'viewer.json';closed=dict(started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=proc.pid,chromium_pids=sorted(observed),remaining_observed=remaining,exit=rc,chromium_remaining=bound(short),report_sha256=sha(report)if report.exists()else None,formal_port=31268)
  (work/'standalone-closed.json').write_text(json.dumps(closed,indent=2)+'\n')
  assert rc==0 and observed and not remaining and not closed['chromium_remaining']
  doc=read(report);assert doc['id']==ident and doc['base']==env['MODEL_BASE_URL'] and doc['passed']
  assert len(doc['views'])==6 and {v['viewport']['width'] for v in doc['views']}=={390,1250}
  assert sorted((v['viewport']['width'],v['role'])for v in doc['views'])==sorted((v['viewport']['width'],v['role'])for v in read(audit/'standalone-31268/viewer.json')['views'])
  assert len(doc['downloads'])==4 and all(sha(out/v['filename'])==v['sha256'] for v in doc['views'])
  manifest=read(isolated/'assets/models/candidates'/ident/'manifest.json')
  assert all(doc['downloads'][k]['sha256']==manifest['assets'][k]['sha256']for k in ['raw','full','lod','native'])
  for role,item in doc['downloads'].items():
   f=out/item['saved'];assert item['saveAsVerified'] and sha(f)==manifest['assets'][role]['sha256'] and f.stat().st_size==item['bytes']
 print('31268 separate viewer certified',flush=True)
