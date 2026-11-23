"""Three independently fitted photographs plus the overview and five building details."""
from pathlib import Path
import json,numpy as np
D=Path(__file__).resolve().parent
def view(name,label,target,eye,width):return dict(name=name,label=label,target=target,eye=eye,width_m=width,width=960,height=640)
def make():
 fit=json.loads((D/'garden-registration.json').read_bytes());cams=[view('overview','四跨院廊与外阶',[0,1.0,6.92],[6.2,-34,13.42],28.8)]
 for name,label in [('commons-2014','2014年四月院面正照'),('park-stair','阶侧斜照'),('garden-oblique','庭园仰望角度')]:
  s=fit['stations'][name];R=np.array(s['R']);C=np.array(s['eye']);K=np.array(s['K']);iw,ih=s['size'];dist=24.;cx=K[0,2]+.5;cy=K[1,2]+.5
  cams.append(dict(name=name,label=label,eye=C.tolist(),target=(C+dist*R[2]).tolist(),world_up=(-R[1]).tolist(),width_m=dist*iw/K[0,0],width=iw,height=ih,reference=name,source_crop=[0,0,iw,ih],source_dimensions=[iw,ih],sensor_fit='HORIZONTAL',blender_pixel_aspect_x=1.,blender_pixel_aspect_y=1.,pixel_aspect_y=1.,shift_x=(iw/2-cx)/iw,shift_y=(cy-ih/2)/iw,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=s['P']))
 cams.extend([view('double-flights','双跑外阶与平台',[-.4,-1.1,1.6],[-9.,-18.,5.9],21.6),view('terrace-openings','洗石台身和四个小窗',[0,-1.45,1.62],[-1.6,-12.,2.65],11.8),view('pier-bracket','砖柱与檐下撑托',[5,.0,7.82],[3.45,-6.8,6.90],3.55),view('upper-gallery','二层栏板透孔与廊后窗',[2.4,.55,6.58],[-2,-9,7.08],8.6),view('roof-dormers','四樘坡顶老虎窗及烟囱',[0,1.33,10.90],[3.4,-19.,14.6],23.8)])
 return cams
if __name__=='__main__':(D.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
