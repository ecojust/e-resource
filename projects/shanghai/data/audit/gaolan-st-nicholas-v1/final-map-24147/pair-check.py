from pathlib import Path
from urllib.request import urlopen
import json,hashlib
w=Path(__file__).parent;P=Path('/workspace/e-resource/projects/shanghai');A=P/'data/audit/gaolan-st-nicholas-v1';C='data/candidate-city-integrations.json';I='huangpu-gaolan-st-nicholas-church'
record=json.loads((A/'viewer.json').read_bytes());source=json.loads((P/'source/precise'/I/'footprint-review.json').read_bytes());rows={};reports={}
def sha(b):return hashlib.sha256(b).hexdigest()
for n in [146,147]:
 d=Path('/tmp/shanghai-east-medical-focus/scenes');sigp=d/f'{n}-production.json';sig=json.loads(sigp.read_bytes())['files'];meta=json.loads((d/f'{n}-comparison.json').read_bytes());urls={v['path']:v['actual_url']for v in meta['files']};base=f'http://127.0.0.1:{24000+n}/'
 keys=[C,'src/app.js','src/map-scene.js','src/building-beacons.js','src/building-beacon-groups.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','index.html','landmarks.html'];expected={k:sig[k]for k in keys}
 for v in source['frozen_bindings']:expected[v['repository_path'].removeprefix('projects/shanghai/')]=v['sha256']
 if n==147:
  expected.update(record['files']);manifest='assets/models/candidates/'+I+'/manifest.json';expected[manifest]=record['manifestSHA256']
  for item in record['downloads'].values():expected['assets/models/candidates/'+I+'/'+item['file']]=item['sha256']
  for k in ['data/audit/gaolan-st-nicholas-v1/final-placement-contract.json','tools/check-candidate-viewer.cjs']:
   expected[k]=sig[k] if k in sig else sha((P/k).read_bytes())
 receipts={}
 for k,h in expected.items():
  url=base+urls.get(k,k)
  with urlopen(url,timeout=55)as response:
   data=response.read();assert response.status==200 and sha(data)==h,(n,k,sha(data),h)
  receipts[k]={'sha256':h,'bytes':len(data),'url':url}
  if k==C:rows[n]=json.loads(data)
 reports[str(n)]={'count':rows[n]['resulting_city_count'],'catalog':sig[C],'signature_sha256':sha(sigp.read_bytes()),'signed_inputs':len(sig),'requests':receipts}
assert rows[146]['models']==rows[147]['models'][:-1] and rows[147]['models'][-1]['id']==I
assert all(sha((A/v['filename']).read_bytes())==v['sha256']for v in record['views'])and len(record['downloads'])==4 and record['passed']and not record['pageErrors'];assert sha((P/'tools/check-candidate-viewer.cjs').read_bytes())==record['scriptSHA256']
z={'model':I,'catalogs_unchanged_except_new_row':True,'old_city_count':183,'new_city_count':184,'retained_candidate_rows':len(rows[146]['models']),'stages':reports,'same_standalone_viewer_as_author_check':{'previous_real_browser_origin':record['base'],'verified_route':record['route'],'retained_image_count':len(record['views']),'real_saved_downloads':record['downloads'],'confirmed_html_js_manifest_all_four_asset_digests':True},'checked':sum(len(v['requests'])for v in reports.values())}
(w/'pair-and-standalone-http.json').write_text(json.dumps(z,indent=2)+'\n');print(z['checked'],z['retained_candidate_rows'])
