"""Projection into the measured 1062 × 597 copy and intersections with explicit metric planes."""
from pathlib import Path
import json
import numpy as np

HERE=Path(__file__).absolute().parent
DATA=json.loads((HERE.parent/'measurements/balcony-camera.json').read_bytes())
P=np.array(DATA['world_to_working_image'])

def project(points):
    a=np.atleast_2d(points);q=np.column_stack([a,np.ones(len(a))])@P.T
    return q[:,:2]/q[:,2,None]
def on_plane(points,axis,value):
    assert axis in (0,1,2)
    keys=[i for i in range(3)if i!=axis];a=np.atleast_2d(points)
    H=np.column_stack([P[:,keys[0]],P[:,keys[1]],P[:,3]+value*P[:,axis]])
    h=np.column_stack([a,np.ones(len(a))])@np.linalg.inv(H).T;uv=h[:,:2]/h[:,2,None]
    output=np.full((len(a),3),value,dtype=float);output[:,keys]=uv
    return output

def frontage():
    from scipy.interpolate import PchipInterpolator
    edge=json.loads((HERE.parent/'measurements/slab-edge.json').read_bytes())['edge_samples_xy_m']
    xy=np.array(edge);return xy[:,0],PchipInterpolator(xy[:,0],xy[:,1])
def surface(points,offset=0.09):
    """Intersect a reference ray with the street face at the specified setback."""
    from scipy.optimize import brentq
    xs,shape=frontage();eye=np.array(DATA['camera_eye_enu_m']);images=np.atleast_2d(points)
    solution=[]
    for u,v in images:
        ray=np.linalg.solve(P[:,:3],[u,v,1]);ray/=np.linalg.norm(ray)
        def err(t):
            x,y,_=eye+t*ray
            if x<xs[0]:f=shape(xs[0])
            elif x>xs[-1]:f=shape(xs[-1])
            else:f=shape(x)
            return y-f-offset
        t=brentq(err,.1,30)
        solution.append(eye+t*ray)
    return np.array(solution)
