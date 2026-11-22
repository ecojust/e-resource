"""Run the Willow Court city views and optionally yield two real physical gaps to the bank pavilion."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).resolve().parent;old=Path('/tmp/shanghai-main-247/247-map-slot-released.json');ev=w/'isolated-evidence'
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
   fcntl.flock(lock,fcntl.LOCK_EX);subprocess.run([sys.executable,'-Bu',str(w/'capture-with-verified-runtime.py'),stage,*([str(old)]if stage=='control'else[])],check=True)
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
 guest=Path('/tmp/kangding313');admit=guest/'handoff/admit-after-restart.py'
 if kind=='viewer' and (w/'313-viewer-deferred.json').is_file():
  deferred=r(w/'313-viewer-deferred.json')
  assert deferred['started'] is False and deferred['source_sha256']==h(prior)
  return
 if not admit.exists():
  write(w/f'313-{kind}-deferred.json',dict(order=313,host=248,kind=kind,deferred=True,source=str(prior),source_sha256=h(prior),missing=[str(admit)],blender_started=False,browser_started=False));return
 subprocess.run([sys.executable,'-B',admit,kind,prior],check=True)
 end=guest/f'{kind}-closed.json';delay=guest/'handoff'/f'{kind}-deferred.json'
 if end.is_file():closed_external(end,313,kind);return
 d=r(delay);assert d.get('source_sha256',d.get('host_receipt_sha256'))==h(prior) and d['deferred'] and d['order']==313
 if d.get('attempted') and not d.get('actual_prior_attempt'):
  assert d.get('exit',d.get('exit_code'))!=0 and d['remaining']==[]
 elif d.get('actual_prior_attempt'):
  assert d['all_processes_closed'] and d['remaining']==[] and d['attempt_exit_code']!=0 and d['physical_exit']['wrapper_closed'] and d['physical_exit']['remaining']==[]
 else:assert (d.get('started') is False or d.get('missing') and not d.get('blender_started') and not d.get('browser_started'))
 write(w/f'313-{kind}-deferred.json',d)
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['passed'] and (predecessor.get('views_reviewed') or predecessor.get('all_captures_visually_reviewed'))
 assert predecessor['order']==247 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 external('native',use('control'));use('mobile-card');external('viewer',use('mobile-pin'))
 for stage in ['desktop-card','desktop-pin','street','roof','arcade','corner-door','distant']:
  returned=use(stage)
  if stage=='desktop-pin':
   work=Path('/tmp/jingcun558');entry=work/'recheck-after-248.py'
   assert h(entry)=='5e7e460665d58918fc6682142750550dc96e36c126620242980835901b3917df'
   subprocess.run([sys.executable,'-Bu',entry,returned],check=True)
   outcome=r(work/'248-native-returned.json')
   assert (outcome['order'],outcome['host'],outcome['phase'])==(558,248,'desktop-pin')
   assert outcome['host_sha256']==h(returned) and outcome['host_report_sha256']==r(returned)['report_sha256']
   assert outcome['all_children_exited'] and not outcome['remaining_children'] and outcome['phases']
   if outcome.get('already_completed'):
    assert not outcome['attempted'] and outcome['exit_code'] is None and outcome['previous_completed_exit']==0 and outcome['passed']
   else:
    assert outcome['phases'][-1]['exit_code']==outcome['exit_code']
   for step in outcome['phases']:
    if step['physical']:assert h(Path(step['physical']))==step['physical_sha256']
 print('All 248 main-scene sessions have closed. Inspect the ten actual views.',flush=True)
