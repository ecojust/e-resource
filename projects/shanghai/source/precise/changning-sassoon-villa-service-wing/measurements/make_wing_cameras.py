"""Two registered source-image crops and seven study cameras for the service wing."""
import json
from pathlib import Path
import numpy as np
from wing_frame import WingFrame

HERE=Path(__file__).resolve().parent
REGISTERED={'album':('album-1937','1937年相册 · 辅楼局部',[286,470,670,656],[1500,1222]),'design':('design-2014','2014年修缮透视 · 院面局部',[58,103,403,252],[573,323])}

def original(frame,key):
    name,label,crop,size=REGISTERED[key];camera=getattr(frame,key)
    left,top,right,bottom=crop
    width,height=right-left,bottom-top
    centre=np.array([frame.width/2,1.4,frame.eave])
    distance=float(np.dot(centre-camera.C,camera.R[2]))
    intrinsic=camera.K.copy();intrinsic[0,2]-=left;intrinsic[1,2]-=top
    fx=float(intrinsic[0,0]);aspect=fx/intrinsic[1,1]
    cx,cy=intrinsic[0,2]+.5,intrinsic[1,2]+.5
    return dict(name=name,label=label,eye=camera.C.tolist(),target=(camera.C+distance*camera.R[2]).tolist(),
                world_up=(-camera.R[1]).tolist(),width_m=float(distance*width/fx),width=width,height=height,
                reference=key,source_dimensions=size,source_crop=crop,sensor_fit='HORIZONTAL',pixel_aspect_y=aspect,
                blender_pixel_aspect_x=max(1.,1/aspect),blender_pixel_aspect_y=max(1.,aspect),shift_x=(width/2-cx)/width,
                shift_y=(cy-height/2)*aspect/width,principal_point_edge_px=[cx,cy],skew_px=float(camera.K[0,1]),
                photo_focal_x_px=fx,projection_world_to_photo_pixel_centres=(intrinsic@camera.R@np.column_stack([np.eye(3),-camera.C])).tolist())

def study(name,label,target,offset,width,size=(960,620)):
    return dict(name=name,label=label,eye=(np.array(target)+offset).tolist(),target=list(target),width_m=width,width=size[0],height=size[1])

def make():
    f=WingFrame();w=f.width;d=f.depth;h=f.eave;rz=f.ridge
    door=(f.portal_left+f.portal_right)/2
    return [study('overview','院面与连接廊',[12.44,.30*d,2.85],[-11,-32,8.6],30.75,(1024,680)),
            original(f,'album'),original(f,'design'),
            study('oak-entrance','中部门洞与外露木架',[door,.05,.64*h],[-1.4,-10,.45],7.3),
            study('front-dormers','院面三座屋窗',[.50*w,.73,.63*rz],[-.9,-19,3.6],16.5),
            study('return-windows','返墙窗与阶进腰枋',[0,.55*d,.56*h],[-9,-1.9,.55],7.85),
            study('hip-dormers','髋坡两座屋窗',[.85,.66*d,.64*rz],[-9,-2.3,4.2],6.5),
            study('roof-joint','左髋线与圆脊瓦',[.69*f.left_hip,.34*d,.71*rz],[-7.8,-8.4,7.9],9.85),
            study('connecting-passage','右侧连接廊',[22.01,1.08,3.69],[1.3,-14,2.9],16.94)]

if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
