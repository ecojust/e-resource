"""Offer the empty 226 map slot to the Pathé house after the seven map processes and 367 have returned."""
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys
from pathlib import Path
host=Path(__file__).resolve().parent
guest=Path('/tmp/pathe-hengshan-380/development-native')
author=Path('/workspace/e-resource/projects/shanghai/data/audit/pathe-records-office-v1/preflight/model-review.json')
ready=guest/'author-ready.json'
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def persist(p,value):
 scratch=p.with_suffix('.new');scratch.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');scratch.replace(p)
now=lambda:datetime.now(timezone.utc).isoformat()
events=[]
for phase in ('before','phone','desktop','architecture','mouse','touch','distant'):
 receipt=host/phase/'process.json'
 report=receipt.with_name('control-browser.json' if phase=='before' else 'main-browser.json')
 row=read(receipt);assert row['phase']==phase and row['exit_code']==0 and row['node_closed']
 assert row['node_pids'] and row['chromium_pids'] and row['remaining_chromium']==row['remaining_children']==[]
 assert row['report_sha256']==sha(report) and read(report)['completed']
 events.append(dict(phase=phase,receipt=str(receipt),receipt_sha256=sha(receipt),report=str(report),report_sha256=sha(report)))
previous=Path('/tmp/anfu233-367/mapping/226-distant-city-closed.json');ended=read(previous)
assert ended['order']==367 and ended['host']==226 and ended['all_children_exited'] and ended['remaining_children']==[]
assert ended['host_receipt_sha256']==events[-1]['receipt_sha256'] and ended['host_report_sha256']==events[-1]['report_sha256']
prior=host/'through-distant-and-367.json'
inputs=dict(host=226,phase='after-distant',all_children_exited=True,remaining_children=[],phase_processes=events,
            previous=str(previous),previous_sha256=sha(previous))
if prior.exists():assert read(prior)==inputs
else:persist(prior,inputs)
out=host/'380-development-returned.json'
if out.exists():
 old=read(out);assert old['host_sha256']==sha(prior) and old['all_children_exited'] and not old['remaining_children']
 if not old.get('deferred'):sys.exit(0)
missing=[str(p)for p in [author,ready]if not p.is_file()]
base=dict(order=380,host=226,host_sha256=sha(prior),previous_sha256=sha(previous))
if missing:
 persist(out,dict(**base,attempted=False,deferred=True,missing=missing,all_children_exited=True,remaining_children=[],ended=now()));sys.exit(0)
signature=sha(author);inputs=read(ready)
assert inputs['order']==380 and inputs['author_sha256']==signature and read(author)['passed']
assert read(author)['accepted_manifest_sha256']==sha(guest.parent/'packaged/manifest.json')==inputs['manifest_sha256']
entry=guest/'start.py';assert sha(entry)=='bed5c7d3598f16707c13b53ae823d0a47cedbd9160605878e543a99ced4cc696'
proc=subprocess.run([sys.executable,'-Bu',entry,prior,signature],env={**os.environ,'PATHEOFFICE_WORKFILES':os.environ.get('PATHEOFFICE_WORKFILES','/tmp')},check=False)
closed=guest/'physical.json';r=read(closed);assert r['order']==380 and r['all_children_exited'] and not r['remaining_children']
assert r['exit_code']==proc.returncode and r['passed']==(proc.returncode==0)
assert all(sha(guest/key)==h for key,h in r['reports'].items())
if r['passed']:
 assert {'manifest.json','geometry-native.json','verified-editable.json','storage/development-views/viewer.json'}<=set(r['reports'])
assert read(guest/'admit.json')['previous_sha256']==sha(prior) and read(guest/'admit.json')['author_sha256']==signature
persist(out,dict(**base,attempted=True,deferred=False,passed=r['passed'],exit_code=r['exit_code'],
     physical=str(closed),physical_sha256=sha(closed),author_sha256=signature,all_children_exited=True,remaining_children=[],ended=now()))
