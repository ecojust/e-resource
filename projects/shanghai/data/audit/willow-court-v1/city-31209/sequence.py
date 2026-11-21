"""Run the Willow Court city views and optionally yield two real physical gaps to the bank pavilion."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).resolve().parent;old=Path('/tmp/picardie208/208-map-slot-released.json');ev=w/'isolated-evidence'
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
 n=Path('/tmp/saltbank272/native-closed.json');raw=Path('/tmp/saltbank272/raw-272-confirmed.json');sn=Path('/tmp/shanghaibank273/native-closed.json')
 gate=w/f'273-{stage}-window.json';defer=w/f'273-{stage}-deferred.json';returned=sn if stage=='native' else Path('/tmp/shanghaibank273/viewer-closed.json')
 if returned.is_file():trueclose(returned);return
 if defer.exists():return
 ready=n.is_file() and raw.is_file() and (stage=='native' or sn.is_file())
 if stage=='viewer' and ready:
  from urllib.request import urlopen
  raw273=Path('/tmp/shanghaibank273/raw-273-confirmed.json');layer273=Path('/tmp/shanghai-yongjia-porch/scenes/273-comparison.json')
  prior_view=Path('/tmp/saltbank272/viewer-closed.json')
  ready=prior_view.is_file() and raw273.is_file() and layer273.is_file() and r(raw273).get('order')==273 and r(layer273).get('passed') is True
  if ready:
   try:
    with urlopen('http://127.0.0.1:31273/shanghai-commercial-savings-bank-pavilion.html',timeout=8)as response:ready=response.status==200 and b'showCandidateAssetViewer' in response.read()
   except OSError:ready=False
 if not ready:
  write(defer,{'order':273,'authorized':False,'previous_session':str(prior),'sha256':h(prior),'reason':'The agreed predecessor or current native receipt had not arrived when the preceding actual map session closed.'});return
 native=trueclose(n);rr=r(raw);assert native['order']==272 and rr['order']==272 and rr.get('passed',True)
 ss=Path(rr['snapshot']);sig=rr.get('sha256',rr.get('snapshot_sha256'));assert h(ss)==sig
 if stage=='viewer':trueclose(sn);trueclose(prior_view)
 write(gate,{'order':273,'authorized':True,'previous_session':str(prior),'previous_session_sha256':h(prior),'previous_browser_report_sha256':r(prior)['report_sha256'],'remaining_chromium':[],'predecessor_receipts':{str(q):h(q)for q in [n,raw]},'since':datetime.now(timezone.utc).isoformat()})
 print('authorized',stage,flush=True)
 while not (returned.is_file() or defer.is_file()):time.sleep(3)
 if returned.is_file():trueclose(returned)
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['order']==208 and predecessor['exit_code']==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 before=use('control');external('native',before)
 subprocess.run([sys.executable,'-B',w/'offer-272.py','control'],check=True)
 use('mobile-card');mobile=use('mobile-pin')
 subprocess.run([sys.executable,'-B',w/'offer-272.py','mobile-pin'],check=True)
 external('viewer',mobile)
 for stage in ['desktop-card','desktop-pin','street','roof','entrance','drive','distant']:
  use(stage)
 print('All 209 main-scene sessions have closed. Inspect the ten actual views.',flush=True)
