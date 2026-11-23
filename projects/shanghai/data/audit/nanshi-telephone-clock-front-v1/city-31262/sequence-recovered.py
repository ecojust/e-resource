"""Run the Nanshi Telephone Exchange city views with two signed windows for the Sino-German Hospital loggia."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path('/tmp/shanghai-main-262/formal-31262');old=Path('/tmp/shanghai-main-261/261-map-slot-released.json');ev=w/'isolated-evidence'
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
   fcntl.flock(lock,fcntl.LOCK_EX);subprocess.run([sys.executable,'-Bu',str(w/'capture-measured.py'),stage,*([str(old)]if stage=='control'else[])],check=True)
 closed=trueclose(target);assert closed['phase']==stage and closed['cdp_closed'] and closed['observed_chromium_pid_and_starttime']
 assert h(Path(closed['report']))==closed['report_sha256'] and closed['source_code_sha256']==h(target.parent/'actual-driver.cjs')
 assert closed['frame_check_sha256']==h(target.parent/'frame-check.json')
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
 guest=Path('/tmp/sino-german-hospital327');admit=guest/'handoff/admit-window-recovered.py'
 pinned=w.parent/'guest-327-recovered.json'
 assert admit.is_file() and pinned.is_file(),(admit,pinned)
 mark=r(pinned);assert mark['order']==327 and mark['host']==262 and Path(mark['admit'])==admit
 for kind_of_input in ['author','dispatch','admit']:assert h(Path(mark[kind_of_input]))==mark[kind_of_input+'_sha256']
 end=guest/f'{kind}-closed.json'
 if not end.is_file():subprocess.run([sys.executable,'-B',admit,kind,prior],check=True)
 delay=guest/'handoff'/f'{kind}-deferred.json'
 if end.is_file():
  done=closed_external(end,327,kind);assert done['host_receipt_sha256']==h(prior) and done['host_report_sha256']==source['report_sha256'] and done['all_processes_closed'] and done['wrapper_closed']
  if kind=='native':assert len(done['blender_pids'])>=2 and done['remaining_blender']==[] and len(done['assets'])==4
  else:
   report=Path(done['report']);assert done['views']==6 and done['downloads']==4 and h(report)==done['receipt_sha256'] and done['chromium_pids'] and done['remaining_chromium']==[]
   details=r(report);assert len(details['views'])==6 and len(details['downloads'])==4
  return
 detail=r(delay) if delay.is_file() else {}
 if kind=='viewer' and detail.get('deferred') and detail.get('started') is False and detail.get('attempted') is False:
  assert detail['order']==327 and detail['host']==262 and detail['kind']==kind
  assert detail['source_sha256']==h(prior) and detail['host_report_sha256']==source['report_sha256']
  assert not detail['blender_started'] and not detail['browser_started'] and detail['missing']
  write(w/'327-viewer-deferred.json',detail)
  return
 raise RuntimeError(f'327 {kind} did not return a successful closure: {detail}')
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['passed'] and (predecessor.get('views_reviewed') or predecessor.get('all_captures_visually_reviewed') or predecessor.get('visually_reviewed'))
 assert predecessor['order']==261 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 external('native',use('control'));use('mobile-card');mobile=use('mobile-pin');external('viewer',mobile)
 for stage in ['desktop-card','desktop-pin','street','roof','clock','central-arch','distant']:
  use(stage)
  guest=Path('/tmp/sino-german-hospital327')
  comparison=Path('/tmp/shanghai-yongjia-porch/scenes/327-comparison.json')
  if not (guest/'viewer-closed.json').is_file() and (guest/'raw-327-confirmed.json').is_file() and comparison.is_file():
   external('viewer',mobile)
 print('All 262 main-scene sessions have closed. Inspect the ten actual views.',flush=True)
