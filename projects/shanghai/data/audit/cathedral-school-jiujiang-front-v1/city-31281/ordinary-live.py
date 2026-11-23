from pathlib import Path
import os,fcntl,json,hashlib,datetime,subprocess,tempfile,shutil,time
p=Path('/workspace/e-resource/projects/shanghai')
work=Path('/tmp/shanghai-main-281/formal-31281')
audit=p/'data/audit/cathedral-school-jiujiang-front-v1'
out=work/'current-standalone-31281';out.mkdir(exist_ok=True);ident='huangpu-cathedral-school-jiujiang-front'
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
 scratch=Path('/dev/shm/jiujiang281-live/profiles')
 with tempfile.TemporaryDirectory(prefix='v-',dir=scratch)as short:
  short="/tmp/g80/work/jiujiang281/profiles/"+Path(short).name
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=short,MODEL_BASE_URL='http://127.0.0.1:31281/',SHANGHAI_VIEWER_SIGNED_INPUTS='/tmp/g80/work/jiujiang281/work/current-viewer-inputs',XDG_CACHE_HOME=short+'/ca',XDG_CONFIG_HOME=short+'/cfg',CHROME_CONFIG_HOME=short+'/cfg',MALLOC_ARENA_MAX='1',LP_NUM_THREADS='1')
  with(work/'independent-real.log').open('ab',buffering=0)as log:
   proc=subprocess.Popen(['nsenter','--preserve-credentials','--user','--mount','--target','3609719','--','node','-r',p/'data/audit/brunner-mond-v1/viewer-timeout.cjs',work/'school-viewer-live.cjs',ident,'/tmp/g80/work/jiujiang281/work/current-standalone'],env=env,cwd=p,stdout=log,stderr=log,start_new_session=True)
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
  report=out/'viewer.json';closed=dict(started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=proc.pid,chromium_pids=sorted(observed),remaining_observed=remaining,exit=rc,chromium_remaining=bound(short),report_sha256=sha(report)if report.exists()else None,formal_port=31281)
  closed.update(order=281,passed=rc==0 and bool(observed) and not remaining and not closed['chromium_remaining'],remaining_chromium=remaining,node_closed=not Path('/proc/'+str(proc.pid)).exists())
  (work/'current-standalone-closed.json').write_text(json.dumps(closed,indent=2)+'\n')
  assert rc==0 and observed and not remaining and not closed['chromium_remaining']
  doc=read(report);assert doc['id']==ident and doc['base']==env['MODEL_BASE_URL'] and doc['passed']
  assert len(doc['views'])==6 and {(v['viewport'][0] if isinstance(v['viewport'],list) else v['viewport']['width']) for v in doc['views']}=={390,1250}
  assert all(sum(1 for v in doc['views'] if (v['viewport'][0] if isinstance(v['viewport'],list) else v['viewport']['width'])==width and v['role']==role)==count for width in (390,1250) for role,count in [('full',3 if width==1250 else 1),('lod',1)])
  assert len(doc['downloads'])==4 and all(sha(out/v.get('filename',v.get('file')))==v['sha256'] for v in doc['views'])
  manifest=read(p/'assets/models/candidates'/ident/'manifest.json')
  assert all(doc['downloads'][k]['sha256']==manifest['assets'][k]['sha256']for k in ['raw','full','lod','native'])
 print('31281 separate viewer certified',flush=True)

for entry in doc['downloads'].values():
 saved=out/'saved'/entry['file']
 assert entry['actualSaved'] and saved.stat().st_size==entry['bytes'] and sha(saved)==entry['sha256']

alias=work/'standalone-31281'
original=work/'standalone-before-current-281'
if not original.is_symlink():
 assert alias.is_symlink() and alias.resolve()!=out.resolve()
 original.symlink_to(os.readlink(alias),target_is_directory=True)
assert original.resolve().is_dir()
next_alias=work/'standalone-31281.new'
next_alias.symlink_to(out, target_is_directory=True)
next_alias.replace(alias)
assert sha(alias/'viewer.json')==closed['report_sha256']
