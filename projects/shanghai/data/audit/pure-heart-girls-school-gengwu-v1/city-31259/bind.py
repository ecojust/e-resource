"""Read the ordinary public pages and sign the site's historic marker and saved model downloads."""
from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256
import json,sys
w=Path(__file__).resolve().parent
p=Path('/workspace/e-resource/projects/shanghai')
a=p/'data/audit/pure-heart-girls-school-gengwu-v1'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full,canon,SCENES
read=lambda f:json.loads(f.read_bytes())
h=lambda b:sha256(b).hexdigest()
catalog_path='data/candidate-city-integrations.json'
ident='huangpu-pure-heart-girls-school-gengwu-front'
prior='huangpu-ruikang-comprador-residence'
viewer=read(a/'viewer.json');contract=read(a/'final-placement-contract.json');origins={};catalogs=[]
for n,count in [(258,293),(259,294)]:
    sig=full(n);release=read(SCENES/f'{n}-comparison.json')
    assert release['passed'] and h(canon(sig))==release['production_receipt_sha256']
    urls={r['path']:r['actual_url'] for r in release['files']};base=f'http://127.0.0.1:{31000+n}/';rows={}
    def get(k):
        url=base+urls.get(k,k)
        with urlopen(url,timeout=90) as r:assert r.status==200;body=r.read()
        assert h(body)==sig['files'][k],k
        rows[k]=dict(sha256=h(body),bytes=len(body),url=url)
        return body
    catalog=json.loads(get(catalog_path));catalogs.append(catalog)
    assert catalog['resulting_city_count']==count and prior in {r['id'] for r in catalog['models']}
    for k in ['index.html','landmarks.html','src/app.js','src/map-scene.js','src/historical-view.js','src/precise-registration-ui.js','src/candidate-city-integrations.js']:get(k)
    if n==258:assert all(row['id']!=ident for row in catalog['models'])
    else:
        row=catalog['models'][-1];assert row['id']==ident and row['kind']=='historical-site' and catalog['models'][:-1]==catalogs[0]['models']
        for k in ['historical_view','collision_geometry','replacement_geometry','source_feature_ids','navigation','lng','lat']:assert row[k]==contract[k],k
        assert row['historical_view']=={'kind':'archival-facade','building_year':1930,'evidence_years':[2014,2014]}
        assert release['previous_catalog_sha256']==origins['258']['catalog_sha256']
        page=get(row['individual_page']).decode();assert '民国照片与2014年11月23日的正面照' in page and '五个开间、两层通高的柱列和山花圆窗' in page
        manifest=json.loads(get(row['candidate_manifest']))
        assert viewer['passed'] and len(viewer['views'])==6 and len(viewer['downloads'])==4 and viewer['base']==base
        assert {v['filename'] for v in viewer['views']}=={'viewer-'+device+'-'+view+'.png' for device in ('desktop','mobile')for view in ('full','gengwu-capitals-and-windows','lod')}
        for view in viewer['views']:assert h((a/view['filename']).read_bytes())==view['sha256']
        for k,v in viewer['files'].items():assert h(get(k))==v
        for role,v in manifest['assets'].items():
            k=str(Path(row['candidate_manifest']).parent/v['file'])
            assert h(get(k))==v['sha256']==viewer['downloads'][role]['sha256'] and rows[k]['bytes']==v['bytes']
    origins[str(n)]=dict(url=base,count=count,signed_files=len(sig['files']),snapshot_sha256=release['production_receipt_sha256'],catalog_sha256=rows[catalog_path]['sha256'],files=rows)
result=dict(id=ident,previous=prior,origins=origins,name=row['name'],page=row['individual_page'],point=[row['lng'],row['lat']],previous_last_id=catalogs[0]['models'][-1]['id'],earlier_rows_unchanged=len(catalogs[0]['models']),location_scope=row['historical_view'],saved_downloads=4,viewer_sha256=h((a/'viewer.json').read_bytes()))
dest=w/'bound-inputs.json';tmp=dest.with_suffix('.part');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');tmp.replace(dest)
print([r['count'] for r in origins.values()],result['point'])
