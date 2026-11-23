from pathlib import Path
from hashlib import sha256
import sys,time,fcntl,subprocess,json
q=Path(__file__).parent;w=q/'final-map-31272';before=Path('/tmp/shanghai-main-271/271-map-slot-released.json')
assert sha256((w/'standalone-recovered.py').read_bytes()).hexdigest()=='7cae7710fe8a5b7ce83b80e25a7bf2277d1d490a0fe9a897404d59a3b051935d'
assert sha256((q/'finish-reviewed-recovered.py').read_bytes()).hexdigest()=='43563c17c7f6ee16664770f7458f9e7ee542b8e97117e406e71a9096a579aec1'
with(q/'gate.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not before.is_file():time.sleep(10)
 p=json.loads(before.read_bytes());assert p['order']==271 and p['passed']and p.get('all_captures_visually_reviewed',p.get('views_reviewed'))and not p['remaining_chromium']and p['exit_code']==0 and p['reports']and p.get('final_closed_at',p.get('finished')) and p['screenshots'] and set(p['actual_saved_downloads'])=={'native','raw','full','lod'}
 for item in p['real_browser_process_exits'].values():
  if not isinstance(item,dict):continue
  for path_key,sha_key in [('closed','sha256'),('report','report_sha256')]:
   if path_key in item and sha_key in item:assert sha256(Path(item[path_key]).read_bytes()).hexdigest()==item[sha_key]
 for script in ['bind-observed.py','prewarm-current.py','sequence-recovered.py']:
  subprocess.run([sys.executable,'-Bu',w/script],check=True)
 if not(w/'standalone-closed.json').exists():subprocess.run([sys.executable,'-Bu',w/'standalone-recovered.py'],check=True)
 subprocess.run([sys.executable,'-Bu',q/'finish-reviewed-recovered.py'],check=True,stdout=(q/'unreviewed-inventory.json').open('w'))
