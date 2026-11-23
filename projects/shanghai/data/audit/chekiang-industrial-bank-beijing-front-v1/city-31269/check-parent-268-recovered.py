from pathlib import Path
from hashlib import file_digest
import json,sys
p=Path(sys.argv[1]);assert p.samefile(Path('/tmp/shanghai-main-268/268-map-slot-released.json'))
r=json.loads(p.read_bytes())
assert r['order']==268 and r['passed'] and r['exit_code']==0 and r['remaining_chromium']==[]
assert r['all_captures_visually_reviewed'] and r['after_real_screenshot_review'] and r['views_reviewed']
assert r['ports']==[31267,31268] and r['count']==[302,303] and r['screenshots']>=18
assert set(r['actual_saved_downloads'])=={'raw','full','lod','native'}
phases=r['real_browser_process_exits']
assert {'before','phone','desktop','standalone'}<=set(phases) or ('standalone'in phases and len(phases)>=6)
def sha(f):
 with Path(f).open('rb')as inp:return file_digest(inp,'sha256').hexdigest()
for name,row in phases.items():
 assert row['exit']==0 and row['node_pids'] and row['chromium_pids']
 assert sha(row['closed'])==row['sha256'] and sha(row['report'])==row['report_sha256']
 assert r['reports'][name]==row['report']
print('268 physical receipts verified',len(phases))
import subprocess,time
development=Path('/workspace/.e-resource-recovery/root/hongkou-664-study/development-native/complete-268.py')
assert sha(development)=='c9f13ea68c638cd33ee10ea6d9eaf021a3862c44ea4bfcbbc2b9757e9623cec1'
primary=development.parent/'early-development-returned.json'
companion=development.parent.parent/'browser/development-native/early-companion-returned.json'
while not(primary.is_file() and companion.is_file()):time.sleep(4)
subprocess.run([sys.executable,'-Bu',development,'verify',p],check=True)
