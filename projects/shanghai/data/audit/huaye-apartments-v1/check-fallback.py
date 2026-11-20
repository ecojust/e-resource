"""Measure the nearest real aggregated OpenFreeMap building in the frozen z14 fallback tile."""
from pathlib import Path
import argparse,hashlib,json,math
import mapbox_vector_tile
import numpy as np
import shapely
from shapely.geometry import shape
from urllib.request import urlopen

audit=Path(__file__).resolve().parent
tile='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13719/6694.pbf'
expected='21ae0cc5b91bfb8c85d320d3d0295804e5af8d04fcca02fb316f3e5ef80449e2'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--tile',type=Path)
parser.add_argument('--contract',type=Path,default=audit/'final-placement-contract.json')
parser.add_argument('--out',type=Path,default=audit/'fallback-vector.json')
a=parser.parse_args()
blob=a.tile.read_bytes() if a.tile else urlopen(tile,timeout=40).read()
assert hashlib.sha256(blob).hexdigest()==expected
layer=mapbox_vector_tile.decode(blob,default_options={'y_coord_down':True})['building']
m=json.loads(a.contract.read_bytes());k=6371008.8*math.cos(math.radians(m['lat']))
phi=math.asinh(math.tan(math.radians(m['lat'])))
def transform(p):
    lon=(p[:,0]/layer['extent']+13719)/16384*360-180
    loglat=np.pi*(1-2*(p[:,1]/layer['extent']+6694)/16384)
    return np.column_stack((np.radians(lon-m['lng'])*k,(loglat-phi)*k))
def en(p):
    return np.column_stack((np.radians(p[:,0]-m['lng'])*k,(np.arcsinh(np.tan(np.radians(p[:,1])))-phi)*k))
cut=shapely.transform(shape(m['replacement_geometry']),en)
near=[]
for feature in layer['features']:
    original=shapely.transform(shape(feature['geometry']),transform)
    near.append((original.distance(cut),feature['id']))
near.sort();assert near[0][0]>1.,near[:3]
a.out.write_text(json.dumps({'id':m['id'],'source':'OpenFreeMap building layer, height-aggregated OSM vector fallback',
    'url':tile,'tile_bytes':len(blob),'tile_sha256':expected,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'contract_sha256':hashlib.sha256(a.contract.read_bytes()).hexdigest(),'all_features_checked':len(near),'intersecting_features':0,
    'closest_feature_id':near[0][1],'minimum_clearance_m':near[0][0]},indent=2)+'\n')
