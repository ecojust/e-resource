"""Measure the 2019 street photograph on the plane of the shutter frames."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import box
HERE=Path(__file__).resolve().parent
SURVEY=json.loads((HERE.parent/'measurements/2019-front-camera.json').read_bytes())
P=np.asarray(SURVEY['P_800'])
INV=np.linalg.inv(P[:,:3]);EYE=-INV@P[:,3]
def hit(x,y,d=0.):
    ray=INV@[x,y,1]
    xyz=EYE+ray*(d-EYE[1])/ray[1]
    return float(xyz[0]),float(xyz[2])
def opening(tl,tr,br,bl,d=0):
    l,r,rb,lb=[hit(*pt,d)for pt in [tl,tr,br,bl]]
    return box((l[0]+lb[0])/2,(rb[1]+lb[1])/2,(r[0]+rb[0])/2,(l[1]+r[1])/2)
