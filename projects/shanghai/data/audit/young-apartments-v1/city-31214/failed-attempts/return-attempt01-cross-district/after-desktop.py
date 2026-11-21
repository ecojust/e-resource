from pathlib import Path
import hashlib,json,subprocess,sys
s=Path('/dev/shm/young214-final/segments')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def r(f):return json.loads(f.read_bytes())
desktop=s/'desktop-closed.json';receipt=r(desktop);assert receipt['exit']==0 and not receipt['remaining_chromium'] and sha(Path(receipt['report']))==receipt['report_sha256']
guest=Path('/dev/shm/joffre330/desktop-window.py')
assert sha(guest)=='db63e70c0716679dee393e9733b6a864348bc51af01d821516e742e2d8b42a18'
outcome=Path('/tmp/joffre-lane330/214-model-closed.json')
if not outcome.is_file():subprocess.run([sys.executable,'-B',guest,desktop],check=False)
hand=r(outcome);assert hand['host_receipt_sha256']==sha(desktop) and not hand['remaining'] and 'exit_code' in hand
# Additional previously deferred independent-page work can run at this authenticated boundary.
late=s.parent/'desktop-fallback-278.py'
if late.is_file():subprocess.run([sys.executable,'-Bu',late,desktop],check=True)
if late.is_file():
 result=Path('/tmp/nankin278/214-desktop-viewer-returned.json')
 if result.is_file():
  previous=r(result);assert previous['source_sha256']==sha(desktop) and previous['host_report_sha256']==receipt['report_sha256'] and previous['passed']
  subprocess.run([sys.executable,'-Bu',s.parent/'after-desktop-279.py','279','viewer'],check=True)

subprocess.run([sys.executable,'-Bu','/tmp/nanchang333/desktop-exit-check.py'],check=True)
gate=Path('/tmp/gaolan335/mapping/finish-camera.py')
assert sha(gate)=='1dabeab499144aaf77c6e7e4babe3dfab4396690b73b4d0e3dbf8004c729ac5b'
subprocess.run([sys.executable,'-Bu',gate,'desktop'],check=False)
