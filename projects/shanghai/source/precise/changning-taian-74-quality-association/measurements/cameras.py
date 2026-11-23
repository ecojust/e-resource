"""Prepare the press, street and inspection views of 74 Tai’an Road."""
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
    stations=json.loads((HERE/'three-front-stations.json').read_bytes())
    cameras=[view('overview','74号临街门廊与西侧窗带',[-24,-27,19],[2.4,6.8,6.55],33,840)]
    for key,label in [('press-oblique','文旅照片 · 沿街斜面'),('street-front-2020','2020年2月 · 两樘拱肩门'),('street-corner-2020','2020年2月 · 74号门牌与街角')]:
        state=stations[key]
        cameras.append(registered(key,label,dict(projection=state['P'],frame=state['size']),[0,0,*state['size']],[5.5,0,7.]))
    cameras.extend([view('pediment','临街屋顶山花及檐口',[4,-17,14.4],[5.55,0,11.9],13.2),
                    view('porch','檐下双门与门罩徽章',[3.,-10,4.22],[5.1,.1,2.49],10.8,800),
                    view('number','两扇门之间的74号',[5.1,-2.3,2.34],[5.68,1.02,2.25],1.09,820),
                    view('spandrel','挂着七字名牌的西柱',[1.1,-4.9,2.43],[1.9,.98,1.76],3.65,940),
                    view('side','弄侧山花、V纹与六格凹板',[-22.,16.,9.],[0,14.4,8.6],16.9,840),
                    view('cornice','转角上方的挑檐和层间装饰',[-8.1,-11.4,13.4],[.72,2,10.75],14.3)])
    return cameras
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
