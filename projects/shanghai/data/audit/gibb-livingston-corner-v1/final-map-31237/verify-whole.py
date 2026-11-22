"""Bind the individually recorded 237 HTTP responses and compare five actual byte ranges."""
from pathlib import Path
from urllib.request import Request,urlopen
from hashlib import sha256
import json,sys
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai')
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full,canon
read=lambda f:json.loads(f.read_bytes());sha=lambda b:sha256(b).hexdigest()
a=p/'data/audit/gibb-livingston-corner-v1'
j=read(a/'31237-all-http.json');snapshot=full(237);comparison=read(Path('/tmp/shanghai-yongjia-porch/scenes/237-comparison.json'))
assert j['passed'] and j['order']==237 and j['port']==31237
assert j['production_receipt_sha256']==comparison['production_receipt_sha256']==sha(canon(snapshot))
assert len(j['files'])==len(snapshot['files'])==j['count'] and sum(r['bytes'] for r in j['files'])==j['bytes']
assert {r['path']:r['sha256'] for r in j['files']}==snapshot['files']
urls={r['path']:r['actual_url']for r in j['files']}
ranges=[]
for name in ('index.html','src/app.js','src/candidate-overview-camera.js','tests/candidate-overview-camera.test.mjs','assets/models/candidates/huangpu-gibb-livingston-corner/'+read(p/'assets/models/candidates/huangpu-gibb-livingston-corner/manifest.json')['assets']['full']['file']):
 url='http://127.0.0.1:31237/'+urls[name]
 with urlopen(url,timeout=30)as res:
  b=res.read();assert res.status==200 and sha(b)==snapshot['files'][name]
 with urlopen(Request(url,headers={'Range':'bytes=21-45'}),timeout=30)as res:
  part=res.read();assert res.status==206 and res.headers['Content-Range']==f'bytes 21-45/{len(b)}' and part==b[21:46]
 ranges.append(dict(path=name,sha256=sha(b),range_sha256=sha(part),bytes='21-45'))
out=dict(passed=True,count=j['count'],total_bytes=j['bytes'],production_receipt_sha256=j['production_receipt_sha256'],source_receipt='data/audit/gibb-livingston-corner-v1/31237-all-http.json',source_receipt_sha256=sha((a/'31237-all-http.json').read_bytes()),ranges=ranges)
(w/'all-http.json').write_text(json.dumps(out,indent=2)+'\n')
print(j['count'],j['bytes'],len(ranges))
