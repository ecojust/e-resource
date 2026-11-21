"""Preserve the first 338/352 executable and append the requested short checks after 352."""
from pathlib import Path
import hashlib,subprocess,sys
w=Path(__file__).parent
def run(path,digest,*args):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    subprocess.run([sys.executable,'-B',path,*args],check=True)
if sys.argv[1:]==['352']:
    import json
    take=lambda p:json.loads(p.read_bytes())
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    ret=take(w/'352-cpu-return.json')
    window=w/'independent-author-window-218.json'
    assert ret['independent_map_exit_sha256']==digest(window) and take(window)['all_children_exited'] and not take(window)['remaining_children']
    evidence=Path(ret['actual_return']);reported=take(evidence)
    assert ret['sha256']==digest(evidence) and ret['exit_code']==reported['exit_code'] and reported['prior_sha256']==digest(window) and not reported['remaining_children']
    later=take(w/'356-trial-return.json')
    assert later['previous_sha256']==digest(w/'352-cpu-return.json') and not later['remaining']
    last=take(Path('/tmp/park-fuxing338/surface-recheck-closed.json'))
    assert last['previous_sha256']==digest(w/'356-trial-return.json') and last['passed'] and not last['remaining']
else:
    run(w/'original-guest-338-and-352.py','87710ee4dd494e4fde1e33f6db69b7ff3ebc990fd40335a8dde58647f9f0a83f',*sys.argv[1:])
