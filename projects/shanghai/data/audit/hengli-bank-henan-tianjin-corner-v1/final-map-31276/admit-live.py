from pathlib import Path
from hashlib import sha256
import sys,time,fcntl,subprocess,json,os
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
 assert sha256(closed_692.read_bytes()).hexdigest()=='1d6633d439910a06a5fc4d85ad2631a1a47fc3309620a621435ca63ee1b191f3'
 assert sha256((entry.parent/'physical.json').read_bytes()).hexdigest()=='b3cfb629a2057101a1e6bb653bfeb0480395377f603e5ead74cdbfd76c66e6b2'
 sig=json.loads(Path('/workspace/shanghai-publisher-preservation/275-master-confirmed.json').read_bytes())
 assert sig['master']=='e5e027832cea75d5549eff67a09aabd91751a735' and sig['model_commit']=='48e87aff1cb42194816487956fc73e1af523858d' and sig['normal_https_verified']==39
 assert sha256(before.read_bytes()).hexdigest()=='045ddea68cb9e8964313c2057f9cd653d173bc16d0d06359348959a3b6d3698e'
 assert '276 2026 ' in Path('/dev/shm/restart-276/full.log').read_text() and Path('/tmp/shanghai-release-stack-276-278/evidence/276-all-http.json').is_file()
 os.environ['CITY276_MATERIALIZED']='/run/lock/h276-material'
 os.environ['CHROMIUM_PATH']='/workspace/shanghai-publisher-preservation/city-275/chromium-340-mesa'
 subprocess.run([sys.executable,'-Bu',entry,'verify',before],check=True)
 for script in ['bind-live.py','prewarm.py','sequence-live.py']:
  subprocess.run([sys.executable,'-Bu',w/script],check=True)
 if not(w/'standalone-closed.json').exists():subprocess.run([sys.executable,'-Bu',w/'standalone-retained.py'],check=True)
 subprocess.run([sys.executable,'-Bu',q/'finish-reviewed-live.py'],check=True,stdout=(q/'unreviewed-inventory.json').open('w'))
