"""Project original 890 by 500 image points into a local architectural plane.
The nominal tablet width supplies scale. Normals and moulding depths remain estimates.
"""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
data=json.loads((Path(__file__).parent/'inscription-strokes.json').read_bytes())
W=data['panel_width_assumed_m']; H=data['panel_height_assumed_m']
def hfit(source,dest):
    a=[];b=[]
    for (x,y),(u,v) in zip(source,dest):
        a.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
        b.extend([u,v])
    return np.r_[np.linalg.lstsq(a,b,rcond=None)[0],1].reshape(3,3)
field=[[-W/2,H],[W/2,H],[W/2,0],[-W/2,0]]
M=hfit(field,data['field_corners_tl_tr_br_bl'])
# Without EXIF calibration or a scale object, normals and depths are estimated.
# The front image in-plane mapping is determined by the four measured tablet corners.
K=np.array([[880.,0.,445.],[0.,880.,250.],[0.,0.,1.]])
a,up,offset=(np.linalg.inv(K)@M).T
normal=np.cross(up,a);normal=normal/np.linalg.norm(normal)*np.sqrt(np.linalg.norm(a)*np.linalg.norm(up))
if normal[2]<0:normal*=-1
P=np.column_stack((M[:,0],K@normal,M[:,1],M[:,2]))
def plane(pixels,y=0):
    a=np.asarray(pixels,float);h=np.column_stack((P[:,0],P[:,2],P[:,3]+y*P[:,1]))
    w=np.c_[a.reshape(-1,2),np.ones(a.size//2)]@np.linalg.inv(h).T
    return (w[:,:2]/w[:,2,None]).reshape(a.shape)
def pixels(coords):
    a=np.asarray(coords);w=np.c_[a.reshape(-1,3),np.ones(a.size//3)]@P.T
    return (w[:,:2]/w[:,2,None]).reshape(a.shape[:-1]+(2,))
