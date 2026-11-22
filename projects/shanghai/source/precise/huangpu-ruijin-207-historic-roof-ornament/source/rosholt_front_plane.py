"""Original 1020 × 706 Ro-s018 print and the reconstructed external wall plane."""
import json
from pathlib import Path
import numpy as np

DATA = json.loads((Path(__file__).resolve().parents[1] / 'measurements' / 'rosholt-long-front-registration.json').read_text())
PROJECTION = np.array(DATA['projection'])

def on_face(uv, y=0.):
    u,v=uv
    eq=PROJECTION[:2]-np.array([[u],[v]])*PROJECTION[2]
    x,z=np.linalg.solve(eq[:,[0,2]],-eq[:,3]-y*eq[:,1])
    return np.array([x,y,z])

def pixel(xyz):
    uvw=PROJECTION@np.r_[xyz,1.]
    return (uvw[:2]/uvw[2]).tolist()
