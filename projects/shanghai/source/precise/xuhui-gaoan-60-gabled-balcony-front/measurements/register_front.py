"""Register Sony long and vertical façade lines in the plane of the balcony fronts.

Canonical reporting raster is 665 by 1000. Original photo is 3264 by 4912.
One repeated storey is assigned three display units; the site was not surveyed.
"""
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
HORIZONTAL=[
 ((25,429),(128,388),1), ((300,326),(426,279),1), ((361,450),(450,432),1),
 ((379,626),(458,620),1), ((30,648),(113,644),1), ((286,211),(393,159),1),
 ((535,209),(627,173),.15), ((182,291),(203,282),.7), ((33,410),(124,373),.8),
 ((308,286),(341,271),.5), ((324,128),(391,88),.8), ((184,527),(197,525),.3)]
VERTICAL=[
 ((142,288),(109,642),1), ((227,252),(194,606),1), ((443,215),(465,592),1),
 ((257,146),(244,210),.5), ((573,388),(587,569),.5), ((187,357),(179,396),.4), ((629,67),(640,139),.6), ((183,243),(176,279),.4)]
K=np.array([[665.91,0,332.5],[0,665.91,500],[0,0,1]])
def direction(lines):
    rows=[]
    for p,q,confidence in lines:
        n=np.cross(np.linalg.solve(K,[*p,1]),np.linalg.solve(K,[*q,1]))
        rows.append(n/np.linalg.norm(n)*np.sqrt(np.linalg.norm(np.subtract(p,q))*confidence))
    return np.linalg.svd(rows)[2][-1]
def camera():
    x=direction(HORIZONTAL);z=direction(VERTICAL)
    if x[0]<0:x=-x
    if z[1]>0:z=-z
    angle=float(np.degrees(np.arccos(x@z)))
    z-=x*(x@z);z/=np.linalg.norm(z)
    inward=np.cross(z,x);inward/=np.linalg.norm(inward)
    r=np.linalg.solve(K,[166,640,1]);origin=r/(r@inward)
    def interim(u,v):
        ray=np.linalg.solve(K,[u,v,1]);a=ray/(inward@ray)-origin
        return np.array([x@a,z@a])
    scale=6/(interim(442,276)[1]-interim(465,618)[1])
    P=K@np.c_[x,inward,z,origin*scale-x*.35-z*.225]
    return P,angle
P,_=camera()
def project(x,y,z):
    q=P@[x,y,z,1];return q[:2]/q[2]
def cut(u,v,depth=0):
    mat=P[:,[0,2,3]].copy();mat[:,2]+=depth*P[:,1]
    q=np.linalg.solve(mat,[u,v,1]);return q[:2]/q[2]
if __name__=='__main__':
    p,ang=camera()
    d={'working_raster':[665,1000],'native_raster':[3264,4912],'horizontal':HORIZONTAL,'vertical':VERTICAL,'axis_angle_before_orthogonalization_degrees':ang,'P_world_to_image':p.tolist(),
       'intrinsics':K.tolist(),'scale':'Six display units between right rail bottom edges at floor 2 and 4. Metric dimensions have not been surveyed.',
       'exif_lens':'SONY DSLR-A580, 16.0mm; 35mm equivalent 24mm. Crop-scale focal length estimated from this field.',
       'local_coordinates':'X image-right along façade, Y inward into the balcony recess, Z up; cutting plane Y0 at the front cornice and rail.'}
    (HERE/'facade-registration.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
