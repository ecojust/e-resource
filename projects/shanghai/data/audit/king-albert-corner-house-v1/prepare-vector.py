"""Decode the complete, signed OpenMapTiles aggregate containing the southwest King Albert house and adjacent buildings."""
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
assert digest=='36448c327185ab13a8d07e723bda4d00dec0c1d36c6831a4c6aa50de13a07893'
buildings=mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})['building']
extent=buildings['extent']
def wgs(p):
    lon=(p[:,0]/extent+13719)/2**14*360-180
    lat=np.degrees(np.arctan(np.sinh(np.pi*(1-2*(p[:,1]/extent+6695)/2**14))))
    return np.column_stack((lon,lat))
feature,=[f for f in buildings['features'] if f['id']==1658263140]
geometry=shapely.transform(shape(feature['geometry']),wgs)
assert len(geometry.geoms)==17
feature['geometry']=mapping(geometry)
j={'url':'https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13719/6695.pbf','x':13719,'y':6695,'z':14,
   'bytes':len(data),'sha256':digest,'features':[feature]}
review=json.loads((Path(__file__).resolve().parents[3]/'source/precise/huangpu-king-albert-corner-house/footprint-review.json').read_bytes())
neighbor_polys=[shape(rec['geometry'])for rec in review['named_neighbors'].values()]
center_bounds=shape(review['source_outline']).buffer(.00015)
selected=[]
for feature in buildings['features']:
    if feature['id']==1658263140:continue
    geometry=shapely.transform(shape(feature['geometry']),wgs)
    if geometry.intersects(center_bounds) or any(geometry.intersects(neighbor)for neighbor in neighbor_polys):
        selected.append({**feature,'geometry':mapping(geometry)})
j['nearby_additional_features']=selected
j['total_tile_buildings']=len(buildings['features'])
j['method']='All distinct features meeting the source owner or its 0.00015-degree envelope, or the outlines of the individually named neighboring apartment buildings.'
args.output.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':'))+'\n')
