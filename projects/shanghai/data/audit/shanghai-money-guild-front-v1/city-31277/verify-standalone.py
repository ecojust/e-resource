"""Verify the already closed 31277 six-view session using its independent PID witness."""
from pathlib import Path
from hashlib import sha256
import json
w=Path(__file__).parent;original=Path('/tmp/moneyguild277')
read=lambda p:json.loads(p.read_bytes())
h=lambda f:sha256(f.read_bytes()).hexdigest()
receipt=original/'viewer-closed.json';pids=original/'214-second-attempt-viewer-returned.json';c=read(receipt);z=read(pids);f=Path(c['report']);r=read(f)
assert z['response_sha256']==h(receipt) and r['base']=='http://127.0.0.1:31277/' and c['passed'] and z['passed'] and z['exit']==c['exit']==0 and z['remaining']==c['remaining_chromium']==[]
assert z['report_sha256']==c['sha256']==h(f) and len(r['views'])==6 and r['passed'] and not r['pageErrors']
cp=[int(k)for k,v in z['observed_pids'].items()if v=='chromium'];node=[int(k)for k,v in z['observed_pids'].items()if v=='node'];assert cp and len(node)==1
confirm={i['filename']:h(f.parent/i['filename'])for i in r['views']};assert {i['filename']:i['sha256']for i in r['views']}==confirm
manual=read(w/'standalone-visual-review.json');assert manual['personally_reviewed'] and manual['screens']==confirm
manifest=Path('/workspace/e-resource/projects/shanghai/assets/models/candidates')/r['id']/'manifest.json';m=read(manifest);assert r['manifestSHA256']==h(manifest) and set(r['downloads'])==set(m['assets'])=={'raw','full','lod','native'}
for k,v in m['assets'].items():assert all(r['downloads'][k][prop]==v[prop]for prop in ('file','sha256','bytes')) and h(manifest.parent/v['file'])==v['sha256']
if not(w/'standalone-31277').exists():(w/'standalone-31277').symlink_to(f.parent,target_is_directory=True)
record={**c,'views':6,'downloads':4,'receipt_sha256':h(f),'report_sha256':h(f),'node_closed':True,'node':node[0],'chromium_pids':cp,'observed_source':str(pids),'physical_witness_sha256':h(pids),'closed_receipt':str(receipt),'closed_receipt_sha256':h(receipt),'visual_review_sha256':h(w/'standalone-visual-review.json'),'remaining':[],'reused_exact_origin':True}
(w/'standalone-closed.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
