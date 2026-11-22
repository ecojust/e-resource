"""Calibrate the 2012 garden window photograph from the four outer timber beads and EXIF lens."""
import hashlib,json,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from scipy.stats import theilslopes

HERE=Path(__file__).resolve().parent
path=Path(os.environ.get('LIANG_WINDOW_PHOTO',HERE.parent/'61-window.jpg'))
with Image.open(path)as im:
    exif=im.getexif().get_ifd(34665);w,h=im.size
    assert (w,h)==(3240,4320)and int(exif[41989])==26
    image=np.asarray(im.resize((1020,1360),Image.Resampling.LANCZOS).convert('RGB'),float)
scale=2;lum=image@np.array([.32,.53,.15])
def edge(profile,center,radius,sign):
    d=np.gradient(gaussian_filter1d(profile,.88))*sign;lo=round((center-radius)*scale);hi=round((center+radius)*scale)
    j=lo+int(np.argmax(d[lo:hi+1]));a,b,c=d[j-1:j+2];shift=(a-c)/(2*(a-2*b+c)) if a+c!=2*b else 0.
    return (j+np.clip(shift,-.5,.5))/scale
def fit(points):
    q=np.asarray(points);s,b,*_=theilslopes(q[:,1],q[:,0]);res=q[:,1]-(s*q[:,0]+b);keep=abs(res-np.median(res))<max(.85,2.6*np.median(abs(res-np.median(res))))
    return np.polyfit(q[keep,0],q[keep,1],1)
edges={k:[]for k in ['left','right','head','sill']}
for y in range(181,550,4):
    if 425<y<454:continue
    left=155+(y-165)*(136-155)/(566-165);right=359+(y-162)*(390-359)/(567-162)
    edges['left'].append([y,edge(lum[y*scale],left,4.9,-1)])
    edges['right'].append([y,edge(lum[y*scale],right,4.9,1)])
for x in range(171,351,4):
    edges['head'].append([x,edge(lum[:,x*scale],164.,4.3,-1)])
    edges['sill'].append([x,edge(lum[:,x*scale],567.,3.5,1)])
l,r,t,b=map(lambda k:fit(edges[k]),['left','right','head','sill'])
def cross(a,b):
    x=(a[0]*b[1]+a[1])/(1-a[0]*b[0]);return [x,b[0]*x+b[1]]
px=np.array([cross(l,b),cross(r,b),cross(r,t),cross(l,t)])
focal=26*np.hypot(510,680)/np.hypot(36,24);width=1.46
def project(v,xyz):
    K=np.array([[focal,0,255],[0,focal,340],[0,0,1.]])
    R=Rotation.from_rotvec(v[3:6]).as_matrix()
    P=K@np.c_[R,-R@v[:3]];q=np.c_[xyz,np.ones(len(xyz))]@P.T
    return P,q[:,:2]/q[:,2,None]
def ends(height):return [[-width/2,0,0],[width/2,0,0],[width/2,0,height],[-width/2,0,height]]
def solve(v):return (project(v,ends(v[6]))[1]-px).ravel()
eye=np.array([.0,-3.4,.30]);axis=np.array([0,0,1.5])-eye;axis/=np.linalg.norm(axis);right=np.cross(axis,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(axis,right)
v=least_squares(solve,[*eye,*Rotation.from_matrix(np.stack([right,down,axis])).as_rotvec(),2.7],bounds=([-3,-9,-3,-3.4,-3.4,-3.4,1.5],[3,-1.1,3,3.4,3.4,3.4,4.0]),loss='soft_l1').x
P,projected=project(v,ends(v[6]));err=np.linalg.norm(projected-px,axis=1)
# A four-corner projective rectification keeps thin iron bands in register.
# The independent constrained camera estimate above records lens/pose uncertainty.
section=np.array(ends(v[6]))[:,[0,2]];A=[];B=[]
for (x,z),(u,y) in zip(section,px):
    A.extend([[x,z,1,0,0,0,-u*x,-u*z],[0,0,0,x,z,1,-y*x,-y*z]]);B.extend([u,y])
H=np.r_[np.linalg.solve(A,B),1.].reshape(3,3)*P[2,3];PP=P.copy();PP[:,[0,2,3]]=H
eye_registered=np.linalg.solve(PP[:,:3],-PP[:,3])
out=dict(photo_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_image_size=[w,h],working_size=[510,680],camera_make='SANYO',camera_model='E1600 TP',equivalent_focal_35mm=26,used_focal_pixels=focal,
         nominal_outer_frame_width_m=width,derived_outer_frame_height_m=v[6],corners_working_px=px.tolist(),observed_edges=edges,eye_xyz=eye_registered.tolist(),pinhole_3x4=PP.tolist(),metric_camera_3x4=P.tolist(),metric_camera_eye_xyz=v[:3].tolist(),rectified_facade_hxz=H.tolist(),training_rms_working_px=float(np.sqrt(np.mean(err**2))),scope='世界原点为木框下缘中点。宽度估计1.46米，其他尺寸取同一张立面照片的相对比例。4.7毫米镜头，等效26毫米，照片记录未给实测窗宽。')
(HERE/'window-camera.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(px.round(2),v[:3].round(3),v[6],out['training_rms_working_px'])
