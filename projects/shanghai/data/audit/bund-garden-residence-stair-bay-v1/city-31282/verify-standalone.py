"""Verify this release’s original six model views and all four actual saved downloads."""
from pathlib import Path
from hashlib import file_digest
import json
w=Path(__file__).resolve().parent
p=Path('/workspace/e-resource/projects/shanghai')
orig=Path('/tmp/hankou-garden-hotel282')
ident='huangpu-bund-garden-residence-stair-bay'
where=p/'data/audit/bund-garden-residence-stair-bay-v1/standalone-31282'
receipt=orig/'viewer-closed.json';report=where/'viewer.json';viewer=orig/'handoff/check-stair-viewer.cjs'
def read(f):return json.loads(Path(f).read_bytes())
def sha(f):
    with Path(f).open('rb')as stream:return file_digest(stream,'sha256').hexdigest()
s=read(receipt);d=read(report);assert s['order']==282 and s['passed'] and s['exit']==0 and s['all_processes_closed'] and s['remaining_chromium']==s['remaining']==[]
assert s['node']>0 and s['chromium_pids'] and set(s['chromium_pids'])=={int(pid)for pid in s['observed_births']}
assert s['server']==d['base']=='http://127.0.0.1:31282/' and s['views']==6 and s['downloads']==4 and s['receipt_sha256']==sha(report)
assert d['passed'] and d['id']==ident and d['scriptSHA256']==sha(viewer) and not d['pageErrors']
mfile=p/'assets/models/candidates'/ident/'manifest.json';m=read(mfile);assert sha(mfile)==d['manifestSHA256']
assert len(d['views'])==6 and set(d['downloads'])==set(m['assets'])=={'raw','full','lod','native'}
for role,asset in d['downloads'].items():
    spec=m['assets'][role];assert all(spec[k]==asset[k]for k in ['file','bytes','sha256']) and sha(mfile.parent/spec['file'])==spec['sha256']
pics={}
for item in d['views']:
    name=item.get('filename',item.get('file'));file=where/name
    assert file.is_file() and sha(file)==item['sha256'];pics[name]=item['sha256']
manual=read(w/'standalone-visual-review.json');assert manual['personally_reviewed'] and pics==manual['screens'] and sha(report)==manual['source_report_sha256']
link=w/'standalone-31282'
if not link.exists():link.symlink_to(where,target_is_directory=True)
assert link.resolve()==where.resolve()
record={**s,'node_closed':True,'closed_receipt':str(receipt),'closed_receipt_sha256':sha(receipt),'report':str(report),'report_sha256':sha(report),'visual_review_sha256':sha(w/'standalone-visual-review.json')}
(w/'standalone-closed.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
