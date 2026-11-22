"""Bind the signed 323 dispatch only when its approved author SHA and executable have been supplied."""
from pathlib import Path
from hashlib import sha256
import argparse,json,os
W=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('dispatch',type=Path);ap.add_argument('dispatch_sha256');ap.add_argument('author_review',type=Path);ap.add_argument('author_sha256');args=ap.parse_args()
def h(f):return sha256(f.read_bytes()).hexdigest()
p=args.dispatch.resolve(strict=True);assert p.name=='dispatch-contract.json';G=p.parent;ex=G/'admit-window.py';assert h(p)==args.dispatch_sha256 and h(args.author_review)==args.author_sha256 and ex.is_file()
d=json.loads(p.read_bytes());assert d['order']==323;assert d['host']==258 and d['source_review_sha256']==h(args.author_review) and d['admission_sha256']==h(ex)
doc=dict(order=323,host=258,author=str(args.author_review.resolve()),author_sha256=h(args.author_review),admit=str(ex),admit_sha256=h(ex),dispatch=str(p),dispatch_sha256=h(p))
target=W/'guest-323.json';data=(json.dumps(doc,indent=2)+'\n').encode()
if target.is_file():assert target.read_bytes()==data
else:
 tmp=target.with_suffix('.new');tmp.write_bytes(data);tmp.replace(target)
print(h(target))
