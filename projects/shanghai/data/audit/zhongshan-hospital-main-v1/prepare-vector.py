"""Decode the actual OpenMapTiles building(s) at Building 3 and its neighbors."""
from argparse import ArgumentParser
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

import mapbox_vector_tile
import numpy as np
import shapely
from shapely.geometry import mapping, shape

parser=ArgumentParser(description=__doc__)
parser.add_argument('--tile',type=Path)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
url='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13719/6696.pbf'
raw=args.tile.read_bytes()if args.tile else urlopen(url,timeout=30).read()
tile_hash=hashlib.sha256(raw).hexdigest()
assert tile_hash=='10bfe55192f209dfc54252624ab909853c15f92ca51f0004c6c1d1743a9aaa6e'
layer=mapbox_vector_tile.decode(raw,default_options={'y_coord_down':True})['building']
def wgs(points):
    x=(points[:,0]/layer['extent']+13719)/2**14
    y=(points[:,1]/layer['extent']+6696)/2**14
    return np.column_stack((x*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*y))))))
a=Path(__file__).resolve().parent
review=json.loads((a.parents[2]/'source/precise/xuhui-zhongshan-hospital-main-building/footprint-review.json').read_bytes())
areas=[shape(review['source_outline']),*[shape(r['geometry'])for r in review['retained_neighbors']]]
selected=[]
for feature in layer['features']:
    geometry=shapely.transform(shape(feature['geometry']),wgs)
    if any(geometry.intersection(area).area>1e-13 for area in areas):
        selected.append({**feature,'geometry':mapping(geometry)})
args.out.write_text(json.dumps({'type':'FeatureCollection','features':selected,'url':url,'sha256':tile_hash,'bytes':len(raw)})+'\n')
print('vector IDs',[f['id']for f in selected])
