"""Offer the current city pause to the author of the verified 325 facade and validate its outcome."""
from pathlib import Path
import fcntl,json,subprocess,sys
from guest_result import verify,load,digest
w=Path(__file__).parent;g=Path('/tmp/pan325');p=Path('/tmp/sta-xiong324')
kind=sys.argv[1]; assert kind in ('native','viewer')
phase='before' if kind=='native' else 'phone'
slot=w/'evidence/260'/('before' if kind=='native' else 'separate/phone')/'closed.json'
r=load(slot);report=Path(r['report']);rh=digest(report);s=digest(slot)
assert r['order']==260 and r['phase']==phase and r['exit']==r['exit_code']==0 and r['node_closed'] and r['chromium_pids'] and r['remaining']==r['remaining_chromium']==[]
actual=load(report);assert actual['section']==phase and actual['completed'] and rh==r['report_sha256']
info=dict(order=325,host=260,phase=kind,host_closed=str(slot),host_closed_sha256=s,host_report_sha256=rh)
bind=w/'guest-325-recovered.json';admit=g/'handoff/admit-window-recovered.py'
def write(key,data):
 target=w/f'325-{kind}-{key}.json';payload=(json.dumps({**info,**data},ensure_ascii=False,indent=2)+'\n').encode()
 if target.exists():
  if target.read_bytes()==payload:return
  previous=load(target)
  if key!='deferred' or not previous.get('deferred') or any(info[k]!=previous.get(k) for k in info):
   raise AssertionError((target,'prior receipt differs'))
  # Keep each verified deferral while its actual prerequisites change.
  previous_name=target.with_name(target.stem+'-'+digest(target)[:16]+target.suffix)
  if not previous_name.exists():previous_name.hardlink_to(target)
  assert digest(previous_name)==digest(target)
 temp=target.with_suffix('.part');temp.write_bytes(payload);temp.replace(target)
def num(v):return len(v) if isinstance(v,(dict,list))else v
with (w/f'325-{kind}.lock').open('a') as f:
 fcntl.flock(f,fcntl.LOCK_EX)
 needs=[p/'native-closed.json',p/'raw-324-confirmed.json',bind,admit]
 if kind=='viewer':needs+=[p/'viewer-closed.json',g/'native-closed.json',g/'raw-325-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/325-comparison.json')]
 missing=[str(x) for x in needs if not x.is_file()]
 if missing:write('deferred',dict(deferred=True,started=False,attempted=False,native_started=False,viewer_started=False,missing=missing));sys.exit(0)
 for i in [p/'native-closed.json']+([p/'viewer-closed.json',g/'native-closed.json'] if kind=='viewer' else []):
  a=load(i);assert a['order']==(324 if i.parent==p else 325) and a['passed'] and a['exit']==0 and a.get('remaining',[])==[] and a.get('remaining_chromium',[])==[] and a.get('remaining_blender',[])==[]
 for i in [p/'raw-324-confirmed.json']+([g/'raw-325-confirmed.json'] if kind=='viewer' else []):
  row=load(i);assert row['order']==(324 if i.parent==p else 325) and digest(row['snapshot'])==row['sha256'] and Path(row['root']).is_dir()
  cat='data/candidate-city-integrations.json';snap=load(row['snapshot']);assert row['catalog_sha256']==snap['files'][cat]==digest(Path(row['root'])/'projects/shanghai'/cat) and row['count']==snap['resulting_count']
 b=load(bind);assert b['host']==260 and b['order']==325 and b['admit']==str(admit) and digest(admit)==b['admit_sha256'] and digest(b['dispatch'])==b['dispatch_sha256']
 if kind=='viewer':assert load(needs[-1])['passed']
 outcomes=[g/(kind+'-closed.json'),g/('260-'+kind+'-deferred.json'),g/('260-'+kind+'-failed.json')]
 def match():return [t for t in outcomes if t.is_file() and load(t).get('host_receipt_sha256')==s]
 found=match()
 if not found:
  proc=subprocess.run([sys.executable,'-Bu',admit,kind,slot])
  found=match();assert proc.returncode==0 or (found and found==[outcomes[-1]]),(proc.returncode,found)
 assert len(found)==1,found
 q=found[0];state=verify(kind,slot,q)
 completed_contract=load(q).get('dispatch_sha256',b['dispatch_sha256'])
 if completed_contract!=b['dispatch_sha256']:
  prior=Path('/workspace/shanghai-publisher-preservation/city-260/before-325-front-default/1-dispatch-recovered.json')
  assert state=='complete' and kind=='native' and digest(prior)==completed_contract
 write('returned' if state=='complete' else 'deferred',dict(passed=state=='complete',deferred=state!='complete',state=state,actual_receipt=str(q),sha256=digest(q),dispatch_sha256=completed_contract))
