"""Create three original projection cameras and six dimensional studies."""
from pathlib import Path
import json,numpy as np
D=Path(__file__).resolve().parent
def view(name,label,target,eye,width):return dict(name=name,label=label,target=target,eye=eye,width_m=width,width=960,height=640)
def make():
 fit=json.loads((D/'seaman-registration.json').read_bytes());cams=[view('overview','四合院外廊与东风楼门额',[35,23,4.3],[55,-79,61],97)]
 for name,label in [('court-colonnade','校方院廊近照'),('east-wind-entrance','校方东风楼门额'),('school-aerial','校方全院航照')]:
  s=fit['stations'][name];R=np.array(s['R']);C=np.array(s['eye']);K=np.array(s['K']);iw,ih=s['size'];cx=K[0,2]+.5;cy=K[1,2]+.5
  dist={'court-colonnade':15.,'east-wind-entrance':16.,'school-aerial':99.}[name]
  cams.append(dict(name=name,label=label,eye=C.tolist(),target=(C+dist*R[2]).tolist(),world_up=(-R[1]).tolist(),width_m=dist*iw/K[0,0],width=iw,height=ih,reference=name,source_crop=[0,0,iw,ih],source_dimensions=[iw,ih],sensor_fit='HORIZONTAL',pixel_aspect_y=1.,blender_pixel_aspect_x=1.,blender_pixel_aspect_y=1.,shift_x=(iw/2-cx)/iw,shift_y=(cy-ih/2)/iw,principal_point_edge_px=[cx,cy],projection_world_to_photo_pixel_centres=s['P']))
 c=fit['parameters']['entrance axis'];z=fit['parameters']['sign centre']
 cams.extend([view('east-wind-plaque','东风楼匾与红砖线脚',[c,0,z],[c+.5,-8.3,z+.1],6.0),view('passage','街侧券门与穿堂',[c,2.,2.3],[c-3.8,-12.,2.8],12.5),view('gallery-capitals','院廊石脚与层叠砖托',[58.,35.9,2.1],[50.7,29,2.65],10.3),view('court-stairs','四级踏步与廊后白墙',[56.5,35.2,1.2],[52,25.8,3.15],13.1),view('front-roofs','瓦脊与前檐四座横坡',[35.8,8.4,8.6],[53.5,-50.2,38.5],90.2)])
 return cams
if __name__=='__main__':(D.parent/'source/cameras.json').write_text(json.dumps(make(),indent=2,ensure_ascii=False)+'\n')
