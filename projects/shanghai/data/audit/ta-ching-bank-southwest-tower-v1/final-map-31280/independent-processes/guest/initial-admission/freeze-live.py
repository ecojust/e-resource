"""Record the current two physical offers against the intact earlier contract."""
from pathlib import Path
import argparse, datetime, hashlib, json, os
p=argparse.ArgumentParser()
p.add_argument('--before',required=True,type=Path)
p.add_argument('--phone',required=True,type=Path)
args=p.parse_args()
w=Path('/tmp/anhe345');h=w/'mapping/handoff';host=Path('/tmp/shanghai-main-280')
archive=h/'frozen-contracts';archive.mkdir(exist_ok=True)
def sha(path):
 with path.open('rb') as fp:return hashlib.file_digest(fp,'sha256').hexdigest()
def write(p,data):
 b=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
 if p.is_file():
  old=p.read_bytes()
  if b==old:return
  target=archive/(sha(p)+'-'+p.name)
  if not target.exists():target.write_bytes(old)
 t=p.with_suffix(p.suffix+'.new');t.write_bytes(b);t.replace(p)
oldpath=h/'dispatch-recovered.json';old=json.loads(oldpath.read_bytes())
pins=dict(old['physical_inputs'])
assert all(sha(Path(s))==digest for s,digest in pins.items())
inputs=(*[h/n for n in ('admit-live.py','run-phase-live.py','six-view-live.cjs','run-345-devices.py','chromium-345-mesa','official-viewer-files.py','split-scratch.py','blender-one')],Path('/workspace/.e-resource-recovery/toolchain/node_modules/gltfpack/cli.js'),Path('/workspace/.e-resource-recovery/toolchain/one-thread/oidn-single.py'),oldpath)
for directory,names in [('/tmp/guangci344',('native-closed.json','viewer-closed.json','raw-344-confirmed.json')),('/tmp/shanghai-main-279',('344-native-returned.json','344-viewer-returned.json'))]:
 for n in names:
  q=Path(directory)/n
  if q.is_file():pins[str(q)]=sha(q)
for f in inputs:pins[str(f)]=sha(f)
stages={}
for stage,src in [('before',args.before),('phone',args.phone)]:
 sig=sha(src);physical=archive/(sig+'.cjs')
 if not physical.exists():physical.write_bytes(src.read_bytes())
 pins[str(physical)]=sig;stages[stage]=[sig]
dispatch={**old,'physical_inputs':pins,'phase_source_sha256':stages,'historical_dispatch_sha256':sha(oldpath),'historical_input_count':len(old['physical_inputs']),'predecessor_actual':344,'device_processes':2}
write(h/'dispatch-live.json',dispatch)
source=host/'guest-345-recovered.json';guest=json.loads(source.read_bytes());write(host/'guest-345-live.json',{**guest,'historical_guest_sha256':sha(source),'dispatch_sha256':sha(h/'dispatch-live.json'),'admission_sha256':sha(h/'admit-live.py'),'host_phase_sources':stages})
print(sha(h/'dispatch-live.json'),sha(host/'guest-345-live.json'),len(pins))
