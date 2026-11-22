from pathlib import Path
from hashlib import sha256
import sys,time,fcntl,subprocess,json
q=Path(__file__).parent;w=q/'final-map-31239';before=Path('/tmp/shanghai-main-238/238-map-slot-released.json')
with(q/'gate.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not before.is_file():time.sleep(10)
 p=json.loads(before.read_bytes());assert p['order']==238 and p['passed']and p['views_reviewed']and not p['remaining_chromium']and p['exit_code']==0 and p['reports']and p['final_closed_at'] and p['screenshots'] and set(p['actual_saved_downloads'])=={'native','raw','full','lod'}
 subprocess.run([sys.executable,'-Bu',w/'sequence.py'],check=True)
 if not(w/'standalone-closed.json').exists():subprocess.run([sys.executable,'-Bu',w/'standalone.py'],check=True)
 subprocess.run([sys.executable,'-Bu',q/'finish-reviewed.py'],check=True,stdout=(q/'unreviewed-inventory.json').open('w'))
