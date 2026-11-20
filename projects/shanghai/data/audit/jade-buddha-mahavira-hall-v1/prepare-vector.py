"""Decode the complete, signed OpenMapTiles aggregate containing the relocated hall and its neighboring temple buildings."""
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
assert digest=='01127bf6cc584c8be8a8bd880b6178e8f8e52da9d7855a117fed0c8ec3a877ac'
buildings=mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})['building']
extent=buildings['extent']
def wgs(p):
    lon=(p[:,0]/extent+13718)/2**14*360-180
    lat=np.degrees(np.arctan(np.sinh(np.pi*(1-2*(p[:,1]/extent+6693)/2**14))))
    return np.column_stack((lon,lat))
feature,=[f for f in buildings['features'] if f['id']==117811070]
geometry=shapely.transform(shape(feature['geometry']),wgs)
assert len(geometry.geoms)==755
feature['geometry']=mapping(geometry)
j={'url':'https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13718/6693.pbf','x':13718,'y':6693,'z':14,
   'bytes':len(data),'sha256':digest,'features':[feature]}
args.output.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':'))+'\n')
