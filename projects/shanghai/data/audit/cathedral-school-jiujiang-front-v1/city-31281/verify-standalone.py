"""Check the already completed 31281 school page, process IDs, saved assets, and personally reviewed screenshots."""
from pathlib import Path
from hashlib import sha256
import json
w=Path(__file__).resolve().parent
project=Path('/workspace/e-resource/projects/shanghai')
author=Path('/tmp/palace219-281');receipt=author/'viewer-closed.json';physical=author/'mapping/handoff/node-chromium-physical.json'
def sig(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
closed=read(receipt);pid=read(physical);assert closed['order']==281 and closed['passed'] and closed['exit']==0 and closed['remaining']==closed['remaining_chromium']==[]
assert closed['process_receipt_sha256']==sig(physical) and pid['node_closed'] and not pid['remaining'] and pid['exit']==closed['exit']
assert closed['node']==pid['node'] and set(closed['chromium_pids'])==set(map(int,pid['chromium_pids_and_birth']))
report=Path(closed['report']);d=read(report);assert d['base']==closed['server']=='http://127.0.0.1:31281/' and sig(report)==closed['report_sha256']
assert d['passed'] and not d['pageErrors'] and d['scriptSHA256']==sig(author/'mapping/handoff/six-view-download.cjs')
rv=read(w/'standalone-visual-review.json');assert rv['personally_reviewed'] and len(d['views'])==6 and rv['screens']=={shot['filename']:sig(report.parent/shot['filename'])for shot in d['views']}
assert rv['screens']=={shot['filename']:shot['sha256'] for shot in d['views']}
manifest=project/'assets/models/candidates'/d['id']/'manifest.json';m=read(manifest)
assert sig(manifest)==d['manifestSHA256'] and set(m['assets'])==set(d['downloads'])=={'raw','full','lod','native'}
for k,v in m['assets'].items():
 dl=d['downloads'][k];assert dl['actualSaved'] and sig(manifest.parent/v['file'])==v['sha256']==dl['sha256'] and dl['bytes']==v['bytes'] and dl['file']==v['file']
q=w/'standalone-31281'
if not q.exists():q.symlink_to(report.parent,target_is_directory=True)
out={**closed,'node_closed':True,'actual_closed_sha256':sig(receipt),'camera_screens_sha256':sig(w/'standalone-visual-review.json'),'physical_receipt':str(physical),'physical_receipt_sha256':sig(physical)}
(w/'standalone-closed.json').write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n')
