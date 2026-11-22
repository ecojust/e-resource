"""Measure the registered cut against every original footprint intersecting this complete building tile."""
from hashlib import sha256
from pathlib import Path
from argparse import ArgumentParser
import json
import math
import mapbox_vector_tile
import numpy as np
import shapely
from shapely.geometry import shape

cli=ArgumentParser(description=__doc__)
for key in ('tile','contract','out'):
    cli.add_argument('--'+key,required=True,type=Path)
args=cli.parse_args()
data=args.tile.read_bytes()
digest=sha256(data).hexdigest()
assert digest=='21ae0cc5b91bfb8c85d320d3d0295804e5af8d04fcca02fb316f3e5ef80449e2'
doc=json.loads(args.contract.read_bytes())
assert doc['id']=='jingan-daxin-tobacco-northeast-tower'
layer=mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})['building']
scale=float(layer['extent'])
R=6371008.8
k=R*math.cos(math.radians(doc['lat']))
x0=math.radians(doc['lng'])*k
y0=math.asinh(math.tan(math.radians(doc['lat'])))*k
def local(coords):
    return np.column_stack((np.radians(coords[:,0])*k-x0,np.arcsinh(np.tan(np.radians(coords[:,1])))*k-y0))
def tile_local(coords):
    nx=(13719+coords[:,0]/scale)/2**14
    ny=(6694+coords[:,1]/scale)/2**14
    return np.column_stack(((nx*2-1)*math.pi*k-x0,(1-2*ny)*math.pi*k-y0))
mask=shapely.transform(shape(doc['replacement_geometry']),local)
records=[]
for row in layer['features']:
    transformed=shapely.transform(shape(row['geometry']),tile_local)
    pieces=list(shapely.get_parts(transformed))
    area=[]
    for idx,part in enumerate(pieces):
        if part.intersects(mask):
            overlap=part.intersection(mask).area
            if overlap>1.e-7:area.append({'component':idx,'overlap_m2':overlap})
    records.append({'id':row['id'],'parts':len(pieces),'intersections':area})
changed=[(r['id'],a['component'])for r in records for a in r['intersections']]
assert changed==[(64634100,247)] and len(records)==26,changed
out={'passed':True,'id':doc['id'],'tile_sha256':digest,'contract_sha256':sha256(args.contract.read_bytes()).hexdigest(),
     'all_original_features':len(records),'total_original_parts':sum(v['parts']for v in records),
     'unaffected_features':len(records)-1,'records':records}
args.out.write_text(json.dumps(out,indent=2)+'\n')
print(out['all_original_features'],out['total_original_parts'],changed)
