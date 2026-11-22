"""Replay the two signed city catalogues and bank entrance clipping with the actual rendering modules."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
ID = 'jingan-central-reserve-bank-changshu-front'
TAG = 'central-reserve-bank-changshu-front-v1'
CATALOG = 'data/candidate-city-integrations.json'

def read(path):
    return json.loads(path.read_bytes())

def digest(value):
    return hashlib.sha256(value).hexdigest()

def replay(order, base, project, destination):
    comp = read(HERE/f'{order}-comparison.json')
    book_data = gzip.decompress((HERE/f'{order}-production.json.gz').read_bytes())
    assert comp['passed'] and comp['order'] == order
    assert comp['production_receipt_sha256'] == digest(book_data)
    book = json.loads(book_data)['files']
    route = {r['path']: r['actual_url'] for r in comp['files']}
    audit = project/'data/audit'/TAG
    reference = read(HERE/'verified-321-placement.json')
    case = read(HERE/'map-case.json')
    fetched = {}
    def fetch(key):
        requested = route.get(key,key)
        with urlopen(base.rstrip('/')+'/'+requested, timeout=60) as response:
            assert response.status == 200
            value = response.read()
        sha = digest(value)
        expected = book.get(key) or reference['http_sha256'][key]
        if sha != expected:
            raise ValueError(f'HTTP SHA-256 mismatch for {key}')
        fetched[key] = {'sha256':sha,'bytes':len(value)}
        return value
    catalog_data = fetch(CATALOG)
    catalog = json.loads(catalog_data)
    contract = read(audit/'final-placement-contract.json')
    if order == 321:
        assert not any(r['id']==ID for r in catalog['models'])
        assert catalog['resulting_city_count'] == 356 and len(catalog['models']) + catalog['existing_city_count'] == 356
        assert case['predecessor_catalog_sha256'] == digest(catalog_data)
        catalog['models'].append(contract)
        catalog['resulting_city_count'] += 1
    else:
        assert catalog['resulting_city_count'] == 357 and len(catalog['models']) + catalog['existing_city_count'] == 357
        assert catalog['models'][-1]['id'] == ID
        for field in ('owner','collision_geometry','replacement_geometry','model_geometry_sha256','lat','lng','heading'):
            assert catalog['models'][-1][field] == contract[field], field
        assert fetch(f'data/audit/{TAG}/final-placement-contract.json') == (audit/'final-placement-contract.json').read_bytes()
    with tempfile.TemporaryDirectory(prefix='changshu-map-') as directory:
        stage = Path(directory)
        (stage/'package.json').write_text('{"type":"module"}\n')
        for key in reference['http_sha256']:
            if key==CATALOG:
                continue
            target=stage/key
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(fetch(key))
        tmp_audit=stage/'review'
        tmp_audit.mkdir()
        for target,source in [('map-case.json',HERE/'map-case.json'),('final-placement-contract.json',audit/'final-placement-contract.json')]:
            (tmp_audit/target).write_bytes(source.read_bytes())
        footprint=f'source/precise/{ID}/footprint-review.json'
        target=stage/footprint
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((project/footprint).read_bytes())
        target=stage/CATALOG
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(catalog_data if order==322 else json.dumps(catalog).encode())
        subprocess.run(['node',project/'tools/check-sourced-candidate-runtime.mjs',tmp_audit/'map-case.json'],
                       env={**os.environ,'SHANGHAI_PROJECT_ROOT':str(stage),'QA_OUTPUT_DIR':str(tmp_audit)},
                       check=True)
        result=read(tmp_audit/'runtime-placement.json')
    assert result['after']['scopedTargetDraw']['clip_feature_local_ids']==sorted(set(case['existingGroupOwners'])|{3343})
    assert result['after']['triangles']-result['before']['triangles']==case['addedTriangles']
    assert len(result['ground'])==len(case['ground'])+len(case['neighbors'])
    output={'order':order,'passed':True,'mode':'previous catalogue with proposed entrance' if order==321 else 'published catalogue',
            'comparison_sha256':digest((HERE/f'{order}-comparison.json').read_bytes()),'production_sha256':digest(book_data),
            'origin':base,'retrieved':fetched,'runtime':result}
    destination.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('order',type=int,choices=(321,322))
    p.add_argument('--origin')
    p.add_argument('--project',type=Path,default=HERE.parents[3])
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    replay(args.order,args.origin or f'http://127.0.0.1:{31000+args.order}/',args.project,args.output)
