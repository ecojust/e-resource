"""Verify the regenerated Changshu Road model inputs before a native or browser session."""
from pathlib import Path
import hashlib,json,sys,subprocess
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
offer=Path('/workspace/shanghai-publisher-preservation/city-257/guest-322-native-label.json')
assert sha(offer)=='0b494cab28ad9c818d9843350693cf7ff8eb0087c50ed8826e3657207ec8820d'
r=json.loads(offer.read_bytes())
for kind,field in [('admit','admit'),('dispatch','dispatch')]:assert sha(r[field])==r['authorized_sha256'][kind]
kind,host=sys.argv[1:];assert kind in ('viewer','native')
if kind=='viewer':
    import time
    stage=Path('/tmp/shanghai-yongjia-porch/scenes/322-comparison.json')
    original=Path('/tmp/changshu322/raw-322-confirmed.json')
    while not (stage.is_file() and original.is_file()):time.sleep(2)
    assert json.loads(stage.read_bytes())['passed']
receipt=Path(r['closed'][kind=='viewer'])
if not receipt.is_file():subprocess.run([sys.executable,'-Bu',r['admit'],kind,host],check=True)
out=json.loads(receipt.read_bytes());assert out['order']==322 and out['host']==257 and out['passed'] and out['exit']==0 and not out['remaining']
assert out['dispatch_sha256']==sha(r['dispatch']) and out['host_receipt_sha256']==sha(host)
