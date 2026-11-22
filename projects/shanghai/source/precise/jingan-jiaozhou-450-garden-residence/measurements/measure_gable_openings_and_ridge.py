"""Transfer the observed street openings and roof profiles into the arcade survey."""
from pathlib import Path
import json,numpy as np
from scipy.optimize import brentq
from PIL import Image
from refit_west_street_views import yz
import argparse
p=argparse.ArgumentParser();p.add_argument("garden_photo",type=Path);p.add_argument("output",type=Path);args=p.parse_args()
D=Path(__file__).parent
cams=json.loads((D/'west-cameras.json').read_bytes())
P=np.asarray(cams['cameras']['2020-side']['P'])
Q=np.asarray(json.loads((D/'arcade-cameras.json').read_bytes())['13']['P'])
# The open light behind the branches gives only part of the north shutter.
windows=[('Lower north',[(277,382),(323,387),(317,446),(269,438)],15,1),('Lower centre',[(414,391),(455,397),(453,452),(411,449)],14,1),
 ('Lower south',[(512,401),(563,405),(562,463),(509,459)],13,2),('Attic north',[(397,248),(436,255),(435,287),(398,282)],9,1),
 ('Attic south',[(483,259),(523,265),(521,300),(484,297)],9,1)]
wins=[]
for name,uv,n,leaves in windows:
 q=np.array([yz(P,v)for v in uv]);y0=q[[1,2],0].mean();y1=q[[0,3],0].mean();z0=q[2:,1].mean();z1=q[:2,1].mean();wins.append(dict(label=name,uv=uv,yz=[y0,z0,y1,z1],louvre_rows=n,leaves=leaves,reading='中层斜百叶可见；高处两洞下缘有架空线遮挡，扇数与片数按清晰段近似。'))
# Native scanline at the roof against the sky. A few leaf clusters at the west
# end were excluded before sampling the straight unobstructed middle section.
photo=np.asarray(Image.open(args.garden_photo).convert('RGB')).mean(2)
trace=[]
for u in range(260,461,4):
 column=photo[:,u-1:u+2].mean(1)
 v=next(v for v in range(190,335) if column[v]<150 and (column[v+1:v+5]<178).all())
 trace.append([u,v])
coef=np.polyfit(*np.array(trace).T,1)
m=(14.98-10.437)/(9.17-4.55)
def zroof(y):return 10.437+m*(y-4.55)
def solve(x):
 def gap(y):
  p=Q@[x,y,zroof(y),1.];u,v=p[:2]/p[2];return v-np.polyval(coef,u)
 return brentq(gap,7.,17.)
yst=solve(0)
# Crown of the small return arch, under the six pale turned balusters. Low
# opening legs are hidden behind the street wall.
R=np.asarray(cams['cameras']['rail-detail-3']['P']);arc=[(321,431),(340,413),(358,402),(377,396),(397,398),(418,407),(438,421),(452,435)]
xr=np.array([yz(R,p,.005)for p in arc])
roof=dict(native_skyline=trace,ridge_line_uv=np.asarray(coef).tolist(),ridge_y=yst,ridge_z=zroof(yst),sloping_roof_tan=m,dormer_break=[[4.55,10.437],[9.17,14.98]],independent_street_gable=cams['joint_control_points'][0])
for w in wins: print(w['label'],np.around(w['yz'],2))
print('roof',yst,zroof(yst),'arc',xr.round(3))
out=dict(axes='X along the garden front to the right, Y into the house, Z above the porch landing. West gable viewed from the street.',west_openings=wins,roof=roof,west_side_arch=dict(native_points=arc,projected_yz=xr.tolist(),obscuration='街墙遮住两拱脚。上缘及放射砖可见，以下直边和拱肩按同廊规则估形。'))
args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
