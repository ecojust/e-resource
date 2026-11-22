"""Offer the idle interval between signed city viewports to the Soong residence author."""
from pathlib import Path
from hashlib import file_digest
from datetime import datetime,timezone
import fcntl,json,os,sys,subprocess,time
q=Path(__file__).parent;previous=Path('/tmp/rongzhai303');owner=Path('/tmp/soong304')
mode=sys.argv[1];closed=Path(sys.argv[2]);assert mode in ('native','viewer')
def sha(f):
 with f.open('rb')as stream:return file_digest(stream,'sha256').hexdigest()
def read(f):return json.loads(f.read_bytes())
def store(f,v):
 tmp=f.with_suffix('.partial');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,f)
receipt=read(closed)
assert receipt['exit_code']==0 and receipt['node_closed']and receipt['node_pids'] and receipt['chromium_pids']and not receipt['remaining_children']and not receipt['remaining_chromium']
report=closed.parent/('control-browser.json'if mode=='native'else'main-browser.json');assert sha(report)==receipt['report_sha256']
checks=[(previous/'native-closed.json',303,'native'),(previous/'raw-303-confirmed.json',303,'raw')]
if mode=='viewer':
 checks.extend([(previous/'viewer-closed.json',303,'viewer'),(owner/'native-closed.json',304,'native'),(owner/'raw-304-confirmed.json',304,'raw'),(Path('/tmp/shanghai-yongjia-porch/scenes/304-comparison.json'),304,'release')])
who=owner/'mapping/handoff/admit-window.py'
def validate(f,n,role):
 d=read(f);assert d.get('order',n)==n
 if role=='raw':assert Path(d['root']).is_dir() and sha(Path(d['snapshot']))==d['sha256'] and len(d['catalog_sha256'])==64;return
 if role=='release':assert d['passed']and len(d['production_receipt_sha256'])==64;return
 assert d['passed'] and d.get('exit_code',d.get('exit'))==0
 assert not(d.get('remaining_chromium')or d.get('remaining_blender')or d.get('remaining'))
 if role=='native':assert len(d.get('assets',d.get('files',{})))==4
 else:
  for k,count in [('views',6),('downloads',4)]:
   v=d[k];assert (len(v)if isinstance(v,(dict,list))else v)==count
with(q/f'304-{mode}.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 finished=owner/(mode+'-closed.json');defer=q/f'304-{mode}-deferred.json';grant=q/f'304-{mode}-window.json'
 if finished.exists():validate(finished,304,mode);raise SystemExit
 if defer.exists():assert read(defer)['deferred'];raise SystemExit
 prior=dict(order=304,mode=mode,previous_session=str(closed),previous_session_sha256=sha(closed),previous_browser_report_sha256=sha(report),remaining_chromium=[],checked=datetime.now(timezone.utc).isoformat())
 missing=[str(f)for f,n,r in checks if not f.exists()]
 if not who.is_file():missing.append(str(who))
 if missing:
  store(defer,dict(**prior,deferred=True,missing=missing,blender_started=False,chromium_started=False));raise SystemExit
 for f,n,r in checks:validate(f,n,r)
 store(grant,dict(**prior,authorized=True,inputs={str(f):sha(f)for f,n,r in checks}))
 subprocess.run([sys.executable,'-Bu',who,mode,str(closed)],check=True)
 while not finished.exists():
  author_defer=owner/'mapping/handoff'/f'239-{mode}-deferred.json'
  if author_defer.is_file():
   v=read(author_defer);assert v['deferred']and not v.get('blender_started')and not v.get('chromium_started')
   store(defer,dict(**prior,deferred=True,author_file=str(author_defer),sha256=sha(author_defer),blender_started=False,chromium_started=False));raise SystemExit
  time.sleep(2)
 validate(finished,304,mode)
