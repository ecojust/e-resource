"""Fit the second publication photograph. Pass the original image and output JSON. Source and credits in two-lane-source-history.json."""
from pathlib import Path
import numpy as np,json
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from scipy.ndimage import gaussian_filter,map_coordinates
from PIL import Image
import sys
HERE=Path(__file__).resolve().parent
ref=np.array(json.loads((HERE/'garden-front-layout.json').read_bytes())['camera_P'])
src=Path(sys.argv[1]);im=Image.open(src).convert('RGB');pixels=np.array(im).astype(float)
candidates=[
 [298,570,84.6,128.2],[478,570,150.5,131.5],[388,516,118,111.4],
 [535,570,172.7,132.3],[718,570,235.6,135.5],[626.5,517,205,116.5],
 [775,572,258.4,137.1],[959,572,318.5,140.7],[867,517,287.6,121.6],
 [540,923,157.9,249.5],[723,923,231.0,251.5],[627,840,195.1,225.2],
 [776,923,251,252],[962,923,319.2,254.3],[866,840,284.5,225.3]]
obs=np.array(candidates);s=183/2.38
points=np.column_stack(((obs[:,0]-626.5)/s,np.zeros(len(obs)),(1130.-obs[:,1])/s))
xy=points[:,[0,2]];uv=obs[:,2:]
def hom(u,v):
 out=[]
 for (x,y),(a,b)in zip(u,v):
  out.extend([[x,y,1.,0,0,0,-a*x,-a*y,-a],[0,0,0,x,y,1.,-b*x,-b*y,-b]])
 return np.linalg.svd(out)[2][-1].reshape(3,3)
H=hom(xy,uv)
H=H/H[2,2];cx,cy=320.,216.
a=H[:,0];b=H[:,1];ac=a[:2]-[cx*a[2],cy*a[2]];bc=b[:2]-[cx*b[2],cy*b[2]]
print('f2 limits',-ac@bc/(a[2]*b[2]),-(ac@ac-bc@bc)/(a[2]**2-b[2]**2))
K=np.array([[440,0,cx],[0,440,cy],[0,0,1.]])
A=np.linalg.inv(K)@H
scale=(np.linalg.norm(A[:,0])+np.linalg.norm(A[:,1]))/2
rr=np.column_stack([A[:,0]/scale,np.cross(A[:,1],A[:,0])/scale**2,A[:,1]/scale])
u1,ss,v1=np.linalg.svd(rr);rot=Rotation.from_matrix(u1@v1)
start=np.r_[rot.as_rotvec(),A[:,2]/scale,440.]
def unpack(c):
 rot=Rotation.from_rotvec(c[:3]).as_matrix();K=np.array([[c[6],0,cx],[0,c[6],cy],[0,0,1]])
 return K@np.column_stack([rot,c[3:6]])
def proj(c,pts):
 q=pts@unpack(c)[:,:3].T+unpack(c)[:,3];return q[:,:2]/q[:,2:]
def fun(c):return (proj(c,points)-uv).reshape(-1)
fit=least_squares(fun,start,loss='soft_l1',bounds=(np.r_[np.repeat(-np.inf,6),170],np.r_[np.repeat(np.inf,6),1400]))
# Independent arc traces on the second image use the visible row of red brick just outside the window reveal.
# The target transitions must be red on the outward side and dark on the opening side.
red=gaussian_filter(pixels[:,:,0]-.50*pixels[:,:,1]-.50*pixels[:,:,2],.8)
grad=gaussian_filter(pixels.mean(2),.8)
def samples(cam):
 origs=[];moved=[]
 for ux,sp,rx,rz,shift in [(388,570,90,54,0),(626.5,570,91.5,53,0),(867,572,92,55,0),(631,923,92,83,-4),(868,923,94,83,-3)]:
  ring=np.linspace(.23,np.pi-.23,27)
  if sp<700:
   R=rx*rx/(2*rz)+rz/2.;off=R-rz
   theta=np.linspace(np.arcsin(off/R)+.08,np.pi-np.arcsin(off/R)-.08,27)
   u=ux+R*np.cos(theta);v=sp+off-R*np.sin(theta)
  else:u=ux+rx*np.cos(ring)+shift*np.sin(ring);v=sp-rz*np.sin(ring)
  world=np.stack([(u-626.5)/s,np.zeros(len(u)),(1130-v)/s],axis=1)
  ap=proj(cam,world);t=np.gradient(ap,axis=0);n=np.stack([t[:,1],-t[:,0]],axis=1);n/=np.linalg.norm(n,axis=1)[:,None]
  # Ensure n points into the opening below its crown. Pass from brick into the opening.
  if n[len(n)//2,1]>0:n*=-1
  offs=np.linspace(-3.8,3.8,33)
  def values(k,channel):
   z=ap[:,None,:]+n[:,None,:]*(offs+k)[None,:,None]
   return map_coordinates(channel,[z[:,:,1],z[:,:,0]],order=1)
  score=values(2.1,red)-values(-2.1,red)+.17*abs(values(1.4,grad)-values(-1.4,grad))-.30*abs(offs)
  pick=score.argmax(1)
  for i,j in enumerate(pick):
   if score[i,j]<5.5 or j in (0,len(offs)-1):continue
   origs.append(world[i]);moved.append(ap[i]+n[i]*offs[j])
 return np.array(origs),np.array(moved)
c=fit.x
for iteration in range(4):
 pts,measure=samples(c)
 def res(x):return np.r_[(proj(x,pts)-measure).flatten(),fun(x)*.60,(x[-1]-450)/250]
 c=least_squares(res,c,loss='soft_l1',f_scale=.85,bounds=(np.r_[np.repeat(-np.inf,6),170],np.r_[np.repeat(np.inf,6),1400])).x
p=unpack(c);errors=np.linalg.norm(proj(c,points)-uv,axis=1);traces=np.linalg.norm(proj(c,pts)-measure,axis=1)
data={'source':str(src.name),'reference_camera_P':ref.tolist(),'camera_P':p.tolist(),'focal_pixels':float(c[-1]),'principal_point':[cx,cy],
      'historic_front_control_points':obs.tolist(),'native_manual_errors_px':errors.tolist(),'red_reveal_observations':len(pts),'median_refined_error_px':float(np.median(traces)),'p90_refined_error_px':float(np.quantile(traces,.9)),'source_utc':'2022 publication'}
Path(sys.argv[2]).write_text(json.dumps(data,indent=2)+'\n')
