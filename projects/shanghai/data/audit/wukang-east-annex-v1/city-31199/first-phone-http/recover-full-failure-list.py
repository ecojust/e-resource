from pathlib import Path
import os,json,hashlib,subprocess
from urllib.parse import urlsplit
from urllib.request import urlopen
w=Path(__file__).parent
base=Path('/tmp/shanghai-release-stack-181-200/cache/17199/server-cache')
target=next(base.glob('*/objects'));rev=target.parent.name
records=json.loads((w/'evidence/199/failed-first-phone-http/main-browser.json').read_bytes())['failed']
roots=[]
for d in Path('/tmp').glob('shanghai-*'):
 for fmt in ('cache/*/server-cache','server-cache','http/server-cache','http-*/server-cache'):
  roots.extend(d.glob(fmt+'/'+rev+'/objects'))
def hashes(p):
 size=p.stat().st_size;g=hashlib.sha1(b'blob '+str(size).encode()+b'\0');h=hashlib.sha256()
 with p.open('rb')as f:
  while b:=f.read(131072):g.update(b);h.update(b)
 return g.hexdigest(),h.hexdigest()
results=[]
for row in records:
 assert row['status']==502
 path=urlsplit(row['url']).path.lstrip('/');dst=target/path
 blob=subprocess.check_output(['git','--no-lazy-fetch','rev-parse',rev+':projects/shanghai/'+path],cwd='/workspace/e-resource',text=True).strip()
 linked=False
 if not dst.is_file():
  for folder in roots:
   src=folder/path
   if not src.is_file() or src.resolve().stat().st_dev!=target.stat().st_dev:continue
   actual,dig=hashes(src)
   if actual!=blob:continue
   dst.parent.mkdir(exist_ok=True,parents=True)
   try:os.link(src.resolve(),dst);linked=True
   except FileExistsError:pass
   rec=dst.with_name(dst.name+'.receipt.json')
   record=dict(path=path,baseline_commit=rev,git_blob=blob,actual_git_blob=blob,sha256=dig,bytes=src.stat().st_size,origin='verified-existing-cache-hardlink',source=str(src))
   if not rec.is_file():
    try:
     with rec.open('x')as f:json.dump(record,f);f.write('\n')
    except FileExistsError:pass
   break
 assert dst.is_file(),path
 actual,dig=hashes(dst);assert actual==blob
 for port in [17199,31199]:
  with urlopen(row['url'].replace(':31199/',f':{port}/'),timeout=20)as response:
   assert response.status==200 and int(response.headers['Content-Length'])==dst.stat().st_size
   h=hashlib.sha256()
   while b:=response.read(131072):h.update(b)
  assert h.hexdigest()==dig
 results.append(dict(path=path,git_blob=blob,sha256=dig,bytes=dst.stat().st_size,preseeded=linked,source_nlink=dst.stat().st_nlink,passed_get_ports=[17199,31199]))
 print(len(results),path,dst.stat().st_size,flush=True)
(w/'all-first-phone-failures-recovered.json').write_text(json.dumps({'passed':True,'original_report':str(w/'evidence/199/failed-first-phone-http/main-browser.json'),'rows':results},indent=2)+'\n')
