"""Build nine views in the same metre frame as the measured 143-1 doors and windows."""
import json
from pathlib import Path
import numpy as np
from register_street import Camera

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
    data=json.loads((HERE/'number-plates.json').read_bytes())
    camera=Camera('2018')
    plates=[camera.wall(np.mean(v['corners_full_source_px'],axis=0),-.045 if k=='black-door' else -.205)
            for k,v in data['plates'].items()]
    centre=(plates[0]+plates[1])/2
    flank=json.loads((HERE/'lane-return-metric.json').read_bytes())
    lane_y=flank['measured_end_y_m']*.52
    lane_x=flank['wall_x_at_y0_m']+lane_y*flank['wall_dx_per_y']
    return [
        study('overview','临街转角与弄口',(-2.78,2.45,5.29),(15.0,-25.0,8.0),22.8,(1040,730)),
        original('2018','street-2018','2018年街对面摄影站'),
        original('1512-6','street-2015','2015年12月反向街站'),
        study('two-numbers','143-1门牌与143弄弄牌',centre,(1.85,-5.45,.41),max(2.80,abs(plates[0][0]-plates[1][0])+1.45)),
        study('staggered-windows','七樘错层钢窗',(-4.77,0,6.27),(.55,-14.9,.14),8.25,(810,860)),
        study('upper-sashes','上亮、绿钢窗与浅色墙',(-2.54,0,9.08),(1.05,-5.65,.15),3.36),
        study('lane-return','弄内开窗与窗篷',(lane_x,lane_y,4.94),(9.6,-2.85,1.72),10.30,(920,785)),
        study('service-pipes','穿墙金属件与修补砖缘',(.98,-.04,7.95),(1.22,-6.9,.23),5.02,(845,835)),
        study('roof-eaves','街角屋面与檐口',(-3.25,2.15,10.74),(5.20,-11.4,5.50),15.1,(1000,660)),
    ]

if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
