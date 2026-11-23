from pathlib import Path
from datetime import datetime,timezone
import subprocess,os,json,psutil,time,hashlib
here=Path(__file__).resolve().parent
import tempfile
w=Path(os.environ.get('ORDINARY_OUTPUT') or tempfile.mkdtemp(prefix='jianguo629-ui-')).resolve()
w.mkdir(parents=True,exist_ok=True)
env=dict(os.environ)
for key,folder in {'XDG_CONFIG_HOME':'config','XDG_CACHE_HOME':'cache','XDG_RUNTIME_DIR':'runtime','ORDINARY_SAVED':'saved','ORDINARY_DOWNLOAD_STAGING':'staging'}.items():
 dest=w/folder; dest.mkdir(exist_ok=True,mode=0o700);env[key]=str(dest)
if not env.get('ORDINARY_ROOT'):
    env['ORDINARY_ROOT']=str(next(d for d in here.parents if (d/'vendor/three.module.js').is_file()))
from shutil import which
env.setdefault('CHROMIUM_PATH',which('chromium') or which('chromium-browser') or 'chromium')
print('Browser reports:',w,flush=True)
start=datetime.now(timezone.utc).isoformat()
with (w/'run.log').open('wb') as f:
 p=subprocess.Popen(['node',here/'test.cjs'],cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT)
 observed={}
 while p.poll() is None:
  try:
   for c in psutil.Process(p.pid).children(recursive=True):
    try:observed[(c.pid,c.create_time())]=c.name()
    except psutil.Error:pass
  except psutil.Error:pass
  time.sleep(.05)
def alive(pid,birth):
 try:q=psutil.Process(pid);return q.create_time()==birth and q.status()!='zombie'
 except psutil.Error:return False
remaining=[k[0] for k,v in observed.items() if alive(*k)]
report=w/'report.json'
(w/'closed.json').write_text(json.dumps(dict(exit=p.returncode,node=p.pid,started=start,finished=datetime.now(timezone.utc).isoformat(),chrome_pids=[k[0]for k,v in observed.items()if v=='chromium'],remaining=remaining,report_sha256=hashlib.sha256(report.read_bytes()).hexdigest()if report.exists()else None),indent=2)+'\n')
assert not remaining and p.returncode==0 and report.is_file()
