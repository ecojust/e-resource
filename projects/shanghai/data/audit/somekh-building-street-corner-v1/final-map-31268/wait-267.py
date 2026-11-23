from pathlib import Path
from hashlib import sha256
import sys,time,fcntl,subprocess,json
q=Path(__file__).parent;w=q/'final-map-31268';before=Path('/tmp/shanghai-main-267/267-map-slot-released.json')
with(q/'gate.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not before.is_file():time.sleep(10)
 p=json.loads(before.read_bytes());assert p['order']==267 and p['passed']and p.get('all_captures_visually_reviewed',p.get('views_reviewed'))and not p['remaining_chromium']and p['exit_code']==0 and p['reports']and p.get('final_closed_at',p.get('finished')) and p['screenshots'] and set(p['actual_saved_downloads'])=={'native','raw','full','lod'}
 for script in ['bind.py','prewarm.py','sequence.py']:
  subprocess.run([sys.executable,'-Bu',w/script],check=True)
 if not(w/'standalone-closed.json').exists():subprocess.run([sys.executable,'-Bu',w/'standalone.py'],check=True)
 subprocess.run([sys.executable,'-Bu',q/'finish-reviewed.py'],check=True,stdout=(q/'unreviewed-inventory.json').open('w'))
