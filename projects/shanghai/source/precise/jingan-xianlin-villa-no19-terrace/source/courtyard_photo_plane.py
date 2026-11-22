"""Fayhoo's 2015 photograph of No.19, in original 2144×1424 pixels."""
import json
from pathlib import Path
import numpy as np

CAMERA=json.loads((Path(__file__).resolve().parents[1]/'measurements'/'courtyard-camera.json').read_text())
P=np.array(CAMERA['P'],float)

def fixed_plane(u,v,axis,value):
    """Intersect a photographed pixel ray with X, Y or Z equal to value."""
    free=[i for i in range(3) if i!=axis]
    A=np.column_stack((P[:,free],P[:,3]+value*P[:,axis]))
    a,b,k=np.linalg.solve(A,[u,v,1.])
    q=np.zeros(3);q[axis]=value;q[free]=[a/k,b/k]
    return q.tolist()

def on_side(u,v,y=0.):
    return fixed_plane(u,v,1,y)

def on_front(u,v,x=0.):
    return fixed_plane(u,v,0,x)

def pixel(xyz):
    u,v,q=P@np.r_[xyz,1.]
    return [u/q,v/q]
