"""Register the street-side balcony in the upright 2018 image using independent parallel lines."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).absolute().parent
SIZE=[1062,597];C=np.array([531,298.5]);IMAGE='0b4252d6f0bf74d8b4fc3b86255cd0b52de92c09d66a7813cc59f20df81941e3'
# The three sets describe the facade direction, the receding end wall and the verticals.
LINES=[
 [[8,256,332,3],[165,209,342,79],[173,261,292,189],[465,259,603,196],[473,277,629,209],
  [507,244,623,191],[534,322,656,284]],
 [[815,268,1049,442],[822,280,1043,444],[877,395,1017,469],[863,151,945,240],
  [862,83,889,119],[940,232,988,283]],
 [[408,226,407,381],[316,283,309,410],[748,46,807,261],[797,86,845,257],
  [702,228,711,279],[540,268,541,325],[1008,277,1045,411],[468,271,469,365]]]
def orientation(q):
    yaw,pitch,roll=q[:3]
    right=np.array([np.cos(yaw),np.sin(yaw),0.])
    forward=np.array([-np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
    down=np.cross(forward,right)
    return np.array([np.cos(roll)*right+np.sin(roll)*down,-np.sin(roll)*right+np.cos(roll)*down,forward])
def intrinsics(f):return np.array([[f,0,C[0]],[0,f,C[1]],[0,0,1.]])
def residual(q,detail=False):
    V=intrinsics(q[-1])@orientation(q);result=[]
    observed=json.loads((HERE/'line-observations.json').read_bytes())['axes']
    for i,g in enumerate(observed):
        group=[r['edge']for r in g if r['sustained_contrast']>=12]
        # Glancing near-parallel runs carry the same pixel endpoints' error as close runs.
        van=V[:2,i]/V[2,i]
        for x0,y0,x1,y1 in group:
            dx=x1-x0;dy=y1-y0;axis=van-[.5*(x0+x1),.5*(y0+y1)];axis/=np.linalg.norm(axis)
            result.append(dx*axis[1]-dy*axis[0])
    if detail:return np.array(result)
    return np.r_[result,(q[-1]-np.hypot(*SIZE)*28/43.27)/45,q[2]/.03]
def solve():
    fit=least_squares(residual,[.62,.31,0,795],bounds=([.18,.12,-.13,640],[1.25,.65,.13,950]),loss='soft_l1',f_scale=2.4)
    R=orientation(fit.x);K=intrinsics(fit.x[-1])
    # Visible slender guard upright near the left central scroll, excluding its curled ends.
    # The foot has a small seat on the balcony cap. 0.94 m is a scale assumption.
    foot=np.linalg.solve(K,[550,326.5,1]);head=np.linalg.solve(K,[545,257.5,1])
    depth=np.linalg.lstsq(np.column_stack([foot,-head]),-.94*R[:,2],rcond=None)[0][0]
    off=foot*depth;P=K@np.column_stack([R,off])
    return dict(photo_sha256=IMAGE,working_size=SIZE,original_size=[5312,2988],effective_equivalent_focal_mm=28,
      calibration_lines=LINES,camera_angles_rad=fit.x[:3].tolist(),focal_px=fit.x[-1],direction_residual_px=residual(fit.x,True).tolist(),
      conditional_guard_post_height_m=.94,guard_post_top_and_base_px=[[545,257.5],[550,326.5]],
      camera_eye_enu_m=(-R.T@off).tolist(),world_to_working_image=P.tolist(),
      limits='单张斜照中的沿街阳台端部、栏杆与晾衣架。绝对比例以0.94米栏高估算。')
if __name__=='__main__':
    r=solve();print('camera',np.round(r['camera_angles_rad'],3),r['focal_px'],np.round(r['camera_eye_enu_m'],2),'residual',np.round(r['direction_residual_px'],1))
    (HERE/'balcony-camera.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
