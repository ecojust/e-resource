from pathlib import Path
from hashlib import file_digest
import json,sys
p=Path(sys.argv[1]);assert p.samefile('/tmp/shanghai-main-276/276-map-slot-released.json')
def digest(f):
 with Path(f).open('rb')as inp:return file_digest(inp,'sha256').hexdigest()
r=json.loads(p.read_bytes());assert r['order']==276 and r['passed'] and r['exit_code']==0 and r['remaining_chromium']==[] and r['all_captures_visually_reviewed']
assert set(r['actual_saved_downloads'])=={'raw','full','lod','native'}
rows=r['real_browser_process_exits']; reports=r['reports'];assert len(rows)>=6 and 'standalone'in rows
for phase,physical in rows.items():
 report=reports[phase]
 if isinstance(report,str):assert physical['report']==report
 else:assert report['report_sha256']==physical['report_sha256']
 assert physical['exit']==0 and physical['node_pids'] and physical['chromium_pids']
 assert digest(physical['closed'])==physical['sha256'] and digest(physical['report'])==physical['report_sha256']
