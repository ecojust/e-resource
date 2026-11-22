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
assert signature=='4fb028ba24738a5b5d34cd7c65859a7370fa48036e588f75c165167f8351406b'
layer=mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})['building']
extent=layer['extent']
def lonlat(p):
    col, row=p.T/extent
    return np.column_stack(((13721+col)/16384*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(6693+row)/16384))))))
register=Path(__file__).resolve().parents[3]/'source/precise/hongkou-unrra-gray-building-north-front/footprint-review.json'
owner=shape(json.loads(register.read_bytes())['original_geometry_wgs84']);near=owner.buffer(.0006)
parts=[];closest=[]
for f in layer['features']:
    geom=transform(shape(f['geometry']),lonlat)
    dist=owner.distance(geom)
    closest.append({'id':f['id'],'distance_degrees':dist})
    polygons=geom.geoms if geom.geom_type=='MultiPolygon' else [geom]
    for index,part in enumerate(polygons):
        if part.intersects(near):
            parts.append({'id':f['id'],'component':index,'properties':f['properties'],'geometry':mapping(part)})
args.output.write_text(json.dumps({'sha256':signature,'extent':extent,'total_tile_buildings':len(closest),'nearest_features':sorted(closest,key=lambda r:r['distance_degrees'])[:4],'nearby_features':parts},separators=(',',':'))+'\n')
