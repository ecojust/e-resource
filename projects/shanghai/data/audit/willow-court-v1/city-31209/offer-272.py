"""Offer a second real window for the salt bank when its signed viewer has reached production."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
from urllib.request import urlopen
import json,os,sys,time
w=Path(__file__).parent;bank=Path('/tmp/saltbank272');site=Path('/workspace/e-resource/projects/shanghai');tag='salt-industry-bank-entrance-v1';receipt=bank/'viewer-closed.json'
def read(f):return json.loads(f.read_bytes())
def sha(f):return sha256(f.read_bytes()).hexdigest()
def save(f,x):
 if f.exists():
  prior=read(f);assert prior['previous_session_sha256']==x['previous_session_sha256'];return
 t=f.with_suffix('.new');t.write_text(json.dumps(x,indent=2)+'\n');t.replace(f)
def done():
 data=read(receipt);assert data['order']==272 and data['passed']and data['exit']==0 and data['remaining_chromium']==[]
 f=Path(data['report']);assert sha(f)==data['sha256'];review=read(f);assert review['passed'] and len(review['downloads'])==4 and len(review['views'])>=4
phase=sys.argv[1];assert phase in ('control','mobile-pin')
f=(w/'isolated-evidence'/phase/'closed.json').resolve();row=read(f);report=Path(row['report']);assert row['order']==209 and row['phase']==phase and row['exit_code']==0 and row['cdp_closed'] and row['observed_chromium_pid_and_starttime'] and not row['remaining_chromium'] and row['remaining']==[] and sha(report)==row['report_sha256'];assert read(report)['completed']
if receipt.is_file():done();sys.exit(0)
files=[bank/'native-closed.json',bank/'raw-272-confirmed.json',Path('/tmp/zhongyi271/native-closed.json'),Path('/tmp/zhongyi271/raw-271-confirmed.json'),Path('/tmp/zhongyi271/viewer-closed.json'),Path('/tmp/shanghai-yongjia-porch/scenes/272-comparison.json')]
out=dict(order=272,host=209,phase=phase,previous_session=str(f),previous_session_sha256=sha(f),previous_browser_report_sha256=sha(report),remaining_chromium=[],created=datetime.now(timezone.utc).isoformat())
missing=[str(p)for p in files if not p.is_file()]
if not missing:
 dep=read(files[1]);assert dep['order']==272 and sha(Path(dep['snapshot']))==dep.get('sha256',dep.get('snapshot_sha256'))
 comp=read(files[-1]);assert comp['port']==31272 and comp['passed']
 page='salt-industry-bank-front.html'
 manifest=site/'assets/models/candidates/huangpu-salt-industry-bank-entrance/manifest.json'
 if not manifest.exists():
  import runpy
  job=runpy.run_path('/tmp/shanghai-jobs.py')['jobs'][272];manifest=site/'assets/models/candidates'/job['id']/'manifest.json'
 page=read(manifest)['viewer_page']
 try:
  with urlopen('http://127.0.0.1:31272/'+page,timeout=10)as response:assert response.status==200 and sha256(response.read()).hexdigest()==sha(site/page)
 except OSError as e:missing.append(str(e))
if missing:
 save(w/f'272-{phase}-viewer-deferred.json',{**out,'authorized':False,'deferred':True,'started':False,'missing':missing});sys.exit(0)
save(w/f'272-{phase}-viewer-window.json',{**out,'authorized':True,'predecessors':{str(p):sha(p)for p in files}})
print('Authorized 272 after',phase,flush=True)
while not receipt.is_file():
 failed=w/f'272-{phase}-viewer-failed.json'
 if failed.is_file():
  d=read(failed);assert d['previous_session_sha256']==sha(f) and d['exit']!=0 and not d['remaining_chromium'];sys.exit(0)
 time.sleep(1.5)
done()
