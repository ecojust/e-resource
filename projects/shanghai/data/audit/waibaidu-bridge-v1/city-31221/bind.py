from pathlib import Path
import json,importlib.util,hashlib
from urllib.request import urlopen
from bs4 import BeautifulSoup
W=Path(__file__).resolve().parent;P=Path('/workspace/e-resource/projects/shanghai')
J=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
layer=Path('/tmp/shanghai-yongjia-porch');s=importlib.util.spec_from_file_location('camera31',layer/'common.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows={};id='huangpu-waibaidu-bridge'
for n in (220,221):
 manifest=m.full(n);proof=J(layer/'scenes'/f'{n}-comparison.json');assert proof['passed']and sha(m.canon(manifest))==proof['production_receipt_sha256']
 files=manifest['files'];port=31000+n;b=f'http://127.0.0.1:{port}/';items={}
 def get(key,check=True):
  with urlopen(b+key,timeout=45)as r:assert r.status==200;data=r.read()
  h=sha(data);items[key]=dict(bytes=len(data),sha256=h);assert not check or h==files[key];return data
 catalog=json.loads(get(m.CAT));lamps=catalog['models']
 assert catalog['resulting_city_count']==n+37 and sum(r['id']==id for r in lamps)==(n==221)
 directory=BeautifulSoup(get('landmarks.html'),'html.parser');cards=directory.select(f'article[data-landmark="{id}"]')
 assert len(cards)==(n==221)
 for key in ['index.html','src/app.js','src/map-scene.js','src/building-beacons.js','src/candidate-city-integrations.js','src/candidate-bridge-walk.js','src/candidate-asset-viewer.js']:
  if n==221 or key in files:get(key)
 if n==221:
  card=cards[0];links=[a.get('href')for a in card.select('a')];assert any(a.endswith('mode=walk')for a in links)and any(a.endswith('mode=overview')for a in links)
  row=next(r for r in lamps if r['id']==id);contract=J(P/'data/audit/waibaidu-bridge-v1/final-placement-contract.json')
  for k in ('bridge_walk','navigation','model_geometry_sha256','lng','lat','heading','altitude','replacement_geometry','source_feature_ids'):
   assert row[k]==contract[k],k
  single=get('waibaidu-bridge.html');meta=json.loads(get(row['candidate_manifest']))
  for asset in meta['assets'].values():
   path=(Path(row['candidate_manifest']).parent/asset['file']).as_posix();assert sha(get(path))==asset['sha256']
  assert set(row['bridge_walk']['transportation_feature_ids'])
 rows[n]={'port':port,'count':catalog['resulting_city_count'],'candidate_count':len(lamps),'catalog_sha256':items[m.CAT]['sha256'],'production_sha256':proof['production_receipt_sha256'],'files':items,'standalone_and_directory_links':links if n==221 else []}
out={'passed':True,'rows':rows,'contract_sha256':sha((P/'data/audit/waibaidu-bridge-v1/final-placement-contract.json').read_bytes())};(W/'presentation-inputs.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print([(n,x['count'],len(x['files']))for n,x in rows.items()])
