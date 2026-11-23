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
    cameras=[view('overview','新华路200号朝南双层外廊与重檐',[22,-38,17],[0,4,7.5],35,780)]
    for key,label in [('garden-2010','2010年庭院正面'),('garden-2023','2023年市文旅局庭院视角')]:
        q=st[key];cameras.append(registered(key,label,dict(projection=q['P'],frame=q['size']),[0,0,*q['size']],[0,2.8,7.4]))
    return cameras+[
      view('entrance','南入口并柱与石阶',[6,-13,3.4],[0,-.1,2.3],13.5),
      view('lion','石台与卧狮',[7,-6,1.85],[3.62,-1.86,1.10],4.2),
      view('balustrade','二层石栏与镂空',[-8.5,-9.5,6.8],[-2,-.33,5.92],11.0),
      view('brackets','短挑檐与柱头彩绘',[5.1,-6.9,9.5],[2.1,-.24,9.25],6.75),
      view('attic','上层五组窗洞与折肩口',[3,-16,11.4],[0,2.85,11.8],21.8),
      view('roof','主脊及四个屋角',[19,-20,22],[0,7.5,13],30),
      view('section','自东转角看前廊进深',[21,-10,8.0],[6,2.5,6.6],18)]
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
