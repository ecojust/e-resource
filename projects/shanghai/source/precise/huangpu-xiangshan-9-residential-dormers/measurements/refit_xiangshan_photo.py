"""Refit the licensed photograph to the observed wall corners and paired dormer details."""
from pathlib import Path
import json, math
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
D=Path(__file__).parent
obs=json.loads((D/'xiangshan-visible-landmarks.json').read_text())
def projection(v):
    f=math.exp(v[-1])
    intrinsic=np.array([[f,0.,2656.],[0.,f,1494.],[0.,0.,1.]])
    return intrinsic@np.column_stack((Rotation.from_rotvec(v[:3]).as_matrix(),v[3:6]))
def pixel(P,xyz):
    p=P@np.r_[xyz,1.]
    return p[:2]/p[2]
def angle_residual(vanishing,ends):
    a,b=np.array(ends)
    line=np.cross(np.r_[a,1.],np.r_[b,1.])
    return (line@vanishing)/np.linalg.norm(line[:2])/np.linalg.norm(vanishing[:2]-a*vanishing[2])*np.linalg.norm(b-a)
def residual(v):
    P=projection(v)
    points=[(pixel(P,k['xyz'])-k['uv'])*k['weight'] for k in obs['photo_features'] if k['used']]
    lines=[angle_residual(P[:,i],ends)*2 for i,group in [(0,'horizontal_lines'),(2,'vertical_lines')] for ends in obs[group]]
    return np.r_[np.ravel(points),lines,(v[-1]-math.log(obs['photo_focal_prior_px']))*100.]
if __name__=='__main__':
    v=least_squares(residual,obs['camera_initial_parameters'],loss='soft_l1',f_scale=6,max_nfev=2000).x
    P=projection(v)
    controls=[dict(name=k['name'],retained=k['used'],error_original_px=float(np.linalg.norm(pixel(P,k['xyz'])-k['uv'])))for k in obs['photo_features']]
    f=D/'xiangshan-exterior-cameras.json';j=json.loads(f.read_text())
    j['camera_matrices']['2018_commons']=P.tolist()
    j['main_photo_control'].update(fitted_focal_px=math.exp(v[-1]),controls=controls,retained_median_original_px=float(np.median([k['error_original_px']for k in controls if k['retained']])))
    j['main_photo_control'].pop('observed_xyz_px',None)
    j['main_photo_control'].pop('median_residual_px',None)
    f.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
    print(j['main_photo_control']['retained_median_original_px'],[(k['name'],round(k['error_original_px'],2))for k in controls])
