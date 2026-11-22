"""Use the second camera's rectangular relief panel to solve the entrance cheeks and porch depth."""
from pathlib import Path
import json,runpy,sys
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).absolute().parent
shared=runpy.run_path(HERE/'register-entrance.py')
model=shared['model'];proj=shared['project'];LINES=shared['LINES'];anchor=shared['ANCHOR']
plate_a=[[166.,342.5],[228.,349.],[213.,510.],[153.,535.5]]
plate_b=[[73,34],[389,54],[344,489],[90,486]]
corners=[[[253,229],[242,592]],[[128,320],[102,590]],[[523,225],[529,488]],[[626,355],[636,596]]]
def aspect(corners):
    # Relative lengths of the two orthogonal columns in calibrated plane coordinates.
    pairs=[];rhs=[];focal=28*np.hypot(450,600)/np.hypot(36,24)
    for (u,v),(x,y)in zip([[0,0],[1,0],[1,1],[0,1]],corners):
        pairs.extend([[u,v,1,0,0,0,-x*u,-x*v],[0,0,0,u,v,1,-y*u,-y*v]]);rhs.extend([x,y])
    K=np.array([[focal,0,225],[0,focal,300],[0,0,1]])
    H=np.linalg.solve(K,np.r_[np.linalg.solve(pairs,rhs),1].reshape(3,3));a,b=H[:,0],H[:,1]
    return np.linalg.norm(a)/np.linalg.norm(b),np.degrees(np.arccos(a@b/np.linalg.norm(a)/np.linalg.norm(b)))
ASPECT,ANGLE=aspect(plate_b)
def features(q):
    depth,xl,xr,al,ar,yp,zp,h=q[7:]
    plate_t=np.array([np.sin(al),np.cos(al),0]);n=np.array([np.cos(al),-np.sin(al),0])
    pos=[xl+yp*np.tan(al),yp,zp];center=pos+n*.026
    plate=[center+t*h*ASPECT*plate_t+[0,0,s*h]for t,s in [(-.5,.5),(.5,.5),(.5,-.5),(-.5,-.5)]]
    side=[(xl,0),(xl+depth*np.tan(al),depth),(xr,0),(xr+depth*np.tan(ar),depth)]
    tangent=[np.array([np.sin(k),np.cos(k),0])for k in [al,ar]]
    return plate,side,tangent
def resid(q):
    P,_=model(q[:7]);plate,side,tangent=features(q);out=[]
    for axis,lines in [(np.array([1.,0,0]),LINES[0]),(np.array([0.,0,1.]),LINES[2]),(tangent[0],LINES[1][:4]),(tangent[1],LINES[1][4:])]:
        vp=P[:,:3]@axis
        for line in lines:
            a,b=np.array(line).reshape(2,2);t=vp[:2]-(a+b)/2*vp[2];t/=np.linalg.norm(t);d=b-a;out.append((d[0]*t[1]-d[1]*t[0])*.55)
    for (x,y),obs in zip(side,corners):
        a,b=proj(P,[[x,y,-1.5],[x,y,.7]]);t=(b-a)/np.linalg.norm(b-a)
        for v in np.array(obs)-a:out.append((v[0]*t[1]-v[1]*t[0])*.68)
    return np.r_[out,(proj(P,[[-.54,0,0],[.54,0,0]])-anchor).ravel(),(proj(P,plate)-plate_a).ravel()*.65,(q[3]-647.1)/5.]
if __name__=='__main__':
    start=[.006,.169,-.036,649,4.10,390,345,-1.25,-.87,.85,.23,-.23,-.56,-.55,.91]
    lo=[-.35,.025,-.13,592,3.28,379,338,-2.25,-1.11,.65,-.04,-.52,-1.35,-.8,.65]
    hi=[.35,.37,.13,710,4.73,402,355,-.73,-.68,1.04,.52,.04,-.25,-.28,1.13]
    r=least_squares(resid,start,bounds=(lo,hi),loss='soft_l1',f_scale=1.5);q=r.x;P,eye=model(q[:7]);plate,side,directions=features(q)
    # This refinement supersedes the single-view temporary y-parallel cheek estimates.
    s=HERE/'entrance-camera.json';data=json.loads(s.read_bytes())
    if 'single_view_initial'not in data:data['single_view_initial']={k:data[k]for k in ('world_to_working','parameters','eye_enu_m','outer_sidewall_width_limits_m','independent_front_plane_estimates_m','outer_front_y_m')}
    data.update(datum='内层木拱门左右起拱的平均标高。本解采用两幅照片联合校正的张角与进深。',world_to_working=P.tolist(),parameters=q[:7].tolist(),eye_enu_m=eye.tolist(),outer_front_y_m=q[7],outer_sidewall_width_limits_m=q[8:10].tolist(),
        sidewall_bearings_from_depth_deg=np.degrees(q[10:12]).tolist(),wall_corners_xy=side,plaque_corners_enu=np.asarray(plate).tolist(),
        plaque_homography_photo_sha256='dd659672b9fb5873809f552a16e13d50682b3a3bcabb9b88921fa24d7855caec',plaque_closeup_quad_px=plate_b,street_plaque_quad_px=plate_a,closeup_size=[450,600],
        plaque_aspect=ASPECT,orthogonality_angle_deg=ANGLE,calibration_residuals=r.fun.tolist(),plaque_reprojection_errors_px=(proj(P,plate)-plate_a).tolist(),
        method='独立的信报箱照片给出石板的宽高比。结合外门照片中的同一石板、门洞、前后砖棱和侧墙灰缝，联合求解两侧墙面方位、外拱所在深度与相机；石板突出墙面26毫米为估计。')
    data.pop('independent_front_plane_estimates_m',None)
    assert -.52<q[11]<.04 and -.04<q[10]<.52 and 83<ANGLE<97
    s.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print(q.round(4),np.std(r.fun),np.max(abs(r.fun)),proj(P,plate)-plate_a)
