"""Read both original releases and restore the local browser inputs from their signed bytes."""
from hashlib import sha256
from pathlib import Path
import gzip, json, os, tempfile
from urllib.request import urlopen

stage=Path('/tmp/shanghai-main-281/formal-31281')
work=Path(__file__).resolve().parent
scenes=Path('/tmp/shanghai-yongjia-porch/scenes')
model='huangpu-cathedral-school-jiujiang-front'
review=json.loads((stage/'signed-comparison.json').read_bytes())
store=Path('/dev/shm/reopened-281-camera-inputs')
store.mkdir(exist_ok=True)
def installed(p,data,digest):
    assert sha256(data).hexdigest()==digest
    if p.is_file():
        assert sha256(p.read_bytes()).hexdigest()==digest,p
        return
    p.parent.mkdir(parents=True,exist_ok=True)
    anchor=store/digest
    if not anchor.exists():
        with tempfile.NamedTemporaryFile(dir=store,delete=False)as out:
            tmp=Path(out.name)
            try:
                out.write(data);out.flush();os.fsync(out.fileno());os.replace(tmp,anchor)
            finally:tmp.unlink(missing_ok=True)
    assert sha256(anchor.read_bytes()).hexdigest()==digest
    temp=p.with_name(p.name+'.reopened-281')
    temp.symlink_to(anchor)
    temp.replace(p)
    assert p.read_bytes()==data
def get(url):
    with urlopen(url,timeout=75) as response:
        assert response.status==200
        return response.read()
checked=[]
catalogs=[]
for row in review['stages']:
    n=row['n']
    assert n in (280,281)
    origin=f'http://127.0.0.1:{31000+n}/'
    book=gzip.decompress((stage/f'{n}-production.json.gz').read_bytes())
    assert sha256(book).hexdigest()==row['production_sha256']
    signatures=json.loads(book)['files']
    complete=json.loads((scenes/f'{n}-all-http.json').read_bytes())
    assert complete['passed'] and complete['count']==len(signatures) and len(complete['ranges'])>=5 and complete['production_receipt_sha256']==row['production_sha256']
    for path,item in row['actual_reads'].items():
        assert item['url'].startswith(origin)
        data=get(item['url']);digest=sha256(data).hexdigest()
        assert digest==item['sha256']==signatures[path] and len(data)==item['bytes']
        if path.startswith('src/') or path in ('data/candidate-city-integrations.json','landmarks.html','index.html'):
            installed(stage/f'stage{n}'/path,data,digest)
        if path=='data/candidate-city-integrations.json':
            catalog=json.loads(data);assert digest==row['catalog_sha256'] and catalog['resulting_city_count']==n+35
            catalogs.append(catalog['models'])
        if n==281 and (path in ('cathedral-school-jiujiang-front.html','src/candidate-asset-viewer.js') or path.endswith('/manifest.json')):
            installed(stage/'current-viewer-inputs'/path,data,digest)
        checked.append({'period':n,'path':path,'sha256':digest,'bytes':len(data)})
    for path,item in review['original_city_bindings_retrieved_on_both'].items():
        b=get(origin+path);assert len(b)==item['bytes'] and sha256(b).hexdigest()==item['sha256']
assert catalogs[0]==catalogs[1][:-1] and catalogs[1][-1]['id']==model
(work/'reopened-sites.json').write_text(json.dumps({'inputs':checked,'passed':True},indent=2)+'\n')
