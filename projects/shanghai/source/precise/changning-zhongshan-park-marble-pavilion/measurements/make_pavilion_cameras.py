"""Derive the three photographic cameras and six inspection views of the marble pavilion."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).resolve().parent


def study(name,label,target,eye,width,shape=(960,640)):
    return {'name':name,'label':label,'target':target,'eye':eye,'width_m':width,'width':shape[0],'height':shape[1]}


def photograph(key,label,crop,cam):
    k,r,c=[np.array(cam[n]) for n in ('K','R','C')]
    d=float(r[2]@(np.array([0,1.5,2.4])-c))
    l,t,rr,b=crop;w=rr-l;h=b-t
    k[0,2]-=l;k[1,2]-=t;cx,cy=k[0,2]+.5,k[1,2]+.5
    return dict(name=key,label=label,eye=c.tolist(),target=(c+d*r[2]).tolist(),world_up=(-r[1]).tolist(),
        width_m=d*w/k[0,0],width=w,height=h,reference=key,source_dimensions=cam['size'],source_crop=crop,
        sensor_fit='HORIZONTAL',pixel_aspect_y=1.0,blender_pixel_aspect_x=1.,blender_pixel_aspect_y=1.,
        shift_x=(.5*w-cx)/w,shift_y=(cy-.5*h)/w,principal_point_edge_px=[cx,cy],
        projection_world_to_photo_pixel_centres=(k@np.column_stack((r,-r@c))).tolist())


def make():
    cams=json.loads((HERE/'pavilion-cameras.json').read_bytes())['stations']
    return [
        study('overview','四柱、三孔石屏与石阶',[0,1.7,2.2],[11,-25,10],23.7,(1024,650)),
        photograph('fayhoo2014','2014年正面',[16,112,1028,495],cams['fayhoo2014']),
        photograph('district-oblique','现况左斜视角',[426,346,892,680],cams['district-oblique']),
        photograph('district-archive','资料旧照右斜视角',[0,25,396,249],cams['district-archive']),
        study('roof','透空椽架',[0,2.1,4.16],[5.5,-9,10],13.1),
        study('columns','柱列与柱脚',[0,0,2.30],[8.2,-12,3.5],13.1),
        study('screen','中央三拱口与两侧雕像龛',[0,4.1,2.43],[.1,-6.7,2.42],12.6),
        study('terrace','平台与正面各级踏步',[0,-.7,.55],[9.4,-14,4.8],21.8),
        study('urn','花钵与侧石栏',[-7.25,1.2,1.20],[-12.4,-5.4,3.1],5.8)
    ]

if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
