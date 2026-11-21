"""Run the Willow Court city views and optionally yield two real physical gaps to the bank pavilion."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path(__file__).resolve().parent;old=Path('/tmp/shanghai-main-226/226-map-slot-released.json');ev=w/'isolated-evidence'
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
 owner=Path('/tmp/yangtze-hankou292');parent=Path('/tmp/chinahotel291')
 native=owner/'native-closed.json';raw=owner/'raw-292-confirmed.json';end=native if stage=='native'else owner/'viewer-closed.json'
 delay=w/f'292-{stage}-deferred.json'
 if end.is_file():trueclose(end);return
 if delay.is_file():return
 needed=[parent/'native-closed.json',parent/'raw-291-confirmed.json']
 if stage=='viewer':needed.extend([parent/'viewer-closed.json',native,raw,Path('/tmp/shanghai-yongjia-porch/scenes/292-comparison.json')])
 missing=[str(f)for f in needed if not f.is_file()]
 if missing:
  write(delay,dict(order=292,authorized=False,previous_session=str(prior),previous_sha256=h(prior),absent_at_handoff=missing));return
 trueclose(needed[0]);ancestor=r(needed[1]);assert ancestor['order']==291 and h(Path(ancestor['snapshot']))==ancestor['sha256']
 if stage=='viewer':
  from urllib.request import urlopen
  trueclose(needed[2]);trueclose(native)
  assert r(raw)['order']==292 and h(Path(r(raw)['snapshot']))==r(raw)['sha256'] and r(needed[-1])['passed']
  with urlopen('http://127.0.0.1:31292/yangtze-hotel-hankou-balconies.html',timeout=14) as response:assert response.status==200 and b'showCandidateAssetViewer' in response.read()
 evidence=trueclose(prior);assert evidence['cdp_closed'] and h(Path(evidence['report']))==evidence['report_sha256']
 subprocess.run([sys.executable,'-B',owner/'handoff/admit-window.py',stage,prior],check=True)
 print('292',stage,'released',h(prior),flush=True)
 while not (end.is_file() or delay.is_file()):time.sleep(3)
 if end.is_file():trueclose(end)
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['order']==226 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 first=use('control');external('native',first)
 slot291=Path('/tmp/chinahotel291/offer-227.py');assert h(slot291)=='8461bc0b1eecdff16f6a5380e2ab2cb698f4e49a144379e736fe3ea44142a69e'
 prev292=Path('/tmp/yangtze-hankou292/native-closed.json');prev292=prev292 if prev292.is_file() else w/'292-native-deferred.json'
 subprocess.run([sys.executable,'-Bu',slot291,first,prev292],check=True)
 ret291=slot291.parent/'227-formal-viewer-returned.json';ans291=r(ret291)
 assert ans291['host']==227 and ans291['order']==291 and ans291['host_sha256']==h(first) and ans291['host_report_sha256']==r(first)['report_sha256'] and ans291['previous_sha256']==h(prev292) and ans291['all_children_exited'] and not ans291['remaining_children']
 write(w/'291-formal-recheck-returned.json',dict(source=str(ret291),sha256=h(ret291),previous_sha256=h(prev292)))
 mobile=use('mobile-card');prog380=Path('/dev/shm/p38/control/after-227.py');assert h(prog380)=='0ef17bbbea1e3c233641657bcbe0a422fcce20e9e02cb50fa88dd0f05f1fcce5'
 subprocess.run([sys.executable,'-Bu',prog380,mobile],check=True)
 returned380=prog380.parent/'227-development-returned.json';actual380=r(returned380)
 assert actual380['order']==380 and actual380['host']==227 and actual380['host_sha256']==h(mobile) and actual380['host_report_sha256']==r(mobile)['report_sha256'] and actual380['all_children_exited'] and not actual380['remaining_children']
 write(w/'380-development-recheck-returned.json',dict(source=str(returned380),sha256=h(returned380),exit_code=actual380.get('exit_code')))
 external('viewer',use('mobile-pin'))
 for stage in ['desktop-card','desktop-pin','street','roof','plaque','windows','distant']:
  closed=use(stage)
  if stage=='desktop-card':
   script=Path('/tmp/sinan-even342/design/after-227-camera.py')
   assert h(script)=='ebe1a2576797618a089c76510d4e77040215310eb3022757128155e37b739f84'
   returned=script.parents[1]/'227-camera-closed.json'
   if not returned.is_file():subprocess.run([sys.executable,'-Bu',script,closed],check=True)
   q=r(returned);c=r(closed)
   assert q['order']==342 and q['host']==227 and q['host_sha256']==h(closed) and q['host_report_sha256']==h(Path(c['report'])) and q['remaining']==[]
   assert (q.get('attempted') and isinstance(q['exit_code'],int) and q['all_children_exited']) or (q.get('deferred') and q.get('started') is False and q['missing'])
   write(w/'342-camera-returned.json',dict(host=227,stage=stage,closed=str(closed),closed_sha256=h(closed),returned=str(returned),sha256=h(returned)))
  if stage=='desktop-pin':
   program=Path('/tmp/taiyuan363/mapping/after-227.py')
   assert h(program)=='1f16515d17729cae8b94beb2e59cde175557e33f83cf8d13852c61acfdf4c428'
   result_file=program.parent/'227-model-closed.json'
   if not result_file.is_file():subprocess.run([sys.executable,'-Bu',str(program),str(closed)],check=True)
   result=r(result_file);source=r(closed)
   assert result['order']==363 and result['host']==227 and result['host_sha256']==h(closed) and result['host_report_sha256']==h(Path(source['report'])) and result['remaining']==[]
   assert (result.get('attempted') and isinstance(result['exit_code'],int)) or (result.get('deferred') and not result.get('started'))
   write(w/'363-physical-returned.json',dict(host=227,stage='desktop-pin',receipt=str(closed),sha256=h(closed),actual_receipt=str(result_file),actual_sha256=h(result_file)))
  if stage=='street':
   author=Path('/tmp/wukang2-374/design/after-227-street.py')
   assert h(author)=='51ab2b83167dc36b1347762a2159735d205d8a2880bc3f055696c55c055a7c3d'
   return_file=author.parent.parent/'227-model-and-views-closed.json'
   if not return_file.is_file():subprocess.run([sys.executable,'-Bu',author,closed],check=True)
   outcome=r(return_file);assert outcome['order']==374 and outcome['host']==227 and outcome['host_sha256']==h(closed) and outcome['host_report_sha256']==r(closed)['report_sha256']
   assert outcome['attempted'] and isinstance(outcome['exit_code'],int) and outcome['all_children_exited'] and outcome['remaining']==[]
   write(w/'374-cpu-returned.json',dict(phase=stage,receipt=str(return_file),receipt_sha256=h(return_file),exit_code=outcome['exit_code']))
  if stage=='roof':
   program=Path('/tmp/jingu-shaoxing346/design/after-227-roof.py')
   assert h(program)=='64ac8f3e5dfb5977e39c2f0c1b61cce8e14519d6ab3701e9595c27bc37852a25'
   subprocess.run([sys.executable,'-Bu',program,closed],check=True)
   out=program.parent.parent/'227-runtime-closed.json'
   result=r(out);assert result['order']==346 and result['host_sha256']==h(closed) and result['host_report_sha256']==r(closed)['report_sha256'] and result['remaining']==[]
   assert (result.get('attempted') and isinstance(result['exit_code'],int) and result['all_children_exited']) or (result.get('deferred') and not result['started'] and result['missing'])
   write(w/'346-physical-returned.json',dict(phase=stage,receipt=str(out),receipt_sha256=h(out),previous=str(closed),previous_sha256=h(closed)))
  if stage=='plaque':
   code=Path('/tmp/george-hengshan377/after-227-plaque.py');assert h(code)=='93732c6fb286ac0655cd55a35ac1bc975debb39e740bf7dc631e296f2117564e'
   subprocess.run([sys.executable,'-Bu',code,closed],check=True)
   out=code.parent/'227-model-closed.json';ret=r(out);assert ret['order']==377 and ret['host_sha256']==h(closed) and ret['host_report_sha256']==r(closed)['report_sha256'] and ret['remaining']==[] and ret['all_children_exited']
   write(w/'377-physical-returned.json',dict(phase=stage,receipt=str(out),receipt_sha256=h(out),previous=str(closed),previous_sha256=h(closed)))
  if stage=='windows':
   work350=Path('/tmp/donghu-70-350/after-interruption');runner=work350/'run-after-windows.py'
   assert h(runner)=='13a846f69e11274f8abd9871085504dc3951b26c6420b0732e16439db9150de1'
   subprocess.run([sys.executable,'-Bu',runner,closed],check=True)
   source350=work350/'227-new-ground-and-views.json';res350=r(source350)
   assert res350['host_sha256']==h(closed) and res350['host_report_sha256']==r(closed)['report_sha256'] and res350['remaining']==[] and res350['all_children_exited'] and isinstance(res350['exit_code'],int)
   write(w/'350-actual-study-returned.json',dict(phase=stage,source=str(source350),sha256=h(source350),exit_code=res350['exit_code']))
  if stage=='distant':
   code=w/'offer-384.py';assert h(code)=='ffed2630c5a4df1bbb1e75a21c9b701e1b0cfad308d6806ff5051019dfc3c049'
   subprocess.run([sys.executable,'-Bu',code,closed],check=True)
   ret=r(w/'384-development-returned.json');assert ret['remaining_children']==[] and ret['host_sha256']==h(closed)
   extra=Path('/tmp/four-page-camera-repair/after-release.py')
   assert h(extra)=='090ee7780106ae096b437849fd039ac1a22af6a4e3912f1cc67edb9698559a2b'
   previous=w/'384-development-returned.json';result=extra.parent/'227-actual-controls-closed.json'
   if not result.exists():subprocess.run([sys.executable,'-Bu',extra,'227',closed,previous],check=True)
   answer=r(result);assert answer['host_sha256']==h(closed) and answer['host_report_sha256']==r(closed)['report_sha256'] and answer['prior_sha256']==h(previous) and answer['all_children_exited'] and not answer['remaining_children']
   write(w/'411-415-development-returned.json',dict(host=227,result=str(result),sha256=h(result),previous_sha256=h(previous),exit_code=answer['exit_code'],finished=datetime.now(timezone.utc).isoformat()))
 print('All 227 main-scene sessions have closed. Inspect the ten actual views.',flush=True)
