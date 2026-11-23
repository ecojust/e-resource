"""Prepare two photographic stations and eight inspection views of Building 18."""
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
    st=json.loads((HERE/'two-stations.json').read_bytes())
    cams=[view('overview','南立面三券廊、18号山墙和外阶',[8.7,-31.5,14.0],[-4.45,.9,6.90],26.8,780)]
    for key,label,focus in [('numbered-gable','2018年街道相片 · 18号题号山墙',[0,0,7.1]),('outside-stair','外阶近照 · 三级柱头与穿孔栏板',[-4.9,-2.7,2.35])]:
        q=st[key];cams.append(registered(key,label,dict(projection=q['P'],frame=q['size']),[0,0,*q['size']],focus))
    cams.extend([view('house-number','圆形18号牌、入口挑檐和门扇',[2.25,-7.55,3.65],[0,0,2.62],5.4,800),
                 view('lower-arcade','底层三道砖券及墙厚',[-12.9,-9.1,1.73],[-8.55,1.3,1.77],12.5),
                 view('upper-gallery','通层红砖柱与一层高台弧廊',[-12.8,-10.6,6.65],[-8.25,.75,6.35],10.4),
                 view('stairs','室外石阶和方柱压顶',[-11.9,-9.8,4.7],[-5.85,-1.70,2.23],9.10),
                 view('east-gable','阁楼绿窗与三角山花',[4.5,-9.3,11.9],[0,.22,12.16],9.2,820),
                 view('stack','烟囱砖肩和坡檐',[-6.8,-4.7,15.8],[-2.4,2.35,13.4],6.80),
                 view('roof','四坡红瓦和东山墙交接',[-17.,-8.2,21.0],[-4.7,3.40,11.4],24.0)])
    return cams
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
