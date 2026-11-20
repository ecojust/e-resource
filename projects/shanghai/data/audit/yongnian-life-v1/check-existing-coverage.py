"""Compare an actual predecessor scene to the surveyed building footprint."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from shapely.affinity import affine_transform
from shapely.geometry import Point,shape

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project',type=Path,required=True)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--count',type=int,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
read=lambda path:json.loads(path.read_bytes())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
foot=read(args.source)
site=shape(foot['source_outline'])
lon,lat=site.centroid.coords[0]
kx=math.pi/180*6371008.8*math.cos(math.radians(lat))
ky=math.pi/180*6371008.8
def local(geom):return affine_transform(geom,[kx,0,0,ky,-lon*kx,-lat*ky])
site=local(site)
catalog=args.project/'data/candidate-city-integrations.json'
base=args.project/'data/landmarks.json'
before=read(catalog)
visible=read(base)+before['models']
assert len(visible)==args.count==before['resulting_city_count']
checks=[]
for row in visible:
    if row.get('replacement_geometry'):
        envelope=local(shape(row['replacement_geometry']))
        method='registered replacement polygon'
    else:
        center=local(Point(row['lng'],row['lat']))
        bounds=row.get('bounds_glb')
        if bounds:
            radius=math.hypot(*[max(abs(bounds['min'][i]),abs(bounds['max'][i])) for i in [0,2]])*row.get('scale',1)
            envelope=center.buffer(radius)
            method='scale-adjusted enclosing disk, safe for any yaw'
        else:
            envelope=center
            method='registered anchor'
    checks.append({'id':row['id'],'name':row['name'],'geometry':method,
                   'gap_m':site.distance(envelope),'overlap_m2':site.intersection(envelope).area})
checks.sort(key=lambda row:row['gap_m'])
out={'expected_catalog_count':args.count,'catalog_sha256':sha(catalog),'base_sha256':sha(base),
     'source_sha256':sha(args.source),'minimum_separations':checks[:10],
     'all_intersections':[r for r in checks if r['overlap_m2']>0]}
args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
assert not out['all_intersections'],out['all_intersections']
