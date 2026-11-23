from pathlib import Path
from hashlib import sha256
import sys,time,fcntl,subprocess,json
q=Path(__file__).parent;w=q/'final-map-31276';before=Path('/tmp/shanghai-main-275/275-map-slot-released.json')
with(q/'gate.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not before.is_file():time.sleep(10)
 p=json.loads(before.read_bytes());assert p['order']==275 and p['passed']and p.get('all_captures_visually_reviewed',p.get('views_reviewed'))and not p['remaining_chromium']and p['exit_code']==0 and p['reports']and p.get('final_closed_at',p.get('finished')) and p['screenshots'] and set(p['actual_saved_downloads'])=={'native','raw','full','lod'}
 for phase,item in p['reports'].items():
  report,closed=Path(item['report']),Path(item['exit'])
  assert sha256(report.read_bytes()).hexdigest()==item['report_sha256'] and sha256(closed.read_bytes()).hexdigest()==item['exit_sha256'],phase
  assert json.loads(closed.read_bytes())==p['real_browser_process_exits'][phase]
 closed_692=Path('/workspace/.e-resource-recovery/root/changning-692-study/development-native/early-development-returned.json')
 while not closed_692.is_file():time.sleep(3)
 entry=Path('/workspace/.e-resource-recovery/root/changning-692-study/development-native/complete-275.py')
 assert sha256(entry.read_bytes()).hexdigest()=='6fc159d1d4c2ff4def11cec6d156b322aeab02ebde8863899769c6957c2feeed'
 subprocess.run([sys.executable,'-Bu',entry,'verify',before],check=True)
 for script in ['bind.py','prewarm.py','sequence.py']:
  subprocess.run([sys.executable,'-Bu',w/script],check=True)
 if not(w/'standalone-closed.json').exists():subprocess.run([sys.executable,'-Bu',w/'standalone-retained.py'],check=True)
 subprocess.run([sys.executable,'-Bu',q/'finish-reviewed-retained.py'],check=True,stdout=(q/'unreviewed-inventory.json').open('w'))
