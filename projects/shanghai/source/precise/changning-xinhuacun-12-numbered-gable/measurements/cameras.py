"""Prepare three matched photographic stations and seven inspection views of House 12."""
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
    stations=json.loads((HERE/'three-photographic-stations.json').read_bytes())
    cameras=[view('overview','12号山墙、院廊和三道砖券',[21,-20,12.0],[4.5,3.2,5.1],21.5)]
    focus=[3.9,0,6.4]
    for key,label in [('numbered-front','园中正面 · 墙上的12号'),('archival-front','旧照 · 12号楼山墙'),('garden-oblique','2026年 · 从花园看山墙转角')]:
        s=stations[key];cameras.append(registered(key,label,dict(projection=s['P'],frame=s['size']),[0,0,*s['size']],focus))
    cameras.extend([view('gable','三樘小格窗与山花',[5.6,-13,6.7],[3.0,.10,6.2],9.5,920),
                    view('number','门牌铸字及粗砂面',[3.5,-4.4,5.6],[2.5,0,5.52],2.6,790),
                    view('attic','山花、绿框阁楼窗与檐口',[6.5,-8.3,10.3],[3.7,.11,10.2],7.7,850),
                    view('arcade','平台下三道砖券',[17,3.8,2.65],[8.5,4.22,1.71],10.1,850),
                    view('upper-gallery','上层凹廊与垂挂花木',[13.1,-1.8,7.5],[7.27,4.08,5.74],8.8,850),
                    view('roof','转角檐槽、老虎窗及远端山花',[16.6,15.0,17.9],[5.3,4.,8.0],15.2)])
    return cameras
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
