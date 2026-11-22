"""Restore the two historical trees from their own ordinary sites and original production signatures."""
from pathlib import Path
from urllib.request import urlopen
import hashlib,json,os,subprocess,sys
w=Path('/tmp/shanghai-main-253')
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full,canon
def put(target,b):
    target=target.resolve();target.parent.mkdir(exist_ok=True,parents=True)
    if target.is_file():assert target.read_bytes()==b,target
    else:
        t=target.with_name(target.name+'.downloading');t.write_bytes(b);os.replace(t,target)
for n in (252,253):
    sig=full(n);raw=canon(sig);bound=json.loads((w/f'{n}-bindings.json').read_bytes())
    assert hashlib.sha256(raw).hexdigest()==bound['production'] and bound['port']==31000+n
    put(w/f'{n}-production.json',raw)
    root=w/f'stage{n}';root.resolve().mkdir(parents=True,exist_ok=True)
    requests={r['path']:r['url'] for r in bound['actual']}
    for key in set(bound['files']) | set(requests):
        digest=sig['files'][key];assert bound['files'].get(key,digest)==digest
        base=f'http://127.0.0.1:{31000+n}/'
        url=requests.get(key,base+key);assert url.startswith(base)
        with urlopen(url,timeout=75)as req:assert req.status==200;data=req.read()
        assert hashlib.sha256(data).hexdigest()==digest
        put(root/key,data)
(w/'runtime253').resolve().mkdir(exist_ok=True,parents=True)
# All stage-local files which feed the runtime, DOM and image checks are now detached from the main checkout.
subprocess.run(['bash',w/'prime.sh'],cwd=w,check=True)
