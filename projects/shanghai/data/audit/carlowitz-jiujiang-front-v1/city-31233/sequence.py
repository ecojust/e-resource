"""Run Carlowitz and offer the closed control and mobile sessions to the Lianshi Association when its predecessor is ready."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).resolve().parent;old=Path('/tmp/shanghai-main-232/232-map-slot-released.json');ev=w/'isolated-evidence'
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
 end_dir=Path('/tmp/lianyi298');parent=Path('/tmp/renji297');gate=end_dir/'mapping/handoff/admit-window.py'
 end=end_dir/('native-closed.json' if kind=='native' else 'viewer-closed.json')
 deferred=w/f'298-{kind}-deferred.json'
 if end.is_file():trueclose(end);return
 if deferred.is_file():return
 req=[parent/'native-closed.json',parent/'raw-297-confirmed.json']
 if kind=='viewer':req+=[parent/'viewer-closed.json',end_dir/'native-closed.json',end_dir/'raw-298-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/298-comparison.json')]
 absent=[str(f)for f in req if not f.is_file()]
 if absent:
  write(deferred,dict(order=298,phase=kind,authorized=False,previous_session=str(prior),previous_sha256=h(prior),missing=absent));return
 ancestor=r(req[1]);assert ancestor['order']==297 and h(Path(ancestor['snapshot']))==ancestor['sha256'];trueclose(req[0])
 if kind=='viewer':
  trueclose(req[2]);trueclose(req[3]);child=r(req[4]);assert child['order']==298 and h(Path(child['snapshot']))==child['sha256'] and r(req[5])['passed']
 receipt=trueclose(prior);assert receipt['cdp_closed'] and h(Path(receipt['report']))==receipt['report_sha256']
 subprocess.run([sys.executable,'-B',gate,kind,prior],check=True)
 while not end.is_file():time.sleep(3)
 trueclose(end)
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['passed'] and predecessor['all_captures_visually_reviewed'] and predecessor['order']==232 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 external('native',use('control'));use('mobile-card');external('viewer',use('mobile-pin'))
 for stage in ['desktop-card','desktop-pin','street','roof','bowed','gable','distant']:
  use(stage)
 subprocess.run([sys.executable,'-B',w/'obtain-destination-picture.py'],check=True)
 subprocess.run([sys.executable,'-B',w/'check-pixels.py'],check=True)
 subprocess.run([sys.executable,'-B',w/'independent.py'],check=True)
 guest=Path('/tmp/hongkou-408-study/development-native/link-233.py')
 assert h(guest)=='d4463736168a95cc053fcadbd262178c05fd62e1e0e98b623de95b1470c0a526'
 prior=ev/'independent/closed.json';report=prior.parent/'viewer.json'
 subprocess.run([sys.executable,'-Bu',guest,prior,report],check=True)
 ticket=guest.parent/'233-development-returned.json';proof=r(ticket)
 assert proof['order']==408 and proof['host']==233 and proof['host_sha256']==h(prior) and proof['host_report_sha256']==h(report)
 assert proof['all_children_exited'] and proof['remaining_children']==[]
 if proof.get('deferred'):assert not proof['started'] and proof['missing']
 elif proof['passed']:assert proof['exit_code']==0 and h(Path(proof['physical']))==proof['physical_sha256']
 write(w/'408-development-handback.json',dict(ticket=str(ticket),ticket_sha256=h(ticket),host_sha256=h(prior),finished=proof.get('finished')))
 follow=Path('/tmp/derring-400-study/development-native/recheck-after-233.py')
 assert h(follow)=='9d37ecd6e79230d81790d9c43fd8d9985baac4e33246c98de82843dafa0a75c6'
 if proof.get('deferred'):
  write(w/'400-development-handback.json',dict(order=400,host=233,started=False,deferred=True,reason='408 did not start',host_sha256=h(prior),host_report_sha256=h(report),previous_sha256=h(ticket),remaining_children=[]))
 else:
  assert h(Path(proof['physical']))==proof['physical_sha256']
  subprocess.run([sys.executable,'-Bu',follow,prior,ticket],check=True)
  returned=follow.parent/'233-development-returned.json';item=r(returned)
  assert item['order']==400 and item['host']==233 and item['host_sha256']==h(prior) and item['host_report_sha256']==h(report)
  assert item['previous_sha256']==h(ticket) and item['all_children_exited'] and item['remaining_children']==[]
  if item.get('started') or item.get('already_completed'):
   assert item['passed']==(item['exit_code']==0) and h(Path(item['physical']))==item['physical_sha256']
  write(w/'400-development-handback.json',dict(ticket=str(returned),ticket_sha256=h(returned),host_sha256=h(prior),previous_sha256=h(ticket)))
 print('All 233 main-scene sessions have closed. Inspect the ten actual views.',flush=True)
