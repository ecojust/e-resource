"""Wait for the two existing 233 jobs to clear before the first 234 viewport."""
from pathlib import Path
from hashlib import file_digest
import json,time
base=Path('/tmp/shanghai-main-233/formal-31233')
host=base/'isolated-evidence/independent/closed.json'
report=host.parent/'viewer.json'
def digest(p):
    with Path(p).open('rb') as f:return file_digest(f,'sha256').hexdigest()
for n in (408,400):
    handback=base/f'{n}-development-handback.json'
    while not handback.is_file():time.sleep(1)
    hand=json.loads(handback.read_bytes())
    assert hand['host_sha256']==digest(host)
    if hand.get('deferred'):
        assert n==400 and hand['deferred'] and not hand['started'] and hand['remaining_children']==[] and hand['previous_sha256']==prior
        continue
    actual=Path(hand['ticket'])
    assert digest(actual)==hand['ticket_sha256']
    job=json.loads(actual.read_bytes())
    assert job['order']==n and job['host']==233 and job['host_sha256']==digest(host) and job['host_report_sha256']==digest(report)
    assert job['all_children_exited'] and job['remaining_children']==[]
    if job.get('physical'):assert digest(job['physical'])==job['physical_sha256']
    if n==408:prior=digest(actual)
    else:assert hand['previous_sha256']==job['previous_sha256']==prior
