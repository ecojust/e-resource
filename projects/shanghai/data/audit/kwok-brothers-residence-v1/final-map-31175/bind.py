"""Bind 211 and 212 public entries; verify the prior model, archive page and signed standalone bytes."""
from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256
import json
w=Path(__file__).parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/kwok-brothers-residence-v1')
read=lambda f:json.loads(f.read_bytes());h=lambda b:sha256(b).hexdigest()
path='data/candidate-city-integrations.json';ident='jingan-kwok-brothers-residence-historic-front';prior='xuhui-huaihai-1431-historic-garden-front';catalogs=[];origins={}
for n,count in [(174,211),(175,212)]:
 base=f'http://127.0.0.1:{31000+n}/';snap=Path('/tmp/grace-final-31k/175')/f'{n}-production.json';s=read(snap);receipt={}
 def get(f):
  with urlopen(base+f,timeout=60)as resp: assert resp.status==200;b=resp.read()
  fingerprint=h(b);assert fingerprint==s['files'][f],f
  receipt[f]={'sha256':fingerprint,'bytes':len(b)}
  return b
 body=get(path);catalog=json.loads(body);catalogs.append(catalog)
 assert catalog['resulting_city_count']==count and any(r['id']==prior for r in catalog['models'])
 for f in ['src/candidate-overview-camera.js','src/building-beacons.js','src/building-beacon-groups.js','index.html','landmarks.html','src/app.js','src/historical-view.js','src/candidate-city-integrations.js','src/precise-registration-ui.js','src/map-scene.js']:get(f)
 if n==174:assert all(r['id']!=ident for r in catalog['models'])
 else:
  marker=catalog['models'][-1];assert marker['id']==ident and catalog['models'][:-1]==catalogs[0]['models']
  assert s['previous_catalog_sha256']==origins['174']['catalog_sha256']
  contract=read(a/'final-placement-contract.json');assert marker['historical_view']==contract['historical_view']
  for k in ('navigation','collision_geometry','replacement_geometry','source_feature_ids'):assert marker[k]==contract[k]
  manifest=json.loads(get(marker['candidate_manifest']));page=get(marker['individual_page'])
  assert all(term in page.decode() for term in ['2014年及2019年照片','中央圆饰墩','跨度、颜色和树冠遮挡处的重复节距为估计'])
  old_viewer=read(a/'viewer.json');assert old_viewer['passed']and len(old_viewer['views'])==6
  assert old_viewer['files'][marker['individual_page']]['sha256']==h(page)
  for role,v in manifest['assets'].items():
   data=get(str(Path(marker['candidate_manifest']).parent/v['file']));assert h(data)==v['sha256']==old_viewer['downloads'][role]['sha256']
  for view in old_viewer['views']:assert h((a/view['file']).read_bytes())==view['sha256']
  for k in old_viewer['files']:
   blob=get(k)if not k in receipt else None
   if k==marker['candidate_manifest']:
    index=read(a/'archival-index-classification.json');assert index['all_four_file_digests_unchanged'] and old_viewer['files'][k]['sha256']==index['before_sha256'] and receipt[k]['sha256']==index['after_sha256'] and index['actual_viewer_receipt_sha256']==h((a/'viewer.json').read_bytes())
   else:assert old_viewer['files'][k]['sha256']==receipt[k]['sha256']
 origins[str(n)]={'url':base,'catalog_sha256':h(body),'count':count,'signed_files':len(s['files']),'snapshot_sha256':h(snap.read_bytes()),'files':receipt}
(w/'bound-inputs.json').write_text(json.dumps({'previous':prior,'id':ident,'origins':origins,'earlier_rows_unchanged':len(catalogs[0]['models']),'exterior_reference':marker['historical_view'],'existing_viewer_sha256':h((a/'viewer.json').read_bytes()),'old_viewer_screenshots':6},ensure_ascii=False,indent=2)+'\n')
