from pathlib import Path
from hashlib import sha256
from urllib.request import urlopen,Request
from PIL import Image
from io import BytesIO
import json,time
u=Path('/dev/shm/russell283-live');p=Path('/workspace/e-resource/projects/shanghai');ident='huangpu-russell-company-fuzhou-three-bay-front'
s=p/'source/precise'/ident;a=p/'data/audit/russell-company-fuzhou-three-bay-front-v1/preflight'; ref=json.loads((s/'reference-review.json').read_bytes());station=json.loads((a/'north-detail-sources.json').read_bytes())
def get(r,image=True,save=False):
 url=r.get('raw_url',r['url'])
 for attempt in range(3):
  try:
   with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (Shanghai architectural model documentation)'}),timeout=25)as h:
    body=h.read();assert 200==h.status
   break
  except OSError:
   if attempt==2:raise
   time.sleep(.5)
 sig=sha256(body).hexdigest();assert sig==r['sha256'],(url,sig,r['sha256'])
 if r.get('bytes'):assert len(body)==r['bytes']
 record=dict(url=url,sha256=sig,bytes=len(body))
 if image:
  with Image.open(BytesIO(body))as im:
   record['dimensions']=list(im.size)
   if save:
    im.draft('RGB',(700,520));im.thumbnail((700,520));im.convert('RGB').save(u/'work/2015-review.jpg',quality=88)
   else:im.verify()
 return record
out=u/'verified-audit/photo-recheck';res=dict(catalog=ref['listing'],survey_sha256=sha256((a/'three-bay-survey.json').read_bytes()).hexdigest(),independent_2015_fit_sha256=sha256((a/'independent-photo-height.json').read_bytes()).hexdigest(),photo=get(ref['dated_original'],save=True),stations=[])
for k,st in station.items():
 r=next(row for row in ref['public_2021']['poses'] if row['id']==st['id'])
 res['stations'].append(dict(id=st['id'],heading=r['heading'],geo=r['geo'],images=[get(t)for t in st['refs']]))
 print(k,len(st['refs']),flush=True)
(out/'photos.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
