"""Use a physically closed 234 viewport as the single 299 graphics window."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import fcntl,json,sys,subprocess,os
q=Path(__file__).parent;j=Path('/tmp/jixian299');p=Path('/tmp/lianyi298');mode=sys.argv[1];closed=Path(sys.argv[2]);assert mode in ('native','viewer')
def read(f):return json.loads(f.read_bytes())
def sha(f):
 with f.open('rb') as s:return __import__('hashlib').file_digest(s,'sha256').hexdigest()
def write(f,obj):
 t=f.with_suffix('.partial');t.write_text(json.dumps(obj,indent=2)+'\n');os.replace(t,f)
prev=read(closed);assert prev['node_closed'] and prev['exit_code']==0 and prev['chromium_pids'] and prev['remaining_children']==prev['remaining_chromium']==[]
assert sha(closed.parent/('control-browser.json' if mode=='native' else 'main-browser.json'))==prev['report_sha256']
checks=[(p/'native-closed.json','native'),(p/'raw-298-confirmed.json','raw')]
if mode=='viewer':checks.extend([(p/'viewer-closed.json','viewer'),(j/'native-closed.json','self'),(j/'physical-299.json','physical')])
miss=[]
for f,kind in checks:
 if not f.is_file():miss.append(str(f));continue
 rec=read(f);assert rec.get('order',299 if kind in ['self','physical']else 298)==(299 if kind in ['self','physical']else 298)
 if kind=='raw':assert rec['count'] and Path(rec['root']).is_dir() and sha(Path(rec['snapshot']))==rec['sha256']
 elif kind=='physical':assert rec['passed']
 else:assert rec['passed'] and rec.get('exit',rec.get('exit_code'))==0 and not rec.get('remaining_chromium',[])and not rec.get('remaining_blender',[])
state=dict(order=299,mode=mode,previous_session=str(closed),previous_session_sha256=sha(closed),previous_browser_report_sha256=prev['report_sha256'],remaining_chromium=[],time=datetime.now(timezone.utc).isoformat())
if miss:
 write(q/f'299-{mode}-deferred.json',{**state,'deferred':True,'missing':miss,'blender_started':False,'chromium_started':False});sys.exit()
job=j/('run-native.py'if mode=='native' else'run-viewer.py');assert job.is_file(),job
with(q/f'299-{mode}.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);good=j/(mode+'-closed.json')
 if not good.is_file():
  write(q/f'299-{mode}-window.json',{**state,'authorized':True})
  subprocess.run([sys.executable,'-Bu',job],check=True)
 r=read(good);assert r['order']==299 and r['passed']and r['exit']==0 and not r.get('remaining_blender',[])and not r.get('remaining_chromium',[])
