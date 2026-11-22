"""Continuous north wall, northwest return and western street wall in the registered local frame."""
from pathlib import Path
import json
import numpy as np

MEASUREMENTS=Path(__file__).resolve().parents[1]/'measurements'
RING=np.asarray(json.loads((MEASUREMENTS/'north-front-site.json').read_bytes())['ring_xy_m'])
WEST_START=RING[0]
WEST_END=RING[5]
WEST_VECTOR=(WEST_END-WEST_START)/np.linalg.norm(WEST_END-WEST_START)
NORTH_LENGTH=np.linalg.norm(RING[3]-RING[2])
WEST_LENGTH=np.linalg.norm(WEST_END-WEST_START)
# The surveyed footprint has only two chords at the rounded return. The
# exterior street photos show a continuously turning front tangent to both
# straight walls. The fit preserves both endpoints and both tangencies.
P0=RING[2]
HANDLE=2.605898672
P1=P0+np.array([HANDLE,0.])
P2=WEST_START-HANDLE*WEST_VECTOR
P3=WEST_START
T=np.linspace(0.,1.,1201)
B=((1-T)**3)[:,None]*P0+(3*(1-T)**2*T)[:,None]*P1+(3*(1-T)*T**2)[:,None]*P2+(T**3)[:,None]*P3
S=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(B,axis=0),axis=1))]
CURVE_LENGTH=S[-1]

def station(s):
    """Position, unit tangent and outward horizontal normal at street distance s."""
    if s<=0.:
        xy=np.array([s,0.]);tangent=np.array([1.,0.])
    elif s>=CURVE_LENGTH:
        xy=WEST_START+(s-CURVE_LENGTH)*WEST_VECTOR;tangent=WEST_VECTOR.copy()
    else:
        t=float(np.interp(s,S,T));r=1-t
        xy=r**3*P0+3*r*r*t*P1+3*r*t*t*P2+t**3*P3
        tangent=r*r*(P1-P0)+2*r*t*(P2-P1)+t*t*(P3-P2)
        tangent/=np.linalg.norm(tangent)
    return xy,tangent,np.array([tangent[1],-tangent[0]])

def xyz(s,z,projection=0.):
    xy,_,out=station(s)
    return np.array([*(xy+projection*out),z])

def photo_station(u,v,view='a',projection=0.):
    """Original photo ray to the first intersection with the visible facade path."""
    from nanjing_photo_plane import CAMERAS
    camera=CAMERAS[view]
    eye=-np.linalg.solve(camera[:,:3],camera[:,3])
    direction=np.linalg.solve(camera[:,:3],[u,v,1.])
    marks=np.r_[-NORTH_LENGTH,S,CURVE_LENGTH+WEST_LENGTH]
    xy=np.asarray([xyz(s,0.,projection)[:2] for s in marks])
    edges=np.diff(xy,axis=0)
    delta=xy[:-1]-eye[:2]
    cross=lambda a,b:a[...,0]*b[...,1]-a[...,1]*b[...,0]
    den=cross(direction[:2],edges)
    approach=np.divide(cross(delta,edges),den,out=np.full(len(edges),np.nan),where=np.abs(den)>1.e-12)
    blend=np.divide(cross(delta,direction[:2]),den,out=np.full(len(edges),np.nan),where=np.abs(den)>1.e-12)
    keep=(approach>0)&(blend>=0)&(blend<=1)
    if not keep.any():return None
    i=np.flatnonzero(keep)[np.argmin(approach[keep])]
    return [float(marks[i]+blend[i]*(marks[i+1]-marks[i])),float(eye[2]+approach[i]*direction[2])]
