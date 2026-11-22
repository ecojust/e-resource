"""Take one separate Chromium photograph of the already selected mouse destination."""
from pathlib import Path
import fcntl,hashlib,json,subprocess,sys
w=Path(__file__).resolve().parent;root=w/'desktop-pin-visual-supplement';root.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with (root/'guard').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 selected=root/'selected.json'
 if selected.exists():
  from importlib.machinery import SourceFileLoader
  SourceFileLoader('supplement',str(w/'confirm-destination-picture.py')).load_module().read();sys.exit(0)
 prior=w/'isolated-evidence/desktop-pin/closed.json';r=json.loads(prior.read_bytes());assert r['cdp_closed'] and r['exit_code']==0 and not r['remaining_chromium']
 name='capture-'+str(sum(x.is_dir() for x in root.iterdir())+1)
 code=subprocess.run([sys.executable,'-Bu',w/'capture-mouse-destination.py',name]).returncode
 if code:sys.exit(code)
 closed=root/name/'closed.json';report=root/name/'main-browser.json'
 selected.write_text(json.dumps(dict(order=233,session=name,original_visual_close_sha256=sha(prior),close_sha256=sha(closed),report_sha256=sha(report),driver_sha256=sha(w/'check-mouse-destination-pixels.cjs'),method='Additional physical photograph of the mouse destination following the earlier loading image.'),indent=2)+'\n')
