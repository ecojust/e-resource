"""Follow the ordinary model page on the final server, save the four downloadable assets and check the two requested levels on both screens."""
from pathlib import Path
from process_family import chrome_descendants, still_alive
import hashlib,json,subprocess,os,time,fcntl,shutil
from datetime import datetime,timezone
w=Path(__file__).parent;pr=Path('/workspace/e-resource/projects/shanghai');out=Path((w/'evidence-root.txt').read_text().strip())/'independent';out.mkdir(exist_ok=True);temp=max([Path('/run/codex-docker/user'),Path('/tmp'),Path('/dev/shm')],key=lambda p:shutil.disk_usage(p).free)/'m208-viewer';temp.mkdir(exist_ok=True)
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
previous=w/'physical-touch/physical-exit.json';close=json.loads(previous.read_bytes());assert close['exit_code']==0 and not close['remaining_chromium']
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 if r.exists():raise FileExistsError('Preserve the previous independent attempt before rerunning.')
 env=dict(os.environ,MODEL_BASE_URL='http://127.0.0.1:31208/',NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=str(temp))
 start=now();seen={}
 with(out/'viewer.log').open('wb')as log:
  p=subprocess.Popen(['node',pr/'tools/check-candidate-viewer.cjs','xuhui-picardie-apartments-south-front',out],cwd=pr,env=env,stdout=log,stderr=log)
  while p.poll()is None:seen.update(chrome_descendants(p.pid));time.sleep(.2)
 for k in range(60):
  if not live():break
  time.sleep(.10)
 assert seen and not live() and not still_alive(seen) and p.returncode==0
 d=json.loads(r.read_bytes());old=json.loads((pr/'data/audit/picardie-apartments-v1/viewer.json').read_bytes());assert d['passed'] and d['base']==env['MODEL_BASE_URL']
 assert set(d['downloads'])==set(old['downloads'])=={'raw','full','lod','native'}
 for role,item in d['downloads'].items():assert all(item[k]==old['downloads'][role][k]for k in ('file','bytes','sha256'))
 assert len(d['views'])==4 and not d['pageErrors']
 assert all(sha(out/v['filename'])==v['sha256']for v in d['views'])
 for v in d['views']:
  from PIL import Image
  im=Image.open(out/v['filename']).convert('RGB');assert max(c[1]-c[0]for c in im.getextrema())>48
 v=dict(order=208,phase='independent',passed=True,exit_code=0,started=start,finished=now(),node_pid=p.pid,observed_chromium_pid_and_starttime=seen,remaining_chromium=[],report=str(r),report_sha256=sha(r),predecessor_sha256=sha(previous),downloads=4,views=4)
 tmp=report.with_suffix('.part');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(report)
