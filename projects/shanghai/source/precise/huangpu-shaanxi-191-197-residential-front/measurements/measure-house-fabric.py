from pathlib import Path
import json,sys,numpy as np
from PIL import Image
from hashlib import sha256
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('photo',type=Path);args=parser.parse_args()
s=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(s/'source'))
from west_photo_plane import on_wall
img=Image.open(args.photo); a=np.array(img)
def point(q,y=0.):return [round(i,5) for i in on_wall(*q,y)]
def rect(uv,y):
 left,top,right,bottom=uv
 corners=[(left,top),(right,top),(right,bottom),(left,bottom)]
 world=np.array([point(c,y) for c in corners])
 return dict(photo_rect=uv,face_y_m=y,left=round(world[[0,3],0].mean(),5),right=round(world[[1,2],0].mean(),5),top=round(world[:2,2].mean(),5),bottom=round(world[2:,2].mean(),5))
cornices=[[1500,1430],[2380,1436]];ends=[[785,1250],[3000,1250]]
eaves=[[980,819],[2900,854]]; roof_top=[[980,767],[2900,772]]
patches=[]
for x,y in [(1179,1343),(1384,1326),(1354,1372),(2205,1351),(2434,1311),(2502,1288),(2580,1377)]:
 patch=a[y-9:y+10,x-9:x+10].reshape(-1,3)
 patches.append({'center_px':[x,y],'median_rgb':np.median(patch,axis=0).astype(int).tolist()})
d=dict(photo= {'title':'陕西南路195号','author':'WQL','date':'2018-06-10','dimensions':img.size,'sha256':sha256(args.photo.read_bytes()).hexdigest()}, lower_windows=[rect([1161,1632,1479,1862],.11),rect([2015,1640,2321,1868],.11)], envelope=dict(wall_ends_px=ends,wall_ends_x_m=[point(q)[0] for q in ends],string_course_px=cornices,string_course_z_m=[point(q,-.055)[2] for q in cornices],eaves_front_px=eaves,eaves_front_y_m=-.65,eaves_front_z_m=[point(q,-.65)[2] for q in eaves],visible_tile_upper_px=roof_top,represented_rear_y_m=2.83,upper_z_m=[point(q,2.83)[2] for q in roof_top]),roughcast_samples=patches, limits=['Roof projection, return thickness and tile depth are working estimates. The modeled roof stops after the photographed street slope.','The lower window edge disappears behind the boundary wall. The lower dark pane extends only to the last visible band.','The separate 2018 court wall model includes three lamps and the observed length of railing. The public pedestrian barrier, trees and telephone kiosks are omitted.'])
(s/'measurements/house-fabric-and-roof.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
