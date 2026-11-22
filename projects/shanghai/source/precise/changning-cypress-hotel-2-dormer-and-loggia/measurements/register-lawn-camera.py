"""Fit the two measured openings with a nominal module and retain lens sensitivity."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
p=Path(__file__).resolve().parent
obs=json.loads((p/'second-storey-openings.json').read_bytes());target=np.concatenate([w['corners']for w in obs['windows']]);spacing=1.44
centers=(np.array([-.5,.5])*spacing)
def world(v):
    width,height=v[-2:]
    return np.array([(cx+ox*width,0,h*height)for cx in centers for ox,h in [(-.5,1),(.5,1),(.5,0),(-.5,0)]])
def matrix(v):
    R=Rotation.from_rotvec(v[3:6]).as_matrix()
    return np.array([[v[6],0,514],[0,v[6],343],[0,0,1.]])@np.column_stack([R,-R@v[:3]])
def project(m,xyz):
    homog=np.c_[xyz,np.ones(len(xyz))]@m.T
    return homog[:,:2]/homog[:,2,None]
eye=np.array([5.,-39.,-3.3]);axis=np.array([0,0,-2.7])-eye;axis/=np.linalg.norm(axis);right=np.cross(axis,[0,0,1]);right/=np.linalg.norm(right);down=np.cross(axis,right)
rot=Rotation.from_matrix(np.stack([right,down,axis])).as_rotvec();fits=[]
for focal in [700,870,1040]:
    def error(v):
        proj=project(matrix(v),world(v));return np.r_[(proj-target).ravel(),(v[6]-focal)/150,(v[-2]-.86)/.18,(v[-1]-1.48)/.22,(v[2]+3.1)/2.1]
    fit=least_squares(error,np.r_[eye,rot,focal,.84,1.46],bounds=([-32,-85,-6.5,-3.6,-3.6,-3.6,440,.59,1.1],[32,-14,-.5,3.6,3.6,3.6,1450,1.17,1.88]),loss='soft_l1')
    fits.append((focal,fit.x.tolist()))
v=np.asarray(fits[1][1]);P=matrix(v);res=project(P,world(v))-target
r=dict(source_sha256=obs['source_sha256'],image_size=obs['source_pixels'],nominal_between_window_centres_m=spacing,broad_focal_priors_pixels=[f[0]for f in fits],eye_xyz=v[:3].tolist(),pinhole_3x4=P.tolist(),nominal_fit_opening_width_m=v[-2],nominal_fit_opening_height_m=v[-1],training_rms_pixels=float(np.linalg.norm(res)/np.sqrt(len(res))),fit_parameters_by_focal_prior=fits,local_axes='中段二层两窗窗台中点为原点，X向照片右，Y进墙，Z向上。依据8个角点和建筑窗间距的估计尺度。深度属于单视图近似。')
(p/'lawn-camera.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(v.round(3),r['training_rms_pixels'])
