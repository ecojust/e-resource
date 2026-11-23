from pathlib import Path
from hashlib import sha256
import sys,time,fcntl,subprocess,json
q=Path(__file__).parent;w=q/'final-map-31284';before=Path('/tmp/shanghai-main-283/283-map-slot-released.json')
with(q/'gate.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not before.is_file():time.sleep(10)
 p=json.loads(before.read_bytes());assert p['order']==283 and p['passed']and p.get('all_captures_visually_reviewed',p.get('views_reviewed'))and not p['remaining_chromium']and p['exit_code']==0 and p['reports']and p.get('final_closed_at',p.get('finished')) and p['screenshots'] and set(p['actual_saved_downloads'])=={'native','raw','full','lod'}
 for phase,item in p['reports'].items():
  report,closed=Path(item['report']),Path(item['exit'])
  assert sha256(report.read_bytes()).hexdigest()==item['report_sha256'] and sha256(closed.read_bytes()).hexdigest()==item['exit_sha256'],phase
  closed_data=json.loads(closed.read_bytes());assert closed_data.get('exit',closed_data.get('exit_code'))==0 and not closed_data.get('remaining_chromium',closed_data.get('remaining',[])),phase
 for script in ['bind.py','prewarm.py','sequence-recovered.py']:
  subprocess.run([sys.executable,'-Bu',w/script],check=True)
 guest=Path('/tmp/jiangvilla349')
 for key in ('native','viewer'):
  done=guest/(key+'-closed.json')
  if not done.is_file():
   if key=='viewer':
    for required in (guest/'raw-349-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/349-comparison.json'),Path('/tmp/shanghai-yongjia-porch/scenes/349-all-http.json')):
     while not required.is_file():time.sleep(3)
   subprocess.run([sys.executable,'-Bu',q/'offer-349-recovered.py',key,w/('before' if key=='native' else 'phone')/'process.json'],check=True)
  result=json.loads(done.read_bytes());assert result['passed'] and result['exit']==0 and not result['remaining']
 if not(w/'standalone-closed.json').exists():subprocess.run([sys.executable,'-Bu',w/'standalone-retained.py'],check=True)
 subprocess.run([sys.executable,'-Bu',q/'finish-reviewed-retained.py'],check=True,stdout=(q/'unreviewed-inventory.json').open('w'))
