"""Read every signed file on 31258 again because the earlier complete byte receipt used the preceding order number."""
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,gzip,sys,time
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full,canon
P=Path('/workspace/e-resource/projects/shanghai/data/audit/ruikang-comprador-residence-v1')
old=P/'31258-all-http.json';original=json.loads(old.read_bytes());snapshot=full(258)
def h(b):return hashlib.sha256(b).hexdigest()
assert original['port']==31258 and original['order']==257 and original['passed'] and original['production_receipt_sha256']==h(canon(snapshot))
assert {v['path']:v['sha256']for v in original['files']}==snapshot['files'] and len(original['files'])==1882
def check(row):
 url='http://127.0.0.1:31258/'+row['actual_url'].lstrip('/')
 with urlopen(url,timeout=150)as body:
  assert body.status==200 and body.url==url
  s=hashlib.sha256();count=0
  while block:=body.read(96*1024):count+=len(block);s.update(block)
  assert count==row['bytes']and s.hexdigest()==snapshot['files'][row['path']]
 return {**row,'bytes':count,'sha256':s.hexdigest()}
start=time.time()
with ThreadPoolExecutor(2)as pool:checked=list(pool.map(check,original['files']))
assert sum(x['bytes']for x in checked)==1535335630
receipt=dict(passed=True,order=258,port=31258,count=len(checked),bytes=sum(x['bytes']for x in checked),production_receipt_sha256=h(canon(snapshot)),previous_record=str(old.name),previous_record_sha256=h(old.read_bytes()),previous_recorded_order=original['order'],rechecked_started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(start)),rechecked_finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),files=checked)
target=P/'31258-all-http-order-verified.json.gz';data=gzip.compress(json.dumps(receipt,ensure_ascii=False,separators=(',',':')).encode(),compresslevel=6,mtime=0)
if not target.exists():
 out=target.with_suffix('.pending');out.write_bytes(data);assert json.loads(gzip.decompress(out.read_bytes()))==receipt;out.replace(target)
print(len(checked),receipt['bytes'],h(target.read_bytes()),flush=True)
