"""Fit a shifted pinhole model to the photograph after straightening of its verticals."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
import cv2
cv2.setNumThreads(1)
w=Path(__file__).resolve().parent
fn=Path(sys.argv[1])
im=cv2.resize(cv2.imread(str(fn),0),(920,690),interpolation=cv2.INTER_AREA)
seg=cv2.createLineSegmentDetector().detect(im)[0].reshape((-1,4))
c=459.5
def transform(th):
 yaw,pitch,roll,f,cy=th
 r0=np.array([[np.cos(yaw),-np.sin(yaw),0],[0,0,-1],[np.sin(yaw),np.cos(yaw),0]])
 R=Rotation.from_rotvec([0,0,roll]).as_matrix()@Rotation.from_rotvec([pitch,0,0]).as_matrix()@r0
 K=np.array([[f,0,c],[0,f,cy],[0,0,1]])
 return K,R
# Cropped architectural streetscape. Street and original return are the only selected surfaces.
masks=[np.int32([[307,98],[708,309],[708,561],[306,537]]),np.int32([[139,167],[286,100],[286,535],[137,535]])]
def pick(th,angle=.05,limit=12):
 K,R=transform(th);vp=K@R;groups=[[],[],[]]
 for l in seg:
  a,b=l[:2],l[2:];u=(a+b)/2;ab=b-a;length=np.linalg.norm(ab)
  if length<limit:continue
  i=next((i for i,m in enumerate(masks)if cv2.pointPolygonTest(m,tuple(float(v)for v in u),False)>=0),None)
  if i is None:continue
  for d in (2,i):
   v=vp[:2,d]-vp[2,d]*u;e=(v[0]*ab[1]-v[1]*ab[0])/np.linalg.norm(v)
   if abs(e)<min(2.3,.38+angle*length):
    groups[d].append(l.tolist());break
 return [np.array(g)for g in groups]
def err(th,groups):
 K,R=transform(th);v=K@R;errs=[]
 for i,g in enumerate(groups):
  a,b=g[:,:2],g[:,2:];m=(a+b)/2;ab=b-a;d=v[:2,i]-m*v[2,i];errs.extend((d[:,0]*ab[:,1]-d[:,1]*ab[:,0])/np.linalg.norm(d,axis=1))
 return np.array(errs)
th=np.array([.91,.001,-.004,1110.,615.])
for angle,limit in [(.065,12),(.043,16),(.027,18),(.019,21),(.013,23)]:
 gp=pick(th,angle,limit)
 th=least_squares(lambda t:err(t,gp),th,loss='soft_l1',f_scale=.22,x_scale='jac',max_nfev=700).x
 K,R=transform(th);V=K@R;print(th.tolist(),[len(g)for g in gp],np.round((V[:2,:]/V[2,:]).T,1).tolist(),round(np.median(np.abs(err(th,gp))),3))
data=dict(source_sha256=hashlib.sha256(fn.read_bytes()).hexdigest(),working_size=[920,690],native_size=[940,705],K=K.tolist(),R=R.tolist(),intrinsic_fit=th.tolist(),retained_groups=[g.round(3).tolist()for g in gp],median_direction_residual_px=float(np.median(abs(err(th,gp)))),method='Vertical and two horizontal line sets on the verified historic walls. After fitting a fixed horizontal principal point, allow the principal point height to shift to account for architectural perspective correction. Residual is the transverse displacement across each segment in the 920px image.')
(w/'qiao-shifted-perspective.json').write_text(json.dumps(data,indent=2)+'\n')
