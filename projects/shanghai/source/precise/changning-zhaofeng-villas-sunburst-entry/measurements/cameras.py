"""The six registered photographic stations and four detail cameras of the gate."""
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
    stations=json.loads((HERE/'registered-views.json').read_bytes())
    cams=[view('overview','长宁路入口与两侧门墙',[-6.5,-13.,6.8],[-2.1,.6,1.45],13.2)]
    labels={'street-station-3':'街景西站望向入口','street-station-7':'街景中站看两侧门墙','street-station-8':'街景东站望向西柱','road-anniversary':'2021年报道的长宁路入口','district-detail':'2021年区府照片中的东墙','opposite-detail':'另一侧的日升纹及铸字'}
    for key,label in labels.items():
        d=stations[key]
        focus=[1.45,.23,2.65] if key in ('district-detail','opposite-detail') else [-2.,.2,2.]
        cams.append(registered(key,label,dict(projection=d['P'],frame=d['size']),[0,0,*d['size']],focus))
    cams.extend([view('sunburst','日升纹、铸字和花台',[2.,-4.7,2.86],[1.55,.22,2.1],3.9,890),
                 view('address','长宁路绿牌和西侧壁灯',[-5.86,-4.7,2.68],[-5.3,-.30,2.44],1.85,900),
                 view('leaves','两扇铁门与门后空间',[-3.6,-6.8,3.86],[-2.,1.45,1.34],7.85)])
    return cams
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
