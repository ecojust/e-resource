"""Recreate the three school photograph frusta and six authored viewpoints."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).resolve().parent
def study(name,label,target,eye,width):
    return dict(name=name,label=label,target=target,eye=eye,width_m=width,width=960,height=640)
def make():
    reg=json.loads((HERE/'river-registration.json').read_bytes());w=reg['width'];b1,b2,eave,ridge,axis,proj,tw,oc,*_=reg['parameters'];cx=w*axis
    cams=[study('overview','思孟堂临河十开间',[w/2,5.,6.7],[w*.87,-52.,25.5],51.)]
    for key,label in [('river-day','校方临河日景机位'),('river-night','校方临河夜景机位'),('river-aerial','校方临河俯斜机位')]:
        cam=reg['stations'][key];C=np.array(cam['eye']);R=np.array(cam['R']);K=np.array(cam['K']);iw,ih=cam['size'];cxp=K[0,2]+.5;cyp=K[1,2]+.5
        dist=R[2]@(np.array([w/2,2,6])-C)
        cams.append(dict(name=key,label=label,eye=C.tolist(),target=(C+dist*R[2]).tolist(),world_up=(-R[1]).tolist(),width_m=dist*iw/K[0,0],width=iw,height=ih,reference=key,source_crop=[0,0,iw,ih],source_dimensions=[iw,ih],sensor_fit='HORIZONTAL',pixel_aspect_y=1.,blender_pixel_aspect_x=1.,blender_pixel_aspect_y=1.,shift_x=(iw/2-cxp)/iw,shift_y=(cyp-ih/2)/iw,principal_point_edge_px=[cxp,cyp],projection_world_to_photo_pixel_centres=cam['P']))
    cams += [study('oculus','楼梯塔圆窗与小屋面',[cx,0.,oc+.7],[cx-2.8,-11.,oc+1.05],7.55),study('landing-sash','错层双窗与下门',[cx,-proj,3.84],[cx+2.6,-15.5,4.40],12.2),study('north-arches','北端折面和上下券窗',[w+.2,10.,6.0],[w+17.5,4.6,7.65],16.),study('upper-sashes','上层木窗与百叶',[w*.76,0.,b2+1.11],[w*.76+3.5,-12.5,b2+2.91],11.1),study('hipped-roof','临河瓦坡、屋脊与歇山转角',[w*.52,5.3,eave+1.30],[w*.18,-23.4,26.5],44.)]
    return cams
if __name__=='__main__':(HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
