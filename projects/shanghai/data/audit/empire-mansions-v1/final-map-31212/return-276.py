"""Offer one supplemental bank-viewer session between the authentic previous-city and mobile sessions."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
w=Path(__file__).parent;q=Path('/tmp/hengli276')
def read(p):return json.loads(p.read_bytes())
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
host=w/'before/process.json';report=w/'before/control-browser.json'
h=read(host);r=read(report);bound=read(w/'bound-inputs.json')['211']
assert h['phase']=='before' and h['exit_code']==0 and h['node_closed'] and h['node_pids'] and h['chromium_pids']
assert h['remaining_chromium']==h['remaining_children']==[] and sha(report)==h['report_sha256']
assert r['id']=='xuhui-empire-mansions-street-front' and r['completed'] and r['server']==bound['origin'] and r['catalog']['sha256']==bound['catalog_sha256']
script=q/'offer-standalone-makeup.py';pin='de795954a445178b5787a2d96eff95356376af7463c208561ecc4f2c99e95bc6'
assert sha(script)==pin
local=w/'276-supplement-result.json'
if local.is_file():
 previous=read(local);assert previous['host_sha256']==sha(host)and sha(Path(previous['guest_record']))==previous['guest_record_sha256']
else:
 result=subprocess.run([sys.executable,'-Bu',script,'212',host])
 states=['handback','viewer-failed','viewer-deferred']
 outcome,=[(state,q/('212-supplement-'+state+'.json'))for state in states if (q/('212-supplement-'+state+'.json')).is_file() and read(q/('212-supplement-'+state+'.json')).get('host_receipt_sha256')==sha(host)]
 state,guest=outcome;d=read(guest);assert d['order']==276 and d['host_order']==212 and d['host_report_sha256']==sha(report)
 if state=='handback':
  receipt=q/'independent-closed.json';end=read(receipt)
  assert result.returncode==0 and d['passed'] and d['receipt_sha256']==sha(receipt)and end['passed']and end['exit']==0 and end['views']==6 and end['downloads']==4
 elif state=='viewer-failed':
  assert d['failed'] and d['attempted'] and not d['remaining'] and sha(Path(d['log']))==d['log_sha256']
 else:assert result.returncode==0 and d['missing'] and d['deferred'] and not d['started'] and not d['remaining']
 out=dict(order=212,guest=276,state=state,host_sha256=sha(host),report_sha256=sha(report),offer_sha256=pin,guest_record=str(guest),guest_record_sha256=sha(guest))
 tmp=local.with_suffix('.new');tmp.write_text(json.dumps(out,indent=2)+'\n');tmp.replace(local)
