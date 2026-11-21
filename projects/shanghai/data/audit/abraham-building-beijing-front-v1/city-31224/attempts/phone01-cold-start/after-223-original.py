from pathlib import Path
import fcntl,hashlib,json,os,subprocess,sys,time
w=Path(__file__).parent
p=Path('/workspace/e-resource/projects/shanghai')
m=Path('/tmp/shanghai-main-223/223-map-slot-released.json')
def call(*v,env=None):
 subprocess.run([sys.executable,'-Bu',*v],check=True,env=env)
with (w/'admission.lock').open('a')as gate:
 fcntl.flock(gate,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not m.exists():time.sleep(5)
 r=json.loads(m.read_bytes());assert r['order']==223 and r['exit_code']==0 and not r['remaining_chromium']
 call(w/'local-catalogs.py','restore') if (w/'catalogs-ready.json').exists() else None
 call(w/'run-224-separated.py',m)
 call(w/'merge-224.py');call(w/'viewer.py','--assigned-standalone-slot')
 for n in (223,224):
  full=Path(f'/tmp/shanghai-yongjia-porch/scenes/{n}-all-http.json')
  if not full.is_file():call('/tmp/shanghai-yongjia-porch/release.py','all-http',str(n))
  q=json.loads(full.read_bytes());assert q['passed'] and q['production_receipt_sha256']==hashlib.sha256((w/f'{n}-production.json').read_bytes()).hexdigest()
  save=w/f'{n}-all-http.json'
  if not save.exists():os.link(full,save)
 guest=Path('/tmp/dingxiang-three-372/development-native/after-224.py');assert hashlib.sha256(guest.read_bytes()).hexdigest()=='dfc8a68604b27b91775aeb20018e5a3a5265c3c1b7359dbd581dd5bd4ea784f4'
 call(guest,w/'viewer-31224/closed.json',Path('/tmp/blackstone361/224-pilot-closed.json'))
 call(w/'archive.py','224');call(w/'local-catalogs.py','store')
 print('224 sessions are available for actual image review',flush=True)
