"""Add three registered views to the existing lawn facade camera set."""
from pathlib import Path
import json
import numpy as np

HERE=Path(__file__).parent
def view(name,label,target,eye,width):
    return dict(name=name,label=label,target=target,eye=eye,width_m=width,width=1080,height=648)
def make():
    cams=[view('front','草坪院面全景',[1.5,-1.0,7.8],[-1.0,-92,16.5],94),
          view('oblique','院落与东南返翼',[-.8,-1.4,7.6],[-59,-91,29],94),
          view('above','屋面与两个转角',[1.,1.5,7.0],[-30,-63,77],92),
          view('arcade','六孔券廊与柱脚',[-20,2.5,3.2],[-29,-27,7.1],27),
          view('leaded-entry','门廊石雕与菱形铅窗',[0,.2,4.4],[-8.5,-24,6.3],22),
          view('return-window','东南返翼的双开窗与屋面窗',[36.65,-7.4,7.5],[8,-10,9],27)]
    controls=json.loads((HERE/'lawn-return-stations.json').read_bytes())['stations']
    labels=['Ctny 草坪斜照','Ctny 全景的返翼局部','Historic Shanghai 草坪侧照']
    for (key,cam),label in zip(controls.items(),labels):
        x0,y0,x1,y1=cam['crop'];w=x1-x0;h=y1-y0
        k=np.array(cam['K']);k[0,2]-=x0;k[1,2]-=y0
        r=np.array(cam['R']);c=np.array(cam['C']);d=float(np.dot(r[2],np.array([36.,-7.5,7.])-c))
        aspect=k[0,0]/k[1,1];cx=k[0,2]+.5;cy=k[1,2]+.5
        p=k@np.column_stack((r,-r@c))
        cams.append(dict(name=key,label=label,eye=c.tolist(),target=(c+r[2]*d).tolist(),world_up=(-r[1]).tolist(),width_m=d*w/k[0,0],width=w,height=h,reference=key,source_crop=cam['crop'],source_dimensions=[cam['width'],cam['height']],sensor_fit='HORIZONTAL',pixel_aspect_y=aspect,blender_pixel_aspect_x=max(1.,1./aspect),blender_pixel_aspect_y=max(1.,aspect),shift_x=(w/2-cx)/w,shift_y=(cy-h/2)*aspect/w,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=p.tolist()))
    return cams
if __name__=='__main__':(HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
