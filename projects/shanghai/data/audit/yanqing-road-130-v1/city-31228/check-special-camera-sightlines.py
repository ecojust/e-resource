"""Check the actual recessed entrance and rounded seventh- and eighth-floor parapets in their separate city camera views."""
import argparse, json, math, gzip, hashlib, runpy
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import LineString,Point,shape
import urllib.request
output=Path(__file__).resolve().parent
p=Path('/workspace/e-resource/projects/shanghai')
audit=p/'data/audit/yanqing-road-130-v1'
root=output/'stage228'
load=lambda v:json.loads(v.read_bytes())
digest=lambda v:hashlib.sha256(v.read_bytes()).hexdigest()
con=load(audit/'final-placement-contract.json');lng,lat=con['lng'],con['lat'];theta=math.radians(con['heading'])
rad=math.pi/180;merc=math.asinh(math.tan(lat*rad));k=6371008.8*math.cos(lat*rad)
rot=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
bounds=lambda coords: np.column_stack([(coords[:,0]-lng)*rad*k,(np.arcsinh(np.tan(coords[:,1]*rad))-merc)*k]) @ rot.T
macro=con['owner']['macro_id'];remote=f'assets/city-detail/macros/{macro}/feature-table.json.gz'
with urllib.request.urlopen('http://127.0.0.1:31228/'+remote,timeout=90) as res:
 assert res.status==200;bt=res.read()
review=load(root/'source/precise/xuhui-yanqing-road-130-residence/footprint-review.json')
record=next(el for el in review['frozen_bindings'] if el['repository_path'].endswith(remote))
assert hashlib.sha256(bt).hexdigest()==record['sha256'] and len(bt)==record['bytes']
scene=[];anchor=Point(lng,lat)
for row in json.loads(gzip.decompress(bt))['features']:
 poly=shape(row['geometry'])
 if poly.distance(anchor)>.0022 or row['localId']==con['owner']['feature_local_id']:continue
 scene.append((row['localId'],shapely.transform(poly,bounds),row['height'] or 0))
asset=root/f"assets/models/candidates/{con['id']}/{con['id']}-raw.glb"
assert digest(asset)==con['model_geometry_sha256']['raw']
mesh=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](asset)
targets=load(audit/'surface-probes.json')['results']['raw']['probes']
near=[(item['label'],np.array(item['first_hit']['point_enu_m'])) for item in targets if item.get('first_hit')]
def measure(center,elevation,pitch,bearingOffset,zoom,criteria):
 w,h=740,580;focal=h/(2*math.tan(math.radians(36.87)/2));distance=focal*2*math.pi*k/(512*2**zoom)
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
portico=measure([-.28,-.86],2.60,76,-5,21.54,('lower hall pane','freestanding shaft','visible lowest western door step','continuous transom'))
crowns=measure([.02,.24],11.43,68,12,21.07,('short pediment pier','crown sash glass','segmental tympanum','pierced balcony spindle'))
result=dict(model=con['id'],macro=macro,feature_table=record,raw_sha256=digest(asset),size=[740,580],portico=portico,crowns=crowns)
(output/'special-camera-sightlines.json').write_text(json.dumps(result,indent=1)+'\n')
for v in (portico,crowns):print(v['clear'],len(v['witnesses']),[r['feature']for r in v['witnesses']if r['clear']])
