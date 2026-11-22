"""Follow the ordinary model page on the final server, save the four downloadable assets and check the two requested levels on both screens."""
from pathlib import Path
import hashlib,json,subprocess,os,time,fcntl
from datetime import datetime,timezone
w=Path(__file__).parent;pr=Path('/workspace/e-resource/projects/shanghai');out=w/'isolated-evidence/independent';out.mkdir(exist_ok=True);temp=Path('/dev/shm/v232p');temp.mkdir(exist_ok=True)
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
 env=dict(os.environ,MODEL_BASE_URL='http://127.0.0.1:31232/',NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=str(temp))
 from urllib.request import urlopen
 from hashlib import sha256
 mpath='assets/models/candidates/xuhui-zikawei-convent-central-front/manifest.json'
 production=json.loads((w/'232-production.json').read_bytes())
 frozen=w/'standalone-232-frozen'
 def get(k):
  with urlopen(env['MODEL_BASE_URL']+k,timeout=25)as rr:
   assert rr.status==200
   b=rr.read()
  assert sha256(b).hexdigest()==production['files'][k],k
  t=frozen/k;t.parent.mkdir(exist_ok=True,parents=True)
  if t.is_file():assert sha(t)==production['files'][k]
  else:t.write_bytes(b)
  return b
 manifest=json.loads(get(mpath));route=manifest['viewer_page'];get(route);get('src/candidate-asset-viewer.js')
 start=now();seen={}
 with(out/'viewer.log').open('wb')as log:
  p=subprocess.Popen(['node',w/'check-232-viewer.cjs','xuhui-zikawei-convent-central-front',out],cwd=pr,env=env,stdout=log,stderr=log)
  while p.poll()is None:seen.update(live());time.sleep(.2)
 for k in range(60):
  if not live():break
  time.sleep(.10)
 assert seen and not live() and p.returncode==0
 d=json.loads(r.read_bytes());old=json.loads((w/'standalone-originals.json').read_bytes());assert d['passed'] and d['base']==env['MODEL_BASE_URL']
 assert set(d['downloads'])==set(old['downloads'])=={'raw','full','lod','native'}
 for role,entry in d['downloads'].items():
  assert {k:entry[k] for k in ('file','bytes','sha256')}==old['downloads'][role] and entry['actualSaved'] and entry['saveAsVerified']
 assert d['manifestSHA256']==old['manifest_sha256']
 assert all(d['files'][k]==production['files'][k]for k in (route,'src/candidate-asset-viewer.js'))
 assert len(d['views'])==4 and not d['pageErrors']
 assert all(sha(out/v['filename'])==v['sha256']for v in d['views'])
 for v in d['views']:
  from PIL import Image
  im=Image.open(out/v['filename']).convert('RGB');assert max(c[1]-c[0]for c in im.getextrema())>48
 v=dict(order=232,phase='independent',passed=True,exit_code=0,started=start,finished=now(),node_pid=p.pid,observed_chromium_pid_and_starttime=seen,remaining_chromium=[],report=str(r),report_sha256=sha(r),predecessor_sha256=sha(previous),downloads=4,actual_saved_downloads=d['downloads'],viewer_inputs={k:production['files'][k] for k in (mpath,route,'src/candidate-asset-viewer.js')},views=4)
 tmp=report.with_suffix('.part');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(report)
