"""Derive the three photographic cameras and six inspection views of the named gate."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).resolve().parent


def study(name,label,target,eye,width,shape=(960,640)):
    return {'name':name,'label':label,'target':target,'eye':eye,'width_m':width,'width':shape[0],'height':shape[1]}


def photograph(key,label,crop,cam):
    k,r,c=[np.array(cam[n]) for n in ('K','R','C')]
    d=float(r[2]@(np.array([-1,.0,1.5])-c))
    l,t,rr,b=crop;w=rr-l;h=b-t
    k[0,2]-=l;k[1,2]-=t;cx,cy=k[0,2]+.5,k[1,2]+.5
    return dict(name=key,label=label,eye=c.tolist(),target=(c+d*r[2]).tolist(),world_up=(-r[1]).tolist(),
        width_m=d*w/k[0,0],width=w,height=h,reference=key,source_dimensions=cam['size'],source_crop=crop,
        sensor_fit='HORIZONTAL',pixel_aspect_y=1.0,blender_pixel_aspect_x=1.,blender_pixel_aspect_y=1.,
        shift_x=(.5*w-cx)/w,shift_y=(cy-.5*h)/w,principal_point_edge_px=[cx,cy],
        projection_world_to_photo_pixel_centres=(k@np.column_stack((r,-r@c))).tolist())


def make():
    cams=json.loads((HERE/'gate-cameras.json').read_bytes())['stations']
    return [
        study('overview','刻名门柱、步行口与铁门',[-.90,.69,1.55],[4.75,-17.5,6.5],14.9,(1024,640)),
        photograph('front2015','2015年2月正面',[0,127,935,655],cams['8-1502']),
        photograph('east2013','2013年10月东斜面',[26,153,840,550],cams['9-1310']),
        photograph('west2015','2015年12月西斜面',[337,207,933,545],cams['7-1512']),
        study('name-panels','四块竖排刻名石',[0,0,1.53],[.65,-4.1,1.64],1.96,(650,920)),
        study('pedestrian','左侧行人铁门',[-5.86,.35,1.41],[-7.68,-6.65,2.3],3.25),
        study('main-leaves','入弄方向敞开的两扇铁门',[-2.31,1.15,1.29],[-.5,6.7,2.96],6.12),
        study('return-rail','刻名柱右侧砖基铁栏',[2.35,.2,1.35],[3.8,-6.4,2.5],5.79),
        study('caps','两座柱头的灯球与压顶',[-2.3,0,3.12],[-3.1,-6.8,4.7],6.4)
    ]

if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
