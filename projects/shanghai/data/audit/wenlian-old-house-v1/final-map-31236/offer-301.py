"""Use a physically closed 236 viewport as the single 301 graphics window."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import fcntl,json,sys,subprocess,os
q=Path(__file__).parent;j=Path('/tmp/qianguild301');p=Path('/tmp/xiaonanmen300');mode=sys.argv[1];closed=Path(sys.argv[2]);assert mode in ('native','viewer')
def read(f):return json.loads(f.read_bytes())
def sha(f):
 with f.open('rb') as s:return __import__('hashlib').file_digest(s,'sha256').hexdigest()
def write(f,obj):
 t=f.with_suffix('.partial');t.write_text(json.dumps(obj,indent=2)+'\n');os.replace(t,f)
prev=read(closed);assert prev['node_closed'] and prev['exit_code']==0 and prev['chromium_pids'] and prev['remaining_children']==prev['remaining_chromium']==[]
assert sha(closed.parent/('control-browser.json' if mode=='native' else 'main-browser.json'))==prev['report_sha256']
# Only the original publisher writes this after the two recorded public commits have been read back.
import time, re
master=Path('/workspace/shanghai-publisher-preservation/235-master-confirmed.json')
while not master.is_file():time.sleep(1)
release=read(master)
assert release['order']==235 and release['passed'] and release['normal_https_verified']
assert all(re.fullmatch(r'[0-9a-f]{40}',release[k]) for k in ('master','model_commit'))
if mode=='native':
    decision=q/'522-admission-after-before.json'
    while not decision.exists():time.sleep(.5)
    supplement=read(decision);assert supplement['before_sha256']==sha(closed)
    if supplement['started']:
        closed522=Path(supplement['returned'])
        assert sha(closed522)==supplement['returned_sha256'] and read(closed522)['all_children_exited']
checks=[(p/'native-closed.json','native'),(p/'raw-300-confirmed.json','raw')]
if mode=='viewer':checks.extend([(p/'viewer-closed.json','viewer'),(j/'native-closed.json','self'),(j/'physical-301.json','physical')])
miss=[]
for f,kind in checks:
 if not f.is_file():miss.append(str(f));continue
 rec=read(f);assert rec.get('order',301 if kind in ['self','physical']else 300)==(301 if kind in ['self','physical']else 300)
 if kind=='raw':assert rec['count'] and Path(rec['root']).is_dir() and sha(Path(rec['snapshot']))==rec['sha256']
 elif kind=='physical':assert rec['passed']
 else:assert rec['passed'] and rec.get('exit',rec.get('exit_code'))==0 and not rec.get('remaining_chromium',[])and not rec.get('remaining_blender',[])
state=dict(order=301,mode=mode,previous_session=str(closed),previous_session_sha256=sha(closed),previous_browser_report_sha256=prev['report_sha256'],remaining_chromium=[],time=datetime.now(timezone.utc).isoformat())
if miss:
 write(q/f'301-{mode}-deferred.json',{**state,'deferred':True,'missing':miss,'blender_started':False,'chromium_started':False});sys.exit()
job=j/('run-native.py'if mode=='native' else'run-viewer.py');assert job.is_file(),job
with(q/f'301-{mode}.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);good=j/(mode+'-closed.json')
 if not good.is_file():
  write(q/f'301-{mode}-window.json',{**state,'authorized':True})
  subprocess.run([sys.executable,'-Bu',job],check=True)
 r=read(good);assert r['order']==301 and r['passed']and r['exit']==0 and not r.get('remaining_blender',[])and not r.get('remaining_chromium',[])
