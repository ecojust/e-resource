"""Fit two street sides and verticals in the named 2021 photograph."""
import json,sys,hashlib
from pathlib import Path
import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
cv2.setNumThreads(1)
p=Path(__file__).parent
photo=Path(sys.argv[1])
size=(640,427)
gray=cv2.resize(cv2.imread(str(photo),0),size,interpolation=cv2.INTER_AREA)
seg=cv2.createLineSegmentDetector().detect(gray)[0].reshape(-1,4)
angle=np.deg2rad(110.16)
dirs=np.array([[np.cos(angle),1,0],[np.sin(angle),0,0],[0,0,1.]])
masks=[np.int32([[65,219],[174,130],[174,145],[236,107],[218,300],[44,329]]),np.int32([[349,85],[493,151],[534,306],[369,295]])]
def camera(t):
 y,pitch,roll,f,cy=t
 B=np.array([[np.cos(y),-np.sin(y),0],[0,0,-1],[np.sin(y),np.cos(y),0]])
 R=Rotation.from_rotvec([0,0,roll]).as_matrix()@Rotation.from_rotvec([pitch,0,0]).as_matrix()@B
 K=np.array([[f,0,319.5],[0,f,cy],[0,0,1]])
 return K,R
def select(t,tol,length_limit):
 K,R=camera(t);v=K@R@dirs;groups=[[],[],[]]
 for l in seg:
  a,b=l[:2],l[2:];d=b-a;m=(a+b)/2;length=np.linalg.norm(d)
  if length<length_limit:continue
  i=next((i for i,poly in enumerate(masks) if cv2.pointPolygonTest(poly,tuple(map(float,m)),False)>=0),None)
  if i is None:continue
  for j in (2,i):
   ray=v[:2,j]-v[2,j]*m
   residual=(ray[0]*d[1]-ray[1]*d[0])/np.linalg.norm(ray)
   if abs(residual)<min(3.9,.43+tol*length):groups[j].append(l);break
 return [np.array(g)for g in groups]
def errors(t,gps):
 K,R=camera(t);v=K@R@dirs;result=[]
 for i,seg in enumerate(gps):
  a,b=seg[:,:2],seg[:,2:];d=b-a;ray=v[:2,i]-(a+b)*.5*v[2,i]
  result.extend((ray[:,0]*d[:,1]-ray[:,1]*d[:,0])/np.linalg.norm(ray,axis=1))
 return np.array(result)
t=[.55,-.34,0.,345.,213.]
for tol,lim in [(t,7) for t in [.08,.06,.04,.028]]+[(.024,8),(.019,10),(.014,10)]:
 groups=select(t,tol,lim)
 t=least_squares(lambda t:errors(t,groups),t,loss='soft_l1',f_scale=.19,x_scale='jac').x
 K,R=camera(t);v=K@R@dirs
 print(np.round(t,3).tolist(),[len(x)for x in groups],np.round((v[:2,:]/v[2,:]).T,1).tolist(),np.median(abs(errors(t,groups))),flush=True)
(p/'named-camera.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(photo.read_bytes()).hexdigest(),native_size=[640,427],working_size=size,angle_degrees=110.16,K=K.tolist(),R=R.tolist(),fit=t.tolist(),retained_groups=[g.round(3).tolist()for g in groups],median_direction_residual_px=float(np.median(abs(errors(t,groups)))),method='Fit two street material planes and verticals to separate image masks; the three corner faces and pediment slopes are excluded. Principal height is free to account for the corrected near-parallel verticals. Principal X fixed at image center.')))
