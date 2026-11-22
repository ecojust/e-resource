"""Fit both independent published photographs using the shaft corners, cap returns and plinths."""
from pathlib import Path
import json
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
root=Path(__file__).resolve().parent
# Observations in ORIGINAL image pixels, master from 2023, oblique from opening day.
a={'L:ol/base':(143,434),'L:ir/base':(260,433),'R:il/base':(542,436),'R:or/base':(665,435),
'L:ol/head':(142,144),'L:ir/head':(257,142),'R:il/head':(545,140),'R:or/head':(665,140),
'L:ol/top':(111,55),'L:ir/top':(266,49),'L:rB/top':(311,98),'R:il/top':(524,47),'R:or/top':(697,46),'R:lB/top':(509,103),
'L:ol/ground':(143,505),'L:ir/ground':(261,506),'R:il/ground':(542,514),'R:or/ground':(665,512),
'R:lB/head':(528,159)}
b={'L:ol/head':(54,224),'L:ir/head':(149,231),'R:il/head':(302,247),'R:or/head':(348,251),
'R:il/base':(302,389),'R:or/base':(347,378),'L:ol/top':(40,156),'L:ir/top':(171,180),'R:il/top':(302,202),'R:or/top':(359,214),'R:lB/top':(263,220),'R:lB/head':(278,254)}
# Paper/stone units calibrated to 28 courses between plinth and shaft head.
# When surveyed course height becomes available, all dimensional quantities scale together.
course=.064
init=np.array([.70,.73,1.69,.44,.74,.116,.545])
def point(k,par):
 wL,wR,gap,base,depth,over,h=par
 post,n=k.split(':');corner,level=n.split('/');lo,hi=(-gap/2-wL,-gap/2)if post=='L' else(gap/2,gap/2+wR)
 x=lo if corner in ('ol','il','lB') else hi
 y=depth if corner.endswith('B')else 0.
 z={'ground':0,'base':base,'head':base+28*course,'top':base+28*course+h}[level]
 if level=='top':x+=-over if x==lo else over;y+=over if corner.endswith('B')else -over
 return x,y,z
def project(points,cam,size):
 f=cam[0];K=np.array([[f,0,size[0]/2],[0,f,size[1]/2],[0,0,1.]])
 p=(np.asarray(points)@Rotation.from_rotvec(cam[1:4]).as_matrix().T+cam[4:])@K.T;return p[:,:2]/p[:,2,None]
def start(obs,size,f):
 K=np.array([[f,0.,size[0]/2],[0.,f,size[1]/2],[0,0,1.]])
 rows=[]
 for k,uv in obs.items():
  x,y,z=point(k,init)
  if y!=0:continue
  u,v=uv;rows.extend(([x,z,1,0,0,0,-u*x,-u*z,-u],[0,0,0,x,z,1,-v*x,-v*z,-v]))
 H=np.linalg.svd(rows)[2][-1].reshape(3,3)
 A=np.linalg.inv(K)@H;A=A/((np.linalg.norm(A[:,0])+np.linalg.norm(A[:,1]))/2)*np.sign(A[2,2])
 rx,rz,t=A.T;M=np.column_stack([rx,np.cross(rz,rx),rz]);u,_,vt=np.linalg.svd(M)
 return np.r_[f,Rotation.from_matrix(u@vt).as_rotvec(),t]
sizes=[(865,578),(600,400)]
# Hold out opposite front plinth bottom points and the oblique right cap's far lower return.
hold=[{'L:ol/ground','R:or/ground'}, {'R:lB/head','L:ir/head'}]
ties=json.loads((root/'gate-brick-and-plaque-ties.json').read_text())
def errors(p):
 rows=[]
 for i,obs in enumerate((a,b)):
  keys=[k for k in obs if k not in hold[i]];uv=project([point(k,p[:7]) for k in keys],p[7+i*7:14+i*7],sizes[i])
  rows.extend((uv-np.array([obs[k]for k in keys])).ravel())
 P0=p[7:14];K=np.array([[P0[0],0,865/2],[0,P0[0],578/2],[0,0,1.]])
 M=K@np.c_[Rotation.from_rotvec(P0[1:4]).as_matrix(),P0[4:]]
 world=[];target=[]
 for i,t in enumerate(ties):
  if i%5==0:continue
  u,v=t['close'];y=-.024 if 142<u<254 and 169<v<263 else -.036 if 548<u<670 and 166<v<252 else 0.
  H=M[:,[0,2,3]].copy();H[:,2]+=y*M[:,1];q=np.linalg.solve(H,[u,v,1]);world.append([q[0]/q[2],y,q[1]/q[2]]);target.append(t['opening_day'])
 uv=project(world,p[14:21],sizes[1]);rows.extend(((uv-target)*.8).ravel())
 return np.r_[rows, (p[:7]-init)/[.12,.12,.25,.09,.20,.08,.12]]
p=least_squares(errors,np.r_[init,start(a,sizes[0],730),start(b,sizes[1],500)],loss='soft_l1',f_scale=2,max_nfev=1000).x
data={'units':'metres, nominal 64 mm course. Street right is +X, court side +Y, Z up. World origin at middle clear opening, on the line of brick shaft fronts and pavement.','course_m_estimated':course,'n_courses':28,'dimensions':dict(zip(('left_width','right_width','clear_width','plinth_top','depth','cap_overhang','cap_height'),p[:7])),'views':[]}
for i,obs in enumerate((a,b)):
 cam=p[7+i*7:14+i*7];f=cam[0];cx,cy=np.array(sizes[i])/2
 K=np.array([[f,0,cx],[0,f,cy],[0,0,1]]);P=K@np.c_[Rotation.from_rotvec(cam[1:4]).as_matrix(),cam[4:]]
 measurements=[]
 for k,uv in obs.items():
  xyz=point(k,p[:7]); pp=P@np.r_[xyz,1];xy=pp[:2]/pp[2]
  measurements.append(dict(point=k,pixel=uv,xyz=xyz,predicted=xy.tolist(),residual=float(np.linalg.norm(xy-uv)),fit=k not in hold[i]))
 data['views'].append(dict(source=['district-2023-14','open21-original'][i],size=sizes[i],P=P.tolist(),points=measurements))
 print(i,round(cam[0],1),[(v['point'],round(v['residual'],1)) for v in measurements])
print(data['dimensions']);(root/'gate-camera-fit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
