"""Run the Shanghai Money Guild Ningbo Road frontage city views with two signed windows for the Sinan Road even-numbered garden residence."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).resolve().parent;old=Path('/tmp/shanghai-main-276/276-map-slot-released.json');ev=w/'isolated-evidence'
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
   fcntl.flock(lock,fcntl.LOCK_EX);subprocess.run([sys.executable,'-Bu',str(w/'capture-live.py'),stage,*([str(old)]if stage=='control'else[])],check=True)
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
 guest=Path('/tmp/sinan-even342');admit=guest/'handoff/admit-window-live.py'
 if not admit.exists():
  write(w/f'342-{kind}-deferred.json',dict(order=342,host=277,kind=kind,deferred=True,source=str(prior),source_sha256=h(prior),missing=[str(admit)],blender_started=False,browser_started=False));return
 pinned=w.parent/'guest-342-live.json'
 if not pinned.exists():
  write(w/f'342-{kind}-deferred.json',dict(order=342,host=277,kind=kind,deferred=True,started=False,source=str(prior),host_receipt_sha256=h(prior),host_report_sha256=source['report_sha256'],missing=[str(pinned)]));return
 mark=r(pinned);assert mark['order']==342 and mark['host']==277 and Path(mark['admit'])==admit
 for kind_of_input in ['author','dispatch','admit']:assert h(Path(mark[kind_of_input]))==mark[kind_of_input+'_sha256']
 if not (guest/f'{kind}-closed.json').is_file() and not (w/f'342-{kind}-deferred.json').is_file():
  subprocess.run([sys.executable,'-B',admit,kind,prior],check=True)
 end=guest/f'{kind}-closed.json';delay=guest/'handoff'/f'{kind}-deferred.json'
 if end.is_file():
  done=closed_external(end,342,kind);assert done['host_receipt_sha256']==h(prior) and done['host_report_sha256']==source['report_sha256'] and done['all_processes_closed'] and done['wrapper_closed']
  if kind=='native':assert len(done['blender_pids'])>=2 and done['remaining_blender']==[] and len(done['assets'])==4
  else:
   report=Path(done['report']);assert done['views']==6 and done['downloads']==4 and h(report)==done['receipt_sha256'] and done['chromium_pids'] and done['remaining_chromium']==[]
   details=r(report);assert len(details['views'])==6 and len(details['downloads'])==4
  return
 d=r(delay);assert d.get('source_sha256',d.get('host_receipt_sha256'))==h(prior) and d['deferred'] and d['order']==342
 if d.get('attempted') and not d.get('actual_prior_attempt'):
  assert d.get('exit',d.get('exit_code'))!=0 and d['remaining']==[] and d['wrapper_closed'] and d['host_receipt_sha256']==h(prior) and d['host_report_sha256']==source['report_sha256'] and h(Path(d['launch_log']))==d['launch_log_sha256']
 elif d.get('actual_prior_attempt'):
  assert d['all_processes_closed'] and d['remaining']==[] and d['attempt_exit_code']!=0 and d['physical_exit']['wrapper_closed'] and d['physical_exit']['remaining']==[]
 else:assert (d.get('started') is False or d.get('missing') and not d.get('blender_started') and not d.get('browser_started'))
 write(w/f'342-{kind}-deferred.json',d)
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['passed'] and (predecessor.get('views_reviewed') or predecessor.get('all_captures_visually_reviewed') or predecessor.get('visually_reviewed'))
 assert predecessor['order']==276 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 control=use('control');external('native',control);use('mobile-card');phone=use('mobile-pin');external('viewer',phone)
 for stage in ['desktop-card','desktop-pin','street','roof','arched-entrance','balcony-brackets','distant']:
  use(stage)
 subprocess.run([sys.executable,'-Bu',w/'verify-standalone.py'],check=True)
 print('All 277 main-scene sessions have closed. Inspect the ten actual city views together with the independent assets.',flush=True)
