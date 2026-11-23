"""Prepare the exterior and stair photograph cameras and seven inspections of No. 20."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import rq
HERE=Path(__file__).resolve().parent
def registered(key,label,station,crop,focus):
    projection=np.asarray(station['projection'],dtype=float)
    scale=np.linalg.norm(projection[2,:3]);projection=projection/scale
    intrinsic,axes=rq(projection[:,:3]);signs=np.diag(np.where(np.diag(intrinsic)<0,-1.,1.))
    intrinsic=intrinsic@signs;axes=signs@axes
    fx,fy=intrinsic[0,0],intrinsic[1,1]
    eye=-np.linalg.solve(projection[:,:3],projection[:,3])
    r=axes[2];depth=float((np.array(focus)-eye)@r)
    w,h=crop[2]-crop[0],crop[3]-crop[1]
    cx=intrinsic[0,2]+.5-crop[0];cy=intrinsic[1,2]+.5-crop[1];aspect=fx/fy
    return dict(name='photo-'+key,label=label,eye=eye.tolist(),target=(eye+depth*r).tolist(),world_up=(-axes[1]).tolist(),
                width_m=float(w*depth/fx),width=w,height=h,reference=key,source_dimensions=station['frame'],source_crop=list(crop),sensor_fit='HORIZONTAL',
                pixel_aspect_y=aspect,blender_pixel_aspect_x=max(1.,1/aspect),blender_pixel_aspect_y=max(1.,aspect),
                shift_x=float((w/2-cx)/w),shift_y=float((cy-h/2)*aspect/w),principal_point_edge_px=[cx,cy],
                skew_px=float(intrinsic[0,1]),photo_focal_x_px=float(fx),projection_world_to_photo_pixel_centres=projection.tolist())
def view(key,label,eye,focus,width,height=750):
    return dict(name=key,label=label,eye=eye,target=focus,width_m=width,width=1080,height=height)
def make():
    ss=json.loads((HERE/'two-stations.json').read_bytes())
    views=[view('overview','临弄巷墙与灰腰线',[13,-21,11],[2.25,0,4.9],20)]
    for key,label,focus in [('photo-lane','2015年巷内原摄影位',[2,0,4.4]),('photo-stair','2015年梯口原摄影位',[-1.1,6.4,1.3])]:
        st=ss[key];v=registered(key,label,dict(projection=st['P'],frame=st['size']),[0,0,*st['size']],focus);v['name']=key;views.append(v)
    views.extend([view('curved-crown','卷额和上层窄窗',[6.8,-8,8.4],[3.1,0,8.0],6.6),
                  view('lower-windows','底层长窗与红棕色壁柜',[8,-10,3.9],[5.30,0,2.17],7.6),
                  view('stair-nose','水磨石踏面与前缘',[-1.49,4.74,1.35],[-1.10,6.75,.72],2.05),
                  view('handrail','上行木扶手与栏杆',[-1.49,5.67,1.47],[-.44,7.9,1.93],2.45),
                  view('mailboxes','梯口木制与绿漆信箱',[-1.55,4.0,1.62],[-.36,4.90,1.57],1.78),
                  view('entry','临弄的深门洞、窗和竖管',[3.5,-8.5,3.31],[-.25,0,2.88],7.9)])
    return views
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
