from pathlib import Path
import os,fcntl,json,hashlib,datetime,subprocess,tempfile,shutil,time
p=Path('/workspace/e-resource/projects/shanghai')
frozen=Path('/tmp/shanghai-following-key-sites/stage219/projects/shanghai')
work=Path('/tmp/jiangnan219')
audit=p/'data/audit/jiangnan-historic-general-office-v1'
out=work/'standalone-31219';out.mkdir(exist_ok=True);ident='huangpu-jiangnan-historic-general-office'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
read=lambda f:json.loads(f.read_bytes())
def bound(profile):
 rows=[]
 for f in Path('/proc').glob('[0-9]*/cmdline'):
  try:b=f.read_bytes()
  except OSError:continue
  if str(profile).encode()in b and b'chromium' in b: rows.append(int(f.parent.name))
 return rows
assert sha(work/'compact-verified-downloads.cjs')=='00d5fd76f577ef47e963f686497999592b162fe1cf6ff8207cc53223ad540ba1' and sha(audit/'check-webgl.cjs')=='a6b4b299066492ba8a975eb24493bdfacd223c1ca85555d32bb244efebe43e91'
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 scratch=max([Path('/tmp'),Path('/dev/shm')],key=lambda z:shutil.disk_usage(z).free)
 with tempfile.TemporaryDirectory(prefix='jiangnan219-independent-',dir=scratch)as short:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=short,MODEL_BASE_URL='http://127.0.0.1:31219/',SHANGHAI_PROJECT_ROOT=str(frozen))
  with(work/'independent-real.log').open('ab',buffering=0)as log:
   proc=subprocess.Popen(['node',work/'compact-verified-downloads.cjs',out],env=env,stdout=log,stderr=log,start_new_session=True)
   import psutil
   observed={}
   while proc.poll() is None:
    try:
     for child in psutil.Process(proc.pid).children(recursive=True):
      try:
       if child.name() in ('chromium','chrome','headless_shell'):observed[child.pid]=child.create_time()
      except psutil.Error:pass
    except psutil.Error:pass
    time.sleep(.15)
   rc=proc.returncode
  for _ in range(20):
   if not bound(short):break
   time.sleep(.3)
  def live(pid,born):
   try:
    active=psutil.Process(pid)
    return active.create_time()==born and active.status() not in (psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD)
   except psutil.NoSuchProcess:return False
  remaining=sorted(set(bound(short))|{pid for pid,born in observed.items() if live(pid,born)})
  report=out/'viewer.json'
  closed=dict(started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=proc.pid,exit=rc,
              chromium_remaining=remaining,remaining_chromium=remaining,report=str(report),
              report_sha256=sha(report) if report.exists() else None,formal_port=31219,
              chromium_pids=sorted(observed),chromium_birth_times=observed,node_closed=not psutil.pid_exists(proc.pid))
  def save_receipt(f):
   part=f.with_suffix('.writing')
   part.write_text(json.dumps(closed,indent=2)+'\n')
   part.replace(f)
  try:
   assert rc==0 and closed['node_closed'] and observed and not remaining,closed
   doc=read(report)
   assert doc['id']==ident and doc['base']==env['MODEL_BASE_URL'] and doc['passed'] and not doc['errors']
   assert len(doc['views'])==6
   assert {(v['device'],v['role'],v['pose']) for v in doc['views']}=={(d,r,v) for d in ['desktop','mobile'] for r,v in [('full','front'),('full','oblique'),('lod','above')]}
   assert len(doc['downloads'])==4 and all(sha(out/v['file'])==v['sha256'] for v in doc['views'])
   manifest=read(p/'assets/models/candidates'/ident/'manifest.json')
   assert all(all(doc['downloads'][k][field]==manifest['assets'][k][field] for field in ('file','sha256','bytes'))
              for k in ['raw','full','lod','native'])
  except Exception as error:
   archive=work/'standalone-attempts'/start.replace(':','-')
   archive.mkdir(parents=True)
   for item in out.iterdir():
    if item.is_file():os.link(item,archive/item.name)
   if report.is_file():closed['report']=str(archive/report.name)
   closed.update(passed=False,reason=repr(error))
   save_receipt(archive/'closed.json')
   for item in out.iterdir():
    if item.is_file():item.unlink()
   raise
  closed.update(passed=True,views=6,downloads=doc['downloads'])
  save_receipt(work/'standalone-closed.json')
 print('31219 separate viewer certified',flush=True)
