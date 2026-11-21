"""Check each live 31k asset used by the public directory and the same historical viewer in both releases."""
from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256
import json,runpy
d=Path(__file__).parent;proj=Path('/workspace/e-resource/projects/shanghai'); audit=proj/'data/audit/wuyi-road-127-garden-front-v1';tier=Path('/tmp/shanghai-yongjia-porch');lib=runpy.run_path(str(tier/'common.py'));canon=lib['canon'];full=lib['full'];h=lambda b:sha256(b).hexdigest();rd=lambda f:json.loads(f.read_bytes())
ident='changning-wuyi-road-127-garden-front';prior='xuhui-jianguo-618-historic-front';origins={};older=None;prevsha=None;oldviewer=rd(audit/'viewer.json');assert oldviewer['passed']and len(oldviewer['views'])==4
for n in [182,183]:
 base=f'http://127.0.0.1:{31000+n}/';s=full(n);snap=canon(s);c=rd(tier/'scenes'/f'{n}-comparison.json')
 assert c['passed'] and h(snap)==c['production_receipt_sha256']and set(c['changed_paths'])=={'src/app.js','src/candidate-overview-camera.js','index.html','tests/candidate-overview-camera.test.mjs'}
 (d/f'{n}-comparison.json').write_bytes((tier/'scenes'/f'{n}-comparison.json').read_bytes())
 urls={r['path']:r['actual_url']for r in c['files']};receipt={}
 def get(k):
  url=base+urls.get(k,k)
  with urlopen(url,timeout=45)as f:b=f.read();assert f.status==200
  assert h(b)==s['files'][k],k;receipt[k]={'sha256':h(b),'bytes':len(b),'url':url};return b
 for k in ['src/candidate-overview-camera.js','src/building-beacons.js','src/building-beacon-groups.js','index.html','landmarks.html','src/app.js','src/historical-view.js','src/candidate-city-integrations.js','src/precise-registration-ui.js','src/map-scene.js','src/candidate-city-clipping.js','tests/candidate-overview-camera.test.mjs']:get(k)
 b=get('data/candidate-city-integrations.json');catalog=json.loads(b);rows=catalog['models'];assert catalog['resulting_city_count']==n+37
 if n==182:assert all(r['id']!=ident for r in rows)and rows[-1]['id']==prior
 else:
  assert s['previous_catalog_sha256']==prevsha and rows[:-1]==older and rows[-1]['id']==ident
  row=rows[-1];contract=rd(audit/'final-placement-contract.json')
  for k in ['historical_view','source_feature_ids','navigation','collision_geometry','replacement_geometry']:assert row[k]==contract[k]
  manifest=json.loads(get(row['candidate_manifest']))
  for k in oldviewer['files']:assert h(get(k))==oldviewer['files'][k]
  for k,asset in manifest['assets'].items():
   f=str(Path(row['candidate_manifest']).parent/asset['file']);assert h(get(f))==asset['sha256']==oldviewer['downloads'][k]['sha256']
  for item in oldviewer['views']:assert h((audit/item['filename']).read_bytes())==item['sha256']
  assert all(term in (proj/row['individual_page']).read_text()for term in ['三跨玻璃廊','1925年','1932年','2018年及2024年'])
 origins[str(n)]={'url':base,'catalog_sha256':h(b),'count':catalog['resulting_city_count'],'registered_candidate_rows':len(rows),'signed_files':len(s['files']),'snapshot_sha256':h(snap),'files':receipt};older=rows;prevsha=h(b)
(d/'bound-inputs.json').write_bytes(canon({'previous':prior,'id':ident,'origins':origins,'previous_city_entries':219,'earlier_candidate_rows_unchanged':len(rows)-1,'exterior_reference':row['historical_view'],'existing_viewer_sha256':h((audit/'viewer.json').read_bytes()),'old_viewer_screenshots':4}))
(d/'31k-live-inputs.json').write_bytes(canon({'order':183,'passed':True,'stages':{n:origins[n]['snapshot_sha256']for n in origins},'runner_sha256':h((d/'check-historical-map.cjs').read_bytes()),'sequence_sha256':h((d/'sequence.sh').read_bytes()),'initial_viewer_script_sha256':oldviewer['scriptSHA256'],'current_viewer_script_sha256':h((proj/'tools/check-candidate-viewer.cjs').read_bytes())}))
