"""Run Yanqing Road 130 and hand two completed browser sessions to the Fifth Textile Warehouse when its predecessor is ready."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,subprocess,sys,time,fcntl,os
w=Path('/tmp/shanghai-main-228/formal-31228');old=Path('/tmp/shanghai-main-227/227-map-slot-released.json');ev=w/'isolated-evidence'
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
 end_dir=Path('/tmp/textile-fifth293');parent=Path('/tmp/yangtze-hankou292');gate=end_dir/'mapping/handoff/admit-window.py'
 end=end_dir/('native-closed.json' if kind=='native' else 'viewer-closed.json')
 deferred=w/f'293-{kind}-deferred.json'
 if end.is_file():trueclose(end);return
 if deferred.is_file():return
 req=[parent/'native-closed.json',parent/'raw-292-confirmed.json']
 if kind=='viewer':req+=[parent/'viewer-closed.json',end_dir/'native-closed.json',end_dir/'raw-293-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/293-comparison.json')]
 absent=[str(f)for f in req if not f.is_file()]
 if absent:
  write(deferred,dict(order=293,phase=kind,authorized=False,previous_session=str(prior),previous_sha256=h(prior),missing=absent));return
 ancestor=r(req[1]);assert ancestor['order']==292 and h(Path(ancestor['snapshot']))==ancestor['sha256'];trueclose(req[0])
 if kind=='viewer':
  trueclose(req[2]);trueclose(req[3]);child=r(req[4]);assert child['order']==293 and h(Path(child['snapshot']))==child['sha256'] and r(req[5])['passed']
 receipt=trueclose(prior);assert receipt['cdp_closed'] and h(Path(receipt['report']))==receipt['report_sha256']
 subprocess.run([sys.executable,'-B',gate,kind,prior,*(['--work-directory','/dev/shm/scene228-current/293-scratch'] if kind=='native' else [])],check=True)
 while not end.is_file():time.sleep(3)
 trueclose(end)
with (w/'assigned-sequence.lock').open('a')as queue:
 fcntl.flock(queue,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not old.is_file():time.sleep(3)
 predecessor=r(old)
 assert predecessor['passed'] and predecessor['all_captures_visually_reviewed'] and predecessor['order']==227 and predecessor.get('exit_code',predecessor.get('exit'))==0 and not any(predecessor.get(k)for k in ['remaining','remaining_chromium','remaining_processes'])
 external('native',use('control'))
 mobile_card=use('mobile-card')
 corrected=Path('/dev/shm/ordered-standalone-page-evidence/physical.py')
 assert h(corrected)=='52b0183e9acb0a14599e581600fddac605ecd464ed74f06fa98ffc75c241d26e'
 assert h(corrected.parent/'compare-live.cjs')=='558252f3744200cf5cfc643c46d8a99207aecef43714c5cfe330455387e68695'
 if not (corrected.parent/'228-actual-controls-closed.json').is_file():subprocess.run([sys.executable,'-Bu',corrected,'228',mobile_card],check=True)
 proof=r(corrected.parent/'228-actual-controls-closed.json')
 assert proof['host_sha256']==h(mobile_card) and proof['host_report_sha256']==r(mobile_card)['report_sha256']
 assert proof['orders']==[403,407] and proof['all_children_exited'] and proof['remaining_children']==[]
 pin=use('mobile-pin')
 page292=Path('/tmp/yangtze-hankou292/handoff/offer-228.py');assert h(page292)=='fb024e31819798b01f48ad57d7a9d6b6ae51f5444bde85110c0153698eae758d'
 out292=Path('/tmp/yangtze-hankou292/228-viewer-returned.json')
 if not out292.exists():subprocess.run([sys.executable,'-Bu',page292,pin],check=True)
 returned=r(out292);assert returned['host_sha256']==h(pin) and returned['host_report_sha256']==r(pin)['report_sha256'] and returned['all_children_exited'] and not returned['remaining_children'] and not returned['remaining_chromium']
 assert (returned.get('deferred') and not returned.get('started') and returned['missing']) or isinstance(returned['exit_code'],int)
 external('viewer',pin)
 for stage in ['desktop-card','desktop-pin','street','roof','portico','crowns','distant']:
  prior=use(stage)
  if stage=='desktop-card':
   extra=Path('/dev/shm/ordered-standalone-page-evidence/physical.py')
   assert h(extra)=='52b0183e9acb0a14599e581600fddac605ecd464ed74f06fa98ffc75c241d26e'
   if not (extra.parent/'419-actual-controls-closed.json').is_file():subprocess.run([sys.executable,'-Bu',extra,'419',prior],check=True)
   result=r(extra.parent/'419-actual-controls-closed.json')
   assert result['orders']==[419] and result['host_sha256']==h(prior) and result['all_children_exited'] and not result['remaining_children']
   check384=Path('/dev/shm/v384/p/link-228.py');assert h(check384)=='4c8ce1fdcb9a0b7b56777a29ef7793055af72e1e836daeb0bbd22f1913bc2147'
   prev419=extra.parent/'419-actual-controls-closed.json';out384=check384.parent/'228-viewer-returned.json'
   if not out384.exists():subprocess.run([sys.executable,'-Bu',check384,prior,prev419],check=True)
   ret=r(out384);assert ret['host_sha256']==h(prior) and ret['host_report_sha256']==r(prior)['report_sha256'] and ret['previous_sha256']==h(prev419)
   assert ret['all_children_exited'] and ret['remaining_children']==[]
   assert ret.get('deferred') or (ret.get('attempted') and isinstance(ret['exit_code'],int))
  if stage=='desktop-pin':
   recheck=Path('/dev/shm/ordered-standalone-page-evidence/363-recheck/mapping/228-retry-geometry.py')
   assert h(recheck)=='a34084d149b9de3839fb9e26f226913b4f94b98459a9913c8172f0c347c201f5'
   subprocess.run([sys.executable,'-Bu',recheck,prior],check=True)
   actual=r(recheck.parent/'228-retry-model-closed.json')
   assert actual['host_sha256']==h(prior) and actual['previous_sha256']==h(recheck.parent/'227-model-closed.json') and actual['remaining']==[]
   check=recheck.parent/'228-after-verified-retry.py'
   assert h(check)=='a4a502d4e9d02f71cac11737f835527cc15a62787201f6a86951ab744e8a604d'
   subprocess.run([sys.executable,'-B',check,prior],check=True)
   result=r(check.parent/'228-city-closed.json')
   assert result['host_sha256']==h(prior) and result['host_report_sha256']==r(prior)['report_sha256'] and result['remaining']==[]
   assert result.get('deferred') or (result['started'] and all(z['remaining']==[] for z in result['phases']))
  if stage=='street':
   guest=Path('/tmp/yongjia630-381/after-228-street.py')
   assert h(guest)=='1389c593a8fe650466fb6131caaf79f67a7b577a6edb5bbb528816d8611303ae'
   subprocess.run([sys.executable,'-Bu',guest,prior],check=True)
   closure=Path('/tmp/yongjia630-381/228-model-closed.json');result=r(closure)
   assert result['order']==381 and result['host']==228 and result['phase']=='street'
   assert result['host_sha256']==result['host_receipt_sha256']==h(prior) and result['host_report_sha256']==r(prior)['report_sha256']
   assert result['all_children_exited'] and result['remaining']==[]
   if result.get('deferred'):assert not result.get('attempted') and not result.get('started')
   else:assert result['stages'] and all(row.get('pid') for row in result['stages'])
   write(w/'381-street-handback.json',dict(host=228,order=381,physical=str(closure),sha256=h(closure),source_sha256=h(prior)))
   program=Path('/tmp/george-hengshan377/after-228-street.py')
   assert h(program)=='7d566b299b8d78bf9501a152fcaf942560a617ee86217f57276ac914bc0e95a9'
   subprocess.run([sys.executable,'-Bu',program,prior,closure],check=True)
   physical=program.parent/'228-wall-check-closed.json';walls=r(physical)
   assert walls['order']==377 and walls['host']==228 and walls['host_sha256']==h(prior)
   assert walls['host_report_sha256']==r(prior)['report_sha256'] and walls['previous_sha256']==h(closure)
   assert walls['all_children_exited'] and walls['remaining']==[]
   if walls.get('deferred'):
    assert walls['started'] is False and walls['attempted'] is False
   else:
    assert walls['pid']>1 and walls['observed_births'] and h(Path(walls['log']))==walls['log_sha256']
    assert walls['passed']==(walls['exit_code']==0)
    if walls['passed']:assert h(Path(walls['evidence']))==walls['evidence_sha256']
   write(w/'377-street-handback.json',dict(host=228,order=377,physical=str(physical),sha256=h(physical),previous_sha256=h(closure),source_sha256=h(prior)))
 subprocess.run([sys.executable,'-B',w/'check-pixels.py'],check=True)
 subprocess.run([sys.executable,'-B',w/'independent.py'],check=True)
 addon=w/'after-228-development-388.py';assert h(addon)=='d98d6c400f8b1ee8cb67fc6c764c31b1043644558bd3fcbae87841085e7e6bfd'
 subprocess.run([sys.executable,'-Bu',addon],check=True)
 checker=Path('/tmp/yangtze-hankou292/handoff/offer-late.py');assert h(checker)=='75ce5056d2af40ee244a053b0e673be5e8a87680ef5c0288a57a4abde6eb8f1c'
 late=checker.parents[1]/'228-distant-viewer-returned.json';distant=ev/'distant/closed.json'
 if not late.is_file():subprocess.run([sys.executable,'-Bu',checker,distant],check=True)
 a=r(late);assert a['host_sha256']==h(distant) and a['host_report_sha256']==r(distant)['report_sha256'] and a['previous_sha256']==h(out292) and a['all_children_exited'] and a['remaining_children']==[]
 assert a.get('deferred') or isinstance(a['exit_code'],int)
 print('All 228 main-scene sessions have closed. Inspect the ten actual views.',flush=True)
