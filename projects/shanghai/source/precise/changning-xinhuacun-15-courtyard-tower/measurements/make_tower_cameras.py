"""Build six architectural study views and three original photograph cameras."""
from pathlib import Path
import json
import numpy as np

HERE=Path(__file__).parent
def view(name,label,target,eye,width):
    return dict(name=name,label=label,target=target,eye=eye,width_m=width,width=1080,height=648)
def make():
    cams=[view('overview','方塔与院廊',[4.2,2.4,7.0],[16.,-26.,12.],27.1),
          view('court-windows','院面三层旧窗',[0,0,8.25],[5.8,-14.,9.],14.1),
          view('gallery','侧廊栏板与白格窗',[7.7,3.5,5.50],[16.,-13.,7.9],13.5),
          view('north-stack','北面三层钢木窗',[0,3.,8.20],[-4.,17.,8.3],14.5),
          view('hip-roof','短脊、烟囱与檐沟',[0,1.2,12.5],[12.,-12.,18.9],13.0),
          view('door','绿色双扇与错缝砖角',[-.1,-.07,2.6],[4.,-10.,3.8],8.9)]
    controls=json.loads((HERE/'three-tower-stations.json').read_bytes())['stations']
    labels=['院内题注15号 · 高参图17','长宁路599号 · 2015年12月','北门斜站 · 高参图13']
    for (key,cam),label in zip(controls.items(),labels):
        x0,y0,x1,y1=cam['crop'];w=x1-x0;h=y1-y0
        k=np.array(cam['K']);k[0,2]-=x0;k[1,2]-=y0
        r=np.array(cam['R']);c=np.array(cam['C']);d=float(np.dot(r[2],np.array([2.,1.,8.])-c))
        aspect=k[0,0]/k[1,1];cx=k[0,2]+.5;cy=k[1,2]+.5
        p=k@np.column_stack((r,-r@c))
        cams.append(dict(name=key,label=label,eye=c.tolist(),target=(c+r[2]*d).tolist(),world_up=(-r[1]).tolist(),width_m=d*w/k[0,0],width=w,height=h,reference=key,source_crop=cam['crop'],source_dimensions=[cam['width'],cam['height']],sensor_fit='HORIZONTAL',pixel_aspect_y=aspect,blender_pixel_aspect_x=max(1.,1./aspect),blender_pixel_aspect_y=max(1.,aspect),shift_x=(w/2-cx)/w,shift_y=(cy-h/2)*aspect/w,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=p.tolist()))
    return cams
if __name__=='__main__':(HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
