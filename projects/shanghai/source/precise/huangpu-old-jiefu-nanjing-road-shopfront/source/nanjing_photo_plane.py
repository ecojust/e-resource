"""Map upright Chainwit. 2024 photographs to the local north facade at chosen Y."""
from pathlib import Path
import json
import numpy as np

data=json.loads((Path(__file__).resolve().parents[1]/'measurements/nanjing-window-registration.json').read_bytes())
CAMERAS={k:np.array(v)for k,v in data['cameras_west_inward_up_to_px'].items()}
def position(u,v,y=0.,view='b'):
    """Return west X, inward Y and grade Z. View a is upright oblique, b is near."""
    p=CAMERAS[view]
    h=p[:,[0,2,3]].copy()
    h[:,2]+=p[:,1]*y
    local=np.linalg.solve(h,[u,v,1.])
    return np.array([local[0]/local[2],y,local[1]/local[2]])
def pixel(xyz,view='b'):
    p=CAMERAS[view]@np.r_[xyz,1.]
    return p[:2]/p[2]
