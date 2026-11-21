from pathlib import Path
from hashlib import sha256
from urllib.request import urlopen
from datetime import datetime,timezone
import json,sys
project=Path('/workspace/e-resource/projects/shanghai')
cases={217:('huaihai-road-1634-residence-v1','/tmp/shanghai-main-217/final-map-31217')}
for order,(tag,loc) in cases.items():
 work=Path(loc);audit=project/'data/audit'/tag
 case=json.loads((audit/'map-case.json').read_bytes());identity=case['id']
 src=json.loads((project/'source/precise'/identity/'footprint-review.json').read_bytes())
 mf=Path('assets/models/candidates')/identity/'manifest.json'; assets=json.loads((project/mf).read_bytes())['assets']
 fixed={r['repository_path'].removeprefix('projects/shanghai/'):r['sha256']for r in src['frozen_bindings'] if r['repository_path'].startswith('projects/shanghai/assets/city-detail/')}
 record={}
 for n in (order-1,order):
  base=f'http://127.0.0.1:{31000+n}/';wanted=dict(fixed)
  if n==order:
   wanted[mf.as_posix()]=sha256((project/mf).read_bytes()).hexdigest()
   wanted.update({str(mf.parent/r['file']):r['sha256']for r in assets.values()})
  rows=[]
  for f,sig in wanted.items():
   url=base+f;h=sha256();size=0
   with urlopen(url,timeout=90) as resp:
    code=resp.status
    while b:=resp.read(128*1024):h.update(b);size+=len(b)
   rows.append(dict(file=f,url=url,status=code,bytes=size,sha256=h.hexdigest()));assert code==200 and h.hexdigest()==sig,(n,f)
  record[str(n)]=rows
 report={'order':order,'created':datetime.now(timezone.utc).isoformat(),'origins':record,'actual_bytes':sum(row['bytes']for rows in record.values()for row in rows)}
 (work/'prewarm-bound-files.json').write_text(json.dumps(report,indent=2)+'\n')
 print(order,[(n,len(rows)) for n,rows in record.items()],report['actual_bytes'],flush=True)
