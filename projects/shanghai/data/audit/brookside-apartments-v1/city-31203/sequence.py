"""Run the actual Brookside city views, handing physical windows to 268 only after the preceding Chromium really closed."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).resolve().parent;old=Path('/tmp/clements202/202-map-slot-released.json');ev=w/'isolated-evidence'
r=lambda f:json.loads(f.read_bytes());h=lambda f:sha256(f.read_bytes()).hexdigest()
def write(p,data):
 if p.exists():return r(p)
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
 return data
def trueclose(p):
 rec=r(p);rc=next((rec[k]for k in ['exit','exit_code','returncode','code']if k in rec),None)
 assert rc==0 and not any(rec.get(k)for k in ['remaining','remaining_chromium','remaining_blender','remaining_oidn','remaining_processes']),p
 return rec
def use(stage):
 target=ev/stage/'closed.json'
 if not target.is_file():
  with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);subprocess.run([sys.executable,'-Bu',str(w/'capture.py'),stage,*([str(old)]if stage=='control'else[])],check=True)
 closed=trueclose(target);assert closed['phase']==stage and closed['cdp_closed'] and closed['observed_chromium_pid_and_starttime']
 assert h(Path(closed['report']))==closed['report_sha256']
 print('closed',stage,closed['finished'],flush=True)
 return target
def external(stage,prior):
 n=Path('/tmp/hengfeng267/native-closed.json');raw=Path('/tmp/hengfeng267/raw-267-confirmed.json');sn=Path('/tmp/shamei268/native-closed.json')
 gate=w/f'268-{stage}-window.json';defer=w/f'268-{stage}-deferred.json';returned=sn if stage=='native' else Path('/tmp/shamei268/viewer-closed.json')
 if returned.is_file():trueclose(returned);return
 if defer.exists():return
 ready=n.is_file() and raw.is_file() and (stage=='native' or sn.is_file())
 if stage=='viewer' and ready:
  from urllib.request import urlopen
  raw268=Path('/tmp/shamei268/raw-268-confirmed.json');layer268=Path('/tmp/shanghai-yongjia-porch/scenes/268-comparison.json')
  ready=raw268.is_file() and layer268.is_file() and r(raw268).get('order')==268 and r(layer268).get('passed') is True
  if ready:
   try:
    with urlopen('http://127.0.0.1:31268/somekh-building-street-corner.html',timeout=8)as response:ready=response.status==200 and b'showCandidateAssetViewer' in response.read()
   except OSError:ready=False
 if not ready:
  write(defer,{'order':268,'authorized':False,'previous_session':str(prior),'sha256':h(prior),'reason':'The agreed predecessor or current native receipt had not arrived when the preceding actual map session closed.'});return
 native=trueclose(n);rr=r(raw);assert native.get('order',267)==267 and rr['order']==267
 ss=Path(rr['snapshot']);sig=rr.get('sha256',rr.get('snapshot_sha256'));assert h(ss)==sig
 if stage=='viewer':trueclose(sn)
 write(gate,{'order':268,'authorized':True,'previous_session':str(prior),'previous_session_sha256':h(prior),'previous_browser_report_sha256':r(prior)['report_sha256'],'remaining_chromium':[],'predecessor_receipts':{str(q):h(q)for q in [n,raw]},'since':datetime.now(timezone.utc).isoformat()})
 print('authorized',stage,flush=True)
 while not (returned.is_file() or defer.is_file()):time.sleep(3)
 if returned.is_file():trueclose(returned)
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor.get('order',202)==202 and predecessor and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 external('native',use('control'));use('mobile-card');external('viewer',use('mobile-pin'))
 for name in ['desktop-card','desktop-pin','street','roof','crown','wings','distant']:use(name)
 print('all 203 real browsers closed; inspect the actual figures',flush=True)
