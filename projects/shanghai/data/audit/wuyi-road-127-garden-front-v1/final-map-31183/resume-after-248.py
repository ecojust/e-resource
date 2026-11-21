"""Start the closed predecessor/new-city browser check only after the 248 native handoff."""
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
import fcntl,json,os,subprocess,time
w=Path(__file__).parent
load=lambda f:json.loads(f.read_bytes());h=lambda f:sha256(f.read_bytes()).hexdigest()
with (w/'current-run.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 native=Path('/tmp/yeetsoong248/native-slot-released.json')
 while not native.is_file():time.sleep(1)
 n=load(native)
 assert n['passed'] and n['order']==248 and n['exit']==0 and not n['remaining'] and n['wrapper_closed']
 assert n['prior_exit_sha256']==h(Path('/tmp/ram247/native-slot-released.json'))
 assert h(Path('/workspace/e-resource/projects/shanghai/data/audit/yee-tsoong-tobacco-front-v1/geometry-native.json'))==n['geometry_receipt_sha256']
 prior=load(w/'first-before-neighborhood-failure/before/before.json');assert prior['browser_closed']and not prior['passed']
 pin=load(w/'31k-live-inputs.json')
 for key,filename in [('runner_sha256','check-historical-map.cjs'),('sequence_sha256','sequence.sh'),('bound_input_sha256','bound-inputs.json'),('neighborhood_sha256','public-neighborhood.json')]:assert pin[key]==h(w/filename)
 (w/'resume-after-248.json').write_text(json.dumps(dict(order=183,admitted=datetime.now(timezone.utc).isoformat(),native_248_receipt=h(native),neighborhood=pin['neighborhood_sha256'],driver=pin['runner_sha256']),indent=2)+'\n')
 with (w/'sequence-run.log').open('ab')as out:
  p=subprocess.run(['bash',w/'sequence.sh'],stdout=out,stderr=out)
 (w/'resumed-sequence.exit').write_text(str(p.returncode)+'\n')
 raise SystemExit(p.returncode)
