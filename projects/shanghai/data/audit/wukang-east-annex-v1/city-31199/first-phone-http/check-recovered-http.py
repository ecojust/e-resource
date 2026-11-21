from pathlib import Path
import json,hashlib,subprocess,urllib.request as u,urllib.parse as a
from datetime import datetime,timezone
w=Path(__file__).parent;repo=Path('/workspace/e-resource')
rev='ae55637ce1d7cbc4d21fd94934c8309aca1dcd09'
cases=json.loads((w/'phone-first-live-http.json').read_bytes())
rows=[]
for rec in cases['requested']:
 if rec['code']<400:continue
 path=a.urlparse(rec['url']).path.strip('/')
 blob=subprocess.check_output(['git','--no-lazy-fetch','rev-parse',rev+':projects/shanghai/'+path],cwd=repo,text=True).strip()
 cache=Path('/tmp/shanghai-release-stack-181-200/cache/17199/server-cache')/rev/'objects'/path
 for port in [17199,31199]:
  with u.urlopen(f'http://127.0.0.1:{port}/{path}',timeout=30) as r:
   assert r.status==200 and (n:=int(r.headers['Content-Length']))==cache.stat().st_size
   a1=hashlib.sha1(b'blob '+str(n).encode()+b'\0');a2=hashlib.sha256()
   while b:=r.read(131072):a1.update(b);a2.update(b)
  with cache.open('rb') as f: local=hashlib.file_digest(f,'sha256').hexdigest()
  assert (blob,local)==(a1.hexdigest(),a2.hexdigest())
  rows.append(dict(port=port,path=path,code=200,bytes=n,git_blob=blob,sha256=local,cache_links=cache.stat().st_nlink))
out=dict(passed=True,finished=datetime.now(timezone.utc).isoformat(),original_status=502,rows=rows)
(w/'phone-first-http-recovered.json').write_text(json.dumps(out,indent=2)+'\n')
print([(r['port'],r['path'],r['bytes'])for r in rows])
