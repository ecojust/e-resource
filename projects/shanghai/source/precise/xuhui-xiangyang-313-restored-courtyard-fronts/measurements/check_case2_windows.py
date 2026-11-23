"""Test Photo 2 pixels against the nearest triangle in the real local or placed GLB."""
from pathlib import Path
import argparse,json,runpy,hashlib
import numpy as np
from register_courtyard import Camera
here=Path(__file__).parent
pa=argparse.ArgumentParser();pa.add_argument('--glb',type=Path,required=True);pa.add_argument('--output',type=Path,required=True)
pa.add_argument('--project',type=Path,default=here.parents[3]);pa.add_argument('--pose',type=Path,help='JSON with origin_xyz and local_to_model_3x3');pa.add_argument('--plan',type=Path,help='Registered local-to-ENU frames');a=pa.parse_args()
helpers=runpy.run_path(str(a.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
cam=Camera(2)
pose=json.loads(a.pose.read_bytes()) if a.pose else {'origin_xyz':[0,0,0],'local_to_model_3x3':np.eye(3).tolist()}
if a.plan:
 assert not a.pose
 T=np.array(json.loads(a.plan.read_bytes())['facade_frames']['case2']['local_to_ENU'])
 pose={'origin_xyz':T[:3,3].tolist(),'local_to_model_3x3':T[:3,:3].tolist(),'plan_sha256':hashlib.sha256(a.plan.read_bytes()).hexdigest()}
transform=np.array(pose['local_to_model_3x3']);origin=np.array(pose['origin_xyz']);eye=origin+transform@cam.c
scene=helpers['SerialScene'](a.glb)
def mat(k):return 'Xiangyang 313 | '+k
wall=mat('light yellow rendered window wall');glass=mat('case 2 neutral reflected glass');tint=mat('upper light below cyan canopy');frame=mat('dark painted window joinery')
hood=mat('translucent cyan canopy');dark=mat('dark hood edging and pipe');rack=mat('shelf and pale metal rails');sill=mat('pale projecting sill');deep=mat('shaded inside reveal')
tests={
 'yellow wall between upper western and centre windows':([364,105],wall),'yellow wall right of eastern upper window':([507,110],wall),'yellow wall between middle windows':([380,190],wall),
 'western window upper left light':([326,91],glass),'western window lower light':([346,112],glass),'western window centre post':([338,111],frame),
 'centre tinted top light':([379,97],tint),'centre clear lower light':([385,110],glass),'centre window central stile':([393,109],frame),
 'east tinted top light':([486,103],tint),'east lower right reflected light':([488,125],mat('pale eastern reflection')),'shadowed eastern lower left pane':([470,130],mat('shadow in upper eastern light')),
 'centre canopy left field':([375,80.4],hood),'centre canopy middle field':([395,81.4],hood),'centre canopy right field':([408,82.3],hood),
 'east canopy left field':([462,86.4],hood),'east canopy middle field':([478,87.9],hood),'east canopy right field':([494,89.6],hood),
 'shelf upper guard':([417,121.9],rack),'shelf platform edge':([408,129],rack),'shelf soffit':([408,133],rack),
 'open window recessed shadow':([349,200],deep),'open window lowest clear area':([351,227],deep),'edge-on open leaf':([367,216],glass),
 'narrow middle right pane':([391,217],glass),'narrow middle right sill':([389,256],sill),
 'central rain pipe above branches':([374.5,235],dark),'upper pipe left discharging arm':([341,163],dark),
 'lower partial western opening':([312,297],deep),'lower central opening head':([357,301],frame),'lower eastern opening':([406,346],deep)}
tests.update({
 'exterior condenser pale corner':([469,143],mat('ivory appliance housing')),
 'condenser inside circular fan recess':([452,149],mat('shaded circular intake')),
 'condenser radial front guard':([455,146.7],mat('dull metal fan grille')),
 'condenser bracket left leg':([448.2,160],dark),'condenser bracket right leg':([463.2,162],dark),
 'exposed short service pipe':([435.4,147],mat('ivory appliance housing')),
 'partial west window head':([278.0,172],frame),'partial west mid transom':([278,190.6],frame),
 'partial west lower transom':([277,207.5],frame),'right jamb of partial window':([280.5,197.5],frame),
 'partial pane behind projecting wing':([276,200],mat('pale eastern reflection')),
 'gridded housing near left edge':([280,262],mat('shaded circular intake')),
 'western grille upright':([283,267],mat('dull metal fan grille')),
 'small grille projecting lower shelf':([282,279.3],dark),
 'separate hook above lower grille':([274.9,243.7],dark)})
def hit(uv):
 result=scene.ray(eye,transform@cam.ray(uv),60)
 return None if result is None else result['material']
rows=[]
for feature,(uv,expected) in tests.items():
 actual=hit(uv);offset=None
 for distance in [0,.5,1,1.5,2,3]:
  for dx,dy in [(distance,0),(-distance,0),(0,distance),(0,-distance),(distance*.7071,distance*.7071),(-distance*.7071,distance*.7071),(distance*.7071,-distance*.7071),(-distance*.7071,-distance*.7071)]:
   if hit((uv[0]+dx,uv[1]+dy))==expected:offset=[round(dx,3),round(dy,3)];break
  if offset is not None:break
 rows.append({'feature':feature,'uv':uv,'expected':expected,'first_hit':actual,'nearest_expected_offset_work_px':offset})
out={'model':a.glb.name,'sha256':hashlib.sha256(a.glb.read_bytes()).hexdigest(),'triangles':len(scene.tri),'pose':pose,
'photograph_sha256':'3edf3374b870eaa12ba49d2c1f0f8f47781e3402fbc946701ec2114bb2dde2a1',
'count':len(rows),'at_exact_pixel':sum(x['first_hit']==x['expected']for x in rows),
'within_2_pixels':sum(x['nearest_expected_offset_work_px']is not None and float(np.linalg.norm(x['nearest_expected_offset_work_px']))<2.001 for x in rows),'rows':rows}
a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out['at_exact_pixel'],out['within_2_pixels'],[(i['feature'],i['first_hit'],i['nearest_expected_offset_work_px'])for i in rows if i['first_hit']!=i['expected']])
