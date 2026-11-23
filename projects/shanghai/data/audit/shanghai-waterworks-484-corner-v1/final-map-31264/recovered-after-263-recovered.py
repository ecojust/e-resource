from pathlib import Path
from hashlib import sha256
import sys,time,fcntl,subprocess,json
q=Path(__file__).parent;w=q/'final-map-31264';before=Path('/tmp/shanghai-main-263/263-map-slot-released.json')
with(q/'gate.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not before.is_file():time.sleep(10)
 p=json.loads(before.read_bytes());assert p['order']==263 and p['passed']and p['views_reviewed']and not p['remaining_chromium']and p['exit_code']==0 and p['reports']and p['final_closed_at'] and p['screenshots'] and set(p['actual_saved_downloads'])=={'native','raw','full','lod'}
 previous=before.parent/'viewer-31263'/'closed.json'
 preceding=Path('/workspace/.e-resource-recovery/root/jingan-644-study/development-native/early-development-returned.json')
 returned=json.loads(preceding.read_bytes());ordinary=json.loads(previous.read_bytes())
 assert (returned['order'],returned['host'],returned['passed'],returned['exit_code'],returned['all_children_exited'],returned['remaining_children'])==(644,263,True,0,True,[])
 assert returned['host_sha256']==sha256(previous.read_bytes()).hexdigest()
 actual=previous.with_name('viewer.json')
 assert returned['host_report_sha256']==sha256(actual.read_bytes()).hexdigest()
 assert returned['physical_sha256']==sha256(Path(returned['physical']).read_bytes()).hexdigest()
 for script in ['bind-recovered.py','prewarm.py','sequence-recovered.py']:
  subprocess.run([sys.executable,'-Bu',w/script],check=True)
 if not(w/'standalone-closed.json').exists():subprocess.run([sys.executable,'-Bu',w/'standalone-recovered.py'],check=True)
 entry=Path('/tmp/shengshi441/development-native/after-264.py');assert sha256(entry.read_bytes()).hexdigest()=='99b24f703345045dc6dbb9d8eca98824b1028becf74752348b75745d6d639067'
 subprocess.run([sys.executable,'-Bu',entry,w/'standalone-closed.json',w/'all-real-processes-closed.json'],check=True)
 side=json.loads((entry.parent/'264-development-returned.json').read_bytes());assert side['passed'] and side['exit_code']==0 and not side['remaining_children'] and side['all_children_exited']
 crown=Path('/workspace/.e-resource-recovery/root/hongkou-648-study/development-native/link-264.py')
 assert sha256(crown.read_bytes()).hexdigest()=='e4982f234a289ccce72217cab40dae6fbec986f7c3575c2c40423ff1988b2e1b'
 subprocess.run([sys.executable,'-Bu',crown,w/'standalone-closed.json',entry.parent/'264-development-returned.json'],check=True)
 development=json.loads(crown.with_name('early-development-returned.json').read_bytes())
 assert development['passed'] and development['exit_code']==0 and development['all_children_exited'] and not development['remaining_children']
 subprocess.run([sys.executable,'-Bu',q/'finish-reviewed-recovered.py'],check=True,stdout=(q/'unreviewed-inventory.json').open('w'))
