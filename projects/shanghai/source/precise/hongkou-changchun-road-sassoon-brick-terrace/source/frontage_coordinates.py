"""Camera coordinates for the photographed eight window axes on Changchun Road."""
import json
from pathlib import Path

import numpy as np

MEASUREMENTS = Path(__file__).resolve().parents[1] / 'measurements'
CAMERAS = json.loads((MEASUREMENTS / 'north-frontage-cameras.json').read_bytes())
FRONT_CAMERA = np.asarray(CAMERAS['front'])
EARLIER_CAMERA = np.asarray(CAMERAS['gao'])
WINDOW_PLANES = {1:-.03,2:-.03,3:0.,4:0.,5:0.,6:0.,7:-.03,8:-.03}

def facade_point(u,v,face_y=0.,camera=FRONT_CAMERA):
    """Intersect an original image pixel with the vertical plane Y=face_y."""
    eq=camera[:2]-np.array([[u],[v]])*camera[2]
    x,z=np.linalg.solve(eq[:,[0,2]],-eq[:,3]-face_y*eq[:,1])
    return float(x),float(face_y),float(z)

def project(point,camera=FRONT_CAMERA):
    uv=camera@[*point,1.0]
    return uv[:2]/uv[2]
