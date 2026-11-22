"""Project into the oblique 2024 exposure and intersect a street ray with the curved crown."""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from street_path import CURVE_LENGTH,NORTH_LENGTH,S,WEST_LENGTH,station

RECORD=json.loads((Path(__file__).resolve().parents[1]/"measurements/corner-crown-camera.json").read_bytes())
CAMERA=np.array(RECORD["camera_3x4"])
EYE=-np.linalg.solve(CAMERA[:,:3],CAMERA[:,3])
INVERSE=np.linalg.inv(CAMERA[:,:3])
MARKS=np.r_[-NORTH_LENGTH,S,CURVE_LENGTH+WEST_LENGTH]
STATIONS=[station(s) for s in MARKS]
XY=np.asarray([p[0]for p in STATIONS])
NORMALS=np.asarray([p[2]for p in STATIONS])
VERTICAL_VP=np.array(RECORD["vanishing_points_px"][-1])


def pixel(xyz):
    q=CAMERA[:,:3]@xyz+CAMERA[:,3]
    return q[:2]/q[2]


def on_wall(u,v,projection=0.):
    """Return arc length and elevation for the nearest point on this exterior surface."""
    direction=INVERSE@np.array([u,v,1.])
    xy=XY+projection*NORMALS
    edges=np.diff(xy,axis=0);delta=xy[:-1]-EYE[:2]
    def cross(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
    den=cross(direction[:2],edges)
    approach=np.divide(cross(delta,edges),den,out=np.full(len(edges),np.nan),where=abs(den)>1.e-12)
    frac=np.divide(cross(delta,direction[:2]),den,out=np.full(len(edges),np.nan),where=abs(den)>1.e-12)
    keep=np.flatnonzero((approach>0)&(frac>=0)&(frac<=1.))
    if not len(keep):raise ValueError("The source ray misses both street walls")
    j=keep[np.argmin(approach[keep])]
    return float(MARKS[j]+frac[j]*(MARKS[j+1]-MARKS[j])),float(EYE[2]+approach[j]*direction[2])


def at_row(u,v,target):
    return float(VERTICAL_VP[0]+(u-VERTICAL_VP[0])*(target-VERTICAL_VP[1])/(v-VERTICAL_VP[1]))
