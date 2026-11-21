"""Follow the ordinary model page on the final server, save the four downloadable assets and check the two requested levels on both screens."""
from pathlib import Path
import hashlib,json,subprocess,os,time,fcntl
from datetime import datetime,timezone
w=Path(__file__).parent;pr=Path('/workspace/e-resource/projects/shanghai');out=w/'isolated-evidence/independent';out.mkdir(exist_ok=True);temp=Path('/tmp/b228i');temp.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=lambda:datetime.now(timezone.utc).isoformat()
def live():
 result={}
 for f in Path('/proc').glob('[0-9]*/cmdline'):
  try:
   a=f.read_bytes().split(b'\0');s=(f.parent/'stat').read_text().rsplit(')',1)[1].split()
   if len(a)>1 and s[0]!='Z' and 'chrom' in os.fsdecode(a[0]) and str(temp).encode() in b' '.join(a):result[int(f.parent.name)]=s[19]
  except OSError:continue
 return result
r=out/'viewer.json';report=out/'closed.json'
if report.exists():
 d=json.loads(report.read_bytes());assert d['passed'] and sha(r)==d['report_sha256'];raise SystemExit(0)
previous=w/'isolated-evidence/distant/closed.json';close=json.loads(previous.read_bytes());assert close['exit_code']==0 and not close['remaining_chromium']
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 if r.exists():raise FileExistsError('Preserve the previous independent attempt before rerunning.')
 env=dict(os.environ,MODEL_BASE_URL='http://127.0.0.1:31228/',NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=str(temp))
 inputs=json.loads((w/'viewer-source-bindings.json').read_bytes());assert inputs['production_sha256']==sha(w/'228-production.json') and all(sha(w/'viewer-inputs'/f)==v['sha256'] for f,v in inputs['files'].items())
 start=now();seen={}
 with(out/'viewer.log').open('wb')as log:
  p=subprocess.Popen(['node',w/'check-actual-independent.cjs','xuhui-yanqing-road-130-residence',out],cwd=pr,env=env,stdout=log,stderr=log)
  import psutil
  parent=psutil.Process(p.pid)
  while p.poll()is None:
   try:
    for ch in parent.children(recursive=True):
     if ch.name() in ('chromium','chrome','chrome_crashpad_handler'):
      with open('/proc/'+str(ch.pid)+'/stat') as stat: seen[ch.pid]=stat.read().rsplit(')',1)[1].split()[19]
   except (psutil.NoSuchProcess,FileNotFoundError):pass
   seen.update(live());time.sleep(.1)
 for k in range(60):
  if not live():break
  time.sleep(.10)
 assert seen and not live() and p.returncode==0
 for pid,tick in seen.items():
  f=Path('/proc')/str(pid)/'stat'
  if f.is_file():
   try: content=f.read_text().rsplit(')',1)[1].split()
   except FileNotFoundError:continue
   assert content[0] in ('Z','X') or content[19]!=str(tick)
 d=json.loads(r.read_bytes());old=json.loads((w/'standalone-originals.json').read_bytes());assert d['passed'] and d['base']==env['MODEL_BASE_URL']
 assert d['scriptSHA256']==sha(w/'check-actual-independent.cjs') and all(v['savedAs']==v['file'] for v in d['actualSavedDownloads'].values()) and len(d['actualSavedDownloads'])==4;assert d['downloads']==old['downloads'];assert len(d['views'])==4 and not d['pageErrors']
 assert all(sha(out/v['filename'])==v['sha256']for v in d['views'])
 for v in d['views']:
  from PIL import Image
  im=Image.open(out/v['filename']).convert('RGB');assert max(c[1]-c[0]for c in im.getextrema())>48
 v=dict(order=228,phase='independent',passed=True,exit_code=0,started=start,finished=now(),node_pid=p.pid,observed_chromium_pid_and_starttime=seen,remaining_chromium=[],report=str(r),report_sha256=sha(r),predecessor_sha256=sha(previous),downloads=4,views=4)
 tmp=report.with_suffix('.part');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(report)
