"""Resolve the courtyard station and the independently geolocated, restricted winter view for each row hypothesis."""
from pathlib import Path
import json,math,numpy as np
HERE=Path(__file__).absolute().parent
def camera_sets():
    pool=json.loads((HERE/'registered-stair-stations.json').read_bytes())['stations']
    return {k:pool[k]for k in ['district-archive','press-archive','road-centre']}
def make():
    def view(k,label,c,t,span):return dict(name=k,label=label,eye=c,target=t,width_m=span,width=1080,height=648)
    result=[view('overview','临街楼梯间与上檐',[-16,-29,11],[2.5,.1,10.6],24),view('stepped-lights','三联阶梯钢窗',[1.2,-12,11],[2.4,.1,11.4],8.1),view('oculus','底层圆形开口',[.7,-8.2,2.6],[2,.1,3.1],4.2),view('eyebrow','顶层混凝土遮檐',[-6,-10,20.2],[2.1,.2,16.5],8.3),view('lower-sash','下窗与勒脚连接',[7,-11,6.9],[2.4,.12,6.1],8.4),view('side-return','水泥腰线短侧返',[-8,-8,15],[1.4,.6,16.3],9)]
    for (key,cam),label in zip(camera_sets().items(),['区规资局档案斜照','周到上海刊载的旧院正照','2020年2月街面复测']):
        x,y,a,b=cam['crop'];w,h=a-x,b-y;k=np.array(cam['K'],float);k[0,2]-=x;k[1,2]-=y;r=np.array(cam['R']);c=np.array(cam['C']);d=float((np.array([2.55,.1,10.6])-c)@r[2]);aspect=k[0,0]/k[1,1];cx=k[0,2]+.5;cy=k[1,2]+.5
        result.append(dict(name=key,label=label,eye=c.tolist(),target=(c+r[2]*d).tolist(),world_up=(-r[1]).tolist(),width_m=d*w/k[0,0],width=w,height=h,reference=key,source_crop=cam['crop'],source_dimensions=[cam['width'],cam['height']],sensor_fit='HORIZONTAL',pixel_aspect_y=aspect,blender_pixel_aspect_x=max(1.,1./aspect),blender_pixel_aspect_y=max(1.,aspect),shift_x=(w/2-cx)/w,shift_y=(cy-h/2)*aspect/w,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=(k@np.c_[r,-r@c]).tolist()))
    return result
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
