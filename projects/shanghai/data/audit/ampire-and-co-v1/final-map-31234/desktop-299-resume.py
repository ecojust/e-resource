"""Give the actual 299 follow-up the desktop release before the next map viewport."""
from pathlib import Path
import json,time
from hashlib import file_digest
w=Path(__file__).parent
host=w/'final-map-31234/desktop/process.json'
def digest(f):
 with Path(f).open('rb') as inp:return file_digest(inp,'sha256').hexdigest()
assert (q:=json.loads(host.read_bytes()))['exit_code']==0 and q['node_closed'] and q['remaining_children']==q['remaining_chromium']==[]
assert q['report_sha256']==digest(host.with_name('main-browser.json'))
marker=w/'desktop-followup-cleared.json'
while not marker.exists():time.sleep(.8)
note=json.loads(marker.read_bytes())
assert note['host_sha256']==digest(host) and note['host_report_sha256']==q['report_sha256']
back=Path(note['receipt']);assert digest(back)==note['receipt_sha256']
r=json.loads(back.read_bytes());assert r['all_children_exited'] and r['remaining_children']==[]
