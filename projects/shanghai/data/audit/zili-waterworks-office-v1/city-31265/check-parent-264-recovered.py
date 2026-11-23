from pathlib import Path
from hashlib import file_digest
import json,sys
p=Path(sys.argv[1]);assert p.samefile(Path('/tmp/shanghai-main-264/264-map-slot-released.json'))
r=json.loads(p.read_bytes())
assert r['order']==264 and r['passed'] and r['exit_code']==0 and r['remaining_chromium']==[]
assert r['all_captures_visually_reviewed'] and r['after_real_screenshot_review'] and r['views_reviewed']
assert r['ports']==[31263,31264] and r['count']==[298,299] and r['screenshots']>=18
assert set(r['actual_saved_downloads'])=={'raw','full','lod','native'}
phases=r['real_browser_process_exits']
assert {'before','phone','desktop','standalone'}<=set(phases) or ('standalone'in phases and len(phases)>=6)
def sha(f):
 with Path(f).open('rb')as inp:return file_digest(inp,'sha256').hexdigest()
for name,row in phases.items():
 assert row['exit']==0 and row['node_pids'] and row['chromium_pids']
 assert sha(row['closed'])==row['sha256'] and sha(row['report'])==row['report_sha256']
 assert r['reports'][name]==row['report']
print('264 physical receipts verified',len(phases))

early=Path('/dev/shm/root-tanggu648/development-native/early-development-returned.json')
cl= json.loads(early.read_bytes())
assert cl['order']==648 and cl['host']==264 and cl['passed'] and cl['exit_code']==0 and cl['all_children_exited'] and not cl['remaining_children']
assert sha(cl['physical'])==cl['physical_sha256'] and sha('/tmp/shengshi441/development-native/264-development-returned.json')==cl['prior_in_this_window_sha256']
assert sha('/tmp/shanghai-main-264/final-map-31264/standalone-closed.json')==cl['host_sha256']
print('648 and 441 returned',sha(early))
