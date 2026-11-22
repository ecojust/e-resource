"""Run the Willow Court city views and optionally yield two real physical gaps to the bank pavilion."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).resolve().parent;old=Path('/tmp/shanghai-main-246/246-map-slot-released.json');ev=w/'isolated-evidence'
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
def closed_external(path,order,stage):
 rec=trueclose(path);assert rec['order']==order and rec.get('passed') is True
 left=[rec[k]for k in ['remaining','remaining_blender','remaining_oidn','remaining_chromium','remaining_processes']if k in rec]
 assert left and all(v in ([],{})for v in left),path
 if stage=='native':
  assets=rec.get('files',rec.get('assets',{}));assert len(assets)==4,path
 else:
  assert rec.get('receipt_sha256') or rec.get('report_sha256') or rec.get('viewer_sha256') or rec.get('report'),path
 return rec
def external(kind,prior):
 source=trueclose(prior)
 assert source['cdp_closed'] and source['node_closed'] and source['chromium_pids'] and source['remaining']==[]
 guest=Path('/tmp/yide-changhua312');admit=guest/'handoff/admit-window.py'
 if not admit.exists():
  write(w/f'312-{kind}-deferred.json',dict(order=312,host=247,kind=kind,deferred=True,source=str(prior),source_sha256=h(prior),missing=[str(admit)],blender_started=False,browser_started=False));return
 subprocess.run([sys.executable,'-B',admit,kind,prior],check=True)
 end=guest/f'{kind}-closed.json';delay=guest/'handoff'/f'{kind}-deferred.json'
 if end.is_file():closed_external(end,312,kind);return
 d=r(delay);assert d['source_sha256']==h(prior) and d['deferred'] and d['order']==312
 if d.get('actual_prior_attempt'):
  assert d['all_processes_closed'] and d['remaining']==[] and d['attempt_exit_code']!=0 and d['physical_exit']['wrapper_closed'] and d['physical_exit']['remaining']==[]
 else:assert d['missing'] and not d['blender_started'] and not d['browser_started']
 write(w/f'312-{kind}-deferred.json',d)
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['passed'] and (predecessor.get('views_reviewed') or predecessor.get('all_captures_visually_reviewed'))
 assert predecessor['order']==246 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 external('native',use('control'));use('mobile-card');external('viewer',use('mobile-pin'))
 for stage in ['desktop-card','desktop-pin','street','roof','octagon','inscription','distant']:
  host=use(stage)
  if stage=='desktop-pin':
   entry=Path('/tmp/changle272-554/after-247.py')
   assert h(entry)=='ffc55d3e9cdf934247458d44fb4588523da559dcba716550acc5bc7a11e13566'
   subprocess.run([sys.executable,'-Bu',entry,host],check=True)
   proof=r(entry.parent/'247-native-returned.json');report=r(host)
   assert proof['order']==554 and proof['host']==247 and proof['phase']==stage
   assert proof['host_sha256']==h(host) and proof['host_report_sha256']==report['report_sha256']
   assert proof['all_children_exited'] and proof['remaining_children']==[]
   if proof.get('previous_completed_exit') is not None:
    assert proof['previous_completed_exit']==0 and proof['attempted'] is False and proof['exit_code'] is None
   elif not proof.get('deferred'):
    assert isinstance(proof['exit_code'],int)
 print('All 247 main-scene sessions have closed. Inspect the ten actual views.',flush=True)
