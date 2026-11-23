"""Emit three perspective-matched original stations and six architectural views."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).resolve().parent
def study(name,label,target,eye,width):return dict(name=name,label=label,target=target,eye=eye,width_m=width,width=960,height=640)
def make():
    stations=json.loads((HERE/'church-registration.json').read_bytes())['stations']
    cams=[study('overview','七竖扇尖窗山墙与扶壁',[0,.7,9.1],[11,-33,12],32.0)]
    for n,t,crop in [('fayhoo2017','2017年衡山路正面',[1200,116,2855,1950]),('livelikerw2013','2013年右斜面',[1550,463,3440,2250]),('szalai2018','2018年院中近照',[405,45,2640,1826])]:
        c=stations[n];K,R,C=map(np.asarray,[c['K'],c['R'],c['C']]);d=R[2]@(np.array([0,0,11.0])-C)
        l,top,right,bottom=crop;w=right-l;h=bottom-top;K[0,2]-=l;K[1,2]-=top;cx,cy=K[0,2]+.5,K[1,2]+.5
        cams.append(dict(name=n,label=t,eye=C.tolist(),target=(C+d*R[2]).tolist(),world_up=(-R[1]).tolist(),width_m=d*w/K[0,0],width=w,height=h,reference=n,source_crop=crop,source_dimensions=c['size'],sensor_fit='HORIZONTAL',pixel_aspect_y=1.,blender_pixel_aspect_x=1.,blender_pixel_aspect_y=1.,shift_x=(w/2-cx)/w,shift_y=(cy-h/2)/w,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=(K@np.column_stack((R,-R@C))).tolist()))
    cams.extend([study('seven-lights','七扇铅条花窗',[0,.4,9.7],[1,-16,9.5],7.15),
                 study('foils','双圆花饰与中央拱梃',[0,.4,11.35],[.6,-7.8,11.55],3.7),
                 study('buttress','山墙支墩与砖砌退台',[3.45,.3,11.1],[12,-8.5,13.4],7.6),
                 study('arch-moulding','尖券分层石线',[0,.5,11.80],[-5,-8,13.52],8.25),
                 study('stoop','尖窗下的门厅与台阶',[0,.1,2.9],[5.5,-14,4.6],10.4)])
    return cams
if __name__=='__main__':(HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
