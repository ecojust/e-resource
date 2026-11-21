"""Bind 223 and 224 public entries; verify the prior model, archive page and signed standalone bytes."""
from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256
import json
w=Path(__file__).parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/hongqiao-road-2275-history-v1')
read=lambda f:json.loads(f.read_bytes());h=lambda b:sha256(b).hexdigest()
path='data/candidate-city-integrations.json';ident='changning-hongqiao-road-2275-historic-front';prior='changning-xinhua-lane-329-no17';catalogs=[];origins={}
for n,count in [(186,223),(187,224)]:
 base=f'http://127.0.0.1:{31000+n}/';snap=Path('/tmp/hongqiao187/final-map-31187')/f'{n}-production.json';base_source=Path('/tmp/shanghai-east-medical-focus/scenes')
 full=read(base_source/f'{n}-production.json')
 raw=base_source/f'{n}-production.json'
 for folder in ('shanghai-riyue-courtyard','shanghai-yongjia-porch'):
  patch=read(Path('/tmp')/folder/'scenes'/f'{n}-comparison.json')
  assert h(raw.read_bytes())==patch['parent_receipt_sha256']
  full['files'].update((k,v['after'])for k,v in patch['changed_paths'].items())
  raw=w/(f'{n}-production.json');raw.write_text(json.dumps(full,ensure_ascii=False,indent=2)+'\n')
  assert h(raw.read_bytes())==patch['production_receipt_sha256']
 s=full;receipt={}
 def get(f):
  with urlopen(base+f,timeout=60)as resp: assert resp.status==200;b=resp.read()
  fingerprint=h(b);assert fingerprint==s['files'][f],f
  receipt[f]={'sha256':fingerprint,'bytes':len(b)}
  return b
 body=get(path);catalog=json.loads(body);catalogs.append(catalog)
 assert catalog['resulting_city_count']==count and any(r['id']==prior for r in catalog['models'])
 for f in ['index.html','landmarks.html','src/app.js','src/historical-view.js','src/candidate-city-integrations.js','src/precise-registration-ui.js','src/map-scene.js']:get(f)
 if n==186:assert all(r['id']!=ident for r in catalog['models'])
 else:
  marker=catalog['models'][-1];assert marker['id']==ident and catalog['models'][:-1]==catalogs[0]['models']
  assert patch['previous_catalog_sha256']==origins['186']['catalog_sha256']
  contract=read(a/'final-placement-contract.json');assert marker['historical_view']==contract['historical_view']
  for k in ('navigation','collision_geometry','replacement_geometry','source_feature_ids'):assert marker[k]==contract[k]
  manifest=json.loads(get(marker['candidate_manifest']));page=get(marker['individual_page'])
  assert '2015年出版、2020年重刊' in page.decode()
  old_viewer=read(a/'viewer.json');assert old_viewer['passed']and len(old_viewer['views'])==4
  assert old_viewer['files'][marker['individual_page']]==h(page)
  for role,v in manifest['assets'].items():
   data=get(str(Path(marker['candidate_manifest']).parent/v['file']));assert h(data)==v['sha256']==old_viewer['downloads'][role]['sha256']
  for view in old_viewer['views']:assert h((a/view['filename']).read_bytes())==view['sha256']
  for k in old_viewer['files']:
   blob=get(k)if not k in receipt else None
   assert old_viewer['files'][k]==receipt[k]['sha256']
 origins[str(n)]={'url':base,'catalog_sha256':h(body),'count':count,'signed_files':len(s['files']),'snapshot_sha256':h(snap.read_bytes()),'files':receipt}
(w/'bound-inputs.json').write_text(json.dumps({'previous':prior,'id':ident,'origins':origins,'earlier_rows_unchanged':len(catalogs[0]['models']),'exterior_reference':marker['historical_view'],'existing_viewer_sha256':h((a/'viewer.json').read_bytes()),'old_viewer_screenshots':4},ensure_ascii=False,indent=2)+'\n')
