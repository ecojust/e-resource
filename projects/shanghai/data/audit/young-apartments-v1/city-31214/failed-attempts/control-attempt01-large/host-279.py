from pathlib import Path
from hashlib import sha256
import sys,json,psutil,os,subprocess
w=Path('/tmp/young214');s=Path('/dev/shm/young214-final/segments')
kind=sys.argv[1];phase='control'if kind=='native'else'phone'
section=s/(phase+'-closed.json')
def sha(f):return sha256(f.read_bytes()).hexdigest()
def r(f):return json.loads(f.read_bytes())
c=r(section);report=Path(c['report'])
assert c['exit']==0 and not c['remaining_chromium'] and sha(report)==c['report_sha256'] and r(report)['completed']
try:assert psutil.Process(c['node_pid']).status()==psutil.STATUS_ZOMBIE
except psutil.NoSuchProcess:pass
f=w/(phase+'-closed.json');g=f.with_suffix('.tmp');g.write_text(json.dumps(dict(**c,order=214,passed=True),indent=2)+'\n');os.replace(g,f)
if kind=='native':
 offer=Path('/tmp/moneyguild277/offer-viewer-after214.py')
 assert sha(offer)=='045f10aae6c2d698f22c4502086bd8cbf166f20ac8293d196c4d1dc8d6dfd55f'
 signed277=offer.parent/'viewer-closed.json'
 extra277=next((offer.parent/name for name in ('213-post-distant-viewer-returned.json','213-distant-viewer-returned.json') if (offer.parent/name).is_file()),offer.parent/'213-distant-viewer-returned.json')
 if signed277.exists() and extra277.exists():
  import runpy
  lib=runpy.run_path(str(offer))
  lib['lib']['viewer'](277,signed277)
  prior=r(extra277);assert prior['response_sha256']==sha(signed277) and prior['passed'] and prior['exit']==0
  past=Path(prior['physical_exit'])
  if not past.is_file():
   past=Path('/tmp/shanghai-main-213/evidence/213/separate/distant/closed.json')
  assert past.is_file() and sha(past)==prior['source_sha256'] and sha(Path(prior['host_report']))==prior['host_report_sha256'] and not r(past).get('remaining_chromium',[])
 else:
  subprocess.run([sys.executable,'-B',offer,'control',section],check=True)
  tickets=[offer.parent/('214-control-viewer-'+name+'.json') for name in ('returned','deferred','failed')]
  recorded=[r(x) for x in tickets if x.is_file()]
  assert len(recorded)==1 and recorded[0]['source_sha256']==sha(section) and recorded[0]['host_report_sha256']==sha(report)
 offer278=Path('/dev/shm/nankin278-decoded-preflight/offer-viewer-after214.py')
 assert sha(offer278)=='cb14a0bf7ee2ce6f446472470a7cc461ab0e8fba40a4741390a1c17a05780ee2'
 subprocess.run([sys.executable,'-Bu',offer278,section],check=True)
 tickets278=[Path('/tmp/nankin278')/('214-control-viewer-'+name+'.json') for name in ('returned','deferred','failed')]
 recorded278=[r(x) for x in tickets278 if x.is_file()]
 assert len(recorded278)==1 and recorded278[0]['source_sha256']==sha(section) and recorded278[0]['host_report_sha256']==sha(report)
subprocess.run([sys.executable,'-Bu','/dev/shm/mosque-verified-private-inputs/author-window.py','279',kind],check=True)
if kind=='viewer':
 capture=s.parent/'desktop-before-guest.py'
 assert sha(capture)=='485f562ed7348d12d1583bbced4b25ab0a60586d3983b4a4b520029e91d1365e'
 assert sha(s.parent/'physical-segments.py')=='222b71355356cb447f91422207fa6b83b65bf5def45f4f6371a1937227887ff4'
 subprocess.run([sys.executable,'-Bu',capture],check=True)
 desktop=s/'desktop-closed.json';receipt=r(desktop);assert receipt['exit']==0 and not receipt['remaining_chromium'] and sha(Path(receipt['report']))==receipt['report_sha256']
 guest=Path('/dev/shm/joffre330/desktop-window.py')
 assert sha(guest)=='db63e70c0716679dee393e9733b6a864348bc51af01d821516e742e2d8b42a18'
 outcome=Path('/tmp/joffre-lane330/214-model-closed.json')
 if not outcome.is_file():subprocess.run([sys.executable,'-B',guest,desktop],check=False)
 hand=r(outcome);assert hand['host_receipt_sha256']==sha(desktop) and not hand['remaining'] and 'exit_code' in hand
 # Additional previously deferred independent-page work can run at this authenticated boundary.
 late=s.parent/'desktop-fallback-278.py'
 if late.is_file():subprocess.run([sys.executable,'-Bu',late,desktop],check=True)
