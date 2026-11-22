"""Photo mapping for the west street facade, metres; X south, Y inward, Z upward."""
import json
from pathlib import Path
import numpy as np

M=Path(__file__).resolve().parents[1]/'measurements'
CALIBRATION=json.loads((M/'west-upper-window-calibration.json').read_text())
FRAME_SETBACK=.10  # Assumed reveal between exterior wall and face of the dark frames.

def matrix(camera='2018_commons'):
    p=np.array(CALIBRATION['photographic_cameras'][camera],float)
    p[:,3]-=p[:,1]*FRAME_SETBACK
    return p

def on_wall(u,v,y=0.,camera='2018_commons'):
    p=matrix(camera)
    h=np.column_stack((p[:,0],p[:,2],p[:,3]+y*p[:,1]))
    q=np.linalg.solve(h,[float(u),float(v),1.])
    return [float(q[0]/q[2]),float(y),float(q[1]/q[2])]

def pixel(xyz,camera='2018_commons'):
    q=matrix(camera)@np.r_[xyz,1.]
    return [float(q[0]/q[2]),float(q[1]/q[2])]
