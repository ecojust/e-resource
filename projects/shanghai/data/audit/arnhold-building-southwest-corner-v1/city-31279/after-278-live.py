"""Consume the real predecessor's phase receipts before the two Central Trust natural guest windows."""
from pathlib import Path
import fcntl,hashlib,json,subprocess,sys
w=Path(__file__).parent;parent=Path('/tmp/shanghai-main-278/278-map-slot-released.json')
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def run(program,*args):subprocess.run([sys.executable,'-Bu',w/program,*args],check=True)
with (w/'admission.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 s=read(parent)
 assert s['order']==278 and s['passed'] and s['exit_code']==0 and not s['remaining_chromium'] and s['views_reviewed'] and s['all_captures_visually_reviewed']
 assert s['reports']==s['receipts'] and len(s['actual_saved_downloads'])==4 and s['finished']
 assert {'before','phone','desktop','distant'}<=set(s['reports'])
 for phase,v in s['reports'].items():
  assert h(v['report'])==v['report_sha256'] and h(v['exit'])==v['exit_sha256']
  q=read(v['exit']);assert q.get('exit',q.get('exit_code',q.get('code')))==0 and not q.get('remaining',q.get('remaining_chromium'))
  assert q.get('node_closed',True) and q.get('chromium_pids',q.get('chromium',q.get('browsers')))
  r=read(v['report']);assert r.get('completed',r.get('passed')) and not r.get('errors',[]) and not r.get('failed',[])
 supervisor=read(w/'supervisor.json');assert all(h(Path(n))==v for n,v in supervisor['geometry_inputs'].items());subprocess.run([sys.executable,'-Bu','/workspace/shanghai-publisher-preservation/city-279/attest-sites.py'],check=True);run('run-279-live.py',parent);run('merge-279-live.py')
 if not (w/'viewer-31279/closed.json').exists():run('viewer-live.py','--assigned-standalone-slot')
 run('bind-full-http.py');run('archive-live.py','279');(w/'catalog-store').resolve().mkdir(exist_ok=True,parents=True);run('local-catalogs.py','store')
 print('279 real screenshots are ready for review.',flush=True)
