"""Offer a second ordinary 31282 viewing interval after the real 217 handoff."""
from datetime import datetime,timezone
from pathlib import Path
from hashlib import file_digest
from urllib.request import urlopen
import json,subprocess,sys,time

root=Path(__file__).resolve().parent
prior=Path('/tmp/shanghai-main-217/217-map-slot-released.json')
control=Path('/tmp/shanghai-main-217/final-map-31217/distant/process.json')
author=Path('/tmp/hankou-garden-hotel282')
last=Path('/tmp/palace219-281/viewer-closed.json')
comparison=Path('/tmp/shanghai-yongjia-porch/scenes/282-comparison.json')
def read(p):return json.loads(p.read_bytes())
def sha(p):
    with p.open('rb')as s:return file_digest(s,'sha256').hexdigest()
def receipt(path,data):
    tmp=path.with_suffix('.new');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)
def finished(r):return r.get('exit',r.get('exit_code'))==0 and not r.get('remaining',[]) and not r.get('remaining_chromium',[])
def check_viewer():
    r=read(author/'viewer-closed.json')
    assert r['passed'] and r['order']==282 and r['views']==6 and r['downloads']==4 and finished(r)
    report=Path('/workspace/e-resource/projects/shanghai/data/audit/bund-garden-residence-stair-bay-v1/standalone-31282/viewer.json')
    assert sha(report)==r['receipt_sha256'] and r['chromium_pids']
assert read(prior).get('order',read(prior).get('stage'))==217 and finished(read(prior))
r=read(control)
assert r['phase']=='distant' and r['node_closed'] and r['chromium_pids'] and not r['remaining_children'] and finished(r)
report=control.with_name('main-browser.json');assert read(report)['completed'] and sha(report)==r['report_sha256']
base=dict(order=282,host=218,phase='before opening 218 ordinary map',previous_session=str(control),previous_session_sha256=sha(control),previous_browser_report_sha256=sha(report),previous_publication_sha256=sha(prior))
if (author/'viewer-closed.json').is_file():
    check_viewer();receipt(root/'282-followup-offer.json',dict(base,already_complete=True,return_sha256=sha(author/'viewer-closed.json')));sys.exit()
needed=[last,author/'native-closed.json',author/'raw-282-confirmed.json',comparison]
missing=[str(p)for p in needed if not p.is_file()]
if missing:
    receipt(root/'282-followup-deferred.json',dict(base,deferred=True,started=False,missing=missing));sys.exit()
assert finished(read(last)) and read(last)['passed']
raw=read(needed[2]);assert raw['count']==317 and raw['sha256']==sha(Path(raw['snapshot']))
assert read(comparison)['passed'] and read(needed[1])['passed'] and finished(read(needed[1]))
with urlopen('http://127.0.0.1:31282/bund-garden-residence-stair-bay.html',timeout=20) as res:
    assert res.status==200 and b'bund-garden-residence-stair-bay' in res.read()
subprocess.run([sys.executable,'-B',author/'handoff/admit-window.py','viewer',control],check=True)
window=author/'handoff/viewer-window.json';assert read(window)['sha256']==sha(control)
receipt(root/'282-followup-offer.json',dict(base,authorized=True,admission_sha256=sha(window)))
while not (author/'viewer-closed.json').is_file():time.sleep(.5)
check_viewer();receipt(root/'282-followup-returned.json',dict(base,passed=True,return_sha256=sha(author/'viewer-closed.json')))
