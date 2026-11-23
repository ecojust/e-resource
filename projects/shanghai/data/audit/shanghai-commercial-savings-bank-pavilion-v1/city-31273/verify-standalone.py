"""Recheck the closed live 31273 viewer against the signed six images and four actual saves."""
from pathlib import Path
from hashlib import sha256
import json
w=Path(__file__).parent
source=Path('/tmp/shanghaibank273/viewer-closed.json')
read=lambda p:json.loads(p.read_bytes())
h=lambda p:sha256(p.read_bytes()).hexdigest()
x=read(source); report=Path(x['report']);v=read(report)
assert x['passed'] and x['order']==273 and x['node_closed'] and x['exit']==0 and x['remaining']==x['remaining_chromium']==[]
assert len(x['chromium_pids'])==12 and x['views']==6 and x['downloads']==4 and x['receipt_sha256']==h(report)
assert v['passed'] and not v['pageErrors'] and v['base']==x['server']=='http://127.0.0.1:31273/'
original=read(w/'standalone-originals.json')
for im in v['views']:
 assert h(report.parent/im['filename'])==im['sha256']
assert len(set(im['filename']for im in v['views']))==6
assert v['downloads']==original['downloads'] and set(v['downloads'])=={'raw','full','lod','native'}
review=read(w/'standalone-visual-review.json');assert review['personally_reviewed'] and review['screens']=={im['filename']:im['sha256']for im in v['views']}
if not(w/'standalone-31273').exists():(w/'standalone-31273').symlink_to(report.parent,target_is_directory=True)
out={**x,'closed_receipt':str(source),'closed_receipt_sha256':h(source),'report_sha256':h(report),'reused_exact_origin':True,'visual_review_sha256':h(w/'standalone-visual-review.json')}
(w/'standalone-closed.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
