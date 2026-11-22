"""Seal the 251 city handoff after all streetscape photographs are reviewed."""
from pathlib import Path
from hashlib import sha256
import json, os
w=Path(__file__).parent;run=w/'final-map-31251'
def read(p):return json.loads(p.read_bytes())
def digest(f):
 with f.open('rb')as r:return __import__('hashlib').file_digest(r,'sha256').hexdigest()
technical=read(run/'verified-for-visual-review.json');results_path=Path(technical['report']);official=results_path.parent
results=read(results_path);judge=run/'manual-visual-review.json';review=read(judge)
assert technical['order']==251 and results['passed']and results['previous_city_count']==285 and results['city_count']==286
assert len(results['screenshots'])==12 and set(results['screenshots'])==set(review['screenshots'])
shots={};receipts={}
for filename in results['screenshots']:
 sig=digest(official/filename);q=review['screenshots'][filename];assert sig==q['sha256'] and q['observation'].strip()
 shots[filename]=sig
for phase,summary in technical['real_browser_process_exits'].items():
 out=official/phase;report=out/('control-browser.json' if phase=='before' else 'main-browser.json');exit_file=out/'process.json'
 proc=read(exit_file);c=read(report)
 assert c['completed']and not c['errors']and not c['failed']and proc==summary
 assert proc['exit_code']==0 and proc['node_closed'] and proc['node_pids']and proc['chromium_pids']and not proc['remaining_chromium']and not proc['remaining_children']
 assert proc['report_sha256']==digest(report)
 receipts[phase]=dict(report=str(report),report_sha256=digest(report),exit=str(exit_file),exit_sha256=digest(exit_file))
assert set(receipts)=={'before','phone','desktop','architecture','distant','mouse','touch'}
assert len(results['ground'])==76 and all(g['found']==g['expected']for g in results['ground'])
audit=official.parent;viewer=read(audit/'viewer.json');replay=read(run/'standalone-replay.json');assert viewer['passed']and len(viewer['views'])==4 and len(viewer['downloads'])==4
assert digest(audit/'viewer.json')==replay['report_sha256'] and viewer['downloads']==replay['actual_saved']
assets=audit.parents[2]/'assets/models/candidates'/results['id'];m=read(assets/'manifest.json')
saved={}
for role,record in viewer['downloads'].items():
 physical=assets/m['assets'][role]['file'];sig=digest(physical)
 assert record['sha256']==sig and record['bytes']==physical.stat().st_size
 saved[role]=dict(file=m['assets'][role]['file'],bytes=record['bytes'],sha256=sig)
for frame in viewer['views']:assert digest(audit/frame['filename'])==frame['sha256']
fields=dict(order=251,passed=True,exit=0,exit_code=0,remaining=[],remaining_chromium=[],views_reviewed=True,after_real_screenshot_review=True,all_captures_visually_reviewed=True,finished=technical['closed_time'],closed_time=technical['closed_time'],reports=receipts,receipts=receipts,real_browser_process_exits=technical['real_browser_process_exits'],screenshots=shots,actual_saved_downloads=saved,standalone_replay={'report':str(audit/'viewer.json'),'report_sha256':digest(audit/'viewer.json'),'evidence':str(run/'standalone-replay.json'),'sha256':digest(run/'standalone-replay.json')},manual_sha256=digest(judge),actual_report_sha256=digest(results_path))
current=official/'current-standalone'
closure=read(current/'closed.json');report=read(current/'viewer.json')
assert report['passed'] and closure['passed'] and closure['exit_code']==0 and not closure['remaining'] and closure['chromium']
assert closure['report_sha256']==digest(current/'viewer.json') and closure['driver_sha256']==digest(current/'formal-viewer.cjs')
assert report['base']=='http://127.0.0.1:31251/' and set(saved)==set(report['downloads'])
assert len(report['views'])==4 and set(review['current_standalone'])=={r['filename'] for r in report['views']}
for frame in report['views']:
 rec=review['current_standalone'][frame['filename']]
 assert rec['observation'].strip() and rec['sha256']==frame['sha256']==digest(current/frame['filename'])
 shots['current-standalone/'+frame['filename']]=frame['sha256']
for role,item in report['downloads'].items():
 actual=Path(closure['report']).parent/'saved'/item['file'];assert item['saveAsVerified'] and digest(actual)==item['sha256'] and actual.stat().st_size==item['bytes']
 assert saved[role]=={k:item[k] for k in ('file','sha256','bytes')}
fields.update(actual_saved_downloads=report['downloads'],current_standalone={'report':str(current/'viewer.json'),'report_sha256':digest(current/'viewer.json'),'closed':str(current/'closed.json'),'closed_sha256':digest(current/'closed.json')},closed_time=closure['finished'],finished=closure['finished'])
extension=official/'entrance-reframe'
supp=read(extension/'closed.json')
assert supp['exit_code']==0 and supp['remaining']==[] and supp['node_closed'] and supp['cdp_closed']
assert supp['report_sha256']==digest(extension/'main-browser.json') and supp['source_code_sha256']==digest(extension/'east-entrance.cjs')
assert supp['predecessor']['sha256']==digest(official/'guest-returns/596-independent-returned.json')
fields.update(entrance_reframe={'closed_sha256':digest(extension/'closed.json'),'screenshots':{f.name:digest(f) for f in extension.glob('*.png')},'review_sha256':digest(extension/'independent-observations.json')},finished=supp['finished'],closed_time=supp['finished'],guest_returns={f.name:digest(f) for f in (official/'guest-returns').glob('*.json')})
assert len(fields['entrance_reframe']['screenshots'])==4
text=json.dumps(fields,ensure_ascii=False,indent=2)+'\n';name=w/'251-map-slot-released.json'
if name.exists():assert name.read_text()==text
else:
 tmp=name.with_suffix('.working');tmp.write_text(text);os.replace(tmp,name)
print(name,digest(name))
