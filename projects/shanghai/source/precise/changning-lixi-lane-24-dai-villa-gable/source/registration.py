"""Street photograph projection and intersections in local facade coordinates, metres."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).absolute().parent
C=json.loads((HERE.parent/'measurements/street-camera.json').read_bytes())
P=np.array(C['world_to_local'])
def projected(points):
    a=np.atleast_2d(points);q=np.column_stack([a,np.ones(len(a))])@P.T
    return q[:,:2]/q[:,2,None]
def plane(pixels,axis,value):
    a=np.atleast_2d(pixels);indices=[i for i in range(3)if i!=axis]
    H=np.column_stack([P[:,indices[0]],P[:,indices[1]],P[:,3]+P[:,axis]*value])
    q=np.column_stack([a,np.ones(len(a))])@np.linalg.inv(H).T
    xyz=np.full((len(a),3),value,dtype=float);xyz[:,indices]=q[:,:2]/q[:,2,None];return xyz
def wall(pixels,y=0):return plane(pixels,1,y)[:,[0,2]]
