"""Decode the real vector aggregate containing both the former Daxin and Rong gardens."""
import argparse,json,hashlib
from pathlib import Path
from urllib.request import urlopen
import numpy as np,mapbox_vector_tile,shapely as geo
from shapely.geometry import shape,mapping
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tile',type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
url='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13719/6694.pbf'
raw=a.tile.read_bytes() if a.tile else urlopen(url,timeout=45).read()
digest=hashlib.sha256(raw).hexdigest();assert digest=='21ae0cc5b91bfb8c85d320d3d0295804e5af8d04fcca02fb316f3e5ef80449e2'
group=mapbox_vector_tile.decode(raw,default_options={'y_coord_down':True})['building']
def wgs(pts):
    x=13719+pts[:,0]/group['extent'];y=6694+pts[:,1]/group['extent']
    return np.column_stack([x/2**14*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*y/2**14))))])
data=[]
for f in group['features']:
    if f['id']!=64634100:continue
    g=geo.transform(shape(f['geometry']),wgs);assert len(geo.get_parts(g))==1813
    data.append(dict(f,geometry=mapping(g)))
assert len(data)==1
a.out.write_text(json.dumps(dict(url=url,sha256=digest,bytes=len(raw),type='FeatureCollection',features=data))+'\n')
