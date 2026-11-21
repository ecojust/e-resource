"""Read every building in the frozen fallback tile and measure its distance to the lot."""
import argparse
import hashlib
import json
from pathlib import Path

import mapbox_vector_tile
import numpy as np
from shapely import transform
from shapely.geometry import Point, shape, mapping

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('pbf',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
data=args.pbf.read_bytes()
signature=hashlib.sha256(data).hexdigest()
assert signature=='ef9df460f908f294d516f8753ac4366603662b592d4fb5bd2c214df51e6cf5e0'
layer=mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})['building']
extent=layer['extent']
def lonlat(p):
    col, row=p.T/extent
    return np.column_stack(((13718+col)/16384*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(6695+row)/16384))))))
register=Path(__file__).resolve().parents[3]/'source/precise/jingan-brookside-apartments/footprint-review.json'
owner=shape(json.loads(register.read_bytes())['source_outline']);near=owner.buffer(.0006)
parts=[];closest=[]
for f in layer['features']:
    geom=transform(shape(f['geometry']),lonlat)
    dist=owner.distance(geom)
    closest.append({'id':f['id'],'distance_degrees':dist})
    if not geom.is_empty:
        parts.append({'id':f['id'],'properties':f['properties'],'geometry':mapping(geom)})
args.output.write_text(json.dumps({'sha256':signature,'extent':extent,'total_tile_buildings':len(closest),'nearest_features':sorted(closest,key=lambda r:r['distance_degrees'])[:4],'nearby_features':parts},separators=(',',':'))+'\n')
