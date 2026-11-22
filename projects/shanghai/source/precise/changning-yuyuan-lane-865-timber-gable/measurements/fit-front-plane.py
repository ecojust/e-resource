"""Calibrate the street-facing wall axes from photographed rails, brickwork and jambs."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).absolute().parent
PHOTO = 'f56bbaf9906f0c680e0bc55be216c207796277a9d51f1bf212bf7be7a163551e'
HORIZONTAL = [
    [201,432,439,397], [202,384,425,335], [206,283,421,214],
    [252,465,354,454], [199,642,434,667], [200,615,244,620],
]
VERTICAL = [
    [207,281,199,429], [246,265,243,405], [301,151,300,396], [330,156,332,392],
    [359,187,361,389], [421,206,431,397], [252,467,245,639], [355,456,361,642],
]
PRINCIPAL = np.array([304.,343.])
SCALE = 2.12  # Assumed front portal clear height at its centre, not survey data.

def vanishing(lines):
    p = np.array(lines,float).reshape(-1,2,2)
    v = p[:,1]-p[:,0]
    def orthogonal_pixels(vp):
        tangent = vp-p.mean(axis=1)
        tangent /= np.linalg.norm(tangent,axis=1)[:,None]
        return v[:,0]*tangent[:,1]-v[:,1]*tangent[:,0]
    normals = np.column_stack([v[:,1],-v[:,0]])
    initial = np.linalg.lstsq(normals,(normals*p[:,0]).sum(axis=1),rcond=None)[0]
    sol = least_squares(orthogonal_pixels,initial,loss='soft_l1',f_scale=1.4)
    return sol.x, sol.fun

def fit():
    x, xerr = vanishing(HORIZONTAL)
    z, zerr = vanishing(VERTICAL)
    focal = np.sqrt(-(x-PRINCIPAL)@(z-PRINCIPAL))
    K = np.array([[focal,0,PRINCIPAL[0]],[0,focal,PRINCIPAL[1]],[0,0,1.]])
    ray = lambda p: np.linalg.solve(K,np.r_[p,1.])
    unit = lambda a: a/np.linalg.norm(a)
    ex,ez=-unit(ray(x)),unit(ray(z))
    R=np.stack([ex,np.cross(ez,ex),ez],axis=1)
    assert abs(np.linalg.det(R)-1)<1.e-7
    foot,head=ray([302,649]),ray([302,476])
    # Choose depth at the threshold so that the measured scale span projects to its lintel.
    depth=np.linalg.lstsq(np.stack([foot,-head],axis=1),-SCALE*ez,rcond=None)[0][0]
    offset=depth*foot
    P=K@np.column_stack([R,offset])
    return dict(source_sha256=PHOTO,source_dimensions_px=[608,686],assumed_principal_point=PRINCIPAL.tolist(),
        horizontal_controls=HORIZONTAL,vertical_controls=VERTICAL,horizontal_vanishing_point=x.tolist(),
        vertical_vanishing_point=z.tolist(),horizontal_direction_residual_px=xerr.tolist(),vertical_direction_residual_px=zerr.tolist(),
        inferred_focal_px=float(focal),front_portal_centre_height_assumed_m=SCALE,scale_endpoints_px=[[302,649],[302,476]],
        world_to_photo=P.tolist(),camera_eye_enu_m=(-R.T@offset).tolist(),
        limitations='单张低分辨率斜照。模型尺度以门套前沿中央净高2.12米为假设；墙厚、出檐和门内退进量按可见侧壁估计。')

if __name__=='__main__':
    result=fit()
    (HERE/'front-plane-camera.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['horizontal_vanishing_point'],result['vertical_vanishing_point'],result['inferred_focal_px'],result['camera_eye_enu_m'])
