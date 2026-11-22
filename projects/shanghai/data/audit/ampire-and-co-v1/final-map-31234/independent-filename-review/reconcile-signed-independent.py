"""Read the original browser close and validate the saved files using the producing driver's four view names."""
from pathlib import Path
from hashlib import sha256
import json,shutil
q=Path(__file__).parent;w=q/'final-map-31234';d=w/'standalone-31234';signed=w/'standalone-signed'
def h(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
f=w/'standalone-closed.json';bk=w/'independent-filename-review';bk.mkdir(exist_ok=True)
for src in (f,w/'standalone.py',q/'second-distant-calibrated.log'):
 t=bk/src.name
 if not t.exists():shutil.copyfile(src,t)
original=read(bk/f.name);r=read(d/'viewer.json');prog=q/'signed-four-downloads.cjs'
assert original['exit']==0 and original['chromium_pids'] and not(original['chromium_remaining']or original['remaining_observed']) and original['report_sha256']==h(d/'viewer.json') and original['formal_port']==31234
assert r['passed'] and r['base']=='http://127.0.0.1:31234/' and r['scriptSHA256']==h(prog)
m=read(signed/'assets/models/candidates'/r['id']/'manifest.json');source=signed/'source-inputs.json'
assert len(read(source))==3 and r['id']=='huangpu-ampire-and-co-building' and r['manifestSHA256']==h(signed/'assets/models/candidates'/r['id']/'manifest.json')
assert {(v['filename'],v['role'],v['mode'])for v in r['views']}=={('viewer-'+device+'-'+role+(''if mode=='front'else'-'+mode)+'.png',role,mode)for device in ('desktop','mobile')for role,mode in [('full','front'),('lod','oblique')]}
for v in r['views']:assert h(d/v['filename'])==v['sha256']
for role,asset in m['assets'].items():
 item=r['downloads'][role];z=d/item['saved'];assert item['saveAsVerified'] and z.name==item['file']==asset['file'] and z.stat().st_size==item['bytes']==asset['bytes'] and h(z)==item['sha256']==asset['sha256']
closed=dict(original,source_inputs=str(source),source_inputs_sha256=h(source),driver_sha256=h(prog),original_physical_close_sha256=h(bk/f.name),validation_source_sha256=h(Path(__file__)))
t=f.with_suffix('.reviewed');t.write_text(json.dumps(closed,indent=2)+'\n');t.replace(f)
p=w/'standalone.py';text=p.read_text();old="{'viewer-'+device+'-'+role+'.png'for device in ('desktop','mobile')for role in ('full','lod')}";new="{'viewer-'+device+'-'+suffix+'.png'for device in ('desktop','mobile')for suffix in ('full','lod-oblique')}"
if old in text:
 t=p.with_suffix('.corrected');t.write_text(text.replace(old,new));t.replace(p)
print(h(f))
