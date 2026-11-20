"""Compare the moved hall against every previously registered map position and extent."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Point, shape

audit=Path(__file__).resolve().parent
project=audit.parents[2]
ident='putuo-jade-buddha-mahavira-hall'
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('previous',type=Path)
cli.add_argument('out',type=Path)
args=cli.parse_args()
previous=args.previous
source=json.loads((project/'source/precise'/ident/'footprint-review.json').read_bytes())
catalog='data/candidate-city-integrations.json'
legacy='data/landmarks.json'
catalog_bytes=(previous/catalog).read_bytes()
catalog_digest=hashlib.sha256(catalog_bytes).hexdigest()
rows=json.loads(catalog_bytes)['models']+json.loads((previous/legacy).read_bytes())
assert len({r['id']for r in rows})==len(rows)==json.loads(catalog_bytes)['resulting_city_count']
x,y=source['author_frame']['anchor'].values()
k=6371008.8*math.cos(math.radians(y));north=math.asinh(math.tan(math.radians(y)))
def local(pts):
    return np.column_stack((np.radians(pts[:,0]-x)*k,(np.arcsinh(np.tan(np.radians(pts[:,1])))-north)*k))
if (audit/'final-placement-contract.json').is_file():
    frame=json.loads((audit/'final-placement-contract.json').read_bytes())['replacement_geometry']
else:
    frame=json.loads((project/'source/precise'/ident/'roof-registration.json').read_bytes())['city_owner']['source_outline_wgs84']
site=shapely.transform(shape(frame),local)
out=[]
for r in rows:
    ids=set(r.get('source_feature_ids',{}).get('building',[]))
    assert source['owner']['source_key'].split(':')[1] not in ids
    center=Point(local(np.array([[r['lng'],r['lat']]]))[0])
    if r.get('replacement_geometry'):
        poly=shapely.transform(shape(r['replacement_geometry']),local); method='registered replacement polygon'
    elif r.get('bounds_glb'):
        bounds=r['bounds_glb'];xmax=max(abs(bounds[part][0])for part in ['min','max']);zmax=max(abs(bounds[part][2])for part in ['min','max'])
        radius=math.hypot(xmax,zmax)*r.get('scale',1)
        poly=center.buffer(radius/math.cos(math.pi/128),quad_segs=32)
        method='enclosing horizontal disk for every rotation'
    else:
        poly=center;method='registered location, bounds unavailable'
    out.append({'id':r['id'],'name':r['name'],'scope':method,'gap_m':poly.distance(site),'intersection_m2':poly.intersection(site).area})
out.sort(key=lambda item:item['gap_m'])
assert out[0]['gap_m']>25 and all(q['intersection_m2']==0 for q in out)
args.out.write_text(json.dumps({'id':ident,'previous_count':len(rows),'prior_catalog_sha256':catalog_digest,
    'legacy_sha256':hashlib.sha256((previous/legacy).read_bytes()).hexdigest(),'method_counts':{m:sum(o['scope']==m for o in out)for m in sorted(set(o['scope']for o in out))},'nearest':out[:15],
    'zero_intersection_count':len(out),'duplicate_source_owner_count':0},ensure_ascii=False,indent=2)+'\n')
print(out[:2])
