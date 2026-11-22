"""Bind the two full HTTP receipts and repeat five published full-file and range reads per release."""
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
import json, sys
work = Path(__file__).parent
project = Path('/workspace/e-resource/projects/shanghai')
sys.path.insert(0, '/tmp/shanghai-yongjia-porch')
from common import full, canon
def read(path): return json.loads(path.read_bytes())
def sha(data): return sha256(data).hexdigest()
bound = read(work/'bound-inputs.json')
for n, tag in [(256,'bank-of-east-asia-corner-v1'),(257,'qianxin-historic-front-v1')]:
    previous = project/'data/audit'/tag/f'{31000+n}-all-http.json'
    receipt = read(previous)
    production = full(n)
    assert receipt['passed'] and receipt['port']==31000+n and receipt['order']==n
    assert receipt['production_receipt_sha256']==sha(canon(production))==bound['origins'][str(n)]['snapshot_sha256']
    original = {r['path']:r for r in receipt['files']}
    assert {k:r['sha256'] for k,r in original.items()}==production['files']
    assert len(original)==receipt['count'] and sum(r['bytes'] for r in original.values())==receipt['bytes']
    ident = bound['id'] if n==257 else bound['previous']
    keys=['index.html','landmarks.html','src/app.js','data/candidate-city-integrations.json',next(k for k in original if f'/{ident}/' in k and k.endswith('-web.glb'))]
    counts=[]
    for key in keys:
        url=f'http://127.0.0.1:{31000+n}/'+original[key]['actual_url'].lstrip('/')
        with urlopen(url,timeout=120) as response:
            data=response.read()
            assert response.status==200 and len(data)==original[key]['bytes'] and sha(data)==original[key]['sha256']
        with urlopen(Request(url,headers={'Range':'bytes=21-45'}),timeout=120)as response:
            segment=response.read()
            assert response.status==206 and segment==data[21:46]
            assert response.headers['Content-Range']==f'bytes 21-45/{len(data)}'
        counts.append(dict(path=key,url=url,range=[21,45],sha256=sha(segment),full_sha256=sha(data)))
    out=dict(order=n,passed=True,count=receipt['count'],bytes=receipt['bytes'],production_receipt_sha256=sha(canon(production)),original_receipt=str(previous),original_receipt_sha256=sha(previous.read_bytes()),ranges=counts)
    dest=work/f'{n}-all-http.json'
    if dest.exists():assert read(dest)==out
    else:dest.write_text(json.dumps(out,indent=2)+'\n')
    print(n,receipt['count'],receipt['bytes'])
