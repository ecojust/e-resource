"""Schedule the Lunghwa stair's development native and viewer in the confirmed Seventy-fifth group's final slot."""
from pathlib import Path
from hashlib import sha256
import json,sys,subprocess,os
host=Path(__file__).parent;city=host/'final-map-31234';q=Path('/tmp/longhua-terminal397/development-native')
def sha(f):
 with f.open('rb')as r:return __import__('hashlib').file_digest(r,'sha256').hexdigest()
def read(f):return json.loads(f.read_bytes())
def write(f,x):
 b=(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
 if f.is_file():assert f.read_bytes()==b
 else:
  t=f.with_suffix('.new');t.write_bytes(b);t.replace(f)
source=city/'distant/process.json';stand=city/'standalone-closed.json';a=read(stand);s=read(source)
assert s['phase']=='distant'and s['node_closed']and s['exit_code']==0 and s['chromium_pids']and not(s['remaining_children']or s['remaining_chromium'])
rr=city/'distant/main-browser.json';assert sha(rr)==s['report_sha256']and read(rr)['completed']
sr=city/'standalone-31234/viewer.json';assert a['exit']==0 and a['chromium_pids'] and not(a['remaining_observed']or a['chromium_remaining']) and a['report_sha256']==sha(sr) and read(sr)['passed']
last=Path('/tmp/jixian299/234-formal-viewer-returned.json');d=read(last);assert d['order']==299 and d['host']==234 and d['host_sha256']==sha(source) and not d['remaining_chromium']
sources={'city_closure':source,'city_report':rr,'standalone':stand,'standalone_report':sr,'299_outcome':last}
if d.get('started'):
 c=Path(d['closure']);o=read(c);assert d['closure_sha256']==sha(c) and o['node_closed'] and not o['remaining_chromium'];sources['299_closure']=c
else:assert d.get('passed')or d.get('deferred'),d
w=host/'397-prior-closed.json';write(w,dict(order=234,all_children_exited=True,remaining_children=[],sources={n:{'file':str(f),'sha256':sha(f)}for n,f in sources.items()}))
exe=q/'start.py';author=Path('/workspace/e-resource/projects/shanghai/data/audit/lunghwa-terminal-curved-stair-v1/preflight/model-review.json')
assert sha(exe)=='60093f9b1fb2219b9831b0023ef703d054bd6acacfc97acdf6571e91c403f49b' and sha(author)=='dd472f6aed7ebc4e5ae10345d63c30ce3998997f85c8be4d1a9d0f02732b912e'
rc=subprocess.run([sys.executable,'-Bu',exe,w,sha(author)]).returncode
physical=q/'physical.json';v=read(physical);assert v['exit_code']==rc and v['all_children_exited'] and not v['remaining_children']
write(host/'397-development-returned.json',dict(order=397,host=234,prior_sha256=sha(w),physical=str(physical),physical_sha256=sha(physical),passed=not rc,exit_code=rc,all_children_exited=True,remaining_children=[]))
