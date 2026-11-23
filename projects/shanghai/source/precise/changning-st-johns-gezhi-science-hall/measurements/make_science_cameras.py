"""Export the three registered photographs and six additional views of the west elevation."""
from pathlib import Path
import json,numpy as np
HERE=Path(__file__).parent
def study(name,label,target,eye,width):return dict(name=name,label=label,target=target,eye=eye,width_m=width,width=960,height=640)
def make():
    data=json.loads((HERE/'science-registration.json').read_bytes())['stations']
    cameras=[study('overview','格致楼西院券廊全景',[-3.7,1.1,6],[11,-43,15],43.)]
    for k,label in [('west-school-ground','校方近正面摄影'),('west-oblique','西南斜看院廊'),('school-aerial','校方斜航摄')]:
        d=data[k];w,h=d['size'];R=np.array(d['R']);C=np.array(d['C']);K=np.array(d['K']);cx=K[0,2]+.5;cy=K[1,2]+.5
        distance=np.dot(R[2],np.array([0,0,7.2])-C)
        cameras.append(dict(name=k,label=label,eye=C.tolist(),target=(C+distance*R[2]).tolist(),world_up=(-R[1]).tolist(),width_m=distance*w/K[0,0],width=w,height=h,reference=k,source_crop=[0,0,w,h],source_dimensions=[w,h],sensor_fit='HORIZONTAL',pixel_aspect_y=K[0,0]/K[1,1],blender_pixel_aspect_x=1.,blender_pixel_aspect_y=K[0,0]/K[1,1],shift_x=(w/2-cx)/w,shift_y=(cy-h/2)*K[0,0]/K[1,1]/w,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=d['P']))
    cameras.extend([study('west-gallery','九开间西院立面',[-3.7,0,5.9],[-8,-37,9],39),study('inscribed-door','三字横匾与阶梯',[0,.4,3.6],[2,-13,5.2],10.5),study('eyebrow-eaves','屋檐下起翘的小屋面',[7,.5,13.3],[14,-16,18],14),study('window-guards','券窗与几何栏扇',[0,0,7.85],[2,-9,8.2],7),study('round-window','端部圆窗',[-16.8,0,7.7],[-19,-10,8.2],7.6)])
    return cameras
if __name__=='__main__':(HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
