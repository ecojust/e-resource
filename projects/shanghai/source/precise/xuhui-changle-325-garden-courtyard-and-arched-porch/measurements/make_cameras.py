"""Build nine views in the courtyard frame of the measured entrance and curved garden wing."""
import json
from pathlib import Path
import numpy as np
from register_court import Camera
from register_porch import PorchFrame

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
    frame=PorchFrame()
    def porch(name,label,target,eye,span,size=(960,640)):
        return study(name,label,frame.xyz(*target),frame.xyz(*eye)-frame.xyz(*target),span,size)
    return [
        study('overview','院内券廊与弧形窗墙',[-6.95,6.85,2.95],[-5.,-45.,16.],26.3,(1024,700)),
        original('fayhoo','photo-court','2015年4月4日院内摄影站'),
        original('3-1504-171','photo-street','2015年4月街口摄影站'),
        porch('stone-flight','十级石阶与上下平台',[0.,-1.93,1.30],[1.55,-9.7,4.2],6.53,(930,740)),
        porch('glass-entrance','双扇玻璃、拉手与底夹',[.30,1.17,2.84],[.12,-4.45,2.84],3.24,(830,765)),
        porch('tile-canopy','红瓦坡、黑檐与托座',[0.,.89,5.25],[-2.02,-7.05,7.15],5.65,(920,690)),
        porch('stone-newels','浅盘、石球与梯栏',[-2.03,-2.28,2.43],[-5.75,-8.20,4.40],4.05,(880,695)),
        study('curved-windows','转弧窗扇与分格',[-2.83,.12,2.27],[-2.54,-7.4,.52],4.57,(910,690)),
        study('wing-eaves','弧翼上沿与两处窗墙',[-1.19,.19,3.04],[-3.15,-8.5,3.31],8.15,(985,690)),
    ]
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
