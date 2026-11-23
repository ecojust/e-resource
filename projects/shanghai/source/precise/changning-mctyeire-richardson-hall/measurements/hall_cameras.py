"""Register the model viewer and editable cameras to the visitor agency, district and entrance photographs."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import rq
from frontage import matrix
HERE=Path(__file__).resolve().parent
def registered(key,label,station,crop,focus):
    projection=np.asarray(station['projection'],dtype=float)
    scale=np.linalg.norm(projection[2,:3]);projection=projection/scale
    intrinsic,axes=rq(projection[:,:3]);signs=np.diag(np.where(np.diag(intrinsic)<0,-1.,1.))
    intrinsic=intrinsic@signs;axes=signs@axes
    fx,fy=intrinsic[0,0],intrinsic[1,1]
    eye=-np.linalg.solve(projection[:,:3],projection[:,3])
    r=axes[2];depth=float((np.array(focus)-eye)@r)
    w,h=crop[2]-crop[0],crop[3]-crop[1]
    cx=intrinsic[0,2]+.5-crop[0];cy=intrinsic[1,2]+.5-crop[1];aspect=fx/fy
    return dict(name='photo-'+key,label=label,eye=eye.tolist(),target=(eye+depth*r).tolist(),world_up=(-axes[1]).tolist(),
                width_m=float(w*depth/fx),width=w,height=h,reference=key,source_dimensions=station['frame'],source_crop=list(crop),sensor_fit='HORIZONTAL',
                pixel_aspect_y=aspect,blender_pixel_aspect_x=max(1.,1/aspect),blender_pixel_aspect_y=max(1.,aspect),
                shift_x=float((w/2-cx)/w),shift_y=float((cy-h/2)*aspect/w),principal_point_edge_px=[cx,cy],
                skew_px=float(intrinsic[0,1]),photo_focal_x_px=float(fx),projection_world_to_photo_pixel_centres=projection.tolist())
def view(key,label,eye,focus,width,height=750):
    return dict(name=key,label=label,eye=eye,target=focus,width_m=width,width=1080,height=height)
def make():
    cams=[view('overview','草坪教学翼与后礼堂',[56,-90,49],[-1,18,5],83),
          registered('lawn','文旅正面照 · 五段教室窗与十一扇屋窗',matrix(),[1,103,1149,459],[0,.6,6.2])]
    for station in json.loads((HERE/'oblique-stations.json').read_bytes())['stations']:
        key=station['name'];cams.append(registered(key,{'lawn-gathering':'区府草坪合影机位','lawn-bench':'区府草坪长椅机位'}[key],station,station['native_crop_xyxy'],[0,0,6.]))
    station=json.loads((HERE/'vestibule-station.json').read_bytes())
    cams.append(registered('vestibule','2017年门厅 · 灯冠与礼堂三门',station,[150,0,1460,1067],[0,13.2,4.35]))
    theatre=json.loads((HERE/'auditorium-station.json').read_bytes())
    theatre['projection']=theatre['native_projection'];theatre['frame']=theatre['native']
    cams.append(registered('auditorium','2017年礼堂 · 中央走道与楼座',theatre,[0,0,*theatre['frame']],[0,25.79,3.6]))
    cams.extend([view('roof','临草坪三坡屋窗与两端女儿墙',[-9,-24,19],[0,1,12.2],33),
                 view('portal','门楣三面盾饰与哥特花窗',[4.4,-11,5.0],[0,0,4.2],7.85,880),
                 view('hall-gallery','礼堂中央走道与后楼座',[2.6,44.2,1.56],[-2,24.8,3.5],24),
                 view('hall-window','礼堂侧壁的尖券彩色玻璃',[-8.8,34,3.1],[-16.2,35.5,4.4],8.5,850),
                 view('rear-volume','倒T形平面与后礼堂',[-60,85,48],[-1,24,5.4],77)])
    return cams
if __name__=='__main__':
    cameras=make();(HERE.parent/'source/cameras.json').write_text(json.dumps(cameras,ensure_ascii=False,indent=2)+'\n')
    print([(c['name'],round(c['width_m'],2)) for c in cameras])
