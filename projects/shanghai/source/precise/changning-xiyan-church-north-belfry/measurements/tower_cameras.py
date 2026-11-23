"""Translate the four measured camera crops and five architectural views into the viewer convention."""
import json
from pathlib import Path
import numpy as np
from check_views import CROPS
HERE=Path(__file__).resolve().parent
def registered(key,label,focus):
    station=json.loads((HERE/'tower-stations.json').read_bytes())['stations'][key]
    projection=np.asarray(station['projection'])
    r=projection[2,:3];r=r/np.linalg.norm(r);m=projection[:,:3]
    cx=float(r@m[0]);cy=float(r@m[1])
    x=m[0]-cx*r;y=m[1]-cy*r
    fx=np.linalg.norm(x);fy=np.linalg.norm(y)
    eye=-np.linalg.solve(m,projection[:,3])
    depth=float((np.array(focus)-eye)@r)
    crop,size=CROPS[key],station['frame'];w,h=crop[2]-crop[0],crop[3]-crop[1]
    cx+=.5-crop[0];cy+=.5-crop[1];aspect=fx/fy
    return dict(name='photo-'+key,label=label,eye=eye.tolist(),target=(eye+depth*r).tolist(),world_up=(-y/fy).tolist(),
                width_m=float(w*depth/fx),width=w,height=h,reference=key,source_dimensions=size,source_crop=crop,sensor_fit='HORIZONTAL',
                pixel_aspect_y=aspect,blender_pixel_aspect_x=max(1.,1/aspect),blender_pixel_aspect_y=max(1.,aspect),
                shift_x=float((w/2-cx)/w),shift_y=float((cy-h/2)*aspect/w),principal_point_edge_px=[cx,cy],
                skew_px=0.,photo_focal_x_px=float(fx),projection_world_to_photo_pixel_centres=projection.tolist())
def view(name,label,target,offset,width,dimensions=(960,660)):
    return dict(name=name,label=label,target=target,eye=(np.asarray(target)+offset).tolist(),width_m=width,width=dimensions[0],height=dimensions[1])
def make():
    return [view('overview','独立钟楼全貌',[0,0,10.25],[-15,-31,5.8],17.4,(750,960)),
            registered('june-court','2016年6月院前 · 三联券与碑',[0,-1,10.3]),
            registered('may-court','2016年5月院前 · 沿阶窄窗',[0,-1,10.3]),
            registered('may-river','2016年5月隔河 · 两面钟室',[0,0,12.4]),
            registered('winter-river','2011年冬季隔河 · 双面采光缝',[0,0,10.4]),
            view('belfry','钟室尖券和水平百叶',[0,-1.25,14.6],[-3.8,-8.7,.85],5.10),
            view('shaft','沿内梯逐级下降的窄窗',[0,-1.3,6.17],[-4.25,-13.2,.95],6.7,(750,960)),
            view('lantern','短灯亭和塔顶铁十字',[0,0,18.75],[-5.2,-7.7,1.45],5.60),
            view('memorial','院前深色刻石与十字',[0,-1.92,.72],[-1.22,-3.35,.43],2.29)]
if __name__=='__main__':
    result=make()
    (HERE.parent/'source/cameras.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
