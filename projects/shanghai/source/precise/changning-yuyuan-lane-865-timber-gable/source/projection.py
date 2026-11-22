"""Project between the 608×686 district photograph and parallel vertical planes."""
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).absolute().parent
DATA=json.loads((HERE.parent/'measurements/front-plane-camera.json').read_bytes())
P=np.array(DATA['world_to_photo'])

def world(pixels, depth=0.):
    """Return local x,z. Depth is positive behind the exposed facade."""
    flat=np.atleast_2d(np.array(pixels,float))
    H=np.column_stack([P[:,0],P[:,2],P[:,3]+P[:,1]*depth])
    h=np.column_stack([flat,np.ones(len(flat))])@np.linalg.inv(H).T
    return h[:,:2]/h[:,2,None]

def photo(points):
    obj=np.atleast_2d(np.asarray(points,float))
    q=np.column_stack([obj,np.ones(len(obj))])@P.T
    return q[:,:2]/q[:,2,None]
