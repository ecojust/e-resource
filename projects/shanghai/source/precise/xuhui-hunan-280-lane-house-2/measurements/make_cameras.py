"""Nine registered and study cameras of No. 2, Lane 280, Hunan Road."""
import json
from pathlib import Path
import numpy as np
from register_house import Camera


HERE=Path(__file__).absolute().parent

def original(key,name,label):
    cam=Camera(key)
    width,height=cam.size
    fx,fy=cam.K[0,0],cam.K[1,1]
    px,py=cam.K[0,2]+.5,cam.K[1,2]+.5
    ratio=fx/fy
    return dict(name=name,label=label,eye=cam.c.tolist(),target=(cam.c+8*cam.R[2]).tolist(),
                world_up=(-cam.R[1]).tolist(),width_m=8*width/fx,width=width,height=height,reference=key,
                sensor_fit='HORIZONTAL',pixel_aspect_y=ratio,blender_pixel_aspect_x=max(1.,1/ratio),
                blender_pixel_aspect_y=max(1.,ratio),shift_x=(width/2-px)/width,
                shift_y=(py-height/2)*ratio/width,principal_point_edge_px=[px,py],
                skew_px=float(cam.K[0,1]),photo_focal_x_px=fx,
                projection_world_to_photo_pixel_centres=cam.P.tolist())

def study(name,label,target,offset,span,size=(960,640)):
    return dict(name=name,label=label,eye=(np.asarray(target)+offset).tolist(),
                target=list(target),width_m=span,width=size[0],height=size[1])

def make():
    face=json.loads((HERE/'entrance-placement.json').read_bytes())
    limits=json.loads((HERE/'corner-site-layout.json').read_bytes())['curve']
    eye_normal=np.r_[face['outside_unit_enu'],0.]
    along=np.r_[face['across_unit_enu'],0.]
    origin=np.array(face['left_sill_enu_m'])
    opening=face['opening_size_m']
    door=origin+.45*opening[0]*along+[0.,0.,.52*opening[1]]
    plate=np.array(face['house_plaque']['centre_enu_m'])
    return [
        study('overview','五层临街窗墙和西南转角',[5.39124,5.45754,8.60895],[-32.,-39.,11.6],37.5,(1024,700)),
        original('84','photo-lane','2016年3月 · 弄内摄影站'),
        original('86','photo-street','2016年3月 · 湖南路摄影站'),
        original('6-1512','photo-winter','2015年12月 · 临街窗墙摄影站'),
        study('paired-door','转角下的双扇门',door,4.4*eye_normal+[0.,0.,.26],2.92,(820,760)),
        study('number-two','门左的绿色2号牌',plate+.13*along,1.7*eye_normal+[0.,0.,.07],.94,(800,650)),
        study('corner-sashes','转角钢窗的三折分格',[limits[0],limits[1],limits[2]+3.9],[-5.4,-5.4,1.3],4.8,(930,720)),
        study('street-windows','临街外挑窗墙与窄窗',[6.55,-.18,8.45],[1.,-19.4,1.6],14.8,(930,760)),
        study('lane-windows','弄内窗列与落水管',[-3.1,10.0,8.1],(Camera('84').c-np.array([-3.1,10.0,8.1])).tolist(),11.9,(930,720)),
    ]

if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
