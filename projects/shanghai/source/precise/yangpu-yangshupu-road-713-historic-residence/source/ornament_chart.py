"""Image coordinates and a local display-scale chart for the photographed gable alone."""
import numpy as np
PHOTO_SIZE=(2053,1369)
U0,V0=777.5,615.8
PIXELS_PER_COURSE=2.39
COURSE=.066
Z_SCALE=PIXELS_PER_COURSE/COURSE
X_SCALE=Z_SCALE*(27.2/36.8)
FOCAL=2053*27/36
K=np.array([[FOCAL,0,PHOTO_SIZE[0]*.5],[0,FOCAL,PHOTO_SIZE[1]*.5],[0,0,1.]])
kx=-np.sqrt(1-(X_SCALE/Z_SCALE)**2)*Z_SCALE/FOCAL
kz=.003
HX=np.array([X_SCALE+U0*kx,-.225*X_SCALE+V0*kx,kx])
HZ=np.array([-.40+U0*kz,-Z_SCALE+V0*kz,kz])
O=np.array([U0,V0,1.])
rx=np.linalg.solve(K,HX);rz=np.linalg.solve(K,HZ)
normal=np.cross(rz,rx)
normal*=np.sign(normal[-1])*np.linalg.norm(rz)/np.linalg.norm(normal)
P=np.column_stack([HX,K@normal,HZ,O])

def cut(uv,depth=0.):
    h=np.linalg.solve(P[:,[0,2,3]]+np.column_stack([np.zeros(3),np.zeros(3),depth*P[:,1]]),[*uv,1.])
    return h[:2]/h[2]

def project(xyz):
    q=P@[*xyz,1.]
    return q[:2]/q[2]
