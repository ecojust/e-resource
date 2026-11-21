"""Resolve and verify the seven retained city parcels sampled around the photographed south front."""
from pathlib import Path
from urllib.request import urlopen
import gzip,hashlib,json
from shapely.geometry import shape,Point
p=Path('/workspace/e-resource/projects/shanghai')
a=p/'data/audit/yongfu-road-151-v1'
dest=a/'city-24170';dest.mkdir(exist_ok=True)
read=lambda f:json.loads(f.read_bytes())
review=read(p/'source/precise/xuhui-yongfu-road-151-south-front/footprint-review.json')
t=next(v for v in review['frozen_bindings'] if v['repository_path'].endswith('/feature-table.json.gz'))
url='http://127.0.0.1:24170/'+t['repository_path'].removeprefix('projects/shanghai/')
with urlopen(url,timeout=45)as r:assert r.status==200;raw=r.read()
assert len(raw)==t['bytes'] and hashlib.sha256(raw).hexdigest()==t['sha256']
table=json.loads(gzip.decompress(raw));case=read(a/'map-case.json');points=read(a/'placement-geometry.json')['neighbor_points_wgs84']
assert points==case['neighborGround']
rows=[]
for key,point in points.items():
 k=int(key);feature=next(o for o in table['features']if o['localId']==k)
 assert feature['key']==table['keys'][k]and shape(feature['geometry']).covers(Point(*point))
 rows.append({'local_id':k,'key':feature['key'],'height':feature['height'],'point':point})
assert len(rows)==7
(dest/'neighbor-owner-keys.json').write_text(json.dumps({'url':url,'frozen_table':t,'ground':'building','neighbors':rows},indent=2)+'\n')
