"""Check the signed photographic wording and approximate register marker on both releases."""
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen
import json

w=Path(__file__).parent
binding=json.loads((w/'bound-inputs.json').read_bytes())
evidence={}
ident=binding['id']
page='jianguo-618-historic-front-history.html'
for n in ['181','182']:
    site=binding['origins'][n]
    sig=json.loads((w/(n+'-production.json')).read_bytes())['files']
    def fetch(path):
        with urlopen(site['url']+path, timeout=35) as reply:
            assert reply.status==200
            body=reply.read()
        digest=sha256(body).hexdigest()
        assert digest==sig[path]
        return body,digest
    cr,cat_hash=fetch('data/candidate-city-integrations.json')
    catalog=json.loads(cr)
    rows=catalog['models']
    assert catalog['resulting_city_count']==site['count']
    sources={}
    for f in ('src/app.js','src/candidate-city-integrations.js','src/historical-view.js'):
        raw,digest=fetch(f)
        text=raw.decode()
        sources[f]={'sha256':digest}
        if f.endswith('app.js'):
            assert 'pitch:60,bearing:place.bearing??35' in text
        elif f.endswith('integrations.js'):
            assert 'overviewZoom:17.4' in text
        elif n=='182':
            assert 'first===last ? String(first)' in text
            assert '${period}年照片' in text
    if n=='181':
        assert all(row['id']!=ident for row in rows)
        old=rows
    else:
        item=rows[-1]
        assert rows[:-1]==old and item['id']==ident
        assert item['historical_view']['evidence_years']==[2013,2013] and item['historical_view']['building_year']==1948
        assert 'bounds_glb' not in item and 'bearing' not in item and item['navigation']=={'listed':False}
        assert not item['collision_geometry'] and not item['replacement_geometry'] and not any(item['source_feature_ids'].values())
        b,digest=fetch(page)
        text=b.decode()
        for word in ('2013年7月10日','挑阳台','斜看板底与栏板','俯看挑阳台','扶手下的窄缝'):assert word in text
        sources[page]={'sha256':digest,'features':['挑阳台外缘','扶手下的窄缝和两层窗列','实体栏板侧向收口']}
    evidence[n]={'origin':site['url'],'city_count':site['count'],'catalog_sha256':cat_hash,'sources':sources}
result={'id':ident,'origins':evidence,'city_focus':{'rounded_center':[item['lng'],item['lat']],'zoom':17.4,'pitch':60,'bearing':35},'photo_date':'2013-07-10','register_building_year':1948,'period_caption':'2013年照片','source_cuts':0,'current_model':False,'registered_mode':'独立历史立面展件，街区资料标记'}
(w/'historical-focus-preflight.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
