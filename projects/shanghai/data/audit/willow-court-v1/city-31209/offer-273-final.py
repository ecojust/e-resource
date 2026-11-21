"""Offer the signed bank viewer after the physically closed Willow Court distant view."""
from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256
from datetime import datetime, timezone
import json,time
w=Path(__file__).resolve().parent;bank=Path('/tmp/shanghaibank273')
def rd(p):return json.loads(p.read_bytes())
def sign(p):return sha256(p.read_bytes()).hexdigest()
def physical(p):
 b=rd(p);exitcode=b.get('exit',b.get('exit_code'));assert b['passed'] and exitcode==0 and not any(b.get(k)for k in ['remaining_chromium','remaining','remaining_blender']);return b
def save(name,blob):
 f=w/name
 if f.exists():assert rd(f)['previous_session_sha256']==blob['previous_session_sha256'];return
 tmp=f.with_suffix('.previous');tmp.write_text(json.dumps(blob,indent=2)+'\n');tmp.replace(f)
end=bank/'viewer-closed.json';prior=w/'isolated-evidence/distant/closed.json';r=rd(prior);assert r['phase']=='distant'and r['exit_code']==0 and not r['remaining_chromium']and r['remaining']==[]and r['cdp_closed']
report=Path(r['report']);assert sign(report)==r['report_sha256']and rd(report)['completed']
base=dict(order=273,host=209,previous_session=str(prior),previous_session_sha256=sign(prior),previous_browser_report_sha256=sign(report),remaining_chromium=[],at=datetime.now(timezone.utc).isoformat())
if end.exists():physical(end);raise SystemExit()
required=[Path('/tmp/saltbank272/viewer-closed.json'),bank/'native-closed.json',bank/'raw-273-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/273-comparison.json')];missing=[str(p)for p in required if not p.is_file()]
if not missing:
 physical(required[0]);physical(required[1]);raw=rd(required[2]);assert raw['order']==273 and sign(Path(raw['snapshot']))==raw['sha256'];layer=rd(required[-1]);assert layer['passed']and layer['port']==31273
 try:
  with urlopen('http://127.0.0.1:31273/shanghai-commercial-savings-bank-pavilion.html',timeout=6)as res:
   body=res.read();assert res.status==200 and b'showCandidateAssetViewer' in body
 except OSError as e:missing.append(str(e))
if missing:
 save('273-final-viewer-deferred.json',{**base,'authorized':False,'started':False,'deferred':True,'missing':missing});raise SystemExit()
save('273-final-viewer-window.json',{**base,'authorized':True,'actual_predecessors':{str(p):sign(p)for p in required}})
while not end.is_file():
 failed=w/'273-final-viewer-failed.json'
 if failed.is_file():
  x=rd(failed);assert x['previous_session_sha256']==sign(prior) and x['exit']!=0 and x['remaining_chromium']==[];raise SystemExit()
 time.sleep(1.5)
physical(end)
