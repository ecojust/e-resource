"""Fetch the pinned OpenFreeMap tile and export its actual merged feature for check-vector.mjs.

Run with Python, NumPy, Shapely 2 and mapbox-vector-tile 2.2.0. Only the
source coordinates travel through scratch space; the evidence records hashes.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

import mapbox_vector_tile
import numpy as np
import shapely
from shapely.geometry import mapping,shape

ROOT=Path(__file__).resolve().parents[3]
source=json.loads((ROOT/'source/precise/jingan-majestic-theatre/footprint-review.json').read_bytes())['fallback_vector']
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--tile',type=Path)
args=parser.parse_args()
tile=args.tile.read_bytes() if args.tile else urlopen(source['url'],timeout=40).read()
assert len(tile)==source['bytes'] and hashlib.sha256(tile).hexdigest()==source['sha256']
d=mapbox_vector_tile.decode(tile,default_options={'y_coord_down':True})['building']
z,x,y=source['zxy']
def wgs(p):
    xx=p[:,0]/d['extent']+x
    yy=p[:,1]/d['extent']+y
    return np.column_stack((xx/2**z*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*yy/2**z))))))
feature=next(f for f in d['features'] if f['id']==source['feature_id'])
assert feature['properties']==source['properties']
feature['geometry']=mapping(shapely.transform(shape(feature['geometry']),wgs))
args.out.write_text(json.dumps({'type':'FeatureCollection','features':[feature],'tile_sha256':source['sha256']},separators=(',',':'))+'\n')
