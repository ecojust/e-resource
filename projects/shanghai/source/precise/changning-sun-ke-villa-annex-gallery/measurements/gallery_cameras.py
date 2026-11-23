"""Translate the two original camera crops and seven architectural views into the viewer convention."""
import json
from pathlib import Path
import numpy as np
from fit_gallery import GalleryPlane
HERE=Path(__file__).resolve().parent
CROPS={'gallery':([12,180,932,605],[1080,638]),'passage':([868,190,1080,469],[1080,810])}
def registered(key,label,focus):
    src=HERE/('gallery-station.json'if key=='gallery'else'passage-station.json')
    projection=np.array(json.loads(src.read_bytes())['projection'])
    r=projection[2,:3];r=r/np.linalg.norm(r);m=projection[:,:3]
    cx=float(r@m[0]);cy=float(r@m[1])
    x=m[0]-cx*r;y=m[1]-cy*r
    fx=np.linalg.norm(x);fy=np.linalg.norm(y)
    eye=-np.linalg.solve(m,projection[:,3])
    depth=float((np.array(focus)-eye)@r)
    crop,size=CROPS[key];w,h=crop[2]-crop[0],crop[3]-crop[1]
    cx+=.5-crop[0];cy+=.5-crop[1];aspect=fx/fy
    return dict(name='photo-'+key,label=label,eye=eye.tolist(),target=(eye+depth*r).tolist(),world_up=(-y/fy).tolist(),
                width_m=float(w*depth/fx),width=w,height=h,reference=key,source_dimensions=size,source_crop=crop,sensor_fit='HORIZONTAL',
                pixel_aspect_y=aspect,blender_pixel_aspect_x=max(1.,1/aspect),blender_pixel_aspect_y=max(1.,aspect),
                shift_x=float((w/2-cx)/w),shift_y=float((cy-h/2)*aspect/w),principal_point_edge_px=[cx,cy],
                skew_px=0.,photo_focal_x_px=float(fx),projection_world_to_photo_pixel_centres=projection.tolist())
def view(name,label,target,offset,width,dimensions=(960,660)):
    return dict(name=name,label=label,target=target,eye=(np.asarray(target)+offset).tolist(),width_m=width,width=dimensions[0],height=dimensions[1])
def make():
    return [view('overview','附楼临院面全貌',[3.10,2.40,3.29],[-5.85,-24.6,7.6],23.8),
            registered('gallery','修缮实照 · 三券与木廊',[3.0,0,2.8]),
            registered('passage','园口指示牌旁 · 方门',[ -3.12,0,1.27]),
            view('arcade','三道扁券与斜帽券墩',[4.65,.34,1.48],[-1.9,-12.4,1.20],12.45),
            view('timber-gallery','七跨木柱与栏杆',[5.6,.13,3.77],[-.8,-13.8,1.0],13.80),
            view('gable-tiles','错台筒瓦与檐沟',[-1.1,1.3,5.70],[-4.4,-8.6,4.60],9.95),
            view('hopper','双入口接水斗与立管',[-1.64,-.06,4.50],[-1.77,-5.40,.56],2.38),
            view('passage-return','方门右壁六枚圆形饰件',[-2.06,3.80,1.50],[-3.00,-5.9,.30],6.72),
            view('arched-return','首券内侧通往院内的开口',[1.0,.80,1.24],[-.48,-7.7,.30],3.8)]
if __name__=='__main__':
    result=make()
    (HERE.parent/'source/cameras.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
