"""Derive the two photographic crops and seven additional views of the measured garden corner."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).resolve().parent


def study(name,label,target,eye,width,shape=(960,640)):
    return {'name':name,'label':label,'target':target,'eye':eye,'width_m':width,'width':shape[0],'height':shape[1]}


def photograph(key,label,crop,cam):
    k,r,c=[np.array(cam[n]) for n in ('K','R','C')]
    d=float(r[2]@(np.array([2.5,-2.3,1.2])-c))
    l,t,rr,b=crop;w=rr-l;h=b-t
    k[0,2]-=l;k[1,2]-=t;cx,cy=k[0,2]+.5,k[1,2]+.5
    return dict(name=key,label=label,eye=c.tolist(),target=(c+d*r[2]).tolist(),world_up=(-r[1]).tolist(),
        width_m=d*w/k[0,0],width=w,height=h,reference=key,source_dimensions=cam['size'],source_crop=crop,
        sensor_fit='HORIZONTAL',pixel_aspect_y=1.0,blender_pixel_aspect_x=1.,blender_pixel_aspect_y=1.,
        shift_x=(.5*w-cx)/w,shift_y=(cy-.5*h)/w,principal_point_edge_px=[cx,cy],
        projection_world_to_photo_pixel_centres=(k@np.column_stack((r,-r@c))).tolist())


def make():
    s=json.loads((HERE/'garden-cameras.json').read_bytes())['stations']
    return [study('overview','水庭、转角长窗与石池',[2.5,-4.7,1.13],[13.5,-24.3,9.2],18.3,(1024,650)),
        photograph('whb2019','2019年文汇报近景',[32,124,490,277],s['whb2019']),
        photograph('garden2017','2017年解放日报水池视角',[24,130,405,244],s['garden2017']),
        study('back-screen','五层白色横向格栅',[6.10,0,1.25],[7.0,-6.80,2.15],4.4),
        study('red-glazing','红框玻璃与帘窗',[2.2,-.1,1.3],[3.85,-8.0,2.15],6.7),
        study('return-end','侧翼长窗与树旁露出的端部',[ -2.02,-6.90,1.45],[3.65,-9.65,2.52],8.7),
        study('roof-corner','两段薄檐交角',[ -.96,-.70,2.80],[3.40,-8.20,5.2],6.30),
        study('pool','石池压顶与水面',[4.9,-7.6,0],[11.9,-15.5,7.7],11.0),
        study('garden-section','水庭与格栅间的高差',[1.,-4.8,.75],[14.8,-8.6,3.4],16.5)]


if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
