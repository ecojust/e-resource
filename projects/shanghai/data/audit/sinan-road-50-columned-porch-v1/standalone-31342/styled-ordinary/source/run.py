import fcntl, tempfile, json, subprocess, os, hashlib, psutil, time, sys
from datetime import datetime,timezone
from pathlib import Path
d=Path(__file__).parent;work=d/'rendered';work.mkdir(exist_ok=True);w=Path(os.environ['SHANGHAI_342_CASE']).absolute()
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(w/'viewer-closed.json');f=Path(os.environ['SHANGHAI_VIEWER_SIGNED_INPUTS']).absolute();model=read(w/'raw-config.json')['id']
with open(os.environ.get('SHANGHAI_VIEWER_LOCK',str(Path(tempfile.gettempdir())/'shanghai-standalone-viewer.lock')),'a')as lock,tempfile.TemporaryDirectory(prefix='v342',dir=os.environ.get('SHANGHAI_TEMP_DIR'))as t:
 fcntl.flock(lock,fcntl.LOCK_EX)
 env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','TMPDIR':t,'SHANGHAI_VIEWER_SIGNED_INPUTS':str(f),'MODEL_BASE_URL':'http://127.0.0.1:31342/'}
 started=datetime.now(timezone.utc).isoformat();proc=subprocess.Popen([sys.executable,'-Bu',d/'run-342-devices.py',model,work],env=env);seen={}
 while proc.poll() is None:
  try:
   for c in psutil.Process(proc.pid).children(recursive=True):seen[c.pid]=[c.create_time(),c.name()]
  except psutil.Error:pass
  time.sleep(.10)
 remain=[]
 for pid,(born,name) in seen.items():
  try:
   c=psutil.Process(pid)
   if c.create_time()==born and c.status()!=psutil.STATUS_ZOMBIE:remain.append(pid)
  except psutil.Error:pass
 closed=dict(order=342,exit_code=proc.returncode,started=started,finished=datetime.now(timezone.utc).isoformat(),wrapper=proc.pid,observed_children=seen,remaining=remain,first_complete_six_images_sha256=sha(w/'viewer-closed.json'),host_receipt_sha256=r['host_receipt_sha256'],stylesheet_sha256=sha(Path(os.environ['SHANGHAI_PROJECT_ROOT'])/'src/dacheng-hall.css'),driver_sha256=sha(d/'six-view-download-live.cjs'));(work/'closed.json').write_text(json.dumps(closed,indent=2)+'\n');assert proc.returncode==0 and not remain
