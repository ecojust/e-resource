"""Recheck the signed Sino-German Hospital courtyard loggia on the two frozen city editions."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urljoin
import gzip
import hashlib
import json
import sys

root=Path(__file__).absolute().parent
def read(name):return json.loads((root/name).read_bytes())
def hashed(raw):return hashlib.sha256(raw).hexdigest()
def fetch(base,path):
    with urlopen(urljoin(base.rstrip('/')+'/',path),timeout=90) as response:
        assert response.status==200
        return response.read()
def check(year,base):
    c=read(f'{year}-comparison.json')
    raw=gzip.decompress((root/f'{year}-production.json.gz').read_bytes())
    assert hashed(raw)==c['production_receipt_sha256']
    signed=json.loads(raw)['files']; routes={x['path']:x['actual_url'] for x in c['files']}
    parent={ 'verified_original_macro': {x['repository_path'].removeprefix('projects/shanghai/'):x['sha256'] for x in read('original-review.json')['frozen_bindings']} }
    paths=set(parent['verified_original_macro'])
    paths.add('data/candidate-city-integrations.json')
    if year==327:paths.add('data/audit/sino-german-hospital-courtyard-loggia-v1/final-placement-contract.json')
    for key in sorted(paths):
        x=fetch(base,routes.get(key,key))
        expected=signed.get(key) or parent['verified_original_macro'].get(key)
        assert expected and hashed(x)==expected,(year,key,hashed(x),expected)
        if key=='data/candidate-city-integrations.json':catalog=json.loads(x)
        elif key.endswith('/final-placement-contract.json'):contract=json.loads(x)
    assert catalog['resulting_city_count']==year+35
    if year==327:
        row=catalog['models'][-1]
        for key in ('id','owner','model_geometry_sha256','replacement_geometry','display_height_clips','collision_geometry','heading','lat','lng'):
            assert row[key]==contract[key]
        assert row['owner']['feature_local_id']==369
    return catalog['models']
if __name__=='__main__':
    urls=sys.argv[1:] or ['http://127.0.0.1:31326/','http://127.0.0.1:31327/']
    assert len(urls)==2
    prev,now=(check(n,b) for n,b in zip((326,327),urls))
    assert now[:-1]==prev
    print('Verified the predecessor, the added courtyard loggia, and its operative placement.')
