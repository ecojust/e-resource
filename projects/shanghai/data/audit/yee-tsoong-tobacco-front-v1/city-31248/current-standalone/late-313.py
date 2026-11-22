"""Use the original mobile-pin admission after the deferred 313 model has its serving snapshot."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

host=Path('/tmp/shanghai-main-248/formal-31248')
guest=Path('/tmp/kangding313')
def read(p):
    return json.loads(p.read_bytes())
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
first=host/'313-viewer-deferred.json'
original=host/'isolated-evidence/mobile-pin/closed.json'
assert read(first)['deferred'] and read(first)['source_sha256']==sha(original)
final=host/'current-standalone/closed.json'
assert read(final)['passed'] and read(final)['exit_code']==0
prior=Path('/dev/shm/root-maylee584/development-native/early-development-returned.json')
assert read(prior)['passed'] and read(prior)['host_sha256']==sha(final)
scenes=Path('/tmp/shanghai-yongjia-porch/scenes')
while not all(p.is_file() for p in (guest/'raw-313-confirmed.json',scenes/'313-comparison.json',scenes/'313-all-http.json')):
    time.sleep(3)
assert read(scenes/'313-all-http.json')['passed'] and read(scenes/'313-comparison.json')['passed']
stamp=datetime.now(timezone.utc).isoformat()
entry=guest/'handoff/admit-after-restart.py'
assert sha(entry)==read(guest/'handoff/recovered-host-programs.json')['files'][entry.name]
if not (guest/'viewer-closed.json').is_file():
    subprocess.run([sys.executable,'-Bu',entry,'viewer',original],check=True)
done=guest/'viewer-closed.json'
r=read(done)
assert r['passed'] and r['exit']==0 and not r['remaining'] and r['wrapper_closed'] and r['all_processes_closed']
assert (r['views'],r['downloads'])==(6,4) and r['host_receipt_sha256']==sha(original) and r['receipt_sha256']==sha(Path(r['report']))
result={'order':313,'host':248,'passed':True,'started':stamp,'finished':datetime.now(timezone.utc).isoformat(),'original_defer_sha256':sha(first),'original_mobile_pin_sha256':sha(original),'current_standalone_sha256':sha(final),'after_584_sha256':sha(prior),'viewer_closed_sha256':sha(done),'full_http_sha256':sha(scenes/'313-all-http.json')}
out=host/'313-viewer-after-584.json'
out.write_text(json.dumps(result,indent=2)+'\n')
