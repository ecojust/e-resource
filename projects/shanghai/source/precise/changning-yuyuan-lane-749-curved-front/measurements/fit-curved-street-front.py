"""Recover the rounded cornice and three two-storey bays from the named 2018 residence photograph."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.optimize import least_squares

HERE=Path(__file__).absolute().parent
record=json.loads((HERE/'photographic-source.json').read_bytes())
resize=3.30
centre=np.array([(5312/2-1360)/resize,(2988/2-38)/resize])
focal0=np.hypot(5312,2988)*28/np.hypot(36,24)/resize
photograph=Image.open(HERE/record['crop_file']).crop((0,0,2970,2632)).resize((900,798),Image.Resampling.LANCZOS)
luma=np.asarray(photograph)@np.array([.299,.587,.114]);fall=luma[:-2]-luma[2:]
# Only upper edges bordering bright sky can be read from this stretch of the cap.
u_fit=np.array([145,204,259,322,375,435,489,550,603])
def read_coping(u):
    limit=140
    profile=fall[8:limit,u-2:u+3].mean(axis=1)
    assert profile.max()>70
    return float(9+profile.argmax())
v_fit=np.array([read_coping(u)for u in u_fit])
# Upper then lower opening, clockwise from upper left. Null marks an edge behind equipment or cables.
picked=[[[116,194],[213,158],[211,299],None],[[102,512],[209,488],None,None],
        [[393,142],[501,151],[514,279],[400,271]],[[412,474],[540,481],[550,645],[421,638]],
        [[637,211],[685,247],[701,358],[656,335]],[[682,517],[738,546],[759,681],[706,661]]]
points=np.array([p for row in picked for p in row if p])
mask=[(j,k)for j,row in enumerate(picked)for k,p in enumerate(row)if p]
def camera(p):
    yaw,pitch,roll,f,dist,u,v=p[:7]
    right=np.array([np.cos(yaw),np.sin(yaw),0.])
    forward=np.array([-np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
    down=np.cross(forward,right)
    rot=np.array([np.cos(roll)*right+np.sin(roll)*down,-np.sin(roll)*right+np.cos(roll)*down,forward])
    t=np.r_[(np.array([u,v])-centre)*dist/f,dist]
    K=np.array([[f,0,centre[0]],[0,f,centre[1]],[0,0,1.]])
    return K@np.column_stack([rot,t]),-rot.T@t

def point(r,theta,z,offset=0):
    theta=np.asarray(theta)
    return np.stack([(r+offset)*np.sin(theta),r-(r+offset)*np.cos(theta),np.full(theta.shape,z)],axis=-1)
def project(P,xyz):
    xyz=np.atleast_2d(xyz);p=np.c_[xyz,np.ones(len(xyz))]@P.T
    return p[:,:2]/p[:,2,None]
def geometry(p):
    r,al,ar,wl,wc,wr,lt,lh,h=p[7:]
    rows=[]
    for angle,width in [(al,wl),(0,wc),(ar,wr)]:
        deltheta=np.arcsin(width/(2*r))
        for lo,hi in [(0,1.60),(lt-lh,lt)]:
            rows.append([point(r,angle-deltheta,hi),point(r,angle+deltheta,hi),point(r,angle+deltheta,lo),point(r,angle-deltheta,lo)])
    return np.asarray([rows[j][k]for j,k in mask]),rows
def cap_projected(p,u):
    P,_=camera(p);r=p[7];t=np.linspace(-1.48,1.48,761)
    uv=project(P,point(r,t,p[-1],.083))
    # Use the front-facing portion of the circular cornice. The cropped roof joins a straight wing farther right.
    j0=np.argmin(uv[:,0]);j1=np.argmax(uv[:,0]);xx,yy=uv[j0:j1+1].T
    return np.interp(u,xx,yy)
def errors(p):
    P,_=camera(p)
    residual=project(P,geometry(p)[0])-points
    return np.r_[(residual/2.65).ravel(),(cap_projected(p,u_fit)-v_fit)/1.75,(p[3]-focal0)/85,p[2]/.055]
if __name__=='__main__':
    initial=[-.22,.46,0,focal0,12,454,274,5.65,-.69,.68,1.35,1.42,1.28,-2.05,1.62,2.96]
    lower=[-1.15,.04,-.14,890,5,420,240,3.,-1.17,.30,.65,.8,.65,-3.8,1.16,2.20]
    upper=[.95,.95,.14,1650,24,495,310,11.,-.30,1.32,2.20,2.1,2.2,-1.1,2.45,3.85]
    candidates=[]
    for r0 in [4,6.5,9.2]:
        initial[7]=r0
        candidates.append(least_squares(errors,initial,bounds=(lower,upper),max_nfev=1500))
    fit=min(candidates,key=lambda f:f.cost);p=fit.x;P,eye=camera(p)
    x,rows=geometry(p);projected=project(P,x);rr=projected-points
    print('parameters',np.round(p,4),'camera eye',eye,'window rms',np.mean(rr**2)**.5,'cap errors',np.round(cap_projected(p,u_fit)-v_fit,2),flush=True)
    print('window residuals',np.round(rr,1).tolist(),flush=True)
    dims=dict(radius_m=float(p[7]),bay_angles_rad=[float(p[8]),0.,float(p[9])],bay_widths_m=p[10:13].tolist(),
              upper_window_bottom_m=0.,upper_window_top_m=1.60,lower_window_top_m=p[13],lower_window_height_m=p[14],
              cap_top_m=p[15],coping_offset_m=.083)
    (HERE.parent/'source/dimensions.json').write_text(json.dumps(dims,indent=2)+'\n')
    obj=dict(original_photo_sha256=record['sha256'],crop_sha256=record['crop_sha256'],working_region_in_crop_px=[0,0,2970,2632],
             working_image_size_px=[900,798],principal_point=centre.tolist(),exif_35mm_equivalent=28,focal_prior_px=focal0,
             estimated_focal_px=p[3],world_to_working_image=P.tolist(),eye_m=eye.tolist(),assumed_central_window_height_m=1.60,
             model=dims,point_controls=[dict(bay=label//2+1,level='upper'if label%2==0 else 'lower',corner=k,source_px=actual.tolist(),predicted_px=pred.tolist())for (label,k),actual,pred in zip(mask,points,projected)],
             trained_coping_samples=[dict(u=int(u),observed_v=float(v),predicted_v=float(y))for u,v,y in zip(u_fit,v_fit,cap_projected(p,u_fit))],
             method='Three pairs of visible window openings constrain the camera and cylinder; nine sky-facing cornice points constrain its curvature. Metres depend on the adopted 1.60 m centre window height.')
    (HERE/'curved-corner-camera.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    # Read the lower edge of the cornice against its curved face separately from the sky crest.
    edge_points=[[198,96],[260,83],[307,78],[347,76],[398,77],[445,84],[495,93],[551,105],[590,122]]
    heights=[]
    for uv in edge_points:
        direction=np.linalg.solve(P[:,:3],[*uv,1]);origin=eye-[0,p[7],0];rho=p[7]+.048
        roots=np.roots([direction[:2]@direction[:2],2*origin[:2]@direction[:2],origin[:2]@origin[:2]-rho**2])
        distance=min(k.real for k in roots if np.isreal(k)and k.real>0)
        heights.append(float((eye+distance*direction)[2]))
    dims.update(coping_bottom_m=float(np.median(heights)),visible_arc_limits_rad=[-1.125,.96],lower_cut_m=-4.83)
    (HERE.parent/'source/dimensions.json').write_text(json.dumps(dims,indent=2)+'\n')
    (HERE/'cornice-lower-line.json').write_text(json.dumps(dict(source_sha256=record['sha256'],selected_working_px=edge_points,
       intersection_heights_m=heights,median_height_m=dims['coping_bottom_m'],
       basis='front face of cornice offset 0.048m, conditional on central opening 1.60m high'),indent=2)+'\n')
