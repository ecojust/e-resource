"""Intersect observed rays with the street-facing surface and record independent date residuals."""
from pathlib import Path
from math import *
import json,sys,hashlib,numpy as np
q=Path(__file__).parent;sys.path.insert(0,str(q));from solve import ray,fit,C,M
# The second gold character is visible from the front and the southern 2020 station.
samples=[('aligned-front-2020',372,413),('aligned-south-2020',375,372)]
anchor,res=fit(samples);angle=-103.2;ex=np.array([cos(radians(angle)),-sin(radians(angle))]);ey=np.array([sin(radians(angle)),cos(radians(angle))]);A=(np.array(anchor)-C)*M
def project(name,u,v):
 d,az,el,_,camera=ray(name,u,v);vec=np.array([sin(radians(az)),cos(radians(az))]);t=(A-camera)@ey/(vec@ey);pos=camera+vec*t
 return [round(float((pos-A)@ex),3),round(float(d['station']['height']+t*tan(radians(el))),3)]
front='aligned-front-2020'
points={'ground_at_name_face':(371,653),'left_face_at_mid':(337,413),'right_face_at_mid':(412,413),'front_of_plinth_top':(372,597),'main_shaft_top':(372,215),'top_cap_high':(372,171),'gold_upper_center':(371,361),'gold_middle_center':(372,413),'gold_lower_center':(373,478),'plaque_wall_left':(201,445),'plaque_wall_right':(337,445),'plaque_wall_coping':(268,352),'green_address_center':(290,378),'white_protection_center':(303,424),'lower_frame_center':(308,507)}
measured={k:{'image_xy':pt,'x_z_absolute':project(front,*pt)}for k,pt in points.items()}
ground=measured['ground_at_name_face']['x_z_absolute'][1]
for r in measured.values():r['x_z_ground']=[r['x_z_absolute'][0],round(r['x_z_absolute'][1]-ground,3)]
print('anchor',anchor,'heading',angle,'ground',ground,{k:v['x_z_ground']for k,v in measured.items()})
out=dict(id='huangpu-meilan-lane-named-gatepost',site_wgs84=anchor,heading_deg=angle,local_x='沿街朝北偏西，面对院门时向右',local_y='朝院内西南偏西',center_samples=samples,resulting_rays=res,plane_image=front,model_ground_reference=ground,surface_points=measured,positional_uncertainty_m=.55,vertical_uncertainty_m=.30,observations='近正面为2020-02-19。南侧同期站以第二字交会，绿牌与下方竖框的高度为两层正墙上的估值。更近的2015站绝对登记与2020相差约0.6米；2015和2024用于核构件及相对比例。南侧透视与正面观察到的字心高差约0.4米，按正面相对物面底部折算。',references={f:hashlib.sha256((q/f).read_bytes()).hexdigest()for f in ['aligned-front-2020.json','aligned-south-2020.json','front-2015.json','front-2019.json','travel-4.json','official.json']})
(q/'field-dimensions.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
