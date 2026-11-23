"""Bind the street passage and two height-bounded facade cuts to the signed raw and production predecessor."""
import argparse
from hashlib import sha256
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
MODEL = 'huangpu-cozy-apartments-494-lane-portal'
PREVIOUS = 'huangpu-sino-german-hospital-courtyard-loggia'
CATALOG = 'data/candidate-city-integrations.json'

def read(file):
    return json.loads(file.read_bytes())

def digest(content):
    return sha256(content).hexdigest()

def check_parent(order, parent_file, comparison_file, out):
    raw = read(parent_file)
    comparison = read(comparison_file)
    assert order in (276,327) and raw['order'] == comparison['order'] == order
    assert comparison['passed'] and comparison['port'] == 31000 + order
    snapshot = Path(raw['snapshot'])
    assert digest(snapshot.read_bytes()) == raw['sha256']
    raw_catalog = Path(raw['root'])/'projects/shanghai'/CATALOG
    assert digest(raw_catalog.read_bytes()) == raw['catalog_sha256'] == read(snapshot)['files'][CATALOG]
    ids = [r['id'] for r in read(raw_catalog)['models']]
    assert len(set(ids)) == len(ids) and MODEL not in ids
    assert read(raw_catalog)['resulting_city_count'] == raw['count']
    if order == 327:
        assert ids[-1] == PREVIOUS
    sys.path.insert(0,os.environ['SHANGHAI_VERIFICATION_TOOLS'])
    from common import full, canon
    production = full(order)
    assert digest(canon(production)) == comparison['production_receipt_sha256']
    def fetch(key):
        with urlopen(f"http://127.0.0.1:{comparison['port']}/"+key, timeout=45) as res:
            assert res.status == 200
            value = res.read()
        if key in production['files']:
            assert digest(value) == production['files'][key], key
        return value
    catalog=fetch(CATALOG)
    assert [row['id'] for row in json.loads(catalog)['models']]==ids
    review=PROJECT/'source/precise'/MODEL/'footprint-review.json'
    copy_from = HERE/'placement-inputs'
    with TemporaryDirectory(dir=out) as dirname:
        scratch = Path(dirname)
        sources = {'footprint-review.json':review,
                   'final-placement-contract.json':HERE/'final-placement-contract.json',
                   'placement-geometry.json':HERE/'placement-geometry.json'}
        sources.update({n:copy_from/n for n in ('portal-frame.json','vector-scope.json','vector.pbf.gz','model-assets.json')})
        for name,original in sources.items():
            (scratch/name).symlink_to(original)
        env={**os.environ,'COZY_WORK':str(scratch),'COZY_PROJECT':str(PROJECT),
             'OPENBLAS_NUM_THREADS':'1','COZY_VECTOR_FILE':str(copy_from/'vector.pbf.gz')}
        run = lambda name, *args: subprocess.run([sys.executable,'-B',copy_from/name,*args], env=env,check=True)
        run('runtime.py',str(order))
        run('vector-runtime.py')
        base=read(scratch/'runtime-baseline.json')
        checked=read(scratch/'runtime-placement.json')
        vec=read(scratch/'vector-renderer.json')
        assert base['source']==ids[-1] and base['catalog_sha256']==digest(catalog)
        assert checked['after']['triangles']-checked['before']['triangles']==read(scratch/'map-case.json')['addedTriangles']
        assert vec['passed'] and vec['checked_neighbor_components']==2297
        camera = read(HERE/'overview-sightlines.json')
        assert camera['camera_module_sha256']==digest(fetch('src/candidate-overview-camera.js'))
        macro_base='assets/city-detail/macros/'+read(review)['frozen_macro']+'/'
        macro_files={}
        for record in read(review)['frozen_bindings']:
            key=record['repository_path'].split('projects/shanghai/',1)[1]
            value=fetch(key)
            assert digest(value)==record['sha256'] and len(value)==record['bytes']
            macro_files[key]=digest(value)
        for row in read(HERE/'neighbor-meshes.json')['source_triangle_counts']:
            key=macro_base+row['group']
            if key not in macro_files:
                macro_files[key]=digest(fetch(key))
            assert macro_files[key]==row['source_sha256']
        for key,value in base['inputs'].items():
            if key not in production['files']:
                assert key.startswith('vendor/'), key
                body=fetch(key)
                ref=f"{read(review)['baseline_commit']}:projects/shanghai/{key}"
                oid=subprocess.check_output(['git','--no-lazy-fetch','-C',PROJECT.parents[1],'rev-parse',ref],text=True).strip()
                from hashlib import sha1
                assert sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid and digest(body)==value
        prefix = f'verified-{order}' if order==327 else 'early'
        items={('map-case.json' if order==327 else 'early-map-case.json'):'map-case.json',
               prefix+'-vector.json':'vector-renderer.json',prefix+'-clip-table.json':'runtime-placement.json'}
        result={'id':MODEL,'order':328,'parent_order':order,'passed':True,'physical_url_port':comparison['port'],
                'raw_receipt_sha256':digest(parent_file.read_bytes()),'raw_catalog_sha256':raw['catalog_sha256'],
                'raw_snapshot_sha256':raw['sha256'],'production_sha256':comparison['production_receipt_sha256'],
                'comparison_sha256':digest(comparison_file.read_bytes()),'http_sha256':base['inputs'],
                'camera_module_sha256':camera['camera_module_sha256'],'verified_original_macro':macro_files,
                'contract_sha256':digest((HERE/'final-placement-contract.json').read_bytes()),
                'files':{name:digest((scratch/file).read_bytes()) for name,file in items.items()}}
        documents={name:(scratch/file).read_bytes() for name,file in items.items()}
        documents[prefix+'-placement.json']=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
        for name,payload in documents.items():
            target=out/name
            if target.exists(): assert target.read_bytes()==payload, name
        for name,payload in documents.items():
            target=out/name
            if not target.exists():
                staged=scratch/('emit-'+name);staged.write_bytes(payload);os.replace(staged,target)

if __name__=='__main__':
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('--parent',required=True,type=Path)
    args.add_argument('--comparison',required=True,type=Path)
    args.add_argument('--required-order',type=int,default=327)
    args.add_argument('--out',required=True,type=Path)
    options=args.parse_args()
    options.out.mkdir(parents=True,exist_ok=True)
    check_parent(options.required_order,options.parent,options.comparison,options.out)
