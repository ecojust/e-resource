"""Measure the independently visible mullions and vents of the long historical facade."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.signal import find_peaks
S=Path(__file__).resolve().parents[1]

sys.path.insert(0,str(S/'source'))
from rosholt_front_plane import PROJECTION
path=Path(sys.argv[1]);out=Path(sys.argv[2])
size=(1510,660);scale=32.;ox=736;oz=128
H=PROJECTION[:,[0,2,3]]@np.linalg.inv(np.array([[scale,0,ox],[0,-scale,oz],[0,0,1.]]))
H/=H[2,2]
im=Image.open(path)
rect=np.asarray(im.convert('L').transform(size,Image.Transform.PERSPECTIVE,H.flat[:8],Image.Resampling.BICUBIC),float)
# Coordinates in the metric rectification, at 32 px/m, generated before fitting the lights.
edges=[(178,276),(303,401),(429,526),(553,652),(680,817),(854,942),(982,1065),(1108,1190),(1236,1320)]
bands=[(190,248),(300,359),(415,470)]
columns=[(170,16),(296,15),(422,15),(548,15),(674,15),(848,17),(974,16),(1100,16),(1229,17),(1356,17)]
def source_uv(u,v):
 z=H@np.array([u,v,1]);return (z[:2]/z[2]).round(3).tolist()
def peaks(vec,distance,prom):
 pp,info=find_peaks(vec,distance=distance,prominence=prom)
 return pp.tolist()
items=[];vents=[]
for row,(t,b) in enumerate(bands):
 for i,(l,r) in enumerate(edges):
  if row==2 and i==4:continue
  g=rect[t:b+1,l:r+1];xs=peaks(np.percentile(g[13:-4],65,axis=0),9,36)
  # Upper-band operable sash diagonals are independently traced, avoiding a false stationary mullion.
  if row==0:xs=[[15,43,70],[13,40,67],[9,37,64],[9,36,64],[3,28,55,83,109],[3,30,58],[27,55],[26,54],[23,51]][i]
  yy=peaks(np.median(g[:,6:-6],axis=1),5,28)
  offs=[int(np.argmax(np.median(g[y0:y1,5:-5],axis=1)))+y0 for y0,y1 in [(12,31),(35,min(len(g)-2,52))]]
  layout=dict(bay=i+1,tier_from_top=row+1,rectified_bounds=[l,t,r,b],corners_px=[source_uv(*q)for q in [(l,t),(r,t),(r,b),(l,b)]],mullions_rectified_x_px=[l+x for x in xs if 2<x<r-l-2],transoms_rectified_y_px=[t+y for y in offs],source_profile_transom_peaks=yy)
  items.append(layout)
  if row<2 or i in (0,1,2):
   cent=[(l+r)//2] if i!=4 else [705,783]
   for cx in cent:
    cy=[275,386,497][row];patch=rect[cy-5:cy+8,cx-11:cx+12]
    if patch.mean()<120:continue
    mask=patch<min(137,np.percentile(patch,65)-40);Y,X=np.where(mask)
    if len(X)<8:continue
    v=[int(X.min()+cx-11),int(Y.min()+cy-5),int(X.max()+cx-11+1),int(Y.max()+cy-5+1)]
    if v[2]-v[0]<=20 and v[3]-v[1]<=9:vents.append(dict(bay=i+1,tier=row+1,rectified_bounds=v))
data=dict(reference='University of Bristol Historical Photographs of China, Ro-s018, circa 1938',sha256='8a22ced1ee705ff3a087edd39036a4027824dff0fb40e4d3d2b0d85787067a61',rectification=dict(pixel_x=ox,pixel_z=oz,pixels_per_m=scale,homography_rectified_to_print=H.tolist()),regular_windows=items,photographed_vent_slots=vents,round_front_piers=columns,central_dark_opening_px=[[581,422],[650,424],[653,501],[585,501]],open_top_hung_lights=[[[168,191],[196,193],[204,208],[177,205]],[[501,239],[526,241],[534,253],[508,252]]],stair_glass=dict(near_strip_rectified=[90,161,157,512],far_strip_rectified=[1369,185,1402,480],glass_block_pitch_m=.18,reading='Light structural bars bound panels of small textured translucent glass units. The individual glass block pitch is an estimate.'),limits='The front centre has a fourth, lower glazed portion behind the hedge. Only the visible part of its dark bay is reconstructed. Dark print tone varies with exposure. Absolute window recess estimates do not come from a survey.')
out.write_text(json.dumps(data,indent=2)+'\n')
print(len(items),len(vents))
