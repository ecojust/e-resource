"""Measure sightlines for the entrance inscription, striped stone jambs and rounded balconies from the final specialist cameras."""
import argparse, json, math, gzip, hashlib, runpy
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import LineString,Point,shape
audit=Path(__file__).resolve().parent.parent
p=audit.parents[2]
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--project', type=Path, default=p, help='Project root containing the signed city assets')
root=cli.parse_args().project
load=lambda v:json.loads(v.read_bytes())
digest=lambda v:hashlib.sha256(v.read_bytes()).hexdigest()
con=load(audit/'final-placement-contract.json');lng,lat=con['lng'],con['lat'];theta=math.radians(con['heading'])
rad=math.pi/180;merc=math.asinh(math.tan(lat*rad));k=6371008.8*math.cos(lat*rad)
rot=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
bounds=lambda coords: np.column_stack([(coords[:,0]-lng)*rad*k,(np.arcsinh(np.tan(coords[:,1]*rad))-merc)*k]) @ rot.T
macro=con['owner']['macro_id'];ft=root/f'assets/city-detail/macros/{macro}/feature-table.json.gz'
signed=load(audit/'city-31192/public-runtime-inputs.json')[1]
assert digest(ft)==next(x['sha256'] for x in signed['inputs'] if x['file']==ft.relative_to(root).as_posix())
scene=[];anchor=Point(lng,lat)
for row in json.loads(gzip.decompress(ft.read_bytes()))['features']:
 poly=shape(row['geometry'])
 if poly.distance(anchor)>.0022 or row['localId']==con['owner']['feature_local_id']:continue
 scene.append((row['localId'],shapely.transform(poly,bounds),row['height'] or 0))
asset=root/f"assets/models/candidates/{con['id']}/{con['id']}-raw.glb"
assert digest(asset)==con['model_geometry_sha256']['raw']
mesh=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](asset)
targets=load(audit/'surface-checks.json')['variants']['raw']['probes']
near=[(item['label'],np.array(item['hit']['point_enu_m'])) for item in targets if item.get('hit')]
def measure(center,elevation,pitch,bearingOffset,zoom,criteria):
 w,h=900,680;focal=h/(2*math.tan(math.radians(36.87)/2));distance=focal*2*math.pi*k/(512*2**zoom)
 a,t=bearingOffset*rad,pitch*rad;direction=np.array([math.sin(a),math.cos(a)])
 eye=np.r_[np.array(center)-direction*distance*math.sin(t),elevation+distance*math.cos(t)];rows=[]
 for label,target in near:
  if not any(x in label for x in criteria):continue
  line=LineString([eye[:2],target[:2]]);blockers=[]
  for owner,foot,z in scene:
   if line.intersects(foot):
    pts=shapely.get_coordinates(line.intersection(foot))
    zs=[eye[2]+(target[2]-eye[2])*line.project(Point(pt),normalized=True) for pt in pts]
    if min(zs,default=math.inf)<z-.10:blockers.append(owner)
  dist=np.linalg.norm(target-eye);hit=mesh.ray(eye,target-eye,dist+.10)
  delta=target-np.r_[center,elevation];forward=delta[:2]@direction;depth=distance+forward*math.sin(t)-delta[2]*math.cos(t);screen=[w/2+(delta[0]*math.cos(a)-delta[1]*math.sin(a))*focal/depth,h/2-(forward*math.cos(t)+delta[2]*math.sin(t))*focal/depth]
  err=round(dist-hit['distance_m'],3) if hit else None
  rows.append(dict(feature=label,pixel=[round(v,1) for v in screen],nearer_owners=blockers,own_first_hit_material=hit['material'] if hit else None,own_first_hit_shortfall_m=err,clear=bool(not blockers and err is not None and abs(err)<.30 and 0<screen[0]<w and 0<screen[1]<h)))
 return {'center':center,'elevation':elevation,'pitch':pitch,'bearing_offset':bearingOffset,'zoom':zoom,'clear':sum(i['clear'] for i in rows),'witnesses':rows}
entrance=measure([-.18,-.88],3.46,42,-13,21.30,['striped jamb','entrance inscription','green address plate','recessed door'])
balconies=measure([10.62,-.12],16.7,48,-16,20.23,['long balcony parapet','rounded parapet end','four stepped tiers','centre balcony','glazed room behind balcony'])
result=dict(feature_table_sha256=digest(ft),original_mesh_sha256=digest(asset),author_witness_sha256=digest(audit/'surface-checks.json'),approximation='First hits in the authored triangles, with nearby city blocks represented by their signed base polygons and heights. Actual visibility and screen labels are checked in the browser separately.',entrance_and_name=entrance,balconies_and_setbacks=balconies)
(audit/'city-31192'/'special-camera-sightlines.json').write_text(json.dumps(result,indent=2)+'\n')
for view in (entrance,balconies):print(view['clear'],len(view['witnesses']),{i['feature'] for i in view['witnesses'] if i['clear']})

for view, required in [(entrance, {'striped jamb dark band','striped jamb light band','green address plate','entrance inscription 常','entrance inscription 德','entrance inscription 公','entrance inscription 寓'}),(balconies,{'long balcony parapet','rounded parapet end','four stepped tiers at the parapet','centre balcony'})]:
    assert required <= {r['feature'] for r in view['witnesses'] if r['clear']}
