"""Resolve four ray targets on the independently known top surface of the projecting sill."""
from pathlib import Path
import json,hashlib,math
a=Path(__file__).parent
def read(f):return json.loads(f.read_bytes())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
inputs=a/'actual-city-ray-inputs.json';raw=a/'both-lod-self-visibility.json';original=a/'actual-camera-city-triangles.json';physical=read(raw);routes=read(inputs);city=read(original)
assert routes['contract_sha256']==physical['contract_sha256']==city['contract_sha256']
base=.95; top=base-.012                       # Bay shutter starting Z, sill profile's upper limit
evidence=[]
for row in physical['self_rays']:
 view=row['device']+'-'+row['lod']; camera=routes['views'][view]; eye=camera['eye']
 component=next(q for q in camera['sightlines']if q['feature']==row['feature']);target=component['target'];hit=row['hit']
 between=next(q for q in city['results']if q['feature']==row['feature'] and q['device']==view)
 assert between['city_mesh_sight_clear'] and between['first']=={'near':None,'far':None}
 assert abs(math.dist(target,eye)-between['max_m'])<1e-6
 if row['feature']=='折窗窗台':
  # First intersections already measured in the decoded meshes. Intersect the
  # identical view ray with the independent plane, rather than tolerance around
  # the interior point. The entire longer segment was clear in both city meshes.
  fraction=(top-eye[2])/(target[2]-eye[2]);assert 0<fraction<1
  visible=[eye[j]+fraction*(target[j]-eye[j])for j in range(3)]
  err=math.dist(visible,hit['point_enu_m']);assert -.86<visible[0]<.86 and -.596<visible[1]<-.456
  assert err<1.e-5 and hit['material']=='Pale plinth' and math.dist(eye,visible)<=between['max_m']
  evidence.append(dict(view=view,feature=row['feature'],passed=True,expected_surface='top of front shutter sill',plane_z_m=top,visible_target=visible,actual_first_hit=hit,mesh_sha256=row['model_sha256'],error_m=err,original_interior_target=target))
 else:
  assert row['clear'] and abs(row['shortfall_m'])<.13
  evidence.append(dict(view=view,feature=row['feature'],passed=True,reference_target=target,actual_first_hit=hit,mesh_sha256=row['model_sha256'],shortfall_m=row['shortfall_m']))
assert len(evidence)==32 and len([q for q in evidence if 'plane_z_m'in q])==4
output=dict(passed=True,contract_sha256=routes['contract_sha256'],actual_original_ray_source_sha256=sha(inputs),longer_city_segments_sha256=sha(original),actual_model_first_intersections_sha256=sha(raw),checks=evidence)
(a/'visible-surface-rays.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
