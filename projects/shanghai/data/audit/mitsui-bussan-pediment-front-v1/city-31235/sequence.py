"""Run the Willow Court city views and optionally yield two real physical gaps to the bank pavilion."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).resolve().parent;old=Path('/tmp/shanghai-main-234/234-map-slot-released.json');ev=w/'isolated-evidence'
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
def external(stage,prior):
 owner=Path('/tmp/xiaonanmen300');parent=Path('/tmp/jixian299')
 native=owner/'native-closed.json';raw=owner/'raw-300-confirmed.json';end=native if stage=='native'else owner/'viewer-closed.json'
 delay=w/f'300-{stage}-deferred.json'
 if end.is_file():closed_external(end,300,stage);return
 if delay.is_file():return
 admit=owner/'mapping/handoff/admit-window.py'
 needed=[parent/'native-closed.json',parent/'raw-299-confirmed.json']
 if stage=='viewer':needed.extend([parent/'viewer-closed.json',native,raw,Path('/tmp/shanghai-yongjia-porch/scenes/300-comparison.json')])
 dispatch=admit.parent/'dispatch-contract.json'
 assert h(dispatch)=='e1c05d63584d7cbe9cc501e878086bbaf4bc3f4303fa3ae281aceffabac1ca73' and h(admit)=='3ea094da2ffc048501c4ac7b769d5d5e5d7f205847e0787161664602964b3f48'
 if stage=='viewer' and not (parent/'formal-independent-closed.json').is_file():
  write(delay,dict(order=300,authorized=False,started=False,attempted=False,previous_session=str(prior),previous_sha256=h(prior),absent_at_handoff=[str(parent/'formal-independent-closed.json')]));return
 missing=[str(f)for f in [*needed,admit] if not f.is_file()]
 if missing:
  write(delay,dict(order=300,authorized=False,previous_session=str(prior),previous_sha256=h(prior),absent_at_handoff=missing));return
 closed_external(needed[0],299,'native');ancestor=r(needed[1]);assert ancestor['order']==299 and h(Path(ancestor['snapshot']))==ancestor['sha256']
 if stage=='viewer':
  from urllib.request import urlopen
  closed_external(needed[2],299,'viewer');closed_external(native,300,'native')
  assert r(raw)['order']==300 and h(Path(r(raw)['snapshot']))==r(raw)['sha256'] and r(needed[-1])['passed']
  root=Path(r(raw)['root'])/'projects/shanghai'
  cat=r(root/'data/candidate-city-integrations.json');row=cat['models'][-1]
  manifest=r(root/row['candidate_manifest']);assert manifest['id']==row['id']
  with urlopen('http://127.0.0.1:31300/'+manifest['viewer_page'],timeout=14) as response:assert response.status==200 and b'showCandidateAssetViewer' in response.read()
 evidence=trueclose(prior);assert evidence['cdp_closed'] and h(Path(evidence['report']))==evidence['report_sha256']
 subprocess.run([sys.executable,'-B',owner/'mapping/handoff/admit-window.py',stage,prior],check=True)
 if delay.is_file():
  returned=r(delay);assert returned['order']==300 and returned['authorized'] is False and returned['previous_session']==str(prior)
  if returned.get('attempted'):assert returned['previous_report_sha256']==evidence['report_sha256'] and 'Production exited' in returned['reason']
  return
 closed_external(end,300,stage)
 write(w/f'300-{stage}-window.json',dict(order=300,host=235,authorized=True,previous_session=str(prior),previous_session_sha256=h(prior),report_sha256=evidence['report_sha256'],received_source_receipts={str(f):h(f)for f in needed}))
 print('300',stage,'released',h(prior),flush=True)
 while not (end.is_file() or delay.is_file()):time.sleep(3)
 if end.is_file():closed_external(end,300,stage)
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['passed'] and predecessor['all_captures_visually_reviewed']
 assert predecessor['order']==234 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 control=use('control')
 guest=Path('/tmp/jixian299/offer-real-31299.py');assert h(guest)=='a87eaf36e8d01f5553f6cf01c468f68194883a98be08b400c7d6ce51df4d0e12'
 subprocess.run([sys.executable,'-Bu',str(guest),str(control)],check=True)
 returned=guest.parent/'235-formal-viewer-returned.json';rec=r(returned);prev=r(control)
 assert rec['host']==235 and rec['order']==299 and rec['host_sha256']==h(control) and rec['host_report_sha256']==h(Path(prev['report'])) and rec['remaining_chromium']==[]
 write(w/'299-formal-returned.json',dict(host=235,phase='control',physical_sha256=h(control),return_sha256=h(returned),actual_return=str(returned)))
 external('native',control);use('mobile-card');external('viewer',use('mobile-pin'))
 for stage in ['desktop-card','desktop-pin','street','roof','plaque','pediment','distant']:
  stage_close=use(stage)
  if stage=='desktop-card':
   w510=Path('/tmp/guangyuan510')
   action=Path('/workspace/.e-resource-recovery/grace/reboot235/recheck-published-510.py');assert h(action)=='e625e5630d19b54e76d0ca051a26dd9331659e4262bc2e0a3e6aaebb34795fb9'
   subprocess.run([sys.executable,'-Bu',action,stage_close],check=True)
   done=r(w510/'235-native-returned.json')
   assert done['host']==235 and done['order']==510 and done['host_sha256']==h(stage_close) and done['host_report_sha256']==r(stage_close)['report_sha256']
   assert done['all_children_exited'] and not done['remaining_children']
   for entry in done['phases']:
    if entry['physical']:assert h(Path(entry['physical']))==entry['physical_sha256']
 endpoint=w/'isolated-evidence/distant/closed.json'
 follow=Path('/tmp/hongkou-416-study/development-native/recheck-after-235.py')
 assert h(follow)=='18a5c914f8005a92c97ccc0cfb0bb7e0b09c84b07cd0398f9c80d4ae7c1ac9c5'
 subprocess.run([sys.executable,'-Bu',str(follow),str(endpoint)],check=True)
 actual=r(follow.with_name('235-development-returned.json'))
 assert actual['order']==416 and actual['host']==235 and actual['host_sha256']==h(endpoint) and actual['host_report_sha256']==r(endpoint)['report_sha256']
 assert actual['previous_sha256']==h(w/'standalone-originals.json') and actual['all_children_exited'] and not actual['remaining_children']
 if actual.get('started'): assert h(Path(actual['physical']))==actual['physical_sha256']
 prior416=follow.with_name('235-development-returned.json')
 source361=Path('/tmp/blackstone361/development-native/after-235.py')
 assert h(source361)=='cf71e18af974e99573b85b974e262b8a393947022941d47ca4872f2b5c26f462'
 subprocess.run([sys.executable,'-Bu',source361,endpoint,prior416],check=True)
 returned361=r(source361.with_name('235-development-returned.json'))
 assert returned361['order']==361 and returned361['host']==235 and returned361['phase']=='distant'
 assert returned361['host_sha256']==h(endpoint) and returned361['host_report_sha256']==r(endpoint)['report_sha256'] and returned361['previous_sha256']==h(prior416)
 assert returned361['all_children_exited'] and returned361['remaining_children']==[]
 physical361=source361.with_name('physical.json');assert returned361['physical_sha256']==h(physical361)
 receipt361=r(physical361);assert receipt361['exit_code']==returned361['exit_code'] and receipt361['passed']==returned361['passed'] and receipt361['all_children_exited'] and receipt361['remaining_children']==[]
 print('All 235 main-scene sessions have closed. Inspect the ten actual views.',flush=True)
