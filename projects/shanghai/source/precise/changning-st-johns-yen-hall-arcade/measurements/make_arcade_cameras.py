"""Export the three original camera stations and six views of the measured arcade."""
from pathlib import Path
import json,numpy as np
HERE=Path(__file__).parent
def study(name,label,target,eye,width):return dict(name=name,label=label,target=target,eye=eye,width_m=width,width=960,height=640)
def make():
    data=json.loads((HERE/'arcade-registration.json').read_bytes())['stations']
    cameras=[study('overview','七间三层廊与四间二层廊',[0,1.9,7.4],[15,-62,18],56.)]
    for k,label in [('west-ground','校档西侧地面站'),('east-ground','校档东侧地面站'),('school-aerial','校档东南航摄站')]:
        d=data[k];w,h=d['size'];R=np.array(d['R']);C=np.array(d['C']);K=np.array(d['K']);cx=K[0,2]+.5;cy=K[1,2]+.5
        distance=np.dot(R[2],np.array([0,0,7.2])-C)
        cameras.append(dict(name=k,label=label,eye=C.tolist(),target=(C+distance*R[2]).tolist(),world_up=(-R[1]).tolist(),width_m=distance*w/K[0,0],width=w,height=h,reference=k,source_crop=[0,0,w,h],source_dimensions=[w,h],sensor_fit='HORIZONTAL',pixel_aspect_y=1.,blender_pixel_aspect_x=1.,blender_pixel_aspect_y=1.,shift_x=(w/2-cx)/w,shift_y=(cy-h/2)/w,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=d['P']))
    cameras.extend([study('three-storeys','草坪西段三层红砖券',[-9.3,.3,7.1],[-19,-36,11],31.0),study('low-arcade','东段二层廊与女儿墙',[13.3,.5,5.8],[21,-25,8],21.0),study('lattice','交错菱孔陶栏',[-15.2,.2,5.85],[-15,-8.0,6.4],5.2),study('roof-step','七间与四间相接的落顶',[6.4,2.4,13.25],[14,-15,20],16.0),study('springing','红券与灰砖墩的承接',[-14.7,0,3.27],[-16,-9,4.0],7.2)])
    return cameras
if __name__=='__main__':(HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
