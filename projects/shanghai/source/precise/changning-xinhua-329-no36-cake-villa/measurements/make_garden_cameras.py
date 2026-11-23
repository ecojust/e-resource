"""Export the two photographic projection matrices and seven inspection views."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).resolve().parent
def study(name,label,target,eye,width):
    return dict(name=name,label=label,target=target,eye=eye,width_m=width,width=960,height=640)
def make():
    book=json.loads((HERE/'garden-registration.json').read_bytes())
    cams=[study('overview','庭院入口、双层弧面与瓦檐',[0,2.3,4.0],[7.5,-24.5,8.1],20.8)]
    for n,title,crop in [('historic-garden','资料旧照的庭院正面',[3,119,950,739]),('district-2024','长宁区所刊彩照的院中视点',[147,66,458,278])]:
        c=book['stations'][n];K,R,C=map(np.asarray,[c['K'],c['R'],c['C']]);d=R[2]@(np.array([0,1,3.7])-C)
        l,t,rr,bb=crop;w=rr-l;h=bb-t;K[0,2]-=l;K[1,2]-=t;cx,cy=K[0,2]+.5,K[1,2]+.5
        cams.append(dict(name=n,label=title,target=(C+d*R[2]).tolist(),eye=C.tolist(),world_up=(-R[1]).tolist(),width_m=d*w/K[0,0],width=w,height=h,reference=n,source_dimensions=c['size'],source_crop=crop,sensor_fit='HORIZONTAL',pixel_aspect_y=1.0,blender_pixel_aspect_x=1.,blender_pixel_aspect_y=1.,shift_x=(w/2-cx)/w,shift_y=(cy-h/2)/w,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=(K@np.column_stack((R,-R@C))).tolist()))
    cams.extend([study('door','分格玻璃门与踏步',[0,-.06,1.59],[2.1,-7.8,2.02],4.8),
          study('glass-blocks','格砖窗与灰框',[-2.16,.26,1.85],[-4.2,-6.8,2.3],4.8),
          study('arcade','三间开敞上廊与栏杆',[0,.10,4.95],[1.2,-11.,5.4],8.4),
          study('return','圆弧转侧与砖间壁',[5.7,2.1,4.0],[16.,-11.,5.2],11.8),
          study('roof','分坡瓦脊与出檐',[0,4.0,6.4],[10.,-12.,13.2],18.9),
          study('steps','门前踏步及落地窗裙',[0,0,.63],[-3.8,-8.,2.4],7.4)])
    return cams
if __name__=='__main__':(HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
