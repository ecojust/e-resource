"""Use the completed ordinary viewer after the original phone window and last city camera."""
from pathlib import Path
from hashlib import sha256
import json, subprocess,sys,os,time
w=Path('/tmp/shanghai-main-250');g=Path('/tmp/eye-residence315')
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:sha256(p.read_bytes()).hexdigest()
late=w/'evidence/250/separate/distant/closed.json'; original=w/'evidence/phone/closed.json'
for f in (original,late):
    c=read(f);assert c['node_closed'] and c['exit']==0 and c['chromium_pids'] and not c['remaining']
    assert sha(Path(c['report']))==c['report_sha256'] and read(Path(c['report']))['completed']
required=[g/'raw-315-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/315-all-http.json'),Path('/tmp/shanghai-yongjia-porch/scenes/315-comparison.json')]
while not all(f.is_file() for f in required):time.sleep(3)
assert read(required[0])['passed'] and read(required[0])['order']==315
assert read(required[1])['passed'] and read(required[1])['count']>2300
assert read(required[2])['passed'] and read(required[2])['order']==315
before=w/'315-viewer-deferred.json';history=w/'original-315-phone-defer.json'
if before.is_file():
 d=read(before);assert d['deferred'] and not d['native_started'] and not d['viewer_started'] and d['host_closed_sha256']==sha(original)
 if history.exists():assert history.read_bytes()==before.read_bytes();before.unlink()
 else:before.rename(history)
subprocess.run([sys.executable,'-Bu',w/'offer-315-after-restart.py','viewer'],check=True)
c=read(g/'viewer-closed.json')
assert c['passed'] and c['exit']==0 and c['host_receipt_sha256']==sha(original) and c['views']==6 and c['downloads']==4 and not c['remaining_chromium']
print('315 standalone',sha(g/'viewer-closed.json'),'after',sha(late),flush=True)
