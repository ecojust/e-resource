"""Prepare three photo registrations and seven inspection views of 4, Lane 1112."""
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
    stations=json.loads((HERE/'registered-stations.json').read_bytes())
    cameras=[view('overview','4号凸翼、绿牌与弄侧窗墙',[-25,-32,23],[5,5,7.5],40,865)]
    for key,label in [('corner-2011','2011年12月 · 侧墙与门牌'),('corner-2015','2015年11月 · 院门及公告箱'),('street-2020','2020年2月 · 南凸翼三窗面')]:
        c=stations[key];cameras.append(registered(key,label,dict(projection=c['P'],frame=c['size']),[0,0,*c['size']],[2.5,1.2,7.8]))
    cameras.extend([view('street-wing','折肩窗与缓拱窗',[6,-28,10.0],[8.9,-2.6,8.65],18),
        view('two-crowns','弄侧与转角弧形墙头',[-15,-12,17.3],[-.1,3.5,11.5],19),
        view('lane','窗楣、腰带与雨管',[-22,9.5,8.9],[-1.1,7,7.0],20),
        view('roof','两片红瓦坡面',[-12,-23,24.5],[7,4.4,12.8],26),
        view('gate','临弄门墙与院门',[-9,-7,4.4],[-1.55,-3.3,2.25],8.55,830),
        view('plaque','4号绿底门牌',[-3.35,-3.58,2.81],[-1.38,-3.42,2.78],.91,790)])
    return cameras
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
