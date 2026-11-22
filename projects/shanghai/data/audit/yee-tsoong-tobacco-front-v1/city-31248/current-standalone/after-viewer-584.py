"""Hand the completed 248 independent exhibit to the registered May Lee Court workflow."""
from pathlib import Path
import hashlib,json,subprocess,sys
host=Path('/tmp/shanghai-main-248/formal-31248');d=Path('/dev/shm/root-maylee584/development-native');entry=d/'link-248.py'
digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
read=lambda f:json.loads(f.read_bytes())
receipt=host/'current-standalone/closed.json'
assert digest(entry)=='60ef3d3d843cb2d964496c50cb25ffb7fd3ccb059aa48d42d327be0e0184c9a9'
r=read(receipt);assert r['passed'] and r['phase']=='independent' and r['order']==248 and r['exit_code']==0 and not r['remaining'] and r['chromium']
assert len(r['views'])==4 and len(r['downloads'])==4 and digest(Path(r['report']))==r['report_sha256']
subprocess.run([sys.executable,'-Bu',entry,receipt],check=True)
ret=d/'early-development-returned.json';j=read(ret);assert j['passed'] and j['exit_code']==0 and j['host_sha256']==digest(receipt) and j['all_children_exited'] and not j['remaining_children']
assert digest(Path(j['physical']))==j['physical_sha256']
