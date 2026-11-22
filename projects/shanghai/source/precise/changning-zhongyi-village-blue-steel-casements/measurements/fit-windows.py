"""Rectify the brick facade and recover the photographed outward casement from its two free corners."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).absolute().parent
def unit(v):return v/np.linalg.norm(v)
def homography(source,target):
    a=[]
    for (x,y),(u,v)in zip(source,target):
        a.extend([[x,y,1,0,0,0,-u*x,-u*y,-u],[0,0,0,x,y,1,-v*x,-v*y,-v]])
    return np.linalg.svd(a)[2][-1].reshape(3,3)
image_size=[4160,3120];centre=np.array(image_size)/2
focal=np.hypot(*image_size)*28/np.hypot(36,24)
K=np.array([[focal,0,centre[0]],[0,focal,centre[1]],[0,0,1.]])
closed=[[1612,975],[1813,1044],[1793,1320],[1597,1270]]
grid=[[-.5,1],[.5,1],[.5,0],[-.5,0]]
G0=homography(grid,closed)
hvp=G0[:2,0]/G0[2,0]
# The estimated EXIF focal length constrains the two facade directions to be
# orthogonal. The width of a far jamb can vary by a few image pixels, which
# makes an unconstrained four-corner vertical vanishing point unstable.
slope=np.mean([(closed[3][0]-closed[0][0])/(closed[3][1]-closed[0][1]),
               (closed[2][0]-closed[1][0])/(closed[2][1]-closed[1][1])])
reference=np.mean(closed,axis=0)
heading=hvp-centre
dxy=np.array([slope,1.])
t=(-focal**2-np.dot(heading,reference-centre))/np.dot(heading,dxy)
vvp=reference+t*dxy
horizontal=unit(np.r_[hvp-centre,focal])
vertical=unit(np.r_[vvp-centre,focal])
normal=unit(np.cross(horizontal,vertical))
def local(uv):
    ray=np.r_[np.array(uv)-centre,focal]
    xyz=ray/np.dot(ray,normal)
    return np.array([np.dot(horizontal,xyz),np.dot(vertical,xyz)])
q=np.array([local(p)for p in closed]);h=1.55
scale=h/(q[:2,1].mean()-q[2:,1].mean())
sign_x=np.sign((q[[1,2],0].mean()-q[[0,3],0].mean())*scale)
origin=[q[:,0].mean(),q[2:,1].mean()]
def metric_xy(uv):
    return (local(uv)-origin)*np.array([sign_x*scale,scale])
registered=np.array([metric_xy(pt)for pt in closed])
width=registered[[1,2],0].mean()-registered[[0,3],0].mean();height=h
H=homography(closed,registered);G=np.linalg.inv(H);dirs=np.linalg.inv(K)@G
if dirs[2,2]<0:dirs=-dirs
yhat=unit(np.cross(dirs[:,1],dirs[:,0]))*(np.linalg.norm(dirs[:,0])+np.linalg.norm(dirs[:,1]))/2
if yhat[2]<0:yhat=-yhat
P=K@np.column_stack([dirs[:,0],yhat,dirs[:,1],dirs[:,2]])
def project(xyz):
    a=P@[*xyz,1.]
    return a[:2]/a[2]
left_corners=[[1142.,805.],[1392.,887.],[1374.,1217.],[1115.,1152.]]
lm=np.array([metric_xy(uv)for uv in left_corners])
bounds=[float(np.mean(lm[[0,3],0])),float(np.mean(lm[[2,3],1])),float(np.mean(lm[[1,2],0])),float(np.mean(lm[[0,1],1]))]
left,bottom,right,top=bounds
# Four tips of the green leaf, including its hinge edge, distinguish
# rotation from a change in height or a shift of the frame in the opening.
leaf_controls=np.array([[1143.,804.],[1116.,1147.],[1264.,826.],[1252.,1156.]])
def predictions(params):
    angle,span,hinge,depth,ztop,zbottom=params
    free=hinge+span*np.cos(angle);outside=depth-span*np.sin(angle)
    return np.array([project([hinge,depth,ztop]),project([hinge,depth,zbottom]),
                     project([free,outside,ztop]),project([free,outside,zbottom])])
def residual(params):
    angle,span,hinge,depth,ztop,zbottom=params
    return np.r_[((predictions(params)-leaf_controls)/2).ravel(),(span-(right-left)*.5+.035)/.04,
                 (depth-.02)/.04,(hinge-left-.035)/.035]
solutions=[]
for angle0 in [.22,.8,1.4]:
    seed=[angle0,.65,left+.034,.023,top,bottom+.032]
    lower=[.001,.45,left-.05,-.10,top-.12,bottom-.06];upper=[1.65,.85,left+.105,.12,top+.10,bottom+.15]
    solutions.append(least_squares(residual,seed,bounds=(lower,upper)))
fitted=min(solutions,key=lambda result:result.cost)
angle,leaf,hinge_x,hinge_d,leaf_top,leaf_bottom=fitted.x
eye=-np.linalg.solve(P[:,:3],P[:,3])
if __name__=='__main__':
    data=dict(photo_sha256='e3196d35a8aea7d9841814425a52b1a93f40f843d58b8c44dcc0b97f4f401a78',image_size=image_size,
       exif_35mm_equivalent=28,assumed_right_opening_height_m=height,closed_controls=closed,open_wall_controls=left_corners,
       outward_leaf_observed_corners=leaf_controls.tolist(),outward_leaf_fitted_px=predictions(fitted.x).tolist(),
       projected_corner_residual_px=(predictions(fitted.x)-leaf_controls).tolist(),
       camera_eye_local_m=eye.tolist(),orthogonal_vanishing_points=[hvp.tolist(),vvp.tolist()],closed_registered_xz=registered.tolist(),focal_px=focal,plane_homography=(H/H[2,2]).tolist(),world_to_pixel=P.tolist(),
       window_returns_note='主窗下缘有石窗台遮挡。被开启扇盖住的左框顶点误差较大，框面和窗下缘分别采用近似位置。')
    dims=dict(closed=[-width/2,0,width/2,height],open_bay=bounds,open_angle_degrees=float(np.degrees(angle)),
      swinging_leaf_width=float(leaf),hinge_origin_x=float(hinge_x),hinge_y_m=float(hinge_d),swing_top_m=float(leaf_top),swing_bottom_m=float(leaf_bottom),
      wall_left=left-.46,wall_right=width/2+.40,section_bottom=min(-.36,bottom-.39),section_top=max(height,top)+.48)
    for dest,r in [(HERE/'two-window-camera.json',data),(HERE.parent/'source/dimensions.json',dims)]:
        dest.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(dims,'residual',data['projected_corner_residual_px'],'eye',eye)
