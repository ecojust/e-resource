"""Fetch the actual HTTP modules selected by this site's cache-key chain."""
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen

number = int(sys.argv[1])
receipt = Path(sys.argv[2])
port = int(sys.argv[3])
directory = Path(sys.argv[4])
files = json.loads(receipt.read_bytes())['files']
site = f'http://127.0.0.1:{port}/'
evidence = {}
def get(url):
    name = urlsplit(url).path.lstrip('/')
    with urlopen(url, timeout=60) as response:
        body = response.read()
        assert response.status == 200
    fingerprint = sha256(body).hexdigest()
    assert fingerprint == files[name], (url, fingerprint, files[name])
    evidence[url] = {'sha256':fingerprint,'bytes':len(body)}
    return body.decode()
def linked(html, regex, src):
    matches = re.findall(regex, html)
    assert len(matches)==1,(src,regex,matches)
    url = urljoin(src,matches[0])
    return url,get(url)
index = get(site+'index.html')
app_url,app = linked(index, r'<script type="module" src="(src/app\.js\?v=[a-z0-9-]+)"',site)
runtime_urls=[]
for js in ('historical-view','precise-registration-ui','candidate-city-integrations'):
    url,source = linked(app, r"from '(\./"+js+r"\.js\?v=[a-z0-9-]+)'",app_url)
    runtime_urls.append(url)
    if js=='historical-view':
        assert '年拍摄的历史照片' in source and '年刊载的历史照片，拍摄年份未详' in source
        assert '保护建筑现存，照片对应的具体楼翼待考' in source
    else:
        hist,content = linked(source,r"from '(\./historical-view\.js\?v=dated-complex-photograph-v1)'",url)
        assert '年刊载的历史照片，拍摄年份未详' in content
        if js=='precise-registration-ui':assert "evidence_kind==='dated-photograph'" in source
catalog=json.loads(get(site+'data/candidate-city-integrations.json'))['models']
marker=next(row for row in catalog if row['id']=='yangpu-yangshupu-power-turbine-hall')
assert marker['individual_page']=='yangshupu-turbine-hall.html'
assert marker['historical_view']=={'kind':'archival-facade','evidence_kind':'dated-photograph','evidence_years':[1926,1926],'site_status':'protected-building-unlocated','location_precision':'complex'}
assert marker['replacement_geometry'] is None and marker['collision_geometry'] is None and 'owner' not in marker
assert marker['navigation']=={'listed':False} and marker['source_feature_ids']=={'building':[],'building_part':[]}
chen=next(row for row in catalog if row['id']=='jingan-chen-bingqian-historic-residence')
assert chen['historical_view']['evidence_kind']=='reprinted-photograph' and chen['historical_view']['approximate_loss_year']==1994
page=get(urljoin(site,marker['individual_page']))
assert '1926' in page and '4号锅炉房' in page and 'showCandidateAssetViewer(' in page
for test in ('tests/test_historical_complex_photograph.py','tests/historical-complex-photograph.test.mjs'):
    get(site+test)
builder=get(site+'tools/build_candidate_city_integrations.py')
assert 'protected-building-unlocated' in builder and 'yangshupu-turbine-hall.html' in builder
readme_generator=get(site+'tools/sync_readme_districts.py')
assert '保护建筑现存，照片对应的具体楼翼待考' in readme_generator
out=dict(stage=number,port=port,receipt_sha256=sha256(receipt.read_bytes()).hexdigest(),signed_inputs=len(files),
         application_url=app_url,modules_from_application=runtime_urls,actual_urls=evidence,historical_view=marker['historical_view'])
directory.mkdir(exist_ok=True,parents=True)
(directory/f'cache-chain-{port}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(port,len(evidence),'actual browser cache-key and producer resources')
