"""Build five architectural study views and four original photograph cameras."""
from pathlib import Path
import json
import numpy as np

HERE=Path(__file__).parent
def view(name,label,target,eye,width):
    return dict(name=name,label=label,target=target,eye=eye,width_m=width,width=1080,height=648)
def make():
    cams=[view('overview','复旦老校门全景',[0,.22,2.59],[-4.3,-14.,5.1],10.55),
          view('threshold','木门与中央踏步',[0,.05,1.36],[-2.15,-6.8,2.08],6.0),
          view('inscribed-front','復旦大學正匾',[-.06,-.36,3.46],[-1.4,-5.8,3.77],3.9),
          view('inscribed-reverse','敬業樂群背匾',[0,.40,3.48],[.45,6.50,3.80],4.00),
          view('ridge','灰瓦正脊与翘檐',[0,.30,3.77],[6.8,-9.,7.1],9.2)]
    controls=json.loads((HERE/'four-gate-stations.json').read_bytes())['stations']
    labels=['2006年夏 · 正面斜照','校方招生资料 · 正面','校方明信片文章 · 另一斜角','校园内侧 · 敬業樂群匾']
    for (key,cam),label in zip(controls.items(),labels):
        x0,y0,x1,y1=cam['crop'];w=x1-x0;h=y1-y0
        k=np.array(cam['K']);k[0,2]-=x0;k[1,2]-=y0
        r=np.array(cam['R']);c=np.array(cam['C']);d=float(np.dot(r[2],np.array([0.,0.,2.65])-c))
        aspect=k[0,0]/k[1,1];cx=k[0,2]+.5;cy=k[1,2]+.5
        p=k@np.column_stack((r,-r@c))
        cams.append(dict(name=key,label=label,eye=c.tolist(),target=(c+r[2]*d).tolist(),world_up=(-r[1]).tolist(),width_m=d*w/k[0,0],width=w,height=h,reference=key,source_crop=cam['crop'],source_dimensions=[cam['width'],cam['height']],sensor_fit='HORIZONTAL',pixel_aspect_y=aspect,blender_pixel_aspect_x=max(1.,1./aspect),blender_pixel_aspect_y=max(1.,aspect),shift_x=(w/2-cx)/w,shift_y=(cy-h/2)*aspect/w,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=p.tolist()))
    return cams
if __name__=='__main__':(HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
