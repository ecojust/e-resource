"""Read-only identity and conservative planar neighbor screen; no city replacement."""
import argparse,gzip,hashlib,json,math
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import shape,MultiPoint,Polygon
from shapely.ops import transform,unary_union

p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parent.parent;project=root.parents[2]
g=json.loads((root/'geometry-input.json').read_text());anchor=g['anchor'];scale=math.cos(math.radians(anchor[1]));radius=6378137.
mx=radius*math.radians(anchor[0]);my=radius*math.log(math.tan(math.pi/4+math.radians(anchor[1])/2))
def local(lon,lat,z=None):
 return ((radius*np.radians(lon)-mx)*scale,(radius*np.log(np.tan(np.pi/4+np.radians(lat)/2))-my)*scale)
table=project/'assets/city-detail/macros'/g['macro']/'feature-table.json.gz'
doc=json.loads(gzip.decompress(table.read_bytes()));owner=next(f for f in doc['features'] if f['localId']==1595)
assert owner==g['feature'];assert hashlib.sha256(table.read_bytes()).hexdigest()==g['source_table_sha256']
source=transform(local,shape(owner['geometry']))
scene=trimesh.load(a.raw,force='scene',process=False);vertices=np.concatenate([m.vertices for m in scene.geometry.values()])
hull=MultiPoint(vertices[:,[0,2]]*np.array([1,-1])).convex_hull
plinth=unary_union([Polygon(tri[:,[0,2]]*np.array([1,-1])) for m in scene.geometry.values() if m.visual.material.name=='stone' for tri in m.triangles if Polygon(tri[:,[0,2]]).area>1e-8])
neighbors=[]
for f in doc['features']:
 if f['localId']==1595:continue
 poly=transform(local,shape(f['geometry']))
 if poly.distance(source)>50:continue
 neighbors.append({'localId':f['localId'],'key':f['key'],'hull_distance_m':hull.distance(poly),'hull_overlap_m2':hull.intersection(poly).area})
neighbors.sort(key=lambda n:(n['hull_distance_m'],n['localId']))
report={'raw_sha256':hashlib.sha256(a.raw.read_bytes()).hexdigest(),'feature_table_sha256':hashlib.sha256(table.read_bytes()).hexdigest(),'source_local_id':1595,'owner_identity_and_polygon_exact':True,'source_area_m2':source.area,'model_plinth_area_m2':plinth.area,'model_plinth_outside_source_m2':plinth.difference(source).area,'model_convex_hull_area_m2':hull.area,'model_hull_outside_owner_m2':hull.difference(source).area,'neighbors_within_50m_in_same_macro':neighbors,'scope':'Conservative convex-hull screen of one frozen macro only. Does not approve positioning, neighboring macros, source replacement, collision, walk spawn, measured ground or complete historic reconstruction. No city files changed.'}
a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='neighbors_within_50m_in_same_macro'}));print('Neighbors:',len(neighbors),'overlaps:',[n for n in neighbors if n['hull_overlap_m2']>1e-6])
