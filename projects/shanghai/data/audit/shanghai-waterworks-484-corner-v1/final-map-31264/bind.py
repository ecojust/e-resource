"""Bind the two real city catalogs and huangpu-shanghai-waterworks-484-corner' previously photographed standalone."""
import hashlib,json,sys
from pathlib import Path
from urllib.request import urlopen
w=Path(__file__).parent;P=Path('/workspace/e-resource/projects/shanghai');ident='huangpu-shanghai-waterworks-484-corner'
a=P/'data/audit/shanghai-waterworks-484-corner-v1'; key='data/candidate-city-integrations.json'
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full,canon
h=lambda b:hashlib.sha256(b).hexdigest()
rd=lambda f:json.loads(f.read_bytes())
results={};prev=None
for n in (263,264):
 signature=full(n)
 cmp=rd(Path('/tmp/shanghai-yongjia-porch/scenes')/f'{n}-comparison.json')
 assert cmp['passed'] and h(canon(signature))==cmp['production_receipt_sha256']
 origin=f'http://127.0.0.1:{31000+n}/'; files={}
 def get(f):
  with urlopen(origin+f,timeout=70) as r:assert r.status==200;b=r.read()
  assert signature['files'][f]==h(b),(f,h(b));files[f]={'sha256':h(b),'bytes':len(b)};return b
 raw=get(key);rows=json.loads(raw)
 for f in ('index.html','landmarks.html','src/app.js','src/map-scene.js','src/candidate-city-integrations.js','src/candidate-overview-camera.js'):get(f)
 if n==263:
  assert rows['resulting_city_count']==298 and not any(r['id']==ident for r in rows['models'])
 else:
  assert rows['resulting_city_count']==299 and rows['models'][:-1]==prev['models'] and signature['previous_catalog_sha256']==results[263]['catalog_sha256']
  row=rows['models'][-1];contract=rd(a/'final-placement-contract.json')
  assert row['id']==ident and row['owner']['feature_local_id']==1766
  for field in ('owner','source_feature_ids','model_geometry_sha256','collision_geometry','replacement_geometry','overviewBearing','overviewZoom','overviewPitch'):assert row[field]==contract[field],field
  assert get('data/audit/shanghai-waterworks-484-corner-v1/final-placement-contract.json')==(a/'final-placement-contract.json').read_bytes()
  view=rd(a/'viewer.json');m=json.loads(get(row['candidate_manifest']));assert view['passed']and len(view['views'])==6
  for f,old in view['files'].items():assert h(get(f))==(old if isinstance(old,str)else old['sha256'])
  for k,asset in m['assets'].items():
   f=str(Path(row['candidate_manifest']).parent/asset['file']);assert h(get(f))==asset['sha256']==view['downloads'][k]['sha256']
  for v in view['views']:assert h((a/v['filename']).read_bytes())==v['sha256']
  assert {(v['role'],v['viewport']['width'])for v in view['views']}=={(role,width)for role in ['full','lod']for width in [1250,390]} and len(view['views'])==6
 results[n]=dict(count=rows['resulting_city_count'],catalog_sha256=h(raw),signed_inputs=len(signature['files']),signature_sha256=h(canon(signature)),origin=origin,fetched=files);prev=rows
(w/'bound-inputs.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print([(k,v['count'],len(v['fetched']))for k,v in results.items()])
