"""Run the Asia Realty city views and optionally yield two real physical gaps to the Beijing Road garden residence."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).resolve().parent;old=Path('/tmp/shanghai-main-241/241-map-slot-released.json');ev=w/'isolated-evidence'
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
 guest=Path('/tmp/beijing-lane1394-307');admit=guest/'handoff/admit-window.py'
 if not admit.exists():
  write(w/f'307-{kind}-deferred.json',dict(order=307,host=242,kind=kind,deferred=True,source=str(prior),source_sha256=h(prior),missing=[str(admit)],blender_started=False,browser_started=False));return
 assert h(admit)=='e4677d70749f58ea3479630e0eaf92c785ff17f85677642fec4986af6dad303c'
 assert h(guest/'handoff/dispatch-contract.json')=='e97a171f1d2032dc033def132cc7bca7b249750ef89c712652496fd8dd00afb1'
 subprocess.run([sys.executable,'-B',admit,kind,prior],check=True)
 end=guest/f'{kind}-closed.json';delay=guest/'handoff'/f'{kind}-deferred.json'
 if end.is_file():closed_external(end,307,kind);return
 d=r(delay);assert d['source_sha256']==h(prior) and d['deferred'] and d['order']==307
 if d.get('actual_prior_attempt'):
  assert d['all_processes_closed'] and d['remaining']==[] and d['attempt_exit_code']!=0 and d['physical_exit']['wrapper_closed'] and d['physical_exit']['remaining']==[]
 else:assert d['missing'] and not d['blender_started'] and not d['browser_started']
 write(w/f'307-{kind}-deferred.json',d)
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['passed'] and predecessor['all_captures_visually_reviewed']
 assert predecessor['order']==241 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 control=use('control')
 external('native',control)
 card=use('mobile-card')
 guest306=Path('/workspace/.e-resource-recovery/grace/reboot241/supplement-306.py')
 assert h(guest306)=='2cb77d1dbdb654cf0a23fe365610579663b65693301c0c382aa6d55480c7b474'
 subprocess.run([sys.executable,'-Bu',guest306,card],check=True)
 late=r(Path('/tmp/daxin306/242-mobile-card-ordinary-returned.json'))
 assert late['order']==306 and late['host']==242 and late['host_sha256']==h(card) and late['host_report_sha256']==r(card)['report_sha256']
 assert late['all_children_exited'] and not late['remaining_children']
 if not Path('/tmp/beijing-lane1394-307/native-closed.json').is_file() and (w/'307-native-deferred.json').is_file() and not r(w/'307-native-deferred.json').get('actual_prior_attempt'):
  external('native',control)
 external('viewer',use('mobile-pin'))
 use('desktop-card')
 host=use('desktop-pin')
 program=Path('/tmp/german-post534/after-242.py')
 assert h(program)=='280f61e1d3de44323f489adad41564597e8482ceeae49034f09dd8d4b5f80078'
 subprocess.run([sys.executable,'-Bu',program,host],check=True)
 receipt=r(Path('/tmp/german-post534/242-native-returned.json'));closed=r(host)
 assert receipt['order']==534 and receipt['host']==242 and receipt['phase']=='desktop-pin'
 assert receipt['host_sha256']==h(host) and receipt['host_report_sha256']==closed['report_sha256']
 assert receipt['all_children_exited'] and not receipt['remaining_children']
 if receipt.get('previous_completed_exit')==0:assert receipt['attempted'] is False and receipt['exit_code'] is None
 for stage in ['street','roof','south-door','upper-wing','distant']:use(stage)
 subprocess.run([sys.executable,'-Bu',w/'after-distant-page.py',ev/'distant/closed.json'],check=True)
 if not Path('/tmp/beijing-lane1394-307/viewer-closed.json').is_file():external('viewer',ev/'independent/closed.json')
 print('All 242 main-scene sessions have closed. Inspect the ten actual views.',flush=True)
