"""Bind the five nearest real street footprints to both signed city-service responses."""
import gzip,json,math,sys,urllib.request
from pathlib import Path
from hashlib import sha256
from shapely.geometry import Point,shape
from shapely import transform
import numpy as np
work=Path(__file__).parent
ident='14-13718-6695'
catalog='data/precise-buildings-v6.json';key='assets/city-detail/macros/'+ident+'/feature-table.json.gz'
out={};feature_ids=None
for n in (182,183):
 base=f'http://127.0.0.1:{31000+n}/'
 def fetch(path):
  with urllib.request.urlopen(base+path,timeout=45)as r:assert r.status==200;return r.read()
 data=fetch(catalog);rd=json.loads(data)
 macro,=[r for r in rd['macros']if r['id']==ident]
 actual=fetch(key);assert sha256(actual).hexdigest()==macro['baseline_feature_table_sha256']
 rows=json.loads(gzip.decompress(actual))['features'];center=Point(0,0);meter=np.array([111195*math.cos(math.radians(31.216)),111195])
 def dist(r):return transform(shape(r['geometry']),lambda p:(p-[121.424,31.216])*meter).distance(center)
 nearby=sorted([(dist(r),r)for r in rows if r.get('geometry')],key=lambda v:v[0])[:6]
 assert max(m for m,_ in nearby)<80
 ids=[r['localId']for _,r in nearby]
 assert feature_ids is None or ids==feature_ids
 feature_ids=ids
 out[n]=dict(count=len(rows),catalog_sha256=sha256(data).hexdigest(),feature_table_sha256=sha256(actual).hexdigest(),features=[{'id':r['localId'],'distance_m':round(dist,3),'source_key':r['key']}for dist,r in nearby])
assert len(set(out[n]['feature_table_sha256']for n in out))==1
(work/'public-neighborhood.json').write_text(json.dumps(dict(id=ident,registry=catalog,table=key,stages=out),indent=2)+'\n')
print(feature_ids,flush=True)
