"""Use the original phone receipt after the 305 catalog arrives and the roof camera physically quits."""
from sequence import handoff, w,e,r,h,write
from pathlib import Path
import time
c=e/'old-roof/closed.json'
while not c.is_file():time.sleep(.3)
record=r(c)
assert record['node_closed'] and not record['remaining'] and record['chromium_pids']
assert h(e/'old-roof/browser.json')==record['report_sha256']
sig=Path('/tmp/shanghai-yongjia-porch/scenes/305-comparison.json')
assert r(sig)['passed'] and r(sig)['port']==31305
handoff('viewer',e/'phone/closed.json')
done=Path('/tmp/shi-tongren305/viewer-closed.json')
if not done.is_file():raise RuntimeError('Physical guest did not certify the independent page')
write(w/'305-returned-on-roof.json',dict(host_close=str(c),host_sha256=h(c),phone_sha256=h(e/'phone/closed.json'),physical=str(done),physical_sha256=h(done),previous_viewer_deferred=h(w/'archived-305-admissions/305-viewer-gate.json'),all_children_exited=True,remaining=[]))
print(h(done),flush=True)
