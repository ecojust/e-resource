"""Decode the complete, signed OpenMapTiles aggregate containing the school and theatre."""
import argparse
import hashlib
import json
from pathlib import Path

import mapbox_vector_tile
import numpy as np
import shapely
from shapely.geometry import mapping, shape

cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('pbf',type=Path)
cli.add_argument('output',type=Path)
args=cli.parse_args()
data=args.pbf.read_bytes()
digest=hashlib.sha256(data).hexdigest()
assert digest=='ef9df460f908f294d516f8753ac4366603662b592d4fb5bd2c214df51e6cf5e0'
buildings=mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})['building']
extent=buildings['extent']
def wgs(p):
    lon=(p[:,0]/extent+13718)/2**14*360-180
    lat=np.degrees(np.arctan(np.sinh(np.pi*(1-2*(p[:,1]/extent+6695)/2**14))))
    return np.column_stack((lon,lat))
feature,=[f for f in buildings['features'] if f['id']==147898520]
geometry=shapely.transform(shape(feature['geometry']),wgs)
assert len(geometry.geoms)==2426
feature['geometry']=mapping(geometry)
j={'url':'https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13718/6695.pbf','x':13718,'y':6695,'z':14,
   'bytes':len(data),'sha256':digest,'features':[feature]}
args.output.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':'))+'\n')
