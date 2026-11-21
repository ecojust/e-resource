"""Offer the signed 268 page the interval after all 203 city renderers have exited."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
from urllib.request import urlopen
import json,socket
w=Path(__file__).resolve().parent
s=Path('/tmp/shamei268')
def read(p):return json.loads(p.read_bytes())
def sig(p):return sha256(p.read_bytes()).hexdigest()
def write(p,q):
    if p.exists():return
    t=p.with_suffix('.tmp');t.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');t.replace(p)
phases=read(w/'isolated-inputs.json')['stage_order']
for phase in phases:
    closed=w/'isolated-evidence'/phase/'closed.json'
    row=read(closed)
    assert row['exit_code']==0 and row['cdp_closed'] and not row['remaining_chromium']
    assert row['report_sha256']==sig(Path(row['report']))
assert phase=='distant'
with socket.socket() as sock:assert sock.connect_ex(('127.0.0.1',19503))!=0
n=Path('/tmp/hengfeng267/native-closed.json')
rawprev=Path('/tmp/hengfeng267/raw-267-confirmed.json')
viewerprev=Path('/tmp/hengfeng267/viewer-closed.json')
native=s/'native-closed.json';raw=s/'raw-268-confirmed.json'
comp=Path('/tmp/shanghai-yongjia-porch/scenes/268-comparison.json')
req=[n,rawprev,viewerprev,native,raw,comp]
q={'order':268,'previous_session':str(closed),'previous_session_sha256':sig(closed),'previous_browser_report_sha256':row['report_sha256'],'remaining_chromium':[],'time':datetime.now(timezone.utc).isoformat()}
reason=None
try:
    for p in req:assert p.is_file(),str(p)
    assert read(comp)['passed'] is True
    for p in [native,n,viewerprev]:
        r=read(p);assert next((r[k] for k in ['exit','exit_code','returncode'] if k in r),None)==0 and not any(r.get(k) for k in ['remaining','remaining_chromium','remaining_blender','remaining_oidn'])
    for p,order in [(rawprev,267),(raw,268)]:
        r=read(p);snapshot=Path(r['snapshot']);assert r['order']==order and sig(snapshot)==r['sha256']
    filename='somekh-building-street-corner.html'
    expected=read(snapshot)['files'][filename]
    with urlopen('http://127.0.0.1:31268/'+filename,timeout=7) as resp:
        body=resp.read()
        assert resp.status==200 and sha256(body).hexdigest()==expected
except (OSError,KeyError,AssertionError,ValueError) as exc:
    reason=repr(exc)
if reason is None:
    q.update(authorized=True,predecessor_receipts={str(p):sig(p) for p in req},served_html_sha256=expected)
    target=w/'268-final-viewer-window.json'
else:
    q.update(authorized=False,reason=reason)
    target=w/'268-final-viewer-deferred.json'
write(target,q)
print(target)
