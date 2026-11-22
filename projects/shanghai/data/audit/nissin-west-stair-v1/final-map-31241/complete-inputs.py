"""Bind the complete highest-layer receipt and verify both physical download editions once."""
from pathlib import Path
from hashlib import sha256
import fcntl,sys,json,os,subprocess
w=Path(__file__).parent;r=lambda p:json.loads(p.read_bytes())
with (w/'input-check.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 home=Path('/tmp/shanghai-yongjia-porch');final=home/'scenes/241-all-http.json'
 if not final.is_file():subprocess.run([sys.executable,'-B',home/'release.py','all-http','241'],check=True)
 row=r(final);b=r(w/'bound.json');assert row['passed'] and row['count']==b['stages']['241']['inputs'] and row['production_receipt_sha256']==b['stages']['241']['sha256']
 digest=sha256(final.read_bytes()).hexdigest();old=b['stages']['241']['all_http_sha256'];assert old in (None,digest)
 if old is None:
  assert not any((w/'evidence').glob('*/browser.json'))
  b['stages']['241']['all_http_sha256']=digest;t=w/'bound.next';t.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n');os.replace(t,w/'bound.json')
 for tool,output in [('downloads.py','actual-saved-downloads.json'),('verify-neighbors.py','neighbor-files.json')]:
  if not (w/output).exists():subprocess.run([sys.executable,'-B',w/tool],check=True)
  assert r(w/output)['passed']
 evidence=dict(order=241,passed=True,count=row['count'],bytes=row['total_bytes'],production_receipt_sha256=row['production_receipt_sha256'],all_http_sha256=digest,case_sha256=sha256((w/'bound.json').read_bytes()).hexdigest(),artifacts={x:sha256((w/x).read_bytes()).hexdigest()for x in ('actual-saved-downloads.json','neighbor-files.json','actual-glb-documents.json')});(w/'official-inputs-verified.json').write_text(json.dumps(evidence,indent=1)+'\n')
 print(row['count'],row['total_bytes'],digest)
