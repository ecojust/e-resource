"""Run the Zikawei convent and provide two completed sessions to the Renji silver shop when its predecessor is ready."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).resolve().parent;old=Path('/tmp/shanghai-main-231/231-map-slot-released.json');ev=w/'isolated-evidence'
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
def external(kind,prior):
 end_dir=Path('/tmp/renji297');parent=Path('/tmp/nanshi-bank296');gate=end_dir/'mapping/handoff/admit-window.py'
 end=end_dir/('native-closed.json' if kind=='native' else 'viewer-closed.json')
 deferred=w/f'297-{kind}-deferred.json'
 if end.is_file():trueclose(end);return
 if deferred.is_file():return
 req=[parent/'native-closed.json',parent/'raw-296-confirmed.json']
 if kind=='viewer':req+=[parent/'viewer-closed.json',end_dir/'native-closed.json',end_dir/'raw-297-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/297-comparison.json')]
 absent=[str(f)for f in req if not f.is_file()]
 if absent:
  write(deferred,dict(order=297,phase=kind,authorized=False,previous_session=str(prior),previous_sha256=h(prior),missing=absent));return
 ancestor=r(req[1]);assert ancestor['order']==296 and h(Path(ancestor['snapshot']))==ancestor['sha256'];trueclose(req[0])
 if kind=='viewer':
  trueclose(req[2]);trueclose(req[3]);child=r(req[4]);assert child['order']==297 and h(Path(child['snapshot']))==child['sha256'] and r(req[5])['passed']
 receipt=trueclose(prior);assert receipt['cdp_closed'] and h(Path(receipt['report']))==receipt['report_sha256']
 subprocess.run([sys.executable,'-B',gate,kind,prior],check=True)
 while not end.is_file():time.sleep(3)
 trueclose(end)
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['passed'] and predecessor['all_captures_visually_reviewed'] and predecessor['order']==231 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 external('native',use('control'));card=use('mobile-card')
 supplement=Path('/tmp/nanshi-bank296/mapping/handoff/supplement-viewer.py');assert h(supplement)=='5d4327aebd94eebd495611b4aad497e89ab55add6a769701ae1042852d3cca47'
 subprocess.run([sys.executable,'-Bu',supplement,card],check=True)
 prior_result=r(Path('/tmp/nanshi-bank296/232-supplemental-viewer-returned.json'))
 assert prior_result['order']==296 and prior_result['host']==232 and prior_result['phase']=='mobile-card' and prior_result['host_sha256']==h(card)
 assert prior_result['host_report_sha256']==r(card)['report_sha256'] and prior_result['all_children_exited'] and not prior_result['remaining_children']
 if prior_result['passed']:assert len(prior_result['downloads'])==4 and h(Path(prior_result['physical']))==prior_result['physical_sha256']
 external('viewer',use('mobile-pin'))
 for stage in ['desktop-card','desktop-pin','street','roof','porch','gable','distant']:
  use(stage)
 subprocess.run([sys.executable,'-B',w/'check-pixels.py'],check=True)
 subprocess.run([sys.executable,'-B',w/'independent.py'],check=True)
 tail=Path('/workspace/.e-resource-recovery/grace/recheck-two-native-after-232.py');assert h(tail)=='7629c49172d2787a3c10b74f4aa2efc9ec0a37842e6a963787c7ce4ec2e8ec6b'
 subprocess.run([sys.executable,'-Bu',tail,ev/'independent/closed.json'],check=True)
 print('All 232 main-scene sessions have closed. Inspect the ten actual views.',flush=True)
