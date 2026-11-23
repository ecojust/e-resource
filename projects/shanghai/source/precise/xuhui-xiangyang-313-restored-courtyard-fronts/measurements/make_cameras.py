"""Locate the two measured court cameras and seven architectural views in the footprint's ENU frame."""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import rq
from plan_points import facade_point,load
from register_courtyard import Camera
HERE=Path(__file__).resolve().parent

def original(key,name,label,plan):
    local=Camera(key)
    t=np.asarray(plan['facade_frames'][key]['local_to_ENU'])
    project=local.P@np.linalg.inv(t)
    k,r=rq(project[:,:3]);sign=np.diag(np.sign(np.diag(k)));k=k@sign;r=sign@r
    k/=k[2,2]
    if np.linalg.det(r)<.9999:raise ValueError('Invalid camera rotation')
    w,h=local.size
    eye=np.array(facade_point(key,*local.c,plan))
    target=eye+8*r[2]
    px,py=k[0,2]+.5,k[1,2]+.5
    ratio=k[0,0]/k[1,1]
    return dict(name=name,label=label,eye=eye.tolist(),target=target.tolist(),world_up=(-r[1]).tolist(),
                width_m=8*w/k[0,0],width=int(w),height=int(h),reference=key,sensor_fit='HORIZONTAL',
                pixel_aspect_y=ratio,blender_pixel_aspect_x=max(1.,1./ratio),blender_pixel_aspect_y=max(1.,ratio),
                shift_x=(w/2-px)/w,shift_y=(py-h/2)*ratio/w,principal_point_edge_px=[px,py],
                skew_px=float(k[0,1]),photo_focal_x_px=float(k[0,0]),projection_world_to_photo_pixel_centres=project.tolist())
def study(name,label,eye,target,span,w=960,h=640):
    return dict(name=name,label=label,eye=eye,target=target,width_m=span,width=w,height=h)
def local_study(case,name,label,eye,target,span,plan):
    return study(name,label,facade_point(case,*eye,plan),facade_point(case,*target,plan),span)
def make():
    plan=load();vertices=plan['vertices'];ground=np.asarray([p['ground_EN_m']for p in vertices])
    bounds=ground.min(0),ground.max(0);cx,cy=(bounds[0]+bounds[1])/2
    return [
        study('overview','住宅与院面',[cx+13.4,cy-25.2,15.7],[cx,cy,5.9],25.65,1040,680),
        original('case1','south-photo','修缮后南院摄影机位',plan),
        local_study('case1','twenty-lights','凸窗四扇二十格',(1.1,-4.1,4.6),(.0,.0,4.55),3.05,plan),
        local_study('case1','shuttered-door','百叶门与薄挑檐',(.7,-4.6,1.83),(.1,0,1.35),3.30,plan),
        local_study('case1','service-balcony','钢阳台、斜栏和波纹矮棚',(-5.7,-7.9,4.18),(-5.95,.06,3.84),5.94,plan),
        local_study('case1','wall-brackets','空调托角与裙边雨篷',(-2.12,-6.55,3.10),(-3.50,.43,2.76),4.44,plan),
        original('case2','north-photo','修缮后北院摄影机位',plan),
        local_study('case2','blue-hoods','青色窗篷与挑架',(.4,-8.4,7.80),(.93,-.14,8.05),6.97,plan),
        local_study('case2','north-leaf','开启窗扇与落水管',(-.75,-6.55,4.47),(-.7,-.09,4.83),4.60,plan),
    ]
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
