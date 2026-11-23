"""Register the model viewer and editable cameras to three photographed views of Schereschewsky Hall."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import rq
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
    first=json.loads((HERE/'tower-stations.json').read_bytes())['stations']
    third=json.loads((HERE/'school-court-station.json').read_bytes())
    an=[('street','修缮后街面钟楼',first['street'],[0,0,8.9]),
        ('court','2004年院内望钟楼',first['court'],[0,12.5,7.3]),
        ('school-court','校方南院望向中跨',third,[0,46.4,6.6])]
    cams=[view('overview','怀施堂南翼和中央院落',[57,-72,46],[0,19,5],69)]
    for k,label,d,focus in an:
        cams.append(registered(k,label,dict(projection=d['P'],frame=d['image_size']),[0,0,*d['image_size']],focus))
    cams.extend([view('street-clock','临街方钟、花窗及校名牌',[4.5,-14.6,15.2],[0,0,12.5],10.2,860),
                 view('court-clock','院内方钟与翘角瓦顶',[-5.5,29,18.1],[0,12.5,14.4],10.8,860),
                 view('portal','韬奋楼额与穿堂券门',[-3.4,-11.4,2.5],[0,.45,3.9],8.1,850),
                 view('gallery','北望东侧两层院廊',[-5.9,15.2,2.79],[9.9,32,3.7],16.8,810),
                 view('pavilion','北面中舱三圆饰与山花',[-2.3,30,4.6],[-.22,46.4,6.6],14.5,810),
                 view('roof','四坡钟楼和主翼屋脊',[25,-28,29],[0,7,13.1],30)])
    return cams
if __name__=='__main__':
    (HERE.parent/'source/cameras.json').write_text(json.dumps(make(),ensure_ascii=False,indent=2)+'\n')
