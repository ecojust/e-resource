"""Estimate the garden camera from the independently segmented four attic panes."""
import os
from pathlib import Path
import json,math
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parents[1];src=json.loads((w/'measurements/attic-glass.json').read_bytes());data=np.concatenate([np.asarray(c['working_corners'])for c in src['panes']]);pitch=.455;glass=.296
# Survey coordinates are unavailable. Fix only one nominal repeat and derive height from the image.
xy=[]
for i in range(4):
 x=(i-1.5)*pitch;xy.extend([(x-glass/2,1),(x+glass/2,1),(x+glass/2,0),(x-glass/2,0)])
xy=np.array(xy);principal=np.array([400,300]);cen=np.array([4.,-19.,-6.7]);aim=np.array([-5.1,0,-4.4]);forward=(aim-cen)/np.linalg.norm(aim-cen);right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);down=np.cross(forward,right)
init=np.r_[cen,Rotation.from_matrix(np.stack((right,down,forward))).as_rotvec(),660,1.33]
def mat(p):
    K=np.array([[p[6],0,400],[0,p[6],300],[0,0,1.] ]);R=Rotation.from_rotvec(p[3:6]).as_matrix();return K@np.c_[R,-R@p[:3]]
def project(Q,pts):
 q=np.c_[pts,np.ones(len(pts))]@Q.T;return q[:,:2]/q[:,2,None]
def residual(p,prior=660):
 pts=np.column_stack([xy[:,0],np.zeros(len(xy)),xy[:,1]*p[-1]])
 return np.r_[(project(mat(p),pts)-data).ravel(),(p[6]-prior)/140]
lo=[-20,-38,-12,-3.5,-3.5,-3.5,340,.9];hi=[20,-6,1,3.5,3.5,3.5,1150,1.9];fits=[]
for prior in [560,660,760]:
 fit=least_squares(lambda v:residual(v,prior),init,bounds=(lo,hi),loss='soft_l1',xtol=1e-13,gtol=1e-13,ftol=1e-13).x
 fits.append((prior,fit))
fit=fits[1][1];Q=mat(fit);H=Q[:,[0,2,3]]
def facade(px):
 q=np.c_[px,np.ones(len(px))]@np.linalg.inv(H).T;return q[:,:2]/q[:,2,None]
verts=np.column_stack([xy[:,0],np.zeros(len(xy)),xy[:,1]*fit[-1]]);err=np.linalg.norm(project(Q,verts)-data,axis=1)
r={'garden_photo_sha256':src['sha256'],'working_size':[800,600],'nominal_spacing_m':pitch,'nominal_glass_width_m':glass,'fitted_glass_height_m':fit[-1],'focal_px':fit[6],'eye_xyz':fit[:3].tolist(),'pinhole_3x4':Q.tolist(),'facade_h_xz':H.tolist(),'pane_corners_xyz':verts.tolist(),'pane_corners_image':data.tolist(),'corner_rms_working_px':float(np.sqrt((err**2).mean())),'perspective_sensitivity':[dict(focal_prior=p,fitted_focal=v[6],eye=v[:3].tolist())for p,v in fits],'method':'正立面的四组玻璃约束，中线玻璃宽度及间距为估计；原照片无镜头焦距，以三个焦距先验记录敏感度。世界坐标原点在阁窗中央下沿，室外方向为负Y。'}
(w/'measurements/garden-camera.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('focal,eye,height,rms',fit[6],fit[:3],fit[-1],r['corner_rms_working_px']);print('gable extents',facade([[480,233],[671,225],[574,65],[512,437],[661,449]]).round(2))
