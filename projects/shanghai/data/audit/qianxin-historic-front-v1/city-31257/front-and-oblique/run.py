import os,time,subprocess,json,hashlib,sys,datetime
from pathlib import Path
import psutil
w=Path(__file__).parent;os.chdir(w)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for device in ('desktop','phone'):
 start=now();tmp=w/(device+'-tmp');tmp.mkdir(exist_ok=True)
 with (w/(device+'-log.txt')).open('wb') as out:
  p=subprocess.Popen(['node','normal-two-views.cjs',device],stdout=out,stderr=subprocess.STDOUT,env={**os.environ,'TMPDIR':str(tmp),'OPENBLAS_NUM_THREADS':'1'});main=psutil.Process(p.pid);birth=main.create_time();seen={}
  while p.poll() is None:
   try:
    for c in main.children(recursive=True):
     try:seen[c.pid]=(c.name(),c.create_time())
     except psutil.NoSuchProcess:pass
   except psutil.NoSuchProcess:pass
   time.sleep(.06)
  code=p.wait()
 def living(pid,b):
  try:q=psutil.Process(pid);return q.create_time()==b and q.status()!=psutil.STATUS_ZOMBIE
  except psutil.NoSuchProcess:return False
 for _ in range(30):
  remaining=[pid for pid,(_,b) in seen.items() if living(pid,b)]
  if not remaining:break
  time.sleep(.1)
 c=w/(device+'-viewer.json');report=dict(device=device,started=start,finished=now(),node_pid=p.pid,node_birth=birth,node_closed=not living(p.pid,birth),exit_code=code,descendants=seen,remaining=remaining,report_sha256=sha(c) if c.exists() else None,log_sha256=sha(w/(device+'-log.txt')))
 (w/(device+'-closed.json')).write_text(json.dumps(report,indent=2)+'\n')
 if code or remaining:sys.exit(1)
