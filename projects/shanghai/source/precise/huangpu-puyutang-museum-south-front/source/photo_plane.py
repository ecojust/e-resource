"""Project a court or entrance photograph onto the south-front coordinate planes."""
from pathlib import Path
import json
import numpy as np

RECORD=json.loads((Path(__file__).resolve().parents[1]/'measurements/two-south-cameras.json').read_bytes())
CAMERAS={name:np.array(RECORD[name]['camera_3x4']) for name in ('close','wide')}

def position(u,v,y=0.,view='close'):
    camera=CAMERAS[view]
    h=camera[:,[0,2,3]].copy()
    h[:,2]+=camera[:,1]*y
    ray=np.linalg.solve(h,[u,v,1.])
    return np.array([ray[0]/ray[2],y,ray[1]/ray[2]])

def pixel(xyz,view='close'):
    p=CAMERAS[view]@np.r_[xyz,1.]
    return p[:2]/p[2]
