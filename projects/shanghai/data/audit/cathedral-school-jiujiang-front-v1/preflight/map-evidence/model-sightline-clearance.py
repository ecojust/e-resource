"""Test the signed bounds of previous city models and actual full/LOD surfaces on two screens."""
import hashlib,json,math,runpy,sys
from pathlib import Path
from urllib.request import urlopen
import numpy as np,shapely
from shapely.geometry import Polygon, LineString
w=Path(__file__).resolve().parent;p=Path('/workspace/e-resource/projects/shanghai');stage=int(sys.argv[1]) if len(sys.argv)>1 else 259
read=lambda f:json.loads(f.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();place=read(w/'final-placement-contract.json');cam=read(w/'map-camera-proof.json')['winner'];pre=read(Path('/tmp/shanghai-yongjia-porch/scenes')/f'{stage}-comparison.json');url=f'http://127.0.0.1:{31000+stage}/data/candidate-city-integrations.json'
with urlopen(url,timeout=30)as r:raw=r.read();assert r.status==200 and sha(raw)==pre['catalog_sha256']==r.headers['X-Audit-SHA256']
models=json.loads(raw)['models'];wgs=lambda a:math.asinh(math.tan(math.radians(a)));lng,lat=place['lng'],place['lat'];earth=6371008.8;earthk=earth*math.cos(math.radians(lat));h=math.radians(place['heading']);c,s=math.cos(h),math.sin(h);quads=[];ids=[];absent=[]
for m in models:
 if m['id']==place['id']:continue
 bounds=m.get('bounds_glb')
 if not bounds:assert not m.get('model');absent.append(m['id']);continue
 lo,hi=bounds['min'],bounds['max'];dlon,mlat=m['lng']-lng,m['lat'];east=math.radians(dlon)*earthk;north=(wgs(mlat)-wgs(lat))*earthk;scale=m.get('scale',1)*math.cos(math.radians(lat))/math.cos(math.radians(mlat));a=math.radians(m['heading']);cx,sx=math.cos(a),math.sin(a);pts=[]
 for xx,zz in [(lo[0],lo[2]),(hi[0],lo[2]),(hi[0],hi[2]),(lo[0],hi[2])]:
  e=east+scale*(xx*cx-zz*sx);n=north+scale*(-xx*sx-zz*cx);pts.append((e*c-n*s,e*s+n*c))
 ids.append(m['id']);quads.append(Polygon(pts))
first=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'];models=[(role,first(w.parent/'pilot'/name))for role,name in [('near','decoded-full.glb'),('far','decoded-lod.glb')]];obstacles=[];actual=[];idx=shapely.STRtree(quads)
for view in cam['scores']:
 eye=np.array(view['camera_local'])
 for q in view['probes']:
  target=np.array(q['point_local']);line=LineString((eye[:2],target[:2]));j=int(idx.nearest(line));nearest=ids[j];dist=line.distance(quads[j]);obstacles.append(dict(screen=view['screen'],target=q['feature'],nearest_existing_model=nearest,min_distance_to_any_model_bounds_m=dist));assert dist>.03,(view['screen'],q['feature'],nearest,dist)
  for role,scene in models:
   # Use actual first surfaces from each variant at the same registered feature. LOD profiles use fewer separate casement members.
   hit=scene.ray([target[0],2.5,target[2]],[0,-1,0],5);assert hit
   point=np.asarray(hit['point_enu_m']);delta=point-eye;length=np.linalg.norm(delta);qhit=scene.ray(eye,delta/length,length+.04);assert qhit
   gap=length-qhit['distance_m'];ok=bool(abs(gap)<.055);actual.append(dict(screen=view['screen'],feature=q['feature'],variant=role,actual_target_material=hit['material'],actual_visible_material=qhit['material'],distance_error_m=gap,same_location_visible=ok))
assert sum(v['same_location_visible']for v in actual)>=60
out=dict(passed=True,comparison_sha256=sha(Path('/tmp/shanghai-yongjia-porch/scenes',f'{stage}-comparison.json').read_bytes()),catalog_sha256=sha(raw),visible_model_bounds=len(quads),map_only_historical_markers=absent,clearance=obstacles,variant_surface_checks=actual);(w/f'previous-model-sightlines-{stage}.json').write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n');print(len(quads),min(q['min_distance_to_any_model_bounds_m'] for q in obstacles),sum(v['same_location_visible']for v in actual),'/',len(actual),[v['feature']for v in actual if not v['same_location_visible']]);
