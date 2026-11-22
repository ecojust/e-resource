"""Decode the real vector fallback at the 522 Jiaozhou Road gate."""
import argparse,json,hashlib
from pathlib import Path
from urllib.request import urlopen
import numpy as np,mapbox_vector_tile,shapely as geo
from shapely.geometry import shape,mapping
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tile',type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
url='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13718/6694.pbf'
raw=a.tile.read_bytes() if a.tile else urlopen(url,timeout=45).read()
digest=hashlib.sha256(raw).hexdigest();assert digest=='1fdad607f7b21b88e0ad7de7768cd646aba6c88aca481544ba3409575d5e2bb2'
group=mapbox_vector_tile.decode(raw,default_options={'y_coord_down':True})['building']
def wgs(pts):
    x=13718+pts[:,0]/group['extent'];y=6694+pts[:,1]/group['extent']
    return np.column_stack([x/2**14*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*y/2**14))))])
data=[]
for f in group['features']:
    g=geo.transform(shape(f['geometry']),wgs)
    data.append(dict(f,geometry=mapping(g)))
assert sum(len(geo.get_parts(shape(f['geometry'])))for f in data)==1335
a.out.write_text(json.dumps(dict(url=url,sha256=digest,bytes=len(raw),type='FeatureCollection',features=data))+'\n')
