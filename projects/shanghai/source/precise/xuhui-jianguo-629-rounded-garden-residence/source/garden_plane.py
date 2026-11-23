"""Registered garden-plane survey, with metres estimated from photographed brick courses."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import box,Polygon
from math import sqrt
HERE=Path(__file__).resolve().parent
SURVEY=json.loads((HERE.parent/'measurements/front-registration.json').read_bytes())
def projection(key):
    station=SURVEY[key]
    return np.asarray(station['K'])@np.asarray(station['R_world_to_camera'])@np.column_stack([np.eye(3),-np.asarray(station['eye'])])
P=projection('camera_2019_publication')
INV=np.linalg.inv(P[:,:3])
EYE=-INV@P[:,3]

def hit(x,y,d=0.):
    v=INV@np.array([x,y,1.])
    pt=EYE+v*((d-EYE[1])/v[1])
    return float(pt[0]),float(pt[2])

def straight_window(top_left,top_right,bottom_right,bottom_left,d=0.):
    tl,tr,br,bl=[hit(*p,d) for p in [top_left,top_right,bottom_right,bottom_left]]
    return box((tl[0]+bl[0])/2,(br[1]+bl[1])/2,(tr[0]+br[0])/2,(tl[1]+tr[1])/2)

def cap_shape(edges,apex,sill,steps):
    l,r=[hit(*p) for p in edges];u0,u1=l[0],r[0]
    spring=(l[1]+r[1])/2;rise=hit(*apex)[1]-spring
    half=(u1-u0)/2;radius=(half*half+rise*rise)/(2*rise);middle=(u0+u1)/2
    top=[]
    for i in range(steps+1):
        x=u1-(u1-u0)*i/steps
        z=spring+rise-radius+sqrt(max(0,radius*radius-(x-middle)**2))
        top.append((x,z))
    return Polygon([(u0,sill),(u1,sill),*top])

def wide_openings(lod=False):
    steps=12 if lod else 32
    return {'ground':cap_shape([(308,321),(418,321)],(361,306),hit(414,393)[1],steps),
            'middle':cap_shape([(307,199.6),(408.6,201.7)],(357.9,184.8),hit(360,262.7)[1],steps),
            'upper':straight_window((304,96),(401,99),(404,146),(305,144))}

def flat_single_windows():
    return [('lower left garden casement',straight_window((120,319),(190,319),(187,396),(114,397))),
            ('middle left garden casement',straight_window((128,195),(193,196),(190,261),(123,261)))]
