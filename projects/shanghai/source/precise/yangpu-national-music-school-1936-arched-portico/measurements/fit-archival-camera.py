"""Fit the arched panel and the three visible eave corners to one perspective camera."""
from pathlib import Path
import json,runpy
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE=Path(__file__).absolute().parent
front=runpy.run_path(HERE/'fit-portal.py');old=runpy.run_path(HERE/'initial-camera.py')
P=old['P'];K=old['K'];pr=old['pr'];d=front['d'];base=d['ground'];L=d['wall_left'];R=d['wall_right']
old_rot=np.linalg.inv(K)@P[:,:3];u,_,v=np.linalg.svd(old_rot);rot=u@v
if np.linalg.det(rot)<0:rot=-rot
cam0=Rotation.from_matrix(rot).as_rotvec()
controls=[([*front['metric'](uv)],uv)for uv in front['FACE']]
# The near eave shoulder is visible as the end of the grey tile field above the black soffit.
roof_px=[[91,86],[254,57],[372,99],[231,37.5]]
weights=[1.8,1.8,3.5,2.5]
size=d['clear_width'];s=d['spring']
def project(points,x):
    rotation=Rotation.from_rotvec(x[:3]);cs=rotation.apply(np.asarray(points)-x[3:6])
    return pr+cs[:,:2]/cs[:,2,None]*np.exp(x[6])
def geometry(x):
    l,r,b,h,peak=x[7:12];f=-.72
    return [[l,f,h],[r,f,h],[r,b,h],[(l+r)/2+x[12],(f+b)/2+x[13],peak]]
def cost(x):
    pts=[[xx,0,z]for (xx,z),_ in controls]
    mis=(project(pts,x)-[uv for _,uv in controls])/np.array(weights)[:,None]
    actual=[[-size/2,0,s],[size/2,0,s],[0,0,s+size/2]]
    ag=(project(actual,x)-[front['spring'][0],front['spring'][1],front['crown']])/1.2
    rg=(project(geometry(x),x)-roof_px)/np.array([1.5,3.2,1.5,1.8])[:,None]
    return np.r_[mis.ravel(),ag.ravel(),rg.ravel(),x[12]/.32,x[13]/.32]
p=np.r_[cam0,old['eye'],np.log(old['f']),L-.8,R+.7,6.5,11.0,13.5,0,0]
lower=[-4]*3+[-15,-130,-.62,np.log(350),L-2,R-.2,2.,8.,10.2,-.85,-.85]
upper=[4]*3+[90,-8,5,np.log(6000),L+.1,R+3.7,13.,16.,19.,.85,.85]
sol=least_squares(cost,p,bounds=(lower,upper),max_nfev=9000,ftol=1e-12,xtol=1e-12,gtol=1e-11)
x=sol.x;rr=np.asarray(geometry(x));pred=project(rr,x);camera=dict(principal_px=pr.tolist(),focal_px=float(np.exp(x[6])),eye_local_m=x[3:6].tolist(),
    world_to_camera_rotation=Rotation.from_rotvec(x[:3]).as_matrix().tolist(),roof_controls_px=roof_px,roof_projection_px=pred.tolist(),
    left_front_eave_xyz=rr[0].tolist(),right_front_eave_xyz=rr[1].tolist(),right_rear_eave_xyz=rr[2].tolist(),apex_xyz=rr[3].tolist(),
    front_plane_controls=controls,front_plane_projection_px=project([[xx,0,z]for (xx,z),_ in controls],x).tolist(),
    arch_projection_px=project([[-size/2,0,s],[size/2,0,s],[0,0,s+size/2]],x).tolist(),
    forward_eave_y_m=-.72,arch_width_assumption_m=size,note='按同一相机联算券面、圆头与檐口的左前、右前、右后三个折角。最前端出檐量及1.32米券半径为假设。')
if __name__=='__main__':
    (HERE/'joint-camera-and-roof.json').write_text(json.dumps(camera,ensure_ascii=False,indent=2)+'\n')
    print('eye',x[3:6],'f',np.exp(x[6]),'roof',rr.round(3),'projection',pred.round(2),'arch',np.round(camera['arch_projection_px'],2),'face',np.round(camera['front_plane_projection_px'],2))
