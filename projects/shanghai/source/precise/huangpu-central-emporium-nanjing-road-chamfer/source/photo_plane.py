"""Map upright pixels of the 2022 photograph to the measured street-face planes."""
import json
from pathlib import Path
import numpy as np

registration=json.loads((Path(__file__).resolve().parents[1]/'measurements/2022-entrance-registration.json').read_bytes())
H=np.array(registration['street_plane_homography'])
D=np.array(registration['positive_depth_axis'])

def position(u,v,y=0.):
    plane=H.copy()
    plane[:,2]+=D*y
    ray=np.linalg.solve(plane,[u,v,1.])
    return np.array([ray[0]/ray[2],y,ray[1]/ray[2]])

def pixel(xyz):
    x,y,z=xyz
    ray=H@[x,z,1]+D*y
    return ray[:2]/ray[2]

def positions(pixels,depths):
    """Intersect a whole sheet of photograph rays with individual depth planes."""
    points=np.asarray(pixels,float)
    uv=points.reshape(-1,2)
    p=np.column_stack((uv,np.ones(len(uv))))
    base=p@np.linalg.inv(H).T
    unit_plane=H.copy()
    unit_plane[:,2]+=D
    unit=p@np.linalg.inv(unit_plane).T
    xz0=base[:,:2]/base[:,2,None]
    xz1=unit[:,:2]/unit[:,2,None]
    ys=np.broadcast_to(depths,points.shape[:-1]).reshape(-1)
    xz=xz0+ys[:,None]*(xz1-xz0)
    return np.column_stack((xz[:,0],ys,xz[:,1])).reshape((*points.shape[:-1],3))
