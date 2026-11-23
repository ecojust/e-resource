"""Bind the Money Guild's two actual city versions and run the ten site sessions."""
from pathlib import Path as P
from urllib.request import urlopen
from hashlib import sha256
import fcntl,sys,gzip,json,subprocess,os,shutil
u=P(__file__).parent;h=P('/tmp/shanghai-main-277');w=h/'formal-31277';d=P('/workspace/shanghai-publisher-preservation/city-277');p=P('/workspace/e-resource/projects/shanghai')
read=lambda f:json.loads(f.read_bytes());hashb=lambda b:sha256(b).hexdigest();sha=lambda f:hashb(f.read_bytes())
def fetch(url,checksum):
 with urlopen(url,timeout=100) as r:assert r.status==200;b=r.read()
 assert hashb(b)==checksum,url
 return b
def bind(t,b):
 if t.is_file():
  assert t.read_bytes()==b,t
  return
 store=u/'inputs'/hashb(b);store.parent.mkdir(exist_ok=True)
 if not store.exists():store.write_bytes(b)
 assert store.read_bytes()==b
 t.parent.mkdir(exist_ok=True,parents=True);tmp=t.with_name(t.name+'.pending')
 if tmp.is_symlink():tmp.unlink()
 tmp.symlink_to(store);tmp.replace(t)
with (u/'admission.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 sig=read(d.parent/'276-master-confirmed.json');assert sig['master']=='71de2c68976956ff9968ad60fab3a81f53d2373c' and sig['model_commit']=='ab5394498bb9d0980c1ee057d2ca18b612aa6419'and sig['normal_https_verified']==39
 public=fetch('https://raw.githubusercontent.com/ecojust/e-resource/'+sig['master']+'/'+sig['publication_path'],sig['publication_sha256']);assert json.loads(public)['commit']==sig['model_commit']
 prev=P('/tmp/shanghai-main-276/276-map-slot-released.json');assert sha(prev)=='afd4db797c5b2e4b2b95a80e5e2d3e9a5cb15a7f08639e00e9f54e609bfc0737';subprocess.run([sys.executable,'-B',w/'check-parent-276-live.py',prev],check=True)
 guest=P('/dev/shm/root-hongji696/development-native');assert sha(guest/'early-development-returned.json')=='2bae0ece29bbcf736b6968963abf30c129c6ebfc318be3bfc418217716ad15b5';assert sha(guest/'complete-276.py')=='8f50d88e185911a8f2f059d32232888fe731e4d4a3167eebd3ddec4f5c01c21f';subprocess.run([sys.executable,'-B',guest/'complete-276.py','verify',prev],check=True)
 pins=read(w/'live-inputs.json');assert all(sha(w/k)==v for k,v in pins['frozen_program_and_inputs'].items());site=read(w/'signed-comparison.json')
 for stage in site['stages']:
  n=stage['n'];prod=read(w/f'{n}-production.json');assert sha(w/f'{n}-production.json')==stage['production_sha256']
  for name,entry in stage['actual_reads'].items():
   b=fetch(entry['url'],prod['files'][name]);assert len(b)==entry['bytes'] and hashb(b)==entry['sha256']
   # Source and authored model trees are shared inputs and already pinned in the original 277 root.
   if name.startswith(('src/','data/')) or name in ['index.html','landmarks.html']:bind(w/f'stage{n}'/name,b)
  for name,entry in site['original_city_bindings_retrieved_on_both'].items():assert len(fetch(stage['origin']+name,entry['sha256']))==entry['bytes']
 manifest='assets/models/candidates/'+pins['id']+'/manifest.json';book=read(w/'277-production.json')['files'];viewer={}
 for name in (manifest,'shanghai-money-guild-front.html','src/candidate-asset-viewer.js'):
  b=fetch('http://127.0.0.1:31277/'+name,book[name]);bind(d/'signed-ordinary-viewer'/name,b);viewer[name]=book[name]
 mark=dict(inputs=viewer,production_sha256=sha(w/'277-production.json'),driver_sha256=sha(d/'formal-viewer.cjs'));(d/'formal-viewer-sources.json').write_text(json.dumps(mark,indent=2)+'\n')
 subprocess.run([sys.executable,'-Bu',w/'sequence-live.py'],check=True)
 if not(w/'current-standalone/closed.json').is_file():subprocess.run([sys.executable,'-Bu',d/'actual-viewer.py'],check=True)
 print('All formal city views, the six earlier photographs and current four-view download session completed',flush=True)
